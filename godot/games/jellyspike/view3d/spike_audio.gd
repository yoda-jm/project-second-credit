class_name SpikeAudio
extends Node
## Jelly Spike music and sound: the beach tune (a tenser one on match point), soft and hard touches (a spike slaps),
## jelly jumps and squelching landings, the ball thumping into sand, the net and the walls, the whistle and a seagull
## flourish on each point, the match win. A sound that is not there yet is skipped.

const SFX := "res://games/jellyspike/audio/sfx/"
const MUSIC := "res://games/jellyspike/audio/music/"
const NAMES := ["touch_soft", "touch_hard", "jelly_jump", "jelly_land", "ball_sand", "ball_net", "ball_wall", "whistle_point",
	"cheer_point", "serve", "match_win", "match_point", "menu_tick"]

@export var game: SpikeGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _tense: AudioStream
var _net_t := 0.0


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
	_theme = _loop(MUSIC + "jellyspike_theme.ogg")
	_tense = _loop(MUSIC + "jellyspike_tense.ogg")
	game.match_started.connect(func(e):
		e.event.connect(_on_event)
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
	_net_t = maxf(0.0, _net_t - delta)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"touch":
			var sp: float = d["speed"]
			if sp > 13.0:
				play("touch_hard", -2.0, randf_range(0.95, 1.05))
			else:
				play("touch_soft", -5.0, randf_range(0.9, 1.1) + (d["n"] - 1) * 0.06)
		"power":
			play("touch_hard", 0.0, 0.7)
			play("ball_wall", -2.0, 0.6)
		"armed": play("menu_tick", -4.0, 1.6)
		"power_ready": play("menu_tick", -8.0, 1.2)
		"jump": play("jelly_jump", -10.0, randf_range(0.9, 1.1))
		"land": play("jelly_land", -12.0, randf_range(0.9, 1.1))
		"floor": play("ball_sand", -2.0)
		"net":
			if _net_t <= 0.0:
				_net_t = 0.15
				play("ball_net", -4.0)
		"wall": play("ball_wall", -8.0)
		"serve": play("serve", -8.0)
		"point":
			play("whistle_point", -4.0)
			play("cheer_point", -6.0)
			var mp: bool = maxi(e.score[0], e.score[1]) >= SpikeEngine.TARGET - 1 and absi(e.score[0] - e.score[1]) >= 1
			if mp:
				play("match_point", -3.0)
				if _tense and _music.stream != _tense:
					_music.stream = _tense
					_music.play()
		"match":
			play("match_win", -1.0)
			if _theme:
				_music.stream = _theme
				_music.play()
