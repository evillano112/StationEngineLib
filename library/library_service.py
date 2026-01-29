def search_library():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    print("\nSearch by:")
    print("1. Title")
    print("2. Artist")
    print("3. Album")
    print("4. Tag")
    print("5. Year range")

    choice = input("Choose option: ").strip()

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

    where_clause = ""
    params = []

    if choice == "1":  # Title
        value = input("Enter title: ").strip()
        where_clause = "WHERE s.title LIKE %s"
        params.append(f"%{value}%")

    elif choice == "2":  # Artist
        value = input("Enter artist: ").strip()
        where_clause = "WHERE s.artist LIKE %s"
        params.append(f"%{value}%")

    elif choice == "3":  # Album
        value = input("Enter album: ").strip()
        where_clause = "WHERE s.album LIKE %s"
        params.append(f"%{value}%")

    elif choice == "4":  # Tag
        value = input("Enter tag: ").strip()
        where_clause = "WHERE t.tagname LIKE %s"
        params.append(f"%{value}%")

    elif choice == "5":  # Year range
        start_year = input("Start year: ").strip()
        end_year = input("End year: ").strip()
        where_clause = "WHERE s.year BETWEEN %s AND %s"
        params.extend([start_year, end_year])

    else:
        print("Invalid choice.")
        cursor.close()
        conn.close()
        return []

    sql = f"""
        {base_sql}
        {where_clause}
        ORDER BY s.artist, s.album, s.title
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        print("No results found.")
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
