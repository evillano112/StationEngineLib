import sys
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from stream.liquidsoap_client import push_to_queue
sys.path.append(str(Path(__file__).parent))

from queue_eng.queue_builder import build_queue
from queue_eng.queue_service import (
    get_full_queue,
    get_queue_range,
    insert_manual_song,
    insert_manual_media,
    delete_queue_item,
)
from queue_eng.queue_cleanup import archive_old_queue, trim_queue_future

from library.library_service import search_library
from importer import import_song_mysql
from playlist.playlist_service import create_playlist
from playlist import playlist_service
from playlist.show_service import create_show, search_shows

from library.tag_service import create_tag
from library.song_edit_service import edit_song, add_tag_to_song
from library.delete_service import (
    delete_song,
    delete_playlist,
    delete_show,
)

try:
    from queue_eng.import_station_media import (
        import_station_media as import_media_file,
        import_incoming_ids,
        import_incoming_sweepers,
    )
except Exception as e:
    print(f"Failed to load station media importer: {e}")
    import_media_file = None
    import_incoming_ids = None
    import_incoming_sweepers = None

LIQ_PROCESS = None
DISPATCHER_PROCESS = None
LIQ_HOST = "localhost"
LIQ_PORT = 1234
LIQ_FILE = "radio_with_telnet.liq"


def normalize_path(p):
    p = p.strip().strip('"').strip("'")
    return Path(p)


def start_liquidsoap():
    global LIQ_PROCESS

    if LIQ_PROCESS and LIQ_PROCESS.poll() is None:
        print("Liquidsoap is already running")
        return

    try:
        LIQ_PROCESS = subprocess.Popen(["liquidsoap", LIQ_FILE])
        print(f"Started Liquidsoap with {LIQ_FILE}")
    except Exception as e:
        print(f"Failed to start Liquidsoap: {e}")


def stop_liquidsoap():
    global LIQ_PROCESS

    if LIQ_PROCESS and LIQ_PROCESS.poll() is None:
        LIQ_PROCESS.terminate()
        print("Stopped Liquidsoap")
    else:
        print("Liquidsoap is not running")


def start_dispatcher():
    global DISPATCHER_PROCESS

    if DISPATCHER_PROCESS and DISPATCHER_PROCESS.poll() is None:
        print("Dispatcher is already running")
        return

    try:
        DISPATCHER_PROCESS = subprocess.Popen([sys.executable, "-m", "queue_eng.dispatcher"])
        print("Started dispatcher")
    except Exception as e:
        print(f"Failed to start dispatcher: {e}")


def stop_dispatcher():
    global DISPATCHER_PROCESS

    if DISPATCHER_PROCESS and DISPATCHER_PROCESS.poll() is None:
        DISPATCHER_PROCESS.terminate()
        print("Stopped dispatcher")
    else:
        print("Dispatcher is not running")


def liquidsoap_request(filepath):
    try:
        response = push_to_queue(filepath)
        print("Liquidsoap response:", response.strip())
        print("Pushed to Liquidsoap")
    except Exception as e:
        print(f"Liquidsoap push failed: {e}")


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
    print("16. Build 3-day queue")
    print("17. View full queue")
    print("18. View queue range")
    print("19. Insert song into queue")
    print("20. Insert media into queue")
    print("21. Delete queue item")
    print("22. Start Liquidsoap")
    print("23. Stop Liquidsoap")
    print("24. Start dispatcher")
    print("25. Stop dispatcher")
    print("26. Push live track")
    print("27. Cleanup old queue")
    print("28. Trim future queue")
    print("29. Import legal ID by file path")
    print("30. Import sweeper by file path")
    print("31. Import all incoming IDs")
    print("32. Import all incoming sweepers")
    print("0. Exit")


def print_all_songs():
    rows = search_library("title", value="")
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
    rows = playlist_service.search_playlists("", "")

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

    print("Select max duration: 30min, 1h, 1h30, 2h")
    duration_input = input("Enter max duration: ").strip().lower()

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

    success = create_playlist(name, int(show_id), max_duration)

    if success:
        print("Playlist created successfully.")
    else:
        print("Show not found or playlist could not be created.")


def main():
    while True:
        printMenu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            rawPath = input("Enter path to audio file: ")
            if rawPath:
                filepath = normalize_path(rawPath)

                if not filepath.exists():
                    print("File does not exist")
                    continue

                success, msg, _ = import_song_mysql.import_song(filepath)
                print(msg)

        elif choice == "2":
            results = import_song_mysql.importIncomingFiles()
            if not results:
                print("No files imported.")
            else:
                for r in results:
                    if isinstance(r, dict):
                        print(f'{r.get("file")}: {r.get("message")}')
                    else:
                        print(r)

        elif choice == "3":
            cli_search()

        elif choice == "4":
            print("\n--- Create Playlist ---")
            cli_create_playlist()

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

        elif choice == "7":
            tagname = input("Enter new tag name: ").strip()
            success, message = create_tag(tagname)
            print(message)

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

        elif choice == "10":
            print_all_songs()
            try:
                songid = int(input("Song ID to delete: ").strip())
            except ValueError:
                print("Invalid song ID")
                continue

            success, message = delete_song(songid)
            print(message)

        elif choice == "11":
            print_all_playlists()
            try:
                playlistid = int(input("Playlist ID to delete: ").strip())
            except ValueError:
                print("Invalid playlist ID")
                continue

            success, message = delete_playlist(playlistid)
            print(message)

        elif choice == "12":
            shows = search_shows()
            for s in shows:
                print(f"{s['showid']} | {s['name']}")
            show_id = input("Show id to delete: ").strip()
            success, message = delete_show(show_id)
            print(message)


        elif choice == "13":

            name = input("Show name: ").strip()

            start_time = input("Start time (HH:MM:SS, must be :00 or :30): ").strip()

            end_time = input("End time (HH:MM:SS, must be :00 or :30): ").strip()

            def valid_half_hour(t):

                try:

                    dt = datetime.strptime(t, "%H:%M:%S")

                    return dt.minute in (0, 30) and dt.second == 0

                except ValueError:

                    return False

            if not valid_half_hour(start_time):
                print("Invalid start time. Use HH:00:00 or HH:30:00.")

                continue

            if not valid_half_hour(end_time):
                print("Invalid end time. Use HH:00:00 or HH:30:00.")

                continue

            if start_time >= end_time:
                print("End time must be after start time.")

                continue

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

        elif choice == "16":
            build_queue(hours=72)
            print("Queue built for 3 days.")

        elif choice == "17":
            rows = get_full_queue()

            for r in rows:
                if r["media_type"] == "SONG":
                    print(f'{r["queueid"]} | {r["play_time"]} | {r.get("dispatch_status")} | {r["artist"]} - {r["title"]}')
                else:
                    print(f'{r["queueid"]} | {r["play_time"]} | {r.get("dispatch_status")} | MEDIA: {r["media_name"]}')

        elif choice == "18":
            start = input("Start datetime (YYYY-MM-DD HH:MM:SS): ")
            end = input("End datetime (YYYY-MM-DD HH:MM:SS): ")

            rows = get_queue_range(start, end)

            for r in rows:
                if r["media_type"] == "SONG":
                    print(f'{r["queueid"]} | {r["play_time"]} | {r.get("dispatch_status")} | {r["artist"]} - {r["title"]}')
                else:
                    print(f'{r["queueid"]} | {r["play_time"]} | {r.get("dispatch_status")} | MEDIA: {r["media_name"]}')

        elif choice == "19":
            play_time = input("Play time (YYYY-MM-DD HH:MM:SS): ")
            songid = int(input("Song ID: "))
            insert_manual_song(play_time, songid)
            print("Inserted song into queue.")

        elif choice == "20":
            play_time = input("Play time (YYYY-MM-DD HH:MM:SS): ")
            mediaid = int(input("Media ID: "))
            insert_manual_media(play_time, mediaid)
            print("Inserted media into queue.")

        elif choice == "21":
            queueid = int(input("Queue ID to delete: "))
            delete_queue_item(queueid)
            print("Deleted.")

        elif choice == "22":
            start_liquidsoap()

        elif choice == "23":
            stop_liquidsoap()

        elif choice == "24":
            start_dispatcher()

        elif choice == "25":
            stop_dispatcher()

        elif choice == "26":
            raw_path = input("Path to audio file: ")
            filepath = normalize_path(raw_path)

            if not filepath.exists():
                print("File does not exist")
                continue

            liquidsoap_request(str(filepath.resolve()))

        elif choice == "27":
            ok, msg = archive_old_queue(2)
            print(msg)

        elif choice == "28":
            trim_queue_future(7)
            print("Trimmed future queue")

        elif choice == "29":
            if import_media_file is None:
                print("Station media importer not available")
                continue

            raw_path = input("Path to legal ID file: ")
            filepath = normalize_path(raw_path)

            if not filepath.exists():
                print("File does not exist")
                continue

            ok, msg, mediaid = import_media_file(filepath, "LEGAL_ID")
            print(msg)

        elif choice == "30":
            if import_media_file is None:
                print("Station media importer not available")
                continue

            raw_path = input("Path to sweeper file: ")
            filepath = normalize_path(raw_path)

            if not filepath.exists():
                print("File does not exist")
                continue

            ok, msg, mediaid = import_media_file(filepath, "SWEEPER")
            print(msg)

        elif choice == "31":
            if import_incoming_ids is None:
                print("Station media importer not available")
                continue

            results = import_incoming_ids()
            if not results:
                print("No incoming IDs imported.")
            else:
                for r in results:
                    if isinstance(r, dict):
                        print(f'{r.get("file")}: {r.get("message")}')
                    else:
                        print(r)

        elif choice == "32":
            if import_incoming_sweepers is None:
                print("Station media importer not available")
                continue

            results = import_incoming_sweepers()
            if not results:
                print("No incoming sweepers imported.")
            else:
                for r in results:
                    if isinstance(r, dict):
                        print(f'{r.get("file")}: {r.get("message")}')
                    else:
                        print(r)

        elif choice == "0":
            stop_dispatcher()
            stop_liquidsoap()
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()