from __future__ import annotations

from db.connection import getConnection
import random


def get_media(media_type: str, exclude_mediaids: set[int] | None = None):
    exclude_mediaids = exclude_mediaids or set()

    conn = getConnection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT * FROM StationMedia
        WHERE media_type = %s
        ORDER BY mediaid
        """,
        (media_type,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return None

    filtered = [r for r in rows if r["mediaid"] not in exclude_mediaids]
    return random.choice(filtered or rows)
