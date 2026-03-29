from datetime import datetime

def get_song_category(year: int) -> str:
    if not year:
        return "NON_ACTIVE"

    current_year = datetime.now().year
    age = current_year - year

    if age <= 1:
        return "NEW"
    elif age <= 5:
        return "RECURRENT"
    elif age <= 20:
        return "THROWBACK"
    else:
        return "NON_ACTIVE"