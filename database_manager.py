import mysql-connector-python
from dotenv import load_dotenv

class DatabaseManager:
    
	load_dotenv()  # Load environment variables from .env
		DB_HOST = os.getenv('DB_HOST')
		DB_USER = os.getenv('DB_USER')
		DB_PASSWORD = os.getenv('DB_PASSWORD')
		DB_NAME = os.getenv('DB_NAME')
	
	def __init__(self, host="your_host", user="your_user", password="your_password", database="your_database"):
    self.conn = mysql.connector.connect(
		host=DB_HOST,
		user=DB_USER,
		password=DB_PASSWORD,
		database=DB_NAME
    )
    self.cursor = self.conn.cursor()
    self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS   
 Voyages (
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                log_link TEXT,
                target_id INTEGER,
                subclass TEXT,
                count INTEGER,
                timestamp TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Forceadd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                type TEXT,
                amount INTEGER,
                moderator_id INTEGER,
                timestamp TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                type TEXT,
                moderator INTEGER,
                old_name TEXT,
                timestamp TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ModNotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                moderator_id INTEGER,
                note TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Auditlogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Settings (
                user_id INTEGER PRIMARY KEY,
                award_ping_enabled BOOLEAN
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

    def log_voyage_data(self, log_id, target_id, amount, log_time):
        try:
			self.cursor.execute('''
				INSERT INTO Voyages (log_id, target_id, amount, log_time)
				VALUES (?, ?, ?, ?)
			''', (log_id, target_id, amount, log_time))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error logging voyage data: {e}")  #Log error for debugging

    def get_voyage_info(self, member_id):
        try:
			self.cursor.execute('SELECT * FROM Voyages WHERE target_id = ?', (member_id,))
			rows = self.cursor.fetchall()
			# Process the fetched rows to calculate voyage info
			
		except mysql.connector.Error as e:
			print(f"Error fetching voyage info: {e}") #Log error for debugging
            return None  #allow the bot to exit on error
			
    def log_hosted_data(self, log_id, host_id, amount, log_time):
		try:	
			self.cursor.execute('''
				INSERT INTO Hosted (log_id, host_id, amount, log_time)
				VALUES (?, ?, ?, ?)
			''', (log_id, host_id, amount, log_time))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error logging hosted data: {e}") #log error for debugging
			
    def get_hosted_info(self, member_id):
		try:
				self.cursor.execute('SELECT * FROM Hosted WHERE host_id = ?', (member_id,))
			rows = self.cursor.fetchall()
			# Process the fetched rows to calculate hosted voyage info (similar to your existing logic)
			
		except mysql.connector.Error as e:
			print(f"Error fetching hosted info: {e}") #Log for Debuggging
			return None #allow bot to exit on error

    def log_subclasses(self, author_id, log_link, target_id, subclass, count, timestamp):
        try:
			self.cursor.execute('''
            INSERT INTO Subclasses (author_id, log_link, target_id, subclass, count, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
			''', (author_id, log_link, target_id, subclass, count, timestamp))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error logging subclasses: {e}") #Log error for debugging

    def get_subclass_points(self, member_id):
		try:
			self.cursor.execute('''
				SELECT subclass, SUM(count) 
				FROM Subclasses 
				WHERE target_id = ?
				GROUP BY subclass
			''', (member_id,))
			rows = self.cursor.fetchall()
			# Process the fetched rows to get subclass points for each subclass
        except mysql.connector.Error as e:
			print(f"Error fetching subclass info: {e}") #Log for Debuggging
			return None #allow bot to exit on error

    def log_forceadd(self, target_id, type, amount, moderator_id, timestamp):
		try:	
			self.cursor.execute('''
				INSERT INTO Forceadd (target_id, type, amount, moderator_id, timestamp)
				VALUES (?, ?, ?, ?, ?)
			''', (target_id, type, amount, moderator_id, timestamp))
			self.conn.commit() 
		except mysql.connector.Error as e:
			print(f"Error logging forceadd: {e}") #Error Log for Debuggging
		
    def log_coin(self, member_id, type, moderator, old_name, timestamp):
		try:	
			self.cursor.execute('''
				INSERT INTO Coins (member_id, type, moderator, old_name, timestamp)
				VALUES (?, ?, ?, ?, ?)
			''', (member_id, type, moderator, old_name, timestamp))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error logging Coin: {e}") #Error log for Debugging

    def get_coins(self, member_id):
		try:
			self.cursor.execute('SELECT * FROM Coins WHERE member_id = ?', (member_id,))
			rows = self.cursor.fetchall()
			# Process the fetched rows to get coin information.
			# You might want to create a list of dictionaries or objects representing each coin,
			# extracting relevant information like coin type, moderator who awarded it, etc.
		except mysql.connector.Error as e:
			print(f"Error Retreiving coins: {e}") #logging error for debugging
			return None #allow bot to exit
			

    def remove_coin(self, line_number):
		try:
			self.cursor.execute('DELETE FROM Coins WHERE id = ?', (coin_id,))
            self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error deleting coin: {e}") #error log for debugging

    def add_note_to_file(self, target_id, moderator_id, note):
		try:
			self.cursor.execute('''
				INSERT INTO ModNotes (target_id, moderator_id, note)
				VALUES (?, ?, ?)
			''', (target_id, moderator_id, note))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error adding note: {e}") #Logging error for debugging

    def get_notes(self, member_id):
        try:
			self.cursor.execute('SELECT * FROM ModNotes WHERE target_id = ?', (member_id,))
			rows = self.cursor.fetchall()
			# Process the fetched rows to get moderation notes.
			# You could create a list of dictionaries or objects representing each note,
			# including the note text, moderator who added it, and timestamp.
		except mysql.connector.Error as e:
			print(f"Error getting notes: {e}") #logging error for debugging
			return None #allow bot to exit

    def remove_note(self, note_id):
		try:
			self.cursor.execute('DELETE FROM ModNotes WHERE id = ?', (note_id,))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error removing note: {e}") #logging error for debugging
			

    def log_event(self, event):
        try:
			self.cursor.execute('''
            INSERT INTO Auditlogs (event)
            VALUES (?)
			''', (event,))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error logging Event: {e}") #Logging error for debugging
			
    def get_audit_logs(self, member_id, action_types=None):
        try:
			if action_types:
				placeholders = ', '.join(['?'] * len(action_types))
				query = f'''
					SELECT * FROM Auditlogs
					WHERE event LIKE '%' || ? || '%' 
					AND event LIKE ANY(VALUES({placeholders}))
					ORDER BY id DESC
				'''
				self.cursor.execute(query, [member_id] + action_types)
			else:
				query = '''
					SELECT * FROM Auditlogs
					WHERE event LIKE '%' || ? || '%'
					ORDER BY id DESC
				'''
				self.cursor.execute(query, (member_id,))

			rows = self.cursor.fetchall()
			# Process the fetched rows to get audit logs
			
		except mysql.connector.Error as e:
			print(f"Error fetching audit logs: {e}") #log error for debugging
			return [] #return empty list in case of error
    def toggle_award_ping(self, user_id, new_choice):
		try:
			self.cursor.execute('''
				INSERT OR REPLACE INTO Settings (user_id, award_ping_enabled)
				VALUES (?, ?)
			''', (user_id, new_choice))
			self.conn.commit()
		except mysql.connector.Error as e:
			print(f"Error changing award ping setting: {e}") #error log for debugging

    def get_award_ping_setting(self, user_id):
		try:
			self.cursor.execute('SELECT award_ping_enabled FROM Settings WHERE user_id = ?', (user_id,))
			row = self.cursor.fetchone()
			return row[0] if row else None  # Return None if no setting found
		except mysql.connector.Error as e:
			print(f"Error retreiving ping setting: {e}") #error log for debugging
			return None #allow bot to exit
			
    def add_gamertag(self, user_id, gamertag):
		try:
		self.cursor.execute('''
				INSERT OR REPLACE INTO Gamertags (user_id, gamertag)
				VALUES (?, ?)
			''', (user_id, gamertag))
		except mysql.connector.Error as e:
			print(f"Error writing Gamertag: {e}") #error log for debugging
		
	def get_gamertag(self, user_id):
		try:	
			self.cursor.execute('SELECT gamertag FROM Gamertags WHERE user_id = ?', (user_id,))
			row = self.cursor.fetchone()
			return row[0] if row else None
		except mysql.connector.Error as e:
			print(f"Error retreiving gamertag: {e}") #Error log for debugging
			return None #Exit so bot doesn't lock

    def get_timezone(self, user_id):
        try:
			self.cursor.execute('SELECT timezone FROM Timezones WHERE user_id = ?', (user_id,))
			row = self.cursor.fetchone()
			return row[0] if row else None
		except mysql.connector.Error as e:
			print(f"Error retreiving timezone: {e}") #Error log for debugging
			return None #Exit so bot doesn't lock