class_name InkAudio
extends Node
## Inkstorm music and sound: the theme, a tense loop when the target is close, the pen scratching (fast) or the brush
## (slow) while a line is drawn, the fuse hissing, a bloom when land is claimed, a bell for every 5 percent.

const SFX := "res://games/inkstorm/audio/sfx/"
const NAMES := ["claim_small", "claim_big", "percent_tick", "spark_spawn", "storm_split", "die", "ready", "stage_clear",
	"game_over", "extra_life"]

@export var game: InkGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _tension: AudioStream
var _pen: AudioStreamPlayer
var _brush: AudioStreamPlayer
var _fuse: AudioStreamPlayer
var _last_pos := Vector2i(-1, -1)
var _moving := 0.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 8:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/inkstorm/audio/music/inkstorm_theme.ogg")
	_tension = load("res://games/inkstorm/audio/music/inkstorm_tension.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_tension as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -12.0
	_music.stream = _theme
	add_child(_music)
	_pen = _loop("draw_fast", -10.0)
	_brush = _loop("draw_slow", -9.0)
	_fuse = _loop("fuse", -6.0)
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		play("ready", -3.0)
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
	var tense := e.claimed > InkEngine.TARGET - 0.12 and e.phase == InkEngine.Phase.PLAY
	if tense and _music.stream != _tension:
		_music.stream = _tension
		_music.play()
	elif not tense and _music.stream == _tension and e.phase != InkEngine.Phase.CLEARED:
		_music.stream = _theme
		_music.play()
	if e.pos != _last_pos:
		_last_pos = e.pos
		_moving = 0.1
	_moving -= delta
	var drawing := e.drawing() and _moving > 0.0 and e.phase == InkEngine.Phase.PLAY
	var slow := drawing and e.draw_slow and not e.draw_fast
	_set_loop(_pen, drawing and not slow)
	_set_loop(_brush, slow)
	_set_loop(_fuse, e.fuse >= 0.0 and e.drawing() and e.phase == InkEngine.Phase.PLAY)


func _set_loop(p: AudioStreamPlayer, on: bool) -> void:
	if on and not p.playing:
		p.play()
	elif not on and p.playing:
		p.stop()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"claim":
			var before: float = d["percent"] - float(d["cells"]) / ((InkEngine.W - 2) * (InkEngine.H - 2))
			play("claim_big" if d["cells"] > 600 else "claim_small", -4.0)
			var ticks := int(d["percent"] * 20.0) - int(before * 20.0)
			for i in mini(ticks, 4):
				get_tree().create_timer(0.25 + i * 0.12).timeout.connect(func(): play("percent_tick", -8.0, 1.0 + i * 0.12))
		"spark_spawn": play("spark_spawn", -6.0)
		"split": play("storm_split", -3.0)
		"die": play("die", -2.0)
		"cleared": play("stage_clear", -2.0)
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
