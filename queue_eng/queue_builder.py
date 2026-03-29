from datetime import datetime, timedelta
from queue_eng.show_logic import get_active_show
from queue_eng.music_selector import get_songs_for_show, pick_random_song
from queue_eng.media_service import get_legal_id, get_sweeper
from queue_eng.queue_service import insert_queue_item
from queue_eng.playlist_logic import get_playlist_for_show, get_playlist_songs


SWEEPER_INTERVAL = 3


def build_queue(hours=3):
    now = datetime.now()
    end_time = now + timedelta(hours=hours)

    pointer = now
    song_counter = 0

    print(f"Building queue {now} → {end_time}")

    while pointer < end_time:

        show = get_active_show(pointer)

        # -------------------
        # LEGAL ID (hourly)
        # -------------------
        if pointer.minute == 0 and pointer.second < 5:
            media = get_legal_id()
            if media:
                insert_queue_item(pointer, "MEDIA", mediaid=media["mediaid"], source="CLOCK")
                pointer += timedelta(seconds=media["duration"])
                continue

        # -------------------
        # SHOW MODE
        # -------------------
        if show:
            playlist_id = get_playlist_for_show(show["showid"])

            if playlist_id:
                songs = get_playlist_songs(playlist_id)

                for s in songs:
                    insert_queue_item(
                        pointer,
                        "SONG",
                        songid=s["songid"],
                        source="PLAYLIST"
                    )
                    pointer += timedelta(seconds=s["duration"] or 180)

                continue

            songs = get_songs_for_show(show["name"])
        else:
            songs = get_songs_for_show("general")

        song = pick_random_song(songs)

        if song:
            insert_queue_item(
                pointer,
                "SONG",
                songid=song["songid"],
                source="AUTO"
            )

            pointer += timedelta(seconds=song["duration"] or 180)
            song_counter += 1

        # -------------------
        # SWEEPER
        # -------------------
        if song_counter >= SWEEPER_INTERVAL:
            sweeper = get_sweeper()

            if sweeper:
                insert_queue_item(
                    pointer,
                    "MEDIA",
                    mediaid=sweeper["mediaid"],
                    source="CLOCK"
                )

                pointer += timedelta(seconds=sweeper["duration"] or 10)

            song_counter = 0