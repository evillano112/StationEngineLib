from datetime import datetime, timedelta
from db.connection import getConnection

from queue_eng.music_selector import (
    build_rotation_pools,
    get_next_rotation_song,
    get_next_show_song,
)
from queue_eng.media_service import get_media
from queue_eng.show_logic import get_active_show
from queue_eng.playlist_logic import get_playlist_for_show, get_playlist_songs

GUARD_MINUTES = 30


def insert(cursor, t, media_type, songid=None, mediaid=None, source="AUTO", showid=None):
    cursor.execute("""
        INSERT INTO PlaybackQueue
        (play_time, media_type, songid, mediaid, source, showid, dispatch_status)
        VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
    """, (t, media_type, songid, mediaid, source, showid))


def clear_future_pending(cursor, guard_minutes=GUARD_MINUTES):
    cursor.execute("""
        DELETE FROM PlaybackQueue
        WHERE play_time > NOW() + INTERVAL %s MINUTE
          AND dispatch_status = 'PENDING'
    """, (guard_minutes,))


def build_queue(hours=72):
    conn = getConnection()
    cursor = conn.cursor()

    print("clearing future pending queue rows")
    clear_future_pending(cursor)
    conn.commit()

    now = datetime.now().replace(microsecond=0)
    build_start = now + timedelta(minutes=GUARD_MINUTES)
    end = now + timedelta(hours=hours)
    pointer = build_start

    pools = build_rotation_pools()
    clock_index = 0

    if not any(pools.values()):
        cursor.close()
        conn.close()
        print("No songs found in library.")
        return

    while pointer < end:
        advanced = False

        # top-of-hour legal ID window
        if pointer.minute == 0 and pointer.second < 90:
            media = get_media("LEGAL_ID")
            if media:
                insert(cursor, pointer, "MEDIA", mediaid=media["mediaid"], source="AUTO")
                pointer += timedelta(seconds=media["duration"] or 10)
                advanced = True

        if advanced:
            continue

        # quarter-hour sweepers with wider windows
        if (
            (pointer.minute == 14 and pointer.second >= 30) or
            (pointer.minute == 15) or
            (pointer.minute == 16 and pointer.second <= 30) or
            (pointer.minute == 29 and pointer.second >= 30) or
            (pointer.minute == 30) or
            (pointer.minute == 31 and pointer.second <= 30) or
            (pointer.minute == 44 and pointer.second >= 30) or
            (pointer.minute == 45) or
            (pointer.minute == 46 and pointer.second <= 30)
        ):
            media = get_media("SWEEPER")
            if media:
                insert(cursor, pointer, "MEDIA", mediaid=media["mediaid"], source="AUTO")
                pointer += timedelta(seconds=media["duration"] or 10)
                advanced = True

        if advanced:
            continue

        show = get_active_show(pointer)

        if show:
            show_end = datetime.combine(pointer.date(), show["end_time"])

            pid = get_playlist_for_show(show["showid"])
            if pid:
                songs = get_playlist_songs(pid)
                for s in songs:
                    dur = s["duration"] or 180
                    if pointer + timedelta(seconds=dur) > show_end:
                        break

                    insert(
                        cursor,
                        pointer,
                        "SONG",
                        songid=s["songid"],
                        source="PLAYLIST",
                        showid=show["showid"]
                    )
                    pointer += timedelta(seconds=dur)
                    advanced = True

            if advanced:
                continue

            show_song = get_next_show_song(show["name"])
            if show_song:
                dur = show_song["duration"] or 180
                if pointer + timedelta(seconds=dur) <= show_end:
                    insert(
                        cursor,
                        pointer,
                        "SONG",
                        songid=show_song["songid"],
                        source="SHOW",
                        showid=show["showid"]
                    )
                    pointer += timedelta(seconds=dur)
                    advanced = True

            if advanced:
                continue

        song = get_next_rotation_song(pools, clock_index)
        clock_index += 1

        if song:
            dur = song["duration"] or 180
            insert(cursor, pointer, "SONG", songid=song["songid"], source="AUTO")
            pointer += timedelta(seconds=dur)
            advanced = True

        if not advanced:
            pointer += timedelta(seconds=60)

    conn.commit()
    cursor.close()
    conn.close()

    print("Queue built successfully")