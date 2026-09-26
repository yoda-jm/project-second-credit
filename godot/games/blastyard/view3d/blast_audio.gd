class_name BlastAudio
extends Node
## Blastyard music and sound, driven by the engine's events: the party theme, then the urgent loop once sudden
## death starts.

const SFX := "res://games/blastyard/audio/sfx/"
const NAMES := ["place", "explode", "explode_big", "crate", "pickup", "skull", "kick", "bump", "die", "enemy_die",
	"win", "draw", "countdown", "go", "hurry", "block_drop", "exit_open", "stage_clear"]

@export var game: BlastGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _last := {}
var _time := 0.0
var _count := -1


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 16:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/blastyard/audio/music/blastyard_theme.ogg")
	_hurry = load("res://games/blastyard/audio/music/blastyard_hurry.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_hurry as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.stream = _theme
	_music.volume_db = -10.0
	add_child(_music)
	_music.play()
	game.round_started.connect(func(e):
		e.event.connect(_on_event)
		_count = -1
		if _music.stream != _theme:
			_music.stream = _theme
			_music.play())


func _process(delta: float) -> void:
	_time += delta
	if game.engine and game.countdown > 0.0 and not game.in_setup:
		var n := ceili(game.countdown)
		if n != _count:
			_count = n
			play("countdown", -4.0)
	elif _count > 0 and not game.in_setup:
		_count = 0
		play("go", -3.0)


func play(name: String, db := 0.0, gap := 0.0) -> void:
	if gap > 0.0 and _time - _last.get(name, -9.0) < gap:
		return
	_last[name] = _time
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = randf_range(0.94, 1.06)
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"bomb": play("place", -6.0)
		"explode": play("explode_big" if d["chain"] else "explode", -3.0, 0.05)
		"crate": play("crate", -6.0, 0.04)
		"pickup": play("skull" if d["kind"] == "skull" else "pickup", -4.0)
		"kick": play("kick", -4.0)
		"bump": play("bump", -8.0, 0.05)
		"death": play("die", -2.0)
		"enemy_die": play("enemy_die", -4.0)
		"hurry":
			play("hurry", -3.0)
			_music.stream = _hurry
			_music.play()
		"block_drop": play("block_drop", -9.0, 0.08)
		"exit_open": play("exit_open", -3.0)
		"stage_clear": play("stage_clear", -2.0)
		"round_over": play("win" if d["winner"] >= 0 else "draw", -2.0)
