extends GdUnitTestSuite
## Tunnel Pop: the hero digs as he goes and turns only at a cell's centre, the hose catches and the pump pops, rocks
## fall when dug under and crush, a creature cut off goes ghost, and the autopilot clears levels.

const D = preload("res://games/tunnelpop/engine/pop_dig_engine.gd")


func _engine(level := 0) -> DigEngine:
	var e := DigEngine.new(level, 0, 3, 5)
	e.phase = D.Phase.PLAY
	return e


## No creatures but one parked far away (so the level isn't cleared at once).
func _alone(e: DigEngine) -> void:
	e.foes.clear()
	e._dig_cell(Vector2i(0, D.ROWS - 1))
	e._spawn(Vector2i(0, D.ROWS - 1), "puffer")
	e.foes[0]["speed"] = 0.0
	e.foes[0]["ghost_t"] = 1e9


func test_digging_opens_cells_and_links() -> void:
	var e := _engine()
	_alone(e)
	var start := e.hero_cell()
	e.want = Vector2i(1, 0)
	for i in 60:
		e.tick()
	var c := e.hero_cell()
	assert_int(c.x).is_greater(start.x)
	assert_bool(e.linked(start, start + Vector2i(1, 0))).is_true()


func test_turns_wait_for_a_centre() -> void:
	var e := _engine()
	_alone(e)
	e.want = Vector2i(1, 0)
	for i in 8:
		e.tick()
	var y0: float = e.hero["pos"].y
	e.want = Vector2i(0, 1)
	e.tick()
	# halfway between centres: he carries on along the row first
	assert_float(e.hero["pos"].y).is_equal(y0)


func test_the_pump_pops_a_creature_in_reach() -> void:
	var e := _engine()
	_alone(e)
	var h := e.hero_cell()
	e._dig_line(h, h + Vector2i(3, 0))
	e._spawn(h + Vector2i(2, 0), "puffer")
	e.foes[1]["speed"] = 0.0
	e.hero["dir"] = 0
	e.hero["face"] = 0
	var pops := []
	e.event.connect(func(k, d): if k == "pop": pops.append(d["points"]))
	for i in 4:
		e.pump_pressed = true
		e.tick()
		e.tick()
	assert_array(pops).has_size(1)


func test_a_rock_falls_and_crushes() -> void:
	var e := _engine()
	_alone(e)
	e.rocks.clear()
	var c := Vector2i(2, 5)
	e.rocks.append({"cell": c, "y": float(c.y), "state": "rest", "t": 0.0, "id": 0, "crushed": 0})
	e._dig_line(c + Vector2i(0, 1), c + Vector2i(0, 4))
	e._spawn(c + Vector2i(0, 3), "puffer")
	e.foes[1]["speed"] = 0.0
	var crushes := []
	e.event.connect(func(k, d): if k == "crush": crushes.append(d["points"]))
	for i in 180:
		e.tick()
	assert_array(crushes).has_size(1)


func test_the_autopilot_clears_levels() -> void:
	var cleared := 0
	for lv in 3:
		var e := DigEngine.new(lv, 0, 9, 11 + lv)
		var bot := DigBot.new()
		var deaths := [0]
		e.event.connect(func(k, d): if k == "die": deaths[0] += 1)
		for n in 60 * 150:
			bot.drive(e)
			e.tick()
			if e.phase == D.Phase.CLEARED or e.phase == D.Phase.OVER:
				break
		var left := e.foes.filter(func(f): return not f["dead"]).size()
		prints("tunnelpop level", lv + 1, "phase", e.phase, "left", left, "of", e.foes.size(), "deaths", deaths[0], "score", e.score, "time", snappedf(e.time, 0.1))
		if e.phase == D.Phase.CLEARED:
			cleared += 1
	assert_int(cleared).is_greater_equal(2)
