class_name BootsAudio
extends Node
## Music and sound for Muddy Boots, driven by the engine's events. Our shots are rate-limited (a squad of four
## firing together would otherwise be a wall of noise); the enemy's are quieter the further they are.

const SFX := "res://games/boots/audio/sfx/"
const NAMES := ["shot", "enemy_shot", "impact", "throw", "explosion", "rocket", "splash", "ugh", "collapse", "pickup",
	"cheer", "mission_won", "mission_lost"]

@export var game: BootsGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _shot_t := 0.0


func _ready() -> void:
	for n in NAMES:
		_streams[n] = load(SFX + n + ".wav")
	for i in 16:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/boots/audio/music/boots_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	game.mission_started.connect(func(e):
		e.event.connect(_on_event)
		create_tween().tween_property(_music, "volume_db", -11.0, 2.0))


func _process(delta: float) -> void:
	_shot_t -= delta


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.93, 1.07)
	p.play()


func _dist_db(pos: Vector2) -> float:
	var l := game.engine.leader()
	if l.is_empty():
		return -6.0
	return -clampf((pos.distance_to(l["pos"]) - 3.0) * 1.2, 0.0, 18.0)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot":
			if _shot_t <= 0.0:
				play("shot", -6.0)
				_shot_t = 0.07
		"enemy_shot": play("enemy_shot", -6.0 + _dist_db(d["from"]))
		"impact": play("impact", -18.0)
		"grenade": play("throw", -6.0)
		"rocket": play("rocket", -3.0)
		"explosion":
			play("splash" if d["splash"] else "explosion", -1.0 + _dist_db(d["pos"]) * 0.5)
		"hut_destroyed": play("collapse", -2.0)
		"death": play("ugh", -4.0, 1.0 if d.get("who", "") == "soldier" else 1.2)
		"enemy_death": play("ugh", -8.0 + _dist_db(d["pos"]), 0.85)
		"pickup": play("pickup", -4.0)
		"rescued": play("cheer", -4.0)
		"won":
			play("mission_won", 0.0)
			create_tween().tween_property(_music, "volume_db", -24.0, 0.5)
		"lost":
			play("mission_lost", 0.0)
			create_tween().tween_property(_music, "volume_db", -30.0, 0.5)
