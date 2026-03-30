from db.connection import getConnection

def export_playlist(path="playlist.txt"):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            CASE
                WHEN pq.media_type='SONG' THEN sf.filepath
                ELSE sm.filepath
            END AS filepath
        FROM PlaybackQueue pq
        LEFT JOIN SongFile sf ON pq.songid = sf.songid
        LEFT JOIN StationMedia sm ON pq.mediaid = sm.mediaid
        ORDER BY pq.play_time
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    with open(path, "w") as f:
        for r in rows:
            if r["filepath"]:
                f.write(r["filepath"] + "\n")

    print("Playlist exported")