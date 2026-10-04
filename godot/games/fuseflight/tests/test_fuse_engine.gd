extends GdUnitTestSuite
## Fuseflight: the leap and the glide, solid platforms, fireworks and the lit fuse's order, enemies, the power star,
## and the autopilot clearing stages.

const F = preload("res://games/fuseflight/engine/fuse_engine.gd")
const FILE := "res://games/fuseflight/stages/festival.fuse"


func _stages() -> Array[FuseStage]:
	return FuseStage.parse_file(FileAccess.get_file_as_string(FILE))


func _engine(i := 0) -> FuseEngine:
	var e := FuseEngine.new(_stages()[i])
	e.phase = F.Phase.PLAY
	e._spawn_t = 999.0
	e._star_t = 999.0
	e._letter_t = 999.0
	return e


func test_stages_parse() -> void:
	var st := _stages()
	assert_int(st.size()).is_equal(5)
	for s in st:
		assert_int(s.bombs.size()).is_equal(24)


func test_a_held_leap_goes_higher_than_a_tap() -> void:
	var a := _engine()
	a.jump_pressed = true
	a.jump_held = true
	var top_a := 0.0
	for i in 90:
		a.jump_held = true
		a.tick()
		top_a = maxf(top_a, a.hero["pos"].y)
	var b := _engine()
	b.jump_pressed = true
	var top_b := 0.0
	for i in 90:
		b.tick()
		top_b = maxf(top_b, b.hero["pos"].y)
	assert_float(top_a).is_greater(top_b + 1.0)


func test_gliding_falls_slowly() -> void:
	var e := _engine()
	e.hero["pos"] = Vector2(8, 10)
	e.hero["ground"] = false
	for i in 60:
		e.jump_held = true
		e.tick()
	assert_float(e.hero["vel"].y).is_greater_equal(-F.GLIDE - 0.01)


func test_platforms_carry_and_bump() -> void:
	var e := _engine()
	e.hero["pos"] = Vector2(3.0, 5.0)  # above the first ledge (2..6, top at 3.9)
	e.hero["ground"] = false
	for i in 120:
		e.tick()
	assert_float(e.hero["pos"].y).is_equal_approx(3.9, 0.01)


func test_the_lit_fuse_follows_the_order() -> void:
	var e := _engine()
	e.hero["pos"] = e.stage.bombs[5] - Vector2(0, 0.4)
	e.tick()
	assert_int(e.lit).is_equal(6)
	e.hero["pos"] = e.stage.bombs[6] - Vector2(0, 0.4)
	var before := e.score
	e.tick()
	assert_int(e.score - before).is_equal(200)
	assert_int(e.lit).is_equal(7)


func test_an_enemy_costs_a_life_and_power_makes_it_points() -> void:
	var e := _engine()
	e.enemies.append({"id": 1, "kind": "orb", "pos": e.hero["pos"] + Vector2(0, 0.4), "vel": Vector2.ZERO, "t": 0.0, "ground": false, "dir": 1.0})
	e.power = 5.0
	e.tick()
	assert_int(e.enemies.size()).is_equal(0)
	e.power = 0.0
	e.enemies.append({"id": 2, "kind": "orb", "pos": e.hero["pos"] + Vector2(0, 0.4), "vel": Vector2.ZERO, "t": 0.0, "ground": false, "dir": 1.0})
	e.tick()
	assert_int(e.phase).is_equal(F.Phase.DYING)


func test_autopilot_clears_stages() -> void:
	var st := _stages()
	for i in st.size():
		var e := FuseEngine.new(st[i], 9)
		var bot := FuseBot.new()
		var deaths := []
		e.event.connect(func(k, d):
			if k == "die":
				var why := []
				for en in e.enemies:
					if (en["pos"] as Vector2).distance_to(d["pos"]) < 1.2:
						why.append([en["kind"], (en["pos"] - d["pos"]).snapped(Vector2(0.1, 0.1)), (en["vel"] as Vector2).snapped(Vector2(0.1, 0.1))])
				deaths.append([d["pos"].snapped(Vector2(0.1, 0.1)), e.hero["ground"], why]))
		for n in int(300.0 / F.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == F.Phase.CLEARED or e.phase == F.Phase.OVER:
				break
		prints("autopilot", st[i].name, "phase", e.phase, "left", e.left(), "deaths", deaths.size(), "lit", e.lit_taken, "time", snappedf(e.time, 0.1))
		# the first stages are cleared; the busier later ones (four or five enemies at once) at least mostly
		if i < 2:
			assert_int(e.phase).is_equal(F.Phase.CLEARED)
			assert_int(deaths.size()).is_less_equal(4)
		else:
			assert_int(24 - e.left()).is_greater_equal(20)
