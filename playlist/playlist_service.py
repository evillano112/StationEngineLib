from db.connection import get_connection

MAX_DURATIONS = {
    "30min": 30 * 60,
    "1h": 60 * 60,
    "1h30": 90 * 60,
    "2h": 120 * 60,
}

def create_playlist(show_name, playlist_name, max_duration_key):
    if max_duration_key not in MAX_DURATIONS:
        raise ValueError(f"Invalid max_duration_key: {max_duration_key}")

    max_duration = MAX_DURATIONS[max_duration_key]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Playlist (show_name, playlist_name, max_duration)
        VALUES (%s, %s, %s)
    """, (show_name, playlist_name, max_duration))

    playlist_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return playlist_id

def add_song_to_playlist(playlist_id, song_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT max_duration FROM Playlist WHERE playlistid = %s", (playlist_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Playlist {playlist_id} does not exist")
    max_duration = row[0]

    cursor.execute("""
        SELECT SUM(sf.duration) 
        FROM PlaylistEntry pe
        JOIN SongFile sf ON pe.songid = sf.songid
        WHERE pe.playlistid = %s
    """, (playlist_id,))
    current_duration = cursor.fetchone()[0] or 0

    cursor.execute("SELECT duration FROM SongFile WHERE songid = %s LIMIT 1", (song_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Song {song_id} does not exist")
    song_duration = row[0] or 0

    if current_duration + song_duration > max_duration:
        cursor.close()
        conn.close()
        return False

    cursor.execute("SELECT MAX(position) FROM PlaylistEntry WHERE playlistid = %s", (playlist_id,))
    next_position = (cursor.fetchone()[0] or 0) + 1

    cursor.execute("""
        INSERT INTO PlaylistEntry (playlistid, songid, position)
        VALUES (%s, %s, %s)
    """, (playlist_id, song_id, next_position))

    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_playlist_songs(playlist_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT pe.position, s.songid, s.title, s.artist, s.album, sf.duration
        FROM PlaylistEntry pe
        JOIN Song s ON pe.songid = s.songid
        JOIN SongFile sf ON s.songid = sf.songid
        WHERE pe.playlistid = %s
        ORDER BY pe.position
    """, (playlist_id,))

    songs = cursor.fetchall()
    cursor.close()
    conn.close()
    return songs
