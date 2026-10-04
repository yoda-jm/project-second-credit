class_name TinGame
extends Node
## Runs Tinplate Turbo: a championship over the six tracks, four tin cars, one or two of them players (F2 or a second
## pad joins the second), the rest CPUs. Each race: the countdown, the laps, the results (points 4, 3, 2, 1), then the
## upgrade bench where three wrenches buy a level of top speed, grip or acceleration; at the end, the standings.
## 60 Hz ticks. Player one: the arrows or the first pad (the stick or the pad's left/right to turn, A or the right
## trigger to accelerate); in a one-player game W A S D work too. Player two: W A S D (W accelerates) or the second
## pad. "--demo" lets CPUs race; "--track=N" starts at a track; "--players=2".

signal race_started(engine: TinEngine)
signal race_ended()

const T = preload("res://games/tinplate/engine/tin_engine.gd")
const FILE := "res://games/tinplate/tracks/tracks.tin"
enum Mode { RACE, RESULTS, BENCH, FINAL }

var tracks: Array[TinTrack] = []
var engine: TinEngine
var index := 0
var mode := Mode.RACE
var demo := false
var demo_locked := false
var humans := 1
var cars: Array[Dictionary] = []      ## the championship's cars: cpu, up, wrenches, points
var bench_car := -1
var bench_cursor := 0
var mode_t := 0.0
var high := 0
var _acc := 0.0
var _bots: Array[TinBot] = []
var _games := 0


func start(at := 0) -> void:
	tracks = TinTrack.parse_file(FileAccess.get_file_as_string(FILE))
	_games += 1
	cars.clear()
	for i in 4:
		cars.append({"cpu": demo or i >= humans, "up": {"speed": 0, "grip": 0, "accel": 0}, "wrenches": 0, "points": 0})
	index = clampi(at, 0, tracks.size() - 1)
	_race()


func _race() -> void:
	var t := tracks[index]
	engine = TinEngine.new(t, cars, 11 + index * 7 + _games * 31)
	engine.event.connect(_on_event)
	_bots.clear()
	for i in 4:
		_bots.append(TinBot.new(t, i + index * 5, [0.95, 0.85, 0.75, 0.9][i] if demo else [0.85, 0.78, 0.7, 0.82][i]))
	mode = Mode.RACE
	mode_t = 0.0
	race_started.emit(engine)


func _on_event(kind: String, _d: Dictionary) -> void:
	if kind == "race_over" and mode == Mode.RACE:
		_results()


func _results() -> void:
	for i in 4:
		var c := engine.cars[i]
		cars[i]["points"] += T.POINTS[clampi(c["place"] - 1, 0, 3)]
		cars[i]["wrenches"] = c["wrenches"]
	mode = Mode.RESULTS
	mode_t = 0.0
	race_ended.emit()


func _process(delta: float) -> void:
	mode_t += delta
	match mode:
		Mode.RACE:
			_acc = minf(_acc + delta, 0.25)
			while _acc >= T.TICK:
				_acc -= T.TICK
				for i in 4:
					var c := engine.cars[i]
					if c["cpu"] or c["done"]:
						_bots[i].drive(engine, c)
					else:
						_steer(i, c)
				engine.tick()
			# the winner is in: the rest have a little while to finish
			if engine.phase == T.Phase.DONE and engine.phase_t > 8.0 and engine.finished < 4:
				engine.close_race()
		Mode.RESULTS:
			if mode_t > 4.5:
				for i in 4:
					if cars[i]["cpu"]:
						TinBot.upgrade(cars[i])
				bench_car = _next_bench(-1)
				if bench_car >= 0 and index + 1 < tracks.size():
					mode = Mode.BENCH
					bench_cursor = 0
				else:
					_next()
		Mode.FINAL:
			if demo and mode_t > 8.0:
				start(0)


func _next_bench(after: int) -> int:
	for i in range(after + 1, 4):
		if not cars[i]["cpu"] and cars[i]["wrenches"] >= 3:
			return i
	return -1


func _next() -> void:
	index += 1
	if index >= tracks.size():
		mode = Mode.FINAL
		mode_t = 0.0
		if not cars[0]["cpu"]:
			high = maxi(high, cars[0]["points"])
		return
	_race()


## The championship standings: by points.
func standings() -> Array[int]:
	var idx: Array[int] = [0, 1, 2, 3]
	idx.sort_custom(func(a, b): return cars[a]["points"] > cars[b]["points"])
	return idx


func _steer(i: int, c: Dictionary) -> void:
	var left := false
	var right := false
	var gas := false
	var pad := i
	if i == 0:
		left = Input.is_physical_key_pressed(KEY_LEFT)
		right = Input.is_physical_key_pressed(KEY_RIGHT)
		gas = Input.is_physical_key_pressed(KEY_UP)
		if humans == 1:
			left = left or Input.is_physical_key_pressed(KEY_A)
			right = right or Input.is_physical_key_pressed(KEY_D)
			gas = gas or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_SPACE)
	else:
		left = Input.is_physical_key_pressed(KEY_A)
		right = Input.is_physical_key_pressed(KEY_D)
		gas = Input.is_physical_key_pressed(KEY_W)
	var ax := Input.get_joy_axis(pad, JOY_AXIS_LEFT_X)
	var steer := (1.0 if right else 0.0) - (1.0 if left else 0.0)
	if absf(ax) > 0.2:
		steer = ax
	if Input.is_joy_button_pressed(pad, JOY_BUTTON_DPAD_LEFT): steer = -1.0
	if Input.is_joy_button_pressed(pad, JOY_BUTTON_DPAD_RIGHT): steer = 1.0
	gas = gas or Input.is_joy_button_pressed(pad, JOY_BUTTON_A) or Input.get_joy_axis(pad, JOY_AXIS_TRIGGER_RIGHT) > 0.3
	# z grows down the screen, so a screen turn to the right is a positive angle
	c["steer"] = steer
	c["throttle"] = 1.0 if gas else 0.0


func _unhandled_input(event: InputEvent) -> void:
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start(0)
			get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F2 and mode == Mode.RACE \
			and engine.phase == T.Phase.COUNTDOWN and humans == 1:
		humans = 2
		cars[1]["cpu"] = false
		engine.cars[1]["cpu"] = false
	match mode:
		Mode.BENCH:
			if event.is_action_pressed("ui_up"):
				bench_cursor = posmod(bench_cursor - 1, 4)
			elif event.is_action_pressed("ui_down"):
				bench_cursor = posmod(bench_cursor + 1, 4)
			elif event.is_action_pressed("ui_accept"):
				if bench_cursor == 3:
					_bench_done()
				else:
					var k: String = ["speed", "grip", "accel"][bench_cursor]
					var c := cars[bench_car]
					if c["wrenches"] >= 3 and c["up"][k] < 4:
						c["up"][k] += 1
						c["wrenches"] -= 3
						if c["wrenches"] < 3:
							_bench_done()
		Mode.RESULTS:
			if event.is_action_pressed("ui_accept") and mode_t > 1.0:
				mode_t = 99.0
		Mode.FINAL:
			if event.is_action_pressed("ui_accept"):
				start(0)


func _bench_done() -> void:
	bench_car = _next_bench(bench_car)
	bench_cursor = 0
	if bench_car < 0:
		_next()
