class_name FlagsMap
extends RefCounted
## An Iron Flags battlefield: terrain tiles, territories (each with its flag), and what stands on them.
## Our own text format (a campaign file holds several maps, each starting with [map]):
##
##   [map]
##   name=Dust Bowl
##   planet=desert           desert, volcanic, arctic, jungle or city
##   ....==..~~~..##..       the grid, one line per row (no spaces in a grid line)
##   zone 0 0 16 12          a territory: x y w h in tiles (a tile belongs to the first zone that holds it)
##   flag 8 6                the territory's flag (the zone holding this tile)
##   fort red 3 2            buildings: fort, robot_factory, vehicle_factory, radar, repair, hut; team x y (top-left)
##   cannon gatling blue 20 5    cannons: gatling, gun, howitzer, missile
##   robot grunt red 6 14        robots: grunt, psycho, sniper, tough, pyro, laser
##   vehicle jeep neutral 9 9    vehicles: jeep, tank_light, tank_medium, tank_heavy, apc, missile_launcher
##   crate grenades 10 11        crates: grenades, rockets
##   prop palm 4 4               decoration: palm, pine, dead_tree, cactus, crystal, bush, ruin_pillar, street_lamp
##
## Terrain: . ground   = road   ~ water   # rock (blocks, can be blasted)   : rough (slows)   b bridge   % lava
## Teams: neutral, red (the player), blue (the computer).
## The Zod Engine's maps are read by ZodImport into the same structure.

enum T { GROUND, ROAD, WATER, ROCK, ROUGH, BRIDGE, LAVA }
enum Team { NEUTRAL, RED, BLUE }

const TERRAIN_CHARS := {".": T.GROUND, "=": T.ROAD, "~": T.WATER, "#": T.ROCK, ":": T.ROUGH, "b": T.BRIDGE, "%": T.LAVA}
const TEAM_NAMES := {"neutral": Team.NEUTRAL, "red": Team.RED, "blue": Team.BLUE}
const PLANETS := ["desert", "volcanic", "arctic", "jungle", "city"]
const BUILDING_SIZE := {"fort": Vector2i(10, 12), "robot_factory": Vector2i(4, 5), "vehicle_factory": Vector2i(4, 5),
	"radar": Vector2i(4, 3), "repair": Vector2i(5, 4), "hut": Vector2i(2, 2)}
const ROBOTS := ["grunt", "psycho", "sniper", "tough", "pyro", "laser"]
const VEHICLES := ["jeep", "tank_light", "tank_medium", "tank_heavy", "apc", "missile_launcher"]
const CANNONS := ["gatling", "gun", "howitzer", "missile"]

var name := ""
var planet := "desert"
var w := 0
var h := 0
var terrain := PackedByteArray()
var zones: Array[Dictionary] = []    ## {rect: Rect2i, flag: Vector2i (or -1,-1), owner: Team}
var buildings: Array[Dictionary] = []  ## {kind, team, cell: Vector2i, size: Vector2i}
var units: Array[Dictionary] = []    ## {cls: robot|vehicle|cannon, kind, team, cell}
var items: Array[Dictionary] = []    ## {kind: grenades|rockets, cell}
var props: Array[Dictionary] = []    ## {kind, cell}
var source := "text"  ## "text" or "zod"


static func parse_campaign(text: String) -> Array[FlagsMap]:
	var out: Array[FlagsMap] = []
	var cur := ""
	for raw in text.split("\n"):
		if raw.strip_edges().to_lower() == "[map]":
			if cur.strip_edges() != "":
				out.append(parse(cur))
			cur = ""
			continue
		cur += raw + "\n"
	if cur.strip_edges() != "":
		out.append(parse(cur))
	return out.filter(func(m): return m.w > 0)


static func team_of(s: String) -> int:
	return TEAM_NAMES.get(s.to_lower(), Team.NEUTRAL)


static func parse(text: String) -> FlagsMap:
	var m := FlagsMap.new()
	var rows := PackedStringArray()
	var flags: Array[Vector2i] = []
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.is_empty() or line.begins_with(";") or line.begins_with("["):
			continue
		if line.begins_with("name=") or line.begins_with("planet="):
			var kv := line.split("=", true, 1)
			if kv[0] == "name":
				m.name = kv[1].strip_edges()
			else:
				m.planet = kv[1].strip_edges() if kv[1].strip_edges() in PLANETS else "desert"
			continue
		if not line.contains(" "):
			rows.append(line)
			continue
		var p := line.split(" ", false)
		var n := p.size()
		match p[0]:
			"zone":
				if n >= 5:
					m.zones.append({"rect": Rect2i(p[1].to_int(), p[2].to_int(), p[3].to_int(), p[4].to_int()),
						"flag": Vector2i(-1, -1), "owner": Team.NEUTRAL})
			"flag":
				if n >= 3:
					flags.append(Vector2i(p[1].to_int(), p[2].to_int()))
			"fort", "robot_factory", "vehicle_factory", "radar", "repair", "hut":
				if n >= 4:
					m.buildings.append({"kind": p[0], "team": team_of(p[1]), "cell": Vector2i(p[2].to_int(), p[3].to_int()),
						"size": BUILDING_SIZE[p[0]]})
			"cannon", "robot", "vehicle":
				if n >= 5:
					m.units.append({"cls": p[0], "kind": p[1], "team": team_of(p[2]), "cell": Vector2i(p[3].to_int(), p[4].to_int())})
			"crate":
				if n >= 4:
					m.items.append({"kind": p[1], "cell": Vector2i(p[2].to_int(), p[3].to_int())})
			"prop":
				if n >= 4:
					m.props.append({"kind": p[1], "cell": Vector2i(p[2].to_int(), p[3].to_int())})
	m.h = rows.size()
	m.w = 0
	for r in rows:
		m.w = maxi(m.w, r.length())
	m.terrain.resize(m.w * m.h)
	for y in m.h:
		for x in m.w:
			var c := rows[y][x] if x < rows[y].length() else "."
			m.terrain[y * m.w + x] = TERRAIN_CHARS.get(c, T.GROUND)
	for f in flags:
		m.set_flag(f)
	m.settle_owners()
	return m


## Gives the flag at c to the zone holding it.
func set_flag(c: Vector2i) -> void:
	var z := zone_at(c)
	if z >= 0 and zones[z]["flag"] == Vector2i(-1, -1):
		zones[z]["flag"] = c


## A zone belongs to the team whose fort stands in it, else to the team of the other buildings, cannons or
## units in it (the map's starting position). Buildings and cannons then take their zone's owner.
func settle_owners() -> void:
	for z in zones.size():
		var owner := Team.NEUTRAL
		for b in buildings:
			if zone_at(b["cell"] + b["size"] / 2) == z and b["team"] != Team.NEUTRAL:
				if b["kind"] == "fort" or owner == Team.NEUTRAL:
					owner = b["team"]
		if owner == Team.NEUTRAL:
			for u in units:
				if u["cls"] == "cannon" and u["team"] != Team.NEUTRAL and zone_at(u["cell"]) == z:
					owner = u["team"]
		zones[z]["owner"] = owner
	for b in buildings:
		var z := zone_at(b["cell"] + b["size"] / 2)
		if z >= 0 and b["kind"] != "fort" and b["kind"] != "hut":
			b["team"] = zones[z]["owner"]
	for u in units:
		if u["cls"] == "cannon":
			var z := zone_at(u["cell"])
			if z >= 0:
				u["team"] = zones[z]["owner"]


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < w and c.y < h


func at(c: Vector2i) -> int:
	return terrain[c.y * w + c.x] if inside(c) else T.ROCK


func set_at(c: Vector2i, t: int) -> void:
	if inside(c):
		terrain[c.y * w + c.x] = t


func zone_at(c: Vector2i) -> int:
	for i in zones.size():
		if zones[i]["rect"].has_point(c):
			return i
	return -1


func count(kind: String) -> int:
	return buildings.filter(func(b): return b["kind"] == kind).size()
