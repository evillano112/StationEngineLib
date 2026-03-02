#
# Usage:
# python import_song_mysql.py "file/path/here"
# or use the incoming folder
#

import hashlib
from pathlib import Path
import shutil
from mutagen import File as MutagenFile
from db.connection import getConnection

# Root folders
MEDIA_ROOT = Path("media/songs")         # permanent storage
INCOMING_FOLDER = Path("media/incoming") # optional batch import


# --------------------
# Hash & store files
# --------------------
def computeHash(filepath, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def storeFile(filepath):
    """Copy the file into organized storage under media/songs"""
    filehash = computeHash(filepath)
    ext = filepath.suffix.lower()

    folder = MEDIA_ROOT / filehash[:2]
    folder.mkdir(parents=True, exist_ok=True)

    dest = folder / f"{filehash}{ext}"

    if not dest.exists():
        shutil.copy2(filepath, dest)

    return dest.resolve(), filehash


# --------------------
# Tag management
# --------------------
def getOrCreateTag(cursor, tagname):
    tagname = tagname.strip()
    if not tagname:
        return None

    cursor.execute("SELECT tagid FROM Tags WHERE tagname = %s", (tagname,))
    row = cursor.fetchone()
    if row:
        return row["tagid"]  # FIXED

    cursor.execute("INSERT IGNORE INTO Tags (tagname) VALUES (%s)", (tagname,))
    cursor.execute("SELECT tagid FROM Tags WHERE tagname = %s", (tagname,))
    row = cursor.fetchone()

    if row:
        return row["tagid"]  # FIXED

    raise RuntimeError(f"Failed to create tag: {tagname}")


# --------------------
# Song management
# --------------------
def getOrCreateSong(cursor, title, artist, album, genre, year, tracknumber):
    cursor.execute("""
        SELECT songid FROM Song
        WHERE title = %s AND artist = %s AND album <=> %s
    """, (title, artist, album))

    row = cursor.fetchone()
    if row:
        return row["songid"]  # FIXED

    cursor.execute("""
        INSERT INTO Song (title, artist, album, genre, year, tracknumber)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, artist, album, genre, year, tracknumber))

    return cursor.lastrowid


# --------------------
# Insert single song
# --------------------
def import_song(filepath: Path):
    if not filepath.exists():
        return False, "File does not exist", None

    audio = MutagenFile(filepath, easy=True)
    if audio is None:
        return False, "Unsupported or unreadable audio file", None

    def get_tag(name):
        return audio.get(name, [None])[0]

    title = get_tag("title") or filepath.stem
    artist = get_tag("artist") or "Unknown Artist"
    album = get_tag("album")
    genre_raw = get_tag("genre") or ""
    genres = [g.strip() for g in genre_raw.split(",") if g.strip()]
    year = get_tag("date")
    tracknumber = get_tag("tracknumber")

    duration = int(audio.info.length) if audio.info else None
    channels = getattr(audio.info, "channels", None)
    codec = audio.mime[0] if audio.mime else None

    # normalize year
    try:
        year = int(year[:4]) if year else None
    except Exception:
        year = None

    # normalize track
    try:
        tracknumber = int(tracknumber.split("/")[0]) if tracknumber else None
    except Exception:
        tracknumber = None

    # Store file AFTER metadata extraction
    new_path, filehash = storeFile(filepath)
    genre_string = ", ".join(genres) if genres else None

    conn = None
    cursor = None

    try:
        conn = getConnection()
        cursor = conn.cursor(dictionary=True)

        # Check duplicate file
        cursor.execute("SELECT fileid FROM SongFile WHERE filehash = %s", (filehash,))
        if cursor.fetchone():
            return False, "Duplicate file", None

        songid = getOrCreateSong(
            cursor, title, artist, album,
            genre_string, year, tracknumber
        )

        cursor.execute("""
            INSERT INTO SongFile (songid, duration, channels, codec, filepath, filehash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (songid, duration, channels, codec, str(new_path), filehash))

        # Insert tag relationships
        for tagname in genres:
            tagid = getOrCreateTag(cursor, tagname)
            if tagid:
                cursor.execute(
                    "INSERT IGNORE INTO TagEntry (songid, tagid) VALUES (%s, %s)",
                    (songid, tagid)
                )

        conn.commit()
        return True, "Imported", songid

    except Exception as e:
        if conn:
            conn.rollback()
        print("IMPORT ERROR:", repr(e))
        return False, str(e), None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# --------------------
# Batch import
# --------------------
def importIncomingFiles():
    if not INCOMING_FOLDER.exists():
        print("Incoming folder does not exist. Creating it.")
        INCOMING_FOLDER.mkdir(parents=True, exist_ok=True)

    files = [f for f in INCOMING_FOLDER.iterdir() if f.is_file()]

    if not files:
        print("No files to import in incoming folder")
        return

    for f in files:
        print(f"Importing {f.name}...")
        success, msg, _ = import_song(f)
        print(msg)

        if success:
            try:
                f.unlink()
            except Exception as e:
                print(f"Could not delete {f.name}: {e}")

    print("Finished importing incoming files")


# --------------------
# CLI usage
# --------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        path = Path(sys.argv[1])
        success, message, songid = import_song(path)
        print(message)
    else:
        print("Usage: python import_song_mysql.py <filepath>")

