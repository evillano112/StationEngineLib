import time
from db.connection import getConnection
import socket

LIQ_HOST = "localhost"
LIQ_PORT = 1234  # Liquidsoap telnet port (we enable below)

def send_to_liquidsoap(filepath):
    cmd = f"request.push {filepath}\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((LIQ_HOST, LIQ_PORT))
        s.send(cmd.encode("utf-8"))

def get_next_queue_item():
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT q.*, sf.filepath, sm.filepath AS media_path
        FROM PlaybackQueue q
        LEFT JOIN SongFile sf ON q.songid = sf.songid
        LEFT JOIN StationMedia sm ON q.mediaid = sm.mediaid
        WHERE q.play_time <= NOW()
        ORDER BY q.play_time
        LIMIT 1
    """)

    item = cursor.fetchone()

    if item:
        cursor.execute("DELETE FROM PlaybackQueue WHERE queueid = %s", (item["queueid"],))
        conn.commit()

    cursor.close()
    conn.close()
    return item


def run_streamer():
    print("Scheduler running...")

    while True:
        try:
            item = get_next_queue_item()

            if not item:
                time.sleep(2)
                continue

            filepath = item["filepath"] or item["media_path"]

            if not filepath:
                continue

            print("Queueing:", filepath)
            send_to_liquidsoap(filepath)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)