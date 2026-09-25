class_name FruitburrowGame
extends Node
## Runs a Fruitburrow game in real time: fixed 60 Hz ticks of the engine, player input (the most recently
## pressed direction wins), the demo autopilot, the next garden after a clear, restarts.
## The view, HUD and audio read `engine` and listen to its events.

signal started(engine: FruitburrowEngine)
signal garden_started(engine: FruitburrowEngine)

const P = FruitburrowEngine.Phase
const DIR_ACTIONS := {"ui_up": Vector2i.UP, "ui_down": Vector2i.DOWN, "ui_left": Vector2i.LEFT, "ui_right": Vector2i.RIGHT}

@export_file("*.gdn") var pack_file := "res://games/fruitburrow/gardens/orchard.gdn"

var engine: FruitburrowEngine
var gardens: Array[GardenMap] = []
var garden_index := 0
var demo := false
var demo_locked := false  ## captures: the demo cannot be taken over by input
var game_over_time := 0.0
var _acc := 0.0
var _held: Array[Vector2i] = []  ## held directions, most recent last
var _bot := GardenBot.new()
var _seed := 1


func start(seed: int = -1) -> void:
	_seed = seed if seed >= 0 else randi()
	gardens = GardenMap.load_pack(pack_file)
	garden_index = 0
	engine = FruitburrowEngine.new(gardens[0], _seed)
	game_over_time = 0.0
	_held.clear()
	started.emit(engine)
	garden_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null:
		return
	if engine.phase == P.GAME_OVER:
		game_over_time += delta
		if demo and game_over_time > 6.0:
			start(_seed + 1)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= FruitburrowEngine.TICK:
		_acc -= FruitburrowEngine.TICK
		if demo:
			_bot.drive(engine)
		else:
			engine.input_dir = _held.back() if not _held.is_empty() else Vector2i.ZERO
		engine.tick()
		if engine.level_done():
			garden_index = (garden_index + 1) % gardens.size()
			engine.load_garden(gardens[garden_index], engine.level + 1)
			garden_started.emit(engine)


func _unhandled_input(event: InputEvent) -> void:
	if engine == null or event.is_echo():
		return
	if demo:
		if not demo_locked and event.is_pressed() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false  # a key press takes over
			start()
		return
	for action in DIR_ACTIONS:
		if event.is_action(action):
			var d: Vector2i = DIR_ACTIONS[action]
			_held.erase(d)
			if event.is_pressed():
				_held.append(d)
			return
	if event.is_pressed() and (event.is_action("ui_accept") or (event is InputEventKey and event.keycode in [KEY_SPACE, KEY_CTRL])
			or (event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT)):
		engine.fire()
	if engine.phase == P.GAME_OVER and event.is_pressed() and event.is_action("ui_accept") and game_over_time > 1.0:
		start()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_PAUSED:
		_held.clear()  # keys released while away never reach us
