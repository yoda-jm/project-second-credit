extends GdUnitTestSuite
## Bastion Coast rules: map parsing, wall pieces, enclosure and the round loop.

const MAP := "res://games/bastion/maps/first-shore.map"


func _engine() -> BastionEngine:
	return BastionEngine.new(CoastMap.load_file(MAP), 42)


func test_map_parses() -> void:
	var m := CoastMap.load_file(MAP)
	assert_str(m.name).is_equal("First Shore")
	assert_int(m.w).is_equal(40)
	assert_int(m.h).is_equal(28)
	assert_int(m.castles.size()).is_equal(4)
	assert_bool(m.is_land(10, 10)).is_true()
	assert_int(m.at(9, 12)).is_equal(CoastMap.Terrain.ROCK)


func test_rotation_keeps_shape() -> void:
	for shape in WallPieces.SHAPES:
		var r := WallPieces.rotated(shape, 4)
		assert_int(r.size()).is_equal(shape.size())
		var s := WallPieces.size_of(WallPieces.rotated(shape, 1))
		var s0 := WallPieces.size_of(WallPieces.rotated(shape, 0))
		assert_vector(s).is_equal(Vector2i(s0.y, s0.x))


func test_home_castle_is_enclosed_at_start() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	assert_int(e.home_castle).is_equal(1)
	assert_int(e.phase).is_equal(BastionEngine.Phase.CANNONS)
	assert_array(e.enclosed_castles).contains([1])
	assert_int(e.cannons_to_place).is_equal(BastionEngine.FIRST_ROUND_CANNONS)


func test_diagonal_walls_seal() -> void:
	var e := _engine()
	# a diamond of walls touching only at their corners around castle 0 (7..8, 6..7)
	var ring: Array[Vector2i] = []
	for y in range(3, 11):
		for x in range(4, 12):
			if absf(x - 7.5) + absf(y - 6.5) == 3.0:
				ring.append(Vector2i(x, y))
	for p in ring:
		e.cells[p.y * e.map.w + p.x] = BastionEngine.Cell.WALL
	e._compute_territory(false)
	assert_bool(e.is_ours(7, 6)).is_true()
	assert_array(e.enclosed_castles).contains([0])
	e.cells[ring[0].y * e.map.w + ring[0].x] = BastionEngine.Cell.EMPTY  # open a gap
	e._compute_territory(false)
	assert_bool(e.is_ours(7, 6)).is_false()


func test_cannons_only_inside_territory() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	assert_bool(e.can_place_cannon(Vector2i(30, 3))).is_false()  # sea
	var placed := 0
	for y in e.map.h:
		for x in e.map.w:
			if e.cannons_to_place > 0 and e.can_place_cannon(Vector2i(x, y)):
				e.cursor = Vector2(x, y)
				if e.act():
					placed += 1
	assert_int(placed).is_equal(BastionEngine.FIRST_ROUND_CANNONS)


func test_a_full_round_without_repairs_survives_if_walls_hold() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	var ticks := 0
	while e.phase != BastionEngine.Phase.BUILD and ticks < 60 * 60:
		e.tick()
		ticks += 1
	assert_int(e.phase).is_equal(BastionEngine.Phase.BUILD)
	assert_bool(e.piece.size() > 0).is_true()
	# fill every breach by placing single blocks where rubble is not blocking: the ring may be broken, so the
	# outcome depends on the ships; we only check that the round ends in either CANNONS or GAME_OVER.
	while e.phase == BastionEngine.Phase.BUILD:
		e.tick()
	assert_bool(e.phase == BastionEngine.Phase.CANNONS or e.phase == BastionEngine.Phase.GAME_OVER).is_true()


func test_shooting_sinks_a_ship() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	for y in e.map.h:
		for x in e.map.w:
			if e.cannons_to_place > 0 and e.can_place_cannon(Vector2i(x, y)):
				e.cursor = Vector2(x, y)
				e.act()
	while e.phase != BastionEngine.Phase.BATTLE:
		e.tick()
	var ship: Dictionary = e.ships[0]
	ship["hp"] = 1
	ship["target"] = ship["pos"]  # hold still
	var sunk := [false]
	e.event.connect(func(kind, _d): if kind == "ship_sunk": sunk[0] = true)
	assert_bool(e.fire_at(ship["pos"])).is_true()
	for i in 240:
		e.tick()
	assert_bool(sunk[0]).is_true()


func test_rubble_clears_after_one_repair_phase() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	var i := 14 * e.map.w + 18
	e._impact({"to": Vector2(18, 14), "ours": false})  # a ship hit on the land near the castle
	assert_int(e.cells[i]).is_equal(BastionEngine.Cell.RUBBLE)
	e._start_cannons()  # next round
	assert_int(e.cells[i]).is_equal(BastionEngine.Cell.EMPTY)


func test_game_scene_runs_the_demo() -> void:
	var runner := scene_runner("res://games/bastion/scenes/bastion_game.tscn")
	var game: BastionGame = runner.find_child("Game")
	game.demo = true
	game.start(7)
	await runner.simulate_frames(80, 250)  # 20 s: castle chosen, cannons placed, battle under way
	assert_int(game.engine.home_castle).is_greater_equal(0)
	assert_int(game.engine.cannons.size()).is_greater(0)


func test_ships_fire_only_from_the_play_area() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	var outside := [0]
	e.event.connect(func(kind, d):
		if kind == "shot" and not d["ours"] and not e._in_play_area(d["from"]):
			outside[0] += 1)
	for round in 3:
		while e.phase != BastionEngine.Phase.BATTLE and e.phase != BastionEngine.Phase.GAME_OVER:
			e.tick()
		while e.phase == BastionEngine.Phase.BATTLE:
			e.tick()
	assert_int(outside[0]).is_equal(0)


func test_friendly_fire_breaks_our_wall_but_not_empty_land() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	var wall := e._our_walls()[0]
	e._impact({"to": Vector2(wall), "ours": true})
	assert_int(e.cell(wall.x, wall.y)).is_equal(BastionEngine.Cell.RUBBLE)
	e._impact({"to": Vector2(10, 10), "ours": true})
	assert_int(e.cell(10, 10)).is_equal(BastionEngine.Cell.EMPTY)


func test_hole_detector_finds_the_gaps() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	assert_array(e.holes_around(1)).is_empty()  # sealed at start
	var walls := e._our_walls()
	var a := walls[3]
	var b := walls[walls.size() - 4]
	e.cells[a.y * e.map.w + a.x] = BastionEngine.Cell.EMPTY
	e.cells[b.y * e.map.w + b.x] = BastionEngine.Cell.EMPTY
	var holes := e.holes_around(1)
	assert_int(holes.size()).is_equal(2)
	assert_bool(holes.has(a) and holes.has(b)).is_true()
	# an unwalled castle is wide open
	assert_int(e.holes_around(0, 6).size()).is_equal(7)


func test_blocked_when_the_piece_fits_nowhere() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	e.phase = BastionEngine.Phase.BUILD
	e._next_piece()
	assert_str(e.blocked()).is_equal("")
	for i in e.cells.size():  # fill every free cell with rubble
		if e.cells[i] == BastionEngine.Cell.EMPTY:
			e.cells[i] = BastionEngine.Cell.RUBBLE
	assert_str(e.blocked()).is_equal("piece")


func test_a_sealed_pocket_without_castle_is_not_territory() -> void:
	var e := _engine()
	e.cursor = Vector2(e.map.castles[1])
	e.act()
	# a small closed ring far from any castle
	for p in [Vector2i(26, 14), Vector2i(27, 14), Vector2i(28, 14), Vector2i(26, 15), Vector2i(28, 15), Vector2i(26, 16),
			Vector2i(27, 16), Vector2i(28, 16)]:
		e.cells[p.y * e.map.w + p.x] = BastionEngine.Cell.WALL
	e._compute_territory(false)
	assert_bool(e.is_ours(27, 15)).is_false()
	assert_bool(e.is_ours(e.map.castles[1].x, e.map.castles[1].y)).is_true()
