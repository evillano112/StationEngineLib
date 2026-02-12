from db.connection import getConnection

MAX_DURATIONS = {
    "30min": 30 * 60,
    "1h": 60 * 60,
    "1h30": 90 * 60,
    "2h": 120 * 60,
}

def makePlaylist(showName, playlistName, maxDurationKey):
    if maxDurationKey not in MAX_DURATIONS:
        raise ValueError(f"Invalid maxDurationKey: {maxDurationKey}")

    maxDuration = MAX_DURATIONS[maxDurationKey]
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Playlist (showName, playlistName, maxDuration)
        VALUES (%s, %s, %s)
    """, (showName, playlistName, maxDuration))

    playlistid = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return playlistid

def addSongToPlaylist(playlistid, songid):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute("SELECT maxduration FROM Playlist WHERE playlistid = %s", (playlistid,))
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

# def deletePlaylist():