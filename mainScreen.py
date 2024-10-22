import sys
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow,QTableWidgetItem,QHeaderView,QPushButton,QMessageBox,QDialog
from editUser_ui import Ui_Dialog

class MainScreen(QMainWindow):
    def __init__(self, login_screen,db_manager, user):
        super(MainScreen, self).__init__()
        uic.loadUi('UIs/MainScreen.ui', self)  # Load the main.ui file
        self.login_screen = login_screen  # Save the login screen reference
        self.db_manager = db_manager  # Store the DatabaseManager instance
        self.user = user  # Store the logged-in user data
        self.stackedWidget.setCurrentIndex(0)  # Assuming stackedWidget is the object name in .ui file

        # Connect buttons to change pages in the stacked widget
        self.btnSensorManagement.clicked.connect(lambda: self.change_page(0))  # Button to show page 1
        self.btnCameraManagement.clicked.connect(lambda: self.change_page(1))  # Button to show page 2
        self.btnUserManagement.clicked.connect(lambda: self.change_page(2))  # Button to show page 3
        self.btnStartTraining.clicked.connect(lambda: self.change_page(3))  # Button to show page 3
        self.btnUserProfile.clicked.connect(lambda: self.change_page(4))  # Button to show page 3

        # Connect logout button click event to the logout function
        self.btnLogout.clicked.connect(self.logout)

         # Connect buttons for adding a user
        self.btnAddNewUser.clicked.connect(self.add_user)  # Connect the add user button click event

        self.btnUserManagement.clicked.connect(self.load_user_data_from_database)  # Button to show page 3

    def add_user(self):
        """Add a new user to the database when btnAddUser is clicked."""
        try:
            # Get data from input fields
            username = self.txtUsername.text()
            password = self.txtPassword.text()
            is_admin = self.isAdminCheckBox.isChecked()  # True if checked, False otherwise

            # Validate the input
            if not username or not password:
                self.lblError.setText("Username and Password cannot be empty.")
                return

            # Try to insert the user into the database
            if not self.db_manager.insert_user(username, password, isAdmin=int(is_admin)):
                self.lblError.setText(f"Error: Username '{username}' already exists.")
            else:
                self.lblError.setText("")
                self.show_success_message(f"User '{username}' added successfully.")

                self.clear_input_fields()  # Clear input fields after successful addition

                # Reload the user data in the table to show the newly added user
                self.load_user_data_from_database()

        except AttributeError as e:
            print(f"Error: {e}")
            self.lblError.setText("Error: One or more UI elements are not found.")

    def load_user_data_from_database(self):
        """
        Fetch user data from the database using DatabaseManager and load it into the table.
        """
        # Fetch data using the DatabaseManager
        columns, rows = self.db_manager.fetch_all_users()

        # Add extra columns for "Edit" and "Delete" actions
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
            user_id = int(self.userDataTable.item(row, 0).text())  # Assuming the ID is in the first column
            
            # Perform deletion operation using the user_id
            if self.db_manager.deactivate_user(user_id):
                # If deletion was successful, remove the row from the table
                self.userDataTable.removeRow(row)
            else:
                self.show_error_message("Error deleting user from the database.")
    
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
        row_data = self.db_manager.fetch_user_by_id(row_id)

        if row_data is None:
            print("Error: No user found with this ID or user is inactive.")
            return

        # Instantiate Ui_Dialog and pass it to MyDialog
        dialog_ui = Ui_Dialog()  # Assuming Ui_Dialog is defined somewhere
        self.dialog = EditUser(dialog_ui, row_data,  self.db_manager,self)  # EditUser should handle the edit dialog
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

    
    def change_page(self, page_index):
        """Change the current page of the QStackedWidget."""
        self.stackedWidget.setCurrentIndex(page_index)  # Assuming stackedWidget is the object name in .ui file

    
    def logout(self):
        self.login_screen.show()  # Show the login screen again
        self.close()

from PyQt5.QtWidgets import QDialog, QMessageBox

class EditUser(QDialog):
    def __init__(self, ui, row_data, db_manager, parent=None):
        super(EditUser, self).__init__(parent)
        self.ui = ui
        self.ui.setupUi(self)
        self.row_data = row_data
        self.db_manager = db_manager
        
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
            success = self.db_manager.update_user(user_id, username, password, int(is_admin))  # Update the user in the database

            if success:
                QMessageBox.information(self, "Success", "User details updated successfully.")
                self.accept()  # Close the dialog and accept changes
            else:
                QMessageBox.warning(self, "Error", "Failed to update user details. Please try again.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))  # Show error message if something goes wrong
