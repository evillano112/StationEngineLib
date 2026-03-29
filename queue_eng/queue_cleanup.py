from db.connection import getConnection
from datetime import datetime, timedelta


def archive_old_queue(days=2):
    """
    Move queue_eng items older than X days into archive
    """

    conn = getConnection()
    cursor = conn.cursor()

    cutoff = datetime.now() - timedelta(days=days)

    try:
        # -----------------------
        # 1. COPY TO ARCHIVE
        # -----------------------
        cursor.execute("""
            INSERT INTO PlaybackQueueArchive (
                queueid, play_time, media_type,
                songid, mediaid, source, showid, notes
            )
            SELECT 
                queueid, play_time, media_type,
                songid, mediaid, source, showid, notes
            FROM PlaybackQueue
            WHERE play_time < %s
        """, (cutoff,))

        # -----------------------
        # 2. DELETE FROM ACTIVE
        # -----------------------
        cursor.execute("""
            DELETE FROM PlaybackQueue
            WHERE play_time < %s
        """, (cutoff,))

        conn.commit()

        return True, f"Archived + deleted items older than {days} days"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()

def trim_queue_future(days_ahead=7):
    """
    Prevent queue_eng from building too far ahead
    """

    conn = getConnection()
    cursor = conn.cursor()

    cutoff = datetime.now() + timedelta(days=days_ahead)

    cursor.execute("""
        DELETE FROM PlaybackQueue
        WHERE play_time > %s
    """, (cutoff,))

    conn.commit()
    cursor.close()
    conn.close()