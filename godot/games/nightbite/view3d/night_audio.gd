class_name NightAudio
extends Node
## Nightbite music and sound: the theme, the fever loop while the spirits are frightened, the rushing eyes,
## a rising pop for each spirit in a chain.

const SFX := "res://games/nightbite/audio/sfx/"
const NAMES := ["munch_0", "munch_1", "power", "eat_spook", "fruit", "fruit_eat", "die", "extra_life", "ready", "stage_clear"]

@export var game: NightGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _munch := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _fever: AudioStream
var _eyes: AudioStreamPlayer


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/nightbite/audio/music/nightbite_theme.ogg")
	_fever = load("res://games/nightbite/audio/music/nightbite_fever.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_fever as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	_music.stream = _theme
	add_child(_music)
	_eyes = AudioStreamPlayer.new()
	var ew: AudioStreamWAV = load(SFX + "eyes_home.wav")
	ew.loop_mode = AudioStreamWAV.LOOP_FORWARD
	ew.loop_end = int(ew.get_length() * ew.mix_rate)
	_eyes.stream = ew
	_eyes.bus = "SFX"
	_eyes.volume_db = -14.0
	add_child(_eyes)
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		play("ready", -3.0)
		_music.stream = _theme
		_music.play())


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _process(_delta: float) -> void:
	var e := game.engine
	if e == null:
		return
	var fever := e.fright > 0.0
	if fever and _music.stream != _fever:
		_music.stream = _fever
		_music.play()
	elif not fever and _music.stream == _fever:
		_music.stream = _theme
		_music.play()
	var eyes := e.spirits.any(func(s): return s["state"] in ["eyes", "entering"])
	if eyes and not _eyes.playing:
		_eyes.play()
	elif not eyes and _eyes.playing:
		_eyes.stop()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"pellet":
			_munch = 1 - _munch
			play("munch_%d" % _munch, -10.0)
		"power": play("power", -4.0)
		"eat_spirit": play("eat_spook", -3.0, pow(2.0, (d["chain"] - 1) / 6.0))
		"bonus_show": play("fruit", -6.0)
		"bonus_eat": play("fruit_eat", -4.0)
		"died": play("die", -2.0)
		"extra_life": play("extra_life", -3.0)
		"cleared": play("stage_clear", -2.0)
