import sqlite3

class DatabaseManager:
    def __init__(self, db_file="data.db"):
        self.conn = sqlite3.connect(db_file)  # Connect to the SQLite database
        self.cursor = self.conn.cursor()  # Create a cursor object to execute SQL commands
    
    def create_table(self):
        # Create a new users table if it doesn't exist
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                isAdmin INTEGER DEFAULT 0,
                isActive INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
        self.conn.commit()  # Commit the transaction to save changes to the database
    
    def get_user_by_credentials(self, username, password):
        # Query the database for a user with matching username and password
        self.cursor.execute('''SELECT * FROM users WHERE username = ? AND password = ? AND isActive = 1''', (username, password))
        user = self.cursor.fetchone()  # Fetch one result (user data)
        return user  # Return user data or None if no match found
    
    def check_username_exists(self, username):
        # Check if a user with the given username already exists
        self.cursor.execute('''SELECT * FROM users WHERE username = ?''', (username,))
        return self.cursor.fetchone() is not None  # Return True if user exists, False otherwise
    
    def insert_user(self, username, password, isAdmin=0, isActive=1):
        # First, check if the username already exists
        if self.check_username_exists(username):
            print(f"Error: Username '{username}' already exists.")
            return False  # Return False indicating that the user was not inserted

        # Insert a new user into the database
        self.cursor.execute('''
            INSERT INTO users (username, password, isAdmin, isActive)
            VALUES (?, ?, ?, ?)
        ''', (username, password, isAdmin, isActive))
        
        self.conn.commit()  # Commit the transaction to save the new user in the database
        print(f"User '{username}' inserted successfully.")
        return True  # Return True indicating that the user was inserted
