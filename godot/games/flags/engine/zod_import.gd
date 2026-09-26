class_name ZodImport
extends RefCounted
## Reads a Zod Engine map (.map) from the player's own files, locally, with the planet's .tileinfo table (the
## terrain of each of its 480 tiles). Nothing is shipped or copied; the result is a FlagsMap in memory.
##
## The format, as written by the Zod Engine (GPL-3.0, zod.sourceforge.net; src/zmap.h), all little-endian, packed:
##   map_basics (62 bytes): width u16, height u16, name char[50], player_count u8, pad u8, object_count u16,
##                          terrain_type u8 (desert, volcanic, arctic, jungle, city), pad u8, zone_count u16
##   zone_count zones      x, y, w, h: u16 each, in tiles
##   object_count objects  (16 bytes) x u16, y u16, owner i8 (0 none, 1 red, 2 blue...), object_type u8, object_id u8,
##                         blevel i8, extra_links u16, health_percent i32
##   width * height tiles  u16, an index into the planet's tile palette
##   .tileinfo             480 records of 12 bytes: is_water, is_passable, is_usable, is_road, is_effect,
##                         is_water_effect (bools), next_tile u16, takes_tank_tracks, crater_type i16, is_starter_tile

const T = FlagsMap.T
enum Obj { ROCK, BRIDGE, BUILDING, CANNON, VEHICLE, ROBOT, ANIMAL, MAP_ITEM }
const BUILDINGS := ["fort", "fort", "radar", "repair", "robot_factory", "vehicle_factory", "bridge_vert", "bridge_horz"]
const ROBOTS := ["grunt", "psycho", "sniper", "tough", "pyro", "laser"]
const VEHICLES := ["jeep", "tank_light", "tank_medium", "tank_heavy", "apc", "missile_launcher", "crane"]
const CANNONS := ["gatling", "gun", "howitzer", "missile"]
## decorative map objects (map_object0...21) -> our props, by planet
const PROPS := {"desert": ["cactus", "palm", "ruin_pillar"], "volcanic": ["crystal", "dead_tree", "ruin_pillar"],
	"arctic": ["pine", "dead_tree", "ruin_pillar"], "jungle": ["palm", "bush", "pine"], "city": ["street_lamp", "ruin_pillar", "bush"]}


static func u16(b: PackedByteArray, at: int) -> int:
	return b.decode_u16(at) if at + 1 < b.size() else 0


static func planet_of(b: PackedByteArray) -> String:
	var t := b[58] if b.size() > 58 else 0
	return FlagsMap.PLANETS[t] if t < FlagsMap.PLANETS.size() else "desert"


## tileinfo: the planet's .tileinfo bytes, or empty (then every tile is ground).
static func from_bytes(map_bytes: PackedByteArray, tileinfo: PackedByteArray) -> FlagsMap:
	var m := FlagsMap.new()
	m.source = "zod"
	if map_bytes.size() < 62:
		return m
	var w := u16(map_bytes, 0)
	var h := u16(map_bytes, 2)
	m.name = map_bytes.slice(4, 54).get_string_from_ascii().strip_edges()
	var object_count := u16(map_bytes, 56)
	m.planet = planet_of(map_bytes)
	var zone_count := u16(map_bytes, 60)
	var at := 62
	var need := at + zone_count * 8 + object_count * 16 + w * h * 2
	if w == 0 or h == 0 or map_bytes.size() < need:
		return m
	for i in zone_count:
		m.zones.append({"rect": Rect2i(u16(map_bytes, at), u16(map_bytes, at + 2), u16(map_bytes, at + 4), u16(map_bytes, at + 6)),
			"flag": Vector2i(-1, -1), "owner": FlagsMap.Team.NEUTRAL})
		at += 8
	var objects: Array[Array] = []
	for i in object_count:
		var owner := map_bytes.decode_s8(at + 4)
		objects.append([u16(map_bytes, at), u16(map_bytes, at + 2), owner, map_bytes[at + 5], map_bytes[at + 6], u16(map_bytes, at + 8)])
		at += 16
	# terrain
	m.w = w
	m.h = h
	m.terrain.resize(w * h)
	for i in w * h:
		var tile := u16(map_bytes, at + i * 2)
		var t := T.GROUND
		if tile * 12 + 11 < tileinfo.size():
			var r := tile * 12
			if tileinfo[r] != 0:
				t = T.WATER
			elif tileinfo[r + 1] == 0:
				t = T.LAVA if m.planet == "volcanic" and tileinfo[r + 4] != 0 else T.ROCK
			elif tileinfo[r + 3] != 0:
				t = T.ROAD
		m.terrain[i] = t
	# objects
	var flags: Array[Vector2i] = []
	for o in objects:
		var c := Vector2i(o[0], o[1])
		var team: int = clampi(o[2], 0, 2)  # teams beyond blue play as blue
		if o[2] > 2:
			team = FlagsMap.Team.BLUE
		var id: int = o[4]
		match o[3]:
			Obj.ROCK:
				m.set_at(c, T.ROCK)
			Obj.BUILDING:
				if id >= BUILDINGS.size():
					continue
				var kind: String = BUILDINGS[id]
				if kind.begins_with("bridge"):
					var links: int = o[5] if o[5] < 64 else 0
					var size := Vector2i(4, 5 + links) if kind == "bridge_vert" else Vector2i(5 + links, 4)
					for y in size.y:
						for x in size.x:
							var cc := c + Vector2i(x, y)
							if m.at(cc) == T.WATER or m.at(cc) == T.LAVA or m.at(cc) == T.ROCK:
								m.set_at(cc, T.BRIDGE)
					continue
				var bsize: Vector2i = FlagsMap.BUILDING_SIZE[kind]
				if kind == "fort" and id == 1:
					bsize = Vector2i(10, 11)
				m.buildings.append({"kind": kind, "team": team, "cell": c, "size": bsize})
			Obj.CANNON:
				if id < CANNONS.size():
					m.units.append({"cls": "cannon", "kind": CANNONS[id], "team": team, "cell": c})
			Obj.VEHICLE:
				if id < VEHICLES.size() and VEHICLES[id] != "crane":
					m.units.append({"cls": "vehicle", "kind": VEHICLES[id], "team": team, "cell": c})
			Obj.ROBOT:
				if id < ROBOTS.size():
					m.units.append({"cls": "robot", "kind": ROBOTS[id], "team": team, "cell": c})
			Obj.MAP_ITEM:
				match id:
					0: flags.append(c)
					1: m.set_at(c, T.ROCK)
					2: m.items.append({"kind": "grenades", "cell": c})
					3: m.items.append({"kind": "rockets", "cell": c})
					4: m.buildings.append({"kind": "hut", "team": FlagsMap.Team.NEUTRAL, "cell": c, "size": Vector2i(2, 2)})
					_:
						var pool: Array = PROPS[m.planet]
						m.props.append({"kind": pool[id % pool.size()], "cell": c})
	for f in flags:
		m.set_flag(f)
	m.settle_owners()
	return m


static func from_files(map_path: String, tileinfo_path: String) -> FlagsMap:
	var tb := FileAccess.get_file_as_bytes(tileinfo_path) if FileAccess.file_exists(tileinfo_path) else PackedByteArray()
	return from_bytes(FileAccess.get_file_as_bytes(map_path), tb)
