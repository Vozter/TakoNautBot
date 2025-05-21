import mysql.connector
from datetime import datetime, timedelta
import pytz

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "aSSaMYbALpGe42zR",  # set yours
    "database": "takonaut"
}

def get_connection():
    return mysql.connector.connect(**db_config)

def add_reminder(chat_id, user_id, text, run_at, recurrence="once"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (chat_id, user_id, remind_text, run_at, recurrence) VALUES (%s, %s, %s, %s, %s)",
        (chat_id, user_id, text, run_at, recurrence)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_due_reminders():
    now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reminders WHERE run_at <= %s AND recurrence = 'once'", (now_utc,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def delete_reminder(reminder_id, chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = %s AND chat_id = %s", (reminder_id, chat_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_reminders_by_chat(chat_id):
    now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, remind_text, run_at, recurrence FROM reminders WHERE chat_id = %s AND run_at > %s ORDER BY run_at",
        (chat_id, now_utc)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def delete_reminder_by_id(reminder_id, chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = %s AND chat_id = %s", (reminder_id, chat_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def get_recurring_reminders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reminders WHERE recurrence != 'once'")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
