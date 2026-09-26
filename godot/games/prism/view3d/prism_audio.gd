class_name PrismAudio
extends Node
## Prism Breaker music and sound: the theme, glass chimes that climb the scale as bricks fall between two paddle
## touches, a clink for hard bricks, a ring for steel, and a sound for each capsule.

const SFX := "res://games/prism/audio/sfx/"
const NAMES := ["paddle", "wall", "brick_0", "brick_1", "brick_2", "brick_3", "brick_4", "brick_5", "hard", "steel",
	"capsule", "laser", "grow", "shrink", "catch", "multiball", "slow", "extra_life", "drone_pop", "lose_ball", "launch",
	"ready", "stage_clear", "warp", "game_over"]
const CAPSULE_SOUND := {"wide": "grow", "laser": "capsule", "catch": "catch", "slow": "slow", "multi": "multiball",
	"life": "extra_life", "break": "capsule"}

@export var game: PrismGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _combo := 0
var _music: AudioStreamPlayer
var _wide := false


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	var theme: AudioStreamOggVorbis = load("res://games/prism/audio/music/prism_theme.ogg")
	theme.loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	_music.stream = theme
	add_child(_music)
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		_combo = 0
		_wide = false
		play("ready", -3.0)
		if not _music.playing:
			_music.play())


func play(name: String, db := 0.0, pitch := 1.0) -> void:
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
	var wide := e.paddle_w > 2.5
	if _wide and not wide:
		play("shrink", -6.0)
	_wide = wide


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"paddle":
			_combo = 0
			play("paddle", -4.0)
		"wall": play("wall", -10.0)
		"brick":
			if d["broken"]:
				play("brick_%d" % mini(_combo, 5), -5.0)
				_combo += 1
			elif d["kind"] == "H":
				play("hard", -5.0)
			else:
				play("steel", -7.0)
		"capsule": play(CAPSULE_SOUND[d["kind"]], -3.0)
		"laser": play("laser", -8.0)
		"drone_pop": play("drone_pop", -4.0)
		"lose_ball": play("lose_ball", -2.0)
		"launch": play("launch", -6.0)
		"cleared": play("stage_clear", -2.0)
		"warp": play("warp", -2.0)
		"game_over": play("game_over", -2.0)
