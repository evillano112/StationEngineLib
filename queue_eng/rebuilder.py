import time
from queue_eng.queue_builder import build_queue

EXTEND_EVERY_SECONDS = 3600

def run_rebuilder():
    print("Queue extender started")

    while True:
        try:
            build_queue(hours=72)
        except Exception as e:
            print(f"Queue extend error: {e}")

        time.sleep(EXTEND_EVERY_SECONDS)


if __name__ == "__main__":
    run_rebuilder()