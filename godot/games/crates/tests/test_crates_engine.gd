extends GdUnitTestSuite
## Crate Keeper: the Sokoban format, pushing, walls, undo and redo, and every puzzle of our set solved by its
## stored solution in exactly par moves.

const SET := "res://games/crates/levels/harbour.xsb"


func _lv(rows: Array[String]) -> CratesLevel:
	return CratesLevel.parse_rows(rows)


func test_the_set_parses_with_names_par_and_solutions() -> void:
	var lv := CratesLevel.parse_file(FileAccess.get_file_as_string(SET))
	assert_int(lv.size()).is_equal(8)
	assert_str(lv[0].name).is_equal("First Crate")
	for l in lv:
		assert_int(l.par).is_greater(0)
		assert_str(l.solution).is_not_empty()
		assert_int(l.goals.size()).is_equal(l.crates.size())


func test_plain_collections_parse() -> void:
	var text := "; 1\n#####\n#@$.#\n#####\n\n; 2\n######\n#@$ .#\n######\n"
	var lv := CratesLevel.parse_file(text)
	assert_int(lv.size()).is_equal(2)
	assert_str(lv[1].name).is_equal("2")


func test_push_one_not_two_and_not_through_walls() -> void:
	var e := CratesEngine.new(_lv(["#######", "#@$$ .#", "#######"]))
	assert_bool(e.step(Vector2i(1, 0))).is_false()  # two crates in a row
	e = CratesEngine.new(_lv(["#####", "#@$.#", "#####"]))
	assert_bool(e.step(Vector2i(1, 0))).is_true()
	assert_bool(e.solved).is_true()
	assert_bool(e.step(Vector2i(1, 0))).is_false()


func test_undo_and_redo() -> void:
	var e := CratesEngine.new(_lv(["######", "#@$ .#", "######"]))
	e.step(Vector2i(1, 0))
	e.step(Vector2i(1, 0))
	assert_bool(e.solved).is_true()
	e.undo()
	e.undo()
	assert_that(e.keeper).is_equal(Vector2i(1, 1))
	assert_that(e.crates[0]).is_equal(Vector2i(2, 1))
	assert_int(e.moves).is_equal(0)
	e.redo()
	e.redo()
	assert_bool(e.solved).is_true()
	assert_int(e.pushes).is_equal(2)


func test_every_puzzle_is_solved_by_its_solution_in_par() -> void:
	for lv in CratesLevel.parse_file(FileAccess.get_file_as_string(SET)):
		var e := CratesEngine.new(lv)
		e.play(lv.solution)
		assert_bool(e.solved).override_failure_message(lv.name + " not solved").is_true()
		assert_int(e.moves).is_equal(lv.par)


func test_click_to_walk_finds_a_way_round() -> void:
	var e := CratesEngine.new(_lv(["#####", "#@  #", "# # #", "#  $#", "#.  #", "#####"]))
	var path := e.walk_to(Vector2i(3, 1))
	assert_int(path.size()).is_equal(2)
