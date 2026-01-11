import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
import random

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def add_expense(conn, expense, commit=False):
    """
    Add a new expense into the expenses table
    :param conn:
    :param expense:
    :param commit: whether to commit the transaction
    :return: expense id
    """
    sql = ''' INSERT INTO expenses(date,category,amount,description,starred)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, expense)
    if commit:
        conn.commit()
    return cur.lastrowid

def get_all_expenses(conn):
    """
    Query all rows in the expenses table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses")

    rows = cur.fetchall()
    return rows

def print_all_expenses(conn):
    """
    Prints all expenses from the expenses table to the console.
    :param conn: the Connection object
    """
    expenses = get_all_expenses(conn)
    print("\n--- All Expenses in Database ---")
    if expenses:
        for expense in expenses:
            print(expense)
    else:
        print("No expenses found.")
    print("--------------------------------")

def get_starred_expenses(conn):
    """
    Query expenses by starred status
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE starred=1")

    rows = cur.fetchall()
    return rows

def get_expenses_for_graphing(conn):
    """
    Query selected columns from the expenses table and return as a list of dictionaries.
    :param conn: the Connection object
    :return: List of dictionaries with 'date', 'category', 'amount'
    """
    cur = conn.cursor()
    cur.execute("SELECT date, category, amount FROM expenses")
    rows = cur.fetchall()
    
    # Convert list of tuples to list of dictionaries
    expenses_list = []
    for row in rows:
        expenses_list.append({
            'date': row[0],
            'category': row[1],
            'amount': row[2]
        })
    return expenses_list

def get_monthly_summary(conn):
    """Returns total expenses grouped by month (YYYY-MM)."""
    cur = conn.cursor()
    cur.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) FROM expenses GROUP BY month ORDER BY month")
    return cur.fetchall()

def get_category_summary(conn):
    """Returns total expenses grouped by category."""
    cur = conn.cursor()
    cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category ORDER BY SUM(amount) DESC")
    return cur.fetchall()

def get_yearly_summary(conn):
    """Returns total expenses grouped by year (YYYY)."""
    cur = conn.cursor()
    cur.execute("SELECT strftime('%Y', date) as year, SUM(amount) FROM expenses GROUP BY year ORDER BY year")
    return cur.fetchall()

def update_expense_star(conn, expense_id, starred):
    """
    update starred status of an expense
    :param conn:
    :param expense_id:
    :param starred:
    """
    sql = ''' UPDATE expenses
              SET starred = ? 
              WHERE id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (starred, expense_id))
    conn.commit()

def delete_expense(conn, expense_id):
    """
    Delete an expense by expense id
    :param conn:  Connection to the SQLite database
    :param expense_id: id of the expense
    :return:
    """
    sql = 'DELETE FROM expenses WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (expense_id,))
    conn.commit()

def clear_all_expenses(conn):
    """
    Delete all expenses from the database.
    :param conn: Connection object
    """
    sql = 'DELETE FROM expenses'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def get_dashboard_stats(conn):
    """Returns a dictionary of key stats for the dashboard."""
    stats = {
        "total_month": 0.0,
        "total_today": 0.0,
        "top_category": "None"
    }
    cur = conn.cursor()
    
    # Total this month
    cur.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
    res = cur.fetchone()[0]
    stats["total_month"] = res if res else 0.0
    
    # Total today
    cur.execute("SELECT SUM(amount) FROM expenses WHERE date = strftime('%Y-%m-%d', 'now')")
    res = cur.fetchone()[0]
    stats["total_today"] = res if res else 0.0
    
    # Top Category
    cur.execute("SELECT category FROM expenses GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1")
    res = cur.fetchone()
    stats["top_category"] = res[0] if res else "None"
    
    return stats

def main(db_file="expense_manager.db"):
    sql_create_expenses_table = """ CREATE TABLE IF NOT EXISTS expenses (
                                        id integer PRIMARY KEY,
                                        date text NOT NULL,
                                        category text NOT NULL,
                                        amount real NOT NULL,
                                        description text,
                                        starred integer NOT NULL DEFAULT 0
                                    ); """

    # create a database connection
    conn = create_connection(db_file)

    # create tables
    if conn is not None:
        # create expenses table
        create_table(conn, sql_create_expenses_table)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()