class_name NovaAudio
extends Node
## Nova Wardens music and sound: a dark night-sky pad under the march beat (four deep pulses, one per whole step of
## the fleet, so the beat quickens as the fleet thins), the cannon's shot, bursts per alien kind, bombs, the shields,
## the mothership's warble while it flies, the cannon lost, waves cleared, the invasion landing. A sound that is not
## there yet is skipped.

const SFX := "res://games/novawardens/audio/sfx/"
const MUSIC := "res://games/novawardens/audio/music/novawardens_ambient.ogg"
const NAMES := ["shot", "hit_squid", "hit_crab", "hit_octopus", "bomb_drop", "bomb_ground", "shield_hit", "player_die",
	"ufo_hit", "extra_life", "wave_clear", "game_over", "land", "step_0", "step_1", "step_2", "step_3"]

@export var game: NovaGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _ufo: AudioStreamPlayer


func _ready() -> void:
	for n in NAMES:
		if ResourceLoader.exists(SFX + n + ".wav"):
			_streams[n] = load(SFX + n + ".wav")
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.volume_db = -12.0
	add_child(_music)
	if ResourceLoader.exists(MUSIC):
		var m: AudioStream = load(MUSIC)
		if m is AudioStreamOggVorbis:
			(m as AudioStreamOggVorbis).loop = true
		_music.stream = m
	_ufo = AudioStreamPlayer.new()
	_ufo.bus = "SFX"
	_ufo.volume_db = -10.0
	if ResourceLoader.exists(SFX + "ufo_loop.wav"):
		var w: AudioStreamWAV = load(SFX + "ufo_loop.wav")
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = int(w.get_length() * w.mix_rate)
		_ufo.stream = w
	add_child(_ufo)
	game.game_started.connect(func(e):
		e.event.connect(_on_event)
		if _music.stream and not _music.playing:
			_music.play())


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	if not _streams.has(name):
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"step": play("step_%d" % d["n"], -4.0)
		"shot": play("shot", -8.0, randf_range(0.97, 1.03))
		"hit": play("hit_" + d["kind"], -4.0, randf_range(0.95, 1.05))
		"bomb": play("bomb_drop", -16.0, randf_range(0.9, 1.1))
		"bomb_ground": play("bomb_ground", -14.0)
		"shield": play("shield_hit", -12.0, randf_range(0.9, 1.1))
		"ufo":
			if _ufo.stream:
				_ufo.play()
		"ufo_gone": _ufo.stop()
		"ufo_hit":
			_ufo.stop()
			play("ufo_hit", -2.0)
		"die": play("player_die", -2.0)
		"cleared": play("wave_clear", -3.0)
		"land": play("land", -1.0)
		"game_over":
			_ufo.stop()
			play("game_over", -2.0)
		"extra_life": play("extra_life", -3.0)
