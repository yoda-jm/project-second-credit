class_name FlagsEngine
extends RefCounted
## The Iron Flags battle: territories, factories, robots, vehicles and guns, at fixed 60 Hz ticks, seeded, so a demo
## replays the same. No base building: plant a robot on a territory's flag and its factories, radar and guns
## change sides; the more territories a team holds, the faster its factories build. Destroy the enemy fort to win.
## The engine knows nothing of the screen: it emits events (shots, hits, deaths, captures) that the view, HUD and
## audio play.

signal event(kind: String, data: Dictionary)

enum Phase { PLAY, WON, LOST }
const T = FlagsMap.T
const Team = FlagsMap.Team
const TICK := 1.0 / 60.0
const MAX_UNITS := 70  ## per team
const FLAG_REACH := 0.75
const FACTORIES := ["fort", "robot_factory", "vehicle_factory"]

## per kind: class, health, speed (tiles/s), range, damage, reload (s), weapon, projectile speed (tiles/s, 0 =
## instant), splash radius, how many come out of the factory, build time (s, with three territories)
const STATS := {
	"grunt": {"cls": "robot", "hp": 40, "speed": 1.5, "range": 5.0, "dmg": 7, "reload": 0.8, "weapon": "rifle", "proj": 0.0, "splash": 0.0, "count": 3, "build": 16.0},
	"psycho": {"cls": "robot", "hp": 45, "speed": 1.7, "range": 4.5, "dmg": 4, "reload": 0.25, "weapon": "smg", "proj": 0.0, "splash": 0.0, "count": 3, "build": 22.0},
	"sniper": {"cls": "robot", "hp": 35, "speed": 1.4, "range": 8.0, "dmg": 26, "reload": 2.0, "weapon": "sniper", "proj": 0.0, "splash": 0.0, "count": 2, "build": 24.0},
	"tough": {"cls": "robot", "hp": 70, "speed": 1.2, "range": 6.0, "dmg": 34, "reload": 2.6, "weapon": "rocket", "proj": 9.0, "splash": 0.8, "count": 2, "build": 28.0},
	"pyro": {"cls": "robot", "hp": 60, "speed": 1.4, "range": 2.6, "dmg": 9, "reload": 0.3, "weapon": "flame", "proj": 0.0, "splash": 0.6, "count": 1, "build": 22.0},
	"laser": {"cls": "robot", "hp": 55, "speed": 1.5, "range": 7.0, "dmg": 22, "reload": 1.1, "weapon": "laser", "proj": 0.0, "splash": 0.0, "count": 1, "build": 30.0},
	"jeep": {"cls": "vehicle", "hp": 90, "speed": 3.4, "range": 5.0, "dmg": 5, "reload": 0.22, "weapon": "smg", "proj": 0.0, "splash": 0.0, "count": 1, "build": 20.0},
	"tank_light": {"cls": "vehicle", "hp": 160, "speed": 2.3, "range": 6.0, "dmg": 20, "reload": 1.5, "weapon": "tank_gun", "proj": 14.0, "splash": 0.6, "count": 1, "build": 30.0},
	"tank_medium": {"cls": "vehicle", "hp": 240, "speed": 1.9, "range": 6.5, "dmg": 30, "reload": 1.8, "weapon": "tank_gun", "proj": 14.0, "splash": 0.7, "count": 1, "build": 40.0},
	"tank_heavy": {"cls": "vehicle", "hp": 340, "speed": 1.5, "range": 7.0, "dmg": 42, "reload": 2.2, "weapon": "tank_gun", "proj": 14.0, "splash": 0.9, "count": 1, "build": 52.0},
	"apc": {"cls": "vehicle", "hp": 220, "speed": 2.2, "range": 5.0, "dmg": 6, "reload": 0.3, "weapon": "smg", "proj": 0.0, "splash": 0.0, "count": 1, "build": 34.0},
	"missile_launcher": {"cls": "vehicle", "hp": 150, "speed": 1.7, "range": 10.0, "dmg": 55, "reload": 4.0, "weapon": "missile", "proj": 8.0, "splash": 1.2, "count": 1, "build": 48.0},
	"gatling": {"cls": "cannon", "hp": 220, "speed": 0.0, "range": 6.0, "dmg": 5, "reload": 0.18, "weapon": "gatling", "proj": 0.0, "splash": 0.0, "count": 1, "build": 0.0},
	"gun": {"cls": "cannon", "hp": 260, "speed": 0.0, "range": 7.0, "dmg": 26, "reload": 1.6, "weapon": "tank_gun", "proj": 14.0, "splash": 0.6, "count": 1, "build": 0.0},
	"howitzer": {"cls": "cannon", "hp": 260, "speed": 0.0, "range": 11.0, "dmg": 40, "reload": 3.5, "weapon": "howitzer", "proj": 7.0, "splash": 1.2, "count": 1, "build": 0.0},
	"missile": {"cls": "cannon", "hp": 240, "speed": 0.0, "range": 9.0, "dmg": 45, "reload": 3.0, "weapon": "missile", "proj": 8.0, "splash": 1.0, "count": 1, "build": 0.0},
}
const BUILDING_HP := {"fort": 4000, "robot_factory": 700, "vehicle_factory": 700, "radar": 400, "repair": 500, "hut": 150}
const ROBOT_BUILDS := ["grunt", "psycho", "sniper", "tough", "pyro", "laser"]
const VEHICLE_BUILDS := ["jeep", "tank_light", "tank_medium", "tank_heavy", "apc", "missile_launcher"]

var map: FlagsMap
var rng := RandomNumberGenerator.new()
var phase := Phase.PLAY
var ticks := 0
var time := 0.0
var units: Array[Dictionary] = []
var buildings: Array[Dictionary] = []
var zones: Array[Dictionary] = []
var items: Array[Dictionary] = []
var grid := AStarGrid2D.new()
var stats := {Team.RED: {"built": 0, "lost": 0, "kills": 0, "captures": 0}, Team.BLUE: {"built": 0, "lost": 0, "kills": 0, "captures": 0}}
var _by_id := {}
var _next_id := 1
var _next_group := 1
var _hits: Array[Dictionary] = []
var _occupied := {}  ## cell -> unit count, rebuilt every few ticks, for spreading orders
var _rock_hits := {}  ## cell -> heavy hits taken
var _count := {Team.RED: 0, Team.BLUE: 0}  ## living units per team, counted twice a second
var _present := {}  ## team -> it had a fort or an army at the start (only such a team can be beaten)


func _init(m: FlagsMap, seed_: int) -> void:
	map = m
	rng.seed = seed_
	grid.region = Rect2i(0, 0, m.w, m.h)
	grid.cell_size = Vector2.ONE
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.jumping_enabled = true  # jump point search: paths across big maps stay cheap (tile costs are ignored)
	grid.update()
	for y in m.h:
		for x in m.w:
			var c := Vector2i(x, y)
			if not passable(c):
				grid.set_point_solid(c)
			elif m.at(c) == T.ROUGH:
				grid.set_point_weight_scale(c, 1.6)
			elif m.at(c) == T.ROAD or m.at(c) == T.BRIDGE:
				grid.set_point_weight_scale(c, 0.8)
	for z in m.zones:
		zones.append({"rect": z["rect"], "flag": z["flag"], "owner": z["owner"]})
	for b in m.buildings:
		var bd := {"id": _new_id(), "kind": b["kind"], "team": b["team"], "cell": b["cell"], "size": b["size"],
			"hp": BUILDING_HP[b["kind"]], "max_hp": BUILDING_HP[b["kind"]], "zone": m.zone_at(b["cell"] + b["size"] / 2),
			"build": _default_build(b["kind"]), "progress": 0.0, "destroyed": false}
		buildings.append(bd)
		_by_id[bd["id"]] = bd
		for y in b["size"].y:
			for x in b["size"].x:
				var c: Vector2i = b["cell"] + Vector2i(x, y)
				if m.inside(c) and (y < b["size"].y - 1 or b["kind"] == "hut" or b["kind"] == "radar"):
					grid.set_point_solid(c)  # the front row stays open: the doors and the ramp
	for u in m.units:
		if u["cls"] == "cannon":  # guns stand on 2x2 tiles
			for y in 2:
				for x in 2:
					if m.inside(u["cell"] + Vector2i(x, y)):
						grid.set_point_solid(u["cell"] + Vector2i(x, y))
		if STATS.has(u["kind"]):
			_spawn(u["kind"], u["team"], Vector2(u["cell"]) + Vector2(0.5, 0.5) if u["cls"] != "cannon" else Vector2(u["cell"]) + Vector2.ONE, _next_group)
			_next_group += 1
	for team in [Team.RED, Team.BLUE]:
		_present[team] = not fort_of(team).is_empty() or not team_units(team).is_empty()
	for it in m.items:
		items.append({"kind": it["kind"], "cell": it["cell"], "taken": false})


func _new_id() -> int:
	_next_id += 1
	return _next_id - 1


static func _default_build(kind: String) -> String:
	match kind:
		"robot_factory", "fort": return "grunt"
		"vehicle_factory": return "jeep"
	return ""


func passable(c: Vector2i) -> bool:
	var t := map.at(c)
	return t != T.WATER and t != T.ROCK and t != T.LAVA


func by_id(id: int) -> Dictionary:
	return _by_id.get(id, {})


func alive(id: int) -> bool:
	var u: Dictionary = _by_id.get(id, {})
	return not u.is_empty() and not u.get("dead", false) and not u.get("destroyed", false)


func fort_of(team: int) -> Dictionary:
	for b in buildings:
		if b["kind"] == "fort" and b["team"] == team:
			return b
	return {}


func zones_owned(team: int) -> int:
	return zones.filter(func(z): return z["owner"] == team).size()


func team_units(team: int, cls := "") -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for u in units:
		if u["team"] == team and not u["dead"] and (cls == "" or u["cls"] == cls):
			out.append(u)
	return out


## How much faster than normal the team's factories build: slow with one territory, quick with many.
func production_rate(team: int) -> float:
	return clampf(0.55 + 0.15 * zones_owned(team), 0.6, 2.4)


func _spawn(kind: String, team: int, pos: Vector2, group: int) -> Dictionary:
	var s: Dictionary = STATS[kind]
	var u := {"id": _new_id(), "team": team, "cls": s["cls"], "kind": kind, "pos": pos, "hp": s["hp"], "max_hp": s["hp"],
		"facing": PI * 0.5 if team == Team.BLUE else -PI * 0.5, "aim": 0.0, "path": [], "order": "", "goal": Vector2i(-1, -1),
		"target": -1, "forced": -1, "cool": rng.randf_range(0.0, 0.5), "dead": false, "group": group, "moving": false,
		"ammo": "", "ammo_left": 0, "firing": 0.0}
	u["aim"] = u["facing"]
	units.append(u)
	_by_id[u["id"]] = u
	event.emit("spawn", {"id": u["id"]})
	return u


# ------------------------------------------------------------------ orders

## Sends units to a cell; each gets its own free cell near it. Robots reaching a flag capture it on the way.
func order_move(ids: Array, cell: Vector2i, forced := true) -> void:
	var movers: Array[Dictionary] = []
	for id in ids:
		var u := by_id(id)
		if not u.is_empty() and not u["dead"] and u["cls"] != "cannon" and u["team"] != Team.NEUTRAL:
			movers.append(u)
	var spots := _spread(cell, movers.size())
	for i in movers.size():
		var u := movers[i]
		u["order"] = "move"
		u["forced"] = -1
		u["target"] = -1 if forced else u["target"]
		_path_to(u, spots[i])


## Sends units after a target (a unit or a building).
func order_attack(ids: Array, target_id: int) -> void:
	var t := by_id(target_id)
	if t.is_empty():
		return
	for id in ids:
		var u := by_id(id)
		if u.is_empty() or u["dead"] or u["cls"] == "cannon":
			continue
		u["order"] = "attack"
		u["forced"] = target_id
		u["target"] = target_id
		_path_to(u, _cell_of(t))


func set_build(building_id: int, kind: String) -> void:
	var b := by_id(building_id)
	if b.is_empty() or not STATS.has(kind):
		return
	var robot: bool = STATS[kind]["cls"] == "robot"
	if (b["kind"] == "vehicle_factory") == robot or not b["kind"] in FACTORIES:
		return
	if b["build"] != kind:
		b["build"] = kind
		b["progress"] = 0.0


func _cell_of(t: Dictionary) -> Vector2i:
	if t.has("size"):
		return t["cell"] + Vector2i(t["size"].x / 2, t["size"].y)
	return Vector2i(t["pos"].floor())


func _center(t: Dictionary) -> Vector2:
	if t.has("size"):
		return Vector2(t["cell"]) + Vector2(t["size"]) * 0.5
	return t["pos"]


## n free cells around c, nearest first.
func _spread(c: Vector2i, n: int) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var r := 0
	while out.size() < n and r < 12:
		for y in range(-r, r + 1):
			for x in range(-r, r + 1):
				if maxi(absi(x), absi(y)) != r:
					continue
				var cc := c + Vector2i(x, y)
				if grid.is_in_boundsv(cc) and not grid.is_point_solid(cc) and out.size() < n:
					out.append(cc)
		r += 1
	while out.size() < n:
		out.append(c)
	return out


func _nearest_free(c: Vector2i) -> Vector2i:
	return _spread(c, 1)[0]


func _path_to(u: Dictionary, cell: Vector2i) -> void:
	var from := _nearest_free(Vector2i(u["pos"].floor()))
	var to := _nearest_free(cell)
	var p := grid.get_id_path(from, to, true)
	u["path"] = []
	for i in range(1, p.size()):
		u["path"].append(p[i])
	u["goal"] = to
	u["moving"] = not u["path"].is_empty()


# ------------------------------------------------------------------ the tick

func tick() -> void:
	if phase != Phase.PLAY:
		ticks += 1
		time += TICK
		return
	ticks += 1
	time += TICK
	if ticks % 30 == 1:
		_count = {Team.RED: team_units(Team.RED).size(), Team.BLUE: team_units(Team.BLUE).size(), Team.NEUTRAL: 0}
	if ticks % 6 == 0:
		_occupied.clear()
		for u in units:
			if not u["dead"]:
				var c := Vector2i(u["pos"].floor())
				_occupied[c] = _occupied.get(c, 0) + 1
	for b in buildings:
		_produce(b)
		if b["kind"] == "fort" and not b["destroyed"]:
			_fort_guns(b)
	for u in units:
		if not u["dead"]:
			_think(u)
	_separate()
	_resolve_hits()
	_pickups()
	if ticks % 30 == 0:
		_repair()
		_check_end()
	if ticks % 120 == 0:
		units = units.filter(func(u): return not u["dead"] or ticks - u.get("died", ticks) < 600)


func _produce(b: Dictionary) -> void:
	if b["destroyed"] or b["team"] == Team.NEUTRAL or not b["kind"] in FACTORIES or b["build"] == "":
		return
	if _count.get(b["team"], 0) >= MAX_UNITS:
		return
	var s: Dictionary = STATS[b["build"]]
	var secs: float = s["build"] * (1.3 if b["kind"] == "fort" else 1.0)
	b["progress"] += TICK * production_rate(b["team"]) / secs
	if b["progress"] < 1.0:
		return
	b["progress"] = 0.0
	var door: Vector2i = b["cell"] + Vector2i(b["size"].x / 2, b["size"].y)
	var spots := _spread(door + Vector2i(0, 1), s["count"])
	var group := _next_group
	_next_group += 1
	var ids: Array[int] = []
	for i in s["count"]:
		var u := _spawn(b["build"], b["team"], Vector2(door) + Vector2(0.5, -0.2) + Vector2(i * 0.3 - 0.3, 0), group)
		ids.append(u["id"])
		u["order"] = "move"
		_path_to(u, spots[i])
	stats[b["team"]]["built"] += s["count"]
	event.emit("produced", {"building": b["id"], "team": b["team"], "kind": b["build"], "ids": ids})


## The fort defends itself: two heavy guns on its towers.
func _fort_guns(b: Dictionary) -> void:
	b["cool"] = b.get("cool", 1.0) - TICK
	if b["cool"] > 0.0:
		return
	b["cool"] = 0.3
	var r := Rect2(Vector2(b["cell"]), Vector2(b["size"]))
	var best := {}
	var bd := 6.5
	for o in units:
		if o["dead"] or o["team"] == b["team"] or o["team"] == Team.NEUTRAL:
			continue
		var d: float = o["pos"].distance_to(o["pos"].clamp(r.position, r.end))
		if d < bd:
			bd = d
			best = o
	if best.is_empty():
		return
	b["cool"] = 1.4
	var from: Vector2 = best["pos"].clamp(r.position + Vector2(1, 1), r.end - Vector2(1, 1))
	var to: Vector2 = best["pos"] + Vector2(rng.randf_range(-0.3, 0.3), rng.randf_range(-0.3, 0.3))
	_hits.append({"tick": ticks + maxi(1, int(from.distance_to(to) / 14.0 / TICK)), "target": best["id"], "pos": to, "dmg": 30.0,
		"splash": 0.7, "team": b["team"], "from": b["id"], "weapon": "tank_gun"})
	event.emit("shot", {"id": b["id"], "target": best["id"], "from": from, "to": to, "weapon": "tank_gun", "time": from.distance_to(to) / 14.0, "fort": true})


func _think(u: Dictionary) -> void:
	var s: Dictionary = STATS[u["kind"]]
	u["cool"] -= TICK
	u["firing"] = maxf(0.0, u["firing"] - TICK)
	if u["team"] == Team.NEUTRAL:
		return  # an empty vehicle or an unmanned gun waits for a crew
	# targets: a forced one, else the nearest enemy in reach (looked for a few times a second)
	if u["forced"] >= 0 and not alive(u["forced"]):
		u["forced"] = -1
		if u["order"] == "attack":
			u["order"] = ""
	if u["forced"] >= 0:
		u["target"] = u["forced"]
	elif u["target"] >= 0 and (not alive(u["target"]) or _dist(u, by_id(u["target"])) > s["range"] + 1.5 or by_id(u["target"])["team"] == u["team"]):
		u["target"] = -1
	if u["target"] < 0 and (ticks + u["id"]) % 12 == 0:
		u["target"] = _find_target(u, s["range"] + 0.5)
	var t := by_id(u["target"]) if u["target"] >= 0 else {}
	var in_range: bool = not t.is_empty() and _dist(u, t) <= s["range"]
	# moving: follow the path; stop to shoot unless the order was a plain move
	if u["cls"] != "cannon":
		if u["order"] == "attack" and not t.is_empty() and not in_range and ticks % 45 == u["id"] % 45 \
				and (u["path"].is_empty() or Vector2(_cell_of(t)).distance_to(Vector2(u["goal"])) > 2.5):
			_path_to(u, _cell_of(t))
		var stop: bool = in_range and u["order"] != "move"
		if u["moving"] and not stop:
			_step(u, s)
		elif u["path"].is_empty():
			u["moving"] = false
			if u["order"] == "move":
				u["order"] = ""
		if u["cls"] == "robot" and (ticks + u["id"]) % 6 == 0:
			_capture(u)
			_board(u)
	# aim and fire
	if in_range:
		var want: float = (_center(t) - u["pos"]).angle()
		if u["cls"] == "robot":
			u["facing"] = want
			u["aim"] = want
		else:
			u["aim"] = rotate_toward(u["aim"], want, TICK * (5.0 if u["cls"] == "cannon" else 3.5))
		if u["cool"] <= 0.0 and absf(angle_difference(u["aim"], want)) < 0.2:
			_fire(u, t, s)
	elif u["cls"] == "vehicle":
		u["aim"] = rotate_toward(u["aim"], u["facing"], TICK * 2.0)


func _step(u: Dictionary, s: Dictionary) -> void:
	if u["path"].is_empty():
		u["moving"] = false
		return
	var next: Vector2i = u["path"][0]
	var target: Vector2 = Vector2(next) + Vector2(0.5, 0.5)
	var d: Vector2 = target - u["pos"]
	var terrain := map.at(Vector2i(u["pos"].floor()))
	var speed: float = s["speed"]
	if terrain == T.ROUGH:
		speed *= 0.65
	elif (terrain == T.ROAD or terrain == T.BRIDGE) and u["cls"] == "vehicle":
		speed *= 1.25
	var want: float = d.angle()
	if u["cls"] == "vehicle":  # tracks turn before they go
		u["facing"] = rotate_toward(u["facing"], want, TICK * 4.5)
		if absf(angle_difference(u["facing"], want)) > 0.9:
			return
	else:
		u["facing"] = rotate_toward(u["facing"], want, TICK * 12.0)
	var step := speed * TICK
	if d.length() <= step:
		u["pos"] = target
		u["path"].pop_front()
		if u["path"].is_empty():
			u["moving"] = false
	else:
		u["pos"] += d.normalized() * step


func _dist(u: Dictionary, t: Dictionary) -> float:
	if t.has("size"):  # to the nearest point of a building
		var r := Rect2(Vector2(t["cell"]), Vector2(t["size"]))
		var p: Vector2 = u["pos"].clamp(r.position, r.end)
		return u["pos"].distance_to(p)
	return u["pos"].distance_to(t["pos"])


func _find_target(u: Dictionary, reach: float) -> int:
	var best := -1
	var bd := reach
	for o in units:
		if o["dead"] or o["team"] == u["team"] or o["team"] == Team.NEUTRAL:
			continue
		var d: float = u["pos"].distance_to(o["pos"])
		if o["cls"] == "robot" and u["kind"] == "missile_launcher":
			d += 3.0  # missiles are wasted on robots
		if d < bd:
			bd = d
			best = o["id"]
	if best < 0:
		for b in buildings:
			if b["kind"] == "fort" and b["team"] != u["team"] and not b["destroyed"] and _dist(u, b) < reach:
				return b["id"]
	return best


func _fire(u: Dictionary, t: Dictionary, s: Dictionary) -> void:
	u["cool"] = s["reload"] * rng.randf_range(0.9, 1.1)
	u["firing"] = 0.25
	var weapon: String = s["weapon"]
	var dmg: float = s["dmg"]
	var splash: float = s["splash"]
	var proj: float = s["proj"]
	if u["ammo_left"] > 0:  # crates: grenades or rockets for a few shots
		u["ammo_left"] -= 1
		weapon = "grenade" if u["ammo"] == "grenades" else "rocket"
		dmg = 28.0
		splash = 1.0
		proj = 7.0 if u["ammo"] == "grenades" else 9.0
	var to := _center(t)
	if t.has("size"):
		var r := Rect2(Vector2(t["cell"]), Vector2(t["size"]))
		to = u["pos"].clamp(r.position + Vector2(1, 1), r.end - Vector2(1, 1))
	var spread := 0.0 if splash == 0.0 else 0.35
	to += Vector2(rng.randf_range(-spread, spread), rng.randf_range(-spread, spread))
	var from: Vector2 = u["pos"]
	var delay := 0.06 if proj == 0.0 else from.distance_to(to) / proj
	_hits.append({"tick": ticks + maxi(1, int(delay / TICK)), "target": t["id"], "pos": to, "dmg": dmg, "splash": splash,
		"team": u["team"], "from": u["id"], "weapon": weapon})
	event.emit("shot", {"id": u["id"], "target": t["id"], "from": from, "to": to, "weapon": weapon, "time": delay})


func _resolve_hits() -> void:
	var due: Array[Dictionary] = []
	var keep: Array[Dictionary] = []
	for h in _hits:
		if h["tick"] <= ticks:
			due.append(h)
		else:
			keep.append(h)
	_hits = keep
	for h in due:
		if h["splash"] > 0.0:
			event.emit("blast", {"pos": h["pos"], "radius": h["splash"], "weapon": h["weapon"]})
			for o in units:
				if not o["dead"] and o["team"] != h["team"] and o["team"] != Team.NEUTRAL:
					var d: float = o["pos"].distance_to(h["pos"])
					if d < h["splash"] + 0.3:
						_damage(o, h["dmg"] * (1.0 if o["id"] == h["target"] else clampf(1.0 - d / (h["splash"] + 0.3), 0.2, 0.8)), h)
			var b := by_id(h["target"])
			if not b.is_empty() and b.has("size"):
				_damage(b, h["dmg"], h)
			if h["weapon"] in ["rocket", "tank_gun", "howitzer", "missile", "grenade"]:
				_blast_rock(Vector2i(h["pos"].floor()))
		else:
			var t := by_id(h["target"])
			if not t.is_empty() and alive(h["target"]):
				_damage(t, h["dmg"], h)
				event.emit("hit", {"id": h["target"], "pos": h["pos"], "weapon": h["weapon"]})


## Heavy shells chip at rock walls: a rock tile hit three times crumbles and opens the way.
func _blast_rock(c: Vector2i) -> void:
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var cc := c + Vector2i(dx, dy)
			if map.at(cc) == T.ROCK and map.inside(cc) and (dx == 0 or dy == 0):
				var n: int = _rock_hits.get(cc, 0) + 1
				_rock_hits[cc] = n
				if n >= 3 and cc.x > 0 and cc.y > 0 and cc.x < map.w - 1 and cc.y < map.h - 1:
					map.set_at(cc, T.ROUGH)
					grid.set_point_solid(cc, false)
					grid.set_point_weight_scale(cc, 1.6)
					event.emit("rock_destroyed", {"cell": cc})
				return


func _damage(t: Dictionary, dmg: float, h: Dictionary) -> void:
	if t.get("dead", false) or t.get("destroyed", false):
		return
	t["hp"] -= dmg
	if t.has("size"):
		if t["kind"] == "fort":
			event.emit("fort_hit", {"id": t["id"], "team": t["team"]})
		if t["hp"] <= 0:
			t["hp"] = 0
			if t["kind"] == "fort":
				t["destroyed"] = true
				event.emit("destroyed", {"id": t["id"], "team": t["team"]})
				_end(Team.RED if t["team"] == Team.BLUE else Team.BLUE)
			else:
				t["hp"] = 1  # other buildings are taken, not razed
		return
	if t["hp"] <= 0:
		t["dead"] = true
		t["died"] = ticks
		t["moving"] = false
		stats[t["team"]]["lost"] += 1
		if stats.has(h["team"]):
			stats[h["team"]]["kills"] += 1
		event.emit("death", {"id": t["id"], "team": t["team"], "cls": t["cls"], "kind": t["kind"], "pos": t["pos"], "weapon": h["weapon"]})
		if t["cls"] == "cannon":  # a wrecked gun is rebuilt when the zone changes hands
			pass


func _capture(u: Dictionary) -> void:
	for i in zones.size():
		var z: Dictionary = zones[i]
		if z["owner"] == u["team"] or z["flag"].x < 0:
			continue
		var fp := Vector2(z["flag"]) + Vector2(0.5, 0.5)
		if u["pos"].distance_to(fp) < FLAG_REACH:
			if units.any(func(o): return o["cls"] == "robot" and not o["dead"] and o["team"] == z["owner"] and o["pos"].distance_to(fp) < FLAG_REACH + 0.6):
				return  # the owner's robots stand guard on it: no taking it until they fall
			var was: int = z["owner"]
			z["owner"] = u["team"]
			stats[u["team"]]["captures"] += 1
			for b in buildings:
				if b["zone"] == i and b["kind"] != "fort" and b["kind"] != "hut":
					b["team"] = u["team"]
					b["progress"] = 0.0
					b["build"] = _default_build(b["kind"])
					b["hp"] = b["max_hp"]
			for o in units:
				if o["cls"] == "cannon" and map.zone_at(Vector2i(o["pos"].floor())) == i:
					o["team"] = u["team"]
					if o["dead"]:  # the new owner rebuilds wrecked guns
						o["dead"] = false
						o["hp"] = o["max_hp"]
					o["target"] = -1
			event.emit("capture", {"zone": i, "team": u["team"], "from": was, "by": u["id"]})


func _board(u: Dictionary) -> void:
	for o in units:
		if o["cls"] == "vehicle" and o["team"] == Team.NEUTRAL and not o["dead"] and u["pos"].distance_to(o["pos"]) < 0.9:
			o["team"] = u["team"]
			o["group"] = _next_group
			_next_group += 1
			u["dead"] = true
			u["died"] = ticks
			event.emit("board", {"robot": u["id"], "vehicle": o["id"], "team": u["team"]})
			return


func _pickups() -> void:
	if ticks % 10 != 0:
		return
	for it in items:
		if it["taken"]:
			continue
		for u in units:
			if u["cls"] == "robot" and not u["dead"] and u["team"] != Team.NEUTRAL and u["pos"].distance_to(Vector2(it["cell"]) + Vector2(0.5, 0.5)) < 0.8:
				it["taken"] = true
				for o in units:
					if o["group"] == u["group"] and not o["dead"]:
						o["ammo"] = it["kind"]
						o["ammo_left"] = 6
				event.emit("pickup", {"kind": it["kind"], "cell": it["cell"], "team": u["team"]})
				break


func _repair() -> void:
	for b in buildings:
		if b["kind"] != "repair" or b["team"] == Team.NEUTRAL:
			continue
		var c := Vector2(b["cell"]) + Vector2(b["size"]) * 0.5
		for u in units:
			if u["cls"] == "vehicle" and u["team"] == b["team"] and not u["dead"] and u["pos"].distance_to(c) < 4.0 and u["hp"] < u["max_hp"]:
				u["hp"] = minf(u["max_hp"], u["hp"] + 6.0)
				event.emit("repaired", {"id": u["id"]})


## Units of one side keep a little apart so a squad reads as a squad, not a pile.
func _separate() -> void:
	if ticks % 2 != 0:
		return
	var buckets := {}
	for u in units:
		if not u["dead"] and u["cls"] != "cannon":
			var k := Vector2i(u["pos"].floor())
			if not buckets.has(k):
				buckets[k] = []
			buckets[k].append(u)
	for k in buckets:
		var here: Array = buckets[k]
		var near: Array = []
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				near.append_array(buckets.get(k + Vector2i(dx, dy), []))
		for a in here:
			if a["team"] == Team.NEUTRAL:
				continue
			var push := Vector2.ZERO
			for b in near:
				if a["id"] == b["id"]:
					continue
				var d: Vector2 = a["pos"] - b["pos"]
				var r := 0.42 if a["cls"] == "robot" and b["cls"] == "robot" else 0.8
				var l := d.length()
				if l < r:
					push += (d / maxf(l, 0.01) if l > 0.001 else Vector2(cos(a["id"]), sin(a["id"]))) * (r - l)
			if push != Vector2.ZERO:
				var np: Vector2 = a["pos"] + push.limit_length(0.05)
				if passable(Vector2i(np.floor())) and not grid.is_point_solid(Vector2i(np.floor())):
					a["pos"] = np


func _check_end() -> void:
	for team in [Team.RED, Team.BLUE]:
		var f := fort_of(team)
		if not _present[team] or not f.is_empty() and f["destroyed"]:
			continue
		var has_units := team_units(team).filter(func(u): return u["cls"] != "cannon").size() > 0
		var has_factories := buildings.any(func(b): return b["team"] == team and b["kind"] in FACTORIES and not b["destroyed"])
		if not has_units and not has_factories:
			_end(Team.RED if team == Team.BLUE else Team.BLUE)


func _end(winner: int) -> void:
	if phase != Phase.PLAY:
		return
	phase = Phase.WON if winner == Team.RED else Phase.LOST
	event.emit("won" if winner == Team.RED else "lost", {"winner": winner})
