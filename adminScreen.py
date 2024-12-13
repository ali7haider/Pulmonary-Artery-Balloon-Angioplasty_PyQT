import sys
import os
import glob
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import Qt, QEvent, QSize
from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
    QGridLayout, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QMessageBox, QWidget, QHeaderView
)

import resources_rc
from editUser_ui import Ui_Dialog
from user_management import UserManager  # Import the UserManager class
from sensor_management import SensorManager  # Import the SensorPage class
from camera_management import CameraManager
from video_player import VideoPlayer
import cv2

class AdminScreen(QMainWindow):
    def __init__(self, login_screen=None,db_manager=None, user=None):
        super(AdminScreen, self).__init__()
        uic.loadUi('UIs/adminScreen.ui', self)  # Load the main.ui file
        
        self.login_screen = login_screen  # Save the login screen reference
        self.db_manager = db_manager  # Store the DatabaseManager instance
        self.user = user  # Store the logged-in user data
        self.user_manager = UserManager(db_manager)  # Initialize UserManager
        self.sensor_manager = SensorManager(self)  # Instantiate the sensor page logic
        
        self.camera_manager = CameraManager(self)  # Instantiate the camera manager
        self.active_button = self.btnSensorManagement  # To store the currently active button
        self.update_button_style(self.active_button)
        
        self.video_path = None  # Path to the video file
        self.settings_data = {}  # Dictionary to hold settings data
        self.video_frame = 0  # Current video frame index
        self.is_admin = user["isAdmin"] if user else False  # Determine if user is admin

        # Connect buttons to change pages in the stacked widget
        self.stackedWidget.setCurrentIndex(0)  # Assuming stackedWidget is the object name in .ui file
        self.btnSensorManagement.clicked.connect(lambda: self.change_page(0, self.btnSensorManagement))
        self.btnCameraManagement.clicked.connect(lambda: self.change_page(1, self.btnCameraManagement))
        self.btnUserManagement.clicked.connect(lambda: self.change_page(2, self.btnUserManagement))
        self.btnStartTraining.clicked.connect(lambda: self.change_page(3, self.btnStartTraining))
        self.btnUserProfile.clicked.connect(lambda: self.change_page(4, self.btnUserProfile))
        # Connect logout button click event to the logout function
        self.btnLogout.clicked.connect(self.logout)

         # Connect buttons for adding a user
        self.btnAddNewUser.clicked.connect(self.add_user)  # Connect the add user button click event

        self.btnUserManagement.clicked.connect(self.load_user_data_from_database)  # Button to show page 3        

        # Connect buttons for camera management
        self.btnConnectCamera.clicked.connect(self.camera_manager.connect_camera)
        self.btnPlotLines.clicked.connect(self.camera_manager.plot_lines)
        self.btnLoadVideo.clicked.connect(self.camera_manager.load_video)
        self.btnCircleCallibaration.clicked.connect(self.camera_manager.calibrate_circle)
        self.btnInsertTubeMonitor.clicked.connect(self.camera_manager.update_frame)
        self.btnInsertWireMonitor.clicked.connect(self.camera_manager.update_frame)
        self.btnInsertBallonMonitor.clicked.connect(self.camera_manager.update_frame)

        self.btnStartTraining.clicked.connect(self.load_training_data)
        # Assume you have a QListWidget in your UI named listTestSubjects
        self.test_subject_list = self.findChild(QTreeWidget, 'listTestSubjects')
        # Set initial row height
        self.set_table_row_height()

        self.load_training_data()  # Call to load training data into the table
        # Load test subjects into left bar when user profile is accessed
        self.btnUserProfile.clicked.connect(self.load_test_subjects)  
        # In your UserScreen class __init__ method, after connecting the QListWidget
        self.test_subject_list.itemClicked.connect(self.handle_item_click)
        self.current_test_subject = None
        self.current_test_date = None  # Initialize current test date


    def handle_item_click(self, item):
        # Check if the clicked item is a test category or test subject
        if item.parent() is None:  # This means it's a test category
            return
        elif item.parent().parent() is not None:  # This means it's a date under a test subject
            self.current_test_subject = item.parent()  # Save the current test subject
            self.current_date = item  # Save the current date
            self.load_media(item)  # Load media for the selected date
        else:  # It's a test subject
            self.current_test_subject = item  # Save the current test subject
            self.load_media(item)  # Load media for the test subject, if needed

    def resizeEvent(self, event):
        if self.current_test_subject is not None and self.current_date is not None:
            self.load_media(self.current_date)  # Reload media on resize
        super(AdminScreen, self).resizeEvent(event)
    def load_media(self, item):
        user_folder_name = f"{self.user['id']}_{self.user['username']}"
        
        # Determine the folder path based on the clicked item
        if item.parent() is not None:  # Check if it's a test subject or a date
            if item.parent().parent() is not None:  # It's a date under a test subject
                test_category = item.parent().parent().text(0)  # Get the test category
                test_subject = item.parent().text(0)  # Get the test subject
                test_date = item.text(0)  # Get the test date
                
                # Set folder_path to the date folder directly
                folder_path = os.path.join("userData", user_folder_name, test_category, test_subject, test_date)
            else:  # It's a test subject
                test_category = item.parent().text(0)  # Get the test category
                test_subject = item.text(0)  # Get the test subject
                folder_path = os.path.join("userData", user_folder_name, test_category, test_subject)
        else:  # If it’s a test category
            return  # Do nothing for now, or handle it accordingly

        # Clear existing widgets in the frameImagesVideos
        layout = self.frameImagesVideos.layout()  # Get the existing layout
        if layout is not None:
            while layout.count():
                widget = layout.itemAt(0).widget()  # Get the first widget
                layout.removeWidget(widget)  # Remove it from layout
                widget.deleteLater()  # Delete the widget to free up memory
        else:
            layout = QGridLayout()
            self.frameImagesVideos.setLayout(layout)

        # Load all images and videos from the selected date folder
        if os.path.exists(folder_path):
            # Initialize lists to store images and videos
            images = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.png"))
            videos = glob.glob(os.path.join(folder_path, "*.avi"))  + glob.glob(os.path.join(folder_path, "*.mp4"))  # Add other video formats if needed

            # Calculate the number of columns based on available width
            item_width = 320  # Adjust this value as needed (image width + margin)
            available_width = self.frameImagesVideos.width()  # Get available width of the frame
            num_columns = available_width // item_width  # Calculate number of columns

            # Initialize row and column indices
            row, col = 0, 0

            # Display images and videos
            for media_path in images + videos:  # Combine images and videos
                if media_path in images:
                    # Display image
                    img_label = QLabel()
                    img_label.setPixmap(QPixmap(media_path).scaled(400, 300, Qt.KeepAspectRatio))  # Load the image with scaling
                    layout.addWidget(img_label, row, col, alignment=Qt.AlignTop)  # Add the image to the grid
                else:
                    # Create a thumbnail for the video
                    thumbnail = self.create_video_thumbnail(media_path)

                    if thumbnail is not None:
                        # Create a widget to hold the thumbnail and overlay
                        video_widget = QWidget()
                        video_layout = QVBoxLayout(video_widget)

                        # Create the thumbnail label
                        thumbnail_label = QLabel()
                        thumbnail_label.setPixmap(thumbnail.scaled(400, 300, Qt.KeepAspectRatio))  # Scale thumbnail

                        video_layout.addWidget(thumbnail_label)

                        # Create the overlay label with the play icon
                        play_icon = QPixmap(":/images/images/icons8-circled-play-100.png")  # Replace with the path to your play icon
                        overlay_label = QPushButton()
                        # Scale the play icon and set it on the button
                        play_icon = play_icon.scaled(80, 80, Qt.KeepAspectRatio)  # Scale the play icon
                        overlay_label.setIcon(QIcon(play_icon))
                        overlay_label.setIconSize(QSize(30, 30))  # Set the icon size for the button

                        overlay_label.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); margin:0px 0px; padding:2px; min-height:30px;")  # Optional semi-transparent background
                        overlay_label.clicked.connect(lambda _, path=media_path: self.play_video(path))

                        # Add overlay label  on top of the thumbnail
                        overlay_widget = QWidget()
                        overlay_widget.setMaximumWidth(300)  # Set the maximum width for the overlay widget

                        overlay_layout = QVBoxLayout(overlay_widget)
                        overlay_layout.addWidget(thumbnail_label)
                        overlay_layout.addWidget(overlay_label)
                        overlay_layout.setContentsMargins(2, 2, 2, 2)  # For the main layout
                        overlay_layout.setSpacing(1)  # For the main layout

                        overlay_widget.setLayout(overlay_layout)
                        video_layout.addWidget(overlay_widget)
                        video_layout.setContentsMargins(0, 0, 0, 0)  # For the main layout
                        video_layout.setSpacing(0)  # For the main layout

                        layout.addWidget(video_widget, row, col)  # Add the video widget to the grid

                # Update the column index
                col += 1
                
                # Move to the next row if column limit is reached
                if col >= num_columns:  
                    col = 0  # Reset column index
                    row += 1  # Move to the next row

            # Ensure that the last row is filled correctly
            layout.setRowStretch(row, 1)  # Stretch the last row if necessary
        else:
            QMessageBox.warning(self, "Folder Not Found", "No media found for the selected test subject.")
    def play_video(self, video_path):
        # Your code to handle video playback, using the provided video_path
        print(f"Playing video from: {video_path}")
        # Implement actual video playback functionality here

    def create_video_thumbnail(self, video_path):
        # Capture the video
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return None  # Return None if video cannot be opened

        # Get a frame at the 1-second mark (or any other time point)
        cap.set(cv2.CAP_PROP_POS_MSEC, 1000)  # Move to 1 second

        ret, frame = cap.read()  # Read the frame
        cap.release()  # Release the video capture

        if ret:
            # Convert the frame from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create a QImage from the frame
            height, width, _ = frame.shape
            qimage = QImage(frame.data, width, height, width * 3, QImage.Format_RGB888)

            # Convert QImage to QPixmap
            return QPixmap.fromImage(qimage)
        
        return None

    
    def load_test_subjects(self):
        # Clear existing widgets in the frameImagesVideos
        layout = self.frameImagesVideos.layout()  # Get the existing layout
        if layout is not None:
            while layout.count():
                widget = layout.itemAt(0).widget()  # Get the first widget
                layout.removeWidget(widget)  # Remove it from layout
                widget.deleteLater()  # Delete the widget to free up memory
        user_folder_name = f"{self.user['id']}_{self.user['username']}"

        # Create folder path for the current user
        folder_path = os.path.join("userData", user_folder_name)

        if os.path.exists(folder_path):
            # Clear existing items in the test subject tree
            self.test_subject_list.clear()

            # Retrieve all test categories (subfolders) within the user's folder
            for test_category in os.listdir(folder_path):
                test_category_path = os.path.join(folder_path, test_category)
                if os.path.isdir(test_category_path):  # Check if it's a directory

                    # Create a parent item for each test category
                    category_item = QTreeWidgetItem(self.test_subject_list)
                    category_item.setText(0, test_category)

                    # Retrieve all test subjects within each test category
                    for test_subject in os.listdir(test_category_path):
                        test_subject_path = os.path.join(test_category_path, test_subject)
                        if os.path.isdir(test_subject_path):  # Check if it's a directory

                            # Create a child item for each test subject
                            subject_item = QTreeWidgetItem(category_item)
                            subject_item.setText(0, test_subject)

                            # Retrieve all dates within each test subject
                            for test_date in os.listdir(test_subject_path):
                                test_date_path = os.path.join(test_subject_path, test_date)
                                if os.path.isdir(test_date_path):  # Check if it's a directory

                                    # Create a sub-child item for each test date
                                    date_item = QTreeWidgetItem(subject_item)
                                    date_item.setText(0, test_date)
        else:
            QMessageBox.warning(self, "Folder Not Found", "No test categories found for the current user.")

    def load_training_data(self):
        try:
            # Check if the training directory exists
            training_dir = self.get_training_directory()
            if not training_dir:
                return

            print(f"Loading training data from directory: {training_dir}")

            # Clear the table and set up headers
            self.setup_training_table()

            # Retrieve folder data with video and test_subject_info content
            folder_data = self.retrieve_folder_data(training_dir)

            # Populate the table with the retrieved folder data
            self.populate_training_table(folder_data)

        except Exception as e:
            print(f"Exception occurred: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while loading training data: {e}")

    def load_settings(self, settings_file):
        """Load the settings from the .txt file and convert them to a dictionary."""
        settings_data = {}
        with open(settings_file, 'r') as file:
            for line in file:
                frame, sensor, required_value, countdown, voice_prompt = line.strip().split(maxsplit=4)
                settings_data[int(frame)] = {
                    "sensor": sensor,
                    "required_value": int(required_value),
                    "countdown": int(countdown),
                    "voice_prompt": voice_prompt
                }
        return settings_data
    def get_training_directory(self):
        """Check for either 'Training' or 'training' directory and return its path if it exists."""
        training_dir = "test_subject" if os.path.exists("test_subject") else "test_Subject"
        if not os.path.exists(training_dir):
            print("Training directory not found.")
            QMessageBox.warning(self, "Error", "Training directory not found.")
            return None
        return training_dir
    def setup_training_table(self):
        # Clear table and set headers
        self.trainingDataTable.setRowCount(0)
        self.trainingDataTable.setColumnCount(6)  # 6 columns for Test Category, Subject, Instrument, Date, MyScore, Action
        self.trainingDataTable.setHorizontalHeaderLabels(["Test Category", "Subject", "Instrument", "Date", "MyScore", "Action"])

        

        # Set column resizing
        # for i in range(6):

    def retrieve_folder_data(self, training_dir):
        """Collects folder name, video path, and content of test_subject_info for each folder in the training directory."""
        folder_data = []
        for folder_name in os.listdir(training_dir):
            folder_path = os.path.join(training_dir, folder_name)
            print(f"Processing folder: {folder_name}")

            if os.path.isdir(folder_path):
                video_file = self.get_video_file(folder_path)
                info_file = os.path.join(folder_path, "test_subject_info.txt")

                if video_file and os.path.exists(info_file):
                    # Load info data from test_subject_info.txt
                    with open(info_file, "r") as file:
                        info_content = file.read().splitlines()
                        if len(info_content) >= 3:
                            test_category, subject, instrument = info_content[:3]
                            date = ""  # Date initially empty
                            score = ""  # MyScore initially empty
                            folder_data.append((test_category, subject, instrument, date, score, folder_path))

        return folder_data


    def get_video_file(self, folder_path):
        """Finds a video file in the folder if available."""
        for file_name in os.listdir(folder_path):
            if file_name.endswith((".mp4", ".avi")):
                print(f"Found video file: {file_name}")
                return file_name
        return None

    def get_settings_content(self, folder_path):
        """Finds a .txt file in the folder and returns its content."""
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".txt"):
                settings_path = os.path.join(folder_path, file_name)
                with open(settings_path, "r") as f:
                    settings_content = f.read()
                print(f"Found settings file: {settings_path}")
                return settings_content
        return None

    def get_latest_score_for_user(self,test_category, subject):
        """
        Constructs the folder path dynamically and retrieves the latest score and date for a specific Test Category and Subject.

        Args:
            user_id (str): User ID.
            username (str): Username.
            test_category (str): Test Category.
            subject (str): Subject.

        Returns:
            tuple: (latest_score, latest_date) or (None, None) if no data is found.
        """
        latest_score = None
        latest_date = None

        try:
            # Define paths based on user info, test category, test subject, and current date
            user_folder_name = f"{self.user['id']}_{self.user['username']}"
            sanitized_user_folder = user_folder_name.strip()
            sanitized_test_category = test_category.strip()
            sanitized_test_subject = subject.strip()

            # Create folder path with test_subject as a subfolder
            subject_path = os.path.join("userData", sanitized_user_folder, sanitized_test_category, sanitized_test_subject)
            # Construct the base path using user ID and username

            if not os.path.isdir(subject_path):
                print(f"Subject path not found: {subject_path}")
                return None, None

            # Iterate over date folders in the subject directory
            for date_folder in os.listdir(subject_path):
                date_path = os.path.join(subject_path, date_folder)
                score_file = os.path.join(date_path, "score.txt")

                if not os.path.isfile(score_file):
                    continue

                try:
                    # Parse date folder name
                    test_date = datetime.strptime(date_folder, "%Y-%m-%d")
                    if latest_date is None or test_date > latest_date:
                        # Read score.txt and get the total score (second line)
                        with open(score_file, 'r') as file:
                            lines = [line.strip() for line in file.readlines()]
                            total_score = int(lines[1])  # Second line is the total score
                            latest_score = total_score
                            latest_date = test_date
                except ValueError:
                    print(f"Skipping invalid date folder: {date_folder}")

        except Exception as e:
            print(f"Error accessing folder for user {self.user['username']}: {e}")

        return latest_score, latest_date.strftime("%Y-%m-%d") if latest_date else None
    def populate_training_table(self, folder_data):
        """Populates the training table with folder data and adds buttons for MyScore and Start Training."""

        # Loop through each folder data and populate the table
        for index, (test_category, subject, instrument, date, score, folder_path) in enumerate(folder_data):
            self.trainingDataTable.insertRow(index)
            # Retrieve the latest score and date dynamically
            latest_score, latest_date = self.get_latest_score_for_user(test_category, subject)
            print(latest_date,latest_score)
            # Populate each column with folder data and disable editing, using QLabel for wrapping
            for col, data in enumerate([test_category, subject, instrument, latest_date]):
                label = QLabel(data)
                label.setStyleSheet("""
                QLabel {
                    font: 9pt "Bahnschrift";
                    font-weight: normal;
                    padding:1px;

                }
                
            """)
                label.setWordWrap(True)  # Enable word wrap for QLabel
                label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                label.setToolTip(data)  # Show full text on hover if wrapped
                self.trainingDataTable.setCellWidget(index, col, label)  # Set QLabel as cell widget
    
                if col == 2 and len(data) > 30:  # Example threshold, adjust as needed
                    self.trainingDataTable.setRowHeight(index, 80)  # Adjust this height as necessary

            # Add MyScore details with button, and set them closer together
            score_widget = QWidget()
            score_layout = QHBoxLayout(score_widget)
            score_label = QLabel(str(latest_score))
            score_button = QPushButton("Details")
            score_button.setCursor(Qt.PointingHandCursor)
            score_button.setStyleSheet("""
                QPushButton {
                    
                    margin: 3px 3px;
                }
               
            """)
            score_button.clicked.connect(lambda _, test=test_category, subj=subject: self.show_score_details(test, subj))

            # Configure layout and widget margins for closeness
            score_layout.addWidget(score_label)
            score_layout.addWidget(score_button)
            score_layout.setContentsMargins(5, 0, 5, 0)
            score_layout.setSpacing(2)  # Close gap between label and button
            self.trainingDataTable.setCellWidget(index, 4, score_widget)

            # Add Start Training button
            btn_start = QPushButton("Start Training")
            btn_start.setCursor(Qt.PointingHandCursor)
            btn_start.setStyleSheet("""
                QPushButton {
                    
                    margin: 3px 3px;
                }
               
            """)
            btn_start.clicked.connect(lambda _, path=folder_path: self.start_training(path))

            # Create a widget to center the button
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.addWidget(btn_start)
            button_layout.setAlignment(Qt.AlignCenter)  # Center the button
            button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

            # Set the widget with the centered button in the table cell
            self.trainingDataTable.setCellWidget(index, 5, button_widget)

        # Resize rows to fit contents
        # self.trainingDataTable.resizeRowsToContents()
        self.trainingDataTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trainingDataTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.trainingDataTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.trainingDataTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.trainingDataTable.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

    def show_score_details(self, test_category, test_subject):
        """
        Display all available scores for the given test category and subject in a new table.

        Args:
            test_category (str): The test category to display scores for.
            test_subject (str): The subject within the test category.
        """
        # Create a dialog or window to display the scores
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Scores for {test_category} - {test_subject}")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Create a table to display the scores
        score_table = QTableWidget(dialog)
        score_table.setColumnCount(3)
        score_table.setHorizontalHeaderLabels(["Date", "Score", "View"])
        score_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        score_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(score_table)

        # Get user folder and construct paths
        user_folder_name = f"{self.user['id']}_{self.user['username']}"
        subject_path = os.path.join("userData", user_folder_name, test_category.strip(), test_subject.strip())

        if not os.path.isdir(subject_path):
            QMessageBox.warning(self, "No Data", f"No data found for {test_category} - {test_subject}")
            return

        # Populate the table with scores
        row_index = 0
        for date_folder in os.listdir(subject_path):
            date_path = os.path.join(subject_path, date_folder)
            score_file = os.path.join(date_path, "score.txt")

            if not os.path.isfile(score_file):
                continue

            try:
                # Read score details
                with open(score_file, 'r') as file:
                    lines = [line.strip() for line in file.readlines()]
                    total_score = int(lines[1])  # Second line is the total score
                    test_date = datetime.strptime(date_folder, "%Y-%m-%d").strftime("%d-%m-%Y")

                    # Add a new row
                    score_table.insertRow(row_index)

                    # Add Date column
                    date_label = QLabel(test_date)
                    date_label.setAlignment(Qt.AlignCenter)
                    score_table.setCellWidget(row_index, 0, date_label)

                    # Add Score column
                    score_label = QLabel(str(total_score))
                    score_label.setAlignment(Qt.AlignCenter)
                    score_table.setCellWidget(row_index, 1, score_label)

                    # Add View button
                    btn_view = QPushButton("View")
                    btn_view.setStyleSheet('''QPushButton {
    color: white;                      /* Text color */
    border-radius: 4px;                /* Rounded corners */
    padding: 5px 8px;                 /* Padding inside button */
font: 10pt "Bahnschrift SemiCondensed";
    background-color: #48ACAC;         /* Slightly darker color on hover */
       /* Border with a slightly darker shade */
}

QPushButton:hover {
    background-color: #2F958D;         /* Slightly darker color on hover */
}

QPushButton:pressed {
       /* Darken the border further when pressed */
    padding-left: 14px;                /* Slight movement for press effect */
    padding-top: 6px;                  /* Slight movement for press effect */
}''')
                    btn_view.setCursor(Qt.PointingHandCursor)
                    btn_view.clicked.connect(lambda _, date_path=date_path: self.view_date_score(date_path))
                    view_widget = QWidget()
                    view_layout = QHBoxLayout(view_widget)
                    view_layout.addWidget(btn_view)
                    view_layout.setAlignment(Qt.AlignCenter)
                    view_layout.setContentsMargins(0, 0, 0, 0)
                    score_table.setCellWidget(row_index, 2, view_widget)

                    row_index += 1

            except Exception as e:
                print(f"Error reading score file {score_file}: {e}")

        # Show the dialog
        dialog.exec_()


    def view_date_score(self, date_path):
        """
        Display the score details for a specific date in a new dialog.

        Args:
            date_path (str): The path to the folder containing the score.txt file for the selected date.
        """
        # Create a dialog to display the score details
        dialog = QDialog(self)
        dialog.setWindowTitle("Score Details")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Create a table to display the score details
        detail_table = QTableWidget(dialog)
        detail_table.setColumnCount(4)
        detail_table.setHorizontalHeaderLabels(["Step", "Weight", "Score", "Reason"])
        detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        detail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(detail_table)

        score_file = os.path.join(date_path, "score.txt")

        if not os.path.isfile(score_file):
            QMessageBox.warning(self, "File Not Found", f"No score file found at {score_file}")
            return

        try:
            # Read the score.txt file
            with open(score_file, 'r') as file:
                lines = [line.strip() for line in file.readlines()]

                # First line: Number of steps
                num_steps = int(lines[0])
                # Second line: Total score (not used in detail view)
                total_score = int(lines[1])

                # Populate the table with step details
                for row_index in range(num_steps):
                    # Parse step details
                    step_details = lines[2 + row_index].split(" ", 3)
                    step_idx = step_details[0]
                    weight = step_details[1]
                    score = step_details[2]
                    reason = step_details[3]

                    # Add a new row
                    detail_table.insertRow(row_index)

                    # Populate each column
                    detail_table.setItem(row_index, 0, QTableWidgetItem(step_idx))
                    detail_table.setItem(row_index, 1, QTableWidgetItem(weight))
                    detail_table.setItem(row_index, 2, QTableWidgetItem(score))
                    detail_table.setItem(row_index, 3, QTableWidgetItem(reason))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load score details: {e}")
            print(f"Error reading score file: {score_file}. Exception: {e}")
            return

        # Show the dialog
        dialog.exec_()

    def start_training(self, folder_path):
        try:
            video_path = None
            settings_file = None
            settings_data = {}
            info_file = os.path.join(folder_path, "test_subject_info.txt")
            if os.path.exists(info_file):
                # Load info data from test_subject_info.txt
                with open(info_file, "r") as file:
                    info_content = file.read().splitlines()
                    if len(info_content) >= 3:
                        self.test_category, self.subject, instrument = info_content[:3]
                        date = ""  # Date initially empty
                        score = ""  # MyScore initially empty
            # current_row = self.trainingDataTable.currentRow()
            # test_category = self.trainingDataTable.item(current_row, 0).text()  # Assuming first column is test category

            # Find a video file and any .txt settings file in the folder
            for file_name in os.listdir(folder_path):
                if file_name.endswith((".mp4", ".avi")):
                    video_path = os.path.join(folder_path, file_name)
                    print(f"Video file path: {video_path}")
                elif file_name.endswith(".txt") and settings_file is None:
                    settings_file = os.path.join(folder_path, file_name)
                    print(f"Settings file path: {settings_file}")

            if video_path and settings_file:
                # Load settings from the .txt file (assuming JSON-like format in .txt)
                settings_data = self.load_settings(settings_file)  # or other format parsing as needed

                # Initialize and show VideoPlayer with video path and settings data
                self.video_player = VideoPlayer(video_path, settings_data,self.user,self.test_category,self.subject)
                self.video_player.show()
            else:
                print("Video or settings file not found.")
                QMessageBox.warning(self, "Error", "Video or settings file not found.")
        except Exception as e:
            print(f"Exception occurred during start training: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while starting training: {e}")
    def set_table_row_height(self):
        if self.isMaximized():
            # Set height for maximized window
            for row in range(self.trainingDataTable.rowCount()):
                self.trainingDataTable.setRowHeight(row, 40)  # Example height for maximized state
        else:
            # Set height for normal window
            for row in range(self.trainingDataTable.rowCount()):
                self.trainingDataTable.setRowHeight(row, 80)  # Example height for normal state

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            self.set_table_row_height()
        super().changeEvent(event)
    def add_user(self):
        username = self.txtUsername.text()
        password = self.txtPassword.text()
        is_admin = self.isAdminCheckBox.isChecked()

        success, message = self.user_manager.add_user(username, password, is_admin)  # Use UserManager
        self.lblError.setText(message)
        if success:
            QMessageBox.information(self, "Success", "User Added successfully.")
            self.clear_input_fields()
            self.lblError.setText("")
            self.load_user_data_from_database()  # Reload user data

    def load_user_data_from_database(self):
        columns, rows = self.user_manager.load_user_data()  # Use UserManager
        columns = ['ID', 'Username', 'Password', 'Admin', 'Edit', 'Delete']
        self.load_data_to_table(columns, rows)

    def load_data_to_table(self, columns, rows):
        """
        Load data from the database to the userDataTable and convert isAdmin to "Yes" or "No".
        """
        # Clear existing data from the table
        self.userDataTable.setRowCount(0)
        self.userDataTable.setColumnCount(0)
        self.userDataTable.horizontalHeader().setVisible(True)
        self.userDataTable.verticalHeader().setVisible(True)

        # Set table column headers
        self.userDataTable.setColumnCount(len(columns))
        self.userDataTable.resizeColumnsToContents()

        self.userDataTable.setHorizontalHeaderLabels(columns)
        self.userDataTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.userDataTable.resizeColumnsToContents()

        # Hide the ID column (assuming it's the first column, index 0)
        self.userDataTable.setColumnHidden(0, True)
        # Icons for edit and delete buttons
        edit_icon = QIcon(":/images/images/edit_icons.png")
        delete_icon = QIcon(":/images/images/delete_icon.png")

        # Populate the table with data
        for row_idx, row_data in enumerate(rows):
            self.userDataTable.insertRow(row_idx)

            for col_idx, col_data in enumerate(row_data):
                if col_idx == 3:  # This is the isAdmin column (index 3)
                    col_data = "Yes" if col_data == 1 else "No"
                self.userDataTable.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

            # Add buttons with icons in the "Edit" and "Delete" columns
            edit_btn = QPushButton()
            edit_btn.setIcon(edit_icon)
            edit_btn.setStyleSheet("background-color: transparent; border: none;cursor: pointer;")
            edit_btn.clicked.connect(lambda _, row=row_idx: self.edit_row(row))  # Connect the button to edit_row
            self.userDataTable.setCellWidget(row_idx, len(columns) - 2, edit_btn)

            delete_btn = QPushButton()
            delete_btn.setIcon(delete_icon)
            delete_btn.setStyleSheet("background-color: transparent; border: none;cursor: pointer;")
            delete_btn.clicked.connect(lambda _, row=row_idx: self.delete_row(row))  # Connect the button to delete_row
            self.userDataTable.setCellWidget(row_idx, len(columns) - 1, delete_btn)

        # Resize columns to content
        self.userDataTable.resizeColumnsToContents()
        self.userDataTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    
    
    
    
    def delete_row(self, row):
        """
        Delete a user row from the table and the database.
        """
        # Ask for confirmation using the custom message box
        confirmation = self.showYesNoMessage("Confirmation", "Are you sure you want to delete this user?")
        
        if confirmation:
            print("Deleting row:", row)
            # Retrieve the ID of the row to be deleted
            user_id = int(self.userDataTable.item(row, 0).text())
            if self.user_manager.delete_user(user_id):  # Use UserManager
                self.userDataTable.removeRow(row)
    
    def edit_row(self, row):
        # Implement logic to edit the selected row
        print("Edit row:", row)

        # Get the ID of the row from the table data
        id_index = 0  # Assuming the ID is stored in the first column
        id_item = self.userDataTable.item(row, id_index)  # Change from studentTable to userDataTable
        if id_item is not None:
            row_id = id_item.text()  # Retrieve the text (ID) from the QTableWidgetItem
        else:
            print("Error: ID item is None.")
            return

        # Fetch the data of the current user from the database based on the retrieved ID
        row_data = self.user_manager.fetch_user_by_id(row_id)

        if row_data is None:
            print("Error: No user found with this ID or user is inactive.")
            return

        # Instantiate Ui_Dialog and pass it to MyDialog
        dialog_ui = Ui_Dialog()  # Assuming Ui_Dialog is defined somewhere
        self.dialog = EditUser(dialog_ui, row_data,  self.user_manager,self)  # EditUser should handle the edit dialog
        self.dialog.exec_()
        self.load_user_data_from_database()

        self.userDataTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Adjust column widths



    def show_success_message(self, message):
        """Show a success message box."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)  # Set the icon to Information
        msg_box.setWindowTitle("Success")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)  # Show an OK button
        msg_box.exec_()
    def showYesNoMessage(self, title, message):
        """
        Display a Yes/No message box and return True if 'Yes' is clicked, otherwise return False.
        """
        reply = QMessageBox.question(self, title, message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        return False

    def show_error_message(self, message):
        """
        Show an error message box.
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    def clear_input_fields(self):
        """Clear the input fields after adding a user."""
        self.txtUsername.clear()
        self.txtPassword.clear()
        self.isAdminCheckBox.setChecked(False)  # Uncheck the admin checkbox

    
    def change_page(self, index, clicked_button):
        # Change page in the stacked widget
        self.stackedWidget.setCurrentIndex(index)
        
        # Update button color
        self.update_button_style(clicked_button)

    def update_button_style(self, clicked_button):
        # Reset the previous button to default style if one was active
        if self.active_button:
            self.active_button.setStyleSheet("")  # Reset to default
        
        # Set the clicked button to a dark color
        clicked_button.setStyleSheet("background-color: #2F958D; color: white;")  # Dark color style
        self.active_button = clicked_button  # Update the active button
    
    def logout(self):
        self.login_screen.show()  # Show the login screen again
        self.close()

from PyQt5.QtWidgets import QDialog, QMessageBox

class EditUser(QDialog):
    def __init__(self, ui, row_data, user_manager, parent=None):
        super(EditUser, self).__init__(parent)
        self.ui = ui
        self.ui.setupUi(self)
        self.row_data = row_data
        self.user_manager = user_manager
        # Set initial values in the UI
        self.set_initial_values()

        # Connect the edit button to the update method
        self.ui.btnEdit.clicked.connect(self.update_user_details)  # Assuming you have a button named btnEdit

    def set_initial_values(self):
        # Assuming row_data format is (id, username, password, isAdmin)
        if self.row_data:
            user_id, username, password, is_admin = self.row_data
            
            # Set values in the UI elements
            self.ui.txtUsername.setText(username)
            self.ui.txtPassword.setText(password)

            # Set checkbox state based on isAdmin
            self.ui.isAdminCheckBox.setChecked(is_admin == 1)  # Check the checkbox if isAdmin is 1
            
            # Optional: Make the checkbox uncheckable if is_admin is 0
            self.ui.isAdminCheckBox.setEnabled(is_admin == 1)  # Disable checkbox if not admin

    def update_user_details(self):
        """Update the user details in the database."""
        # Retrieve updated values from UI elements
        username = self.ui.txtUsername.text()
        password = self.ui.txtPassword.text()
        is_admin = self.ui.isAdminCheckBox.isChecked()  # True if checked, False otherwise

        # Get the user ID from row_data
        user_id = self.row_data[0]  # Assuming ID is the first element in row_data

        # Call the update_user function from db_manager
        try:
            success = self.user_manager.edit_user(user_id, username, password, int(is_admin))  # Update the user in the database

            if success:
                QMessageBox.information(self, "Success", "User details updated successfully.")
                self.accept()  # Close the dialog and accept changes
            else:
                QMessageBox.warning(self, "Error", "Failed to update user details. Please try again.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))  # Show error message if something goes wrong
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminScreen()
    window.show()
    sys.exit(app.exec_())
