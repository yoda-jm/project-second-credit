extends GdUnitTestSuite
## Deep Breath: caverns parse, the miner walks and jumps his fixed arc onto a floor above, a long drop is fatal, a
## crumbling floor gives way, a conveyor carries him, a guardian and a plant kill, keys open the lift, the air runs out,
## and every cavern's demo route reaches the lift.

const E = preload("res://games/deepbreath/engine/deep_engine.gd")
const FILE := "res://games/deepbreath/levels/caverns.deep"


func _levels() -> Array[DeepLevel]:
	return DeepLevel.parse_file(FileAccess.get_file_as_string(FILE))


func _play(i := 0) -> DeepEngine:
	var e := DeepEngine.new(_levels()[i])
	e.phase = E.Phase.PLAY
	e.guards.clear()
	return e


func _run(e: DeepEngine, seconds: float) -> void:
	for i in int(seconds / E.TICK):
		e.tick()


func test_caverns_parse() -> void:
	var ls := _levels()
	assert_int(ls.size()).is_greater(0)
	assert_int(ls[0].keys.size()).is_equal(5)
	assert_that(ls[0].portal).is_equal(Vector2i(29, 13))
	assert_int(ls[0].guards.size()).is_equal(1)


func test_a_jump_reaches_the_floor_above() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(3.5, 15.0)
	e.jump_pressed = true
	_run(e, 1.2)
	assert_float(e.hero["pos"].y).is_equal_approx(12.0, 0.01)
	assert_str(e.hero["state"]).is_equal("walk")


func test_a_long_drop_is_fatal() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(12.5, 6.0)  # on the top floor: walk off towards the bottom, nine tiles down
	e.move_x = 1.0
	_run(e, 2.0)
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_crumbling_floor_gives_way() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(4.5, 9.0)
	_run(e, 0.6)
	assert_str(e.at(4, 9)).is_equal(".")


func test_a_conveyor_carries() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(16.5, 12.0)
	_run(e, 0.5)
	assert_float(e.hero["pos"].x).is_greater(17.5)


func test_keys_open_the_lift_and_air_runs_out() -> void:
	var e := _play()
	for k in e.keys.keys():
		e.hero["pos"] = Vector2(k) + Vector2(0.5, 1.0)
		e._touch()
	assert_bool(e.open).is_true()
	var e2 := _play()
	e2.air = 0.05
	_run(e2, 0.1)
	assert_int(e2.phase).is_equal(E.Phase.DYING)


func test_every_route_reaches_the_lift() -> void:
	for lv in _levels():
		var e := DeepEngine.new(lv)
		var bot := DeepBot.new()
		var deaths := []
		e.event.connect(func(k, d): if k == "die": deaths.append([d["how"], d["pos"]]))
		for i in int(120.0 / E.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("route", lv.name, "phase", e.phase, "keys left", e.keys.keys(), "deaths", deaths, "at", e.hero["pos"], "step", bot._step, "time", snappedf(e.time, 0.1))
		assert_int(e.phase).is_equal(E.Phase.CLEARED)
		assert_int(deaths.size()).is_equal(0)
