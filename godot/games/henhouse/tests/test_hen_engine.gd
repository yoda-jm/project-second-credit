extends GdUnitTestSuite
## Henhouse Heist: levels parse, the farmhand walks, climbs and jumps a two-cell gap, eggs are collected, grain stops
## the clock, a hen costs a life, lifts carry, and the autopilot collects every egg of the first levels.

const E = preload("res://games/henhouse/engine/hen_engine.gd")
const FILE := "res://games/henhouse/levels/farm.hen"


func _levels() -> Array[HenLevel]:
	return HenLevel.parse_file(FileAccess.get_file_as_string(FILE))


func _play(i := 0) -> HenEngine:
	var e := HenEngine.new(_levels()[i], i, 1)
	e.phase = E.Phase.PLAY
	e.hens.clear()
	return e


func _run(e: HenEngine, seconds: float) -> void:
	for i in int(seconds / E.TICK):
		e.tick()


func test_levels_parse() -> void:
	var ls := _levels()
	assert_int(ls.size()).is_equal(3)
	assert_int(ls[0].eggs.size()).is_equal(14)
	assert_int(ls[1].lift_col).is_equal(15)
	assert_bool(ls[2].goose).is_true()


func test_walk_and_climb() -> void:
	var e := _play()
	e.move_x = 1.0
	_run(e, 0.5)
	# at the ladder at x = 5: climb up to the row-21 platform
	e.move_x = 0.0
	e.hero["pos"].x = 5.5
	e.up = true
	_run(e, 2.0)
	assert_float(e.hero["pos"].y).is_equal_approx(21.0, 0.05)


func test_a_jump_clears_a_two_cell_gap() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(10.1, 5.0)
	e.hero["facing"] = -1
	e.move_x = -1.0
	e.jump_pressed = true
	_run(e, 1.0)
	assert_str(e.hero["state"]).is_equal("walk")
	assert_float(e.hero["pos"].y).is_equal(5.0)
	assert_float(e.hero["pos"].x).is_less(7.9)


func test_eggs_and_grain() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(7.0, 25.0)
	e.move_x = 1.0
	_run(e, 1.5)
	assert_bool(e.eggs.has(Vector2i(8, 24))).is_false()
	assert_float(e.freeze).is_greater(0.0)
	var c0 := e.clock
	_run(e, 1.0)
	assert_float(e.clock).is_equal(c0)


func test_a_hen_costs_a_life() -> void:
	var e := HenEngine.new(_levels()[0], 0, 1)
	e.phase = E.Phase.PLAY
	e.hens[0]["pos"] = e.hero["pos"]
	e.hens[0]["speed"] = 0.0
	e.tick()
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_lifts_carry() -> void:
	var e := _play(1)
	e.lifts = [25.0, 12.0]
	e.hero["pos"] = Vector2(16.0, 25.0)
	e.hero["lift"] = -1
	_run(e, 1.0)
	assert_float(e.hero["pos"].y).is_less(24.0)


func test_the_autopilot_collects_the_eggs() -> void:
	for i in 1:  # the first level (the others are longer; they play in the demo)
		var e := HenEngine.new(_levels()[i], i, 2 + i, 9)
		var bot := HenBot.new(i)
		var deaths := []
		e.event.connect(func(k, d): if k == "die": deaths.append(d["how"]))
		for t in int(260.0 / E.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("level", i, "phase", e.phase, "eggs left", e.eggs.size(), "deaths", deaths, "time", snappedf(e.time, 0.1))
		assert_int(e.phase).is_equal(E.Phase.CLEARED)
