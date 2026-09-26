class_name HopAudio
extends Node
## Hopline music and sound: the theme (the hurry loop when time is short), town traffic and the canal lapping as
## ambience, a spring for every hop, horns now and then, and a sound for each way home or not.

const SFX := "res://games/hopline/audio/sfx/"
const NAMES := ["hop", "splat", "plop", "home", "all_home", "fly", "lady", "time_warn", "time_up", "extra_life", "ready",
	"game_over", "turtle_dive", "croc_snap", "horn_a", "horn_b"]

@export var game: HopGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _horn_t := 6.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 8:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/hopline/audio/music/hopline_theme.ogg")
	_hurry = load("res://games/hopline/audio/music/hopline_hurry.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_hurry as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	_music.stream = _theme
	add_child(_music)
	for amb in [["traffic_loop", -14.0], ["river_loop", -13.0]]:
		var w: AudioStreamWAV = load(SFX + amb[0] + ".wav")
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = int(w.get_length() * w.mix_rate)
		var p := AudioStreamPlayer.new()
		p.stream = w
		p.bus = "SFX"
		p.volume_db = amb[1]
		add_child(p)
		p.play()
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		play("ready", -3.0)
		_music.stream = _theme
		_music.play())


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _process(delta: float) -> void:
	var e := game.engine
	if e == null:
		return
	var hurry := e.phase == HopEngine.Phase.PLAY and e.life_t < 8.0
	if hurry and _music.stream != _hurry:
		_music.stream = _hurry
		_music.play()
	elif not hurry and _music.stream == _hurry:
		_music.stream = _theme
		_music.play()
	_horn_t -= delta
	if _horn_t <= 0.0:
		_horn_t = randf_range(7.0, 16.0)
		play("horn_a" if randf() < 0.5 else "horn_b", -14.0, randf_range(0.9, 1.1))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"hop": play("hop", -8.0, randf_range(0.95, 1.08))
		"die":
			match d["how"]:
				"drown", "swept": play("plop", -3.0)
				"time": play("time_up", -3.0)
				"croc": play("croc_snap", -3.0)
				_: play("splat", -3.0)
		"home": play("home", -3.0)
		"all_home": play("all_home", -2.0)
		"fly": play("fly", -4.0)
		"lady_home", "lady": play("lady", -4.0)
		"time_warn": play("time_warn", -5.0)
		"extra_life": play("extra_life", -3.0)
		"turtle_dive": play("turtle_dive", -12.0)
		"game_over": play("game_over", -2.0)
