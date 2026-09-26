class_name IngotAudio
extends Node
## Ingot Run music and sound, driven by the engine's events.

const SFX := "res://games/ingot/audio/sfx/"
const NAMES := ["step", "ladder", "bar", "fall", "land", "dig", "refill", "gold", "all_gold", "trapped", "guard_escape",
	"guard_crushed", "guard_respawn", "die", "level_clear"]

@export var game: IngotGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _step_t := 0.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/ingot/audio/music/ingot_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -11.0
	add_child(_music)
	_music.play()
	game.level_started.connect(func(e): e.event.connect(_on_event))


func play(name: String, db := 0.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = randf_range(0.95, 1.05)
	p.play()


func _process(delta: float) -> void:
	var e := game.engine
	if e == null or e.phase != IngotEngine.Phase.PLAY:
		return
	_step_t -= delta
	var r := e.runner
	if r["state"] == "move" and _step_t <= 0.0:
		var d: Vector2i = r["to"] - r["cell"]
		var here := e.at(r["cell"])
		if d.y != 0:
			play("ladder", -12.0)
			_step_t = 0.2
		elif here == IngotLevel.T.BAR:
			play("bar", -12.0)
			_step_t = 0.22
		else:
			play("step", -14.0)
			_step_t = 0.16


func _on_event(kind: String, _d: Dictionary) -> void:
	match kind:
		"dig": play("dig", -4.0)
		"refill": play("refill", -10.0)
		"gold": play("gold", -4.0)
		"all_gold": play("all_gold", -2.0)
		"trapped": play("trapped", -5.0)
		"escape": play("guard_escape", -7.0)
		"crushed": play("guard_crushed", -4.0)
		"respawn": play("guard_respawn", -8.0)
		"died": play("die", -2.0)
		"cleared": play("level_clear", -2.0)
		"land": play("land", -10.0)
