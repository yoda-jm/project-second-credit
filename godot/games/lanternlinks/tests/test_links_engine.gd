extends GdUnitTestSuite
## Lantern Links: the course file, rolling and friction, banks, slopes, the cup (drop and lip-out), water, the
## stroke limit, honours, the windmill and the loop, and the CPU clearing every hole.

const H = preload("res://games/lanternlinks/engine/links_hole.gd")
const B = preload("res://games/lanternlinks/engine/links_ball.gd")
const P = preload("res://games/lanternlinks/engine/links_physics.gd")
const E = preload("res://games/lanternlinks/engine/links_engine.gd")
const COURSE := "res://games/lanternlinks/courses/lantern_garden.links"


func _course() -> Array[LinksHole]:
	return LinksHole.parse_course(FileAccess.get_file_as_string(COURSE))


func _hole(map: String, extra := "") -> LinksHole:
	var lines: Array[String] = ["hole = Test", "par = 3", "map:"]
	lines.append_array(map.split("\n"))
	lines.append("")
	if extra != "":
		lines.append_array(extra.split("\n"))
	return LinksHole.parse(lines)


func _roll(h: LinksHole, from: Vector2, vel: Vector2, max_t := 12.0) -> LinksBall:
	var b := LinksBall.new()
	b.place(from, h.height(from))
	b.vel = vel
	return P.simulate(h, b, 0.0, max_t)


const LANE := "##############\n#T..........O#\n#............#\n##############"


func test_the_course_has_nine_holes_par_27() -> void:
	var holes := _course()
	assert_int(holes.size()).is_equal(9)
	var par := 0
	for h in holes:
		par += h.par
		assert_bool(h.solid_at(h.tee)).override_failure_message(h.name + ": tee in a wall").is_false()
		assert_int(h.kind_at(h.cup)).override_failure_message(h.name + ": cup not on felt").is_equal(H.FELT)
	assert_int(par).is_equal(27)


func test_felt_slows_the_ball_to_a_stop() -> void:
	var h := _hole(LANE)
	var b := _roll(h, Vector2(1.25, 0.75), Vector2(1.5, 0))
	assert_bool(b.at_rest).is_true()
	# v² / 2a on felt: about 1.6 m for 1.5 m/s
	assert_float(b.pos.x - 1.25).is_between(1.2, 2.0)


func test_a_bank_bounces_the_ball_back() -> void:
	var h := _hole("########\n#......#\n#......#\n########")
	var b := LinksBall.new()
	b.place(Vector2(2.0, 0.75), 0.0)
	b.vel = Vector2(0, -2.0)
	var ev := []
	for i in 30:
		P.tick(h, b, i * P.TICK, ev)
	assert_float(b.vel.y).is_greater(0.5)
	assert_bool(ev.any(func(x): return x[0] == "bank")).is_true()


func test_a_ball_rolls_down_a_ramp() -> void:
	var lines: Array[String] = ["hole = Ramp", "par = 2", "map:", "#########", "#.......#", "#########", "height:",
		"000000000", "044///000", "000000000"]
	var h := LinksHole.parse(lines)
	assert_float(h.height(Vector2(1.25, 0.75))).is_equal_approx(0.4, 0.001)
	assert_float(h.height(Vector2(3.25, 0.75))).is_less(0.35)
	var b := _roll(h, Vector2(1.6, 0.75), Vector2.ZERO)
	assert_float(b.pos.x).is_greater(2.6)


func test_a_slow_ball_drops_and_a_fast_one_lips_out() -> void:
	var h := _hole(LANE)
	var slow := _roll(h, h.cup - Vector2(0.8, 0), Vector2(1.6, 0))
	assert_int(slow.mode).is_equal(B.Mode.SUNK)
	var fast := LinksBall.new()
	fast.place(h.cup - Vector2(0.3, 0), 0.0)
	fast.vel = Vector2(4.5, 0)
	var ev := []
	for i in 12:
		P.tick(h, fast, i * P.TICK, ev)
	assert_bool(ev.any(func(x): return x[0] == "lip")).is_true()


func test_water_costs_a_stroke_and_puts_the_ball_back() -> void:
	var h := _hole("#########\n#T..ww.O#\n#########")
	var e := LinksEngine.new([h] as Array[LinksHole], [{"name": "A", "cpu": false}] as Array[Dictionary])
	for i in 30:
		e.tick()
	e.skip()
	for i in 120:
		e.tick()
	assert_int(e.phase).is_equal(E.Phase.AIM)
	var from := e.ball.pos
	e.shoot(0.0, 0.5)
	for i in 400:
		e.tick()
		if e.phase == E.Phase.AIM:
			break
	assert_int(e.strokes).is_equal(2)
	assert_vector(e.ball.pos).is_equal_approx(from, Vector2(0.001, 0.001))


func test_the_stroke_limit_picks_the_ball_up() -> void:
	var h := _hole(LANE)
	var e := LinksEngine.new([h] as Array[LinksHole], [{"name": "A", "cpu": false}] as Array[Dictionary])
	for i in 30:
		e.tick()
	e.skip()
	for k in E.MAX_STROKES:
		for i in 200:
			e.tick()
			if e.phase == E.Phase.AIM:
				break
		e.shoot(PI, 0.05)
	for i in 400:
		e.tick()
	assert_int(e.players[0]["scores"][0]).is_equal(E.MAX_STROKES + 1)


func test_honours_the_best_score_tees_off_first() -> void:
	var holes := _course()
	var who: Array[Dictionary] = [{"name": "A", "cpu": false}, {"name": "B", "cpu": false}]
	var e := LinksEngine.new(holes, who)
	e.players[0]["scores"][0] = 4
	e.players[1]["scores"][0] = 2
	e._start_hole(1)
	assert_int(e.order[0]).is_equal(1)


func test_the_windmill_blocks_a_third_of_the_time() -> void:
	var g := {"period": 4.0}
	var blocked := 0
	for i in 400:
		if P.windmill_blocked(g, i * 0.01):
			blocked += 1
	assert_int(blocked).is_between(25 * 4, 45 * 4)


func test_the_loop_needs_speed() -> void:
	var holes := _course()
	var h: LinksHole
	for x in holes:
		if x.has_gadget("loop"):
			h = x
	var g: Dictionary = h.gadgets.filter(func(q): return q["type"] == "loop")[0]
	var start: Vector2 = g["pos"] - g["dir"] * 0.3
	var ok := LinksBall.new()
	ok.place(start, h.height(start))
	ok.vel = g["dir"] * 3.2
	var ev := []
	for i in 240:
		P.tick(h, ok, i * P.TICK, ev)
	assert_bool(ev.any(func(x): return x[0] == "loop_out")).is_true()
	var slow := LinksBall.new()
	slow.place(start, h.height(start))
	slow.vel = g["dir"] * 1.6
	ev.clear()
	for i in 240:
		P.tick(h, slow, i * P.TICK, ev)
	assert_bool(ev.any(func(x): return x[0] == "loop_back")).is_true()


## The perfect CPU sinks every hole within par (it plans with the game's own physics).
func test_the_cpu_clears_every_hole() -> void:
	var holes := _course()
	for h in holes:
		var ball := LinksBall.new()
		ball.place(h.tee, h.height(h.tee))
		var bot := LinksBot.new(h)
		var clock := 0.0
		var strokes := 0
		while strokes < h.par + 2:
			bot.plan(ball, clock)
			bot.think()
			strokes += 1
			var from := ball.pos
			ball.vel = Vector2.from_angle(bot.angle) * bot.power * P.MAX_SPEED
			ball.at_rest = false
			for i in 60 * 14:
				P.tick(h, ball, clock, null)
				clock += P.TICK
				if ball.mode != B.Mode.ROLL and ball.mode != B.Mode.AIR and ball.mode != B.Mode.LOOP and ball.mode != B.Mode.PIPE:
					break
				if ball.at_rest:
					break
			if ball.mode == B.Mode.SUNK:
				break
			if ball.mode == B.Mode.LOST:
				strokes += 1
				ball.place(from, h.height(from))
			clock += 1.0
		assert_int(ball.mode).override_failure_message("%s: not holed in %d" % [h.name, strokes]).is_equal(B.Mode.SUNK)
		assert_int(strokes).override_failure_message("%s: %d strokes" % [h.name, strokes]).is_less_equal(h.par)
