class_name FlagsAudio
extends Node
## Music and sound for Iron Flags, driven by the engine's events. Battles far from the camera are quieter, and a
## sound that many guns make at once is played once per short window, so a big fight stays readable.

const SFX := "res://games/flags/audio/sfx/"
const NAMES := ["rifle", "smg", "sniper", "rocket", "flame", "laser", "tank_gun", "gatling", "howitzer", "missile",
	"explosion_small", "explosion_big", "hit_metal", "robot_die", "capture", "lost", "unit_ready", "select", "order",
	"attack_order", "victory", "defeat", "alarm"]
const WEAPON_SOUND := {"rifle": "rifle", "smg": "smg", "sniper": "sniper", "rocket": "rocket", "flame": "flame",
	"laser": "laser", "tank_gun": "tank_gun", "gatling": "gatling", "howitzer": "howitzer", "missile": "missile",
	"grenade": "rocket"}
const Team = FlagsMap.Team

@export var game: FlagsGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _last := {}  ## sound -> time it last played
var _time := 0.0
var _alarm_at := -99.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 20:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/flags/audio/music/flags_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	game.map_started.connect(func(e):
		e.event.connect(_on_event)
		create_tween().tween_property(_music, "volume_db", -11.0, 2.0))
	if game.engine:
		game.engine.event.connect(_on_event)


func _process(delta: float) -> void:
	_time += delta


func play(name: String, db := 0.0, pitch := 1.0, gap := 0.0) -> void:
	if gap > 0.0 and _time - _last.get(name, -9.0) < gap:
		return
	_last[name] = _time
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.93, 1.07)
	p.play()


## Quieter the further the map point is from the middle of the screen.
func _far(pos: Vector2) -> float:
	if game.view == null or not game.view.has_method("focus"):
		return 0.0
	var d: float = pos.distance_to(game.view.focus())
	return -clampf((d - 8.0) * 0.9, 0.0, 30.0)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot":
			var s: String = WEAPON_SOUND.get(d["weapon"], "rifle")
			var heavy := s in ["tank_gun", "howitzer", "missile", "rocket"]
			var db := _far(d["from"]) + (-6.0 if heavy else -12.0)
			if db > -34.0:
				play(s, db, 1.0, 0.05 if heavy else 0.09)
		"hit":
			if randf() < 0.3:
				play("hit_metal", _far(d["pos"]) - 16.0, 1.0, 0.1)
		"blast":
			play("explosion_small", _far(d["pos"]) - 8.0, 1.0, 0.06)
		"death":
			if d["cls"] == "robot":
				play("robot_die", _far(d["pos"]) - 8.0, 1.0, 0.08)
			else:
				play("explosion_big" if d["cls"] != "robot" else "explosion_small", _far(d["pos"]) - 3.0, 1.0, 0.1)
		"destroyed": play("explosion_big", 0.0)
		"capture":
			if game.demo or d["team"] == Team.RED:
				play("capture", -4.0)
			elif d["from"] == Team.RED:
				play("lost", -3.0)
		"produced":
			if d["team"] == Team.RED and not game.demo:
				play("unit_ready", -9.0, 1.0, 0.5)
		"select": play("select", -8.0)
		"order": play("attack_order" if d["attack"] else "order", -6.0, randf_range(0.95, 1.1))
		"fort_hit":
			if d["team"] == Team.RED and _time - _alarm_at > 12.0 and not game.demo:
				_alarm_at = _time
				play("alarm", -6.0)
		"won", "lost":
			create_tween().tween_property(_music, "volume_db", -24.0, 1.0)
			play("victory" if kind == "won" or game.demo else "defeat", -2.0)
