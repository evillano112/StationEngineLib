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

def delete_show(show_id: int):
    try:
        conn = getConnection()
        cursor = conn.cursor()

        # Check if the show exists
        cursor.execute("SELECT showid FROM shows WHERE showid = %s", (show_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, f"Show with ID {show_id} does not exist."

        # Delete the show
        cursor.execute("DELETE FROM shows WHERE showid = %s", (show_id,))
        conn.commit()

        cursor.close()
        conn.close()
        return True, f"Show with ID {show_id} deleted successfully."

    except Exception as e:
        return False, f"Error deleting show: {e}"