extends GdUnitTestSuite
## Rules of Fruitburrow on small hand-made gardens.

const E = preload("res://games/fruitburrow/engine/fruitburrow_engine.gd")
const T = preload("res://games/fruitburrow/engine/garden_map.gd").Terrain


func _garden(rows: String, monsters := 0, diggers := 0) -> GardenMap:
	return GardenMap.parse("name=Test\nmonsters=%d\ndiggers=%d\n%s" % [monsters, diggers, rows])


func _engine(rows: String, monsters := 0, diggers := 0) -> FruitburrowEngine:
	var e := FruitburrowEngine.new(_garden(rows, monsters, diggers), 3)
	_run(e, E.READY_SECONDS + 0.05)
	assert_int(e.phase).is_equal(E.Phase.PLAY)
	return e


func _run(e: FruitburrowEngine, seconds: float, dir := Vector2i.ZERO) -> void:
	for i in int(seconds / E.TICK):
		e.input_dir = dir
		e.tick()


func test_pack_parses_every_garden() -> void:
	var pack := GardenMap.load_pack("res://games/fruitburrow/gardens/orchard.gdn")
	assert_int(pack.size()).is_equal(3)
	for g in pack:
		assert_int(g.w).is_equal(18)
		assert_int(g.h).is_equal(11)
		assert_bool(g.fruit.size() > 0).is_true()
		assert_int(g.terrain[g.start.y * g.w + g.start.x]).is_equal(T.TUNNEL)
		assert_int(g.terrain[g.nest.y * g.w + g.nest.x]).is_equal(T.TUNNEL)
		for a in g.apples:  # no apple starts over a tunnel (it would drop at once)
			var below: Vector2i = a + Vector2i.DOWN
			if g.inside(below):
				assert_int(g.terrain[below.y * g.w + below.x]).is_not_equal(T.TUNNEL)


func test_digging_turns_soil_into_tunnel_and_picks_fruit() -> void:
	var e := _engine("N#####\nP##c##\n######")
	_run(e, 1.5, Vector2i.RIGHT)
	assert_int(e.at(Vector2i(1, 1))).is_equal(T.TUNNEL)
	assert_int(e.at(Vector2i(2, 1))).is_equal(T.TUNNEL)
	assert_bool(e.fruit.has(Vector2i(3, 1))).is_false()
	assert_int(e.score).is_equal(E.SCORE_FRUIT[0] + E.SCORE_CLEAR)
	assert_int(e.phase).is_equal(E.Phase.CLEAR)  # the only fruit: garden cleared


func test_digging_is_slower_than_walking() -> void:
	var dug := _engine("N#########c\nP#########c")
	var walk := _engine("N#########c\nP.........c")
	_run(dug, 1.0, Vector2i.RIGHT)
	_run(walk, 1.0, Vector2i.RIGHT)
	assert_float(walk.pos_of(walk.player).x).is_greater(dug.pos_of(dug.player).x + 1.0)


func test_stone_blocks_the_gardener() -> void:
	var e := _engine("N#c\nPX#\n###")
	_run(e, 1.0, Vector2i.RIGHT)
	assert_that(e.player["cell"]).is_equal(Vector2i(0, 1))


func test_undermined_apple_wobbles_then_falls_and_breaks() -> void:
	# the gardener digs under the apple and walks on; the apple drops two cells and breaks
	var e := _engine("N##A##c\nP######\n###.###\n###.###")
	var events := []
	e.event.connect(func(k, _d): events.append(k))
	_run(e, 0.8, Vector2i.RIGHT)  # under the apple after two cells
	_run(e, 2.0, Vector2i.RIGHT)
	assert_array(events).contains(["apple_wobble", "apple_fall"])
	assert_int(e.apples.size()).is_equal(0)
	assert_array(events).contains(["apple_break"])


func test_short_fall_leaves_the_apple() -> void:
	var e := _engine("N#A###c\nP######\n#######")
	_run(e, 3.0, Vector2i.RIGHT)
	assert_int(e.apples.size()).is_equal(1)
	assert_that(e.apples[0]["cell"]).is_equal(Vector2i(2, 1))
	assert_int(e.apples[0]["state"]).is_equal(E.Apple.REST)


func test_falling_apple_squashes_a_monster() -> void:
	# a monster in a pocket under the apple, the gardener out of its reach
	var e := _engine("N#A##\nP#.##\n##.##\n####c", 1)
	e.apples[0]["state"] = E.Apple.FALL
	e.monsters.append({"kind": E.Kind.PLUM, "cell": Vector2i(2, 2), "to": Vector2i(2, 2), "t": 0.0, "id": 99, "stuck": 0.0, "last": Vector2i.ZERO})
	var squashed := []
	e.event.connect(func(k, d): if k == "squash": squashed.append(d["id"]))
	_run(e, 1.0)
	assert_array(squashed).contains([99])


func test_apple_on_the_gardener_costs_a_life() -> void:
	var e := _engine("N#A#\nP#.#\n###c")
	e.player["cell"] = Vector2i(2, 1)
	e.player["to"] = Vector2i(2, 1)
	e.apples[0]["state"] = E.Apple.FALL
	_run(e, 0.5)
	assert_int(e.lives).is_equal(E.LIVES - 1)
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_monsters_come_out_of_the_nest_and_chase_through_tunnels() -> void:
	var e := _engine("N.........P\n##########c", 1)
	_run(e, E.SPAWN_FIRST + 0.1)
	assert_int(e.monsters.size()).is_equal(1)
	_run(e, 3.5)
	assert_int(e.lives).is_equal(E.LIVES - 1)  # caught at the end of the corridor


func test_blocked_monster_starts_digging() -> void:
	var e := _engine("N#########P\n##########c", 1)
	var events := []
	e.event.connect(func(k, _d): events.append(k))
	_run(e, E.SPAWN_FIRST + E.STUCK_TO_DIGGER + 6.0)
	assert_array(events).contains(["transform"])


func test_ball_follows_the_tunnel_and_knocks_out_a_monster() -> void:
	var e := _engine("P....\n####.\nN....\n####c", 1)
	e.player["face"] = Vector2i.RIGHT
	e.monsters.append({"kind": E.Kind.PLUM, "cell": Vector2i(1, 2), "to": Vector2i(1, 2), "t": 0.0, "id": 7, "stuck": 0.0, "last": Vector2i.ZERO})
	e.map.monsters = 1
	e.spawned = 1
	e.fire()
	_run(e, 0.1)
	assert_bool(e.has_ball).is_false()
	_run(e, 1.0)
	assert_int(e.monsters.size()).is_equal(0)
	assert_int(e.score).is_equal(E.SCORE_BALL + E.SCORE_CLEAR)  # the last monster out clears the garden
	assert_int(e.phase).is_equal(E.Phase.CLEAR)


func test_ball_grows_back() -> void:
	var e := _engine("P...\nN##c")
	e.player["face"] = Vector2i.RIGHT
	e.fire()
	_run(e, E.BALL_LIFE + E.BALL_REGROW + 0.2)
	assert_bool(e.has_ball).is_true()


func test_game_over_after_the_last_life() -> void:
	var e := _engine("N#A#\nP#.#\n###c")
	for i in E.LIVES:
		_run(e, 0.2)
		if e.phase == E.Phase.READY:
			_run(e, E.READY_SECONDS + 0.05)
		e.player["cell"] = Vector2i(2, 1)
		e.player["to"] = Vector2i(2, 1)
		e.apples[0]["cell"] = Vector2i(2, 0)
		e.apples[0]["y"] = 0.0
		e.apples[0]["fell"] = 0
		e.apples[0]["state"] = E.Apple.FALL
		_run(e, E.DYING_SECONDS + 0.6)
	assert_int(e.phase).is_equal(E.Phase.GAME_OVER)


func test_same_seed_and_inputs_replay_identically() -> void:
	var g := GardenMap.load_pack("res://games/fruitburrow/gardens/orchard.gdn")[0]
	var scores := []
	for run in 2:
		var e := FruitburrowEngine.new(g, 42)
		var dirs: Array[Vector2i] = [Vector2i.LEFT, Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN]
		for i in 1800:
			e.input_dir = dirs[(i / 45) % 4]
			if i % 97 == 0:
				e.fire()
			e.tick()
		scores.append([e.score, e.lives, e.monsters.size(), e.pos_of(e.player)])
	assert_array(scores[0]).is_equal(scores[1])


func test_demo_bot_clears_the_first_garden() -> void:
	var g := GardenMap.load_pack("res://games/fruitburrow/gardens/orchard.gdn")[0]
	var e := FruitburrowEngine.new(g, 11)
	var bot := GardenBot.new()
	for i in int(120.0 / E.TICK):
		bot.drive(e)
		e.tick()
		if e.level_done():
			break
	assert_bool(e.level_done()).is_true()
	assert_int(e.lives).is_greater(0)


func test_ball_grows_back_slower_after_each_throw() -> void:
	var e := _engine("P...\nN##c")
	e.player["face"] = Vector2i.RIGHT
	e.fire()
	_run(e, E.BALL_LIFE + 0.1)
	var first := e.ball_regrow
	_run(e, E.BALL_MAX_REGROW)
	e.fire()
	_run(e, E.BALL_LIFE + 0.1)
	assert_float(e.ball_regrow).is_greater(first)
