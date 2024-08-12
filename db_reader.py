import sqlite3

# Path to your SQLite database
DATABASE_PATH = 'instance/site.db'

def connect_db():
    """ Connect to the SQLite database. """
    return sqlite3.connect(DATABASE_PATH)

def execute_query(query, params=()):
    """ Execute a query and return the results. """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def show_all_users():
    """ Fetch and display all users from the database. """
    query = "SELECT * FROM user;"
    users = execute_query(query)
    for user in users:
        print(user)

def main():
    """ Main function to read and display data. """
    print("Fetching all users from the database...")
    show_all_users()

if __name__ == '__main__':
    main()
