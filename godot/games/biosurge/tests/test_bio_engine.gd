extends GdUnitTestSuite
## Biosurge: the cavern always leaves a way through, walls and enemy shots hurt, the gun widens with its level, the shop
## sells and refuses, and the autopilot flies a whole level and kills its boss.

const B = preload("res://games/biosurge/engine/bio_engine.gd")


func test_the_cavern_leaves_a_way_through() -> void:
	for lv in 5:
		var e := BioEngine.new(lv, {}, 3)
		for i in int(e.length):
			assert_float(e.right[i] - e.left[i]).is_greater_equal(5.0)
		for isl in e.islands:
			var i := int(isl.position.y)
			var gap := maxf(isl.position.x - e.left[i], e.right[i] - isl.end.x)
			assert_float(gap).is_greater(2.0)


func test_walls_sting() -> void:
	var e := BioEngine.new(0, {}, 3)
	e.phase = B.Phase.PLAY
	e.foes.clear()
	e.waves.clear()
	e.input = Vector2(-1, 0)
	for i in 120:
		e.tick()
	assert_float(e.energy).is_less(100.0)


func test_the_gun_widens() -> void:
	var e := BioEngine.new(0, {}, 3)
	e.phase = B.Phase.PLAY
	e.waves.clear()
	e.firing = true
	e.tick()
	var one := e.shots.size()
	e.shots.clear()
	e.loadout["gun"] = 5
	e._fire_t = 0.0
	e.tick()
	assert_int(e.shots.size()).is_greater(one)


func test_the_shop() -> void:
	var e := BioEngine.new(0, {"credits": 500}, 3)
	assert_bool(e.buy("side", 400)).is_true()
	assert_bool(e.loadout["side"]).is_true()
	assert_bool(e.buy("laser", 900)).is_false()
	assert_int(e.credits).is_equal(100)


func test_the_autopilot_beats_a_level() -> void:
	var beaten := 0
	for lv in 2:
		var e := BioEngine.new(lv, {"lives": 9, "loadout": {"gun": 3, "side": true, "rear": false, "homing": false, "laser": false, "drone": false, "speed": 1}}, 5 + lv)
		var bot := BioBot.new()
		var deaths := [0]
		e.event.connect(func(k, d): if k == "die": deaths[0] += 1)
		for n in 60 * 400:
			bot.drive(e)
			e.tick()
			if e.phase == B.Phase.CLEARED or e.phase == B.Phase.OVER:
				break
		prints("biosurge level", lv + 1, "phase", e.phase, "deaths", deaths[0], "score", e.score, "credits", e.credits, "time", snappedf(e.time, 0.1),
			"boss hp", e.boss.get("hp", -1))
		if e.phase == B.Phase.CLEARED:
			beaten += 1
	assert_int(beaten).is_greater_equal(1)
