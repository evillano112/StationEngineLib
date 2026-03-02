from db.connection import getConnection
from library.tag_service import create_tag
from datetime import datetime

def create_show(
    name,
    start_time,
    end_time,
    frequency,
    day_of_week=None,
    specific_date=None,
    repeat_until=None,
    is_indefinite=False
):
    conn = getConnection()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO Shows (
                name,
                start_time,
                end_time,
                frequency,
                day_of_week,
                specific_date,
                repeat_until,
                is_indefinite
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(sql, (
            name,
            start_time,
            end_time,
            frequency,
            day_of_week,
            specific_date,
            repeat_until,
            is_indefinite
        ))

        conn.commit()

        # Automatically create tag with show name
        create_tag(name)

        return True, "Show created successfully"

    except Exception as e:
        return False, f"Error creating show: {e}"

    finally:
        cursor.close()
        conn.close()

def search_shows(name=None):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            showid,
            name,
            start_time,
            end_time,
            frequency,
            day_of_week,
            specific_date,
            repeat_until,
            is_indefinite
        FROM Shows
    """

    params = []

    if name:
        sql += " WHERE name LIKE %s"
        params.append(f"%{name}%")

    sql += " ORDER BY start_time"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows