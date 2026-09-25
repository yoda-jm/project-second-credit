class_name FrostpeakAudio
extends Node
## Music and sound for Frostpeak Games: the theme between attempts, the crowd and the wind during them, the
## countdown and the pistol, strides, take-offs and landings, cheers and the medal fanfare.

const SFX := "res://games/frostpeak/audio/sfx/"
const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage

@export var game: FrostpeakGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _crowd: AudioStreamPlayer
var _wind: AudioStreamPlayer
var _last_count := -1


func _ready() -> void:
	for n in ["cheer", "stride", "pistol", "beep", "beep_go", "takeoff", "land", "fall", "fanfare"]:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = _loop(load("res://games/frostpeak/audio/music/frostpeak_theme.ogg"), "Music")
	_crowd = _loop(_looping_wav("crowd"), "SFX")
	_wind = _loop(_looping_wav("wind"), "SFX")
	game.stage_changed.connect(_on_stage)
	game.attempt_started.connect(func(ev): ev.event.connect(_on_event))


func _looping_wav(name: String) -> AudioStreamWAV:
	var w: AudioStreamWAV = load(SFX + name + ".wav")
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_end = int(w.get_length() * w.mix_rate)
	return w


func _loop(stream: AudioStream, bus: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	if stream is AudioStreamOggVorbis:
		(stream as AudioStreamOggVorbis).loop = true
	p.stream = stream
	p.bus = bus
	p.volume_db = -60.0
	add_child(p)
	p.play()
	return p


func _fade(p: AudioStreamPlayer, db: float, secs := 1.0) -> void:
	create_tween().tween_property(p, "volume_db", db, secs).set_trans(Tween.TRANS_SINE)


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.96, 1.04)
	p.play()


func _on_stage(stage: int) -> void:
	match stage:
		S.ATTEMPT:
			_fade(_music, -26.0)
			_fade(_crowd, -14.0)
		S.RESULT:
			_fade(_crowd, -8.0, 0.4)
			play("cheer", -4.0)
		S.PODIUM:
			_fade(_music, -30.0, 0.5)
			play("fanfare", -2.0)
			_fade(_crowd, -16.0)
		_:
			_fade(_music, -9.0, 2.0)
			_fade(_crowd, -24.0)
			_fade(_wind, -60.0)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"go": play("pistol" if game.ev is SpeedSkating else "beep_go", -2.0)
		"stride": play("stride", -6.0 if d["quality"] == "perfect" else -10.0, randf_range(0.9, 1.1))
		"stumble": play("fall", -10.0, 1.4)
		"false_start": play("pistol", -4.0, 0.8)
		"takeoff":
			play("takeoff", -3.0)
			_fade(_crowd, -8.0, 1.5)
		"landed":
			play("fall" if d["fell"] else "land", -2.0)
			if not d["fell"]:
				play("cheer", -3.0)


func _process(_delta: float) -> void:
	var ev := game.ev
	if ev == null or game.stage != S.ATTEMPT:
		return
	if ev.phase == WinterEvent.Phase.READY:
		var c := ceili(ev.phase_left)
		if c != _last_count and c <= 3 and c >= 1:
			play("beep", -8.0)
		_last_count = c
	if ev is SkiJump:
		var j := ev as SkiJump
		var target := -40.0
		if j.stage == SkiJump.Stage.INRUN:
			target = lerpf(-40.0, -10.0, clampf(j.speed / 25.0, 0.0, 1.0))
		elif j.stage == SkiJump.Stage.FLIGHT:
			target = -6.0
		_wind.volume_db = lerpf(_wind.volume_db, target, 0.1)
