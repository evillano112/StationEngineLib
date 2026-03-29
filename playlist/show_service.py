from db.connection import getConnection
from library.tag_service import create_tag
from datetime import datetime

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
        # ----------------------------
        # CHECK FOR TIME OVERLAPS
        # ----------------------------
        overlap_sql = """
            SELECT * FROM Shows
            WHERE (
                -- TIME OVERLAP
                (start_time < %s AND end_time > %s)
            )
        """

        cursor.execute(overlap_sql, (end_time, start_time))
        existing_shows = cursor.fetchall()

        for show in existing_shows:

            # ----------------------------
            # MATCH LOGIC BASED ON FREQUENCY
            # ----------------------------

            # ONE-TIME vs ONE-TIME
            if frequency == "one_time" and show["frequency"] == "one_time":
                if specific_date == show["specific_date"]:
                    return False, "Conflict: overlapping one-time show"

            # WEEKLY / BIWEEKLY
            elif frequency in ("weekly", "biweekly") and show["frequency"] in ("weekly", "biweekly"):
                if day_of_week == show["day_of_week"]:
                    return False, "Conflict: overlapping weekly show"

            # MONTHLY (simplified for now)
            elif frequency == "monthly" and show["frequency"] == "monthly":
                if day_of_week == show["day_of_week"]:
                    return False, "Conflict: overlapping monthly show"

            # ONE-TIME vs RECURRING
            elif frequency == "one_time":
                if show["frequency"] != "one_time":
                    if day_of_week and specific_date:
                        import datetime
                        dow = datetime.datetime.strptime(specific_date, "%Y-%m-%d").strftime("%A").lower()
                        if dow == show["day_of_week"]:
                            return False, "Conflict: overlaps recurring show"

            elif show["frequency"] == "one_time":
                if frequency != "one_time":
                    import datetime
                    dow = datetime.datetime.strptime(show["specific_date"], "%Y-%m-%d").strftime("%A").lower()
                    if dow == day_of_week:
                        return False, "Conflict: overlaps one-time show"

        # ----------------------------
        # INSERT IF SAFE
        # ----------------------------
        sql = """
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
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(sql, (
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

        # Create tag automatically
        create_tag(name)

        return True, "Show created successfully"

    except Exception as e:
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