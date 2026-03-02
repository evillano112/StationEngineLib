from db.connection import getConnection


def delete_song(songid: int):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT songid FROM Song WHERE songid = %s", (songid,))
        if not cursor.fetchone():
            return False, "Song does not exist"

        cursor.execute("DELETE FROM Song WHERE songid = %s", (songid,))
        conn.commit()

        return True, "Song deleted"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()


def delete_playlist(playlistid: int):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT playlistid FROM Playlist WHERE playlistid = %s",
            (playlistid,)
        )

        if not cursor.fetchone():
            return False, "Playlist does not exist"

        cursor.execute(
            "DELETE FROM Playlist WHERE playlistid = %s",
            (playlistid,)
        )

        conn.commit()
        return True, "Playlist deleted"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()


def delete_show(show_name: str):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT playlistid FROM Playlist WHERE show_name = %s",
            (show_name,)
        )

        if not cursor.fetchone():
            return False, "Show does not exist"

        cursor.execute(
            "DELETE FROM Playlist WHERE show_name = %s",
            (show_name,)
        )

        conn.commit()
        return True, "Show and associated playlists deleted"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()