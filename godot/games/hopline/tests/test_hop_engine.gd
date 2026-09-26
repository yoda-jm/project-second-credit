extends GdUnitTestSuite
## Hopline: hops move a cell, cars squash, the canal drowns unless something carries the frog (which rides it),
## the bays take one frog each, the clock runs out, and the autopilot fills all five bays.

const E = preload("res://games/hopline/engine/hop_engine.gd")


func _play() -> HopEngine:
	var e := HopEngine.new(0, 1)
	e.phase = E.Phase.PLAY
	return e


func _run(e: HopEngine, seconds: float, bot: HopBot = null) -> void:
	for i in int(seconds / E.TICK):
		if bot:
			bot.drive(e)
		e.tick()


func test_a_hop_moves_one_cell() -> void:
	var e := _play()
	e.want = "up"
	e.tick()
	assert_int(e.row).is_equal(11)
	assert_float(e.hop_t).is_greater(0.0)


func test_a_car_squashes_the_frog() -> void:
	var e := _play()
	e.row = 11
	e.x = 7.0
	var o: Dictionary = e.lanes[11]["objs"][0]
	# put a car right on the frog
	o["x0"] = fposmod(7.0 - 0.5 + E.SPAN * 0.5 - e.lanes[11]["dir"] * e.lanes[11]["speed"] * e.time, E.W + E.SPAN)
	e.tick()
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_the_canal_drowns_and_logs_carry() -> void:
	var e := _play()
	e.row = 4
	e.x = 7.0
	var o: Dictionary = e.lanes[4]["objs"][0]
	var ox := e.obj_x(4, o, e.time)
	o["x0"] = fposmod(o["x0"] + (7.0 - 1.5) - ox, E.W + E.SPAN)
	var x0 := e.x
	_run(e, 0.5)
	assert_int(e.phase).is_equal(E.Phase.PLAY)
	assert_float(e.x).is_greater(x0 + 0.2)
	e.x = -5.0 + 0.0
	e.row = 3
	e.x = 7.0
	for oo in e.lanes[3]["objs"]:
		oo["x0"] = 100.0
	_run(e, 0.1)
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_a_bay_takes_one_frog() -> void:
	var e := _play()
	e.row = 1
	e.x = 4.0
	e.croc_bay = -1
	for o in e.lanes[1]["objs"]:
		o["x0"] = 0.0
	e.lanes[1]["speed"] = 0.0
	e.lanes[1]["objs"][0]["x0"] = E.SPAN * 0.5 + 2.0
	e.lanes[1]["objs"][0]["len"] = 6.0
	e.want = "up"
	_run(e, 0.3)
	assert_bool(e.filled[1]).is_true()
	assert_int(e.row).is_equal(E.START_ROW)


func test_the_clock_runs_out() -> void:
	var e := _play()
	e.life_t = 0.1
	_run(e, 0.2)
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_the_autopilot_fills_the_bays() -> void:
	for s in [0, 2]:
		var e := HopEngine.new(s, 3 + s, 9)
		var bot := HopBot.new(s)
		var deaths := []
		e.event.connect(func(k, d): if k == "die": deaths.append(d["how"]))
		for i in int(180.0 / E.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("stage", s, "filled", e.filled, "deaths", deaths, "time", snappedf(e.time, 0.1))
		assert_int(e.phase).is_equal(E.Phase.CLEARED)
