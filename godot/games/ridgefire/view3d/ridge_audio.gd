class_name RidgeAudio
extends Node
## Ridgefire music and sound: the march in battle and the shop tune between rounds; the cannon (heavier for the big
## ones), a whistle that rises as a shell comes down, blasts by size and the nuke's long roll, earth thudding, the
## roller's rumble, the drill, the MIRV's split, clangs on armour, wrecks, the aim's ticks, the turn chime, the wind
## (louder as it blows harder), the round's fanfare. A sound that is not there yet is skipped.

const R = preload("res://games/ridgefire/engine/ridge_engine.gd")
const SFX := "res://games/ridgefire/audio/sfx/"
const MUSIC := "res://games/ridgefire/audio/music/"
const NAMES := ["fire", "fire_big", "whistle", "boom_small", "boom", "nuke", "dirt", "dig", "mirv_split", "hit_tank", "tank_die",
	"aim_tick", "power_tick", "buy", "turn", "win", "round_start"]

@export var game: RidgeGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _wind: AudioStreamPlayer
var _roll: AudioStreamPlayer
var _whistle: AudioStreamPlayer
var _theme: AudioStream
var _shop: AudioStream
var _last_angle := -1
var _last_power := -1
var _mode := -1


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	add_child(_music)
	_wind = _loop_player("wind", -22.0)
	_roll = _loop_player("roller", -8.0)
	_whistle = AudioStreamPlayer.new()
	_whistle.bus = "SFX"
	_whistle.volume_db = -12.0
	if _streams.has("whistle"):
		_whistle.stream = _streams["whistle"]
	add_child(_whistle)
	_theme = _loop(MUSIC + "ridgefire_theme.ogg")
	_shop = _loop(MUSIC + "ridgefire_shop.ogg")
	game.round_started.connect(func(e):
		if not e.event.is_connected(_on_event):
			e.event.connect(_on_event)
		play("round_start", -4.0)
		if _wind.stream:
			_wind.play())


func _loop_player(name: String, db: float) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = "SFX"
	p.volume_db = db
	if ResourceLoader.exists(SFX + name + "_loop.wav") or ResourceLoader.exists(SFX + name + ".wav"):
		var path := SFX + name + ("_loop.wav" if ResourceLoader.exists(SFX + name + "_loop.wav") else ".wav")
		var w: AudioStream = load(path)
		if w is AudioStreamWAV:
			var ww := w as AudioStreamWAV
			ww.loop_mode = AudioStreamWAV.LOOP_FORWARD
			ww.loop_end = int(ww.get_length() * ww.mix_rate)
		p.stream = w
	add_child(p)
	return p


func _loop(path: String) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var m: AudioStream = load(path)
	if m is AudioStreamOggVorbis:
		(m as AudioStreamOggVorbis).loop = true
	return m


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	if not _streams.has(name):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _process(_delta: float) -> void:
	# the music follows the mode: the march in battle, the shop tune between rounds
	var want := 1 if game.mode == RidgeGame.Mode.SHOP else 0
	if want != _mode:
		_mode = want
		var s := _shop if want == 1 else _theme
		if s:
			_music.stream = s
			_music.play()
	var e := game.engine
	if e == null:
		return
	_wind.volume_db = -26.0 + absf(e.wind) * 1.4
	# ticks as a player turns the barrel or sets the power
	if e.phase == R.Phase.AIM and not e.current()["cpu"]:
		var a := roundi(e.current()["angle"])
		var pw := roundi(e.current()["power"] / 2.0)
		if _last_angle >= 0 and a != _last_angle:
			play("aim_tick", -18.0, 1.0 + a / 360.0)
		if _last_power >= 0 and pw != _last_power:
			play("power_tick", -18.0, 0.8 + pw / 100.0)
		_last_angle = a
		_last_power = pw
	else:
		_last_angle = -1
		_last_power = -1
	# the whistle of the first shell coming down, rising as it falls
	var falling := false
	var rolling := false
	for s in e.shots:
		if s["rolling"]:
			rolling = true
		elif s["vel"].y < -4.0:
			falling = true
			_whistle.pitch_scale = clampf(1.0 + (-s["vel"].y - 4.0) / 40.0, 1.0, 1.6)
	if falling and not _whistle.playing and _whistle.stream:
		_whistle.play()
	elif not falling and _whistle.playing:
		_whistle.stop()
	if rolling and not _roll.playing and _roll.stream:
		_roll.play()
	elif not rolling and _roll.playing:
		_roll.stop()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"fire": play("fire_big" if d["weapon"] in ["heavy", "nuke", "dirt"] else "fire", -3.0, randf_range(0.95, 1.05))
		"split": play("mirv_split", -4.0)
		"blast":
			var r: float = d["radius"]
			if d["weapon"] == "nuke":
				play("nuke", 0.0)
			elif r >= 4.0:
				play("boom", -2.0, randf_range(0.9, 1.0))
			else:
				play("boom_small", -3.0, randf_range(0.95, 1.1))
		"dirt": play("dirt", -3.0)
		"dig": play("dig", -4.0)
		"hit": play("hit_tank", -5.0, randf_range(0.9, 1.1))
		"die": play("tank_die", -1.0)
		"fall": if d["drop"] > 1.0: play("dirt", -10.0, 1.4)
		"turn": play("turn", -9.0)
		"round_end": play("win", -3.0)
