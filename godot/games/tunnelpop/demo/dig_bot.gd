class_name DigBot
extends RefCounted
## The Tunnel Pop autopilot (the demo). It keeps out of reach of any creature close by (backing off along the tunnel
## that takes it furthest), pumps a caught creature until it pops, and otherwise goes after the nearest one: it plans a
## route over the grid (earth costs more than tunnel), and when the creature lies within the hose's reach along a
## straight open tunnel it turns to face it and shoots.

const D = preload("res://games/tunnelpop/engine/pop_dig_engine.gd")

var _repeat := 0
var _path: Array[Vector2i] = []
var _replan := 0


func drive(e: DigEngine) -> void:
	e.want = Vector2i.ZERO
	e.pump_pressed = false
	if e.phase != D.Phase.PLAY:
		return
	var me := e.hero_cell()
	var p: Vector2 = e.hero["pos"]
	# pumping one: keep squeezing unless another comes close
	if not e.hose.is_empty() and e.hose["id"] >= 0:
		if _danger(e, p, 1.6, e.hose["id"]).is_empty():
			_repeat -= 1
			if _repeat <= 0:
				_repeat = 9
				e.pump_pressed = true
			return
	# danger close by: step away
	var threat := _danger(e, p, 1.4, -1)
	if not threat.is_empty():
		var away := _away(e, me, threat["pos"])
		if away != Vector2i.ZERO:
			e.want = away
			# ...or, if it's right in line, just pump it
			if _in_line(e, p, threat):
				e.want = _toward(p, threat["pos"])
				e.pump_pressed = e.hose.is_empty()
			return
	# a target in reach along an open line: face it and shoot
	var target := _nearest(e, p)
	if target.is_empty():
		return
	if _in_line(e, p, target):
		# aim at it and fire (a shot doesn't step forward)
		e.want = _toward(p, target["pos"])
		_repeat -= 1
		if _repeat <= 0 and e.hose.is_empty():
			_repeat = 6
			e.pump_pressed = true
		elif p.distance_to(target["pos"]) < 1.6:
			e.want = Vector2i.ZERO   # don't walk into it while the hose is out
		return
	# otherwise head for it
	_replan -= 1
	if _replan <= 0 or _path.is_empty():
		_replan = 20
		_path = _route(e, me, Vector2i(roundi(target["pos"].x), roundi(target["pos"].y)))
	while not _path.is_empty() and _path[0] == me and p.distance_to(Vector2(me)) < 0.05:
		_path.pop_front()
	if not _path.is_empty():
		var nxt: Vector2i = _path[0]
		e.want = Vector2i(signi(nxt.x - me.x), signi(nxt.y - me.y)) if nxt != me else _toward(p, Vector2(nxt))
		if e.want == Vector2i.ZERO:
			_path.pop_front()


func _danger(e: DigEngine, p: Vector2, r: float, except: int) -> Dictionary:
	for f in e.foes:
		if f["dead"] or f["id"] == except or f["puff"] > 0.0:
			continue
		if (f["pos"] as Vector2).distance_to(p) < r:
			return f
	return {}


func _nearest(e: DigEngine, p: Vector2) -> Dictionary:
	var best := {}
	var bd := INF
	for f in e.foes:
		if f["dead"] or f["ghost"]:
			continue
		var d := (f["pos"] as Vector2).distance_to(p)
		if d < bd:
			bd = d
			best = f
	return best


static func _toward(p: Vector2, q: Vector2) -> Vector2i:
	var d := q - p
	if absf(d.x) > absf(d.y):
		return Vector2i(signi(roundi(d.x * 100.0)), 0)
	return Vector2i(0, signi(roundi(d.y * 100.0)))


## Whether the creature lies on the hero's row or column within the hose's reach, the tunnel open between them.
func _in_line(e: DigEngine, p: Vector2, f: Dictionary) -> bool:
	if f["ghost"]:
		return false
	var q: Vector2 = f["pos"]
	var same_row := absf(q.y - p.y) < 0.3 and absf(p.y - roundf(p.y)) < 0.05
	var same_col := absf(q.x - p.x) < 0.3 and absf(p.x - roundf(p.x)) < 0.05
	if not same_row and not same_col:
		return false
	if p.distance_to(q) > D.HOSE + 0.3:
		return false
	var a := Vector2i(roundi(p.x), roundi(p.y))
	var b := Vector2i(roundi(q.x), roundi(q.y))
	var d := Vector2i(signi(b.x - a.x), signi(b.y - a.y))
	var c := a
	while c != b:
		if not e.linked(c, c + d):
			return false
		c += d
	return true


func _aligned_facing(e: DigEngine, f: Dictionary) -> bool:
	return _in_line(e, e.hero["pos"], f) and e.hose.is_empty()


## The open way out that ends furthest from a threat.
func _away(e: DigEngine, me: Vector2i, from: Vector2) -> Vector2i:
	var best := Vector2i.ZERO
	var bd := (Vector2(me)).distance_to(from)
	for d in D.DIRS:
		var n: Vector2i = me + d
		if e.linked(me, n) or (D.inside(n) and not e._rock_at(n)):
			var dist := Vector2(n).distance_to(from) + (0.5 if e.linked(me, n) else 0.0)
			if dist > bd:
				bd = dist
				best = d
	return best


## A route over the grid: tunnel steps cost 1, earth 2.5; rocks can't be passed.
func _route(e: DigEngine, from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var dist := {from: 0.0}
	var prev := {}
	var open: Array = [[0.0, from]]
	while not open.is_empty():
		open.sort_custom(func(a, b): return a[0] < b[0])
		var cur: Array = open.pop_front()
		var c: Vector2i = cur[1]
		if c == to:
			break
		if cur[0] > dist.get(c, INF):
			continue
		for d in D.DIRS:
			var n: Vector2i = c + d
			if not D.inside(n) or e._rock_at(n):
				continue
			var nd: float = dist[c] + (1.0 if e.linked(c, n) else 2.5)
			if nd < dist.get(n, INF):
				dist[n] = nd
				prev[n] = c
				open.append([nd, n])
	var path: Array[Vector2i] = []
	if not prev.has(to):
		return path
	var c := to
	while c != from:
		path.push_front(c)
		c = prev[c]
	return path
