class_name RidgeGame
extends Node
## Runs Ridgefire: the seats (two to four tanks, each a player or the CPU), then rounds, with the shop between them,
## then the standings. 60 Hz ticks. Aiming: left/right turn the barrel (shift for fine), up/down set the power, Q/E,
## Tab or the shoulder buttons pick a weapon, space, enter or the pad's A fires; a gamepad's stick aims too. The mouse:
## point where to shoot and hold the left button to set the power, let go to fire. CPU tanks think on a worker thread,
## then visibly turn their barrel and fire. "--demo" lets CPUs play; "--players=N" sets the tanks, "--humans=N" the
## players among them; "--rounds=N"; "--land=N" starts on a given land (1-5).

signal round_started(engine: RidgeEngine)
signal game_over()

const R = preload("res://games/ridgefire/engine/ridge_engine.gd")
enum Mode { SEATS, PLAY, SHOP, FINAL }
const SHOP_ITEMS := ["heavy", "mirv", "roller", "dirt", "digger", "nuke", "shield"]

var engine: RidgeEngine
var mode := Mode.SEATS
var demo := false
var demo_locked := false
var seats := 3
var cpu := [false, true, true, true]
var rounds := 5
var games := 0
var land := 0                     ## the first round's land ("--land=N")
var shop_player := -1             ## the player in the shop
var shop_cursor := 0
var mouse_aim := false
var charging := false             ## the mouse button is held: the power climbs
var _acc := 0.0
var _bots: Array[RidgeBot] = []
var _task := -1
var _planned := false
var _cpu_t := 0.0
var _from := Vector2.ZERO          ## the CPU's aim when it began to turn
var _end_t := 0.0
var _hold := 0.0


func start() -> void:
	if demo:
		seats = 3
		cpu = [true, true, true, true]
		_begin()
	else:
		mode = Mode.SEATS


func _begin() -> void:
	_wait()
	games += 1
	engine = RidgeEngine.new(seats, cpu.slice(0, seats), 17 + games * 31, rounds)
	if land > 0:
		engine.first_land = land
		engine.new_round()
	_bots.clear()
	for i in seats:
		var b := RidgeBot.new(i * 13 + games)
		b.skill = 0.35 if demo else 0.6
		_bots.append(b)
	engine.event.connect(_on_event)
	mode = Mode.PLAY
	_planned = false
	round_started.emit(engine)


func _on_event(kind: String, _d: Dictionary) -> void:
	if kind == "turn":
		_planned = false
		_cpu_t = 0.0


func _process(delta: float) -> void:
	if mode != Mode.PLAY and mode != Mode.SHOP:
		if mode == Mode.FINAL and demo:
			_end_t += delta
			if _end_t > 7.0:
				_begin()
		return
	if mode == Mode.SHOP:
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= R.TICK:
		_acc -= R.TICK
		_step(R.TICK)


func _step(dt: float) -> void:
	var e := engine
	match e.phase:
		R.Phase.AIM:
			if e.current()["cpu"]:
				_drive_cpu(dt)
			else:
				_steer(dt)
		R.Phase.ROUND_END:
			_end_t += dt
			if _end_t > 3.5:
				_end_t = 0.0
				for i in e.players.size():
					if e.players[i]["cpu"]:
						RidgeBot.shop(e, i)
				shop_player = _next_shopper(-1)
				if shop_player >= 0 and e.round_i + 1 < e.rounds:
					mode = Mode.SHOP
					shop_cursor = 0
				else:
					_after_shop()
			return
		R.Phase.OVER:
			mode = Mode.FINAL
			_end_t = 0.0
			game_over.emit()
			return
	e.tick()


func _next_shopper(after: int) -> int:
	for i in range(after + 1, engine.players.size()):
		if not engine.players[i]["cpu"]:
			return i
	return -1


func _after_shop() -> void:
	mode = Mode.PLAY
	engine.next_round()
	if engine.phase == R.Phase.OVER:
		mode = Mode.FINAL
		_end_t = 0.0
		game_over.emit()
		return
	_planned = false
	round_started.emit(engine)


# ------------------------------------------------------------------ the CPU

func _drive_cpu(dt: float) -> void:
	var me := engine.current()
	if not _planned:
		if _task < 0:
			_bots[engine.turn].plan_from = Vector2(me["angle"], me["power"])
			_task = WorkerThreadPool.add_task(_bots[engine.turn].plan.bind(engine))
			_cpu_t = 0.0
			_from = Vector2(me["angle"], me["power"])
		_cpu_t += dt
		if WorkerThreadPool.is_task_completed(_task):
			_wait()
			_planned = true
			_cpu_t = 0.0
		return
	# turn the barrel and set the power over a moment, then fire
	var b := _bots[engine.turn]
	_cpu_t += dt
	var k := clampf(_cpu_t / 1.4, 0.0, 1.0)
	k = k * k * (3.0 - 2.0 * k)
	me["angle"] = lerpf(_from.x, b.angle, k)
	me["power"] = lerpf(_from.y, b.power, clampf((_cpu_t - 0.5) / 1.0, 0.0, 1.0))
	if _cpu_t > 0.6 and me["ammo"].has(b.weapon):
		me["weapon"] = b.weapon
	if _cpu_t > 2.1:
		me["angle"] = b.angle
		me["power"] = b.power
		engine.fire()


func _wait() -> void:
	if _task >= 0:
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -1


# ------------------------------------------------------------------ a player aiming

func _steer(dt: float) -> void:
	var me := engine.current()
	var fine := Input.is_key_pressed(KEY_SHIFT)
	var turn := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A): turn += 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D): turn -= 1.0
	var pw := 0.0
	if Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W): pw += 1.0
	if Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S): pw -= 1.0
	var ax := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
	var ay := Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
	if absf(ax) > 0.2: turn -= ax
	if absf(ay) > 0.2: pw -= ay
	if turn != 0.0 or pw != 0.0:
		_hold += dt
		mouse_aim = false
	else:
		_hold = 0.0
	var speed := 6.0 if fine else minf(14.0 + _hold * 40.0, 70.0)
	me["angle"] = clampf(me["angle"] + turn * speed * dt, 0.0, 180.0)
	me["power"] = clampf(me["power"] + pw * (8.0 if fine else minf(16.0 + _hold * 30.0, 60.0)) * dt, 1.0, 100.0)
	if charging:
		me["power"] = clampf(me["power"] + 45.0 * dt, 1.0, 100.0)


func _unhandled_input(event: InputEvent) -> void:
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			_wait()
			mode = Mode.SEATS
			get_viewport().set_input_as_handled()
		return
	match mode:
		Mode.SEATS:
			_seats_input(event)
		Mode.SHOP:
			_shop_input(event)
		Mode.FINAL:
			if event.is_action_pressed("ui_accept"):
				mode = Mode.SEATS
		Mode.PLAY:
			_play_input(event)


func _seats_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up"):
		seats = mini(4, seats + 1)
	elif event.is_action_pressed("ui_down"):
		seats = maxi(2, seats - 1)
	elif event is InputEventKey and event.pressed and not event.echo and event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_4:
		var i: int = event.physical_keycode - KEY_1
		if i < seats:
			cpu[i] = not cpu[i]
	elif event.is_action_pressed("ui_left") or event.is_action_pressed("ui_right"):
		rounds = clampi(rounds + (1 if event.is_action_pressed("ui_right") else -1), 1, 10)
	elif event.is_action_pressed("ui_accept"):
		_begin()


func _shop_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up"):
		shop_cursor = posmod(shop_cursor - 1, SHOP_ITEMS.size() + 1)
	elif event.is_action_pressed("ui_down"):
		shop_cursor = posmod(shop_cursor + 1, SHOP_ITEMS.size() + 1)
	elif event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_SPACE):
		if shop_cursor == SHOP_ITEMS.size():
			_shop_done()
		else:
			engine.buy(shop_player, SHOP_ITEMS[shop_cursor])
	elif event.is_action_pressed("ui_cancel") or (event is InputEventKey and event.pressed and event.physical_keycode == KEY_TAB):
		_shop_done()
		get_viewport().set_input_as_handled()


func _shop_done() -> void:
	shop_player = _next_shopper(shop_player)
	shop_cursor = 0
	if shop_player < 0:
		_after_shop()


func _play_input(event: InputEvent) -> void:
	if engine.phase != R.Phase.AIM or engine.current()["cpu"]:
		return
	var key: bool = event is InputEventKey and event.pressed and not event.echo
	if (key and event.physical_keycode in [KEY_SPACE, KEY_ENTER, KEY_KP_ENTER]) or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_A):
		engine.fire()
	elif (key and event.physical_keycode in [KEY_E, KEY_TAB]) or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_RIGHT_SHOULDER):
		engine.cycle_weapon(1)
	elif (key and event.physical_keycode == KEY_Q) or (event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_LEFT_SHOULDER):
		engine.cycle_weapon(-1)
	# the mouse: point to aim; hold the left button to wind the power up, let go to fire
	var cam := get_viewport().get_camera_3d()
	if cam and event is InputEventMouseMotion:
		var from := cam.project_ray_origin(event.position)
		var dir := cam.project_ray_normal(event.position)
		if absf(dir.z) > 0.001:
			var hit := from + dir * (-from.z / dir.z)
			var me := engine.current()
			var d := Vector2(hit.x, hit.y) - Vector2(me["x"], me["y"] + 1.1)
			if d.length() > 0.5:
				me["angle"] = clampf(rad_to_deg(atan2(d.y, d.x)), 0.0, 180.0)
				mouse_aim = true
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			charging = true
			engine.current()["power"] = 5.0
		elif charging:
			charging = false
			engine.fire()
	elif event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
		engine.cycle_weapon(1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else -1)
