extends GdUnitTestSuite
## Nova Wardens: the march (a ripple that speeds up as the fleet thins), drops at the walls, one shot at a time,
## scoring by row, shields eroding, at most three bombs, the mystery ship's 23rd shot, landing, and the autopilot.

const N = preload("res://games/novawardens/engine/nova_engine.gd")


func _play() -> NovaEngine:
	var e := NovaEngine.new()
	e.phase = N.Phase.PLAY
	return e


func test_the_fleet_steps_after_every_invader_moved() -> void:
	var e := _play()
	e.bomb_t = 999.0
	var x0 := e.origin.x
	for i in N.COLS * N.ROWS + 1:   # every invader moves once, then the step completes
		e._march()
	assert_float(e.origin.x).is_equal(x0 + N.STEP_X)


func test_fewer_invaders_march_faster() -> void:
	var e := _play()
	for i in N.COLS * N.ROWS - 1:
		e.alive[i] = 0
	var last := N.COLS * N.ROWS - 1
	var x0 := e.invader_pos(last).x
	for i in 10:
		e._march()
	# alone, it moves every tick
	assert_float(e.invader_pos(last).x - x0).is_equal(10.0 * N.STEP_X)


func test_the_fleet_drops_and_turns_at_a_wall() -> void:
	var e := _play()
	var y0 := e.origin.y
	for i in 5000:
		e._march()
		if e.dir < 0:
			break
	assert_int(e.dir).is_equal(-1)
	assert_float(e.origin.y).is_equal(y0 + N.DROP_Y)


func test_one_shot_at_a_time_and_points_by_row() -> void:
	var e := _play()
	e.bomb_t = 999.0
	e.ufo_t = 999.0
	var i := 4 * N.COLS + 5   # an octopus, bottom row, middle
	var target := e.invader_pos(i) + Vector2(6, 4)
	e.cannon_x = target.x - N.CANNON_W * 0.5
	e.fire_pressed = true
	e.tick()
	assert_bool(e.shot.is_empty()).is_false()
	var y: float = e.shot["pos"].y
	e.fire_pressed = true
	e.tick()
	assert_float(e.shot["pos"].y).is_less(y)   # still the first shot: a second press does nothing
	for k in 90:
		e.tick()
	assert_int(e.alive[i]).is_equal(0)
	assert_int(e.score).is_equal(10)


func test_shields_erode() -> void:
	var e := _play()
	var p := Vector2(N.shield_x(0) + 10, N.SHIELD_Y + 8)
	var before := Array(e.shields[0]).count(1)
	e._hit_shield(p, 1)
	assert_int(Array(e.shields[0]).count(1)).is_less(before)


func test_at_most_three_bombs() -> void:
	var e := _play()
	e.cannon_x = 16.0
	for i in 60 * 20:
		e.bomb_t = 0.0
		e._bombs()
		assert_int(e.bombs.size()).is_less_equal(3)
		if e.phase != N.Phase.PLAY:
			e.phase = N.Phase.PLAY


func test_the_23rd_shot_scores_300_on_the_mystery_ship() -> void:
	var e := _play()
	e.shots_fired = 23
	assert_int(e._ufo_points()).is_equal(300)
	e.shots_fired = 38
	assert_int(e._ufo_points()).is_equal(300)


func test_landing_ends_the_game() -> void:
	var e := _play()
	e.lives = 3
	e.origin.y = N.CANNON_Y - (N.ROWS - 1) * N.GAP_Y - N.INV_H   # the bottom row level with the cannon
	for i in N.COLS * N.ROWS + 1:
		e._march()
	assert_bool(e.landed).is_true()
	for i in 200:
		e.tick()
	assert_int(e.phase).is_equal(N.Phase.OVER)


func test_autopilot_clears_the_first_waves() -> void:
	var e := NovaEngine.new(0, 9)
	var bot := NovaBot.new()
	var deaths := []
	var waves := []
	e.event.connect(func(k, d):
		if k == "die": deaths.append(d)
		if k == "cleared": waves.append(1))
	for i in int(400.0 / N.TICK):
		bot.drive(e)
		e.tick()
		if waves.size() >= 2 or e.phase == N.Phase.OVER:
			break
	prints("autopilot waves", waves.size(), "deaths", deaths.size(), "score", e.score, "time", snappedf(e.time, 0.1), "phase", e.phase)
	assert_int(waves.size()).is_greater_equal(2)
	assert_int(deaths.size()).is_less_equal(3)
