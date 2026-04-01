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

HORIZON_HOURS = 72


def insert(cursor, t, media_type, songid=None, mediaid=None, source="AUTO", showid=None, notes=None):
    cursor.execute("""
        INSERT INTO PlaybackQueue
        (play_time, media_type, songid, mediaid, source, showid, notes, dispatch_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING')
    """, (t, media_type, songid, mediaid, source, showid, notes))


def get_queue_end(cursor):
    cursor.execute("""
        SELECT MAX(play_time) AS max_play_time
        FROM PlaybackQueue
        WHERE play_time >= NOW()
    """)
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def build_queue(hours=HORIZON_HOURS):
    conn = getConnection()
    cursor = conn.cursor()

    now = datetime.now().replace(microsecond=0)
    target_end = now + timedelta(hours=hours)

    queue_end = get_queue_end(cursor)
    pointer = queue_end if queue_end else now

    if pointer >= target_end:
        cursor.close()
        conn.close()
        print("Queue already extends far enough ahead.")
        return

    pools = build_rotation_pools()
    clock_index = 0

    if not any(pools.values()):
        cursor.close()
        conn.close()
        print("No songs found in library.")
        return

    # track media windows already placed
    fired_windows = set()

    while pointer < target_end:
        advanced = False

        hour_key = pointer.strftime("%Y-%m-%d %H")

        # legal id once per hour near top of hour
        if pointer.minute == 0 and pointer.second < 90:
            key = f"{hour_key}:LEGAL"
            if key not in fired_windows:
                media = get_media("LEGAL_ID")
                if media:
                    insert(cursor, pointer, "MEDIA", mediaid=media["mediaid"], source="AUTO")
                    pointer += timedelta(seconds=media["duration"] or 10)
                    fired_windows.add(key)
                    advanced = True

        if advanced:
            continue

        # sweeper windows
        sweeper_slot = None
        if (pointer.minute == 14 and pointer.second >= 30) or pointer.minute == 15 or (pointer.minute == 16 and pointer.second <= 30):
            sweeper_slot = "15"
        elif (pointer.minute == 29 and pointer.second >= 30) or pointer.minute == 30 or (pointer.minute == 31 and pointer.second <= 30):
            sweeper_slot = "30"
        elif (pointer.minute == 44 and pointer.second >= 30) or pointer.minute == 45 or (pointer.minute == 46 and pointer.second <= 30):
            sweeper_slot = "45"

        if sweeper_slot is not None:
            key = f"{hour_key}:SWEEPER:{sweeper_slot}"
            if key not in fired_windows:
                media = get_media("SWEEPER")
                if media:
                    insert(cursor, pointer, "MEDIA", mediaid=media["mediaid"], source="AUTO")
                    pointer += timedelta(seconds=media["duration"] or 10)
                    fired_windows.add(key)
                    advanced = True

        if advanced:
            continue

        show = get_active_show(pointer)

        if show:
            show_end = datetime.combine(pointer.date(), show["end_time"])

            # playlist first
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

            # then tagged show fill
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

        # regular rotation fallback
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

    print("Queue extended successfully")