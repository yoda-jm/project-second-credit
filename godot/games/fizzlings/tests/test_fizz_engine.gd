extends GdUnitTestSuite
## Fizzlings: levels parse, heroes stand on platforms and jump up through them, falling out of the bottom comes
## back at the top, a blown bubble traps a toy, popping a chain of trapped toys pays and drops treats, a toy
## touching a hero costs a life, and two autopilots clear the first levels.

const E = preload("res://games/fizzlings/engine/fizz_engine.gd")
const FILE := "res://games/fizzlings/levels/toybox.fizz"


func _levels() -> Array[FizzLevel]:
	return FizzLevel.parse_file(FileAccess.get_file_as_string(FILE))


func _play(i := 0, players := 1) -> FizzEngine:
	var e := FizzEngine.new(_levels()[i], i, 1, players)
	e.phase = E.Phase.PLAY
	return e


func _run(e: FizzEngine, seconds: float) -> void:
	for i in int(seconds / E.TICK):
		e.tick()


func test_levels_parse() -> void:
	var ls := _levels()
	assert_int(ls.size()).is_equal(6)
	for l in ls:
		assert_int(l.toys.size()).is_greater(3)
		assert_float(l.starts[0].x).is_greater(0.0)


func test_heroes_stand_and_jump_through() -> void:
	var e := _play()
	e.toys.clear()
	var h: Dictionary = e.heroes[0]
	_run(e, 0.5)
	assert_bool(h["ground"]).is_true()
	var y0: float = h["pos"].y
	# under the shelf at row 21, jump: it lands on top of it
	h["pos"] = Vector2(7.5, y0)
	h["jump"] = true
	_run(e, 0.1)
	h["jump"] = false
	_run(e, 1.2)
	assert_float(h["pos"].y).is_equal_approx(21.0, 0.01)


func test_the_bottom_wraps_to_the_top() -> void:
	var e := _play()
	e.toys.clear()
	var h: Dictionary = e.heroes[0]
	h["pos"] = Vector2(16.0, 24.9)
	_run(e, 0.4)
	assert_float(h["pos"].y).is_less(10.0)


func test_a_bubble_traps_and_a_chain_pays() -> void:
	var e := _play()
	var h: Dictionary = e.heroes[0]
	e.toys = e.toys.slice(0, 2)
	for i in 2:
		e.toys[i]["pos"] = Vector2(8.0 + i * 1.5, 24.0)
		e.toys[i]["speed"] = 0.0
	h["pos"] = Vector2(4.0, 24.0)
	h["facing"] = 1
	h["blow"] = true
	_run(e, 0.5)
	h["blow"] = true
	_run(e, 0.5)
	var trapped := e.bubbles.filter(func(b): return not b["trapped"].is_empty()).size()
	assert_int(trapped).is_equal(2)
	# bring the bubbles together and pop one
	e.bubbles[0]["pos"] = Vector2(16, 10)
	e.bubbles[1]["pos"] = Vector2(17.2, 10)
	h["inv"] = 5.0
	h["pos"] = Vector2(16, 10.9)
	var s0: int = h["score"]
	e._collide(h)
	assert_int(h["score"] - s0).is_equal(2000)
	assert_int(e.treats.size()).is_equal(2)


func test_a_toy_costs_a_life() -> void:
	var e := _play()
	var h: Dictionary = e.heroes[0]
	h["inv"] = 0.0
	e.toys[0]["pos"] = h["pos"]
	e._collide(h)
	assert_bool(h["alive"]).is_false()
	assert_int(h["lives"]).is_equal(2)


func test_the_autopilots_clear_levels() -> void:
	var cleared := 0
	var ls := _levels()
	for i in 3:
		var e := FizzEngine.new(ls[i], i, 3 + i, 2)
		for h in e.heroes:
			h["lives"] = 9
		var bots := [FizzBot.new(0, i), FizzBot.new(1, i)]
		for t in int(150.0 / E.TICK):
			for b in bots:
				b.drive(e)
			e.tick()
			if e.phase == E.Phase.CLEARED or e.phase == E.Phase.OVER:
				break
		prints("level", i, "phase", e.phase, "toys", e.toys.size(), "time", snappedf(e.time, 0.1), "lives", e.heroes.map(func(h): return h["lives"]))
		if e.phase == E.Phase.CLEARED:
			cleared += 1
	assert_int(cleared).is_greater_equal(2)
