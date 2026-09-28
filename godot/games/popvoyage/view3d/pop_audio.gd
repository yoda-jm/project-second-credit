class_name PopAudio
extends Node
## Pop Voyage music and sound: the travel theme (its hurried variant in the last fifteen seconds), the wire's zip,
## rubbery pops that deepen with the balloon's size, bounces, breaking blocks, items, the shield, the time stop, the
## charge, and the stage's fanfare with the time bonus ticking in. A sound that is not there yet is skipped.

const SFX := "res://games/popvoyage/audio/sfx/"
const MUSIC := "res://games/popvoyage/audio/music/"
const NAMES := ["fire", "wire_stick", "pop_0", "pop_1", "pop_2", "pop_3", "split", "bounce_small", "bounce_big", "block_break",
	"item_drop", "item_take", "shield_on", "shield_lost", "freeze", "charge", "die", "timeout_warn", "stage_start", "stage_clear",
	"bonus_tick", "game_over", "extra_life"]

@export var game: PopGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _warned := false
var _beep_s := -1
var _tick_t := 0.0
var _vy := {}


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -9.0
	add_child(_music)
	_theme = _loop(MUSIC + "popvoyage_theme.ogg")
	_hurry = _loop(MUSIC + "popvoyage_hurry.ogg")
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		_warned = false
		play("stage_start", -3.0)
		if _theme:
			_music.stream = _theme
			_music.play())


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


func _process(delta: float) -> void:
	var e := game.engine
	if e == null:
		return
	if e.phase == PopEngine.Phase.READY and not _music.playing and _theme:
		# the stage starts again after a life is lost
		_warned = false
		_music.stream = _theme
		_music.play()
	if e.phase == PopEngine.Phase.PLAY and e.clock < 15.0:
		# a double beep each second of the last fifteen
		if ceili(e.clock) != _beep_s:
			_beep_s = ceili(e.clock)
			play("timeout_warn", -6.0 + (15.0 - e.clock) * 0.2)
	if e.phase == PopEngine.Phase.PLAY and e.clock < 15.0 and not _warned:
		_warned = true
		if _hurry:
			_music.stream = _hurry
			_music.play()
	# a thud each time a balloon comes off the floor
	for i in e.balls.size():
		var b: Dictionary = e.balls[i]
		var vy: float = b["vel"].y
		if _vy.get(i, 0.0) < -1.0 and vy > 1.0 and b["pos"].y < P_RADIUS(b["size"]) + 0.3:
			play("bounce_big" if b["size"] >= 2 else "bounce_small", -16.0 + b["size"] * 2.0, randf_range(0.95, 1.05))
		_vy[i] = vy
	if e.phase == PopEngine.Phase.CLEARED and e.clock > 0.0:
		_tick_t -= delta
		if _tick_t <= 0.0:
			_tick_t = 0.06
			play("bonus_tick", -12.0)


static func P_RADIUS(s: int) -> float:
	return PopEngine.RADIUS[s]


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"fire": play("fire", -6.0, randf_range(0.97, 1.03))
		"split":
			play("pop_%d" % d["size"], -3.0, randf_range(0.95, 1.05))
			play("split", -9.0)
		"pop": play("pop_0", -3.0, randf_range(0.95, 1.1))
		"block": play("block_break", -3.0)
		"item": play("item_drop", -8.0)
		"take":
			play("item_take", -3.0)
			match d["kind"]:
				"shield": play("shield_on", -4.0)
				"clock": play("freeze", -3.0)
				"charge": play("charge", -1.0)
		"shield_lost": play("shield_lost", -2.0)
		"die":
			play("die", -1.0)
			_music.stop()
		"cleared":
			play("stage_clear", -1.0)
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
