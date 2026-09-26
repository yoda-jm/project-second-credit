extends GdUnitTestSuite
## Iron Flags: maps, the Zod importer, capturing, production, combat and a whole computer-versus-computer battle.

const E = preload("res://games/flags/engine/flags_engine.gd")
const Team = FlagsMap.Team
const SMALL := """[map]
name=Test
planet=desert
##############################
#............................#
#............................#
#............................#
#............................#
#.............~~.............#
#.............~~.............#
#............................#
#............................#
#............................#
##############################
zone 1 1 14 9
zone 15 1 14 9
flag 7 5
flag 22 5
robot_factory neutral 18 2
"""


func _map(text := SMALL) -> FlagsMap:
	return FlagsMap.parse_campaign(text)[0]


func _run(e: FlagsEngine, seconds: float, ais: Array = []) -> void:
	for i in int(seconds / E.TICK):
		for ai in ais:
			ai.drive(e)
		e.tick()


func test_campaign_parses_and_every_flag_is_reachable() -> void:
	var maps := FlagsMap.parse_campaign(FileAccess.get_file_as_string("res://games/flags/maps/campaign.flags"))
	assert_int(maps.size()).is_equal(3)
	for m in maps:
		assert_int(m.zones.size()).is_greater_equal(6)
		assert_int(m.count("fort")).is_equal(2)
		var e := FlagsEngine.new(m, 1)
		var red := e.fort_of(Team.RED)
		var blue := e.fort_of(Team.BLUE)
		assert_bool(red.is_empty() or blue.is_empty()).is_false()
		var door := e._nearest_free(e._cell_of(red))
		for z in m.zones:
			assert_bool(z["flag"].x >= 0).override_failure_message("%s: a zone without a flag" % m.name).is_true()
			var p := e.grid.get_id_path(door, e._nearest_free(z["flag"]))
			assert_bool(p.size() > 0).override_failure_message("%s: flag %s unreachable" % [m.name, z["flag"]]).is_true()
		assert_int(m.zones[m.zone_at(red["cell"] + red["size"] / 2)]["owner"]).is_equal(Team.RED)


func test_parse_reads_zones_flags_and_buildings() -> void:
	var m := _map()
	assert_int(m.w).is_equal(30)
	assert_int(m.h).is_equal(11)
	assert_int(m.zones.size()).is_equal(2)
	assert_that(m.zones[1]["flag"]).is_equal(Vector2i(22, 5))
	assert_int(m.at(Vector2i(14, 5))).is_equal(FlagsMap.T.WATER)
	assert_int(m.buildings[0]["size"].x).is_equal(4)


func test_a_robot_on_the_flag_takes_the_zone_and_its_factory() -> void:
	var e := FlagsEngine.new(_map(), 3)
	var r := e._spawn("grunt", Team.RED, Vector2(20.5, 5.5), 1)
	var f := e.buildings[0]
	assert_int(f["team"]).is_equal(Team.NEUTRAL)
	e.order_move([r["id"]], Vector2i(22, 5))
	var kinds: Array[String] = []
	e.event.connect(func(k, _d): kinds.append(k))
	_run(e, 3.0)
	assert_int(e.zones[1]["owner"]).is_equal(Team.RED)
	assert_int(f["team"]).is_equal(Team.RED)
	assert_bool(kinds.has("capture")).is_true()


func test_more_territory_builds_faster() -> void:
	var e := FlagsEngine.new(_map(), 3)
	var one := e.production_rate(Team.RED)
	e.zones[0]["owner"] = Team.RED
	e.zones[1]["owner"] = Team.RED
	assert_float(e.production_rate(Team.RED)).is_greater(one)


func test_a_factory_builds_a_squad() -> void:
	var e := FlagsEngine.new(_map(), 3)
	e.buildings[0]["team"] = Team.RED
	e.zones[1]["owner"] = Team.RED
	var made := []
	e.event.connect(func(k, d): if k == "produced": made.append(d))
	_run(e, 30.0)
	assert_int(made.size()).is_greater_equal(1)
	assert_int(made[0]["ids"].size()).is_equal(3)  # grunts come three at a time
	assert_int(e.team_units(Team.RED).size()).is_greater_equal(3)


func test_units_fight_and_die() -> void:
	var e := FlagsEngine.new(_map(), 5)
	var a := e._spawn("tough", Team.RED, Vector2(5.5, 3.5), 1)
	var b := e._spawn("grunt", Team.BLUE, Vector2(9.5, 3.5), 2)
	var deaths := []
	e.event.connect(func(k, d): if k == "death": deaths.append(d["id"]))
	_run(e, 20.0)
	assert_bool(a["dead"] or b["dead"]).is_true()
	assert_int(deaths.size()).is_greater_equal(1)


func test_robots_board_empty_vehicles() -> void:
	var e := FlagsEngine.new(_map(), 5)
	var v := e._spawn("jeep", Team.NEUTRAL, Vector2(6.5, 7.5), 1)
	var r := e._spawn("grunt", Team.RED, Vector2(3.5, 7.5), 2)
	e.order_move([r["id"]], Vector2i(6, 7))
	_run(e, 3.0)
	assert_int(v["team"]).is_equal(Team.RED)
	assert_bool(r["dead"]).is_true()


func test_zod_import_reads_a_synthetic_map() -> void:
	# a 4x3 map, one zone, a flag, a red fort front, a blue grunt; tile 1 is water, tile 2 is rock, tile 3 road
	var b := PackedByteArray()
	b.resize(62)
	b.encode_u16(0, 20)
	b.encode_u16(2, 16)
	var name := "Synthetic".to_ascii_buffer()
	for i in name.size():
		b[4 + i] = name[i]
	b[54] = 2
	b.encode_u16(56, 3)
	b[58] = 2  # arctic
	b.encode_u16(60, 1)
	var z := PackedByteArray()
	z.resize(8)
	z.encode_u16(0, 0)
	z.encode_u16(2, 0)
	z.encode_u16(4, 20)
	z.encode_u16(6, 16)
	b.append_array(z)
	for o in [[3, 3, 0, 7, 0], [5, 2, 1, 2, 0], [15, 10, 2, 5, 0]]:
		var ob := PackedByteArray()
		ob.resize(16)
		ob.encode_u16(0, o[0])
		ob.encode_u16(2, o[1])
		ob.encode_s8(4, o[2])
		ob[5] = o[3]
		ob[6] = o[4]
		b.append_array(ob)
	var tiles := PackedByteArray()
	tiles.resize(20 * 16 * 2)
	tiles.encode_u16((1 * 20 + 1) * 2, 1)
	tiles.encode_u16((1 * 20 + 2) * 2, 2)
	tiles.encode_u16((1 * 20 + 3) * 2, 3)
	b.append_array(tiles)
	var info := PackedByteArray()
	info.resize(480 * 12)
	for i in 480:
		info[i * 12 + 1] = 1  # passable
	info[1 * 12] = 1          # tile 1: water
	info[2 * 12 + 1] = 0      # tile 2: not passable
	info[3 * 12 + 3] = 1      # tile 3: road
	var m := ZodImport.from_bytes(b, info)
	assert_str(m.name).is_equal("Synthetic")
	assert_str(m.planet).is_equal("arctic")
	assert_int(m.w).is_equal(20)
	assert_int(m.at(Vector2i(1, 1))).is_equal(FlagsMap.T.WATER)
	assert_int(m.at(Vector2i(2, 1))).is_equal(FlagsMap.T.ROCK)
	assert_int(m.at(Vector2i(3, 1))).is_equal(FlagsMap.T.ROAD)
	assert_that(m.zones[0]["flag"]).is_equal(Vector2i(3, 3))
	assert_int(m.zones[0]["owner"]).is_equal(Team.RED)
	assert_str(m.buildings[0]["kind"]).is_equal("fort")
	assert_str(m.units[0]["kind"]).is_equal("grunt")
	assert_int(m.units[0]["team"]).is_equal(Team.BLUE)


func test_zod_maps_from_a_local_install_load_when_present() -> void:
	# the player's own Zod Engine files (never shipped); skipped when there are none
	var dir := ProjectSettings.globalize_path("res://").path_join("../.tools/ref/zod")
	if not DirAccess.dir_exists_absolute(dir.path_join("maps")):
		return
	var names := DirAccess.get_files_at(dir.path_join("maps"))
	var loaded := 0
	for n in names:
		if not n.ends_with(".map"):
			continue
		var bytes := FileAccess.get_file_as_bytes(dir.path_join("maps").path_join(n))
		var planet := ZodImport.planet_of(bytes)
		var m := ZodImport.from_files(dir.path_join("maps").path_join(n), dir.path_join("assets/planets/%s.tileinfo" % planet))
		if m.w == 0:
			continue
		loaded += 1
		assert_int(m.zones.size()).is_greater(0)
		var e := FlagsEngine.new(m, 1)
		_run(e, 1.0, [FlagsAI.new(Team.RED, 1), FlagsAI.new(Team.BLUE, 1)])
	assert_int(loaded).is_greater(0)


func test_computer_battle_is_deterministic_and_moves_on() -> void:
	var m1 := FlagsMap.parse_campaign(FileAccess.get_file_as_string("res://games/flags/maps/campaign.flags"))[0]
	var m2 := FlagsMap.parse_campaign(FileAccess.get_file_as_string("res://games/flags/maps/campaign.flags"))[0]
	var e1 := FlagsEngine.new(m1, 9)
	var e2 := FlagsEngine.new(m2, 9)
	_run(e1, 150.0, [FlagsAI.new(Team.RED, 9), FlagsAI.new(Team.BLUE, 9)])
	_run(e2, 150.0, [FlagsAI.new(Team.RED, 9), FlagsAI.new(Team.BLUE, 9)])
	var caps: int = e1.stats[Team.RED]["captures"] + e1.stats[Team.BLUE]["captures"]
	assert_int(caps).is_greater_equal(3)
	assert_int(e1.stats[Team.RED]["kills"] + e1.stats[Team.BLUE]["kills"]).is_greater(0)
	assert_int(e1.units.size()).is_equal(e2.units.size())
	assert_int(e1.stats[Team.RED]["captures"]).is_equal(e2.stats[Team.RED]["captures"])
