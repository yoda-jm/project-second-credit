class_name CaveAudio
extends Node
## Music and sound effects, driven by the engine's events. Sounds of the same kind in one frame are merged
## (ten boulders landing make one louder thud), continuous ones (amoeba, magic wall) are rate-limited.

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")
const SFX := "res://games/glimmerdeep/audio/sfx/"

@export var game: CaveGame
@export var music_volume_db := -8.0

var _music: AudioStreamPlayer
var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _last_played := {}


func _ready() -> void:
	for name in ["dig", "step", "boulder_land", "boulder_roll", "gem_land", "gem_collect", "explosion", "exit_open",
			"hatch", "exit_enter", "tick", "fail", "amoeba", "magic_wall", "butterfly_burst", "count", "go"]:
		_streams[name] = load(SFX + name + ".wav")
	for i in 16:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/glimmerdeep/audio/music/cave_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.volume_db = music_volume_db
	_music.bus = "Music"
	add_child(_music)
	game.frame_done.connect(_on_frame)
	game.cave_started.connect(func(_e): if not _music.playing: _music.play())
	game.cave_finished.connect(func(_e, success): play("exit_enter" if success else "fail"))
	game.countdown_tick.connect(func(n): play("go" if n == 0 else "count", -3.0))
	if game.engine:
		_music.play()


func play(name: String, volume_db: float = 0.0, pitch: float = 1.0, min_gap_ms: int = 0) -> void:
	var now := Time.get_ticks_msec()
	if min_gap_ms > 0 and now - int(_last_played.get(name, -100000)) < min_gap_ms:
		return
	_last_played[name] = now
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = volume_db
	p.pitch_scale = pitch
	p.play()


func _on_frame(engine: CaveEngine, _ms: float) -> void:
	var counts := {}
	for ev in engine.events:
		var key := ""
		match ev[0]:
			"eat":
				var el: int = ev[1]
				if el == E.DIAMOND or el == E.FLYING_DIAMOND:
					key = "gem_collect"
				elif (E.FLAGS[el] & E.P_DIRT) != 0:
					key = "dig"
				elif el == E.SPACE:
					key = "step"
			"effect":
				if not ev[4]:
					continue
				var el: int = ev[1]
				if el == E.STONE or el == E.STONE_F or el == E.MEGA_STONE or el == E.NUT:
					key = "boulder_land"
				elif el == E.DIAMOND or el == E.DIAMOND_F:
					key = "gem_land"
				elif el == E.AMOEBA:
					key = "amoeba"
				elif el == E.MAGIC_WALL:
					key = "magic_wall"
			"explosion":
				var el: int = ev[1]
				key = "butterfly_burst" if (el >= E.BUTTER_1 and el <= E.BUTTER_4) else "explosion"
			"sound":
				if ev[1] == "crack":
					key = "exit_open" if engine.gate_open else "hatch"
			"seconds":
				if ev[1] <= 10 and ev[1] > 0:
					key = "tick"
		if key != "":
			counts[key] = counts.get(key, 0) + 1
	for key in counts:
		var n: int = counts[key]
		var vol := minf(6.0, 2.0 * log(n) / log(2.0))
		match key:
			"amoeba":
				play(key, -10.0, randf_range(0.9, 1.2), 350)
			"magic_wall":
				play(key, -8.0, 1.0, 300)
			"step":
				play(key, -14.0, randf_range(0.9, 1.1))
			"dig":
				play(key, -4.0, randf_range(0.9, 1.15))
			_:
				play(key, vol - 2.0, randf_range(0.95, 1.05))
