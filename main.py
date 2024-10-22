import sys
from PyQt5 import QtWidgets, uic
import sqlite3
from databaseManager import DatabaseManager
import resources_rc
class LoginScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        uic.loadUi('UIs/LoginPage.ui', self)  # Load the login.ui file
        self.db_manager = DatabaseManager("data.db")  # Initialize DatabaseManager
        self.db_manager.create_table()  # Ensure table is created
        # Insert a new user
        if not self.db_manager.insert_user("", "", isAdmin=1, isActive=1):
            print("Failed to insert user: Username already exists.")        # Connect login button click event to the login function
        self.btnLogIn.clicked.connect(self.check_credentials)
    
    def check_credentials(self):
        # Get username and password input from the UI
        username = self.txtUserName.text()
        password = self.txtPassword.text()

        # Query the database for the entered username and password
        user = self.db_manager.get_user_by_credentials(username, password)

        if user:  # If user is found in the database
            from mainScreen import MainScreen  # Import here to avoid circular import
            self.main = MainScreen(self,self.db_manager, user)  # Pass DatabaseManager and user data
            self.main.show()
            self.close()
        else:
            self.lblError.setText("Invalid username or password")

# Main application
app = QtWidgets.QApplication(sys.argv)

# Show the login screen
login_screen = LoginScreen()
login_screen.show()

sys.exit(app.exec_())
