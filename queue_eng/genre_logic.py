from db.connection import getConnection
from datetime import datetime

def get_active_genre(current_dt: datetime):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    day = current_dt.strftime("%A").lower()
    time_str = current_dt.strftime("%H:%M:%S")

    cursor.execute("""
        SELECT * FROM GenreSchedule
        WHERE day_of_week = %s
        AND start_time <= %s
        AND end_time >= %s
        LIMIT 1
    """, (day, time_str, time_str))

    row = cursor.fetchone()

    cursor.close()
    conn.close()
    return row["genre"] if row else None