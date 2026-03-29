from db.connection import getConnection
from datetime import datetime


def get_active_show(current_time: datetime):
    """
    Returns the currently active show (dict) or None
    """

    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    current_day = current_time.strftime("%A").lower()
    current_time_only = current_time.time()
    current_date = current_time.date()

    cursor.execute("SELECT * FROM Shows")
    shows = cursor.fetchall()

    cursor.close()
    conn.close()

    for show in shows:

        # ------------------------
        # TIME WINDOW CHECK
        # ------------------------
        if not (show["start_time"] <= current_time_only < show["end_time"]):
            continue

        # ------------------------
        # FREQUENCY CHECK
        # ------------------------
        freq = show["frequency"]

        # ONE-TIME SHOW
        if freq == "one_time":
            if show["specific_date"] != current_date:
                continue

        # WEEKLY / BIWEEKLY
        elif freq in ("weekly", "biweekly"):
            if show["day_of_week"] != current_day:
                continue

            if freq == "biweekly":
                # crude biweekly check (based on ISO week number)
                week_num = current_time.isocalendar()[1]
                if week_num % 2 != 0:
                    continue

        # MONTHLY (basic version: same weekday)
        elif freq == "monthly":
            if show["day_of_week"] != current_day:
                continue
            # (can improve later to "first Monday", etc.)

        # ------------------------
        # REPEAT RULES
        # ------------------------
        if not show["is_indefinite"]:
            if show["repeat_until"] and current_date > show["repeat_until"]:
                continue

        # ✅ MATCH FOUND
        return show

    return None