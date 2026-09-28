extends GdUnitTestSuite
## Pop Voyage: bouncing, splitting down the sizes, blocks, items, the clock, and the autopilot clearing every stage.

const P = preload("res://games/popvoyage/engine/pop_engine.gd")
const FILE := "res://games/popvoyage/stages/voyage.pop"


func _stages() -> Array[PopStage]:
	return PopStage.parse_file(FileAccess.get_file_as_string(FILE))


func _engine(i := 0) -> PopEngine:
	var e := PopEngine.new(_stages()[i])
	e.phase = P.Phase.PLAY
	return e


func test_stages_parse() -> void:
	var st := _stages()
	assert_int(st.size()).is_equal(8)
	assert_int(st[3].blocks.size()).is_equal(2)
	assert_bool(st[3].blocks[0]["breakable"]).is_true()


func test_balloons_bounce_to_their_height() -> void:
	var e := _engine()
	var top := 0.0
	for i in 60 * 8:
		e.tick()
		if e.phase != P.Phase.PLAY:
			break
		top = maxf(top, e.balls[0]["pos"].y) if i > 120 else top
	# the biggest bounces to about BOUNCE[3] above the floor (its lowest point touching it)
	assert_float(top - P.RADIUS[3]).is_between(P.BOUNCE[3] - 0.4, P.BOUNCE[3] + 0.4)


func test_wire_splits_a_balloon_down_to_nothing() -> void:
	var e := _engine()
	e.balls = [{"size": 1, "pos": Vector2(8, 3), "vel": Vector2.ZERO}]
	e.hero["x"] = 8.0
	e.fire_pressed = true
	for i in 30:
		e.tick()
	assert_int(e.balls.size()).is_equal(2)
	assert_int(e.balls[0]["size"]).is_equal(0)
	e.frozen = 99.0
	for b in e.balls:
		b["pos"] = Vector2(8, 3)
	e.fire_pressed = true
	for i in 30:
		e.tick()
	e.fire_pressed = true
	for i in 30:
		e.tick()
	assert_int(e.balls.size()).is_equal(0)
	assert_int(e.phase).is_equal(P.Phase.CLEARED)


func test_touching_a_balloon_costs_a_life_unless_shielded() -> void:
	var e := _engine()
	e.balls = [{"size": 2, "pos": Vector2(8, 0.8), "vel": Vector2.ZERO}]
	e.hero["x"] = 8.0
	e.shield = true
	e.tick()
	assert_bool(e.shield).is_false()
	assert_int(e.phase).is_equal(P.Phase.PLAY)
	e.balls = [{"size": 2, "pos": Vector2(8, 0.8), "vel": Vector2.ZERO}]
	e.tick()
	assert_int(e.phase).is_equal(P.Phase.DYING)
	assert_int(e.lives).is_equal(2)


func test_cracked_block_breaks_under_the_wire() -> void:
	var e := _engine(3)
	e.balls = [{"size": 0, "pos": Vector2(15, 9), "vel": Vector2.ZERO}]
	e.frozen = 99.0
	e.hero["x"] = 4.0
	e.fire_pressed = true
	for i in 40:
		e.tick()
	assert_int(e.blocks.size()).is_equal(1)


func test_charge_shatters_everything_to_the_smallest() -> void:
	var e := _engine(1)
	e._take("charge")
	assert_int(e.balls.size()).is_equal(8 + 4)
	for b in e.balls:
		assert_int(b["size"]).is_equal(0)


func test_clock_running_out_costs_a_life() -> void:
	var e := _engine()
	e.clock = 0.05
	for i in 10:
		e.tick()
	assert_int(e.phase).is_equal(P.Phase.DYING)


func test_autopilot_clears_every_stage() -> void:
	var st := _stages()
	for i in st.size():
		var e := PopEngine.new(st[i], 9)
		var bot := PopBot.new()
		var deaths := []
		e.event.connect(func(k, d): if k == "die": deaths.append([d["pos"].x, e.balls.map(func(b): return [b["size"], b["pos"].snapped(Vector2(0.1, 0.1))])]))
		for n in int(200.0 / P.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == P.Phase.CLEARED or e.phase == P.Phase.OVER:
				break
		prints("autopilot", st[i].name, "phase", e.phase, "balls", e.balls.size(), "deaths", deaths.size(), deaths.slice(0, 2), "time", snappedf(e.time, 0.1))
		assert_int(e.phase).is_equal(P.Phase.CLEARED)
		assert_int(deaths.size()).is_less_equal(4)
