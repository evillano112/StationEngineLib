from db.connection import getConnection


def edit_song(
    songid: int,
    title=None,
    artist=None,
    album=None,
    year=None,
    tracknumber=None
):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT songid FROM Song WHERE songid = %s", (songid,))
        if not cursor.fetchone():
            return False, "Song does not exist"

        updates = []
        params = []

        if title is not None:
            updates.append("title = %s")
            params.append(title)

        if artist is not None:
            updates.append("artist = %s")
            params.append(artist)

        if album is not None:
            updates.append("album = %s")
            params.append(album)

        if year is not None:
            updates.append("year = %s")
            params.append(year)

        if tracknumber is not None:
            updates.append("tracknumber = %s")
            params.append(tracknumber)

        if updates:
            sql = f"""
                UPDATE Song
                SET {', '.join(updates)}
                WHERE songid = %s
            """
            params.append(songid)
            cursor.execute(sql, params)
            conn.commit()

        return True, "Song updated"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()


def add_tag_to_song(songid: int, tagname: str):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        # check song exists
        cursor.execute("SELECT songid FROM Song WHERE songid = %s", (songid,))
        if not cursor.fetchone():
            return False, "Song does not exist"

        # get tagid
        cursor.execute("SELECT tagid FROM Tags WHERE tagname = %s", (tagname,))
        row = cursor.fetchone()

        if not row:
            return False, "Tag does not exist"

        tagid = row["tagid"]

        # insert relation
        cursor.execute(
            "INSERT IGNORE INTO TagEntry (songid, tagid) VALUES (%s, %s)",
            (songid, tagid)
        )

        conn.commit()
        return True, "Tag added to song"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()