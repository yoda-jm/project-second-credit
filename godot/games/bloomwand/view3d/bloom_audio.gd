class_name BloomAudio
extends Node
## Bloomwand music and sound: the fairy-tale tune (its hurried variant once the clock runs out), steps and rungs,
## the wand's zap, the catch, the swing and the thud of each slam, the burst, flowers, fruit, letters, the rainbow
## ladder's shimmer, a lost life, the hurry bell, the level's jingles and the extra life's fanfare. A sound that is not
## there yet is skipped.

const B = preload("res://games/bloomwand/engine/bloom_engine.gd")
const SFX := "res://games/bloomwand/audio/sfx/"
const MUSIC := "res://games/bloomwand/audio/music/"
const NAMES := ["step", "climb", "cast", "catch", "slam", "slam_whoosh", "pop", "flower", "fruit", "letter", "ladder_magic", "die", "hurry",
	"level_start", "level_clear", "extra", "game_over", "door_open"]

@export var game: BloomGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _step_t := 0.0


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
	_theme = _loop(MUSIC + "bloomwand_theme.ogg")
	_hurry = _loop(MUSIC + "bloomwand_hurry.ogg")
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("level_start", -3.0)
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
	if e == null or e.phase != B.Phase.PLAY:
		return
	_step_t -= delta
	if _step_t <= 0.0:
		for f in e.fairies:
			if f["dead"]:
				continue
			if f["climbing"] and f["climb_in"] != 0:
				play("climb", -16.0, randf_range(0.9, 1.1))
				_step_t = 0.22
			elif f["anim"] == "walk":
				play("step", -18.0, randf_range(0.9, 1.1))
				_step_t = 0.26


func _on_event(kind: String, _d: Dictionary) -> void:
	match kind:
		"cast": play("cast", -5.0, randf_range(0.95, 1.05))
		"catch": play("catch", -3.0)
		"slam":
			play("slam_whoosh", -8.0)
			play("slam", -2.0, randf_range(0.9, 1.05))
		"hit": play("slam", -8.0, 1.3)
		"pop": play("pop", -2.0, randf_range(0.95, 1.1))
		"flower": play("flower", -6.0, randf_range(0.95, 1.1))
		"take": play("fruit", -4.0)
		"letter": play("letter", -3.0)
		"extra": play("extra", -2.0)
		"ladder": play("ladder_magic", -4.0)
		"die": play("die", -2.0)
		"hurry":
			play("hurry", -3.0)
			if _hurry:
				_music.stream = _hurry
				_music.play()
		"cleared":
			play("level_clear", -2.0)
			_music.stop()
		"game_over": play("game_over", -2.0)
