class_name DriftAudio
extends Node
## Marble Drift music and sound: the racing theme (a hurried one in the last ten seconds), the marble rolling (a loop
## that rises and swells with speed, rougher on rough floor, silent in the air), wall knocks, landings, the glass
## shattering, acid, the fall, checkpoints, enemies' knocks, the countdown, the goal fanfare and the buzzer.
## A sound that is not there yet is skipped.

const SFX := "res://games/marbledrift/audio/sfx/"
const MUSIC := "res://games/marbledrift/audio/music/"
const NAMES := ["bump", "land", "shatter", "acid", "fall", "respawn", "checkpoint", "knock_steelie", "knock_hopper", "finish",
	"countdown_beep", "go", "time_low", "time_up"]

@export var game: DriftGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _roll: AudioStreamPlayer
var _rough: AudioStreamPlayer
var _beeps := 0


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	add_child(_music)
	_theme = _loop_ogg(MUSIC + "marbledrift_theme.ogg")
	_hurry = _loop_ogg(MUSIC + "marbledrift_hurry.ogg")
	_roll = _loop_wav(SFX + "roll_loop.wav")
	_rough = _loop_wav(SFX + "roll_rough_loop.wav")
	game.course_started.connect(func(e):
		e.event.connect(_on_event)
		_beeps = 0
		if _theme:
			_music.stream = _theme
			_music.play())


func _loop_ogg(path: String) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var m: AudioStream = load(path)
	if m is AudioStreamOggVorbis:
		(m as AudioStreamOggVorbis).loop = true
	return m


func _loop_wav(path: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	p.volume_db = -60.0
	add_child(p)
	if ResourceLoader.exists(path):
		var w: AudioStreamWAV = load(path)
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = int(w.get_length() * w.mix_rate)
		p.stream = w
		p.play()
	return p


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	if not _streams.has(name):
		return
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
	# the rolling loops follow the marble's speed (and the floor under it)
	var v: Vector3 = e.ball["vel"]
	var speed := Vector2(v.x, v.z).length()
	var rolling: bool = e.phase == DriftEngine.Phase.PLAY and not e.ball["air"] and speed > 0.2
	var p: Vector3 = e.ball["pos"]
	var rough := e.course.kind(int(floor(p.x)), int(floor(p.z))) == "^"
	var loud := linear_to_db(clampf(speed / 9.0, 0.02, 1.0)) - 6.0
	_roll.volume_db = lerpf(_roll.volume_db, loud if rolling and not rough else -60.0, 1.0 - exp(-delta * 12.0))
	_rough.volume_db = lerpf(_rough.volume_db, loud if rolling and rough else -60.0, 1.0 - exp(-delta * 12.0))
	_roll.pitch_scale = 0.7 + clampf(speed / 12.0, 0.0, 1.0) * 0.8
	_rough.pitch_scale = _roll.pitch_scale
	# the countdown
	if e.phase == DriftEngine.Phase.READY:
		var n := 3 - int(ceil(e.phase_t / 0.66))
		if n > _beeps and n <= 2:
			_beeps = n
			play("countdown_beep", -4.0)
	if e.phase == DriftEngine.Phase.PLAY and e.clock < 10.0 and _hurry and _music.stream != _hurry:
		_music.stream = _hurry
		_music.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"go": play("go", -3.0)
		"bump": play("bump", clampf(-14.0 + d["speed"], -14.0, 0.0), randf_range(0.9, 1.1))
		"land": play("land", clampf(-12.0 + d["drop"] * 3.0, -12.0, 0.0))
		"shatter": play("shatter", -1.0)
		"acid": play("acid", -2.0)
		"fall": play("fall", -2.0)
		"respawn": play("respawn", -4.0)
		"checkpoint": play("checkpoint", -4.0, 1.0 + d["n"] * 0.03)
		"knock": play("knock_" + d["kind"], -3.0, randf_range(0.9, 1.1))
		"finish":
			play("finish", -1.0)
			_music.stop()
		"time_low": play("time_low", -2.0)
		"time_up":
			play("time_up", -1.0)
			_music.stop()
