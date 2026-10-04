class_name TinAudio
extends Node
## Tinplate Turbo music and sound: the race tune (the light one for results and the bench), each player's engine hum
## pitched with its speed (the CPUs' quieter), tyre squeal while sliding, tin clunks on the barriers and on each other,
## jumps and landings, oil, splashes, the wrench's jingle, the countdown beeps and the go, lap dings, the final lap's
## bell and the chequered flag's fanfare. A sound that is not there yet is skipped.

const T = preload("res://games/tinplate/engine/tin_engine.gd")
const SFX := "res://games/tinplate/audio/sfx/"
const MUSIC := "res://games/tinplate/audio/music/"
const NAMES := ["bump", "crash", "car_hit", "jump", "land", "oil", "splash", "wrench", "countdown_beep", "go_beep", "lap",
	"final_lap", "finish", "upgrade", "win", "lose"]

@export var game: TinGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _engines: Array[AudioStreamPlayer] = []
var _skids: Array[AudioStreamPlayer] = []
var _theme: AudioStream
var _menu: AudioStream
var _mode := -1


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
	_music.volume_db = -11.0
	add_child(_music)
	for i in 4:
		_engines.append(_loop_player("engine_loop"))
		_skids.append(_loop_player("skid_loop"))
	_theme = _loop(MUSIC + "tinplate_theme.ogg")
	_menu = _loop(MUSIC + "tinplate_menu.ogg")
	game.race_started.connect(func(e): e.event.connect(_on_event))


func _loop_player(name: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	p.volume_db = -80.0
	if ResourceLoader.exists(SFX + name + ".wav"):
		var w: AudioStream = load(SFX + name + ".wav")
		if w is AudioStreamWAV:
			var ww := (w as AudioStreamWAV).duplicate() as AudioStreamWAV
			ww.loop_mode = AudioStreamWAV.LOOP_FORWARD
			ww.loop_end = int(ww.get_length() * ww.mix_rate)
			w = ww
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
	var want := 0 if game.mode == TinGame.Mode.RACE else 1
	if want != _mode:
		_mode = want
		var s := _theme if want == 0 else _menu
		if s:
			_music.stream = s
			_music.play()
	var e := game.engine
	if e == null:
		return
	for i in mini(4, e.cars.size()):
		var c := e.cars[i]
		var speed: float = (c["vel"] as Vector2).length()
		var ep := _engines[i]
		var sp := _skids[i]
		if ep.stream == null:
			continue
		if not ep.playing:
			ep.play()
			sp.play()
		var mine: bool = not c["cpu"] or (game.demo and i == 0)
		var racing := game.mode == TinGame.Mode.RACE
		ep.pitch_scale = 0.7 + speed / T.BASE_SPEED * 1.1 + c["throttle"] * 0.08
		ep.volume_db = (-12.0 if mine else -24.0) + (0.0 if racing else -40.0)
		var slide: float = c["slide"]
		sp.volume_db = -80.0 if slide < 2.2 or c["air"] or not racing else lerpf(-26.0, -12.0, clampf((slide - 2.2) / 5.0, 0.0, 1.0)) - (0.0 if mine else 8.0)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"countdown": play("countdown_beep", -4.0)
		"go": play("go_beep", -3.0)
		"bump": play("crash" if d["speed"] > 7.0 else "bump", -6.0 + minf(d["speed"], 8.0), randf_range(0.9, 1.1))
		"knock": play("car_hit", -6.0, randf_range(0.9, 1.15))
		"jump": play("jump", -5.0)
		"land": play("land", -4.0)
		"oil": play("oil", -4.0)
		"splash": play("splash", -4.0)
		"wrench": play("wrench", -3.0)
		"lap": if not e.cars[d["car"]]["cpu"]: play("lap", -5.0)
		"final_lap": if not e.cars[d["car"]]["cpu"] or game.demo: play("final_lap", -3.0)
		"finish":
			if d["place"] == 1:
				play("finish", -2.0)
			var c := e.cars[d["car"]]
			if not c["cpu"]:
				play("win" if d["place"] == 1 else "lose", -4.0)
