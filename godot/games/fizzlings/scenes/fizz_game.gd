class_name FizzGame
extends Node
## Runs Fizzlings: level after level, one or two heroes, 60 Hz ticks. Hero 1: arrows to walk, Up or Z to jump,
## Space or X to blow. Hero 2: A and D to walk, W to jump, F to blow; pressing one of those joins in (from the next
## level if a level is running). The demo lets two autopilots play. "--level=N" (user argument) starts at a level.

signal level_started(engine: FizzEngine)
signal game_over()

const E = preload("res://games/fizzlings/engine/fizz_engine.gd")
const FILE := "res://games/fizzlings/levels/toybox.fizz"

var engine: FizzEngine
var levels: Array[FizzLevel] = []
var index := 0
var players := 1
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bots: Array[FizzBot] = []
var _seed := 1
var _join := false


func start(at := 0, seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	levels = FizzLevel.parse_file(FileAccess.get_file_as_string(FILE))
	index = clampi(at, 0, levels.size() - 1)
	over = false
	players = 2 if demo else players
	_load([])


func _load(carry: Array) -> void:
	engine = FizzEngine.new(levels[index % levels.size()], index, _seed + index * 7, players, carry)
	_bots = [FizzBot.new(0, _seed + index), FizzBot.new(1, _seed + index)]
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == E.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		for h in engine.heroes:
			high = maxi(high, h["score"])
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(0, _seed + 1))
		return
	if engine.phase == E.Phase.CLEARED and engine.phase_t <= 0.0:
		var carry := engine.heroes.map(func(h): return {"lives": h["lives"], "score": h["score"], "next_life": h["next_life"]})
		if _join and players == 1:
			players = 2
			_join = false
		index += 1
		_load(carry)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		if demo:
			for b in _bots:
				if b.p < engine.heroes.size():
					b.drive(engine)
		else:
			_steer()
		engine.tick()


func _steer() -> void:
	var keys := [[KEY_LEFT, KEY_RIGHT, [KEY_UP, KEY_Z], [KEY_SPACE, KEY_X]], [KEY_A, KEY_D, [KEY_W], [KEY_F]]]
	for i in engine.heroes.size():
		var h: Dictionary = engine.heroes[i]
		var k: Array = keys[i]
		var x := 0.0
		if Input.is_physical_key_pressed(k[0]): x -= 1.0
		if Input.is_physical_key_pressed(k[1]): x += 1.0
		var pad := Input.get_joy_axis(i, JOY_AXIS_LEFT_X)
		if absf(pad) > 0.3: x = signf(pad)
		h["want_x"] = x
		h["jump"] = k[2].any(func(c): return Input.is_physical_key_pressed(c)) or Input.is_joy_button_pressed(i, JOY_BUTTON_A)
		if k[3].any(func(c): return Input.is_physical_key_pressed(c)) or Input.is_joy_button_pressed(i, JOY_BUTTON_X):
			h["blow"] = true


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
	if over:
		if event.is_action_pressed("ui_accept"):
			start(0)
		return
	if event is InputEventKey and event.pressed and event.physical_keycode in [KEY_W, KEY_F] and players == 1:
		_join = true
