extends GdUnitTestSuite
## Relic Run: the level parses, the hero walks, jumps and climbs, cannot stand under a low roof, the pistol drops a
## skeleton, dynamite breaks cracked stone (and hurts the hero), spikes and the boulder kill, and the demo route
## reaches the exit.

const E = preload("res://games/relic/engine/relic_engine.gd")
const FILE := "res://games/relic/levels/temple.relic"


func _level() -> RelicLevel:
	return RelicLevel.parse_file(FileAccess.get_file_as_string(FILE))[0]


func _play() -> RelicEngine:
	var e := RelicEngine.new(_level(), 1)
	e.phase = E.Phase.PLAY
	e.level.trigger_col = -1  # the boulder stays put unless a test wants it
	return e


func _run(e: RelicEngine, seconds: float) -> void:
	for i in int(seconds / E.TICK):
		e.tick()


func test_the_level_parses() -> void:
	var lv := _level()
	assert_int(lv.w).is_equal(40)
	assert_int(lv.h).is_equal(24)
	assert_that(lv.start).is_equal(Vector2i(3, 9))
	assert_str(lv.at(15, 18)).is_equal("B")
	assert_int(lv.route.size()).is_greater(10)


func test_walk_and_jump() -> void:
	var e := _play()
	var x0: float = e.hero["pos"].x
	e.move_x = 1.0
	_run(e, 0.5)
	assert_float(e.hero["pos"].x).is_greater(x0 + 2.0)
	assert_str(e.hero["state"]).is_equal("ground")
	e.jump_pressed = true
	e.tick()
	_run(e, 0.2)
	assert_float(e.hero["pos"].y).is_less(9.5)


func test_a_low_roof_makes_the_hero_crawl() -> void:
	var e := _play()
	for en in e.enemies:
		en["alive"] = false
	e.hero["pos"] = Vector2(10.5, 22.0)
	e.move_x = -1.0
	_run(e, 1.0)
	# stopped by the roof at x = 9
	assert_float(e.hero["pos"].x).is_greater(10.0)
	e.down = true
	_run(e, 1.0)
	assert_float(e.hero["pos"].x).is_less(9.0)
	assert_str(e.hero["state"]).is_equal("crawl")


func test_the_pistol_and_dynamite() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(29.0, 22.0)
	e.hero["facing"] = -1
	e.fire_pressed = true
	_run(e, 0.6)
	var sk: Array = e.enemies.filter(func(en): return en["kind"] == "skeleton")
	assert_bool(sk[0]["alive"]).is_false()
	e.hero["pos"] = Vector2(16.5, 22.0)
	e.plant_pressed = true
	e.tick()
	e.move_x = 1.0
	_run(e, 0.7)
	e.move_x = 0.0
	_run(e, 2.0)
	assert_str(e.level.at(15, 21)).is_equal("B")  # the level itself is untouched
	assert_str(e.at(15, 21)).is_equal(".")
	assert_int(e.phase).is_equal(E.Phase.PLAY)


func test_spikes_and_the_boulder_kill() -> void:
	var e := _play()
	e.hero["pos"] = Vector2(23.0, 22.0)
	e.move_x = -1.0
	_run(e, 1.0)
	assert_int(e.phase).is_equal(E.Phase.DYING)
	var e2 := RelicEngine.new(_level(), 1)
	e2.phase = E.Phase.PLAY
	# stand still past the mark: the boulder runs the hero down
	e2.hero["pos"] = Vector2(8.0, 10.0)
	e2.boulder["rolling"] = true
	_run(e2, 2.0)
	assert_int(e2.phase).is_equal(E.Phase.DYING)


func test_every_demo_route_reaches_the_exit() -> void:
	for lv in RelicLevel.parse_file(FileAccess.get_file_as_string(FILE)):
		var e := RelicEngine.new(lv, 1)
		var bot := RelicBot.new()
		var deaths := []
		e.event.connect(func(k, d): if k == "die": deaths.append([d["how"], d["pos"]]))
		for i in int(90.0 / E.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("route", lv.name, "phase", e.phase, "deaths", deaths, "at", e.hero["pos"], "step", bot._step, "time", snappedf(e.time, 0.1))
		assert_int(e.phase).is_equal(E.Phase.CLEARED)
		assert_int(deaths.size()).is_equal(0)
