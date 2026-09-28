class_name TumbleAudio
extends Node
## Tumbletop music and sound: Pip's springy hops, the cube tops chiming up a scale as they change (the finished colour
## rings brighter), the undo buzz, balls thudding down the steps, the serpent's hatching and hiss, the disc's whoosh,
## the lured serpent's long fall, the freeze, the catch, and the round's fanfare. A sound that is not there yet is
## skipped.

const SFX := "res://games/tumbletop/audio/sfx/"
const MUSIC := "res://games/tumbletop/audio/music/tumbletop_theme.ogg"
const NAMES := ["hop", "land", "paint", "paint_done", "undo", "fall", "disc", "ride", "drop", "bounce", "hatch", "hiss",
	"lure", "freeze", "catch", "die", "round_start", "round_clear", "game_over", "extra_life"]

@export var game: TumbleGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _combo := 0
var _combo_t := 0.0
var _bounced := {}


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
	if ResourceLoader.exists(MUSIC):
		var m: AudioStream = load(MUSIC)
		if m is AudioStreamOggVorbis:
			(m as AudioStreamOggVorbis).loop = true
		_music.stream = m
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("round_start", -3.0)
		if _music.stream and not _music.playing:
			_music.play())


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
	_combo_t = maxf(0.0, _combo_t - delta)
	if _combo_t <= 0.0:
		_combo = 0
	var e := game.engine
	if e == null:
		return
	# each ball thuds as it lands on a step
	for en in e.enemies:
		var id: int = en.get("id", 0)
		var landed: bool = en["t"] >= 1.0 and not en.has("fall_t") and en.get("drop", 0.0) <= 0.0
		if landed and not _bounced.get(id, false) and en["kind"] in ["red", "green", "purple", "imp"]:
			play("bounce", -14.0, {"red": 1.0, "green": 1.2, "purple": 0.85, "imp": 1.4}[en["kind"]])
		_bounced[id] = landed
	if _music.stream:
		_music.volume_db = lerpf(_music.volume_db, -22.0 if e.frozen > 0.0 else -9.0, minf(1.0, delta * 3.0))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"hop":
			play("hop", -8.0, randf_range(0.96, 1.04))
		"paint":
			# consecutive colours climb a scale
			_combo = mini(_combo + 1, 8)
			_combo_t = 1.2
			var semis: int = [0, 2, 4, 5, 7, 9, 11, 12][_combo - 1]
			play("paint_done" if d["done"] else "paint", -6.0, pow(2.0, semis / 12.0))
		"undo": play("undo", -6.0)
		"fall": play("fall", -3.0)
		"disc":
			play("disc", -3.0)
			play("ride", -6.0)
		"spawn": play("drop", -12.0, randf_range(0.9, 1.1))
		"hatch":
			play("hatch", -4.0)
			play("hiss", -8.0)
		"lure": play("lure", -2.0)
		"freeze": play("freeze", -3.0)
		"catch": play("catch", -3.0)
		"die": play("die", -2.0)
		"cleared": play("round_clear", -1.0)
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
