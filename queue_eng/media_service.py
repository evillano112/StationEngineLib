from db.connection import getConnection
import random

from db.connection import getConnection
import random

def get_media(media_type, exclude_ids=None):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    if exclude_ids:
        format_strings = ','.join(['%s'] * len(exclude_ids))
        cursor.execute(f"""
            SELECT * FROM StationMedia
            WHERE media_type = %s
            AND mediaid NOT IN ({format_strings})
        """, (media_type, *exclude_ids))
    else:
        cursor.execute("""
            SELECT * FROM StationMedia
            WHERE media_type = %s
        """, (media_type,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        return None

    return random.choice(rows)