class_name GardenBot
extends RefCounted
## Demo autopilot for Fruitburrow: heads for the nearest fruit along the cheapest path, where cells near
## monsters and cells under apples cost a lot, and throws the ball when a monster is close. Deterministic, so a
## demo with a fixed seed always plays the same way.

const E = preload("res://games/fruitburrow/engine/fruitburrow_engine.gd")
const T = preload("res://games/fruitburrow/engine/garden_map.gd").Terrain

var _dir := Vector2i.ZERO
var _cooldown := 0


func drive(e: FruitburrowEngine) -> void:
	if e.phase != E.Phase.PLAY:
		e.input_dir = Vector2i.ZERO
		return
	var p := e.player
	if p["t"] == 0.0 or p["to"] == p["cell"] or _danger_ahead(e):
		_dir = _plan(e)
	e.input_dir = _dir
	_cooldown -= 1
	if e.has_ball and _cooldown <= 0 and _monster_near(e, 4.5):
		# face the nearest monster along a tunnel before throwing
		var face := _toward_monster(e)
		if face != Vector2i.ZERO:
			p["face"] = face
		e.fire()
		_cooldown = 30


func _cost(e: FruitburrowEngine, c: Vector2i) -> float:
	if not e.player_can_enter(c):
		return -1.0
	var cost := 1.0 if e.at(c) == T.TUNNEL else 1.4
	var above := c + Vector2i.UP
	var ai := e.apple_at(above)
	if ai >= 0 and e.apple_at(c) < 0:
		cost += 40.0  # never stand or dig under an apple
	for m in e.monsters:
		var d := e.pos_of(m).distance_to(Vector2(c))
		if d < 1.5:
			cost += 80.0
		elif d < 3.0:
			cost += 15.0
	return cost


## Dijkstra from the gardener's cell to the nearest fruit; returns the first step.
func _plan(e: FruitburrowEngine) -> Vector2i:
	var start: Vector2i = e.player["to"] if e.player["t"] > 0.0 else e.player["cell"]
	var dist := {start: 0.0}
	var first := {start: Vector2i.ZERO}
	var open: Array[Vector2i] = [start]
	var done := {}
	while not open.is_empty():
		var bi := 0
		for i in open.size():
			if dist[open[i]] < dist[open[bi]]:
				bi = i
		var c := open[bi]
		open.remove_at(bi)
		if done.has(c):
			continue
		done[c] = true
		if e.fruit.has(c) and c != start:
			return first[c] if first[c] != Vector2i.ZERO else Vector2i.ZERO
		for d in E.DIRS:
			var n := c + d
			var k := _cost(e, n)
			if k < 0.0 or done.has(n):
				continue
			var nd: float = dist[c] + k
			if not dist.has(n) or nd < dist[n]:
				dist[n] = nd
				first[n] = d if c == start else first[c]
				open.append(n)
	return Vector2i.ZERO


func _danger_ahead(e: FruitburrowEngine) -> bool:
	var ahead: Vector2i = e.player["to"]
	for m in e.monsters:
		if e.pos_of(m).distance_to(Vector2(ahead)) < 1.2:
			return true
	return false


func _monster_near(e: FruitburrowEngine, r: float) -> bool:
	var pp := e.pos_of(e.player)
	for m in e.monsters:
		if e.pos_of(m).distance_to(pp) < r:
			return true
	return false


func _toward_monster(e: FruitburrowEngine) -> Vector2i:
	var c := e.near_cell(e.player)
	var best := Vector2i.ZERO
	var best_d := INF
	for d in E.DIRS:
		if not e.hollow(c + d):
			continue
		for m in e.monsters:
			var v := e.pos_of(m) - Vector2(c)
			var along := v.dot(Vector2(d))
			if along > 0.0 and along < best_d:
				best_d = along
				best = d
	return best
