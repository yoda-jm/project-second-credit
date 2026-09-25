class_name FruitburrowAudio
extends Node
## Music and sound effects for Fruitburrow, driven by the engine's events. Fruit picked in a quick run rises in
## pitch, like a little scale.

const SFX := "res://games/fruitburrow/audio/sfx/"
const NAMES := ["dig", "fruit", "apple_wobble", "apple_fall", "apple_land", "apple_break", "squash", "throw", "bounce",
	"monster_hit", "monster_spawn", "transform", "ball_back", "death", "clear", "game_over"]

@export var game: FruitburrowGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _combo := 0
var _combo_t := 0.0
var _dig_t := 0.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/fruitburrow/audio/music/garden_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	create_tween().tween_property(_music, "volume_db", -10.0, 3.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	game.garden_started.connect(func(e):
		if not e.event.is_connected(_on_event):
			e.event.connect(_on_event))
	if game.engine:
		game.engine.event.connect(_on_event)


func _process(delta: float) -> void:
	_combo_t -= delta
	_dig_t -= delta
	if _combo_t <= 0.0:
		_combo = 0


func play(name: String, db: float = 0.0, pitch: float = 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.97, 1.03)
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"dig":
			if d["by"] == "player" and _dig_t <= 0.0:
				play("dig", -6.0, randf_range(0.9, 1.15))
				_dig_t = 0.12
			elif d["by"] == "monster":
				play("dig", -14.0, 0.7)
		"fruit":
			play("fruit", -3.0, pow(2.0, float(mini(_combo, 7)) / 12.0 * 2.0))
			_combo += 1
			_combo_t = 1.6
		"apple_wobble": play("apple_wobble", -4.0)
		"apple_fall": play("apple_fall", -8.0)
		"apple_land": play("apple_land", -3.0)
		"apple_break": play("apple_break", -2.0)
		"squash": play("squash", 0.0, 1.0 + 0.1 * d.get("points", 500) / 500.0)
		"throw": play("throw", -4.0)
		"ball_bounce": play("bounce", -12.0, randf_range(0.9, 1.2))
		"monster_hit": play("monster_hit", -2.0)
		"monster_spawn": play("monster_spawn", -8.0)
		"transform": play("transform", -4.0)
		"ball_back": play("ball_back", -8.0)
		"death":
			play("death", 0.0)
			create_tween().tween_property(_music, "volume_db", -24.0, 0.3)
		"phase":
			if d["phase"] == FruitburrowEngine.Phase.PLAY:
				create_tween().tween_property(_music, "volume_db", -10.0, 1.0)
		"clear":
			play("clear", 0.0)
		"game_over":
			play("game_over", 0.0)
			create_tween().tween_property(_music, "volume_db", -30.0, 1.5)
