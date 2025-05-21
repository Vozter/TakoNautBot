from .reminder_db import get_connection

def set_user_timezone(user_id, timezone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_settings (user_id, timezone) VALUES (%s, %s) ON DUPLICATE KEY UPDATE timezone = VALUES(timezone)",
        (user_id, timezone)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_user_timezone(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timezone FROM user_settings WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else "Asia/Jakarta"
