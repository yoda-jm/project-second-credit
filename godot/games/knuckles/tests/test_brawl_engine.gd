extends GdUnitTestSuite
## Neon Knuckles: moves, grabs, weapons, waves and scrolling.

const B = preload("res://games/knuckles/engine/brawl_engine.gd")


func _level(text := "") -> BrawlLevel:
	if text == "":
		text = "[stage]\nname=Test\nlength=60\n"
	return BrawlLevel.parse_file(text)[0]


func _run(e: BrawlEngine, seconds: float, dir := Vector2.ZERO, attack_every := 0) -> void:
	for i in int(seconds / B.TICK):
		e.set_input(0, dir, attack_every > 0 and i % attack_every == 0, false)
		e.tick()


func _enemy(e: BrawlEngine, kind: String, x: float, z := 0.0) -> Dictionary:
	var f := e._fighter(kind, Vector3(x, 0, z))
	e.fighters.append(f)
	return f


func test_stages_parse() -> void:
	var st := BrawlLevel.parse_file(FileAccess.get_file_as_string("res://games/knuckles/stages/downtown.brawl"))
	assert_int(st.size()).is_equal(3)
	for s in st:
		assert_bool(s.waves.size() >= 4).is_true()
		assert_str(s.waves.back()["enemies"][0]["kind"]).is_equal("boss")


func test_three_hit_combo_ends_in_a_knockdown() -> void:
	var e := BrawlEngine.new(_level(), 1, 1)
	var p := e.players()[0]
	var t := _enemy(e, "thug", p["pos"].x + 0.8, p["pos"].z)
	t["think"] = 99.0
	for i in 3:
		e.set_input(0, Vector2.ZERO, true, false)
		e.tick()
		_run(e, 0.34)
	assert_int(t["state"]).is_equal(B.S.DOWN)
	assert_int(t["hp"]).is_equal(40 - 6 - 8 - 14)


func test_attacks_miss_outside_the_depth_band() -> void:
	var e := BrawlEngine.new(_level(), 1, 1)
	var p := e.players()[0]
	var t := _enemy(e, "thug", p["pos"].x + 0.8, p["pos"].z + 1.0)
	t["think"] = 99.0
	e.set_input(0, Vector2.ZERO, true, false)
	e.tick()
	_run(e, 0.4)
	assert_int(t["hp"]).is_equal(40)


func test_grab_knees_and_throw() -> void:
	var e := BrawlEngine.new(_level(), 1, 1)
	var p := e.players()[0]
	var t := _enemy(e, "bruiser", p["pos"].x + 0.6, p["pos"].z)
	t["think"] = 99.0
	t["state"] = B.S.HITSTUN
	t["t"] = 1.0
	e.set_input(0, Vector2(1, 0), true, false)  # walking into a staggered enemy grabs
	e.tick()
	assert_int(p["state"]).is_equal(B.S.GRABBING)
	var events := []
	e.event.connect(func(k, _d): events.append(k))
	for i in 3:
		e.set_input(0, Vector2.ZERO, true, false)
		e.tick()
		_run(e, 0.35)
	_run(e, 1.0)
	assert_array(events).contains(["throw"])
	assert_bool(t["hp"] < 110 - 27).is_true()


func test_jump_kick_knocks_down() -> void:
	var e := BrawlEngine.new(_level(), 1, 1)
	var p := e.players()[0]
	var t := _enemy(e, "thug", p["pos"].x + 1.6, p["pos"].z)
	t["think"] = 99.0
	e.set_input(0, Vector2(1, 0), false, true)
	e.tick()
	e.set_input(0, Vector2(1, 0), true, false)
	e.tick()
	_run(e, 0.8, Vector2(1, 0))
	assert_bool(t["state"] == B.S.DOWN or t["hp"] < 40).is_true()


func test_bat_pickup_hits_harder() -> void:
	var e := BrawlEngine.new(_level("[stage]\nlength=60\nitem=bat, 2.3, -0.6\n"), 1, 1)
	var p := e.players()[0]
	p["pos"] = Vector3(2.3, 0, -0.6)
	e.set_input(0, Vector2.ZERO, false, false, true)
	e.tick()
	assert_str(p["weapon"]).is_equal("bat")
	var t := _enemy(e, "thug", p["pos"].x + 1.2, p["pos"].z)
	t["think"] = 99.0
	e.set_input(0, Vector2.ZERO, true, false)
	e.tick()
	_run(e, 0.6)
	assert_int(t["hp"]).is_equal(20)


func test_waves_lock_the_screen_until_cleared() -> void:
	var e := BrawlEngine.new(_level("[stage]\nlength=60\nwave=10: thug\nwave=40: thug\n"), 1, 1)
	_run(e, 6.0, Vector2(1, 0))
	assert_int(e.enemies().size()).is_equal(1)
	var p := e.players()[0]
	_run(e, 4.0, Vector2(1, 0))
	assert_float(p["pos"].x).is_less(10.0 + e.view_width * 0.5)  # can't walk off the locked screen
	for en in e.enemies():
		en["hp"] = 0
		e._knock_down(en)
	_run(e, 2.0)
	assert_int(e.wave).is_equal(1)


func test_enemies_come_and_fight() -> void:
	var e := BrawlEngine.new(_level(), 1, 3)
	var p := e.players()[0]
	_enemy(e, "thug", p["pos"].x + 6.0, 1.5)
	_run(e, 8.0)
	assert_int(p["hp"]).is_less(100)


func test_lives_then_game_over() -> void:
	var e := BrawlEngine.new(_level(), 1, 1)
	var p := e.players()[0]
	for i in B.LIVES:
		p["hp"] = 0
		e._knock_down(p)
		_run(e, 3.0)
	assert_int(e.phase).is_equal(B.Phase.GAME_OVER)


func test_same_seed_and_inputs_replay_identically() -> void:
	var st := BrawlLevel.parse_file(FileAccess.get_file_as_string("res://games/knuckles/stages/downtown.brawl"))
	var out := []
	for run in 2:
		var s2 := BrawlLevel.parse_file(FileAccess.get_file_as_string("res://games/knuckles/stages/downtown.brawl"))[0]
		var e := BrawlEngine.new(s2, 2, 5)
		for i in 3000:
			e.set_input(0, Vector2(1 if (i / 100) % 3 else 0, 0), i % 13 == 0, i % 97 == 0)
			e.set_input(1, Vector2(1, 0.3), i % 17 == 0, false)
			e.tick()
		out.append([e.score, e.wave, e.fighters.size(), e.players()[0]["pos"]])
	assert_array(out[0]).is_equal(out[1])
