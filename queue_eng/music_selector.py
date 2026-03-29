def get_song_category(year):
    from datetime import datetime

    current_year = datetime.now().year

    if year is None:
        return "UNKNOWN"

    if year >= current_year - 1:
        return "NEW"
    elif year >= current_year - 5:
        return "RECURRENT"
    else:
        return "THROWBACK"