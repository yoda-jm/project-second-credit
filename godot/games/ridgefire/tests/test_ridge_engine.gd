extends GdUnitTestSuite
## Ridgefire: the ground carved and heaped without overhangs, a shot's flight in the wind, blasts hurting by distance,
## tanks falling, shields, the shop, turns passing, and CPUs playing whole games (they hit, rounds end, money flows).

const R = preload("res://games/ridgefire/engine/ridge_engine.gd")


func test_a_blast_carves_and_the_earth_above_falls() -> void:
	var e := RidgeEngine.new(2, [true, true], 3)
	for i in R.N:
		e.heights[i] = 20.0
	e._carve(Vector2(48.0, 15.0), 3.0)
	# the disc lies under the surface: the earth above drops by its height at the centre
	assert_float(e.ground(48.0)).is_equal_approx(14.0, 0.05)
	assert_float(e.ground(40.0)).is_equal_approx(20.0, 0.01)
	e._carve(Vector2(30.0, 20.0), 3.0)
	assert_float(e.ground(30.0)).is_equal_approx(17.0, 0.05)


func test_a_dirt_ball_heaps_earth() -> void:
	var e := RidgeEngine.new(2, [true, true], 3)
	for i in R.N:
		e.heights[i] = 10.0
	e._heap(Vector2(48.0, 11.0), 3.0)
	assert_float(e.ground(48.0)).is_equal_approx(14.0, 0.05)


func test_wind_bends_the_flight() -> void:
	var e := RidgeEngine.new(2, [true, true], 3)
	for i in R.N:
		e.heights[i] = 5.0
	var land := func(w: float) -> float:
		e.wind = w
		var s := {"pos": Vector2(20, 10), "vel": Vector2(15, 15), "t": 0.0}
		while e.step_shot(s, false) == "":
			pass
		return s["pos"].x
	assert_float(land.call(5.0)).is_greater(land.call(0.0))
	assert_float(land.call(-5.0)).is_less(land.call(0.0))


func test_blasts_hurt_by_distance_and_shields_soak() -> void:
	var e := RidgeEngine.new(2, [true, true], 3)
	var p := e.players[0]
	var q := e.players[1]
	e._hurt(Vector2(p["x"], p["y"] + 0.7), 4.5, 50.0, 1)
	assert_float(p["hp"]).is_less_equal(50.0)
	q["shield"] = 60.0
	e._hurt(Vector2(q["x"], q["y"] + 0.7), 4.5, 50.0, 0)
	assert_float(q["hp"]).is_equal(100.0)
	assert_float(q["shield"]).is_less(60.0)


func test_a_tank_falls_when_its_ground_goes() -> void:
	var e := RidgeEngine.new(2, [true, true], 3)
	var p := e.players[0]
	var x: float = p["x"]
	var falls := []
	e.event.connect(func(k, d): if k == "fall": falls.append(d["drop"]))
	for i in range(R._col(x - 3.0), R._col(x + 3.0)):
		e.heights[i] -= 6.0
	e.phase = R.Phase.SETTLE
	for i in 200:
		e.tick()
	assert_array(falls).is_not_empty()
	assert_float(p["hp"]).is_less(100.0)
	assert_float(p["y"]).is_equal_approx(e.ground(x), 0.05)


func test_the_shop_sells_packs() -> void:
	var e := RidgeEngine.new(2, [true, true], 3)
	e.players[0]["money"] = 1000
	assert_bool(e.buy(0, "heavy")).is_true()
	assert_int(e.players[0]["ammo"]["heavy"]).is_equal(3)
	assert_int(e.players[0]["money"]).is_equal(600)
	assert_bool(e.buy(0, "nuke")).is_false()
	assert_bool(e.buy(0, "shield")).is_false()


func test_the_cpu_lands_near_its_target() -> void:
	var near := 0
	for sd in 6:
		var e := RidgeEngine.new(2, [true, true], 10 + sd)
		e.wind = 0.0
		var bot := RidgeBot.new(sd)
		bot.skill = 0.0
		bot.plan(e)
		var me := e.current()
		var other := e.players[1 - e.turn]
		me["angle"] = bot.angle
		me["power"] = bot.power
		e.fire()
		var s: Dictionary = e.shots[0]
		var t := 0
		while t < 900 and e.step_shot(s) == "":
			t += 1
		if (s["pos"] as Vector2).distance_to(Vector2(other["x"], other["y"])) < 4.0:
			near += 1
	assert_int(near).is_greater_equal(5)


## Whole games between CPUs: every round ends, someone wins it, and the game finishes.
func test_cpus_play_a_whole_game() -> void:
	for sd in 2:
		var e := RidgeEngine.new(3 + sd, [], 40 + sd, 3)
		var bots := []
		for i in e.players.size():
			bots.append(RidgeBot.new(i + sd * 7))
		var ends := []
		e.event.connect(func(k, d): if k == "round_end": ends.append(d["winner"]))
		var guard := 0
		while e.phase != R.Phase.OVER and guard < 60 * 60 * 30:
			guard += 1
			if e.phase == R.Phase.AIM:
				var b: RidgeBot = bots[e.turn]
				b.plan(e)
				var me := e.current()
				me["angle"] = b.angle
				me["power"] = b.power
				if me["ammo"].has(b.weapon):
					me["weapon"] = b.weapon
				e.fire()
			elif e.phase == R.Phase.ROUND_END:
				for i in e.players.size():
					RidgeBot.shop(e, i)
				e.next_round()
			else:
				e.tick()
		prints("ridgefire game", sd, "rounds", ends, "money", e.players.map(func(p): return p["money"]), "ticks", guard)
		assert_int(e.phase).is_equal(R.Phase.OVER)
		assert_int(ends.size()).is_equal(3)
