
#
# Usage:
# python import_song_mysql.py "file/path/here"
# or use the incoming folder

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
    """Copy the file into organized storage under media/songs alphabetically"""
    filehash = computeHash(filepath)

    # Use first letter of original filename for folder
    first_char = filepath.stem[0].upper()

    # If filename does not start with a letter/number, put it in #
    if not first_char.isalnum():
        first_char = "#"

    folder = MEDIA_ROOT / first_char
    folder.mkdir(parents=True, exist_ok=True)

    # Preserve original filename
    dest = folder / filepath.name

    # Avoid overwriting if same filename already exists
    if dest.exists():
        counter = 1
        while True:
            new_name = f"{filepath.stem}_{counter}{filepath.suffix}"
            new_dest = folder / new_name

            if not new_dest.exists():
                dest = new_dest
                break

            counter += 1

    shutil.copy2(filepath, dest)

    return dest.resolve(), filehash
# --------------------
# Tag management
# --------------------
def getOrCreateTag(cursor, tagname):
    tagname = tagname.strip()
    if not tagname:
        return None

    # Check if tag exists
    cursor.execute("SELECT tagid FROM Tags WHERE tagname = %s", (tagname,))
    row = cursor.fetchone()
    if row:
        return row[0]

    # Create tag if missing
    cursor.execute("INSERT IGNORE INTO Tags (tagname) VALUES (%s)", (tagname,))
    cursor.execute("SELECT tagid FROM Tags WHERE tagname = %s", (tagname,))
    row = cursor.fetchone()
    if row:
        return row[0]

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
        return row[0]

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
    except:
        year = None

    # normalize track
    try:
        tracknumber = int(tracknumber.split("/")[0]) if tracknumber else None
    except:
        tracknumber = None

    new_path, filehash = storeFile(filepath)
    genre_string = ", ".join(genres) if genres else None

    try:
        conn = getConnection()
        cursor = conn.cursor()

        cursor.execute("SELECT fileid FROM SongFile WHERE filehash = %s", (filehash,))
        if cursor.fetchone():
            return False, "Duplicate file", None

        songid = getOrCreateSong(cursor, title, artist, album, genre_string, year, tracknumber)

        cursor.execute("""
            INSERT INTO SongFile (songid, duration, channels, codec, filepath, filehash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (songid, duration, channels, codec, str(new_path), filehash))

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
        conn.rollback()
        return False, str(e), None

    finally:
        cursor.close()
        conn.close()


# --------------------
# Batch import from incoming folder
# --------------------
def importIncomingFiles():
    if not INCOMING_FOLDER.exists():
        print("Incoming folder does not exist. Creating it.")
        INCOMING_FOLDER.mkdir(parents=True, exist_ok=True)

    files = [f for f in INCOMING_FOLDER.iterdir() if f.is_file()]
    if not files:
        print("No files to import in incoming folder")
        return []

    results = []

    for f in files:
        print(f"Importing {f.name}...")
        try:
            ok, msg, songid = import_song(f)
            print(f"  -> {msg}")

            results.append({
                "file": f.name,
                "success": ok,
                "message": msg,
                "songid": songid
            })

            if ok:
                try:
                    f.unlink()
                except Exception as e:
                    print(f"  -> imported, but could not delete source file: {e}")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            results.append({
                "file": f.name,
                "success": False,
                "message": str(e),
                "songid": None
            })

    print("Finished importing incoming files")
    return results

# --------------------
# CLI usage idk i was having a problem and this fixed it idk how
# --------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        import_song(sys.argv[1])
