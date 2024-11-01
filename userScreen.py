import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow,QApplication,QTableWidgetItem,QHeaderView,QPushButton,QMessageBox,QWidget,QHBoxLayout,QLabel
from user_management import UserManager  # Import the UserManager class
from sensor_management import SensorManager  # Import the SensorPage class
from camera_management import CameraManager
import os
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QPushButton, QMessageBox
import resources_rc
from PyQt5.QtCore import Qt,QEvent
from PyQt5.QtGui import QFont
from video_player import VideoPlayer
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
        
        self.stackedWidget.setCurrentIndex(0)
        self.btnStartTraining.clicked.connect(lambda: self.change_page(0))
        self.btnUserProfile.clicked.connect(lambda: self.change_page(1))
        self.btnLogout.clicked.connect(self.logout)
        self.btnStartTraining.clicked.connect(self.load_training_data)

        # Set initial row height
        self.set_table_row_height()

        self.load_training_data()  # Call to load training data into the table

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
                    print(len(data))
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


            print(f"Row count after insertion: {self.trainingDataTable.rowCount()}")

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
            test_category='default'
            if os.path.exists(info_file):
                # Load info data from test_subject_info.txt
                with open(info_file, "r") as file:
                    info_content = file.read().splitlines()
                    if len(info_content) >= 3:
                        test_category, subject, instrument = info_content[:3]
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
                self.video_player = VideoPlayer(video_path, settings_data,self.user,test_category)
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

    def change_page(self, page_index):
        self.stackedWidget.setCurrentIndex(page_index)
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
