from db.connection import getConnection
from library.tag_service import create_tag
from datetime import datetime


def _parse_time_str(t: str):
    return datetime.strptime(t, "%H:%M:%S").time()


def _is_valid_boundary(t: str) -> bool:
    parsed = _parse_time_str(t)
    return parsed.minute in (0, 30) and parsed.second == 0


def _date_to_dow(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A").lower()


def _times_overlap(start1, end1, start2, end2) -> bool:
    return start1 < end2 and end1 > start2


def _recurrence_conflicts(
    new_frequency,
    new_day_of_week,
    new_specific_date,
    existing_frequency,
    existing_day_of_week,
    existing_specific_date,
):
    # one-time vs one-time
    if new_frequency == "one_time" and existing_frequency == "one_time":
        return new_specific_date == existing_specific_date

    # one-time vs recurring
    if new_frequency == "one_time" and existing_frequency != "one_time":
        new_dow = _date_to_dow(new_specific_date)
        return new_dow == existing_day_of_week

    # recurring vs one-time
    if new_frequency != "one_time" and existing_frequency == "one_time":
        existing_dow = _date_to_dow(existing_specific_date)
        return new_day_of_week == existing_dow

    # recurring vs recurring
    if new_frequency in ("weekly", "biweekly", "monthly") and existing_frequency in ("weekly", "biweekly", "monthly"):
        return new_day_of_week == existing_day_of_week

    return False


def create_show(
    name,
    start_time,
    end_time,
    frequency,
    day_of_week=None,
    specific_date=None,
    repeat_until=None,
    is_indefinite=False
):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Validate start/end boundaries
        if not _is_valid_boundary(start_time):
            return False, "Start time must be on the hour or half hour (HH:00:00 or HH:30:00)."

        if not _is_valid_boundary(end_time):
            return False, "End time must be on the hour or half hour (HH:00:00 or HH:30:00)."

        parsed_start = _parse_time_str(start_time)
        parsed_end = _parse_time_str(end_time)

        if parsed_start >= parsed_end:
            return False, "End time must be after start time."

        if frequency not in ("weekly", "biweekly", "monthly", "one_time"):
            return False, "Invalid frequency."

        if frequency == "one_time":
            if not specific_date:
                return False, "One-time shows require a specific date."
        else:
            if not day_of_week:
                return False, "Recurring shows require a day_of_week."

        # Pull only potentially overlapping time ranges
        cursor.execute("""
            SELECT *
            FROM Shows
            WHERE start_time < %s
              AND end_time > %s
        """, (end_time, start_time))

        existing_shows = cursor.fetchall()

        for show in existing_shows:
            existing_start = show["start_time"]
            existing_end = show["end_time"]

            if not _times_overlap(parsed_start, parsed_end, existing_start, existing_end):
                continue

            if _recurrence_conflicts(
                frequency,
                day_of_week,
                specific_date,
                show["frequency"],
                show["day_of_week"],
                show["specific_date"]
            ):
                return False, f"Conflict: overlaps with existing show '{show['name']}'"

        cursor.execute("""
            INSERT INTO Shows (
                name,
                start_time,
                end_time,
                frequency,
                day_of_week,
                specific_date,
                repeat_until,
                is_indefinite
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            start_time,
            end_time,
            frequency,
            day_of_week,
            specific_date,
            repeat_until,
            is_indefinite
        ))

        conn.commit()

        create_tag(name)

        return True, "Show created successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Error creating show: {e}"

    finally:
        cursor.close()
        conn.close()


def search_shows(name=None):
    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            showid,
            name,
            start_time,
            end_time,
            frequency,
            day_of_week,
            specific_date,
            repeat_until,
            is_indefinite
        FROM Shows
    """

    params = []

    if name:
        sql += " WHERE name LIKE %s"
        params.append(f"%{name}%")

    sql += " ORDER BY start_time"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows