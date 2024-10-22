import sys
from PyQt5 import QtWidgets, uic
import resources_rc  # Keep if necessary
# Don't import MainScreen here to avoid circular import

class LoginScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        uic.loadUi('UIs/LoginPage.ui', self)  # Load the login.ui file
        
        # Connect login button click event to the login function
        self.btnLogIn.clicked.connect(self.check_credentials)
    
    def check_credentials(self):
        # Hardcoded credentials for now
        username = self.txtUserName.text()
        password = self.txtPassword.text()

        if username == "admin" and password == "password":
            from mainScreen import MainScreen  # Import here to avoid circular import
            self.main = MainScreen(self)  # Pass the current instance
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
