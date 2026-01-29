# library/library_service.py

from db.connection import get_connection
from library.models import SongView

def search_songs(artist=None, album=None, title=None, tag=None, limit=100):
    """
    Search songs with optional filters.
    Returns a list of SongView objects.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Base query
    query = """
    SELECT s.songid, s.title, s.artist, s.album, sf.duration,
           GROUP_CONCAT(t.tagname) AS tags
    FROM Song s
    JOIN SongFile sf ON s.songid = sf.songid
    LEFT JOIN TagEntry te ON s.songid = te.songid
    LEFT JOIN Tags t ON te.tagid = t.tagid
    WHERE 1=1
    """
    params = []

    # Filters
    if artist:
        query += " AND s.artist LIKE %s"
        params.append(f"%{artist}%")
    if album:
        query += " AND s.album LIKE %s"
        params.append(f"%{album}%")
    if title:
        query += " AND s.title LIKE %s"
        params.append(f"%{title}%")
    if tag:
        query += " AND t.tagname = %s"
        params.append(tag)

    query += """
    GROUP BY s.songid
    ORDER BY s.artist, s.title
    LIMIT %s
    """
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        tags = row["tags"].split(",") if row["tags"] else []
        song = SongView(
            songid=row["songid"],
            title=row["title"],
            artist=row["artist"],
            album=row["album"],
            duration=row["duration"],
            tags=tags
        )
        result.append(song)

    cursor.close()
    conn.close()
    return result
