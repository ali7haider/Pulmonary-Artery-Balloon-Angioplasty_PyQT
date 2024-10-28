import sys
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow,QApplication,QTableWidgetItem,QHeaderView,QPushButton,QMessageBox,QDialog
from editUser_ui import Ui_Dialog
from user_management import UserManager  # Import the UserManager class
from sensor_management import SensorManager  # Import the SensorPage class
from camera_management import CameraManager
class userScreen(QMainWindow):
    def __init__(self, login_screen=None,db_manager=None, user=None):
        super(userScreen, self).__init__()
        uic.loadUi('UIs/userScreen.ui', self)  # Load the main.ui file
        self.login_screen = login_screen  # Save the login screen reference
        self.db_manager = db_manager  # Store the DatabaseManager instance
        self.user = user  # Store the logged-in user data
        self.user_manager = UserManager(db_manager)  # Initialize UserManager
        self.sensor_manager = SensorManager(self)  # Instantiate the sensor page logic
        self.camera_manager = CameraManager(self)  # Instantiate the camera manager