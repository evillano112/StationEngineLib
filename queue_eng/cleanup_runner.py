from queue_eng.queue_cleanup import archive_old_queue, trim_queue_future

def run():
    ok, msg = archive_old_queue(days=2)
    print(msg)

    trim_queue_future(days_ahead=7)


if __name__ == "__main__":
    run()