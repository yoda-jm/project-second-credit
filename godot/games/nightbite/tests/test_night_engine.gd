extends GdUnitTestSuite
## Nightbite: mazes, lanes and turns, pellets and power orbs, the chain of eaten spirits, catching, and the
## autopilot clearing a stage.

const E = preload("res://games/nightbite/engine/night_engine.gd")
const FILE := "res://games/nightbite/mazes/night.maze"


func _maze(i := 0) -> NightMaze:
	return NightMaze.parse_file(FileAccess.get_file_as_string(FILE))[i]


func _run(e: NightEngine, seconds: float, bot: NightBot = null) -> void:
	for i in int(seconds / E.TICK):
		if bot:
			bot.drive(e)
		e.tick()


func test_mazes_parse() -> void:
	var ms := NightMaze.parse_file(FileAccess.get_file_as_string(FILE))
	assert_int(ms.size()).is_equal(2)
	for m in ms:
		assert_int(m.w).is_equal(21)
		assert_int(m.powers.size()).is_equal(4)
		assert_int(m.spirits.size()).is_equal(4)
		assert_bool(m.bonus.x >= 0).is_true()


func test_the_hero_runs_and_eats() -> void:
	var e := NightEngine.new(_maze(), 0, 1)
	for s in e.spirits:
		s["state"] = "home"
		s["release"] = 999.0
	_run(e, E.READY_TIME + 0.1)
	e.want = Vector2i(-1, 0)
	var eaten := []
	e.event.connect(func(k, _d): if k == "pellet": eaten.append(1))
	_run(e, 1.0)
	assert_int(eaten.size()).is_greater(3)


func test_a_power_orb_frightens_and_the_chain_doubles() -> void:
	var e := NightEngine.new(_maze(), 0, 1)
	e.phase = E.Phase.PLAY
	var p: Vector2i = e.powers.keys()[0]
	e.hero["pos"] = Vector2(p) + Vector2(0.5, 0.5)
	e._eat()
	assert_bool(e.fright > 0.0).is_true()
	for s in e.spirits:
		s["state"] = "out"
		s["scared"] = true
	var pts := []
	e.event.connect(func(k, d): if k == "eat_spirit": pts.append(d["points"]))
	for i in 3:
		e.spirits[i]["pos"] = e.hero["pos"]
		e._touch()
	assert_array(pts).is_equal([200, 400, 800])
	assert_str(e.spirits[0]["state"]).is_equal("eyes")


func test_a_spirit_catches_the_hero() -> void:
	var e := NightEngine.new(_maze(), 0, 1)
	e.phase = E.Phase.PLAY
	e.spirits[0]["pos"] = e.hero["pos"]
	e._touch()
	assert_int(e.phase).is_equal(E.Phase.DYING)
	assert_int(e.lives).is_equal(2)


func test_eyes_go_home_and_come_back_out() -> void:
	var e := NightEngine.new(_maze(), 0, 1)
	e.phase = E.Phase.PLAY
	var s := e.spirits[0]
	s["state"] = "eyes"
	s["pos"] = Vector2(1.5, 1.5)
	var home := []
	e.event.connect(func(k, _d): if k == "spirit_home": home.append(1))
	for i in 60 * 12:
		e._move_spirit(s)
		e.time += E.TICK
	assert_int(home.size()).is_equal(1)


func test_the_autopilot_clears_a_stage() -> void:
	var cleared := false
	for seed in [1, 2, 3]:
		for mi in 2:
			var e := NightEngine.new(_maze(mi), 0, seed, 5)
			var bot := NightBot.new(seed)
			for n in 60 * 240:
				bot.drive(e)
				e.tick()
				if e.phase == E.Phase.DYING and e.phase_t <= 0.0:
					if e.lives <= 0:
						break
					e.respawn()
				if e.phase == E.Phase.CLEARED:
					cleared = true
					break
			if cleared:
				break
		if cleared:
			break
	assert_bool(cleared).is_true()
