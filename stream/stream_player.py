import subprocess
import time
from datetime import datetime
from queue_eng.queue_service import get_upcoming_queue
from db.connection import getConnection

ICECAST_URL = "icecast://charlie:Ruden06516@wnhu-stream1.newhaven.edu:8050/stationengine"
POLL_INTERVAL = 2  # seconds


def play_file(filepath):
    return subprocess.Popen([
        "ffmpeg",
        "-re",
        "-i", filepath,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "192k",
        "-f", "mp3",
        ICECAST_URL
    ])


def resolve_filepath(item):
    """
    Resolve filepath depending on SONG or MEDIA
    """
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    if item["media_type"] == "SONG":
        cursor.execute("""
            SELECT filepath FROM SongFile
            WHERE songid = %s
            LIMIT 1
        """, (item["songid"],))

    else:
        cursor.execute("""
            SELECT filepath FROM StationMedia
            WHERE mediaid = %s
        """, (item["mediaid"],))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row["filepath"] if row else None


def wait_until(play_time):
    while True:
        now = datetime.now()
        diff = (play_time - now).total_seconds()

        if diff <= 0:
            break

        time.sleep(min(diff, 1))


def stream_from_queue():
    print("Starting queue_eng-based streaming...")

    current_proc = None

    while True:
        queue = get_upcoming_queue(limit=10)

        if not queue:
            print("Queue empty, waiting...")
            time.sleep(3)
            continue

        for item in queue:
            play_time = item["play_time"]

            print(f"Waiting for: {play_time}")
            wait_until(play_time)

            filepath = resolve_filepath(item)

            if not filepath:
                print("Missing file, skipping...")
                continue

            print(f"Playing: {filepath}")

            if current_proc:
                current_proc.terminate()

            current_proc = play_file(filepath)

        time.sleep(POLL_INTERVAL)

def resilient_stream():
    while True:
        try:
            stream_from_queue()
        except Exception as e:
            print(f"Stream crashed: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)