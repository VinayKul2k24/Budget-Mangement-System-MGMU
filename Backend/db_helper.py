import mysql.connector
from contextlib import contextmanager
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@contextmanager
def get_db_cursor(commit=False):
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        port=3306,
        password="root",
        database="expense_manager"
    )
    cursor = connection.cursor(dictionary=True)
    yield cursor
    if commit:
        connection.commit()
    cursor.close()
    connection.close()


def create_user(username, password, role):
    hashed_pw = pwd_context.hash(password)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                       (username, hashed_pw, role))


def get_user_by_username(username):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()


def fetch_expenses_for_user_date(user_id, expense_date):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM expenses WHERE user_id = %s AND expense_date = %s", (user_id, expense_date))
        return cursor.fetchall()


def delete_expenses_for_user_date(user_id, expense_date):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM expenses WHERE user_id = %s AND expense_date = %s", (user_id, expense_date))


def insert_expense_with_user(user_id, expense_date, amount, category, notes):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO expenses (user_id, expense_date, amount, category, notes) VALUES (%s, %s, %s, %s, %s)",
            (user_id, expense_date, amount, category, notes)
        )


def fetch_expense_summary_for_user(user_id, start_date, end_date):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id = %s AND expense_date BETWEEN %s AND %s 
            GROUP BY category""",
                       (user_id, start_date, end_date))
        return cursor.fetchall()
