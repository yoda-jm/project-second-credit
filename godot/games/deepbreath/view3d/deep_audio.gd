class_name DeepAudio
extends Node
## Deep Breath music and sound: the mining theme (the breathless one when the air runs low), boots on timber, the
## key chimes (brighter for the last), the lift bell, crumbling floor, the conveyor's rattle, the air alarm, and the
## air bonus ticking in.

const SFX := "res://games/deepbreath/audio/sfx/"
const NAMES := ["step_0", "step_1", "jump", "land", "key", "key_last", "portal_open", "portal_enter", "crumble", "die",
	"air_low", "air_tick", "steam", "level_start", "level_clear", "game_over", "extra_life"]

@export var game: DeepGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _air: AudioStream
var _belt: AudioStreamPlayer
var _step := 0
var _tick_t := 0.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/deepbreath/audio/music/deepbreath_theme.ogg")
	_air = load("res://games/deepbreath/audio/music/deepbreath_air.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_air as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	add_child(_music)
	var w: AudioStreamWAV = load(SFX + "conveyor.wav")
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_end = int(w.get_length() * w.mix_rate)
	_belt = AudioStreamPlayer.new()
	_belt.stream = w
	_belt.bus = "SFX"
	_belt.volume_db = -12.0
	add_child(_belt)
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("level_start", -3.0)
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
	var low := e.phase == DeepEngine.Phase.PLAY and e.air < 12.0
	var want := _air if low else _theme
	if _music.stream != want and e.phase == DeepEngine.Phase.PLAY:
		_music.stream = want
		_music.play()
	# the belt rattles while the miner stands on a conveyor
	var cell := e._standing_cell(e.hero["pos"]) if e.hero["state"] == "walk" else Vector2i(-1, -1)
	var on_belt := cell.x >= 0 and e.at(cell.x, cell.y) in ["<", ">"] and e.phase == DeepEngine.Phase.PLAY
	if on_belt != _belt.playing:
		if on_belt: _belt.play()
		else: _belt.stop()
	if e.phase == DeepEngine.Phase.CLEARED and e.air > 0.0:
		_tick_t -= delta
		if _tick_t <= 0.0:
			_tick_t = 0.06
			play("air_tick", -10.0, 1.0 + (1.0 - e.air / e.level.air) * 0.5)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"step":
			_step = 1 - _step
			play("step_%d" % _step, -12.0, randf_range(0.95, 1.05))
		"jump": play("jump", -8.0)
		"land": play("land", -9.0)
		"key": play("key_last" if d["left"] == 0 else "key", -4.0, 1.0 + (5 - mini(d["left"], 5)) * 0.03)
		"open": play("portal_open", -3.0)
		"crumble": play("crumble", -8.0)
		"die": play("die", -2.0)
		"air_low": play("air_low", -5.0)
		"cleared":
			play("portal_enter", -3.0)
			get_tree().create_timer(0.8).timeout.connect(func(): play("level_clear", -2.0))
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
