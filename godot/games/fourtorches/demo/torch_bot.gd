class_name TorchBot
extends RefCounted
## A Four Torches autopilot for one hero (the demo, and the CPU companions). Each moment: shoot the nearest monster or
## generator lying along one of the eight directions within reach (turning to it); drink a potion when crowded; then
## head over the tile map (a breadth-first route) for food when weak, treasure, keys and potions close by, a door it
## holds a key for, and otherwise the exit, keeping near the others. As a companion to a human player it never leads:
## it picks things up only near that player, leaves the exit and the doors to them, and otherwise walks at their side.

const T = preload("res://games/fourtorches/engine/torch_engine.gd")
const DIRS := [Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1), Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1), Vector2(1, -1)]

var me := 0
var _route: Array[Vector2i] = []
var _goal := Vector2i(-1, -1)
var _replan := 0
var _dist := PackedInt32Array()
var _aim_t := 0
var _shot := Vector2.ZERO
var _door: Array = []          ## the door cell to walk into after the route, if any


func _init(who := 0) -> void:
	me = who


func drive(e: TorchEngine) -> void:
	var h := e.heroes[me]
	h["move"] = Vector2.ZERO
	h["fire"] = false
	h["potion_pressed"] = false
	if e.phase != T.Phase.PLAY or h["dead"]:
		return
	var p: Vector2 = h["pos"]
	# crowded: a potion
	var near := 0
	for m in e.monsters:
		if (m["pos"] as Vector2).distance_to(p) < 3.5:
			near += 1
	if near >= 6 and h["potions"] > 0:
		h["potion_pressed"] = true
	# a target along one of the eight directions
	_aim_t -= 1
	if _aim_t <= 0:
		_aim_t = 3
		_shot = _aim(e, p)
	var shot := _shot
	if shot != Vector2.ZERO:
		h["face"] = shot.normalized()
		h["fire"] = true
		# keep backing off from anything very close while shooting
		for m in e.monsters:
			if (m["pos"] as Vector2).distance_to(p) < 1.2:
				h["move"] = (p - (m["pos"] as Vector2)).normalized() * 0.6
		return
	# otherwise go somewhere
	_replan -= 1
	if _replan <= 0 or (_route.is_empty() and _replan < 10):
		_replan = 20
		_goal = _pick_goal(e, h)
		_route = _path(e, Vector2i(floori(p.x), floori(p.y)), _goal)
		if not _door.is_empty():
			_route.append(_door[0])   # step into the door: the key opens it
	var here := Vector2i(floori(p.x), floori(p.y))
	while not _route.is_empty() and (Vector2(_route[0]) + Vector2(0.5, 0.5)).distance_to(p) < 0.4:
		_route.pop_front()
	if not _route.is_empty():
		h["move"] = ((Vector2(_route[0]) + Vector2(0.5, 0.5)) - p).normalized()
	elif _goal != here:
		h["move"] = ((Vector2(_goal) + Vector2(0.5, 0.5)) - p).normalized()


## The direction (one of eight) of the nearest monster or generator within reach and in the clear, or zero.
func _aim(e: TorchEngine, p: Vector2) -> Vector2:
	var best := Vector2.ZERO
	var bd := 7.0
	var targets: Array = []
	for m in e.monsters:
		if not m["dead"] and m.get("fade", 0.0) == 0.0:
			targets.append(m["pos"])
	for g in e.gens:
		if g["hp"] > 0.0:
			targets.append(Vector2(g["cell"]) + Vector2(0.5, 0.5))
	for t in targets:
		var to: Vector2 = t - p
		var d := to.length()
		if d > bd or d < 0.05:
			continue
		for dir in DIRS:
			var n: Vector2 = dir.normalized()
			var along := to.dot(n)
			var off := absf(to.cross(n))
			if along > 0.0 and off < 0.45:
				if _clear(e, p, t):
					bd = d
					best = n
	return best


func _clear(e: TorchEngine, a: Vector2, b: Vector2) -> bool:
	var d := a.distance_to(b)
	var k := 0.5
	while k < d - 0.6:
		if e.solid_at(a.lerp(b, k / d)):
			return false
		k += 0.4
	return true


## Where to go: food when weak, treasure, keys, potions close by, a door it holds a key for, the party, the exit;
## chosen by walking distance, so nothing out of reach (behind a locked door) is ever picked.
func _pick_goal(e: TorchEngine, h: Dictionary) -> Vector2i:
	var p: Vector2 = h["pos"]
	var here := Vector2i(floori(p.x), floori(p.y))
	_dist = e._bfs(here)
	_door = []
	var lead := _leader(e, p)
	var best := e.exit_cell
	var bd := INF
	for it in e.items:
		var c: Vector2i = it["cell"]
		var d: int = _dist[e.idx(c)]
		if d >= 1 << 20 or d > 16:
			continue
		if lead.x > -1000.0 and (Vector2(c) + Vector2(0.5, 0.5)).distance_to(lead) > 6.0:
			continue
		var want := 0.0
		match it["kind"]:
			"food_ham", "food_bowl", "food_cider": want = 3.0 if h["health"] < 500.0 else 0.6
			"key": want = 1.6
			"potion": want = 1.2
			"chest", "gold_pile": want = 1.0
		if want > 0.0 and d / want < bd:
			bd = d / want
			best = c
	if bd == INF and lead.x > -1000.0:
		# a companion: stay at the player's side
		_door = []
		return here if p.distance_to(lead) < 2.5 else Vector2i(floori(lead.x), floori(lead.y))
	if bd == INF and h["keys"] > 0:
		# a door beside a reachable floor
		for y in T.H:
			for x in T.W:
				var c := Vector2i(x, y)
				if e.tile(c) != 2:
					continue
				for dd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
					var n: Vector2i = c + dd
					if e.walkable(n) and _dist[e.idx(n)] < 20:
						_door = [c]
						return n
	if bd == INF and me > 0 and p.distance_to(e.centre()) > 5.0:
		return Vector2i(floori(e.centre().x), floori(e.centre().y))
	return best


## The nearest leader (a human hero, or the first hero in the demo), or far away (-INF) when this hero leads.
func _leader(e: TorchEngine, p: Vector2) -> Vector2:
	var best := Vector2(-INF, -INF)
	var ls := e.leaders()
	if ls.has(e.heroes[me]):
		return best
	for o in ls:
		if best.x == -INF or p.distance_to(o["pos"]) < p.distance_to(best):
			best = o["pos"]
	return best


## The way there: down the distance map from the goal back to here.
func _path(e: TorchEngine, from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	if _dist.is_empty() or _dist[e.idx(to)] >= 1 << 20:
		return out
	var c := to
	var guard := 0
	while c != from and guard < 400:
		guard += 1
		out.push_front(c)
		var best := c
		var bd: int = _dist[e.idx(c)]
		for dd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + dd
			if n.x >= 0 and n.y >= 0 and n.x < T.W and n.y < T.H and _dist[e.idx(n)] < bd:
				bd = _dist[e.idx(n)]
				best = n
		if best == c:
			break
		c = best
	return out
