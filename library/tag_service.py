from db.connection import getConnection


def create_tag(tagname: str):
    tagname = tagname.strip()

    if not tagname:
        return False, "Tag name cannot be empty"

    conn = getConnection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT tagid FROM Tags WHERE tagname = %s", (tagname,))
        if cursor.fetchone():
            return False, "Tag already exists"

        cursor.execute(
            "INSERT INTO Tags (tagname) VALUES (%s)",
            (tagname,)
        )

        conn.commit()
        return True, "Tag created successfully"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()