class_name BioAudio
extends Node
## Biosurge music and sound: the level's track, the boss's, the trader's groove in the shop; shots (bigger with the gun),
## the laser's hum, homing missiles, enemy fire, wet hits and bursts, the boss's roar and death, the ship's hurts and
## loss, credits pinging higher as they come, power-ups, the warning, the level's jingles. A missing sound is skipped.

const B = preload("res://games/biosurge/engine/bio_engine.gd")
const SFX := "res://games/biosurge/audio/sfx/"
const MUSIC := "res://games/biosurge/audio/music/"
const NAMES := ["shoot", "shoot_big", "homing", "enemy_shoot", "hit", "boom_small", "boom_big", "boss_hit", "boss_die", "player_hit",
	"shield", "die", "credit", "power", "buy", "shop_open", "warning", "level_start", "level_clear", "game_over"]

@export var game: BioGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _laser: AudioStreamPlayer
var _theme: AudioStream
var _boss: AudioStream
var _shop: AudioStream
var _credit_k := 0
var _credit_t := 0.0
var _hit_t := 0.0


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
	_laser = AudioStreamPlayer.new()
	_laser.bus = "SFX"
	_laser.volume_db = -12.0
	if ResourceLoader.exists(SFX + "laser_loop.wav"):
		var wv: AudioStream = load(SFX + "laser_loop.wav")
		if wv is AudioStreamWAV:
			(wv as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
			(wv as AudioStreamWAV).loop_end = int(wv.get_length() * (wv as AudioStreamWAV).mix_rate)
		_laser.stream = wv
	add_child(_laser)
	_theme = _loop(MUSIC + "biosurge_theme.ogg")
	_boss = _loop(MUSIC + "biosurge_boss.ogg")
	_shop = _loop(MUSIC + "biosurge_shop.ogg")
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		play("level_start", -3.0)
		_music_to(_theme))
	game.shop_opened.connect(func():
		if _music.stream != _shop:
			play("shop_open", -4.0)
			_music_to(_shop)
		else:
			play("buy", -3.0))


func _music_to(s: AudioStream) -> void:
	if s and _music.stream != s:
		_music.stream = s
		_music.play()


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
	_credit_t = maxf(0.0, _credit_t - delta)
	if _credit_t <= 0.0:
		_credit_k = 0
	_hit_t = maxf(0.0, _hit_t - delta)
	var e := game.engine
	if e == null or _laser.stream == null:
		return
	var on: bool = e.firing and e.loadout["laser"] and e.phase in [B.Phase.PLAY, B.Phase.BOSS] and game.mode == BioGame.Mode.FLY
	if on and not _laser.playing:
		_laser.play()
	elif not on and _laser.playing:
		_laser.stop()


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shoot": if not game.engine.loadout["laser"]: play("shoot_big" if d["gun"] >= 3 else "shoot", -14.0, randf_range(0.95, 1.05))
		"homing": play("homing", -12.0)
		"enemy_shoot": play("enemy_shoot", -13.0, randf_range(0.9, 1.1))
		"hit":
			if _hit_t <= 0.0:
				_hit_t = 0.05
				play("hit", -12.0, randf_range(0.9, 1.15))
		"kill": play("boom_big" if d["kind"] in ["pod", "turret", "crab"] else "boom_small", -5.0, randf_range(0.9, 1.1))
		"credit":
			_credit_k = mini(_credit_k + 1, 12)
			_credit_t = 1.2
			play("credit", -8.0, pow(2.0, _credit_k / 12.0))
		"pickup": play("power", -3.0)
		"shield": play("shield", -4.0)
		"player_hit": play("player_hit", -4.0)
		"die": play("die", -1.0)
		"warning":
			play("warning", -2.0)
			_music_to(_boss)
		"boss_hit": if _hit_t <= 0.0: play("boss_hit", -10.0, randf_range(0.9, 1.1))
		"boss_die":
			play("boss_die", 0.0)
			_music.stop()
		"cleared": play("level_clear", -2.0)
		"game_over": play("game_over", -2.0)
