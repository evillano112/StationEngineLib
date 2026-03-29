import sys
from pathlib import Path
from datetime import datetime

from stream.liquidsoap_controller import start_liquidsoap, stop_liquidsoap

sys.path.append(str(Path(__file__).parent))

# ----------------------------
# QUEUE SYSTEM (FIXED)
# ----------------------------
from queue_eng.queue_builder import build_queue
from queue_eng.queue_service import (
    get_full_queue,
    get_queue_range,
    delete_queue_item
)

from queue_eng.clock_engine import inject_legal_id, inject_sweeper

# ----------------------------
# LIBRARY
# ----------------------------
from library.library_service import search_library
from importer import import_song_mysql

# ----------------------------
# PLAYLIST / SHOW SYSTEM
# ----------------------------
from playlist.playlist_service import create_playlist
from playlist import playlist_service
from playlist.show_service import create_show, search_shows

from library.tag_service import create_tag
from library.song_edit_service import edit_song, add_tag_to_song

from library.delete_service import (
    delete_song,
    delete_playlist,
    delete_show
)

# ----------------------------
# STREAM CONTROL (LIQUIDSOAP)
# ----------------------------
import socket

LIQ_HOST = "localhost"
LIQ_PORT = 1234


# ============================
# HELPERS
# ============================

def normalize_path(p):
    return Path(p.strip().strip('"').strip("'"))


def liquidsoap_request(filepath):
    """
    Inject a track directly into Liquidsoap queue_eng
    (LIVE override / manual insert)
    """
    try:
        cmd = f"request.push {filepath}\n"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LIQ_HOST, LIQ_PORT))
            s.send(cmd.encode())
    except Exception as e:
        print("Liquidsoap inject failed:", e)


# ============================
# UI
# ============================

def printMenu():
    print("\n--- Station Engine CLI (LIQUIDSOAP MODE) ---")
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
    print("16. Build queue_eng (3 days)")
    print("17. View full queue_eng")
    print("18. View queue_eng range")
    print("19. Insert song into queue_eng")
    print("20. Insert media into queue_eng")
    print("21. Delete queue_eng item")
    print("22. Inject legal ID")
    print("23. Inject sweeper")
    print("24. PUSH LIVE TRACK (Liquidsoap)")
    print("25. Cleanup queue_eng")
    print("26. Stop stream")
    print("0. Exit")


# ============================
# MAIN
# ============================

def main():

    while True:
        printMenu()
        choice = input("Choose: ").strip()

        # -------------------
        # IMPORT SONG
        # -------------------
        if choice == "1":
            path = normalize_path(input("Path: "))
            if not path.exists():
                print("File not found")
                continue

            success, msg, _ = import_song_mysql.import_song(path)
            print(msg)

        # -------------------
        # IMPORT BATCH
        # -------------------
        elif choice == "2":
            results = import_song_mysql.importIncomingFiles()
            for r in results:
                print(r)

        # -------------------
        # SEARCH
        # -------------------
        elif choice == "3":
            term = input("Search: ")
            rows = search_library("title", value=term)
            for s in rows:
                print(s["songid"], s["artist"], s["title"])

        # -------------------
        # BUILD QUEUE
        # -------------------
        elif choice == "16":
            build_queue(hours=72)
            print("Queue built (3 days)")

        # -------------------
        # VIEW QUEUE
        # -------------------
        elif choice == "17":
            rows = get_full_queue()
            for r in rows:
                print(r)

        # -------------------
        # RANGE QUEUE
        # -------------------
        elif choice == "18":
            start = input("Start: ")
            end = input("End: ")
            rows = get_queue_range(start, end)
            for r in rows:
                print(r)

        # -------------------
        # MANUAL INSERT
        # -------------------
        elif choice == "19":
            t = input("Time: ")
            sid = int(input("Song ID: "))
            insert_manual_song(t, sid)

        elif choice == "20":
            t = input("Time: ")
            mid = int(input("Media ID: "))
            insert_manual_media(t, mid)

        # -------------------
        # DELETE
        # -------------------
        elif choice == "21":
            qid = int(input("Queue ID: "))
            delete_queue_item(qid)

        # -------------------
        # CLOCK ELEMENTS
        # -------------------
        elif choice == "22":
            inject_legal_id(datetime.now())

        elif choice == "23":
            inject_sweeper(datetime.now())

        # -------------------
        # 🔥 LIVE LIQUIDSOAP INJECTION
        # -------------------
        elif choice == "24":
            msg = start_liquidsoap()
            print(msg)

        # -------------------
        # CLEANUP
        # -------------------
        elif choice == "25":
            from queue_eng.queue_cleanup import archive_old_queue
            ok, msg = archive_old_queue(2)
            print(msg)

        elif choice == "26":
            msg = stop_liquidsoap()
            print(msg)
        # -------------------
        # EXIT
        # -------------------
        elif choice == "0":
            sys.exit(0)

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()