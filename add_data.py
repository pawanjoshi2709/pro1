import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('instance/site.db')  # Use forward slashes for file path
cursor = conn.cursor()

# Add the new column 'otp' to the 'user' table
cursor.execute('ALTER TABLE user ADD COLUMN otp_expiry DATETIME')

# Commit the changes and close the connection
conn.commit()
conn.close()
