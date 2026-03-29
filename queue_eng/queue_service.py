from db.connection import getConnection

# =========================
# CORE INSERT
# =========================

def insert_queue_item(play_time, media_type, songid=None, mediaid=None, source="AUTO"):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO PlaybackQueue (
            play_time,
            media_type,
            songid,
            mediaid,
            source
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (play_time, media_type, songid, mediaid, source))

    conn.commit()
    cursor.close()
    conn.close()


# =========================
# READ
# =========================

def get_upcoming_queue(limit=50):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM PlaybackQueue
        ORDER BY play_time ASC
        LIMIT %s
    """, (limit,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


def get_full_queue():
    return get_upcoming_queue(1000)


def get_queue_range(start_dt, end_dt):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM PlaybackQueue
        WHERE play_time BETWEEN %s AND %s
        ORDER BY play_time ASC
    """, (start_dt, end_dt))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


# =========================
# DELETE
# =========================

def delete_queue_item(queueid):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM PlaybackQueue
        WHERE queueid = %s
    """, (queueid,))

    conn.commit()
    cursor.close()
    conn.close()