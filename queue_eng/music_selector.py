from db.connection import getConnection
import random
from datetime import datetime


CLOCK = [
    "THROWBACK", "THROWBACK", "THROWBACK", "THROWBACK",
    "NEW",
    "THROWBACK", "THROWBACK", "THROWBACK",
    "RECURRENT"
]


def get_category(year):
    current_year = datetime.now().year

    if year is None:
        return "THROWBACK"

    age = current_year - year

    if age <= 0:
        return "NEW"
    elif age <= 1:
        return "RECURRENT"
    else:
        return "THROWBACK"


def get_all_songs():
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.songid, s.title, s.artist, s.year, sf.duration
        FROM Song s
        JOIN SongFile sf ON s.songid = sf.songid
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_songs_for_show(show_name):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.songid, s.title, s.artist, s.year, sf.duration
        FROM Song s
        JOIN SongFile sf ON s.songid = sf.songid
        JOIN TagEntry te ON s.songid = te.songid
        JOIN Tags t ON te.tagid = t.tagid
        WHERE t.tagname = %s
    """, (show_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def build_rotation_pools():
    songs = get_all_songs()

    pools = {
        "NEW": [],
        "RECURRENT": [],
        "THROWBACK": []
    }

    for s in songs:
        pools[get_category(s["year"])].append(s)

    return pools


def pick_random_song(song_list):
    if not song_list:
        return None
    return random.choice(song_list)


def get_next_rotation_song(pools, index):
    cat = CLOCK[index % len(CLOCK)]

    if pools[cat]:
        return random.choice(pools[cat])

    for fallback_cat in ("THROWBACK", "RECURRENT", "NEW"):
        if pools[fallback_cat]:
            return random.choice(pools[fallback_cat])

    return None


def get_next_show_song(show_name):
    songs = get_songs_for_show(show_name)
    return pick_random_song(songs)