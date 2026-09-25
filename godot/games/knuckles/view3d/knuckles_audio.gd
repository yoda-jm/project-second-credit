class_name KnucklesAudio
extends Node
## Music and sound for Neon Knuckles, driven by the engine's events.

const SFX := "res://games/knuckles/audio/sfx/"
const NAMES := ["punch", "heavy", "swing", "bat", "slash", "grunt", "fall", "ko", "pickup", "go", "clear", "game_over"]

@export var game: KnucklesGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/knuckles/audio/music/knuckles_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		create_tween().tween_property(_music, "volume_db", -9.0, 2.0))


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.92, 1.08)
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"swing": play("swing", -12.0, 1.1 if d["attack"] in ["jab", "punch"] else 0.85)
		"hit":
			match d["attack"]:
				"bat", "crate": play("bat", -1.0)
				"knife": play("slash", -2.0)
				_: play("heavy" if d["damage"] >= 14 else "punch", -2.0)
			if randf() < 0.4:
				play("grunt", -8.0, randf_range(0.8, 1.2))
		"slam", "knockdown": play("fall", -4.0)
		"ko": play("ko", -4.0)
		"pickup": play("pickup", -4.0)
		"go": play("go", -3.0)
		"stage_clear":
			play("clear", 0.0)
			create_tween().tween_property(_music, "volume_db", -24.0, 0.5)
		"game_over":
			play("game_over", 0.0)
			create_tween().tween_property(_music, "volume_db", -30.0, 1.0)
