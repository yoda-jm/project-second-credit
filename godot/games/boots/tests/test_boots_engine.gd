extends GdUnitTestSuite
## Muddy Boots: map parsing, the original-format importer (on synthetic bytes), and the rules.

const E = preload("res://games/boots/engine/boots_engine.gd")
const T = preload("res://games/boots/engine/boots_map.gd").T


func _map(rows: String, goals := "kill", grenades := 4, rockets := 0) -> BootsMap:
	return BootsMap.parse("goals=%s\ngrenades=%d\nrockets=%d\n%s" % [goals, grenades, rockets, rows])


func _run(e: BootsEngine, seconds: float) -> void:
	for i in int(seconds / E.TICK):
		e.tick()


func test_campaign_parses_with_even_rows() -> void:
	var text := FileAccess.get_file_as_string("res://games/boots/packs/first-tour/first-tour.boots")
	var ms := BootsMap.parse_campaign(text)
	assert_int(ms.size()).is_equal(3)
	for chunk in text.split("[mission]").slice(1):
		var rows: Array = Array(chunk.split("\n")).filter(func(l): return l.strip_edges() != "" and not "=" in l and not l.begins_with(";"))
		for r in rows:
			assert_int(r.strip_edges().length()).is_equal(rows[0].strip_edges().length())
	for m in ms:
		assert_int(m.count("start")).is_equal(1)


func _be(v: int) -> PackedByteArray:
	return PackedByteArray([(v >> 8) & 0xFF, v & 0xFF])


func test_importer_reads_original_map_spt_and_hit() -> void:
	var map := PackedByteArray()
	map.resize(0x60)
	map.fill(0)
	for i in "junbase.blk".length():
		map[i] = "junbase.blk".unicode_at(i)
	map[0x54] = 0; map[0x55] = 3  # width 3 (big-endian)
	map[0x56] = 0; map[0x57] = 2  # height 2
	for tile in [0, 1, 2, 3, 4, 5]:
		map.append_array(_be(tile))
	var hit := PackedByteArray()
	for v in [0, 6, 3, 5, 9, 0xFF60]:  # land, water, block, water edge, drop, a mixed tile (land in its low nibble)
		hit.append_array(_be(v))
	var spt := PackedByteArray()
	for rec in [[0, 0, 0, 0, 0], [0, 0, 16, 16, 5], [0, 0, 0, 16, 72]]:  # player (1,0), enemy (2,1), hostage (1,1)
		for w in rec:
			spt.append_array(_be(w))
	var m := CfImport.from_bytes(map, spt, hit, PackedByteArray(), "test")
	assert_int(m.w).is_equal(3)
	assert_int(m.h).is_equal(2)
	assert_array(Array(m.terrain)).is_equal([T.LAND, T.WATER, T.ROCK, T.SHALLOW, T.CLIFF, T.LAND])
	assert_int(m.count("start")).is_equal(1)
	assert_int(m.count("enemy")).is_equal(1)
	assert_that(m.things.filter(func(t): return t["kind"] == "enemy")[0]["cell"]).is_equal(Vector2i(2, 1))
	assert_str(m.source).is_equal("original")


func test_leader_walks_around_trees_and_the_squad_follows() -> void:
	var e := BootsEngine.new(_map("........\n.P..T...\n....T...\n....T...\n........", "none"), 1, 3)
	e.move_to(Vector2(6.5, 2.5))
	_run(e, 4.0)
	assert_float((e.leader()["pos"] as Vector2).distance_to(Vector2(6.5, 2.5))).is_less(0.1)
	for s in e.soldiers:  # the file stays behind the leader, never inside the trees
		assert_bool(e.blocked(e.cell_of(s["pos"]))).is_false()
	assert_float((e.soldiers[1]["pos"] as Vector2).distance_to(e.leader()["pos"])).is_less(1.5)


func test_bullets_kill_an_enemy_in_the_open_but_not_behind_rock() -> void:
	var e := BootsEngine.new(_map("..........\n.P.....E..\n..........\n.......#..\n.......E..", "none"), 1, 1)
	e.aim = Vector2(7.5, 1.5)
	e.firing = true
	_run(e, 1.0)
	assert_bool(e.enemies[0]["alive"]).is_false()
	e.aim = Vector2(7.5, 4.5)
	_run(e, 1.0)


func test_enemy_shoots_back_when_it_sees_the_squad() -> void:
	var e := BootsEngine.new(_map("..........\n.P.....E..\n..........", "none"), 3, 1)
	var shots := [0]
	e.event.connect(func(k, _d): if k == "enemy_shot": shots[0] += 1)
	_run(e, 4.0)
	assert_int(shots[0]).is_greater(0)


func test_rock_hides_the_squad() -> void:
	var e := BootsEngine.new(_map("..........\n.P...#.E..\n.....#....", "none"), 3, 1)
	var shots := [0]
	e.event.connect(func(k, _d): if k == "enemy_shot": shots[0] += 1)
	e.enemies[0]["home"] = e.enemies[0]["pos"]
	_run(e, 0.5)
	assert_int(shots[0]).is_equal(0)


func test_grenade_destroys_a_hut_and_wins_the_mission() -> void:
	var e := BootsEngine.new(_map("..........\n.P....H...\n..........\n..........", "destroy"), 1, 1)
	e.throw_grenade(Vector2(7.0, 2.0))
	assert_int(e.grenades).is_equal(3)
	_run(e, 1.2)
	assert_bool(e.huts[0]["alive"]).is_false()
	assert_int(e.phase).is_equal(E.Phase.WON)


func test_huts_send_out_soldiers() -> void:
	var e := BootsEngine.new(_map("..........\n.P....H...\n..........\n..........\n..........", "none"), 1, 1)
	_run(e, E.HUT_SPAWN.y + 0.5)
	assert_int(e.enemies.size()).is_greater(0)


func test_mine_kills_the_soldier_on_it() -> void:
	var e := BootsEngine.new(_map("......\n.P.M..\n......", "none"), 1, 1)
	e.move_to(Vector2(4.5, 1.5))
	_run(e, 2.0)
	assert_int(e.phase).is_equal(E.Phase.LOST)


func test_hostage_follows_the_squad_to_the_tent() -> void:
	var e := BootsEngine.new(_map("..........\n.P...h....\n..........\n.X........", "rescue"), 1, 1)
	e.move_to(Vector2(5.5, 1.6))
	_run(e, 2.5)
	assert_bool(e.hostages[0]["following"]).is_true()
	e.move_to(Vector2(1.5, 3.5))
	_run(e, 5.0)
	assert_bool(e.hostages[0]["rescued"]).is_true()
	assert_int(e.phase).is_equal(E.Phase.WON)


func test_crate_gives_grenades() -> void:
	var e := BootsEngine.new(_map("......\n.P.G..\n......", "none", 0), 1, 1)
	e.move_to(Vector2(3.5, 1.5))
	_run(e, 1.5)
	assert_int(e.grenades).is_equal(4)


func test_same_seed_and_orders_replay_identically() -> void:
	var m := BootsMap.parse_campaign(FileAccess.get_file_as_string("res://games/boots/packs/first-tour/first-tour.boots"))[1]
	var out := []
	for run in 2:
		var mm := BootsMap.parse_campaign(FileAccess.get_file_as_string("res://games/boots/packs/first-tour/first-tour.boots"))[1]
		var e := BootsEngine.new(mm, 17)
		for i in 1800:
			if i % 240 == 0:
				e.move_to(Vector2(3 + (i / 240) % 20, 3 + (i / 120) % 8))
			e.aim = Vector2(20, 8)
			e.firing = i % 90 < 30
			e.tick()
		out.append([e.kills, e.alive_soldiers().size(), e.enemies.size(), e.time])
	assert_array(out[0]).is_equal(out[1])


func test_demo_bot_completes_the_campaign() -> void:
	var text := FileAccess.get_file_as_string("res://games/boots/packs/first-tour/first-tour.boots")
	for mi in BootsMap.parse_campaign(text).size():
		var e := BootsEngine.new(BootsMap.parse_campaign(text)[mi], 1)
		var bot := BootsBot.new()
		var n := 0
		while e.phase == E.Phase.PLAY and n < 60 * 240:
			bot.drive(e)
			e.tick()
			n += 1
		assert_int(e.phase).is_equal(E.Phase.WON)


func test_campaign_pack_loads_with_its_story() -> void:
	var p := Pack.find("boots", "first-tour")
	assert_object(p).is_not_null()
	assert_int(BootsMap.parse_campaign(p.levels_text()).size()).is_equal(3)
	assert_str(p.card_before(0).get("title", "")).is_equal("First Tour")
	assert_bool(p.card_before(2).is_empty()).is_false()
	assert_bool(p.outro.is_empty()).is_false()


func test_every_pack_mission_can_be_won() -> void:
	# the autopilot wins each mission of every shipped pack with one of a few seeds (the maps are playable)
	var packs := Pack.scan("boots")
	assert_int(packs.size()).is_greater_equal(2)
	for p in packs:
		var text := p.levels_text()
		for mi in BootsMap.parse_campaign(text).size():
			var won := false
			for seed in [1, 2, 3]:
				var e := BootsEngine.new(BootsMap.parse_campaign(text)[mi], seed)
				var bot := BootsBot.new()
				var n := 0
				while e.phase == E.Phase.PLAY and n < 60 * 300:
					bot.drive(e)
					e.tick()
					n += 1
				if e.phase == E.Phase.WON:
					won = true
					break
			assert_bool(won).override_failure_message("%s mission %d is not won by the bot" % [p.id, mi + 1]).is_true()
