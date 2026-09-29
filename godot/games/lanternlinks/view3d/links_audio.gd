class_name LinksAudio
extends Node
## Lantern Links sound: the putt (pitched by power), wooden banks, bumpers, blades, blocks and the turnstile (loud
## as the knock), the cup's drop and its lip, splashes, sand, the loop's whoosh, pipes, boosters, landings; the
## ball's roll on the felt (a loop following its speed); the windmill creaking near the camera; crickets as night
## falls; jingles for each result and fireworks for a hole in one. The music turns from the evening lounge theme to
## its night variation over the back nine. A sound that is not there yet is skipped.

const SFX := "res://games/lanternlinks/audio/sfx/"
const MUSIC := "res://games/lanternlinks/audio/music/"
const B = preload("res://games/lanternlinks/engine/links_ball.gd")
const E = preload("res://games/lanternlinks/engine/links_engine.gd")
const NAMES := ["putt_soft", "putt_hard", "bank_1", "bank_2", "bumper", "cup", "lip", "splash", "fall", "land", "sand",
	"blade", "loop_whoosh", "pipe_in", "pipe_out", "boost", "mover", "spinner", "tee", "card", "holed_par",
	"holed_birdie", "hole_in_one", "holed_bogey", "penalty", "round_win", "firework_launch", "firework_burst"]

@export var game: LinksGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _theme: AudioStreamPlayer
var _night: AudioStreamPlayer
var _roll: AudioStreamPlayer
var _mill: AudioStreamPlayer
var _crickets: AudioStreamPlayer
var _night_mix := 0.0


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = _music("lanternlinks_theme.ogg")
	_night = _music("lanternlinks_night.ogg")
	_roll = _loop("roll_loop.wav")
	_mill = _loop("windmill_loop.wav")
	_crickets = _loop("crickets_loop.wav")
	game.game_started.connect(func(e):
		e.event.connect(_on_event)
		_night_mix = 1.0 if e.hole_i >= 5 else 0.0)
	if _theme.stream:
		_theme.play()
	if _night.stream:
		_night.play()
	for l in [_roll, _mill, _crickets]:
		if l.stream:
			l.volume_db = -80.0
			l.play()


func _music(name: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "Music"
	p.volume_db = -80.0
	if ResourceLoader.exists(MUSIC + name):
		var m: AudioStream = load(MUSIC + name)
		if m is AudioStreamOggVorbis:
			(m as AudioStreamOggVorbis).loop = true
		p.stream = m
	add_child(p)
	return p


func _loop(name: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	if ResourceLoader.exists(SFX + name):
		var w: AudioStreamWAV = (load(SFX + name) as AudioStreamWAV).duplicate()
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = int(w.get_length() * w.mix_rate)
		p.stream = w
	add_child(p)
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


static func _loud(speed: float, lo := -26.0, hi := -4.0) -> float:
	return lerpf(lo, hi, clampf(speed / 3.5, 0.0, 1.0))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot":
			var pw: float = d["power"]
			play("putt_hard" if pw > 0.55 else "putt_soft", lerpf(-12.0, -2.0, pw), randf_range(0.97, 1.03) * lerpf(1.08, 0.94, pw))
		"bank":
			play("bank_%d" % (1 + randi() % 2), _loud(d["speed"]), randf_range(0.92, 1.08))
		"bumper": play("bumper", -3.0, randf_range(0.95, 1.05))
		"blade": play("blade", _loud(d["speed"], -18.0, -3.0))
		"mover": play("mover", _loud(d["speed"], -20.0, -4.0))
		"spinner": play("spinner", _loud(d["speed"], -18.0, -3.0))
		"land": play("land", _loud(d["speed"], -20.0, -6.0))
		"sink": play("cup", -2.0)
		"lip": play("lip", -4.0)
		"splash": play("splash", -3.0)
		"fall": play("fall", -5.0)
		"loop_in": play("loop_whoosh", -4.0, 0.9 + float(d["speed"]) * 0.05)
		"pipe_in": play("pipe_in", -4.0)
		"pipe_out": play("pipe_out", -4.0)
		"boost": play("boost", -8.0)
		"tee": play("tee", -10.0)
		"card": play("card", -6.0)
		"penalty": play("penalty", -6.0)
		"holed":
			var s: int = d["strokes"]
			var over: int = s - int(d["par"])
			if s == 1:
				play("hole_in_one", -2.0)
				for k in 6:
					get_tree().create_timer(randf_range(0.0, 0.5)).timeout.connect(func(): play("firework_launch", -14.0, randf_range(0.9, 1.1)))
					get_tree().create_timer(randf_range(1.0, 1.7)).timeout.connect(func(): play("firework_burst", -9.0, randf_range(0.85, 1.15)))
			elif over < 0:
				play("holed_birdie", -3.0)
			elif over == 0:
				play("holed_par", -4.0)
			else:
				play("holed_bogey", -7.0)
		"final":
			play("round_win", -3.0)
		"hole":
			_night_mix = 1.0 if int(d["index"]) >= 5 else 0.0


func _process(delta: float) -> void:
	var e := game.engine
	# the music: the evening theme, then its night variation
	var cur_theme := linear_to_db(maxf(1.0 - _night_mix, 0.0001)) - 11.0
	var cur_night := linear_to_db(maxf(_night_mix, 0.0001)) - 10.0
	_theme.volume_db = move_toward(_theme.volume_db, cur_theme, delta * 12.0)
	_night.volume_db = move_toward(_night.volume_db, cur_night, delta * 12.0)
	if e == null:
		return
	# the ball's roll
	var rolling := e.phase == E.Phase.ROLL and e.ball.mode == B.Mode.ROLL
	var sp := e.ball.vel.length() if rolling else 0.0
	var target := lerpf(-40.0, -9.0, clampf(sp / 3.0, 0.0, 1.0)) if sp > 0.05 else -80.0
	_roll.volume_db = move_toward(_roll.volume_db, target, delta * 120.0)
	_roll.pitch_scale = 0.8 + clampf(sp / 3.0, 0.0, 1.0) * 0.5
	# the windmill creaks when the camera is near it
	var mill := -80.0
	var cam := get_viewport().get_camera_3d()
	for g in e.hole.gadgets:
		if g["type"] == "windmill" and cam:
			var hub: Vector2 = g["hub"]
			var dist := cam.global_position.distance_to(Vector3(hub.x, 0.8, hub.y))
			mill = maxf(mill, lerpf(-10.0, -34.0, clampf(dist / 8.0, 0.0, 1.0)))
	_mill.volume_db = move_toward(_mill.volume_db, mill, delta * 40.0)
	# crickets as night falls
	var n := float(e.hole_i) / maxf(1.0, e.holes.size() - 1)
	_crickets.volume_db = move_toward(_crickets.volume_db, lerpf(-40.0, -15.0, smoothstep(0.3, 1.0, n)), delta * 10.0)
