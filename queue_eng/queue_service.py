from db.connection import getConnection


def insert_queue_item(play_time, media_type, songid=None, mediaid=None,
                      source="AUTO", showid=None, notes=None):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO PlaybackQueue (
            play_time,
            media_type,
            songid,
            mediaid,
            source,
            showid,
            notes,
            dispatch_status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,'PENDING')
    """, (
        play_time,
        media_type,
        songid,
        mediaid,
        source,
        showid,
        notes
    ))

    conn.commit()
    cursor.close()
    conn.close()


def get_full_queue(limit=500):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            pq.queueid,
            pq.play_time,
            pq.media_type,
            pq.source,
            pq.dispatch_status,
            pq.dispatched_at,
            pq.played_at,
            s.title,
            s.artist,
            sm.name AS media_name
        FROM PlaybackQueue pq
        LEFT JOIN Song s ON pq.songid = s.songid
        LEFT JOIN StationMedia sm ON pq.mediaid = sm.mediaid
        ORDER BY pq.play_time
        LIMIT %s
    """, (limit,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_queue_range(start_dt, end_dt):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            pq.queueid,
            pq.play_time,
            pq.media_type,
            pq.source,
            pq.dispatch_status,
            pq.dispatched_at,
            pq.played_at,
            s.title,
            s.artist,
            sm.name AS media_name
        FROM PlaybackQueue pq
        LEFT JOIN Song s ON pq.songid = s.songid
        LEFT JOIN StationMedia sm ON pq.mediaid = sm.mediaid
        WHERE pq.play_time BETWEEN %s AND %s
        ORDER BY pq.play_time
    """, (start_dt, end_dt))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


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


def insert_manual_song(play_time, songid):
    insert_queue_item(
        play_time,
        "SONG",
        songid=songid,
        source="MANUAL"
    )


def insert_manual_media(play_time, mediaid):
    insert_queue_item(
        play_time,
        "MEDIA",
        mediaid=mediaid,
        source="MANUAL"
    )


def resolve_queue_item_filepath(queueid):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pq.media_type,
            sf.filepath AS song_path,
            sm.filepath AS media_path
        FROM PlaybackQueue pq
        LEFT JOIN SongFile sf ON pq.songid = sf.songid
        LEFT JOIN StationMedia sm ON pq.mediaid = sm.mediaid
        WHERE pq.queueid = %s
        LIMIT 1
    """, (queueid,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    return row["song_path"] if row["media_type"] == "SONG" else row["media_path"]


def get_dispatchable_items(lookahead_seconds=1800, limit=8):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM PlaybackQueue
        WHERE dispatch_status = 'PENDING'
          AND play_time >= NOW()
          AND play_time <= NOW() + INTERVAL %s SECOND
        ORDER BY play_time ASC
        LIMIT %s
    """, (lookahead_seconds, limit))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def count_dispatched_unplayed():
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM PlaybackQueue
        WHERE dispatch_status = 'DISPATCHED'
          AND played_at IS NULL
    """)

    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def mark_dispatched(queueid):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE PlaybackQueue
        SET dispatch_status = 'DISPATCHED',
            dispatched_at = NOW()
        WHERE queueid = %s
    """, (queueid,))

    conn.commit()
    cursor.close()
    conn.close()


def archive_and_remove_played_due_items():
    conn = getConnection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO PlaybackQueueArchive (
                queueid, play_time, media_type,
                songid, mediaid, source, showid, notes
            )
            SELECT
                queueid, play_time, media_type,
                songid, mediaid, source, showid, notes
            FROM PlaybackQueue
            WHERE dispatch_status = 'DISPATCHED'
              AND play_time <= NOW()
        """)

        cursor.execute("""
            UPDATE PlaybackQueue
            SET dispatch_status = 'PLAYED',
                played_at = NOW()
            WHERE dispatch_status = 'DISPATCHED'
              AND play_time <= NOW()
        """)

        cursor.execute("""
            DELETE FROM PlaybackQueue
            WHERE dispatch_status = 'PLAYED'
              AND played_at IS NOT NULL
        """)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()