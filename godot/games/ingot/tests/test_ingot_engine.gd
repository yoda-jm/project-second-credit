extends GdUnitTestSuite
## Ingot Run: the tile format, running, climbing, bars, falling, digging and refilling, guards trapped and buried,
## the exit, and the autopilot clearing every level of our set.

const E = preload("res://games/ingot/engine/ingot_engine.gd")
const T = IngotLevel.T
const SET := "res://games/ingot/levels/deep-seam.lvl"


func _lv(rows: Array) -> IngotLevel:
	return IngotLevel.parse_rows(rows)


func _run(e: IngotEngine, seconds: float, dir := Vector2i.ZERO) -> void:
	for i in int(seconds / E.TICK):
		e.input = dir
		e.tick()


func test_the_set_parses() -> void:
	var lv := IngotLevel.parse_file(FileAccess.get_file_as_string(SET))
	assert_int(lv.size()).is_equal(5)
	for l in lv:
		assert_int(l.w).is_equal(28)
		assert_int(l.h).is_equal(16)
		assert_bool(l.gold.size() > 0).is_true()


func test_plain_sets_without_headers_parse() -> void:
	var text := "  $  \n##&##\n@@@@@\n\n $   \n# & #\n@@@@@\n"
	assert_int(IngotLevel.parse_file(text).size()).is_equal(2)


func test_run_climb_and_fall() -> void:
	var e := IngotEngine.new(_lv(["     ", " H   ", " H  &", "#####"]), 1)
	_run(e, 0.6, Vector2i(-1, 0))  # three cells to the ladder (the third step finishes after the key is let go)
	_run(e, 0.3)
	assert_int(e.runner["cell"].x).is_equal(1)
	_run(e, 1.0, Vector2i(0, -1))
	assert_int(e.runner["cell"].y).is_equal(0)
	_run(e, 0.5, Vector2i(1, 0))  # off the ladder top into the air: falls back to the floor
	_run(e, 1.0)
	assert_int(e.runner["cell"].y).is_equal(2)


func test_dig_a_hole_that_refills() -> void:
	var e := IngotEngine.new(_lv(["  &  ", "#####", "@@@@@"]), 1)
	e.dig_right = true
	e.tick()
	assert_bool(e.holes.has(Vector2i(3, 1))).is_true()
	assert_int(e.at(Vector2i(3, 1))).is_equal(T.EMPTY)
	_run(e, E.HOLE_OPEN + E.HOLE_REFILL + 0.2)
	assert_bool(e.holes.has(Vector2i(3, 1))).is_false()


func test_stone_does_not_dig() -> void:
	var e := IngotEngine.new(_lv(["  &  ", "#@@@#", "@@@@@"]), 1)
	assert_bool(e._can_dig(Vector2i(2, 0), 1)).is_false()


func test_a_guard_falls_in_the_hole_and_is_buried() -> void:
	var e := IngotEngine.new(_lv(["&      0", "########", "@@@@@@@@"]), 1)
	var kinds := []
	e.event.connect(func(k, _d): kinds.append(k))
	e.dig_right = true
	e.tick()
	_run(e, E.HOLE_OPEN + E.HOLE_REFILL + 0.5)
	assert_bool(kinds.has("trapped")).is_true()


func test_all_gold_reveals_the_exit_and_the_top_wins() -> void:
	var e := IngotEngine.new(_lv(["    S", "  & S", "#####"]), 1)
	e.gold[Vector2i(3, 1)] = true
	_run(e, 0.6, Vector2i(1, 0))
	assert_bool(e.revealed).is_true()
	_run(e, 0.6, Vector2i(1, 0))
	_run(e, 1.2, Vector2i(0, -1))
	assert_int(e.phase).is_equal(E.Phase.CLEARED)


func test_every_level_can_be_cleared() -> void:
	# with the guards out of the way the autopilot clears each level: all gold reachable, the exit at the top
	var levels := IngotLevel.parse_file(FileAccess.get_file_as_string(SET))
	for i in levels.size():
		var lv: IngotLevel = IngotLevel.parse_file(FileAccess.get_file_as_string(SET))[i]
		lv.guards.clear()
		var e := IngotEngine.new(lv, 1)
		var bot := IngotBot.new(1)
		for n in 60 * 200:
			bot.drive(e)
			e.tick()
			if e.phase != E.Phase.PLAY:
				break
		assert_int(e.phase).override_failure_message("%s is not cleared" % levels[i].name).is_equal(E.Phase.CLEARED)


func test_the_autopilot_holds_its_own_against_guards() -> void:
	# the demo: with the guards on, the autopilot gathers a good share of the gold before it is caught (or wins)
	var total := 0
	var taken := 0
	for i in 5:
		var lv: IngotLevel = IngotLevel.parse_file(FileAccess.get_file_as_string(SET))[i]
		var e := IngotEngine.new(lv, 2)
		var bot := IngotBot.new(2)
		total += lv.gold.size()
		for n in 60 * 120:
			bot.drive(e)
			e.tick()
			if e.phase != E.Phase.PLAY:
				break
		taken += lv.gold.size() - e._gold_left()
	assert_int(taken * 2).is_greater_equal(total)
