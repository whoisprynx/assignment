import sqlite3
from sqlite3 import Error


def establish_db_link():
    """Create a database connection using SQLite database"""
    db_link = None
    try:
        db_link = sqlite3.connect('mydatabase.db')
        print(f"Connected to SQLite, SQLite version: {sqlite3.version}")
        return db_link
    except Error as e:
        print(e)

    return db_link


def create_users_table(db):
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    );
    """
    cursor = db.cursor()
    cursor.execute(query)
    db.commit()

# Expense Table to  hold category, date range and amount and note


def generate_expenses_table(db_link):
    """Create a table for storing expenses"""
    try:
        query = ''' CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    note TEXT,
                    user_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );'''
        executor = db_link.cursor()
        executor.execute(query)
        print("Expenses table created successfully")
    except Error as e:
        print(e)

# Create


def insert_expense(db_link, expense):
    """Add a new book to the table"""
    query = '''INSERT INTO expenses(amount, date, category, note)
            VALUES(?,?,?,?)'''
    executor = db_link.cursor()
    executor.execute(query, expense)
    db_link.commit()
    return executor.lastrowid

# Read


def fetch_all_expenses(db_link):
    """Query all rows in the expenses table"""
    executor = db_link.cursor()
    executor.execute("SELECT * FROM expenses")

    records = executor.fetchall()

    for record in records:
        print(record)

# Update


def modify_expense(db_link, expense):
    """Update a expense's information"""
    query = '''UPDATE expenses
                SET amount = ?,
                    date = ?,
                    category = ?,
                    note = ?
                WHERE id = ?'''
    executor = db_link.cursor()
    executor.execute(query, expense)
    db_link.commit()

# Delete


def remove_expenses(db_link, expense_id):
    """Delete an expense by id"""
    query = 'DELETE FROM expenses WHERE id=?'
    executor = db_link.cursor()
    executor.execute(query, (expense_id,))
    db_link.commit()


def execute_program():
    # Create a database connection
    db_link = establish_db_link()

    if db_link is not None:
        # Create table
        generate_expenses_table(db_link)

        # Add expenses
        expense1 = (50.75, '2025-11-19', 'Food', 'Lunch at restaurant')
        expense2 = (120.00, '2025-11-19', 'Transport', 'Fuel for car')
        expense3 = (30.5, '2025-11-19', 'Food', 'Coffee at a café')
        expense4 = (150.00, '2025-11-20', 'Books', 'Bought a novel')
        expense5 = (500.00, '2025-11-21', 'Groceries',
                    'Weekly grocery shopping')
        expense6 = (10.00, '2025-11-22', 'Transport', 'Bus fare')
        expense7 = (450.00, '2025-11-22', 'Entertainment', 'Movie ticket')
        expense8 = (120.00, '2025-11-22', 'Utilities', 'Electricity bill')
        expense9 = (50.00, '2025-11-23', 'Health', 'Pharmacy purchase')
        expense10 = (150.00, '2025-11-23', 'Food', 'Dinner at a restaurant')
        expense11 = (200.00, '2025-11-23', 'Travel', 'Weekend getaway')
        expense12 = (300.00, '2025-11-24', 'Clothing', 'New shoes')
        exp_id1 = insert_expense(db_link, expense1)
        exp_id2 = insert_expense(db_link, expense2)
        exp_id3 = insert_expense(db_link, expense3)
        exp_id4 = insert_expense(db_link, expense4)
        exp_id5 = insert_expense(db_link, expense5)
        exp_id6 = insert_expense(db_link, expense6)
        exp_id7 = insert_expense(db_link, expense7)
        exp_id8 = insert_expense(db_link, expense8)
        exp_id9 = insert_expense(db_link, expense9)
        exp_id10 = insert_expense(db_link, expense10)
        exp_id11 = insert_expense(db_link, expense11)
        exp_id12 = insert_expense(db_link, expense12)

        print(
            f"Added expenses with IDs: {exp_id1}, {exp_id2}, {exp_id3}, {exp_id4}, {exp_id5}, {exp_id6}, {exp_id7}, {exp_id8}, {exp_id9}, {exp_id10}, {exp_id11}, {exp_id12}")

        # View all expenses
        print("\nAll expenses:")
        fetch_all_expenses(db_link)

        # Update an expense
        updated_expense = (55.00, '2025-11-20', 'Food',
                           'Lunch with dessert', exp_id1)
        modify_expense(db_link, updated_expense)
        print("\nAfter update:")
        fetch_all_expenses(db_link)

        # Delete an expense
        # remove_expense(db_link, exp_id2)
        # print("\nAfter deletion:")
        # fetch_all_expenses(db_link)

        # Close the connection
        db_link.close()
    else:
        print("Error! Cannot create the database connection.")


if __name__ == '__main__':
    execute_program()
