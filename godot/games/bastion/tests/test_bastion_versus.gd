extends GdUnitTestSuite
## Bastion Coast versus: regions, players shelling each other, players falling out, a winner, the autopilot.

const SPLIT := "res://games/bastion/packs/versus/split-isle.map"
const CROWNS := "res://games/bastion/packs/versus/three-crowns.map"
const P = BastionEngine.Phase


func _claimed(path: String, n: int, seed: int = 3) -> BastionEngine:
	var e := BastionEngine.new(CoastMap.load_file(path), seed, n)
	for p in n:
		e.act(p)  # each player takes the castle nearest to their cursor
	return e


## Runs the engine until `phase` (or the game ends).
func _until(e: BastionEngine, phase: int) -> void:
	var n := 0
	while e.phase != phase and e.phase != P.GAME_OVER and n < 60 * 120:
		e.tick()
		n += 1


func _place_all_cannons(e: BastionEngine) -> void:
	for pl in e.players:
		for y in e.map.h:
			for x in e.map.w:
				if pl.cannons_to_place > 0 and e.can_place_cannon(Vector2i(x, y), pl.index):
					pl.cursor = Vector2(x, y)
					e.act(pl.index)


func test_versus_maps_have_a_region_and_castles_for_every_player() -> void:
	var p := Pack.find("bastion", "versus")
	assert_object(p).is_not_null()
	assert_int(p.levels.size()).is_greater_equal(3)
	var three := 0
	for f in p.levels:
		var m := CoastMap.load_file(f)
		assert_int(m.players).is_greater_equal(2)
		if m.players == 3:
			three += 1
		for pl in m.players:
			assert_int(m.castles_of(pl).size()).override_failure_message("%s: player %d castles" % [m.name, pl + 1]).is_greater_equal(2)
		# every castle's starting ring fits on its owner's land
		for pl in m.players:
			for c in m.castles_of(pl):
				var e := BastionEngine.new(m, 1, m.players)
				e._claim_home(c, pl)
				assert_array(e.players[pl].enclosed_castles).override_failure_message("%s: castle %d is not sealed by its ring" % [m.name, c]).contains([c])
	assert_int(three).is_greater_equal(1)
	assert_int(BastionGame.versus_maps(2).size()).is_greater_equal(2)
	assert_int(BastionGame.versus_maps(3).size()).is_greater_equal(1)


func test_players_choose_and_build_only_in_their_own_region() -> void:
	var e := BastionEngine.new(CoastMap.load_file(SPLIT), 3, 2)
	var theirs := e.map.castles_of(1)[0]
	e.players[0].cursor = Vector2(e.map.castles[theirs])  # player 1 points at player 2's castle
	e.act(0)
	assert_int(e.map.region_of(e.map.castles[e.players[0].home_castle].x, e.map.castles[e.players[0].home_castle].y)).is_equal(0)
	assert_int(e.phase).is_equal(P.CHOOSE)  # still waiting for player 2
	e.act(1)
	assert_int(e.phase).is_equal(P.CANNONS)
	assert_int(e.players[0].cannons_to_place).is_equal(BastionEngine.FIRST_ROUND_CANNONS)
	assert_int(e.players[1].cannons_to_place).is_equal(BastionEngine.FIRST_ROUND_CANNONS)
	var c1 := e.map.castles[e.players[1].home_castle]
	assert_bool(e.is_ours(c1.x, c1.y, 1)).is_true()
	assert_bool(e.is_ours(c1.x, c1.y, 0)).is_false()
	assert_bool(e.buildable(c1.x + 2, c1.y, 0)).is_false()
	assert_bool(e.buildable(c1.x + 2, c1.y, 1)).is_true()
	for w in e._our_walls(1):
		assert_int(e.map.region_of(w.x, w.y)).is_equal(1)


func test_players_fire_at_each_other() -> void:
	var e := _claimed(SPLIT, 2)
	_place_all_cannons(e)
	assert_int(e.active_cannons(0)).is_equal(BastionEngine.FIRST_ROUND_CANNONS)
	_until(e, P.BATTLE)
	assert_array(e.ships).is_empty()  # no fleet in versus
	var wall := e._our_walls(1)[0]
	var broken := [0]
	e.event.connect(func(kind, d): if kind == "wall_destroyed" and d["player"] == 1: broken[0] += 1)
	assert_bool(e.fire_at(Vector2(wall), 0)).is_true()
	for i in 180:
		e.tick()
	assert_int(e.cell(wall.x, wall.y)).is_equal(BastionEngine.Cell.RUBBLE)
	assert_int(broken[0]).is_equal(1)
	assert_int(e.players[0].score).is_equal(BastionEngine.WALL_POINTS)
	# player 2's cannon takes CANNON_HP hits and is gone
	var gun: Dictionary = e.cannons.filter(func(c): return c["player"] == 1)[0]
	var at := Vector2(gun["pos"]) + Vector2(0.4, 0.4)
	var destroyed := [false]
	e.event.connect(func(kind, d): if kind == "cannon_destroyed" and d["pos"] == gun["pos"]: destroyed[0] = true)
	var shots := 0
	var n := 0
	while not destroyed[0] and n < 60 * 16:
		if e.fire_at(at, 0):
			shots += 1
		e.tick()
		n += 1
	assert_bool(destroyed[0]).is_true()
	assert_int(shots).is_greater_equal(BastionEngine.CANNON_HP)
	assert_int(e.cell(gun["pos"].x, gun["pos"].y)).is_equal(BastionEngine.Cell.RUBBLE)
	assert_int(e.players[1].cannons_broken).is_equal(0)
	assert_int(e.players[0].cannons_broken).is_equal(1)


func test_a_player_with_no_enclosed_castle_is_out_and_the_other_wins() -> void:
	var e := _claimed(SPLIT, 2)
	_until(e, P.BUILD)
	for w in e._our_walls(1):  # player 2's ring is blasted open
		e.cells[w.y * e.map.w + w.x] = BastionEngine.Cell.RUBBLE
	var out := [-1]
	e.event.connect(func(kind, d): if kind == "player_out": out[0] = d["player"])
	_until(e, P.CANNONS)
	assert_int(out[0]).is_equal(1)
	assert_bool(e.players[1].alive).is_false()
	assert_int(e.phase).is_equal(P.GAME_OVER)
	assert_int(e.winner).is_equal(0)
	assert_bool(e.act(1)).is_false()


func test_three_players_play_on_until_one_is_left() -> void:
	var e := _claimed(CROWNS, 3)
	assert_int(e.phase).is_equal(P.CANNONS)
	_until(e, P.BUILD)
	for w in e._our_walls(2):
		e.cells[w.y * e.map.w + w.x] = BastionEngine.Cell.RUBBLE
	_until(e, P.CANNONS)
	assert_bool(e.players[2].alive).is_false()
	assert_int(e.phase).is_equal(P.CANNONS)  # two left: the match goes on
	assert_int(e.players[2].cannons_to_place).is_equal(0)
	assert_array(e.alive_players()).is_equal([0, 1])
	_until(e, P.BUILD)
	for w in e._our_walls(0):
		e.cells[w.y * e.map.w + w.x] = BastionEngine.Cell.RUBBLE
	_until(e, P.GAME_OVER)
	assert_int(e.winner).is_equal(1)


func test_the_best_score_wins_after_the_last_round() -> void:
	var e := _claimed(SPLIT, 2)
	e.map.rounds = 1
	e.players[1].score = 5000
	_until(e, P.GAME_OVER)
	assert_bool(e.players[0].alive and e.players[1].alive).is_true()
	assert_int(e.winner).is_equal(1)


func test_the_solo_game_is_unchanged_by_players() -> void:
	# the solo fields are player 0's, and the solo game has one player and a fleet
	var e := BastionEngine.new(CoastMap.load_file("res://games/bastion/packs/the-coastline/first-shore.map"), 42)
	assert_int(e.players.size()).is_equal(1)
	assert_bool(e.versus or not e.fleet).is_false()
	e.cursor = Vector2(3, 4)
	assert_vector(e.players[0].cursor).is_equal(Vector2(3, 4))


func test_the_autopilot_plays_a_whole_versus_match() -> void:
	for n in [2, 3]:
		var g := BastionGame.new()
		g.demo = true
		add_child(g)
		g.set_process(false)
		g.start_versus(n, 11)
		var e := g.engine
		assert_int(e.players.size()).is_equal(n)
		var shots := {}
		e.event.connect(func(kind, d): if kind == "wall_destroyed" and d.has("player"): shots[d["player"]] = shots.get(d["player"], 0) + 1)
		var ticks := 0
		while e.phase != P.GAME_OVER and ticks < 60 * 60 * 12:
			for pl in e.players:
				if pl.alive:
					g._bot_versus(pl.index, BastionEngine.TICK)
			e.tick()
			ticks += 1
		assert_int(e.phase).override_failure_message("%d players: no winner after %d rounds" % [n, e.round_number]).is_equal(P.GAME_OVER)
		assert_int(e.winner).is_between(0, n - 1)
		assert_int(e.round_number).is_greater_equal(2)
		assert_int(shots.size()).override_failure_message("walls of every player were shelled").is_equal(n)
		g.queue_free()


func _key(physical: int, keycode: int = KEY_NONE) -> InputEventKey:
	var k := InputEventKey.new()
	k.pressed = true
	k.physical_keycode = physical
	k.keycode = keycode if keycode != KEY_NONE else physical
	return k


func test_each_player_has_their_own_controls() -> void:
	var g := BastionGame.new()
	add_child(g)
	g.set_process(false)
	g.start_versus(2, 5)
	var e := g.engine
	g._input(_key(KEY_F, KEY_Z))  # player 2 acts on F by position, whatever the layout says
	assert_int(e.players[1].home_castle).is_greater_equal(0)
	assert_int(e.players[0].home_castle).is_equal(-1)
	g._input(_key(KEY_SPACE))  # player 1
	assert_int(e.phase).is_equal(P.CANNONS)
	# a gamepad's B rotates its player's piece (and is kept from the pause menu)
	_until(e, P.BUILD)
	g._pads = {0: 1}
	var turns := e.players[1].piece_turns
	var b := InputEventJoypadButton.new()
	b.device = 0
	b.button_index = JOY_BUTTON_B
	b.pressed = true
	g._input(b)
	assert_int(e.players[1].piece_turns).is_equal((turns + 1) % 4)
	g.queue_free()


func test_f2_opens_the_versus_chooser_and_3_starts_three_players() -> void:
	var g := BastionGame.new()
	add_child(g)
	g.set_process(false)
	g.demo = true
	g.start(7)
	g._input(_key(KEY_F2))
	assert_bool(g.choosing).is_true()
	g._input(_key(KEY_3))
	assert_bool(g.choosing).is_false()
	assert_bool(g.demo).is_false()
	assert_int(g.engine.players.size()).is_equal(3)
	assert_int(g.engine.map.players).is_equal(3)
	g.queue_free()
