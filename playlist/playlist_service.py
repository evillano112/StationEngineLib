from db.connection import getConnection
from datetime import datetime

MAX_DURATIONS = {
    "30min": 30 * 60,
    "1h": 60 * 60,
    "1h30": 90 * 60,
    "2h": 120 * 60,
}

def makePlaylist(show_name, playlist_name, max_duration):
    conn = getConnection()
    cursor = conn.cursor()

    # Convert duration string to seconds
    duration_map = {
        "30min": 1800,
        "1h": 3600,
        "1h30": 5400,
        "2h": 7200
    }

    if max_duration not in duration_map:
        raise ValueError("Invalid duration")

    seconds = duration_map[max_duration]

    # Get showid
    cursor.execute(
        "SELECT showid FROM Shows WHERE name = %s",
        (show_name,)
    )

    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        raise ValueError("Show does not exist")

    showid = row[0]

    # Insert playlist
    cursor.execute("""
        INSERT INTO Playlist (showid, playlist_name, max_duration)
        VALUES (%s, %s, %s)
    """, (showid, playlist_name, seconds))

    conn.commit()
    pid = cursor.lastrowid

    cursor.close()
    conn.close()

    return pid

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

