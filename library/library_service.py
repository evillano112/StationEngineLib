from db.connection import getConnection

def search_library(search_type, value=None, start_year=None, end_year=None):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    base_sql = """
        SELECT DISTINCT
            s.songid,
            s.title,
            s.artist,
            s.album,
            s.year,
            sf.duration
        FROM Song s
        JOIN SongFile sf ON s.songid = sf.songid
        LEFT JOIN TagEntry te ON s.songid = te.songid
        LEFT JOIN Tags t ON te.tagid = t.tagid
    """

    params = []
    where_clause = ""

    if search_type == "title":
        where_clause = "WHERE s.title LIKE %s"
        params.append(f"{value}%")

    elif search_type == "artist":
        where_clause = "WHERE s.artist LIKE %s"
        params.append(f"%{value}%")

    elif search_type == "album":
        where_clause = "WHERE s.album LIKE %s"
        params.append(f"${value}%")

    elif search_type == "tag":
        where_clause = "WHERE t.tagname LIKE %s"
        params.append(f"%{value}%")

    elif search_type == "year":
        where_clause = "WHERE s.year BETWEEN %s AND %s"
        params.extend([start_year, end_year])

    sql = f"""
        {base_sql}
        {where_clause}
        ORDER BY s.artist, s.album, s.title
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows

def get_random_song():

    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.songid, sf.duration
        FROM Song s
        JOIN SongFile sf ON s.songid = sf.songid
        ORDER BY RAND()
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

def get_random_song_by_tag(tag):

    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT s.songid, sf.duration
        FROM Song s
        JOIN SongFile sf ON s.songid = sf.songid
        JOIN TagEntry te ON s.songid = te.songid
        JOIN Tags t ON te.tagid = t.tagid
        WHERE t.tagname = %s
        ORDER BY RAND()
        LIMIT 1
    """

    cursor.execute(sql, (tag,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row




