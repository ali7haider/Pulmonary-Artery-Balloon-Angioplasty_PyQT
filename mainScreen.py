import sys
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow,QTableWidgetItem,QHeaderView,QPushButton,QMessageBox,QDialog
class MainScreen(QMainWindow):
    def __init__(self, login_screen,db_manager, user):
        super(MainScreen, self).__init__()
        uic.loadUi('UIs/MainScreen.ui', self)  # Load the main.ui file
        self.login_screen = login_screen  # Save the login screen reference
        self.db_manager = db_manager  # Store the DatabaseManager instance
        self.user = user  # Store the logged-in user data

        # Connect buttons to change pages in the stacked widget
        self.btnSensorManagement.clicked.connect(lambda: self.change_page(0))  # Button to show page 1
        self.btnCameraManagement.clicked.connect(lambda: self.change_page(1))  # Button to show page 2
        self.btnUserManagement.clicked.connect(lambda: self.change_page(2))  # Button to show page 3
        self.btnStartTraining.clicked.connect(lambda: self.change_page(3))  # Button to show page 3
        self.btnUserProfile.clicked.connect(lambda: self.change_page(4))  # Button to show page 3

        # Connect logout button click event to the logout function
        self.btnLogout.clicked.connect(self.logout)

    
    def change_page(self, page_index):
        """Change the current page of the QStackedWidget."""
        self.stackedWidget.setCurrentIndex(page_index)  # Assuming stackedWidget is the object name in .ui file

    
    def logout(self):
        self.login_screen.show()  # Show the login screen again
        self.close()
