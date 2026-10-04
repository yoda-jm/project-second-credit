class_name FlowAudio
extends Node
## Brassflow music and sound: the workshop theme while you lay pipe, its hurried variant once the glow flows, with a
## bubbling loop under it; clunks for each piece, a clatter for a scrapped one, a tick as the cursor moves, ticks in
## the last seconds of the countdown, the valve opening, a gurgle per piece that climbs with the length, a chime for a
## loop, the splash of a leak, and the steam whistle for a finished pipeline. A sound that is not there yet is skipped.

const SFX := "res://games/brassflow/audio/sfx/"
const MUSIC := "res://games/brassflow/audio/music/"
const NAMES := ["place", "replace", "move", "flow_start", "fill", "cross_bonus", "spill", "passed", "failed", "game_over",
	"fast", "countdown_tick"]

@export var game: FlowGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _flow: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _tick_s := -1
var _cursor := Vector2i(-1, -1)


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
	_flow = AudioStreamPlayer.new()
	_flow.bus = "SFX"
	_flow.volume_db = -14.0
	add_child(_flow)
	if ResourceLoader.exists(SFX + "flow_loop.wav"):
		var w: AudioStream = load(SFX + "flow_loop.wav")
		if w is AudioStreamWAV:
			var ww := w as AudioStreamWAV
			ww.loop_mode = AudioStreamWAV.LOOP_FORWARD
			ww.loop_end = int(ww.get_length() * ww.mix_rate)
		_flow.stream = w
	_theme = _loop(MUSIC + "brassflow_theme.ogg")
	_hurry = _loop(MUSIC + "brassflow_hurry.ogg")
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		_tick_s = -1
		_flow.stop()
		if _theme and _music.stream != _theme:
			_music.stream = _theme
			_music.play()
		elif _theme and not _music.playing:
			_music.play())


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
	if e.cursor != _cursor:
		if _cursor != Vector2i(-1, -1) and e.phase == FlowEngine.Phase.PLAY:
			play("move", -18.0, randf_range(0.95, 1.05))
		_cursor = e.cursor
	if e.phase == FlowEngine.Phase.PLAY and not e.flowing and e.countdown < 5.0 and not e.fast:
		if ceili(e.countdown) != _tick_s:
			_tick_s = ceili(e.countdown)
			play("countdown_tick", -8.0, 1.0 + (5 - _tick_s) * 0.05)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"place": play("place", -4.0, randf_range(0.94, 1.06))
		"replace": play("replace", -4.0)
		"flow_start":
			play("flow_start", -3.0)
			if _flow.stream:
				_flow.play()
			if _hurry:
				_music.stream = _hurry
				_music.play()
		"fill":
			play("fill", -7.0, minf(1.0 + d["n"] * 0.025, 1.8))
			if d["cross_twice"]:
				play("cross_bonus", -3.0)
		"fast":
			play("fast", -3.0)
			_flow.pitch_scale = 1.4
		"spill":
			play("spill", -2.0)
			_flow.stop()
			_flow.pitch_scale = 1.0
			_music.stop()
		"passed": play("passed", -2.0)
		"failed": play("failed", -3.0)
		"game_over": play("game_over", -2.0)
