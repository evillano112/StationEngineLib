import sys
from pathlib import Path

# Ensure project root is in path (important on Windows)
sys.path.append(str(Path(__file__).parent))

from importer import import_song_mysql
from playlist import playlist_service
from db.connection import get_connection


def normalize_path(p):
    """
    Fix Windows paths pasted with quotes or backslashes.
    """
    p = p.strip().strip('"').strip("'")
    return Path(p)


def print_menu():
    print("\n--- Station Engine CLI ---")
    print("1. Import single song")
    print("2. Import all incoming songs")
    print("3. Search library")
    print("4. Create playlist")
    print("5. Add song to playlist")
    print("6. View playlist songs")
    print("7. Exit")


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




def main():
    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        # -----------------------
        # Import single song
        # -----------------------
        if choice == "1":
            raw_path = input("Enter path to audio file: ")
            filepath = normalize_path(raw_path)

            if not filepath.exists():
                print("File does not exist.")
                continue

            import_song_mysql.insert_song(filepath)

        # -----------------------
        # Batch import incoming
        # -----------------------
        elif choice == "2":
            import_song_mysql.import_incoming_files()

        # -----------------------
        # Search library
        # -----------------------
        elif choice == "3":
            search_library()

        # -----------------------
        # Create playlist
        # -----------------------
        elif choice == "4":
            show = input("Show name: ").strip()
            name = input("Playlist name: ").strip()
            print("Durations: 30min, 1h, 1h30, 2h")
            dur = input("Max duration: ").strip()

            try:
                pid = playlist_service.create_playlist(show, name, dur)
                print(f"Playlist created (ID: {pid})")
            except Exception as e:
                print(f"Error: {e}")

        # -----------------------
        # Add song to playlist
        # -----------------------
        elif choice == "5":
            playlist_id = input("Playlist ID: ").strip()
            song_id = input("Song ID: ").strip()

            try:
                ok = playlist_service.add_song_to_playlist(
                    int(playlist_id),
                    int(song_id)
                )
                if ok:
                    print("Song added to playlist.")
                else:
                    print("Cannot add song: playlist duration exceeded.")
            except Exception as e:
                print(f"Error: {e}")

        # -----------------------
        # View playlist
        # -----------------------
        elif choice == "6":
            playlist_id = input("Playlist ID: ").strip()

            songs = playlist_service.get_playlist_songs(int(playlist_id))
            if not songs:
                print("Playlist is empty or does not exist.")
                continue

            print("\nPlaylist contents:")
            for s in songs:
                dur = s["duration"] or 0
                print(
                    f'{s["position"]:>2}. {s["artist"]} - {s["title"]} '
                    f'[{dur//60}:{dur%60:02}]'
                )

        # -----------------------
        # Exit
        # -----------------------
        elif choice == "7":
            print("Goodbye.")
            sys.exit(0)

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
