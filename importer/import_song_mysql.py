import os
import hashlib
import shutil
from pathlib import Path
import mysql.connector
from mutagen import File as MutagenFile

# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
INCOMING_FOLDER = BASE_DIR / "media" / "incoming"
LIBRARY_FOLDER = BASE_DIR / "media" / "library"

SUPPORTED_EXTENSIONS = ('.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg')


# -------------------------
# Database config
# -------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "radio_user",
    "password": "password",
    "database": "radio_db",
}


# -------------------------
# Helpers
# -------------------------
def compute_file_hash(filepath, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def get_or_create_tag(cursor, tagname):
    tagname = tagname.strip()
    if not tagname:
        return None

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


# -------------------------
# Core import
# -------------------------
def import_song_mysql(file_path, db_config=DB_CONFIG):
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return

    audio = MutagenFile(file_path, easy=True)
    if audio is None:
        print(f"[ERROR] Unsupported audio file: {file_path}")
        return

    def get_tag(name):
        return audio.get(name, [None])[0]

    title = get_tag("title") or file_path.stem
    artist = get_tag("artist") or "Unknown Artist"
    album = get_tag("album")
    year = get_tag("date")
    tracknumber = get_tag("tracknumber")
    genre_raw = audio.get("genre", [])

    duration = int(audio.info.length) if audio.info else None
    channels = getattr(audio.info, "channels", None)
    codec = audio.mime[0] if audio.mime else None

    # Normalize year
    try:
        year = int(year[:4]) if year else None
    except ValueError:
        year = None

    # Normalize track number
    try:
        tracknumber = int(tracknumber.split("/")[0]) if tracknumber else None
    except ValueError:
        tracknumber = None

    filehash = compute_file_hash(file_path)

    LIBRARY_FOLDER.mkdir(parents=True, exist_ok=True)
    dest_path = LIBRARY_FOLDER / file_path.name

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Deduplicate by hash
        cursor.execute(
            "SELECT fileid FROM SongFile WHERE filehash = %s",
            (filehash,)
        )
        if cursor.fetchone():
            print(f"[SKIPPED] Duplicate file: {file_path.name}")
            return

        # Insert Song
        cursor.execute("""
            INSERT INTO Song (title, artist, album, year, tracknumber)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, artist, album, year, tracknumber))
        songid = cursor.lastrowid

        # Insert SongFile
        cursor.execute("""
            INSERT INTO SongFile (songid, duration, channels, codec, filepath, filehash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            songid,
            duration,
            channels,
            codec,
            str(dest_path),
            filehash
        ))

        # Handle genres → tags
        for genre in genre_raw:
            for tag in genre.split(","):
                tagid = get_or_create_tag(cursor, tag)
                if tagid:
                    cursor.execute("""
                        INSERT IGNORE INTO TagEntry (songid, tagid)
                        VALUES (%s, %s)
                    """, (songid, tagid))

        conn.commit()

        shutil.move(str(file_path), dest_path)
        print(f"[IMPORTED] {artist} - {title}")

    except mysql.connector.Error as e:
        print(f"[DB ERROR] {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# -------------------------
# Batch import
# -------------------------
def import_incoming_files():
    INCOMING_FOLDER.mkdir(parents=True, exist_ok=True)

    files = [
        f for f in INCOMING_FOLDER.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print("No files to import.")
        return

    for f in files:
        import_song_mysql(f)

    print("Finished importing incoming files.")

