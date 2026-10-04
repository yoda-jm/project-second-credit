extends GdUnitTestSuite
## Brassflow: pieces and their openings, placing and replacing, the flow filling a laid pipe, spilling at an open end,
## the length to pass, the cross's loop bonus, and the autopilot passing levels.

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


func test_the_flow_spills_at_an_open_end_and_a_short_pipe_fails() -> void:
	var e := _engine()
	e.countdown = 0.05
	e.step_time = 0.05
	var spills := []
	e.event.connect(func(k, d): if k == "spill": spills.append(d["why"]))
	for i in 120:
		e.tick()
	assert_array(spills).contains(["empty"])
	assert_int(e.chances).is_equal(2)


func test_a_laid_pipe_passes() -> void:
	var e := _engine()
	e.length = 3
	# a straight run out of the source
	var c := e.source
	var piece := "h" if e.source_dir == 1 else "v"
	for i in 4:
		c += F.DIRS[e.source_dir]
		if FlowEngine.inside(c):
			e.grid[c] = {"piece": piece, "filled": []}
	e.countdown = 0.05
	e.step_time = 0.05
	for i in 200:
		e.tick()
	assert_bool(e.filled >= 3).is_true()
	assert_bool(e.passed()).is_true()


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
		prints("autopilot level", lv + 1, "passed", e.passed(), "filled", e.filled, "of", e.length, "route", bot.route.size(), "time", snappedf(e.time, 0.1))
		if e.passed():
			passed += 1
	assert_int(passed).is_greater_equal(4)
