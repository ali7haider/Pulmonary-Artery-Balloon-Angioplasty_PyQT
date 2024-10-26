# user_management.py
from PyQt5.QtWidgets import QMessageBox

class UserManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_user(self, username, password, is_admin):
        if not username or not password:
            return False, "Username and Password cannot be empty."

        if not self.db_manager.insert_user(username, password, isAdmin=int(is_admin)):
            return False, f"Error: Username '{username}' already exists."

        return True, f"User '{username}' added successfully."

    def load_user_data(self):
        return self.db_manager.fetch_all_users()

    def delete_user(self, user_id):
        return self.db_manager.deactivate_user(user_id)

    def edit_user(self, user_id, username, password, is_admin):
        return self.db_manager.update_user(user_id, username, password, int(is_admin))
    def fetch_user_by_id(self, user_id):
        return self.db_manager.fetch_user_by_id(user_id)
