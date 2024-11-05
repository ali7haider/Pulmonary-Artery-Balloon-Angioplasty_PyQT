import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow,QApplication,QTreeWidgetItem,QTreeWidget,QTableWidgetItem,QVBoxLayout,QGridLayout,QListWidget,QHeaderView,QPushButton,QMessageBox,QWidget,QHBoxLayout,QLabel
from user_management import UserManager  # Import the UserManager class
from sensor_management import SensorManager  # Import the SensorPage class
from camera_management import CameraManager
import os
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QPushButton, QMessageBox
import resources_rc
from PyQt5.QtCore import Qt,QEvent,QSize
from PyQt5.QtGui import QFont
from video_player import VideoPlayer
from datetime import datetime
import glob
from PyQt5.QtGui import QImage, QPixmap, QIcon
import cv2
from PyQt5.QtWidgets import QTreeWidgetItem,QTreeWidget

class UserScreen(QMainWindow):
    def __init__(self, login_screen=None, db_manager=None, user=None):
        super(UserScreen, self).__init__()
        uic.loadUi('UIs/userScreen.ui', self)
        
        self.login_screen = login_screen
        self.db_manager = db_manager
        self.user = user
        self.user_manager = UserManager(db_manager)
        self.sensor_manager = SensorManager(self)
        self.camera_manager = CameraManager(self)

        self.active_button = self.btnStartTraining  # To store the currently active button
        self.update_button_style(self.active_button)

        self.video_path = None  # Path to the video file
        self.settings_data = {}  # Dictionary to hold settings data
        self.video_frame = 0  # Current video frame index
        self.is_admin = user["isAdmin"] if user else False  # Determine if user is admin

        # Connect buttons to change pages in the stacked widget
        self.stackedWidget.setCurrentIndex(0)
        self.btnStartTraining.clicked.connect(lambda: self.change_page(0, self.btnStartTraining))
        self.btnUserProfile.clicked.connect(lambda: self.change_page(1, self.btnUserProfile))
        self.btnLogout.clicked.connect(self.logout)
        
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
        super(UserScreen, self).resizeEvent(event)

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

    def populate_training_table(self, folder_data):
        """Populates the training table with folder data and adds buttons for MyScore and Start Training."""

        # Loop through each folder data and populate the table
        for index, (test_category, subject, instrument, date, score, folder_path) in enumerate(folder_data):
            self.trainingDataTable.insertRow(index)
            print(f"Adding row {index} with test_category: {test_category}")

            # Populate each column with folder data and disable editing, using QLabel for wrapping
            for col, data in enumerate([test_category, subject, instrument, "31-10-2024"]):
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
            score_label = QLabel("0")
            score_button = QPushButton("Details")
            score_button.setCursor(Qt.PointingHandCursor)
            score_button.setStyleSheet("""
                QPushButton {
                    
                    margin: 3px 3px;
                }
               
            """)
            score_button.clicked.connect(lambda _, path=folder_path: self.show_score_details(path))

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

    def show_score_details(self, folder_path):
        # Implement logic to display detailed score information
        pass

    def start_training(self, folder_path):
        # Load subject video and settings.txt, then initiate training steps
        pass

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
    def logout(self):
        self.login_screen.show()
        self.close()

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
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserScreen()
    window.show()
    sys.exit(app.exec_())
