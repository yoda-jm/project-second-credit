class_name CratesAudio
extends Node
## Crate Keeper music, harbour ambience and sound, driven by the engine's events.

const SFX := "res://games/crates/audio/sfx/"
const NAMES := ["step_0", "step_1", "step_2", "push", "bump", "on_goal", "off_goal", "undo", "restart", "solved", "star"]

@export var game: CratesGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _step := 0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	var music := AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/crates/audio/music/crates_theme.ogg")
	theme.loop = true
	music.stream = theme
	music.bus = "Music"
	music.volume_db = -12.0
	add_child(music)
	music.play()
	var amb := AudioStreamPlayer.new()
	var wav: AudioStreamWAV = load(SFX + "ambience.wav")
	wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
	wav.loop_end = int(wav.get_length() * wav.mix_rate)
	amb.stream = wav
	amb.bus = "SFX"
	amb.volume_db = -14.0
	add_child(amb)
	amb.play()
	game.puzzle_started.connect(func(e): e.event.connect(_on_event))


func play(name: String, db := 0.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = randf_range(0.96, 1.04)
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"move":
			_step = (_step + 1) % 3
			play("step_%d" % _step, -8.0)
			if d["pushed"] >= 0:
				play("push", -4.0)
		"bump": play("bump", -6.0)
		"on_goal": play("on_goal", -3.0)
		"off_goal": play("off_goal", -6.0)
		"undo": play("undo", -8.0)
		"restart": play("restart", -5.0)
		"solved":
			play("solved", -2.0)
			get_tree().create_timer(0.9).timeout.connect(func(): play("star", -4.0))
