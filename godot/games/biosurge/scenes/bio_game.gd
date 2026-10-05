class_name BioGame
extends Node
## Runs Biosurge: five levels, each through a different cavern to its boss, with the trader's shop in between (the
## credits, score, lives and weapons carried on). 60 Hz ticks. Arrows, W A S D or the stick fly the ship; space, Z,
## the left mouse button or the pad's A fires (hold it). In the shop: up and down to choose, enter to buy, escape or
## the last line to fly on. "--demo" lets the autopilot fly (it shops too); "--level=N" starts at a level.

signal level_started(engine: BioEngine)
signal shop_opened()
signal game_over()

const B = preload("res://games/biosurge/engine/bio_engine.gd")
enum Mode { FLY, SHOP, END }

var engine: BioEngine
var level := 0
var mode := Mode.FLY
var demo := false
var demo_locked := false
var won := false
var high := 0
var cursor := 0
var mode_t := 0.0
var _acc := 0.0
var _bot: BioBot
var _games := 0


func start(at := 0) -> void:
	_games += 1
	level = clampi(at, 0, 4)
	won = false
	_load({})


func _load(carry: Dictionary) -> void:
	engine = BioEngine.new(level, carry, _games * 7 + 3)
	_bot = BioBot.new()
	mode = Mode.FLY
	mode_t = 0.0
	level_started.emit(engine)


func _process(delta: float) -> void:
	mode_t += delta
	if engine == null:
		return
	match mode:
		Mode.FLY:
			if engine.phase == B.Phase.OVER and engine.phase_t <= 0.0:
				_end()
				return
			if engine.phase == B.Phase.CLEARED and engine.phase_t <= 0.0:
				if level >= 4:
					won = true
					_end()
					return
				mode = Mode.SHOP
				mode_t = 0.0
				cursor = 0
				shop_opened.emit()
				return
			_acc = minf(_acc + delta, 0.25)
			while _acc >= B.TICK:
				_acc -= B.TICK
				if demo:
					_bot.drive(engine)
				else:
					_steer()
				engine.tick()
		Mode.SHOP:
			if demo and mode_t > 3.0:
				_bot_shop()
				_fly_on()
		Mode.END:
			if demo and mode_t > 6.0:
				start(0)


func _end() -> void:
	mode = Mode.END
	mode_t = 0.0
	high = maxi(high, engine.score)
	game_over.emit()


func _fly_on() -> void:
	level += 1
	_load(engine.carry())


## The autopilot's shopping: what it can afford, best first.
func _bot_shop() -> void:
	for want in ["gun", "side", "homing", "drone", "gun", "speed", "laser", "rear", "gun"]:
		for it in B.SHOP:
			if it[0] == want:
				engine.buy(it[0], it[2])


func _steer() -> void:
	var v := Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_LEFT) or Input.is_physical_key_pressed(KEY_A): v.x -= 1.0
	if Input.is_physical_key_pressed(KEY_RIGHT) or Input.is_physical_key_pressed(KEY_D): v.x += 1.0
	if Input.is_physical_key_pressed(KEY_UP) or Input.is_physical_key_pressed(KEY_W): v.y += 1.0
	if Input.is_physical_key_pressed(KEY_DOWN) or Input.is_physical_key_pressed(KEY_S): v.y -= 1.0
	var stick := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), -Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	if stick.length() > 0.2:
		v = stick
	engine.input = v.limit_length(1.0)
	engine.firing = Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_Z) \
		or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or Input.is_joy_button_pressed(0, JOY_BUTTON_A) \
		or Input.get_joy_axis(0, JOY_AXIS_TRIGGER_RIGHT) > 0.3


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start(0)
			get_viewport().set_input_as_handled()
		return
	match mode:
		Mode.SHOP:
			if event.is_action_pressed("ui_up"):
				cursor = posmod(cursor - 1, B.SHOP.size() + 1)
			elif event.is_action_pressed("ui_down"):
				cursor = posmod(cursor + 1, B.SHOP.size() + 1)
			elif event.is_action_pressed("ui_accept"):
				if cursor == B.SHOP.size():
					_fly_on()
				else:
					var it: Array = B.SHOP[cursor]
					if engine.buy(it[0], it[2]):
						shop_opened.emit()   # refresh
			elif event.is_action_pressed("ui_cancel"):
				_fly_on()
				get_viewport().set_input_as_handled()
		Mode.END:
			if event.is_action_pressed("ui_accept"):
				start(0)
