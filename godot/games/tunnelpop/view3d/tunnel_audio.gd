class_name TunnelAudio
extends Node
## Tunnel Pop music and sound: the walking tune that plays only while the hero moves (as in the classic), its hurried
## variant when the last creature runs; footsteps or crunching earth, the hose, the catch, pumps climbing in pitch,
## the pop, rocks wobbling, falling and landing, a crush, fire, the ghosts' warble, the vegetable, a lost life, the
## round's jingles. A sound that is not there yet is skipped.

const D = preload("res://games/tunnelpop/engine/pop_dig_engine.gd")
const SFX := "res://games/tunnelpop/audio/sfx/"
const MUSIC := "res://games/tunnelpop/audio/music/"
const NAMES := ["shoot", "hook", "pump", "pop", "crush", "rock_wobble", "rock_fall", "rock_land", "breathe", "ghost", "veg_appear",
	"veg_take", "die", "level_start", "level_clear", "last_one", "game_over", "extra_life"]

@export var game: TunnelGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _walk: AudioStreamPlayer
var _dig: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _hurrying := false


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -9.0
	add_child(_music)
	_walk = _loop_player("walk_loop", -16.0)
	_dig = _loop_player("dig_loop", -12.0)
	_theme = _loop(MUSIC + "tunnelpop_theme.ogg")
	_hurry = _loop(MUSIC + "tunnelpop_hurry.ogg")
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		_hurrying = false
		play("level_start", -3.0)
		if _theme:
			_music.stream = _theme
			_music.play()
			_music.stream_paused = true)


func _loop_player(name: String, db: float) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	p.volume_db = db
	if ResourceLoader.exists(SFX + name + ".wav"):
		var w: AudioStream = load(SFX + name + ".wav")
		if w is AudioStreamWAV:
			var ww := w as AudioStreamWAV
			ww.loop_mode = AudioStreamWAV.LOOP_FORWARD
			ww.loop_end = int(ww.get_length() * ww.mix_rate)
		p.stream = w
	add_child(p)
	return p


func _loop(path: String) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var m: AudioStream = load(path)
	if m is AudioStreamOggVorbis:
		(m as AudioStreamOggVorbis).loop = true
	return m


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	if not _streams.has(name):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _process(_delta: float) -> void:
	var e := game.engine
	if e == null:
		return
	var moving: bool = e.hero["moving"] and e.phase == D.Phase.PLAY
	# the tune walks with him
	if _music.stream:
		_music.stream_paused = not moving and not _hurrying
	var digging: bool = moving and e.hero["digging"]
	if _walk.stream:
		if moving and not digging and not _walk.playing:
			_walk.play()
		elif (not moving or digging) and _walk.playing:
			_walk.stop()
	if _dig.stream:
		if digging and not _dig.playing:
			_dig.play()
		elif not digging and _dig.playing:
			_dig.stop()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shoot": play("shoot", -6.0, randf_range(0.95, 1.05))
		"hook": play("hook", -4.0)
		"pump": play("pump", -4.0, pow(2.0, (int(d["step"]) - 1) * 3.0 / 12.0))
		"pop": play("pop", -2.0, randf_range(0.95, 1.05))
		"crush": play("crush", -2.0)
		"wobble": play("rock_wobble", -6.0)
		"fall": play("rock_fall", -4.0)
		"land": play("rock_land", -3.0)
		"breathe": play("breathe", -4.0)
		"ghost": play("ghost", -10.0, randf_range(0.9, 1.1))
		"veg": play("veg_appear", -4.0)
		"veg_take": play("veg_take", -3.0)
		"die":
			play("die", -2.0)
			_music.stop()
		"cleared":
			play("level_clear", -2.0)
			_music.stop()
		"last":
			play("last_one", -4.0)
			_hurrying = true
			if _hurry:
				_music.stream = _hurry
				_music.play()
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
