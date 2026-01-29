# Required install:
# python -m pip install mysql-connector-python mutagen
#
# Usage:
# python import_song_mysql.py "file/path/here"

import mysql.connector
import hashlib
from pathlib import Path
from mutagen import File as MutagenFile

# MySQL config
DB_CONFIG = {
    "host": "localhost",
    "user": "radio_user",
    "password": "password",
    "database": "radio_db",
}


def compute_file_hash(filepath, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def get_or_create_tag(cursor, tagname):
    cursor.execute(
        "SELECT tagid FROM Tags WHERE tagname = %s",
        (tagname,)
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO Tags (tagname) VALUES (%s)",
        (tagname,)
    )
    return cursor.lastrowid


def insert_song(filepath):
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        return

    audio = MutagenFile(filepath, easy=True)
    if audio is None:
        print(f"[ERROR] Unsupported or unreadable audio file: {filepath}")
        return

    def get_tag(name):
        return audio.get(name, [None])[0]

    title = get_tag("title") or filepath.stem
    artist = get_tag("artist") or "Unknown Artist"
    album = get_tag("album")
    genre_raw = audio.get("genre", [])
    year = get_tag("date")
    tracknumber = get_tag("tracknumber")

    duration = int(audio.info.length) if audio.info else None
    channels = getattr(audio.info, "channels", None)
    codec = audio.mime[0] if audio.mime else None

    # Normalize year
    try:
        if year:
            year = int(year[:4])
    except ValueError:
        year = None

    # Normalize track number
    try:
        if tracknumber:
            tracknumber = int(tracknumber.split("/")[0])
    except ValueError:
        tracknumber = None

    filehash = compute_file_hash(filepath)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check for duplicate file
        cursor.execute(
            "SELECT fileid FROM SongFile WHERE filehash = %s",
            (filehash,)
        )
        if cursor.fetchone():
            print(f"[INFO] Duplicate file skipped: {filepath}")
            return

        # Insert Song (metadata only)
        cursor.execute(
            """
            INSERT INTO Song (
                title, artist, album, genre, year, tracknumber
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                title,
                artist,
                album,
                ", ".join(genre_raw) if genre_raw else None,
                year,
                tracknumber
            )
        )
        songid = cursor.lastrowid

        # Insert SongFile (technical/audio data)
        cursor.execute(
            """
            INSERT INTO SongFile (
                songid, duration, channels, codec, filepath, filehash
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                songid,
                duration,
                channels,
                codec,
                str(filepath),
                filehash
            )
        )

        # Insert tags (categories)
        for genre in genre_raw:
            genre = genre.strip()
            if not genre:
                continue

            tagid = get_or_create_tag(cursor, genre)

            cursor.execute(
                """
                INSERT IGNORE INTO TagEntry (songid, tagid)
                VALUES (%s, %s)
                """,
                (songid, tagid)
            )

        conn.commit()
        print(f"[OK] Imported: {artist} - {title}")

    except mysql.connector.Error as e:
        print(f"[ERROR] MySQL operation failed: {e}")
        conn.rollback()

    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python import_song_mysql.py <audiofile>")
        sys.exit(1)

    insert_song(sys.argv[1])
