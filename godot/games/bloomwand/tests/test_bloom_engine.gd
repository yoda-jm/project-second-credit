extends GdUnitTestSuite
## Bloomwand: the levels load, a fairy walks and stands, the wand catches a creature in reach and slamming bursts it,
## a magic ladder takes her up a floor, flowers are picked, and the autopilot clears levels.

const B = preload("res://games/bloomwand/engine/bloom_engine.gd")
const FILE := "res://games/bloomwand/levels/garden.bloom"


func _levels() -> Array[BloomLevel]:
	return BloomLevel.parse_file(FileAccess.get_file_as_string(FILE))


func _engine(i := 0) -> BloomEngine:
	var e := BloomEngine.new(_levels()[i], [{}], 3)
	e.phase = B.Phase.PLAY
	return e


func test_levels_load() -> void:
	var ls := _levels()
	assert_int(ls.size()).is_equal(6)
	for l in ls:
		assert_int(l.rows.size()).is_equal(15)


func test_a_fairy_stands_and_walks() -> void:
	var e := _engine()
	e.foes.clear()
	e.foes.append({"id": 99, "kind": "g", "pos": Vector2(0.5, 14.0), "vy": 0.0, "dir": 1, "hp": 3, "held_by": -1, "stun": 0.0, "climb": 0, "climb_t": 9.0, "dead": false})
	var f := e.fairies[0]
	var y0: float = f["pos"].y
	f["move"] = 1
	for i in 30:
		e.tick()
	assert_float(f["pos"].y).is_equal(y0)
	assert_float(f["pos"].x).is_greater(e.fairies[0]["start"].x)


func test_the_wand_catches_and_slams() -> void:
	var e := _engine()
	var f := e.fairies[0]
	e.foes.clear()
	var at: Vector2 = f["pos"] + Vector2(2.0, 0)
	e.foes.append({"id": 7, "kind": "g", "pos": at, "vy": 0.0, "dir": 1, "hp": 3, "held_by": -1, "stun": 0.0, "climb": 0, "climb_t": 9.0, "dead": false})
	f["face"] = 1
	f["cast_pressed"] = true
	f["cast_held"] = true
	var pops := []
	e.event.connect(func(k, d): if k == "pop": pops.append(d["id"]))
	for i in 120:
		e.tick()
	assert_array(pops).contains([7])


func test_a_magic_ladder_takes_her_up() -> void:
	var e := _engine()
	var f := e.fairies[0]
	var y0: float = f["pos"].y
	e.foes.clear()
	e.foes.append({"id": 99, "kind": "g", "pos": Vector2(0.5, 14.0), "vy": 0.0, "dir": 1, "hp": 3, "held_by": -1, "stun": 0.0, "climb": 0, "climb_t": 9.0, "dead": false})
	f["ladder_pressed"] = true
	e.tick()
	assert_array(e.magic).is_not_empty()
	for i in 120:
		f["climb_in"] = 1
		e.tick()
	assert_float(f["pos"].y).is_greater(y0 + 1.5)


func test_the_autopilot_clears_levels() -> void:
	var cleared := 0
	var ls := _levels()
	for i in ls.size():
		var e := BloomEngine.new(ls[i], [{"lives": 9}], 7 + i)
		var bot := BloomBot.new(0)
		var deaths := [0]
		e.event.connect(func(k, d): if k == "die": deaths[0] += 1)
		for n in 60 * 180:
			bot.drive(e)
			e.tick()
			if e.phase == B.Phase.CLEARED or e.phase == B.Phase.OVER:
				break
		var left := e.foes.filter(func(c): return not c["dead"]).size()
		prints("bloomwand", ls[i].name, "phase", e.phase, "left", left, "of", e.foes.size(), "flowers left", e.flowers.size(), "deaths", deaths[0], "time", snappedf(e.time, 0.1))
		if e.phase == B.Phase.CLEARED:
			cleared += 1
	assert_int(cleared).is_greater_equal(4)
