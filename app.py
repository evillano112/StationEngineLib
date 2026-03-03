import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent))

from library.library_service import search_library
from importer import import_song_mysql
from playlist.playlist_service import create_playlist, search_playlists
from playlist import playlist_service

from library.tag_service import create_tag
from library.song_edit_service import edit_song, add_tag_to_song
from library.delete_service import (
    delete_song,
    delete_playlist,
    delete_show
)
from playlist.show_service import create_show, search_shows

def normalize_path(p):
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
    print("7. Create new tag")
    print("8. Edit song")
    print("9. Add tag to song")
    print("10. Delete song")
    print("11. Delete playlist")
    print("12. Delete show")
    print("13. Create show")
    print("14. Search playlists")
    print("15. Search shows")
    print("0. Exit")


def print_all_songs():
    rows = search_library("title",value="")
    for song in rows:
        dur = song["duration"] or 0
        minutes = dur // 60
        seconds = dur % 60

        print(
            f'{song["songid"]:>4} | '
            f'{song["artist"]} - {song["title"]} '
            f'[{minutes}:{seconds:02}]'
        )

def print_all_playlists():
    rows = playlist_service.search_playlists("","")

    if not rows:
        print("No playlists found")
    else:
        print("\nPlaylists:\n")
        for p in rows:
            print(
                f'{p["playlistid"]:>3} | '
                f'{p["show_name"]} - {p["playlist_name"]}'
            )

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

    print("\nResults:\n")

    for song in rows:
        dur = song["duration"] or 0
        minutes = dur // 60
        seconds = dur % 60

        print(
            f'{song["songid"]:>4} | '
            f'{song["artist"]} - {song["title"]} '
            f'[{minutes}:{seconds:02}]'
        )

def cli_create_playlist():
    print("\nAvailable Shows:")
    shows = search_shows()

    if not shows:
        print("No shows available.")
        return

    for s in shows:
        print(f"{s['showid']} | {s['name']}")

    name = input("\nEnter playlist name: ").strip()
    show_id = input("Enter Show ID for this playlist: ").strip()

    if not show_id.isdigit():
        print("Invalid Show ID.")
        return

    # Ask for max duration
    print("Select max duration: 30min, 1h, 1h30, 2h")
    duration_input = input("Enter max duration: ").strip().lower()

    # Convert to seconds
    duration_map = {
        "30min": 30 * 60,
        "1h": 60 * 60,
        "1h30": 90 * 60,
        "2h": 120 * 60
    }

    if duration_input not in duration_map:
        print("Invalid duration option.")
        return

    max_duration = duration_map[duration_input]

    # Call service to create playlist
    success = create_playlist(name, int(show_id), max_duration)

    if success:
        print("Playlist created successfully.")
    else:
        print("Show not found or playlist could not be created.")

def main():
    while True:
        printMenu()
        choice = input("Choose an option: ").strip()

        # Import single song
        if choice == "1":
            rawPath = input("Enter path to audio file: ")
            if rawPath:
                filepath = normalize_path(rawPath)

                if not filepath.exists():
                    print("File does not exist")
                    continue

                success, msg, _ = import_song_mysql.import_song(filepath)
                print(msg)

        # Import incoming folder
        elif choice == "2":
            results = import_song_mysql.importIncomingFiles()
            if not results:
                print("No files imported.")
            else:
                for r in results:
                    print(f'{r["file"]}: {r["message"]}')

        # Search
        elif choice == "3":
            cli_search()

        # Create playlist
        elif choice == "4":
            print("\n--- Create Playlist ---")

            cli_create_playlist()


        # Add song to playlist
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

        # View playlist
        elif choice == "6":
            playlistid = input("Playlist ID: ").strip()

            try:
                songs = playlist_service.getPlaylistSongs(int(playlistid))
            except Exception as e:
                print(f"Error: {e}")
                continue

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

        # Create tag
        elif choice == "7":
            tagname = input("Enter new tag name: ").strip()
            success, message = create_tag(tagname)
            print(message)

        # Edit song
        elif choice == "8":
            try:
                songid = int(input("Song ID: ").strip())
            except ValueError:
                print("Invalid song ID")
                continue

            print("Leave blank to keep current value")

            title = input("New title: ").strip()
            artist = input("New artist: ").strip()
            album = input("New album: ").strip()
            year = input("New year: ").strip()
            track = input("New track number: ").strip()

            success, message = edit_song(
                songid,
                title=title if title else None,
                artist=artist if artist else None,
                album=album if album else None,
                year=int(year) if year else None,
                tracknumber=int(track) if track else None
            )

            print(message)

        # Add tag to song
        elif choice == "9":
            print_all_songs()
            try:
                songid = int(input("Song ID: ").strip())
            except ValueError:
                print("Invalid song ID")
                continue

            tagname = input("Tag name to add: ").strip()
            success, message = add_tag_to_song(songid, tagname)
            print(message)

        # Delete song
        elif choice == "10":
            print_all_songs()
            try:
                songid = int(input("Song ID to delete: ").strip())
            except ValueError:
                print("Invalid song ID")
                continue

            success, message = delete_song(songid)
            print(message)

        # Delete playlist
        elif choice == "11":
            print_all_playlists()
            try:
                playlistid = int(input("Playlist ID to delete: ").strip())
            except ValueError:
                print("Invalid playlist ID")
                continue

            success, message = delete_playlist(playlistid)
            print(message)


        # Delete show
        elif choice == "12":
            shows = search_shows()
            for s in shows:
                print(f"{s['showid']} | {s['name']}")
            show_id = input("Show id to delete: ").strip()
            success, message = delete_show(show_id)
            print(message)

        # Create show
        elif choice == "13":
            name = input("Show name: ").strip()
            start_time = input("Start time (HH:MM:SS): ").strip()
            end_time = input("End time (HH:MM:SS): ").strip()

            print("Frequency options:")
            print("weekly, biweekly, monthly, one_time")
            frequency = input("Frequency: ").strip()

            day_of_week = None
            specific_date = None
            repeat_until = None
            is_indefinite = False

            if frequency in ("weekly", "biweekly"):
                day_of_week = input(
                    "Day of week (monday-sunday): "
                ).strip().lower()

                indefinite = input("Repeat indefinitely? (y/n): ").strip().lower()
                if indefinite == "y":
                    is_indefinite = True
                else:
                    repeat_until = input("Repeat until (YYYY-MM-DD): ").strip()

            elif frequency == "monthly":
                day_of_week = input(
                    "Day of week (for now): "
                ).strip().lower()

                indefinite = input("Repeat indefinitely? (y/n): ").strip().lower()
                if indefinite == "y":
                    is_indefinite = True
                else:
                    repeat_until = input("Repeat until (YYYY-MM-DD): ").strip()

            elif frequency == "one_time":
                specific_date = input("Specific date (YYYY-MM-DD): ").strip()

            else:
                print("Invalid frequency")
                continue

            success, message = create_show(
                name=name,
                start_time=start_time,
                end_time=end_time,
                frequency=frequency,
                day_of_week=day_of_week,
                specific_date=specific_date,
                repeat_until=repeat_until,
                is_indefinite=is_indefinite
            )

            print(message)

        elif choice == "14":
            name = input("Playlist name (blank to skip): ").strip()
            show = input("Show name (blank to skip): ").strip()

            rows = playlist_service.search_playlists(
                name=name if name else None,
                show=show if show else None
            )

            if not rows:
                print("No playlists found")
            else:
                print("\nPlaylists:\n")
                for p in rows:
                    print(
                        f'{p["playlistid"]:>3} | '
                        f'{p["show_name"]} - {p["playlist_name"]}'
                    )

        elif choice == "15":
            name = input("Show name (blank to list all): ").strip()

            rows = search_shows(name if name else None)

            if not rows:
                print("No shows found")
            else:
                print("\nShows:\n")
                for s in rows:
                    schedule = ""

                    if s["frequency"] == "one_time":
                        schedule = f'on {s["specific_date"]}'
                    else:
                        schedule = f'{s["frequency"]} on {s["day_of_week"]}'

                        if s["is_indefinite"]:
                            schedule += " (indefinite)"
                        elif s["repeat_until"]:
                            schedule += f' until {s["repeat_until"]}'

                    print(
                        f'{s["showid"]:>3} | {s["name"]} '
                        f'[{s["start_time"]}-{s["end_time"]}] '
                        f'| {schedule}'
                    )
        # Exit
        elif choice == "0":
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()