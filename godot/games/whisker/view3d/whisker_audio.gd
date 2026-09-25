class_name WhiskerAudio
extends Node
## Music and sound effects for Whisker Alley, driven by the engine's events.

const SFX := "res://games/whisker/audio/sfx/"
const NAMES := ["meow", "sad_meow", "jump", "bounce", "land", "bark", "creak", "whoosh", "bonk", "splash", "catch",
	"squeak", "cage_crash", "chirp", "swish", "zap", "room_won", "game_over"]

@export var game: WhiskerGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/whisker/audio/music/alley_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	create_tween().tween_property(_music, "volume_db", -9.0, 3.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	game.started.connect(func(e): e.event.connect(_on_event))
	if game.engine:
		game.engine.event.connect(_on_event)


func play(name: String, db: float = 0.0, pitch: float = 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.95, 1.05)
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"jump": play("jump", -6.0)
		"bounce": play("bounce", -3.0)
		"land": play("land", -12.0)
		"dog_bark": play("bark", -2.0, randf_range(0.9, 1.1))
		"window_open": play("creak", -16.0, randf_range(0.85, 1.2))
		"shoe": play("whoosh", -8.0)
		"shoe_hit":
			play("bonk", -2.0)
			play("meow", -6.0, 1.25)
		"enter_room":
			play("meow", -4.0)
			create_tween().tween_property(_music, "volume_db", -14.0, 0.5)
		"leave_room": create_tween().tween_property(_music, "volume_db", -9.0, 0.8)
		"splash": play("splash", -3.0)
		"catch":
			play("catch", -2.0)
			if d["what"] == "mouse":
				play("squeak", -6.0, 1.2)
			elif d["what"] == "bird":
				play("chirp", -4.0)
		"squeak": play("squeak", -12.0)
		"cage_crash":
			play("cage_crash", -2.0)
			play("chirp", -6.0)
		"broom": play("swish", -2.0)
		"zap": play("zap", 0.0)
		"death": play("sad_meow", -2.0)
		"room_won": play("room_won", -1.0)
		"game_over":
			play("game_over", 0.0)
			create_tween().tween_property(_music, "volume_db", -30.0, 1.5)
