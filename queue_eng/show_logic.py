from db.connection import getConnection
from datetime import datetime


def get_active_show(current_time: datetime):
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
        if not (show["start_time"] <= current_time_only < show["end_time"]):
            continue

        freq = show["frequency"]

        if freq == "one_time":
            if show["specific_date"] != current_date:
                continue

        elif freq in ("weekly", "biweekly"):
            if show["day_of_week"] != current_day:
                continue

            if freq == "biweekly":
                week_num = current_time.isocalendar()[1]
                if week_num % 2 != 0:
                    continue

        elif freq == "monthly":
            if show["day_of_week"] != current_day:
                continue

        if not show["is_indefinite"]:
            if show["repeat_until"] and current_date > show["repeat_until"]:
                continue

        return show

    return None