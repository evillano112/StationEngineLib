from db.connection import getConnection
from datetime import datetime

MAX_DURATIONS = {
    "30min": 30 * 60,
    "1h": 60 * 60,
    "1h30": 90 * 60,
    "2h": 120 * 60,
}

def create_playlist(name, show_id):
    conn = getConnection()
    cursor = conn.cursor()

    # Validate show exists
    cursor.execute("SELECT ShowID FROM shows WHERE ShowID = %s", (show_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return False

    sql = """
        INSERT INTO Playlist (name, showid)
        VALUES (%s, %s)
    """

    cursor.execute(sql, (name, show_id))
    conn.commit()

    cursor.close()
    conn.close()
    return True

def addSongToPlaylist(playlistid, songid):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("SELECT max_duration FROM Playlist WHERE playlistid = %s", (playlistid,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Playlist {playlistid} does not exist")
    max_duration = row[0]

    cursor.execute("""
        SELECT SUM(sf.duration) 
        FROM PlaylistEntry pe
        JOIN SongFile sf ON pe.songid = sf.songid
        WHERE pe.playlistid = %s
    """, (playlistid,))
    current_duration = cursor.fetchone()[0] or 0

    cursor.execute("SELECT duration FROM SongFile WHERE songid = %s LIMIT 1", (songid,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Song {songid} does not exist")
    song_duration = row[0] or 0

    if current_duration + song_duration > max_duration:
        cursor.close()
        conn.close()
        return False

    cursor.execute("SELECT MAX(position) FROM PlaylistEntry WHERE playlistid = %s", (playlistid,))
    nextposition = (cursor.fetchone()[0] or 0) + 1

    cursor.execute("""
        INSERT INTO PlaylistEntry (playlistid, songid, position)
        VALUES (%s, %s, %s)
    """, (playlistid, songid, nextposition))

    conn.commit()
    cursor.close()
    conn.close()
    return True

def getPlaylistSongs(playlistid):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT pe.position, s.songid, s.title, s.artist, s.album, sf.duration
        FROM PlaylistEntry pe
        JOIN Song s ON pe.songid = s.songid
        JOIN SongFile sf ON s.songid = sf.songid
        WHERE pe.playlistid = %s
        ORDER BY pe.position
    """, (playlistid,))

    songs = cursor.fetchall()
    cursor.close()
    conn.close()
    return songs

def search_playlists(name=None, show=None):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            p.playlistid,
            p.playlist_name,
            p.max_duration,
            p.created_at,
            s.name AS show_name
        FROM Playlist p
        JOIN Shows s ON p.showid = s.showid
    """

    params = []
    conditions = []

    if name:
        conditions.append("p.playlist_name LIKE %s")
        params.append(f"%{name}%")

    if show:
        conditions.append("s.name LIKE %s")
        params.append(f"%{show}%")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY p.created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows

