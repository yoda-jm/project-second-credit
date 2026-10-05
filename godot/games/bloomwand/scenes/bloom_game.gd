class_name BloomGame
extends Node
## Runs Bloomwand: the levels in turn (the score, lives and letters carried on), one fairy or two (F2 or a second pad
## brings in the second). 60 Hz ticks. Player one: the arrows to walk and climb (up where there is no ladder conjures
## a rainbow one), space or Z for the wand; the first pad: the stick or d-pad, A the wand. Player two: W A S D and F,
## or the second pad. In a one-player game W A S D work for player one too.
## "--demo" lets the autopilot play; "--level=N" starts at a level; "--players=2".

signal level_started(engine: BloomEngine)
signal game_over()

const B = preload("res://games/bloomwand/engine/bloom_engine.gd")
const FILE := "res://games/bloomwand/levels/garden.bloom"

var levels: Array[BloomLevel] = []
var engine: BloomEngine
var index := 0
var players := 1
var demo := false
var demo_locked := false
var over := false
var won := false
var high := 0
var _acc := 0.0
var _bots: Array[BloomBot] = []
var _games := 0


func start(at := 0) -> void:
	levels = BloomLevel.parse_file(FileAccess.get_file_as_string(FILE))
	_games += 1
	index = clampi(at, 0, levels.size() - 1)
	over = false
	won = false
	var ps := []
	for i in players:
		ps.append({"score": 0, "lives": 3, "letters": []})
	_load(ps)


func _load(ps: Array) -> void:
	engine = BloomEngine.new(levels[index], ps, _games * 17 + index)
	_bots.clear()
	for i in ps.size():
		_bots.append(BloomBot.new(i))
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == B.Phase.OVER and engine.phase_t <= 0.0:
		_end()
		return
	if engine.phase == B.Phase.CLEARED and engine.phase_t <= 0.0:
		var ps := []
		for f in engine.fairies:
			ps.append({"score": f["score"], "lives": maxi(f["lives"], 1) if not f["dead"] or f["lives"] > 0 else 0, "letters": f["letters"]})
		index += 1
		if index >= levels.size():
			won = true
			_end()
			return
		_load(ps)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= B.TICK:
		_acc -= B.TICK
		for i in engine.fairies.size():
			if demo:
				_bots[i].drive(engine)
			else:
				_steer(i)
		engine.tick()


func _end() -> void:
	over = true
	for f in engine.fairies:
		high = maxi(high, f["score"])
	game_over.emit()
	if demo:
		get_tree().create_timer(6.0).timeout.connect(func(): start(0))


func _steer(i: int) -> void:
	var f := engine.fairies[i]
	var l := false
	var r := false
	var u := false
	var d := false
	var wand := false
	var ladder := false
	var solo := engine.fairies.size() == 1
	if i == 0:
		l = Input.is_physical_key_pressed(KEY_LEFT) or (solo and Input.is_physical_key_pressed(KEY_A))
		r = Input.is_physical_key_pressed(KEY_RIGHT) or (solo and Input.is_physical_key_pressed(KEY_D))
		u = Input.is_physical_key_pressed(KEY_UP) or (solo and Input.is_physical_key_pressed(KEY_W))
		d = Input.is_physical_key_pressed(KEY_DOWN) or (solo and Input.is_physical_key_pressed(KEY_S))
		wand = Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_Z) or (solo and Input.is_physical_key_pressed(KEY_F))
		ladder = Input.is_physical_key_pressed(KEY_X) or Input.is_physical_key_pressed(KEY_C) or (solo and Input.is_physical_key_pressed(KEY_G))
	else:
		l = Input.is_physical_key_pressed(KEY_A)
		r = Input.is_physical_key_pressed(KEY_D)
		u = Input.is_physical_key_pressed(KEY_W)
		d = Input.is_physical_key_pressed(KEY_S)
		wand = Input.is_physical_key_pressed(KEY_F)
		ladder = Input.is_physical_key_pressed(KEY_G)
	var ax := Input.get_joy_axis(i, JOY_AXIS_LEFT_X)
	var ay := Input.get_joy_axis(i, JOY_AXIS_LEFT_Y)
	l = l or ax < -0.5 or Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_LEFT)
	r = r or ax > 0.5 or Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_RIGHT)
	u = u or ay < -0.5 or Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_UP)
	d = d or ay > 0.5 or Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_DOWN)
	wand = wand or Input.is_joy_button_pressed(i, JOY_BUTTON_A)
	ladder = ladder or Input.is_joy_button_pressed(i, JOY_BUTTON_B)
	f["move"] = (1 if r else 0) - (1 if l else 0)
	f["climb_in"] = (1 if u else 0) - (1 if d else 0)
	f["cast_pressed"] = wand and not f["cast_held"]
	f["cast_held"] = wand
	f["ladder_pressed"] = ladder and not f.get("ladder_was", false)
	f["ladder_was"] = ladder


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			players = 1
			start(0)
			get_viewport().set_input_as_handled()
		return
	if over and event.is_action_pressed("ui_accept"):
		start(0)
		return
	# a second fairy joins
	var join: bool = (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F2) \
		or (event is InputEventJoypadButton and event.pressed and event.device == 1 and event.button_index == JOY_BUTTON_START)
	if join and players == 1:
		players = 2
		var ps := [{"score": engine.fairies[0]["score"], "lives": engine.fairies[0]["lives"], "letters": engine.fairies[0]["letters"]},
			{"score": 0, "lives": 3, "letters": []}]
		_load(ps)
