class_name BastionAudio
extends Node
## Music and sound effects for Bastion Coast, driven by the engine's events.

const SFX := "res://games/bastion/audio/sfx/"

@export var game: BastionGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer


func _ready() -> void:
	for n in ["cannon_fire", "ship_fire", "whistle", "splash", "wall_destroyed", "wall_place", "cannon_place", "rotate",
			"ship_sunk", "horn", "game_over"]:
		_streams[n] = load(SFX + n + ".wav")
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	var theme: AudioStreamOggVorbis = load("res://games/bastion/audio/music/coast_theme.ogg")
	theme.loop = true
	_music.stream = theme
	_music.bus = "Music"
	_music.volume_db = -40.0
	add_child(_music)
	_music.play()
	create_tween().tween_property(_music, "volume_db", -9.0, 3.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	game.started.connect(func(e): e.event.connect(_on_event))
	if game.engine:
		game.engine.event.connect(_on_event)


func play(name: String, db: float = 0.0, pitch: float = 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch * randf_range(0.95, 1.05)
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot":
			if d["ours"]:
				play("cannon_fire", -2.0)
			else:
				play("ship_fire", -6.0)
				play("whistle", -12.0)
		"impact":
			var at: Vector2 = d["at"]
			if game.engine.map.at(roundi(at.x), roundi(at.y)) == CoastMap.Terrain.WATER:
				play("splash", -6.0)
		"wall_destroyed":
			play("wall_destroyed", -3.0)
		"wall_placed":
			play("wall_place", -2.0)
		"cannon_placed":
			play("cannon_place", -3.0)
		"rotated":
			play("rotate", -8.0)
		"ship_sunk":
			play("ship_sunk", -2.0)
		"phase":
			play("horn", -6.0, 1.0 if d["phase"] != BastionEngine.Phase.BATTLE else 1.12)
		"cannon_hit":
			play("wall_destroyed", -7.0, 0.8)
		"cannon_destroyed":
			play("ship_sunk", -2.0, 1.2)
		"player_out":
			play("game_over", -4.0)
		"game_over":
			if game.engine.versus:  # a winner: the horn, and the music stays up
				play("horn", -2.0, 0.9)
				return
			play("game_over", -2.0)
			create_tween().tween_property(_music, "volume_db", -30.0, 2.0)
