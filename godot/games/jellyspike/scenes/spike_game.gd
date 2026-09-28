class_name SpikeGame
extends Node
## Runs Jelly Spike: a match to 15 (won by two), 60 Hz ticks. One player plays the left blob against the CPU: arrows
## or A / D walk, up, W or space jumps (hold for a full jump), down, S or shift fires the power spike when its meter
## is full, or the first gamepad (A jumps, X powers). F2 (or the second pad's A) brings in a
## second player on the right: then the left blob is A / D / W and the right one the arrows. The demo lets two CPU blobs
## play. "--versus" (user argument) starts with two players.

signal match_started(engine: SpikeEngine)
signal match_over(winner: int)

const S = preload("res://games/jellyspike/engine/spike_engine.gd")

var engine: SpikeEngine
var demo := false
var demo_locked := false
var versus := false
var over := false
var matches := 0
var wins := [0, 0]
var cpu_skill := 0.7
var _acc := 0.0
var _bots: Array[SpikeBot] = []


func start() -> void:
	over = false
	engine = SpikeEngine.new(matches % 2, 11 + matches)
	engine.event.connect(_on_event)
	_bots = [SpikeBot.new(0, 0.85, 3 + matches), SpikeBot.new(1, 0.6 if demo else cpu_skill, 5 + matches)]
	match_started.emit(engine)


func _on_event(kind: String, d: Dictionary) -> void:
	if kind == "match":
		over = true
		wins[d["winner"]] += 1
		matches += 1
		match_over.emit(d["winner"])
		if demo:
			get_tree().create_timer(6.0).timeout.connect(start)


func _process(delta: float) -> void:
	if engine == null:
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= S.TICK:
		_acc -= S.TICK
		if demo:
			_bots[0].drive(engine)
			_bots[1].drive(engine)
		else:
			_steer()
		engine.tick()


func _steer() -> void:
	var key := func(keys: Array) -> bool:
		for k in keys:
			if Input.is_physical_key_pressed(k):
				return true
		return false
	var pad_x := func(dev: int) -> float:
		var ax := Input.get_joy_axis(dev, JOY_AXIS_LEFT_X)
		if Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_LEFT): ax = -1.0
		if Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_RIGHT): ax = 1.0
		return 0.0 if absf(ax) < 0.4 else signf(ax)
	if versus:
		var lx: float = (1.0 if key.call([KEY_D]) else 0.0) - (1.0 if key.call([KEY_A]) else 0.0)
		var rx: float = (1.0 if key.call([KEY_RIGHT]) else 0.0) - (1.0 if key.call([KEY_LEFT]) else 0.0)
		engine.move[0] = lx if lx != 0.0 else pad_x.call(0)
		engine.move[1] = rx if rx != 0.0 else pad_x.call(1)
		engine.jump[0] = key.call([KEY_W, KEY_SPACE]) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)
		engine.jump[1] = key.call([KEY_UP, KEY_ENTER, KEY_KP_0]) or Input.is_joy_button_pressed(1, JOY_BUTTON_A)
		engine.power_pressed[0] = key.call([KEY_S]) or Input.is_joy_button_pressed(0, JOY_BUTTON_X)
		engine.power_pressed[1] = key.call([KEY_DOWN, KEY_KP_1]) or Input.is_joy_button_pressed(1, JOY_BUTTON_X)
	else:
		var x: float = (1.0 if key.call([KEY_D, KEY_RIGHT]) else 0.0) - (1.0 if key.call([KEY_A, KEY_LEFT]) else 0.0)
		engine.move[0] = x if x != 0.0 else pad_x.call(0)
		engine.jump[0] = key.call([KEY_W, KEY_UP, KEY_SPACE]) or Input.is_joy_button_pressed(0, JOY_BUTTON_A)
		engine.power_pressed[0] = key.call([KEY_S, KEY_DOWN, KEY_SHIFT]) or Input.is_joy_button_pressed(0, JOY_BUTTON_X)
		_bots[1].drive(engine)


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start()
			get_viewport().set_input_as_handled()
		return
	var second: bool = (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F2) \
		or (event is InputEventJoypadButton and event.pressed and event.device == 1 and event.button_index == JOY_BUTTON_START)
	if second:
		versus = not versus
		wins = [0, 0]
		start()
		return
	if over and event.is_action_pressed("ui_accept"):
		start()
