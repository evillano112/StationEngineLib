import socket
import time

from queue_eng.queue_service import (
    get_dispatchable_items,
    count_dispatched_unplayed,
    resolve_queue_item_filepath,
    mark_dispatched,
    mark_played_due_items,
)

LIQ_HOST = "localhost"
LIQ_PORT = 1234
LOOKAHEAD_SECONDS = 900
MAX_PENDING_PUSHES = 5
POLL_SECONDS = 5


def push_to_liquidsoap(filepath):
    cmd = f"request.push {filepath}\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((LIQ_HOST, LIQ_PORT))
        s.sendall(cmd.encode("utf-8"))


def run_dispatcher():
    print("Dispatcher started")

    while True:
        try:
            mark_played_due_items()

            pending_count = count_dispatched_unplayed()
            room = max(0, MAX_PENDING_PUSHES - pending_count)

            if room > 0:
                due_items = get_dispatchable_items(
                    lookahead_seconds=LOOKAHEAD_SECONDS,
                    limit=room
                )

                for row in due_items:
                    filepath = resolve_queue_item_filepath(row["queueid"])

                    if not filepath:
                        continue

                    push_to_liquidsoap(filepath)
                    mark_dispatched(row["queueid"])
                    print(f"Dispatched queueid={row['queueid']} -> {filepath}")

            time.sleep(POLL_SECONDS)

        except Exception as e:
            print("Dispatcher error:", e)
            time.sleep(5)


if __name__ == "__main__":
    run_dispatcher()