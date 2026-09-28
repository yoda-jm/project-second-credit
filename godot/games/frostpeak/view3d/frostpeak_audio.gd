class_name FrostpeakAudio
extends Node
## Music and sound for Frostpeak Games: the theme between attempts, the crowd and the wind during them, the
## countdown and the pistol, strides, take-offs and landings, cheers and the medal fanfare; the replay's wipes and its
## slow-motion take-off and landing; the biathlon's pushes, the rifle, the targets and the heart at the range; the
## bobsled's push steps, the crew dropping in, the runners rumbling faster down the run, wall hits and the brake.

const SFX := "res://games/frostpeak/audio/sfx/"
const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage

@export var game: FrostpeakGame
@export var view: FrostpeakView3D

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _crowd: AudioStreamPlayer
var _wind: AudioStreamPlayer
var _last_count := -1
var _last_wipe := -1.0
var _run: AudioStreamPlayer  ## the bob's runners on the ice


func _ready() -> void:
	for n in ["cheer", "stride", "pistol", "beep", "beep_go", "takeoff", "land", "fall", "fanfare", "swoosh", "rifle",
			"target_hit", "target_miss", "heartbeat", "ski_push", "bob_scrape", "bob_step", "bob_load", "bob_brake"]:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = _loop(load("res://games/frostpeak/audio/music/frostpeak_theme.ogg"), "Music")
	_crowd = _loop(_looping_wav("crowd"), "SFX")
	_wind = _loop(_looping_wav("wind"), "SFX")
	_run = _loop(_looping_wav("bob_run"), "SFX")
	game.stage_changed.connect(_on_stage)
	game.attempt_started.connect(func(ev): ev.event.connect(_on_event))
	if view:
		view.tv_sound.connect(func(n: String, db: float, pitch: float) -> void: play(n, db, pitch))


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
			if game.ev is Bobsled:
				_fade(_run, -60.0, 2.5)
				_fade(_wind, -60.0, 1.0)
				if not (game.ev as Bobsled).crashed:
					play("bob_brake", -5.0)
		S.REPLAY:
			_fade(_crowd, -18.0, 0.6)
			_fade(_wind, -60.0, 0.4)
		S.PODIUM:
			_fade(_music, -30.0, 0.5)
			play("fanfare", -2.0)
			_fade(_crowd, -16.0)
		_:
			_fade(_music, -9.0, 2.0)
			_fade(_crowd, -24.0)
			_fade(_wind, -60.0)
			_fade(_run, -60.0, 0.6)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"go": play("beep_go" if game.ev is SkiJump else "pistol", -2.0)
		"stride":
			if game.ev is Bobsled:
				play("bob_step", -6.0 if d["quality"] == "perfect" else -9.0, randf_range(0.9, 1.15))
			elif game.ev is Biathlon:
				play("ski_push", -7.0 if d["quality"] == "perfect" else -11.0, randf_range(0.9, 1.1))
			else:
				play("stride", -6.0 if d["quality"] == "perfect" else -10.0, randf_range(0.9, 1.1))
		"shot":
			play("rifle", -3.0)
			var sound := "target_hit" if d["hit"] else "target_miss"
			get_tree().create_timer(0.17).timeout.connect(func() -> void: play(sound, -6.0))
		"beat":
			if view and view.bview.scope_k > 0.5:
				play("heartbeat", -14.0, 1.0)
		"range_done":
			if d["misses"] == 0:
				play("cheer", -4.0)
		"penalty":
			_fade(_crowd, -12.0, 1.0)
		"load":
			for i in 4:  # the four drop in, one after another
				get_tree().create_timer(0.08 + i * Bobsled.LOAD_T / 4.0 + 0.3).timeout.connect(func() -> void: play("bob_load", -8.0 - i, randf_range(0.9, 1.1)))
		"wall":
			play("bob_scrape", clampf(-14.0 + float(d["strength"]) * 4.0, -14.0, -2.0), randf_range(0.9, 1.1))
		"crash":
			play("bob_scrape", 0.0, 0.8)
			play("fall", -4.0, 0.7)
			_fade(_crowd, -6.0, 0.5)
		"split":
			_fade(_crowd, -10.0, 0.3)
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
	if view:  # a wipe sweeps across
		var w := view.wipe_time()
		if w >= 0.0 and (_last_wipe < 0.0 or w < _last_wipe):
			play("swoosh", -8.0)
		_last_wipe = w
	var ev := game.ev
	if ev == null or game.stage != S.ATTEMPT:
		return
	if ev.phase == WinterEvent.Phase.READY:
		var c := ceili(ev.phase_left)
		if c != _last_count and c <= 3 and c >= 1:
			play("beep", -8.0)
		_last_count = c
	if ev is Biathlon:
		var b := ev as Biathlon
		_wind.volume_db = lerpf(_wind.volume_db, lerpf(-40.0, -14.0, clampf((b.speed - 6.0) / 7.0, 0.0, 1.0)) if b.tuck > 0.5 else -40.0, 0.05)
		_crowd.volume_db = lerpf(_crowd.volume_db, -12.0 if b.stage == Biathlon.Stage.RANGE else -16.0, 0.02)
	if ev is Bobsled:
		var bo := ev as Bobsled
		var riding := bo.stage == Bobsled.Stage.RIDE or bo.stage == Bobsled.Stage.CRASH
		var sp := bo.speed
		_run.volume_db = lerpf(_run.volume_db, lerpf(-30.0, -4.0, clampf(sp / 35.0, 0.0, 1.0)) if riding and sp > 1.0 else -60.0, 0.1)
		_run.pitch_scale = lerpf(0.7, 1.35, clampf(sp / 36.0, 0.0, 1.0)) * (0.8 if bo.crashed else 1.0)
		_wind.volume_db = lerpf(_wind.volume_db, lerpf(-40.0, -12.0, clampf((sp - 15.0) / 20.0, 0.0, 1.0)) if riding else -50.0, 0.05)
		_crowd.volume_db = lerpf(_crowd.volume_db, -16.0, 0.01)
	if ev is SkiJump:
		var j := ev as SkiJump
		var target := -40.0
		if j.stage == SkiJump.Stage.INRUN:
			target = lerpf(-40.0, -10.0, clampf(j.speed / 25.0, 0.0, 1.0))
		elif j.stage == SkiJump.Stage.FLIGHT:
			target = -6.0
		_wind.volume_db = lerpf(_wind.volume_db, target, 0.1)
