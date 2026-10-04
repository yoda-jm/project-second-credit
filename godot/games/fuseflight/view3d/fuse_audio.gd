class_name FuseAudio
extends Node
## Fuseflight music and sound: the festival tune (a racing loop while the power star lasts), leaps and landings,
## fireworks taken (brighter for a lit one), the fuse catching, enemies taking wing, enemies eaten (a chime climbing with
## the chain), letters, the sprite caught, the stage's finale. A soft wind while gliding. A sound not there is skipped.

const SFX := "res://games/fuseflight/audio/sfx/"
const MUSIC := "res://games/fuseflight/audio/music/"
const NAMES := ["jump", "land", "bump", "take", "take_lit", "lit", "spawn", "wing", "power", "power_end", "eat", "letter", "die",
	"stage_clear", "game_over", "extra_life"]

@export var game: FuseGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _power: AudioStream
var _glide: AudioStreamPlayer
var _chain := 0


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
	_theme = _loop_ogg(MUSIC + "fuseflight_theme.ogg")
	_power = _loop_ogg(MUSIC + "fuseflight_power.ogg")
	_glide = AudioStreamPlayer.new()
	_glide.bus = "SFX"
	_glide.volume_db = -60.0
	add_child(_glide)
	if ResourceLoader.exists(SFX + "glide_loop.wav"):
		var w: AudioStreamWAV = load(SFX + "glide_loop.wav")
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = int(w.get_length() * w.mix_rate)
		_glide.stream = w
		_glide.play()
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		if _theme and _music.stream != _theme:
			_music.stream = _theme
			_music.play())


func _loop_ogg(path: String) -> AudioStream:
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
	var gliding: bool = e.phase == FuseEngine.Phase.PLAY and e.hero["gliding"]
	_glide.volume_db = lerpf(_glide.volume_db, -10.0 if gliding else -60.0, 1.0 - exp(-delta * 8.0))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"jump": play("jump", -8.0, randf_range(0.95, 1.05))
		"land": play("land", -12.0)
		"bump": play("bump", -10.0)
		"take": play("take_lit" if d["lit"] else "take", -4.0, randf_range(0.97, 1.03))
		"lit": play("lit", -10.0)
		"spawn": play("spawn", -12.0)
		"wing": play("wing", -8.0)
		"power":
			_chain = 0
			play("power", -2.0)
			if _power:
				_music.stream = _power
				_music.play()
		"power_end":
			play("power_end", -6.0)
			if _theme:
				_music.stream = _theme
				_music.play()
		"eat":
			_chain += 1
			play("eat", -4.0, pow(2.0, mini(_chain - 1, 7) / 12.0 * 2.0))
		"letter": play("letter", -3.0)
		"die":
			play("die", -2.0)
		"cleared": play("stage_clear", -1.0)
		"game_over": play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
