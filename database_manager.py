import mariadb
import os
from dotenv import load_dotenv


class DatabaseManager:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env
        self.DB_HOST = os.getenv('DB_HOST')
        self.DB_USER = os.getenv('DB_USER')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_NAME = os.getenv('DB_NAME')
        self.conn = mariadb.connect(
            host=self.DB_HOST,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            database=self.DB_NAME
        )
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Voyages (
                    log_id INTEGER PRIMARY KEY,
                    target_id INTEGER,
                    amount INTEGER,
                    log_time TIMESTAMP
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Hosted (
                    log_id INTEGER PRIMARY KEY,
                    host_id INTEGER,
                    amount INTEGER,
                    log_time TIMESTAMP
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Subclasses (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    author_id INTEGER,
                    log_link TEXT,
                    target_id INTEGER,
                    subclass TEXT,
                    count INTEGER,
                    log_time TIMESTAMP
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Forceadd (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    target_id INTEGER,
                    type TEXT,
                    amount INTEGER,
                    moderator_id INTEGER,
                    timestamp TIMESTAMP
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Coins (
                    coin_id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    member_id INTEGER,
                    type TEXT,
                    moderator INTEGER,
                    old_name TEXT,
                    timestamp TIMESTAMP
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ModNotes (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    target_id INTEGER,
                    moderator_id INTEGER,
                    note TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Auditlogs (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    event TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Settings (
                    user_id INTEGER PRIMARY KEY,
                    award_ping_enabled INTEGER
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Gamertags (
                    user_id INTEGER PRIMARY KEY,
                    gamertag TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Timezones (
                    user_id INTEGER PRIMARY KEY,
                    timezone TEXT
                )
            ''')
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error creating tables: {e}")

    def get_hosted_info(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM Hosted WHERE host_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to calculate hosted voyage info (similar to your existing logic)
        except mariadb.Error as e:
            print(f"Error fetching hosted info: {e}")
            return None

    def log_voyage_data(self, log_id, target_id, amount, log_time):
        try:
            self.cursor.execute('''
                INSERT INTO Voyages (log_id, target_id, amount, log_time)
                VALUES (%s, %s, %s, %s)
            ''', (log_id, target_id, amount, log_time))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error logging voyage data: {e}")

    def get_voyage_info(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM Voyages WHERE target_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to calculate voyage info
        except mariadb.Error as e:
            print(f"Error fetching voyage info: {e}")
            return None

    def log_hosted_data(self, log_id, host_id, amount, log_time):
        try:
            self.cursor.execute('''
                INSERT INTO Hosted (log_id, host_id, amount, log_time)
                VALUES (%s, %s, %s, %s)
            ''', (log_id, host_id, amount, log_time))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error logging hosted data: {e}")

    def get_hosted_info(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM Hosted WHERE host_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to calculate hosted voyage info (similar to your existing logic)
        except mariadb.Error as e:
            print(f"Error fetching hosted info: {e}")
            return None

    def log_subclasses(self, author_id, log_link, target_id, subclass, count, timestamp):
        try:
            self.cursor.execute('''
                INSERT INTO Subclasses (author_id, log_link, target_id, subclass, count, log_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (author_id, log_link, target_id, subclass, count, timestamp))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error logging subclasses: {e}")

    def get_subclass_points(self, member_id):
        try:
            self.cursor.execute('''
                SELECT subclass, SUM(count) 
                FROM Subclasses 
                WHERE target_id = %s
                GROUP BY subclass
            ''', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get subclass points for each subclass
        except mariadb.Error as e:
            print(f"Error fetching subclass info: {e}")
            return None

    def log_forceadd(self, target_id, type, amount, moderator_id, timestamp):
        try:
            self.cursor.execute('''
                INSERT INTO Forceadd (target_id, type, amount, moderator_id, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            ''', (target_id, type, amount, moderator_id, timestamp))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error logging forceadd: {e}")

    def log_coin(self, member_id, type, moderator, old_name, timestamp):
        try:
            self.cursor.execute('''
                INSERT INTO Coins (member_id, type, moderator, old_name, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            ''', (member_id, type, moderator, old_name, timestamp))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error logging Coin: {e}")

    def get_coins(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM Coins WHERE member_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get coin information.
            # You might want to create a list of dictionaries or objects representing each coin,
            # extracting relevant information like coin type, moderator who awarded it, etc.
            return rows  # Return fetched rows or processed data
        except mariadb.Error as e:
            print(f"Error retrieving coins: {e}")
            return None

    def remove_coin(self, coin_id):
        try:
            self.cursor.execute('DELETE FROM Coins WHERE coin_id = %s', (coin_id,))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error deleting coin: {e}")

    def add_note_to_file(self, target_id, moderator_id, note):
        try:
            self.cursor.execute('''
                INSERT INTO ModNotes (target_id, moderator_id, note)
                VALUES (%s, %s, %s)
            ''', (target_id, moderator_id, note))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error adding note: {e}")

    def get_notes(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM ModNotes WHERE target_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get moderation notes.
            # You could create a list of dictionaries or objects representing each note,
            # including the note text, moderator who added it, and timestamp.
            return rows  # Return fetched rows or processed data
        except mariadb.Error as e:
            print(f"Error getting notes: {e}")
            return None

    def remove_note(self, note_id):
        try:
            self.cursor.execute('DELETE FROM ModNotes WHERE id = %s', (note_id,))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error removing note: {e}")

    def log_event(self, event):
        try:
            self.cursor.execute('''
                INSERT INTO Auditlogs (event)
                VALUES (%s)
            ''', (event,))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error logging Event: {e}")

    def get_audit_logs(self, member_id, action_types=None):
        try:
            if action_types:
                placeholders = ', '.join(['?'] * len(action_types))
                query = f'''
                    SELECT * FROM Auditlogs
                    WHERE event LIKE CONCAT('%', ?, '%') 
                    AND event LIKE ANY(VALUES({placeholders}))
                    ORDER BY id DESC
                '''
                self.cursor.execute(query, [member_id] + action_types)
            else:
                query = '''
                    SELECT * FROM Auditlogs
                    WHERE event LIKE CONCAT('%', ?, '%')
                    ORDER BY id DESC
                '''
                self.cursor.execute(query, (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get audit logs
            return rows  # Return fetched rows or processed data
        except mariadb.Error as e:
            print(f"Error fetching audit logs: {e}")
            return []

    def toggle_award_ping(self, user_id, new_choice):
        try:
            self.cursor.execute('''
                INSERT INTO Settings (user_id, award_ping_enabled)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE award_ping_enabled = VALUES(award_ping_enabled)
            ''', (user_id, new_choice))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error changing award ping setting: {e}")

    def get_award_ping_setting(self, user_id):
        try:
            self.cursor.execute('SELECT award_ping_enabled FROM Settings WHERE user_id = %s', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None  # Return None if no setting is found
        except mariadb.Error as e:
            print(f"Error retrieving ping setting: {e}")
            return None

    def add_gamertag(self, user_id, gamertag):
        try:
            self.cursor.execute('''
                INSERT INTO Gamertags (user_id, gamertag)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE gamertag = VALUES(gamertag)
            ''', (user_id, gamertag))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error writing Gamertag: {e}")

    def get_gamertag(self, user_id):
        try:
            self.cursor.execute('SELECT gamertag FROM Gamertags WHERE user_id = %s', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except mariadb.Error as e:
            print(f"Error retrieving gamertag: {e}")
            return None

    def get_timezone(self, user_id):
        try:
            self.cursor.execute('SELECT timezone FROM Timezones WHERE user_id = %s', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except mariadb.Error as e:
            print(f"Error retrieving timezone: {e}")
            return None