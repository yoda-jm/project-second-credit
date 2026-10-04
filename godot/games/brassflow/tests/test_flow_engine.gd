extends GdUnitTestSuite
## Brassflow: pieces and their openings, turning and placing and replacing, the flow filling a laid pipe, spilling at
## an open end, reaching the engine, the cross's loop bonus, layouts with a way through, and the autopilot passing levels.

const F = preload("res://games/brassflow/engine/flow_engine.gd")


func _engine(level := 0) -> FlowEngine:
	var e := FlowEngine.new(level)
	e.phase = F.Phase.PLAY
	return e


func test_pieces_route_the_flow() -> void:
	assert_bool(FlowEngine.accepts("h", 3)).is_true()
	assert_bool(FlowEngine.accepts("h", 0)).is_false()
	assert_int(FlowEngine.exit_of("ne", 0)).is_equal(1)
	assert_int(FlowEngine.exit_of("x", 3)).is_equal(1)


func test_placing_takes_the_front_piece_and_refills_the_queue() -> void:
	var e := _engine()
	var first: String = e.queue[0]
	e.cursor = Vector2i(8, 0)
	e.place_pressed = true
	e.tick()
	assert_str(e.grid[Vector2i(8, 0)]["piece"]).is_equal(first)
	assert_int(e.queue.size()).is_equal(F.QUEUE)


func test_replacing_costs_and_pauses() -> void:
	var e := _engine()
	e.score = 500
	e.cursor = Vector2i(8, 0)
	e.place_pressed = true
	e.tick()
	e.place_pressed = true
	e.tick()
	assert_int(e.score).is_equal(450)
	assert_float(e.cool).is_greater(0.0)


func test_turning_the_front_piece() -> void:
	var e := _engine()
	e.queue[0] = "ne"
	e.rotate_pressed = true
	e.tick()
	assert_str(e.queue[0]).is_equal("se")
	e.queue[0] = "h"
	e.rotate_pressed = true
	e.tick()
	assert_str(e.queue[0]).is_equal("v")


func test_every_layout_has_a_way_through() -> void:
	for lv in 8:
		for sd in 6:
			var e := FlowEngine.new(lv, 0, 3, sd + 1)
			assert_int(e.shortest()).is_greater(0)
			assert_bool(e.open_cell(e.feed())).is_true()


func test_the_flow_spills_at_an_open_end_and_fails() -> void:
	var e := _engine()
	e.countdown = 0.05
	e.step_time = 0.05
	var spills := []
	e.event.connect(func(k, d): if k == "spill": spills.append(d["why"]))
	for i in 120:
		e.tick()
	assert_array(spills).contains(["empty"])
	assert_int(e.chances).is_equal(2)


func test_a_pipe_into_the_engine_passes() -> void:
	var e := _engine()
	e.blocked.clear()
	e.source = Vector2i(1, 3)
	e.source_dir = 1
	e.exit_cell = Vector2i(6, 3)
	e.exit_dir = 3
	for x in range(2, 6):
		e.grid[Vector2i(x, 3)] = {"piece": "h", "filled": []}
	e.countdown = 0.05
	e.step_time = 0.05
	for i in 200:
		e.tick()
	assert_int(e.filled).is_equal(4)
	assert_bool(e.passed()).is_true()


func test_the_engine_refuses_the_wrong_side() -> void:
	var e := _engine()
	e.blocked.clear()
	e.source = Vector2i(1, 3)
	e.source_dir = 1
	e.exit_cell = Vector2i(4, 3)
	e.exit_dir = 0
	for x in range(2, 4):
		e.grid[Vector2i(x, 3)] = {"piece": "h", "filled": []}
	e.countdown = 0.05
	e.step_time = 0.05
	for i in 200:
		e.tick()
	assert_bool(e.passed()).is_false()
	assert_int(e.chances).is_equal(2)


func test_a_cross_filled_both_ways_scores_the_loop() -> void:
	var e := _engine()
	var c := Vector2i(5, 3)
	e.grid[c] = {"piece": "x", "filled": [3]}
	e.head = c + Vector2i(0, -1)
	e.grid[e.head] = {"piece": "v", "filled": [0]}
	e.head_from = 0
	e.flowing = true
	var before := e.score
	e._advance()
	assert_int(e.score - before).is_equal(550)


func test_autopilot_passes_levels() -> void:
	var passed := 0
	for lv in 5:
		var e := FlowEngine.new(lv, 0, 3, 5)
		var bot := FlowBot.new()
		for n in int(240.0 / F.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == F.Phase.DONE or e.phase == F.Phase.OVER:
				break
		prints("autopilot level", lv + 1, "passed", e.passed(), "filled", e.filled, "shortest", e.length, "route", bot.route.size(), "time", snappedf(e.time, 0.1))
		if e.passed():
			passed += 1
	assert_int(passed).is_greater_equal(4)
