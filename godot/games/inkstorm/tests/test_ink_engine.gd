extends GdUnitTestSuite
## Inkstorm: the marker runs on the edges, draws into the open, closing a line claims the storm-free side, the trail
## may not touch itself, the storm and the sparks cost a life, and the autopilot clears a stage.

const E = preload("res://games/inkstorm/engine/ink_engine.gd")


func _engine() -> InkEngine:
	var e := InkEngine.new(0, 1)
	e.phase = E.Phase.PLAY
	e.sparks.clear()
	e.storms[0]["pos"] = Vector2(100, 60)
	e.storms[0]["vel"] = Vector2.ZERO
	return e


func _walk(e: InkEngine, d: Vector2i, n: int, draw := false) -> void:
	e.want = d
	e.draw_fast = draw
	for i in n:
		var p := e.pos
		for t in 10:
			e._move_marker()
			if e.pos != p:
				break


func test_the_marker_keeps_to_the_edges() -> void:
	var e := _engine()
	e.pos = Vector2i(10, E.H - 1)
	_walk(e, Vector2i(0, -1), 3)
	assert_that(e.pos).is_equal(Vector2i(10, E.H - 1))
	_walk(e, Vector2i(1, 0), 5)
	assert_that(e.pos).is_equal(Vector2i(15, E.H - 1))


func test_a_closed_line_claims_the_side_without_the_storm() -> void:
	var e := _engine()
	e.pos = Vector2i(10, E.H - 1)
	_walk(e, Vector2i(0, -1), 10, true)
	assert_bool(e.drawing()).is_true()
	_walk(e, Vector2i(1, 0), 10, true)
	_walk(e, Vector2i(0, 1), 10, true)
	assert_bool(e.drawing()).is_false()
	# a 9 x 10 pocket plus its line
	assert_int(e.at(Vector2i(15, E.H - 5))).is_equal(E.CLAIMED)
	assert_int(e.at(Vector2i(60, 40))).is_equal(E.FREE)
	assert_float(e.claimed).is_greater(0.005)
	assert_int(e.score).is_greater(100)


func test_the_line_may_not_touch_itself() -> void:
	var e := _engine()
	e.pos = Vector2i(10, E.H - 1)
	_walk(e, Vector2i(0, -1), 6, true)
	_walk(e, Vector2i(1, 0), 3, true)
	_walk(e, Vector2i(0, 1), 3, true)
	var p := e.pos
	_walk(e, Vector2i(-1, 0), 2, true)
	assert_int(e.pos.x).is_greater_equal(p.x - 1)


func test_the_storm_cuts_the_line() -> void:
	var e := _engine()
	e.pos = Vector2i(10, E.H - 1)
	_walk(e, Vector2i(0, -1), 12, true)
	e.storms[0]["pos"] = Vector2(10.5, E.H - 8)
	e._check_hits()
	assert_int(e.phase).is_equal(E.Phase.DYING)
	assert_int(e.lives).is_equal(2)
	assert_bool(e.drawing()).is_false()
	assert_int(e.at(Vector2i(10, E.H - 5))).is_equal(E.FREE)


func test_sparks_hunt_along_the_edges() -> void:
	var e := InkEngine.new(0, 3)
	e.phase = E.Phase.PLAY
	e.time = 10.0
	e.pos = Vector2i(0, E.H / 2)
	for i in 1500:
		e.tick()
		if e.phase != E.Phase.PLAY:
			break
	assert_int(e.lives).is_equal(2)


func test_the_autopilot_clears_a_stage() -> void:
	var cleared := 0
	for s in 3:
		var e := InkEngine.new(s, 5 + s, 9)
		var bot := InkBot.new(s)
		for i in int(300.0 / E.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("stage", s, "claimed", e.claimed, "lives", e.lives, "time", e.time, "score", e.score)
		if e.phase == E.Phase.CLEARED:
			cleared += 1
	assert_int(cleared).is_greater_equal(2)
