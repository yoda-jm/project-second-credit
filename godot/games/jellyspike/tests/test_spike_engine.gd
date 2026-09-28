extends GdUnitTestSuite
## Jelly Spike: the serve, touches and the three-touch rule, the ball on the floor, the net, scoring to 15 by two,
## and two CPU players keeping rallies going.

const S = preload("res://games/jellyspike/engine/spike_engine.gd")


func test_serve_waits_for_the_server() -> void:
	var e := SpikeEngine.new(0)
	for i in 120:
		e.tick()
	assert_int(e.phase).is_equal(S.Phase.SERVE)
	assert_bool(e.ball["hanging"]).is_true()


func test_a_jump_reaches_the_serve() -> void:
	var e := SpikeEngine.new(0)
	var touched := []
	e.event.connect(func(k, d): if k == "touch": touched.append(d))
	for i in 60:
		e.jump[0] = true
		e.tick()
	assert_int(touched.size()).is_equal(1)
	assert_int(e.phase).is_equal(S.Phase.RALLY)


func test_ball_on_the_floor_scores_for_the_other_side() -> void:
	var e := SpikeEngine.new(0)
	e.phase = S.Phase.RALLY
	e.ball = {"pos": Vector2(4, 0.38), "vel": Vector2(0, -5), "hanging": false}
	e.tick()
	assert_array(e.score).is_equal([0, 1])
	assert_int(e.server).is_equal(1)


func test_four_touches_is_a_fault() -> void:
	var e := SpikeEngine.new(0)
	e.phase = S.Phase.RALLY
	for i in 4:
		e.blobs[0]["cool"] = 0.0
		e.ball = {"pos": e.blobs[0]["pos"] + Vector2(0, 0.9), "vel": Vector2(0, -2), "hanging": false}
		e._touch()
	assert_array(e.score).is_equal([0, 1])


func test_net_stops_a_low_ball() -> void:
	var e := SpikeEngine.new(0)
	e.phase = S.Phase.RALLY
	e.ball = {"pos": Vector2(7.4, 1.2), "vel": Vector2(6, 0), "hanging": false}
	for i in 20:
		e._move_ball()
	assert_float(e.ball["pos"].x).is_less(S.NET_X)


func test_match_is_won_by_two() -> void:
	var e := SpikeEngine.new(0)
	e.score = [14, 14]
	e._point(0, "test")
	assert_int(e.phase).is_not_equal(S.Phase.OVER)
	e._point(0, "test")
	assert_int(e.phase).is_equal(S.Phase.OVER)
	assert_int(e.winner).is_equal(0)


func test_cpu_players_rally_and_finish_a_match() -> void:
	var e := SpikeEngine.new(0, 3)
	var a := SpikeBot.new(0, 0.85, 1)
	var b := SpikeBot.new(1, 0.5, 2)
	var touches := []
	var points := []
	e.event.connect(func(k, d):
		if k == "touch": touches.append(d)
		if k == "point": points.append(d))
	for i in int(900.0 / S.TICK):
		a.drive(e)
		b.drive(e)
		e.tick()
		if e.phase == S.Phase.OVER:
			break
	prints("match", e.score, "touches", touches.size(), "points", points.size(), "time", snappedf(e.time, 0.1),
		"why", points.map(func(p): return p["why"]).count("touches"))
	assert_int(e.phase).is_equal(S.Phase.OVER)
	# rallies: well over one touch per point on average
	assert_float(float(touches.size()) / points.size()).is_greater(2.5)


func test_power_spike_needs_a_full_meter_and_fires_harder() -> void:
	var e := SpikeEngine.new(0)
	e.phase = S.Phase.RALLY
	e.power_pressed[0] = true
	e._move_blobs()
	assert_bool(e.armed[0]).is_false()   # the meter is empty
	e.power[0] = 1.0
	e.power_pressed[0] = true
	e._move_blobs()
	assert_bool(e.armed[0]).is_true()
	e.blobs[0]["vel"] = Vector2(5.6, 8.0)
	e.ball = {"pos": e.blobs[0]["pos"] + Vector2(0.4, 0.85), "vel": Vector2(-6, -8), "hanging": false, "fire": false}
	e._touch()
	assert_float(e.ball["vel"].length()).is_greater(S.MAX_BALL)
	assert_bool(e.ball["fire"]).is_true()
	assert_bool(e.armed[0]).is_false()
	assert_float(e.power[0]).is_equal(0.0)
