class_name WhiskerGame
extends Node
## Runs a Whisker Alley game in real time: fixed 60 Hz ticks, player input, the demo autopilot, restarts.

signal started(engine: WhiskerEngine)

const P = WhiskerEngine.Phase

var engine: WhiskerEngine
var demo := false
var demo_locked := false
var game_over_time := 0.0
var _acc := 0.0
var _bot := WhiskerBot.new()
var _seed := 1


func start(seed: int = -1) -> void:
	_seed = seed if seed >= 0 else randi()
	engine = WhiskerEngine.new(_seed)
	_bot = WhiskerBot.new()
	game_over_time = 0.0
	started.emit(engine)


func _process(delta: float) -> void:
	if engine == null:
		return
	if engine.phase == P.GAME_OVER:
		game_over_time += delta
		if demo and game_over_time > 6.0:
			start(_seed + 1)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= WhiskerEngine.TICK:
		_acc -= WhiskerEngine.TICK
		if demo:
			_bot.drive(engine)
		else:
			engine.input_x = int(Input.get_axis("ui_left", "ui_right"))
			engine.input_y = int(Input.get_axis("ui_down", "ui_up"))
		engine.tick()


func _unhandled_input(event: InputEvent) -> void:
	if engine == null or event.is_echo() or not event.is_pressed():
		return
	if demo:
		if not demo_locked and (event is InputEventKey or event is InputEventJoypadButton) and not event.is_action("ui_cancel"):
			demo = false
			start()
		return
	var jump: bool = event.is_action("ui_accept") or event.is_action("ui_up") \
		or (event is InputEventKey and event.keycode in [KEY_SPACE, KEY_Z, KEY_W]) \
		or (event is InputEventJoypadButton and event.button_index == JOY_BUTTON_A)
	if jump:
		engine.jump()
	if engine.phase == P.GAME_OVER and event.is_action("ui_accept") and game_over_time > 1.0:
		start()
