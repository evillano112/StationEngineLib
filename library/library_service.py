from db.connection import getConnection

def searchLibrary():
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    print("\nSearch by:")
    print("1. Title")
    print("2. Artist")
    print("3. Album")
    print("4. Tag")
    print("5. Year range")

    choice = input("Choose option: ").strip()

    sqlbase = """
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

    whereClause = ""
    params = []

    if choice == "1":  # Title
        value = input("Enter title: ").strip()
        whereClause = "WHERE s.title LIKE %s"
        params.append(f"%{value}%")

    elif choice == "2":  # Artist
        value = input("Enter artist: ").strip()
        whereClause = "WHERE s.artist LIKE %s"
        params.append(f"%{value}%")

    elif choice == "3":  # Album
        value = input("Enter album: ").strip()
        whereClause = "WHERE s.album LIKE %s"
        params.append(f"%{value}%")

    elif choice == "4":  # Tag
        value = input("Enter tag: ").strip()
        whereClause = "WHERE t.tagname LIKE %s"
        params.append(f"%{value}%")

    elif choice == "5":  # Year range
        startYear = input("Start year: ").strip()
        endYear = input("End year: ").strip()
        whereClause = "WHERE s.year BETWEEN %s AND %s"
        params.extend([startYear, endYear])

    else:
        print("Invalid choice")
        cursor.close()
        conn.close()
        return []

    sql = f"""
        {sqlbase}
        {whereClause}
        ORDER BY s.artist, s.album, s.title
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        print("No results found")
        return []

    print("\nResults:")
    for r in rows:
        dur = r["duration"] or 0
        minutes = dur // 60
        seconds = dur % 60
        year = r["year"] or "----"

        print(
            f'{r["songid"]:>4} | {r["artist"]} - {r["title"]} '
            f'({r["album"]}, {year}) [{minutes}:{seconds:02}]'
        )

    return rows
