import time
from datetime import datetime, timedelta

from queue_eng.queue_service import (
    get_next_pending_due_item,
    get_next_pending_after,
    count_dispatched_unplayed,
    resolve_queue_item_filepath,
    mark_dispatched,
    archive_and_remove_played_due_items,
)
from stream.liquidsoap_client import push_to_queue

MAX_PENDING_PUSHES = 2
POLL_SECONDS = 2


def run_dispatcher():
    print("Dispatcher started")

    while True:
        try:
            archive_and_remove_played_due_items()

            pending_count = count_dispatched_unplayed()
            room = max(0, MAX_PENDING_PUSHES - pending_count)

            if room > 0:
                now = datetime.now()

                # first: dispatch anything due now or slightly overdue
                due = get_next_pending_due_item()

                if due:
                    filepath = resolve_queue_item_filepath(due["queueid"])
                    if filepath:
                        response = push_to_queue(filepath)
                        mark_dispatched(due["queueid"])
                        print(f"Dispatched due queueid={due['queueid']} -> {filepath}")
                        print(response.strip())
                        room -= 1

                # second: optionally preload only one next item
                if room > 0:
                    nxt = get_next_pending_after(now)
                    if nxt:
                        filepath = resolve_queue_item_filepath(nxt["queueid"])
                        if filepath:
                            response = push_to_queue(filepath)
                            mark_dispatched(nxt["queueid"])
                            print(f"Preloaded next queueid={nxt['queueid']} -> {filepath}")
                            print(response.strip())

            time.sleep(POLL_SECONDS)

        except Exception as e:
            print(f"Dispatcher error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_dispatcher()