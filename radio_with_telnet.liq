settings.log.stdout := true
settings.server.telnet := true
settings.server.telnet.port := 1234

radio = request.queue(id="radio_queue")

live = fallback(track_sensitive=false, [
  radio,
  blank()
])

output.icecast(
  %mp3(bitrate=192),
  host="wnhu-stream1.newhaven.edu",
  port=8050,
  user="charlie",
  password="Ruden06516",
  mount="/stationengine",
  name="WNHU Station Engine",
  description="Live radio stream",
  live
)
