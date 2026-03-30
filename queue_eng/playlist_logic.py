from db.connection import getConnection

def get_playlist_for_show(showid):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT playlistid
        FROM Playlist
        WHERE showid = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (showid,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    return row["playlistid"] if row else None


def get_playlist_songs(pid):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT pe.songid, sf.duration
        FROM PlaylistEntry pe
        JOIN SongFile sf ON pe.songid = sf.songid
        WHERE pe.playlistid = %s
        ORDER BY pe.position
    """, (pid,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return rows