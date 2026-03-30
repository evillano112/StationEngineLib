set("log.stdout", true)

radio = playlist(
  "/home/eurynome/stationenginelib/playlist.txt",
  reload_mode="watch"
)

radio = mksafe(radio)

output.icecast(
  %mp3(bitrate=192),
  host="wnhu-stream1.newhaven.edu",
  port=8050,
  user="charlie",
  password="Ruden06516",
  mount="/stationengine",
  radio
)