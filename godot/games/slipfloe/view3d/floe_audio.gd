class_name FloeAudio
extends Node
## Slipfloe music and sound: the theme (a hurry loop when one mite is left), shoves, blocks sliding and clunking,
## ice shattering, squashes that climb the scale when several mites go at once, wall shakes, the gem fanfare.

const SFX := "res://games/slipfloe/audio/sfx/"
const NAMES := ["push", "block_stop", "shatter", "crush", "crush_2", "crush_3", "egg_break", "hatch", "wall_shake", "stun",
	"stomp", "gem_line", "chew", "die", "ready", "stage_clear", "game_over", "extra_life", "time_bonus"]

@export var game: FloeGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _hurry: AudioStream
var _slide: AudioStreamPlayer


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/slipfloe/audio/music/slipfloe_theme.ogg")
	_hurry = load("res://games/slipfloe/audio/music/slipfloe_hurry.ogg")
	(_theme as AudioStreamOggVorbis).loop = true
	(_hurry as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	_music.stream = _theme
	add_child(_music)
	var w: AudioStreamWAV = load(SFX + "slide.wav")
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_end = int(w.get_length() * w.mix_rate)
	_slide = AudioStreamPlayer.new()
	_slide.stream = w
	_slide.bus = "SFX"
	_slide.volume_db = -8.0
	add_child(_slide)
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
	var sliding := not e.slides.is_empty() and e.phase == FloeEngine.Phase.PLAY
	if sliding and not _slide.playing:
		_slide.play()
	elif not sliding and _slide.playing:
		_slide.stop()
	var hurry := e.phase == FloeEngine.Phase.PLAY and e.mites.size() + e.eggs.size() == 1
	if hurry and _music.stream != _hurry:
		_music.stream = _hurry
		_music.play()
	elif not hurry and _music.stream == _hurry and e.phase != FloeEngine.Phase.CLEARED:
		_music.stream = _theme
		_music.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"push": play("push", -6.0)
		"stop": play("block_stop", -5.0)
		"shatter":
			play("shatter", -4.0, randf_range(0.95, 1.08))
			if d.get("egg", false):
				play("egg_break", -4.0)
		"crush": play(["crush", "crush_2", "crush_3"][mini(d["n"], 3) - 1], -3.0)
		"hatch": play("hatch", -6.0)
		"shake": play("wall_shake", -3.0)
		"stun": play("stun", -5.0)
		"stomp": play("stomp", -4.0)
		"gems": play("gem_line", -2.0)
		"chew": play("chew", -12.0)
		"die": play("die", -2.0)
		"cleared":
			play("stage_clear", -2.0)
			if d["bonus"] > 0:
				for i in 6:
					get_tree().create_timer(1.2 + i * 0.1).timeout.connect(func(): play("time_bonus", -8.0, 1.0 + i * 0.05))
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
