class_name HenAudio
extends Node
## Henhouse Heist music and sound: the farmyard theme (the frantic one once the goose is loose), boots on planks,
## ladder creaks, eggs and grain, clucks, the goose's honks and wing beats, the lifts' pulley.

const SFX := "res://games/henhouse/audio/sfx/"
const NAMES := ["step_0", "step_1", "climb", "jump", "land", "egg", "grain", "cluck_0", "cluck_1", "cluck_2", "goose_honk",
	"goose_free", "die", "bonus_tick", "level_start", "level_clear", "game_over", "extra_life"]

@export var game: HenGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _goose: AudioStream
var _flap: AudioStreamPlayer
var _lift: AudioStreamPlayer
var _step := 0
var _honk_t := 4.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/henhouse/audio/music/henhouse_theme.ogg")
	_goose = load("res://games/henhouse/audio/music/henhouse_goose.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_goose as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	add_child(_music)
	_flap = _loop("flap", -10.0)
	_lift = _loop("lift", -14.0)
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("level_start", -3.0)
		_music.stream = _theme
		_music.play())


func _loop(name: String, db: float) -> AudioStreamPlayer:
	var w: AudioStreamWAV = load(SFX + name + ".wav")
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_end = int(w.get_length() * w.mix_rate)
	var p := AudioStreamPlayer.new()
	p.stream = w
	p.bus = "SFX"
	p.volume_db = db
	add_child(p)
	return p


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
	var loose := not e.goose.is_empty() and e.phase == HenEngine.Phase.PLAY
	if loose != _flap.playing:
		if loose: _flap.play()
		else: _flap.stop()
	var lifts := not e.lifts.is_empty() and e.phase == HenEngine.Phase.PLAY
	if lifts != _lift.playing:
		if lifts: _lift.play()
		else: _lift.stop()
	var want := _goose if loose else _theme
	if _music.stream != want and e.phase == HenEngine.Phase.PLAY:
		_music.stream = want
		_music.play()
	if loose:
		_honk_t -= delta
		if _honk_t <= 0.0:
			_honk_t = randf_range(3.0, 6.0)
			play("goose_honk", -6.0, randf_range(0.9, 1.1))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"step":
			var climbing: bool = game.engine.hero["state"] == "climb"
			if climbing:
				play("climb", -12.0, randf_range(0.9, 1.1))
			else:
				_step = 1 - _step
				play("step_%d" % _step, -12.0, randf_range(0.95, 1.05))
		"jump": play("jump", -8.0)
		"land": play("land", -10.0)
		"egg": play("egg", -5.0, 1.0 + (12 - mini(d["left"], 12)) * 0.02)
		"grain": play("grain", -5.0)
		"cluck": play("cluck_%d" % (d["id"] % 3), -12.0, randf_range(0.95, 1.1))
		"peck": play("cluck_1", -10.0)
		"goose_free": play("goose_free", -3.0)
		"die": play("die", -2.0)
		"cleared":
			play("level_clear", -2.0)
			for i in 8:
				get_tree().create_timer(1.0 + i * 0.08).timeout.connect(func(): play("bonus_tick", -8.0, 1.0 + i * 0.04))
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
