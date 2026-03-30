from pathlib import Path
import hashlib
import shutil
from mutagen import File as MutagenFile

from db.connection import getConnection

MEDIA_ROOT = Path("media/station_media")
INCOMING_IDS_FOLDER = Path("media/incomingIDs")
INCOMING_SWEEPERS_FOLDER = Path("media/incomingSweepers")

ALLOWED_TYPES = {"LEGAL_ID", "SWEEPER", "PROMO", "NEW_SWEEPER"}


def compute_hash(filepath: Path, block_size: int = 65536) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def store_media_file(filepath: Path, media_type: str) -> tuple[Path, str]:
    filehash = compute_hash(filepath)
    ext = filepath.suffix.lower()
    folder = MEDIA_ROOT / media_type.lower() / filehash[:2]
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{filehash}{ext}"

    if not dest.exists():
        shutil.copy2(filepath, dest)

    return dest.resolve(), filehash


def get_duration_seconds(filepath: Path) -> int:
    audio = MutagenFile(filepath)
    if audio is None or not getattr(audio, "info", None):
        raise ValueError("Unsupported or unreadable audio file")
    return int(round(audio.info.length))


def import_station_media(filepath: Path, media_type: str, name: str | None = None):
    media_type = media_type.upper().strip()
    if media_type not in ALLOWED_TYPES:
        return False, f"Invalid media_type: {media_type}", None

    if not filepath.exists():
        return False, "File does not exist", None

    try:
        duration = get_duration_seconds(filepath)
        new_path, filehash = store_media_file(filepath, media_type)
    except Exception as e:
        return False, str(e), None

    media_name = name.strip() if name else filepath.stem

    conn = getConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT mediaid FROM StationMedia WHERE filepath = %s",
            (str(new_path),),
        )
        row = cursor.fetchone()
        if row:
            return False, "Duplicate file", row[0]

        cursor.execute(
            """
            INSERT INTO StationMedia (name, filepath, duration, media_type)
            VALUES (%s, %s, %s, %s)
            """,
            (media_name, str(new_path), duration, media_type),
        )
        conn.commit()
        return True, f"Imported {media_type}", cursor.lastrowid
    except Exception as e:
        conn.rollback()
        return False, str(e), None
    finally:
        cursor.close()
        conn.close()


def _import_folder(folder: Path, media_type: str):
    folder.mkdir(parents=True, exist_ok=True)
    files = [f for f in folder.iterdir() if f.is_file()]
    results = []

    for f in files:
        ok, msg, mediaid = import_station_media(f, media_type)
        results.append({
            "file": f.name,
            "success": ok,
            "message": msg,
            "mediaid": mediaid,
        })
        try:
            f.unlink()
        except Exception as e:
            results.append({
                "file": f.name,
                "success": False,
                "message": f"Imported but could not delete source file: {e}",
                "mediaid": mediaid,
            })
    return results


def import_incoming_ids():
    return _import_folder(INCOMING_IDS_FOLDER, "LEGAL_ID")


def import_incoming_sweepers():
    return _import_folder(INCOMING_SWEEPERS_FOLDER, "SWEEPER")
