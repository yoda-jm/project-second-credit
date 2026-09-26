class_name MossAudio
extends Node
## Mossfolk music and sound: a theme per level (three in turn), the hatch creaking open and the folk chirping as they
## go, the tools at work, bricks rising in pitch, pops and splats, a chirp for each one home, the last ten seconds.

const SFX := "res://games/mossfolk/audio/sfx/"
const NAMES := ["hatch_open", "lets_go", "assign", "select", "bash", "mine", "build", "builder_warn", "shrug", "panic", "pop",
	"splat", "drown", "yippee", "snap", "crush", "nuke", "level_done", "level_fail", "tick", "dig"]
const THEMES := ["mossfolk_theme_a", "mossfolk_theme_b", "mossfolk_theme_c"]

@export var game: MossGame

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _music: AudioStreamPlayer
var _skill := ""
var _last_sec := -1


func _ready() -> void:
	for n in NAMES:
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
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		var m: AudioStreamOggVorbis = load("res://games/mossfolk/audio/music/%s.ogg" % THEMES[game.index % THEMES.size()])
		m.loop = true
		if _music.stream != m:
			_music.stream = m
			_music.play())
	game.level_done.connect(func(_e, passed): play("level_done" if passed else "level_fail", -2.0))


func play(name: String, db := 0.0, pitch := 1.0) -> void:
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = _streams[name]
	p.volume_db = db
	p.pitch_scale = pitch
	p.play()


func _process(_delta: float) -> void:
	if game.skill != _skill:
		if _skill != "":
			play("select", -6.0)
		_skill = game.skill
	var e := game.engine
	if e and not e.over and e.time_left < 10.5 and e.time_left > 0.0:
		var s := int(e.time_left)
		if s != _last_sec:
			_last_sec = s
			play("tick", -6.0)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"hatch":
			play("hatch_open", -4.0)
			get_tree().create_timer(1.0).timeout.connect(func(): play("lets_go", -4.0))
		"assign": play("assign", -6.0)
		"stroke":
			match d["kind"]:
				"dig": play("dig", -14.0, randf_range(0.95, 1.05))
				"bash": play("bash", -10.0, randf_range(0.95, 1.05))
				"mine": play("mine", -10.0, randf_range(0.95, 1.05))
		"brick": play("build", -10.0, pow(2.0, (12 - d["left"]) / 12.0))
		"warn": play("builder_warn", -6.0)
		"shrug": play("shrug", -6.0)
		"panic": play("panic", -6.0)
		"pop": play("pop", -4.0)
		"death":
			match d["how"]:
				"splat": play("splat", -4.0)
				"drown": play("drown", -5.0)
				"trap": play("snap", -4.0)
		"saved": play("yippee", -7.0, randf_range(0.95, 1.1))
		"nuke": play("nuke", -3.0)
