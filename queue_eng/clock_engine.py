from datetime import timedelta
from queue_eng.queue_builder import insert_queue_item_safe
from db.connection import getConnection
import random


def get_random_media(media_type):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT mediaid FROM StationMedia
        WHERE media_type = %s
    """, (media_type,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        return None

    return random.choice(results)["mediaid"]


def inject_legal_id(current_time):
    mediaid = get_random_media("LEGAL_ID")

    if mediaid:
        insert_queue_item_safe(
            play_time=current_time,
            media_type="MEDIA",
            mediaid=mediaid,
            source="CLOCK",
            notes="Top of hour legal ID"
        )


def inject_sweeper(current_time):
    mediaid = get_random_media("SWEEPER")

    if mediaid:
        insert_queue_item_safe(
            play_time=current_time,
            media_type="MEDIA",
            mediaid=mediaid,
            source="CLOCK",
            notes="Sweeper"
        )