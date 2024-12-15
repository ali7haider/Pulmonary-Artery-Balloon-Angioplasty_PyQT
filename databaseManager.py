import sqlite3

class DatabaseManager:
    def __init__(self, db_file="data.db"):
        try:
            self.conn = sqlite3.connect(db_file)  # Connect to the SQLite database
            self.cursor = self.conn.cursor()  # Create a cursor object to execute SQL commands
        except sqlite3.Error as e:
            raise Exception(f"Error connecting to database: {e}")

    def create_table(self):
        try:
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
        except sqlite3.Error as e:
            raise Exception(f"Error creating table: {e}")
    
    def get_user_by_credentials(self, username, password):
        try:
            # Set the row factory to sqlite3.Row to access columns by name
            self.cursor.row_factory = sqlite3.Row
            
            # Query the database for a user with matching username and password
            self.cursor.execute('''SELECT * FROM users WHERE username = ? AND password = ? AND isActive = 1''', (username, password))
            user = self.cursor.fetchone()  # Fetch one result (user data)

            return user  # Return user data or None if no match found
        except sqlite3.Error as e:
            raise Exception(f"Error retrieving user by credentials: {e}")

    
    def check_username_exists(self, username):
        try:
            # Check if a user with the given username already exists
            self.cursor.execute('''SELECT * FROM users WHERE username = ? AND isActive = 1''', (username,))
            return self.cursor.fetchone() is not None  # Return True if user exists, False otherwise
        except sqlite3.Error as e:
            raise Exception(f"Error checking username: {e}")
    
    def insert_user(self, username, password, isAdmin=0, isActive=1):
        try:
            # First, check if the username already exists
            if self.check_username_exists(username):
                return False  # Return False indicating that the user was not inserted

            # Insert a new user into the database
            self.cursor.execute('''
                INSERT INTO users (username, password, isAdmin, isActive)
                VALUES (?, ?, ?, ?)
            ''', (username, password, isAdmin, isActive))
            
            self.conn.commit()  # Commit the transaction to save the new user in the database
            print(f"User '{username}' inserted successfully.")
            return True  # Return True indicating that the user was inserted
        except sqlite3.Error as e:
            raise Exception(f"Error inserting user: {e}")

    def fetch_all_users(self):
        """
        Fetch all active users from the database (id, username, password, isAdmin).
        """
        try:
            query = "SELECT id, username, password, isAdmin FROM users WHERE isActive = 1"
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            return columns, rows
        except sqlite3.Error as e:
            raise Exception(f"Error fetching users: {e}")

    def deactivate_user(self, user_id):
        """
        Deactivate a user from the database using their user ID.
        """
        try:
            query = "UPDATE users SET isActive = 0 WHERE id = ?"
            self.cursor.execute(query, (user_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            raise Exception(f"Error deactivating user: {e}")
    def update_user(self, user_id, username, password, isAdmin):
        """
        Update user details in the database using the user ID.
        """
        try:
            query = '''UPDATE users 
                    SET username = ?, password = ?, isAdmin = ? 
                    WHERE id = ? AND isActive = 1'''
            self.cursor.execute(query, (username, password, isAdmin, user_id))
            self.conn.commit()

            if self.cursor.rowcount == 0:
                print("No user updated. User may not exist or is inactive.")
                return False  # No rows updated
            return True  # Update successful
        except sqlite3.Error as e:
            raise Exception(f"Error updating user: {e}")


    def fetch_user_by_id(self, user_id):
        """
        Fetch a user from the database by their ID.
        Returns the user's data if found and active, else returns None.
        """
        try:
            query = "SELECT id, username, password, isAdmin FROM users WHERE id = ? AND isActive = 1"
            self.cursor.execute(query, (user_id,))
            user_data = self.cursor.fetchone()
            
            if user_data is None:
                print("Error: No user found with this ID or user is inactive.")
            
            return user_data  # Returns None if not found, otherwise returns user data
        
        except sqlite3.Error as e:
            print(f"Error fetching user by ID: {e}")
            return None  # Return None on error
