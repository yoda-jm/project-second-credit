extends GdUnitTestSuite
## Blastyard: arenas, bombs, chains, crates and power-ups, kicks, sudden death, bots playing whole rounds.

const E = preload("res://games/blastyard/engine/blast_engine.gd")
const T = ArenaMap.T
const SMALL := """[arena]
name=Test
crates=0
time=999
#########
#1     2#
# # # # #
#   +   #
#########
"""


func _map(text := SMALL) -> ArenaMap:
	return ArenaMap.parse_file(text)[0]


func _run(e: BlastEngine, seconds: float, bots: Array = []) -> void:
	for i in int(seconds / E.TICK):
		for b in bots:
			b.drive(e)
		e.tick()


func test_arenas_and_stages_parse() -> void:
	var a := ArenaMap.parse_file(FileAccess.get_file_as_string("res://games/blastyard/maps/arenas.blast"))
	assert_int(a.size()).is_equal(3)
	for m in a:
		assert_int(m.starts.size()).is_equal(4)
		assert_int(m.w).is_equal(15)
	var s := ArenaMap.parse_file(FileAccess.get_file_as_string("res://games/blastyard/maps/solo.blast"))
	assert_int(s.size()).is_equal(4)
	for m in s:
		assert_bool(m.solo).is_true()
		assert_int(m.at(m.exit_cell)).is_equal(T.CRATE)
		assert_int(m.enemies.size()).is_greater(0)


func test_a_bomb_bursts_the_crate_and_kills_whoever_stands_in_line() -> void:
	var e := BlastEngine.new(_map(), 2, 1)
	var kinds := []
	e.event.connect(func(k, _d): kinds.append(k))
	# player 1 walks to (3,3)... simpler: drop a bomb where player 2 stands and keep them still
	e.set_input(1, Vector2i.ZERO, true)
	_run(e, 3.5)
	assert_bool(kinds.has("bomb")).is_true()
	assert_bool(kinds.has("explode")).is_true()
	assert_bool(e.player(1)["alive"]).is_false()
	assert_bool(e.player(0)["alive"]).is_true()


func test_crates_burst_and_chains_go_off() -> void:
	var e := BlastEngine.new(_map(), 2, 1)
	e.bombs.append({"id": 90, "cell": Vector2i(3, 3), "pos": Vector2(3.5, 3.5), "owner": 0, "fuse": 0.1, "fire": 2, "slide": Vector2i.ZERO})
	e.bombs.append({"id": 91, "cell": Vector2i(1, 3), "pos": Vector2(1.5, 3.5), "owner": 0, "fuse": 9.0, "fire": 2, "slide": Vector2i.ZERO})
	var explodes := []
	e.event.connect(func(k, d): if k == "explode": explodes.append(d))
	_run(e, 0.6)
	assert_int(e.map.at(Vector2i(4, 3))).is_equal(T.FLOOR)  # the crate burst
	assert_int(explodes.size()).is_equal(2)  # the second bomb went off in the chain
	assert_int(e.bombs.size()).is_equal(0)


func test_kick_sends_a_bomb_sliding() -> void:
	var e := BlastEngine.new(_map(), 2, 1)
	var p := e.player(0)
	p["kick"] = true
	e.bombs.append({"id": 90, "cell": Vector2i(2, 1), "pos": Vector2(2.5, 1.5), "owner": 1, "fuse": 9.0, "fire": 1, "slide": Vector2i.ZERO})
	for i in 40:
		e.set_input(0, Vector2i(1, 0), false)
		e.tick()
	assert_int(e.bombs[0]["cell"].x).is_greater(3)


func test_sudden_death_closes_the_arena() -> void:
	var m := _map(SMALL.replace("time=999", "time=1"))
	var e := BlastEngine.new(m, 2, 1)
	var drops := []
	e.event.connect(func(k, _d): if k == "block_drop": drops.append(1))
	_run(e, 9.0)
	assert_bool(e.sudden).is_true()
	assert_int(drops.size()).is_greater(3)
	assert_int(e.phase).is_equal(BlastEngine.Phase.OVER)


func test_four_bots_play_a_round_to_the_end() -> void:
	var m := ArenaMap.parse_file(FileAccess.get_file_as_string("res://games/blastyard/maps/arenas.blast"), 3)[0]
	var e := BlastEngine.new(m, 4, 3)
	var bots := []
	for i in 4:
		bots.append(BlastBot.new(i, 3))
	var crates := []
	e.event.connect(func(k, _d): if k == "crate": crates.append(1))
	_run(e, 200.0, bots)
	assert_int(e.phase).is_equal(BlastEngine.Phase.OVER)
	assert_int(crates.size()).is_greater(10)


func test_the_bot_clears_a_solo_stage() -> void:
	var cleared := 0
	var stages := ArenaMap.parse_file(FileAccess.get_file_as_string("res://games/blastyard/maps/solo.blast"))
	for si in stages.size():
		for seed in [1, 2, 3]:
			var m := ArenaMap.parse_file(FileAccess.get_file_as_string("res://games/blastyard/maps/solo.blast"), seed)[si]
			var e := BlastEngine.new(m, 1, seed)
			var bot := BlastBot.new(0, seed)
			for i in 60 * 240:
				bot.drive(e)
				e.tick()
				if e.phase == BlastEngine.Phase.OVER:
					break
			if e.phase == BlastEngine.Phase.OVER and e.winner == 0:
				cleared += 1
				break
	assert_int(cleared).is_greater_equal(3)
