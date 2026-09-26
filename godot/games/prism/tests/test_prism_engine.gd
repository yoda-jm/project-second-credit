extends GdUnitTestSuite
## Prism Breaker: the walls parse (ours and LBreakout2's layout), the paddle sets the angle, bricks break and hard
## ones take several hits, capsules take effect, a lost ball costs a life, and the autopilot clears walls.

const E = preload("res://games/prism/engine/prism_engine.gd")
const FILE := "res://games/prism/levels/spectrum.wall"


func _levels() -> Array[PrismLevel]:
	return PrismLevel.parse_file(FileAccess.get_file_as_string(FILE))


func _run(e: PrismEngine, seconds: float, bot: PrismBot = null) -> void:
	for i in int(seconds / E.TICK):
		if bot:
			bot.drive(e)
		e.tick()
		if e.phase != E.Phase.PLAY and e.phase != E.Phase.SERVE:
			return


func test_walls_parse() -> void:
	var ls := _levels()
	assert_int(ls.size()).is_equal(8)
	assert_str(ls[0].name).is_equal("First Light")
	for l in ls:
		for r in l.rows:
			assert_int(r.length()).is_equal(13)


func test_lbreakout_layout_reads() -> void:
	var text := "Title: Test\nAuthor: x\nBricks:\n..............\n.aab##cc......\n\nBonus:\n..............\n"
	var ls := PrismLevel.parse_file(text)
	assert_int(ls.size()).is_equal(1)
	assert_str(ls[0].name).is_equal("Test")
	assert_int(ls[0].rows.size()).is_equal(2)
	assert_str(ls[0].rows[1].substr(4, 2)).is_equal("SS")
	assert_str(ls[0].rows[0]).is_equal(".............")


func test_the_paddle_edge_sends_the_ball_wide() -> void:
	var e := PrismEngine.new(_levels()[0], 0, 1)
	e.launch()
	var b: Dictionary = e.balls[0]
	b["pos"] = Vector2(e.paddle_x + 0.95, E.PADDLE_Y - 0.5)
	b["vel"] = Vector2(0, b["speed"])
	_run(e, 0.2)
	assert_float(b["vel"].y).is_less(0.0)
	assert_float(b["vel"].x).is_greater(b["speed"] * 0.6)


func test_bricks_break_and_hard_ones_take_hits() -> void:
	var e := PrismEngine.new(_levels()[1], 2, 1)
	var hard := Vector2i(6, 1)
	assert_str(e.bricks[hard]["kind"]).is_equal("H")
	var hits: int = e.bricks[hard]["hits"]
	assert_int(hits).is_equal(3)
	for i in hits - 1:
		e._hit_brick(hard)
	assert_bool(e.bricks.has(hard)).is_true()
	var n := e.breakable
	e._hit_brick(hard)
	assert_bool(e.bricks.has(hard)).is_false()
	assert_int(e.breakable).is_equal(n - 1)


func test_capsules_take_effect() -> void:
	var e := PrismEngine.new(_levels()[0], 0, 1)
	e.launch()
	e._take("wide")
	assert_float(e.paddle_w).is_equal(3.0)
	e._take("multi")
	assert_int(e.balls.size()).is_equal(3)
	assert_float(e.paddle_w).is_equal(2.0)
	var lives := e.lives
	e._take("life")
	assert_int(e.lives).is_equal(lives + 1)


func test_a_lost_ball_costs_a_life() -> void:
	var e := PrismEngine.new(_levels()[0], 0, 1)
	e.launch()
	e.balls[0]["pos"] = Vector2(0.5, E.PADDLE_Y + 0.5)
	e.balls[0]["vel"] = Vector2(0, 8)
	e.target_x = 12.0
	_run(e, 1.0)
	assert_int(e.phase).is_equal(E.Phase.LOST)
	assert_int(e.lives).is_equal(2)


func test_the_autopilot_clears_walls() -> void:
	var cleared := 0
	var ls := _levels()
	for i in [0, 1, 2]:
		var e := PrismEngine.new(ls[i], i, 7 + i, 5)
		var bot := PrismBot.new(3)
		for round in 6:
			_run(e, 240.0, bot)
			if e.phase == E.Phase.LOST:
				e.respawn()
			else:
				break
		if e.phase == E.Phase.CLEARED:
			cleared += 1
	assert_int(cleared).is_greater_equal(2)
