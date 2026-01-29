# library/models.py

class SongView:
    def __init__(self, songid, title, artist, album, duration, tags):
        self.songid = songid
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration  # seconds
        self.tags = tags          # list of strings

    def to_dict(self):
        return {
            "songid": self.songid,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "tags": self.tags
        }
