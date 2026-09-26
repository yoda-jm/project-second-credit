class_name FizzAudio
extends Node
## Fizzlings music and sound: the theme (the hurry loop once the toys turn angry), puffs, pops that rise in pitch
## along a chain, gloopy traps, treats, springy bounces off bubbles, the ghost's whoosh.

const SFX := "res://games/fizzlings/audio/sfx/"
const NAMES := ["blow", "pop_0", "pop_1", "pop_2", "pop_3", "trap", "chain", "treat", "treat_big", "jump", "bounce_bubble",
	"angry", "hurry", "die", "extra_life", "ready", "stage_clear", "game_over", "ghost"]

@export var game: FizzGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/fizzlings/audio/music/fizzlings_theme.ogg")
	_hurry = load("res://games/fizzlings/audio/music/fizzlings_hurry.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_hurry as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	_music.stream = _theme
	add_child(_music)
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("ready", -3.0)
		if _music.stream != _theme or not _music.playing:
			_music.stream = _theme
			_music.play())


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"blow": play("blow", -8.0, randf_range(0.95, 1.08))
		"pop":
			play("pop_%d" % (int(d["n"]) % 4), -6.0, pow(2.0, mini(d["n"], 12) / 12.0))
			if d["trapped"] and d["n"] >= 2:
				play("chain", -4.0)
		"trap": play("trap", -5.0)
		"treat": play("treat_big" if d["points"] >= 1000 else "treat", -5.0)
		"jump": play("jump", -12.0)
		"bounce": play("bounce_bubble", -6.0)
		"hurry":
			play("hurry", -3.0)
			_music.stream = _hurry
			_music.play()
		"angry": play("angry", -6.0)
		"ghost": play("ghost", -3.0)
		"die": play("die", -3.0)
		"extra_life": play("extra_life", -3.0)
		"cleared":
			play("stage_clear", -2.0)
			_music.stream = _theme
		"game_over": play("game_over", -2.0)
		"escape": play("angry", -8.0)
