import sys
from PyQt5 import QtWidgets, uic
from databaseManager import DatabaseManager
import resources_rc
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

class LoginScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        uic.loadUi('UIs/LoginPage.ui', self)  # Load the login.ui file
        self.db_manager = DatabaseManager("data.db")  # Initialize DatabaseManager
        self.db_manager.create_table()  # Ensure table is created
        # Insert a new user
        self.db_manager.insert_user("admin", "password", isAdmin=1, isActive=1)       # Connect login button click event to the login function
        self.btnLogIn.clicked.connect(self.check_credentials)
    
    def check_credentials(self):
        # Get username and password input from the UI
        username = self.txtUserName.text()
        password = self.txtPassword.text()

        # Query the database for the entered username and password
        user = self.db_manager.get_user_by_credentials(username, password)
        if user:  # If user is found in the database
            self.txtUserName.clear()
            self.txtPassword.clear()

            is_admin = user["isAdmin"] if user else False  # Check if user is an admin, defaulting to False
            
            # Open different screens based on admin status
            if is_admin:
                from adminScreen import AdminScreen  # Import the Admin screen
                self.admin_screen = AdminScreen(self, self.db_manager, user)  # Pass necessary data
                self.admin_screen.show()
            else:
                from userScreen import UserScreen  # Import the main user screen
                self.main_screen = UserScreen(self, self.db_manager, user)  # Pass necessary data
                self.main_screen.show()
            
            self.close()  # Close the login window after opening the appropriate screen
        else:
            self.lblError.setText("Invalid username or password")


# Main application
app = QtWidgets.QApplication(sys.argv)

# Show the login screen
login_screen = LoginScreen()
login_screen.show()

sys.exit(app.exec_())
