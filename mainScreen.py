import sys
from PyQt5 import QtWidgets, uic

class MainScreen(QtWidgets.QMainWindow):
    def __init__(self, login_screen):
        super(MainScreen, self).__init__()
        uic.loadUi('UIs/MainScreen.ui', self)  # Load the main.ui file
        self.login_screen = login_screen  # Save the login screen reference
        
        # Connect logout button click event to the logout function
        self.logoutButton.clicked.connect(self.logout)

    def logout(self):
        self.login_screen.show()  # Show the login screen again
        self.close()
