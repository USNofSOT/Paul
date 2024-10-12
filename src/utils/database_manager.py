#imports


import mysql.connector
import os

from dotenv import load_dotenv
from typing import Final





class DatabaseManager:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env
        self.DB_HOST = os.getenv('DB_HOST')
        self.DB_USER = os.getenv('DB_USER')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_NAME = os.getenv('DB_NAME')
        self.conn = mysql.connector.connect(
            host=self.DB_HOST,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            database=self.DB_NAME
        )
        self.cursor = self.conn.cursor()
        # Warning: Deprecated should use new database manager instead
        # self.create_tables()

    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    event TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS coins (
                    coin_id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    target_id BIGINT,
                    coin_type TINYTEXT,
                    moderator_id BIGINT,
                    old_name TINYTEXT,
                    coin_time TIMESTAMP
                    )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS force_add (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    target_id BIGINT,
                    add_type TINYTEXT,
                    amount INTEGER,
                    moderator_id BIGINT,
                    add_time TIMESTAMP
                    )
                    ''')


            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS hosted (
                    log_id BIGINT PRIMARY KEY,
                    host_id BIGINT,
                    log_time TIMESTAMP
                    )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS mod_notes (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    target_id BIGINT,
                    moderator_id BIGINT,
                    note TEXT,
                    note_time TIMESTAMP,
                    hidden BOOLEAN DEFAULT FALSE,
                    who_hid TINYTEXT,
                    hide_time TIMESTAMP
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sailor (
                    discord_id BIGINT PRIMARY KEY,
                    gamertag TINYTEXT,
                    timezone TINYTEXT,
                    award_ping_enabled BOOLEAN DEFAULT TRUE,
                    carpenter_points INTEGER DEFAULT 0,
                    flex_points INTEGER DEFAULT 0,
                    cannoneer_points INTEGER DEFAULT 0,
                    helm_points INTEGER DEFAULT 0,
                    grenadier_points INTEGER DEFAULT 0,
                    surgeon_points INTEGER DEFAULT 0,
                    voyage_count INTEGER DEFAULT 0,
                    hosted_count INTEGER DEFAULT 0,
                    force_carpenter_points INTEGER DEFAULT 0,
                    force_flex_points INTEGER DEFAULT 0,
                    force_cannoneer_points INTEGER DEFAULT 0,
                    force_helm_points INTEGER DEFAULT 0,
                    force_grenadier_points INTEGER DEFAULT 0,
                    force_surgeon_points INTEGER DEFAULT 0,
                    force_voyage_count INTEGER DEFAULT 0,
                    force_hosted_count INTEGER DEFAULT 0
                    )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subclasses (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    author_id BIGINT,
                    log_link TINYTEXT,
                    target_id BIGINT,
                    subclass TINYTEXT,
                    log_time TIMESTAMP
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS voyages (
                    log_id BIGINT,
                    participant_id BIGINT,
                    log_time TIMESTAMP,
                    PRIMARY KEY (log_id, participant_id)
                )
            ''')

            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error creating tables: {e}")

    # Database Queries
    def get_audit_logs(self, member_id, action_types=None):
        raise NotImplemented

    def get_award_ping_setting(self, user_id):
        try:
            self.cursor.execute('SELECT award_ping_enabled FROM sailor WHERE discord_id = %s', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None  # Return None if no setting is found
        except mysql.connector.Error as e:
            print(f"Error retrieving ping setting: {e}")
            return None

    def get_coins(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM coins WHERE target_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get coin information.
            # You might want to create a list of dictionaries or objects representing each coin,
            # extracting relevant information like coin type, moderator who awarded it, etc.
            return rows  # Return fetched rows or processed data
        except mysql.connector.Error as e:
            print(f"Error retrieving coins: {e}")
            return None

    def get_hosted_info(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM hosted WHERE target_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to calculate hosted voyage info (similar to your existing logic)
        except mysql.connector.Error as e:
            print(f"Error fetching hosted info: {e}")
            return None

    def get_notes(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM mod_notes WHERE target_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get moderation notes.
            # You could create a list of dictionaries or objects representing each note,
            # including the note text, moderator who added it, and timestamp.
            return rows  # Return fetched rows or processed data
        except mysql.connector.Error as e:
            print(f"Error getting notes: {e}")
            return None

    def get_subclass_points(self, member_id):
        try:
            self.cursor.execute('''
                SELECT subclass, SUM(subclass_count) 
                FROM subclasses 
                WHERE target_id = %s
                GROUP BY subclass
            ''', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to get subclass points for each subclass
        except mysql.connector.Error as e:
            print(f"Error fetching subclass info: {e}")
            return None

    def get_voyage_info(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM voyages WHERE target_id = %s', (member_id,))
            rows = self.cursor.fetchall()
            # Process the fetched rows to calculate voyage info
        except mysql.connector.Error as e:
            print(f"Error fetching voyage info: {e}")
            return None

    # Database Writes
    def add_gamertag(self, user_id, gamertag):
        """adds a gamertag to a members sailor info
        Args:
            user_id (int): The DiscordID of the Sailor
            gamertag(TINYTEXT): The gamertag to add
        """
        try:
            self.cursor.execute('''
                INSERT INTO sailor (discord_id, gamertag)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE gamertag = VALUES(gamertag)
            ''', (user_id, gamertag))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error writing Gamertag: {e}")

    def add_note_to_file(self, target_id, moderator_id, note, note_time):
        """adds a modnote to notes table
               Args:
                   target_id (int): The DiscordID of the Sailor getting the note
                   moderator_id(int): The DiscordID of the moderator
                   note(text): The note to add
                   note_time(TIMESTAMP): Time of the note being added
                   Remaining fields are set by default in this table
               """

        try:
            self.cursor.execute('''
                INSERT INTO mod_notes (target_id, moderator_id, note, note_time, hidden, who_hid, hide_time)
                VALUES (%s, %s, %s, %s, FALSE, NULL, NULL)
            ''', (target_id, moderator_id, note))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error adding note: {e}")

    def hide_note(self, note_id, who_hid, hide_time):
        """Hides a note by setting its hidden value to 1 and updating who_hid and hide_time.

        Args:
            note_id (int): The ID of the note to hide.
            who_hid (int): The user ID of the person who hid the note.
            hide_time (datetime): The timestamp when the note was hidden.
        """
        try:
            self.cursor.execute('''
                UPDATE mod_notes 
                SET hidden = 1, who_hid = ?, hide_time = ? 
                WHERE id = ?
            ''', (who_hid, hide_time, note_id))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error hiding note in database: {e}")

    def log_coin(self, target_id, coin_type, moderator_id, old_name, coin_time):
        """adds a coin to the coins table
               Args:
                   target_id (int): The DiscordID of the Sailor getting the coin
                   coin_type (TINYTEXT): the type of coin
                   moderator_id(int): The DiscordID of the moderator giving the coin
                   old_name (TINYTEXT):
                   coin_time(TIMESTAMP): Time of the coin being added

               """

        try:
            self.cursor.execute('''
                INSERT INTO coins (target_id, coin_type, moderator_id, old_name, coin_time)
                VALUES (%s, %s, %s, %s, %s)
            ''', (target_id, coin_type, moderator_id, old_name, coin_time))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error logging Coin: {e}")

    def log_event(self, event):
        raise NotImplemented
        """
        
        try:
            self.cursor.execute('''
                INSERT INTO audit_logs (event)
                VALUES (%s)
            ''', (event,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error logging Event: {e}")

    def log_forceadd(self, target_id, type, amount, moderator_id, timestamp):
        try:
            self.cursor.execute('''
                INSERT INTO force_add (target_id, type, amount, moderator_id, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            ''', (target_id, type, amount, moderator_id, timestamp))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error logging force_add: {e}")
        """

    def log_hosted_data(self, log_id, host_id, log_time):
        """
        Adds a hosting record for a new voyage. If a record with the same log_id exists,
        it updates the host_id and log_time. Also increments the host's hosted_count.

        Args:
            log_id (int): voyage post id
            host_id (int): DiscordID of the host
            log_time (timestamp): time of the log posting
        """
        try:
            # Check if a record with the given log_id already exists
            self.cursor.execute("SELECT COUNT(*) FROM hosted WHERE log_id = %s", (log_id,))
            record_exists = self.cursor.fetchone()[0] > 0

            if not record_exists:
                # Insert a new record if no duplicates are found
                self.cursor.execute('''
                    INSERT INTO hosted (log_id, target_id, log_time) 
                    VALUES (%s, %s, %s)
                ''', (log_id, host_id, log_time))

                # Check if the discord_id exists in sailor
                self.cursor.execute("SELECT COUNT(*) FROM sailor WHERE discord_id = %s", (host_id,))
                host_exists = self.cursor.fetchone()[0] > 0

                if not host_exists:
                    # Insert a new record in sailor with hosted_count = 1
                    self.cursor.execute('''
                                    INSERT INTO sailor (discord_id, hosted_count) 
                                    VALUES (%s, 1)
                                ''', (host_id,))
                else:
                    # Increment hosted_count in sailor
                    self.cursor.execute('''
                                    UPDATE sailor 
                                    SET hosted_count = hosted_count + 1 
                                    WHERE discord_id = %s
                                ''', (host_id,))
                self.conn.commit()

        except mysql.connector.Error as e:
            print(f"Error logging hosted data: {e}")



    def log_voyage_data(self, log_id, participant_id, log_time):  # New function
        try:
            self.cursor.execute('''
                INSERT INTO voyages (log_id, target_id, log_time) 
                VALUES (%s, %s, %s)
            ''', (log_id, participant_id, log_time))

            # Check if the participant_id exists in sailor
            self.cursor.execute("SELECT COUNT(*) FROM sailor WHERE discord_id = %s", (participant_id,))
            participant_exists = self.cursor.fetchone()[0] > 0

            if not participant_exists:
                # Insert a new record in sailor with voyage_count = 1
                self.cursor.execute('''
                                               INSERT INTO sailor (discord_id, voyage_count) 
                                               VALUES (%s, 1)
                                           ''', (participant_id,))
            else:
                # Increment voyage_count in sailor
                self.cursor.execute('''
                                               UPDATE sailor 
                                               SET voyage_count = voyage_count + 1 
                                               WHERE discord_id = %s
                                           ''', (participant_id,))
            self.conn.commit()

        except mysql.connector.Error as e:
            print(f"Error logging voyage data: {e}")

    def voyage_log_entry_exists(self, log_id, participant_id):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM voyages WHERE log_id = %s AND target_id = %s",
                                (log_id, participant_id))
            count = self.cursor.fetchone()[0]
            return count > 0
        except mysql.connector.Error as e:
            print(f"Error checking voyages entry existence: {e}")
            return False

    def hosted_log_id_exists(self, log_id):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM hosted WHERE log_id = %s", (log_id,))
            count = self.cursor.fetchone()[0]
            return count > 0  # Returns True if log_id exists, False otherwise
        except mysql.connector.Error as e:
            print(f"Error checking log_id existence: {e}")
            return False  # Handle the error appropriately (e.g., return False)


    def log_subclasses(self, author_id, log_id, target_id, subclass, log_time):
        """
        Adds a subclass record for a member. If a record with the same target_id,
        subclass, and log_link exists, the write action is ignored to prevent duplicates.

        Args:
            author_id (int): Discord ID of the person adding the subclass record.
            log_id (int): Link to the Discord message (log) for the subclass entry.
            target_id (int): Discord ID of the member receiving the subclass entry.
            subclass (str): Name of the subclass (e.g., "Carpenter", "Flex").
            log_time (datetime): Time of the subclass entry.
        """
        try:
            # Check if a record with the same target_id, subclass, and log_link already exists
            self.cursor.execute('''
                SELECT COUNT(*) FROM subclasses 
                WHERE target_id = %s AND subclass = %s AND log_id = %s
            ''', (target_id, subclass, log_id))
            record_exists = self.cursor.fetchone()[0] > 0

            if not record_exists:
                # Insert a new record if no duplicates are found
                self.cursor.execute('''
                    INSERT INTO subclasses (author_id, log_id, target_id, subclass, log_time)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (author_id, log_id, target_id, subclass, log_time) )
                self.conn.commit()

        except mysql.connector.Error as e:
            print(f"Error logging subclasses: {e}")

    def log_voyage_data(self, log_id, participant_id, log_time):
        """
        Adds a voyage record for a member. If a record with the same log_id and
        target_id exists, the write action is ignored to prevent duplicates.

        Args:
            log_id (int): voyage post id
            participant_id (int): DiscordID of the member who participated in the voyage
            log_time (timestamp): time of the voyage log
        """
        try:
            # Check if a record with the same log_id and target_id already exists
            self.cursor.execute('''
                SELECT COUNT(*) FROM voyages 
                WHERE log_id = %s AND target_id = %s
            ''', (log_id, participant_id))
            record_exists = self.cursor.fetchone()[0] > 0

            if not record_exists:
                # Insert a new record if no duplicates are found
                self.cursor.execute('''
                    INSERT INTO voyages (log_id, target_id, log_time)
                    VALUES (%s, %s, %s)
                ''', (log_id, participant_id, log_time))
                self.conn.commit()

        except mysql.connector.Error as e:
            print(f"Error logging voyage data: {e}")

    def remove_coin(self, coin_id):
        """Removes a challenge coin from the coins table in the database.

        Args:
            coin_id (int): The ID of the coin to remove.
        """
        try:
            self.cursor.execute('DELETE FROM coins WHERE coin_id = %s', (coin_id,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error deleting coin: {e}")

    def batch_log_voyage_data(self, voyage_data):
        """
        Batch inserts voyage records. Ignores duplicates based on log_id and participant_id.

        Args:
            voyage_data (list): A list of tuples, where each tuple contains (log_id, participant_id, log_time)
        """
        try:
            if voyage_data:  # Only execute if there's data to insert
                self.cursor.executemany("""
                    INSERT IGNORE INTO voyages (log_id, target_id, log_time)
                    VALUES (%s, %s, %s)
                """, voyage_data)
                self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error batch logging voyage data: {e}")

    def toggle_award_ping(self, discord_id, new_choice):
        """Toggles the award ping notification setting for a user.

        Args:
            discord_id (int): The Discord ID of the user.
            new_choice (bool): The new setting for award ping notifications (True/False).
        """
        try:
            self.cursor.execute('''
                INSERT INTO sailor (discord_id, award_ping_enabled)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE award_ping_enabled = VALUES(award_ping_enabled)
            ''', (discord_id, new_choice))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error changing award ping setting: {e}")

    def increment_voyage_count(self, discord_id):
        """
        Increments the voyage_count for the given discord_id in the sailor table.

        Args:
            discord_id (int): The Discord ID of the user.
        """
        try:
            self.cursor.execute("""
                UPDATE sailor 
                SET voyage_count = voyage_count + 1 
                WHERE discord_id = %s
            """, (discord_id,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error incrementing voyage_count: {e}")

    def remove_voyage_log_entry(self, log_id, participant_id):
        """
        Removes a specific entry from the voyages table based on log_id and participant_id.
        This is used for edits where not all logs need to be deleted.

        Args:
            log_id (int): The ID of the voyage log.
            participant_id (int): The Discord ID of the participant.
        """
        try:
            self.cursor.execute("DELETE FROM voyages WHERE log_id = %s AND target_id = %s",
                                (log_id, participant_id))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error removing voyage log entry: {e}")


    #update member database work

    def discord_id_exists(self, discord_id):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM sailor WHERE discord_id = %s", (discord_id,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except mysql.connector.Error as e:
            print(f"Error checking discord_id existence: {e}")
            return False

    def add_discord_id(self, discord_id):
        try:
            self.cursor.execute("INSERT IGNORE INTO sailor (discord_id) VALUES (%s)", (discord_id,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error adding discord_id: {e}")

    #Removal of voyage logs and hosted logs as needed

    def decrement_count(self, discord_id, count_type):
        """
        Decrements the specified count for the given discord_id in the sailor table.

        Args:
            discord_id (int): The Discord ID of the user.
            count_type (str): The type of count to decrement ("hosted_count" or "voyage_count").
        """
        try:
            self.cursor.execute(f"""
                UPDATE sailor 
                SET {count_type} = GREATEST({count_type} - 1, 0)  -- Prevent negative counts
                WHERE discord_id = %s
            """, (discord_id,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error decrementing {count_type}: {e}")

    def remove_voyage_log_entries(self, log_id):
        """
        Removes entries from the voyages table associated with the given log_id.
        This is used when a log is fully deleted.

        Args:
            log_id (int): The ID of the voyage log to remove.
        """
        try:
            self.cursor.execute("DELETE FROM voyages WHERE log_id = %s", (log_id,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error removing voyage log entries: {e}")

    def remove_hosted_entry(self, log_id):
        """
        Removes the entry from the hosted table associated with the given log_id.

        Args:
            log_id (int): The ID of the hosted voyage to remove.
        """
        try:
            self.cursor.execute("DELETE FROM hosted WHERE log_id = %s", (log_id,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error removing hosted entry: {e}")