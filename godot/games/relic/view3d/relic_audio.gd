class_name RelicAudio
extends Node
## Relic Run music and sound: the adventure theme (the chase while the boulder rolls, the tomb theme for inner
## levels), footsteps, the pistol and its ricochets, the fuse and the blast, spikes, darts, crushers, pickups.

const SFX := "res://games/relic/audio/sfx/"
const NAMES := ["shot", "ricochet", "empty", "plant", "boom", "rubble", "jump", "land", "step_0", "step_1", "climb", "spikes",
	"dart", "dart_hit", "crusher", "enemy_hit", "bat", "pickup_treasure", "pickup_ammo", "die", "level_start", "level_clear",
	"game_over", "secret"]

@export var game: RelicGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _chase: AudioStream
var _tomb: AudioStream
var _fuse: AudioStreamPlayer
var _roll: AudioStreamPlayer
var _step := 0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_theme = load("res://games/relic/audio/music/relic_theme.ogg")
	_chase = load("res://games/relic/audio/music/relic_chase.ogg")
	_tomb = load("res://games/relic/audio/music/relic_tomb.ogg")
	for m in [_theme, _chase, _tomb]:
		(m as AudioStreamOggVorbis).loop = true
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -10.0
	add_child(_music)
	_fuse = _loop("fuse", -8.0)
	_roll = _loop("boulder_roll", -4.0)
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("level_start", -3.0)
		_music.stream = _tomb if e.level.theme == 1 else _theme
		_music.play())


func _loop(name: String, db: float) -> AudioStreamPlayer:
	var w: AudioStreamWAV = load(SFX + name + ".wav")
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_end = int(w.get_length() * w.mix_rate)
	var p := AudioStreamPlayer.new()
	p.stream = w
	p.bus = "SFX"
	p.volume_db = db
	add_child(p)
	return p


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
	var fuse := not e.bombs.is_empty()
	if fuse != _fuse.playing:
		if fuse: _fuse.play()
		else: _fuse.stop()
	var rolling: bool = not e.boulder.is_empty() and e.boulder["rolling"] and not e.boulder["done"] and e.phase == RelicEngine.Phase.PLAY
	if rolling != _roll.playing:
		if rolling: _roll.play()
		else: _roll.stop()
	var chase := rolling
	var want: AudioStream = _chase if chase else (_tomb if e.level.theme == 1 else _theme)
	if _music.stream != want:
		_music.stream = want
		_music.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot": play("shot", -5.0, randf_range(0.95, 1.05))
		"empty": play("empty", -6.0)
		"plant": play("plant", -6.0)
		"boom":
			play("boom", -2.0)
			play("rubble", -6.0)
		"break": pass
		"hit": play("enemy_hit", -5.0, 1.0 if d["dead"] else 1.2)
		"dart": play("dart", -6.0)
		"dart_hit": play("ricochet" if d.get("shot", false) else "dart_hit", -10.0 if d.get("shot", false) else -6.0)
		"spikes": play("spikes", -4.0)
		"crush": play("crusher", -3.0)
		"pickup": play("pickup_treasure" if d["kind"] == "$" else "pickup_ammo", -4.0)
		"die": play("die", -2.0)
		"exit": play("level_clear", -2.0)
		"game_over": play("game_over", -2.0)
		"jump": play("jump", -10.0)
		"land": play("land", -10.0)
		"step":
			_step = 1 - _step
			play("step_%d" % _step, -14.0, randf_range(0.95, 1.05))
