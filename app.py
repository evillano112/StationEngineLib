import sys
from pathlib import Path

from library.library_service import search_library

sys.path.append(str(Path(__file__).parent))

from importer import import_song_mysql
from playlist import playlist_service
from db.connection import getConnection


def normalize_path(p):
    # fix windows paths
    
    p = p.strip().strip('"').strip("'")
    return Path(p)


def printMenu():
    print("\n--- Station Engine CLI ---")
    print("1. Import single song")
    print("2. Import all incoming songs")
    print("3. Search library")
    print("4. Create playlist")
    print("5. Add song to playlist")
    print("6. View playlist songs")
    print("7. Delete Something")
    print("8. Exit")



def cli_search():
    print("\nSearch by:")
    print("1. Title")
    print("2. Artist")
    print("3. Album")
    print("4. Tag")
    print("5. Year range")

    choice = input("Choose option: ").strip()

    if choice == "1":
        value = input("Enter title: ")
        rows = search_library("title", value=value)

    elif choice == "2":
        value = input("Enter artist: ")
        rows = search_library("artist", value=value)

    elif choice == "3":
        value = input("Enter album: ")
        rows = search_library("album", value=value)

    elif choice == "4":
        value = input("Enter tag: ")
        rows = search_library("tag", value=value)

    elif choice == "5":
        start = input("Start year: ")
        end = input("End year: ")
        rows = search_library("year", start_year=start, end_year=end)

    else:
        print("Invalid choice")
        return

    if not rows:
        print("No results found")
        return

    for r in rows:
        dur = r["duration"] or 0
        print(f'{r["songid"]:>4} | {r["artist"]} - {r["title"]} [{dur//60}:{dur%60:02}]')





def main():
    while True:
        printMenu()
        choice = input("Choose an option: ").strip()

        # -----------------------
        # Import single song
        # -----------------------
        if choice == "1":

            rawPath = input("Enter path to audio file: ")

            if rawPath != "":
                filepath = normalize_path(rawPath)
                if not filepath.exists():
                    print("File does not exist")
                    continue
                import_song_mysql.insertSong(filepath)

        # -----------------------
        # Batch import incoming
        # -----------------------
        elif choice == "2":
            import_song_mysql.importIncomingFiles()

        # -----------------------
        # Search library
        # -----------------------
        elif choice == "3":
            cli_search()

        # -----------------------
        # Create playlist
        # -----------------------
        elif choice == "4":
            show = input("Show name: ").strip()
            name = input("Playlist name: ").strip()

            print("Durations: 30min, 1h, 1h30, 2h")
            dur = input("Max duration: ").strip()

            try:
                pid = playlist_service.makePlaylist(show, name, dur)
                print(f"Playlist created (ID: {pid})")
            except Exception as e:
                print(f"Error: {e}")

        # -----------------------
        # Add song to playlist
        # -----------------------
        elif choice == "5":
            playlistid = input("Playlist ID: ").strip()
            songid = input("Song ID: ").strip()

            try:
                ok = playlist_service.addSongToPlaylist(
                    int(playlistid),
                    int(songid)
                )
                if ok:
                    print("Song added to playlist")
                else:
                    print("Cannot add song: playlist duration exceeded")
            except Exception as e:
                print(f"Error: {e}")

        # -----------------------
        # View playlist
        # -----------------------
        elif choice == "6":
            playlistid = input("Playlist ID: ").strip()

            songs = playlist_service.getPlaylistSongs(int(playlistid))
            if not songs:
                print("Playlist is empty or does not exist")
                continue

            print("\nPlaylist contents:")
            for s in songs:
                dur = s["duration"] or 0
                print(
                    f'{s["position"]:>2}. {s["artist"]} - {s["title"]} '
                    f'[{dur//60}:{dur%60:02}]'
                )

        # -----------------------
        # Delete Song/Playlist
        # -----------------------

        # -----------------------
        # Exit
        # -----------------------
        elif choice == "8":
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
