import time

from queue_eng.queue_service import (
    get_dispatchable_items,
    count_dispatched_unplayed,
    resolve_queue_item_filepath,
    mark_dispatched,
    archive_and_remove_played_due_items,
)
from stream.liquidsoap_client import push_to_queue

# load roughly the next 30 minutes
LOOKAHEAD_SECONDS = 1800

# cap how many items we preload into Liquidsoap
MAX_PENDING_PUSHES = 8

# how often to poll for new
POLL_SECONDS = 5


def run_dispatcher():
    print("Dispatcher started")

    while True:
        try:
            # move already-played rows into archive and remove from live queue
            archive_and_remove_played_due_items()

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
                        print(f"Skipping queueid={row['queueid']} because filepath could not be resolved")
                        continue

                    response = push_to_queue(filepath)
                    mark_dispatched(row["queueid"])

                    print(f"Dispatched queueid={row['queueid']} -> {filepath}")
                    print(response.strip())

            time.sleep(POLL_SECONDS)

        except Exception as e:
            print(f"Dispatcher error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_dispatcher()