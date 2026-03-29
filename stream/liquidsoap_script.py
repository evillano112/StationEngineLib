from db.connection import getConnection

def build_liquidsoap_playlist():
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT sf.filepath
        FROM PlaybackQueue pq
        JOIN SongFile sf ON pq.songid = sf.songid
        WHERE pq.media_type = 'SONG'
        ORDER BY pq.play_time ASC
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    files = [r["filepath"] for r in rows if r.get("filepath")]

    # fallback so Liquidsoap never dies
    if not files:
        files = ["silence.mp3"]

    playlist_str = "\n".join(files)
    return playlist_str


def write_liquidsoap_file(path="radio.liq"):
    playlist = build_liquidsoap_playlist()

    script = f"""
set("log.level", 3)

radio = playlist(mode="normal", reload_mode="watch", "{playlist}")

radio = mksafe(radio)

output.icecast(
  %mp3(bitrate=128),
  host="127.0.0.1",
  port=8000,
  password="hackme",
  mount="radio.mp3",
  radio
)
"""

    with open(path, "w") as f:
        f.write(script)

    return path