extends GdUnitTestSuite
## Tumbletop: hops, painting under each level's rule, falling off, the discs and the lured serpent, enemies, and the
## autopilot clearing rounds.

const T = preload("res://games/tumbletop/engine/tumble_engine.gd")


func _engine(level := 0, round := 0) -> TumbleEngine:
	var e := TumbleEngine.new(level, round)
	e.phase = T.Phase.PLAY
	e._spawn_t = 9999.0
	return e


func _hop(e: TumbleEngine, dir: String) -> void:
	e.want = dir
	e.tick()
	for i in int(T.HOP / T.TICK) + 2:
		e.tick()


func test_pyramid_has_28_cubes() -> void:
	assert_int(TumbleEngine.cell_count()).is_equal(28)
	assert_int(TumbleEngine.cells().size()).is_equal(28)
	assert_bool(TumbleEngine.on_pyramid(Vector2i(6, 6))).is_true()
	assert_bool(TumbleEngine.on_pyramid(Vector2i(2, 3))).is_false()


func test_a_hop_paints_the_cube() -> void:
	var e := _engine()
	_hop(e, "dl")
	assert_that(e.hero["to"]).is_equal(Vector2i(1, 0))
	assert_bool(e.done(Vector2i(1, 0))).is_true()
	assert_int(e.score).is_equal(25)


func test_two_step_level_needs_two_visits() -> void:
	var e := _engine(1)
	_hop(e, "dr")
	assert_bool(e.done(Vector2i(1, 1))).is_false()
	_hop(e, "ul")
	_hop(e, "dr")
	assert_bool(e.done(Vector2i(1, 1))).is_true()


func test_undo_level_reverts_a_finished_cube() -> void:
	var e := _engine(2)
	_hop(e, "dr")
	assert_bool(e.done(Vector2i(1, 1))).is_true()
	_hop(e, "ul")
	_hop(e, "dr")
	assert_bool(e.done(Vector2i(1, 1))).is_false()


func test_hopping_off_the_edge_falls() -> void:
	var e := _engine()
	var died := []
	e.event.connect(func(k, d): if k == "die": died.append(d["how"]))
	_hop(e, "ur")
	for i in int(T.FALL_TIME / T.TICK) + 2:
		e.tick()
	assert_array(died).contains(["fall"])
	assert_int(e.lives).is_equal(2)


func test_disc_carries_back_to_the_top_and_lures_the_serpent() -> void:
	var e := _engine()
	var row: int = e.discs[0]["row"]
	# stand on the left edge of the disc's row, the serpent right behind
	e.hero["at"] = Vector2i(row, 0)
	e.hero["to"] = Vector2i(row, 0)
	e.enemies.append({"kind": "serpent", "to": Vector2i(row, 1), "from_cell": Vector2i(row, 1), "t": 1.0, "wait": 5.0})
	var lured := []
	e.event.connect(func(k, d): if k == "lure": lured.append(true))
	# (row, 0) -> ul -> (row - 1, -1): the disc on the left floats at its row, reached from the row below
	e.hero["at"] = Vector2i(row + 1, 0)
	e.hero["to"] = Vector2i(row + 1, 0)
	_hop(e, "ul")
	assert_int(e.phase).is_equal(T.Phase.RIDE)
	for i in int((T.RIDE_TIME + 0.5) / T.TICK):
		e.tick()
	assert_int(e.phase).is_equal(T.Phase.PLAY)
	assert_that(e.hero["to"]).is_equal(Vector2i(0, 0))
	assert_bool(lured.size() > 0).is_true()


func test_red_ball_kills_and_green_freezes() -> void:
	var e := _engine()
	e.enemies.append({"kind": "green", "to": Vector2i(1, 0), "from_cell": Vector2i(1, 0), "t": 1.0, "wait": 5.0})
	_hop(e, "dl")
	assert_float(e.frozen).is_greater(0.0)
	e.enemies.append({"kind": "red", "to": Vector2i(2, 0), "from_cell": Vector2i(2, 0), "t": 1.0, "wait": 5.0})
	_hop(e, "dl")
	assert_int(e.phase).is_equal(T.Phase.DYING)


func test_autopilot_clears_rounds() -> void:
	for lv in [0, 1, 2, 3]:
		var e := TumbleEngine.new(lv, 1, 9)
		var bot := TumbleBot.new()
		var deaths := 0
		e.event.connect(func(k, d): if k == "die": deaths += 1)
		for i in int(240.0 / T.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == T.Phase.CLEARED or e.phase == T.Phase.OVER:
				break
		prints("autopilot level", lv + 1, "phase", e.phase, "left", e.remaining(), "deaths", deaths, "time", snappedf(e.time, 0.1))
		assert_int(e.phase).is_equal(T.Phase.CLEARED)
		assert_int(deaths).is_less_equal(3)
