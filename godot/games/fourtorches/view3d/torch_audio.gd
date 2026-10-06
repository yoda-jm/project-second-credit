class_name TorchAudio
extends Node
## Four Torches music and sound: the dungeon's march, its tenser variant when someone is weak; swings, throws,
## fireballs and arrows by class, hits and deaths, generators cracking and breaking, the heroes' hurts and falls,
## doors, keys, treasure, food, the potion's blast, the stairs down, ghosts moaning, the imps' fire. A missing sound
## is skipped.

const T = preload("res://games/fourtorches/engine/torch_engine.gd")
const SFX := "res://games/fourtorches/audio/sfx/"
const MUSIC := "res://games/fourtorches/audio/music/"
const NAMES := ["swing", "throw", "fireball_cast", "arrow_shot", "hit_monster", "monster_die", "gen_hit", "gen_break", "hero_hurt", "hero_die",
	"door_open", "key", "treasure", "food", "potion", "amulet", "exit", "health_low", "ghost_moan", "imp_fire", "level_start", "level_clear",
	"game_over", "join"]
const SHOT := {"knight": "throw", "shieldmaiden": "throw", "mage": "fireball_cast", "ranger": "arrow_shot"}

@export var game: TorchGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _theme: AudioStream
var _danger: AudioStream
var _hit_t := 0.0
var _moan_t := 3.0


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 16:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -9.0
	add_child(_music)
	_theme = _loop(MUSIC + "fourtorches_theme.ogg")
	_danger = _loop(MUSIC + "fourtorches_danger.ogg")
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("level_start", -3.0)
		_to(_theme))


func _loop(path: String) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var m: AudioStream = load(path)
	if m is AudioStreamOggVorbis:
		(m as AudioStreamOggVorbis).loop = true
	return m


func _to(s: AudioStream) -> void:
	if s and _music.stream != s:
		_music.stream = s
		_music.play()


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
	_hit_t = maxf(0.0, _hit_t - delta)
	var e := game.engine
	if e == null or e.phase != T.Phase.PLAY:
		return
	var weak := false
	for h in e.heroes:
		if not h["dead"] and h["health"] < 250.0:
			weak = true
	_to(_danger if weak else _theme)
	# ghosts moan now and then when some are about
	_moan_t -= delta
	if _moan_t <= 0.0:
		_moan_t = randf_range(3.0, 7.0)
		for m in e.monsters:
			if m["kind"] == "ghost" and (m["pos"] as Vector2).distance_to(e.centre()) < 10.0:
				play("ghost_moan", -14.0, randf_range(0.85, 1.15))
				break


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"shoot": play(SHOT.get(e.heroes[d["h"]]["cls"], "throw"), -8.0, randf_range(0.95, 1.05))
		"melee": play("swing", -8.0, randf_range(0.9, 1.1))
		"hit":
			if _hit_t <= 0.0 and d["kind"] != "wall":
				_hit_t = 0.05
				play("hit_monster", -9.0, randf_range(0.9, 1.1))
		"kill": play("monster_die", -8.0, randf_range(0.9, 1.15))
		"gen_hit": play("gen_hit", -5.0)
		"gen_break": play("gen_break", -2.0)
		"hurt":
			if _hit_t <= 0.0:
				_hit_t = 0.08
				play("hero_hurt", -7.0, randf_range(0.95, 1.05))
		"die": play("hero_die", -2.0)
		"door": play("door_open", -3.0)
		"key": play("key", -4.0)
		"treasure": play("treasure", -4.0)
		"food": play("food", -4.0)
		"blast": play("potion", 0.0)
		"exit": play("exit", -2.0)
		"rejoin": play("join", -8.0)
		"food_shot": play("hit_monster", -4.0, 0.6)
		"potion_shot": play("potion", -3.0, 1.2)
		"crumble": play("gen_break", -6.0, 1.3)
		"low": play("health_low", -5.0)
		"monster_shot": if d["kind"] == "imp": play("imp_fire", -11.0)
		"game_over": play("game_over", -2.0)
