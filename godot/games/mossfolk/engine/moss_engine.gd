class_name MossEngine
extends RefCounted
## Mossfolk rules (in the Lemmings tradition; our own tuning from memory), 17 logic steps a second, deterministic.
## The level is a pixel terrain (air, earth, steel). Mosslings drop from the hatch and walk; they step up or down
## small slopes (up to 6 pixels), turn at walls, fall off edges (a fall of more than 60 pixels splats them, unless
## they glide), and are saved at the burrow. Skills: climb and glide (kept for good), pop (a countdown, then a blast
## that eats earth), block (turns the others), build (12 bricks up and forward), bash (a tunnel forward), mine (a
## tunnel down and forward), dig (straight down). Steel stops every tool. Water drowns, traps catch one at a time.
## A creature at (x, y) has its feet in the air pixel y, standing on the pixel (x, y + 1).
## Events: "hatch", "spawn", "assign" {id, skill}, "saved", "death" {id, how}, "pop" {x, y}, "brick", "stroke"
## {id, kind}, "warn" {id}, "shrug", "trap" {i}, "done" {saved, needed}.

signal event(kind: String, data: Dictionary)

const TICK := 1.0 / 17.0
const AIR := 0
const EARTH := 1
const STEEL := 2
const HEAD := 9
const STEP_UP := 6
const SPLAT := 60
const SKILLS := ["climb", "glide", "pop", "block", "build", "bash", "mine", "dig"]
const HATCH_TIME := 26
const BOMB_TIME := 85         ## five seconds
const BRICKS := 12

var level: MossLevel
var w := 0
var h := 0
var terrain := PackedByteArray()
var changed := Rect2i()       ## terrain changed since the view last looked (it clears this)
var folk: Array[Dictionary] = []
var skills := {}              ## skill -> count left
var rate := 50                ## release rate 1..99
var frame := 0
var released := 0
var saved := 0
var dead := 0
var time_left := 0.0
var over := false
var nuking := false
var paused := false
var _next_spawn := 0
var _trap_cool: Array[int] = []
var _nuke_i := 0


func _init(lv: MossLevel) -> void:
	level = lv
	w = lv.w
	h = lv.h
	terrain = lv.terrain.duplicate()
	for s in SKILLS:
		skills[s] = int(lv.skills.get(s, 0))
	rate = lv.rate
	time_left = lv.minutes * 60.0
	_next_spawn = HATCH_TIME + 8
	for t in lv.traps:
		_trap_cool.append(0)


func at(x: int, y: int) -> int:
	if x < 0 or x >= w or y < 0 or y >= h:
		return AIR
	return terrain[y * w + x]


func solid(x: int, y: int) -> bool:
	return at(x, y) != AIR


func _clear(x: int, y: int) -> bool:
	## Removes earth at a pixel; false if it is steel.
	if x < 0 or x >= w or y < 0 or y >= h:
		return true
	var v := terrain[y * w + x]
	if v == STEEL:
		return false
	if v == EARTH:
		terrain[y * w + x] = AIR
		_mark(x, y)
	return true


func _fill(x: int, y: int) -> void:
	if x < 0 or x >= w or y < 0 or y >= h or terrain[y * w + x] != AIR:
		return
	terrain[y * w + x] = EARTH
	_mark(x, y)


func _mark(x: int, y: int) -> void:
	var r := Rect2i(x, y, 1, 1)
	changed = r if changed.size == Vector2i.ZERO else changed.merge(r)


func alive() -> int:
	var n := 0
	for c in folk:
		if c["state"] != "gone":
			n += 1
	return n


func spawn_interval() -> int:
	return 53 - rate / 2


# ------------------------------------------------------------------ the step

func tick() -> void:
	if over or paused:
		return
	frame += 1
	time_left -= TICK
	if frame == 1:
		event.emit("hatch", {})
	if released < level.count and frame >= _next_spawn and not nuking:
		_next_spawn = frame + spawn_interval()
		var e: Vector2i = level.entrance
		folk.append({"id": released, "x": e.x, "y": e.y, "dir": 1, "state": "fall", "fall": 0, "climber": false,
			"glider": false, "bomb": -1, "t": 0, "bricks": 0})
		released += 1
		event.emit("spawn", {})
	if nuking and _nuke_i < folk.size():
		var c := folk[_nuke_i]
		if c["bomb"] < 0 and c["state"] != "gone" and c["state"] != "exit":
			c["bomb"] = 0
		_nuke_i += 1
	for i in _trap_cool.size():
		_trap_cool[i] = maxi(0, _trap_cool[i] - 1)
	for c in folk:
		if c["state"] != "gone":
			_update(c)
	var active := alive()
	if time_left <= 0.0 or (released >= level.count and active == 0) or (nuking and active == 0 and _nuke_i >= folk.size()):
		over = true
		event.emit("done", {"saved": saved, "needed": level.save})


func _update(c: Dictionary) -> void:
	# the bomb counts down whatever the creature does
	if c["bomb"] >= 0 and c["state"] != "panic" and c["state"] != "exit":
		c["bomb"] += 1
		if c["bomb"] >= (BOMB_TIME if not nuking else 20):
			if c["state"] in ["fall", "glide", "climb", "drown", "splat"]:
				_explode(c)
				return
			c["state"] = "panic"
			c["t"] = 0
			event.emit("panic", {"id": c["id"]})
	match c["state"]:
		"walk": _walk(c)
		"fall", "glide": _fall(c)
		"climb": _climb(c)
		"dig": _dig(c)
		"bash": _bash(c)
		"mine": _mine(c)
		"build": _build(c)
		"block": pass
		"shrug":
			c["t"] += 1
			if c["t"] >= 17:
				c["state"] = "walk"
		"panic":
			c["t"] += 1
			if c["t"] >= 17:
				_explode(c)
				return
		"splat", "drown":
			c["t"] += 1
			if c["t"] >= 16:
				_gone(c)
		"exit":
			c["t"] += 1
			if c["t"] >= 14:
				saved += 1
				_gone(c)
				event.emit("saved", {"id": c["id"]})
			return
	if c["state"] == "gone":
		return
	_hazards(c)


func _gone(c: Dictionary) -> void:
	c["state"] = "gone"


func _die(c: Dictionary, how: String) -> void:
	dead += 1
	event.emit("death", {"id": c["id"], "how": how, "x": c["x"], "y": c["y"]})
	if how == "splat" or how == "drown":
		c["state"] = how
		c["t"] = 0
	else:
		_gone(c)


func _hazards(c: Dictionary) -> void:
	var x: int = c["x"]
	var y: int = c["y"]
	if y >= h + 4 or x < 0 or x >= w:
		_die(c, "lost")
		return
	if c["state"] in ["splat", "drown", "exit", "panic"]:
		return
	for r in level.water:
		if (r as Rect2i).has_point(Vector2i(x, y)):
			_die(c, "drown")
			return
	for i in level.traps.size():
		var t: Dictionary = level.traps[i]
		var p: Vector2i = t["pos"]
		if _trap_cool[i] == 0 and absi(x - p.x) <= 4 and y <= p.y and y >= p.y - 10:
			_trap_cool[i] = 34
			event.emit("trap", {"i": i})
			_die(c, "trap")
			return
	var ex: Vector2i = level.exit
	if absi(x - ex.x) <= 3 and absi(y - ex.y) <= 4 and c["state"] != "block":
		c["state"] = "exit"
		c["t"] = 0
		c["bomb"] = -1


func _walk(c: Dictionary) -> void:
	var x: int = c["x"]
	var y: int = c["y"]
	var dir: int = c["dir"]
	var nx := x + dir
	# blockers are walls
	for b in folk:
		if b != c and b["state"] == "block" and absi(b["x"] - nx) <= 4 and absi(b["y"] - y) <= 8 and signi(b["x"] - x) == dir:
			c["dir"] = -dir
			return
	if solid(nx, y):
		var k := 1
		while k <= STEP_UP and solid(nx, y - k):
			k += 1
		if k > STEP_UP:
			if c["climber"]:
				c["state"] = "climb"
			else:
				c["dir"] = -dir
			return
		c["x"] = nx
		c["y"] = y - k
		return
	c["x"] = nx
	var j := 0
	while j < 4 and not solid(nx, y + 1 + j):
		j += 1
	if j < 4:
		c["y"] = y + j
	else:
		c["y"] = y + 3
		c["state"] = "fall"
		c["fall"] = 3


func _fall(c: Dictionary) -> void:
	var gliding: bool = c["glider"] and c["fall"] > 12
	if gliding:
		c["state"] = "glide"
	var speed := 2 if gliding else 3
	for i in speed:
		if solid(c["x"], c["y"] + 1):
			if c["fall"] > SPLAT and not c["glider"]:
				_die(c, "splat")
			else:
				c["state"] = "walk"
			c["fall"] = 0
			return
		c["y"] += 1
		c["fall"] += 1


func _climb(c: Dictionary) -> void:
	var x: int = c["x"]
	var dir: int = c["dir"]
	c["t"] += 1
	if c["t"] % 2 == 0:
		return
	var y: int = c["y"] - 1
	if solid(x, y - HEAD):
		# a ceiling: let go
		c["dir"] = -dir
		c["x"] = x - dir
		c["state"] = "fall"
		c["fall"] = 0
		return
	c["y"] = y
	if not solid(x + dir, y):
		c["x"] = x + dir  # hoisted over the top
		c["state"] = "walk"


func _dig(c: Dictionary) -> void:
	c["t"] += 1
	if c["t"] % 8 != 0:
		return
	var x: int = c["x"]
	var y: int = c["y"] + 1
	var any := false
	for dx in range(-4, 5):
		if at(x + dx, y) != AIR:
			any = true
	if not any:
		c["state"] = "fall"
		c["fall"] = 0
		return
	for dx in range(-4, 5):
		if at(x + dx, y) == STEEL and absi(dx) <= 2:
			c["state"] = "walk"
			return
	for dx in range(-4, 5):
		_clear(x + dx, y)
	c["y"] = y
	event.emit("stroke", {"id": c["id"], "kind": "dig"})


func _bash(c: Dictionary) -> void:
	c["t"] += 1
	if c["t"] % 8 != 0:
		return
	var x: int = c["x"]
	var y: int = c["y"]
	var dir: int = c["dir"]
	# is there anything left to bash just ahead?
	var any := false
	for dx in range(1, 9):
		for dy in range(0, HEAD):
			if at(x + dir * dx, y - dy) == EARTH:
				any = true
	if not any:
		c["state"] = "walk"
		return
	for dx in range(1, 7):
		for dy in range(0, HEAD):
			if at(x + dir * dx, y - dy) == STEEL:
				c["state"] = "walk"
				c["dir"] = -dir
				return
	for dx in range(1, 7):
		for dy in range(0, HEAD):
			_clear(x + dir * dx, y - dy)
	event.emit("stroke", {"id": c["id"], "kind": "bash"})
	for i in 3:
		x += dir
		if not solid(x, y + 1) and not solid(x, y + 2):
			c["x"] = x
			c["state"] = "fall"
			c["fall"] = 0
			return
	c["x"] = x


func _mine(c: Dictionary) -> void:
	c["t"] += 1
	if c["t"] % 12 != 0:
		return
	var x: int = c["x"]
	var y: int = c["y"]
	var dir: int = c["dir"]
	var centre := Vector2i(x + dir * 3, y - 3)
	var cells: Array[Vector2i] = []
	for dy in range(-6, 7):
		for dx in range(-6, 7):
			if dx * dx + dy * dy <= 30:
				cells.append(centre + Vector2i(dx, dy))
	for p in cells:
		if at(p.x, p.y) == STEEL and signi(p.x - x) == dir:
			c["state"] = "walk"
			c["dir"] = -dir
			return
	for p in cells:
		_clear(p.x, p.y)
	event.emit("stroke", {"id": c["id"], "kind": "mine"})
	c["x"] = x + dir * 2
	c["y"] = y + 1
	if not solid(c["x"], c["y"] + 1) and not solid(c["x"], c["y"] + 2):
		c["state"] = "fall"
		c["fall"] = 0


func _build(c: Dictionary) -> void:
	c["t"] += 1
	if c["t"] % 16 != 0:
		return
	var x: int = c["x"]
	var y: int = c["y"]
	var dir: int = c["dir"]
	for i in range(-1, 5):
		_fill(x + dir * i, y)
	c["bricks"] -= 1
	event.emit("brick", {"id": c["id"], "left": c["bricks"]})
	if c["bricks"] == 2:
		event.emit("warn", {"id": c["id"]})
	# up and forward, unless the head would hit something
	for dx in range(1, 3):
		if solid(x + dir * dx, y - 1) or solid(x + dir * dx, y - HEAD):
			c["dir"] = -dir
			c["state"] = "walk"
			return
	c["x"] = x + dir * 2
	c["y"] = y - 1
	if c["bricks"] <= 0:
		c["state"] = "shrug"
		c["t"] = 0
		event.emit("shrug", {})


func _explode(c: Dictionary) -> void:
	var x: int = c["x"]
	var y: int = c["y"] - 4
	for dy in range(-10, 11):
		for dx in range(-10, 11):
			if dx * dx + dy * dy <= 90:
				_clear(x + dx, y + dy)
	event.emit("pop", {"x": x, "y": y, "id": c["id"]})
	dead += 1
	_gone(c)


# ------------------------------------------------------------------ skills

## Gives a skill to a creature; false if it can't take it (or none is left).
func assign(id: int, skill: String) -> bool:
	if over or skills.get(skill, 0) <= 0 or id < 0 or id >= folk.size():
		return false
	var c := folk[id]
	var st: String = c["state"]
	if st in ["gone", "exit", "splat", "drown", "panic"]:
		return false
	var ok := false
	match skill:
		"climb":
			ok = not c["climber"]
			if ok: c["climber"] = true
		"glide":
			ok = not c["glider"]
			if ok: c["glider"] = true
		"pop":
			ok = c["bomb"] < 0
			if ok: c["bomb"] = 0
		"block":
			ok = st in ["walk", "build", "bash", "mine", "dig", "shrug"]
			if ok: c["state"] = "block"
		"build", "bash", "mine", "dig":
			ok = st in ["walk", "build", "bash", "mine", "dig", "shrug"] and st != skill
			if ok:
				c["state"] = skill
				c["t"] = 0
				if skill == "build":
					c["bricks"] = BRICKS
	if ok:
		skills[skill] -= 1
		event.emit("assign", {"id": id, "skill": skill})
	return ok


## The creature nearest a point (in pixels) that could be picked, -1 if none within reach.
func pick(p: Vector2, reach := 8.0) -> int:
	var best := -1
	var bd := reach
	for c in folk:
		if c["state"] in ["gone", "exit", "splat", "drown"]:
			continue
		var d := p.distance_to(Vector2(c["x"], c["y"] - 5))
		if d < bd:
			bd = d
			best = c["id"]
	return best


func nuke() -> void:
	if not nuking:
		nuking = true
		_nuke_i = 0
		event.emit("nuke", {})
