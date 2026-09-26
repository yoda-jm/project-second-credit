extends GdUnitTestSuite
## Slipfloe: the arena is a connected maze, a pushed block slides until it meets something and crushes the mites in
## its way, a stuck block shatters, a wall shake stuns, stunned mites can be stamped on, three gems in a row pay,
## and the autopilot clears a stage.

const E = preload("res://games/slipfloe/engine/floe_engine.gd")


func _clear_board() -> FloeEngine:
	var e := FloeEngine.new(0, 1)
	e.phase = E.Phase.PLAY
	e.grid.fill(E.EMPTY)
	e.eggs.clear()
	e.mites.clear()
	e.otter["cell"] = Vector2i(2, 7)
	e.otter["pos"] = Vector2(2, 7)
	return e


func _mite(e: FloeEngine, c: Vector2i) -> Dictionary:
	var m := {"id": 99 + e.mites.size(), "cell": c, "pos": Vector2(c), "dir": Vector2i.ZERO, "stun": 0.0, "speed": 0.0,
		"chew": 0.0, "carried": false, "hatch": 0.0}
	e.mites.append(m)
	return m


func _run(e: FloeEngine, seconds: float) -> void:
	for i in int(seconds / E.TICK):
		e.tick()


func test_the_arena_is_connected() -> void:
	var e := FloeEngine.new(0, 7)
	var open := 0
	for y in E.H:
		for x in E.W:
			if e.at(Vector2i(x, y)) == E.EMPTY:
				open += 1
	var reach := e._distances(e.otter["cell"]).size()
	# every open cell reachable (hatched mites stand in open cells of their own)
	assert_int(reach).is_greater_equal(open - 3)
	assert_int(e.mites.size()).is_equal(3)


func test_a_block_slides_and_crushes() -> void:
	var e := _clear_board()
	e._put(Vector2i(3, 7), E.ICE)
	_mite(e, Vector2i(7, 7))
	e.otter["facing"] = Vector2i(1, 0)
	e.push_pressed = true
	_run(e, 1.5)
	assert_int(e.mites.size()).is_equal(0)
	assert_int(e.at(Vector2i(12, 7))).is_equal(E.ICE)
	assert_int(e.score).is_greater_equal(400)


func test_a_stuck_block_shatters() -> void:
	var e := _clear_board()
	e._put(Vector2i(3, 7), E.ICE)
	e._put(Vector2i(4, 7), E.ICE)
	e.eggs[Vector2i(3, 7)] = true
	e.otter["facing"] = Vector2i(1, 0)
	_mite(e, Vector2i(10, 1))
	e.push_pressed = true
	e.tick()
	assert_int(e.at(Vector2i(3, 7))).is_equal(E.EMPTY)
	assert_bool(e.eggs.has(Vector2i(3, 7))).is_false()


func test_a_wall_shake_stuns_and_a_stomp_finishes() -> void:
	var e := _clear_board()
	e.otter["cell"] = Vector2i(0, 7)
	e.otter["pos"] = Vector2(0, 7)
	e.otter["facing"] = Vector2i(-1, 0)
	var m := _mite(e, Vector2i(0, 9))
	e.push_pressed = true
	e.tick()
	assert_float(m["stun"]).is_greater(0.0)
	e.want = Vector2i(0, 1)
	_run(e, 0.6)
	assert_int(e.mites.size()).is_equal(0)


func test_three_gems_in_a_row_pay() -> void:
	var e := _clear_board()
	e._put(Vector2i(6, 3), E.GEM)
	e._put(Vector2i(7, 3), E.GEM)
	e._put(Vector2i(8, 5), E.GEM)
	_mite(e, Vector2i(10, 12))
	e.otter["cell"] = Vector2i(8, 6)
	e.otter["pos"] = Vector2(8, 6)
	e.otter["facing"] = Vector2i(0, -1)
	e._put(Vector2i(7, 2), E.ICE)
	e._put(Vector2i(8, 2), E.ICE)
	# push the gem up: it stops at (8, 3), below the ice at (8, 2), completing the row
	e.push_pressed = true
	_run(e, 1.0)
	assert_bool(e.gem_done).is_true()
	assert_int(e.score).is_greater_equal(10000)


func test_the_autopilot_clears_a_stage() -> void:
	var cleared := 0
	for s in 3:
		var e := FloeEngine.new(s, 11 + s, 9)
		var bot := FloeBot.new(s)
		for i in int(240.0 / E.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("stage", s, "phase", e.phase, "lives", e.lives, "mites", e.mites.size(), "eggs", e.eggs.size(), "time", snappedf(e.time, 0.1), "score", e.score)
		if e.phase == E.Phase.CLEARED:
			cleared += 1
	assert_int(cleared).is_greater_equal(2)
