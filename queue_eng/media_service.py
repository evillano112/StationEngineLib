from db.connection import getConnection
import random

def get_media_by_type(media_type):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

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


def get_legal_id():
    return get_media_by_type("LEGAL_ID")


def get_sweeper():
    return get_media_by_type("SWEEPER")


def get_promo():
    return get_media_by_type("PROMO")