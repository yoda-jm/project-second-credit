class_name CaveObjects
extends RefCounted
## BDCFF [objects] lines: parsing, and drawing onto a CaveRendered. Port of GDash's cave/object/*.cpp
## (MIT, Copyright (c) 2007-2013 Czirkos Zoltan; see GDASH_LICENSE.txt).
##
## An object is a Dictionary: {"type": String, "seen_on": [bool x5], ...type-specific fields}.

const E = preload("res://games/rocks/engine/cave_elements.gd")


## Parses one "Type=params" line; returns {} when invalid.
static func parse(line: String) -> Dictionary:
	var eq := line.find("=")
	if eq < 0:
		return {}
	var type := line.substr(0, eq).to_lower()
	var w := Tokens.new(line.substr(eq + 1))
	var o := {}
	match type:
		"point":
			o = {"type": "point", "p": w.coord(), "element": w.element()}
		"line":
			o = {"type": "line", "p1": w.coord(), "p2": w.coord(), "element": w.element()}
		"rectangle":
			o = {"type": "rectangle", "p1": w.coord(), "p2": w.coord(), "element": w.element()}
		"fillrect":
			o = {"type": "fillrect", "p1": w.coord(), "p2": w.coord(), "element": w.element()}
			if w.ok:
				var fill := w.element_optional()
				o["fill"] = o["element"] if fill < 0 else fill
		"raster":
			var p1 := w.coord()
			var n := w.coord()
			var d := w.coord()
			o = {"type": "raster", "p1": p1, "p2": Vector2i(p1.x + (n.x - 1) * d.x, p1.y + (n.y - 1) * d.y),
				"dist": d, "element": w.element()}
		"join", "add", "addbackward":
			o = {"type": "join", "dist": w.coord(), "search": w.element(), "put": w.element(),
				"backwards": type == "addbackward"}
		"boundaryfill":
			o = {"type": "boundaryfill", "start": w.coord(), "fill": w.element(), "border": w.element()}
		"floodfill":
			o = {"type": "floodfill", "start": w.coord(), "fill": w.element(), "search": w.element()}
		"copypaste":
			o = {"type": "copypaste", "p1": w.coord(), "p2": w.coord(), "dest": w.coord()}
			var mirror := w.word()
			var flip := w.word()
			o["mirror"] = mirror.to_lower() == "mirror"
			o["flip"] = flip.to_lower() == "flip"
			w.ok = w.ok or true
		"randomfill", "randomfillc64":
			o = _parse_random_fill(w, type == "randomfillc64")
		"maze":
			o = {"type": "maze", "p1": w.coord(), "p2": w.coord(), "wall_width": w.integer(), "path_width": w.integer(),
				"horiz": w.integer(), "seed": [w.integer(), w.integer(), w.integer(), w.integer(), w.integer()],
				"wall": w.element(), "path": w.element(), "maze_type": w.word().to_lower()}
		_:
			return {}
	if not w.ok or o.is_empty():
		return {}
	o["seen_on"] = [true, true, true, true, true]
	return o


static func _parse_random_fill(w: Tokens, c64: bool) -> Dictionary:
	var o := {"type": "randomfill", "p1": w.coord(), "p2": w.coord(),
		"seed": [w.integer(), w.integer(), w.integer(), w.integer(), w.integer()],
		"initial": w.element(), "c64": c64}
	if not w.ok:
		return {}
	var fills: Array[int] = [E.DIRT, E.DIRT, E.DIRT, E.DIRT]
	var probs: Array[int] = [0, 0, 0, 0]
	var j := 0
	var leftover := ""
	while j < 4:
		var s1 := w.word()
		if s1 == "":
			break
		var s2 := w.word()
		if s2 == "":
			leftover = s1
			break
		var el := CaveNames.element(s1)
		if el < 0 or not s2.is_valid_int():
			return {}
		fills[j] = el
		probs[j] = s2.to_int()
		j += 1
	if j == 4:
		leftover = w.word()
	o["fills"] = fills
	o["probs"] = probs
	o["replace_only"] = E.NONE
	if leftover != "":
		var r := CaveNames.element(leftover)
		if r < 0:
			return {}
		o["replace_only"] = r
	return o


## Draws the object onto the cave map (through cave.store_rc, which handles wraparound).
static func draw(o: Dictionary, cave: CaveRendered) -> void:
	match o["type"]:
		"point":
			cave.store_rc(o["p"].x, o["p"].y, o["element"], o["id"])
		"line":
			_draw_line(o, cave)
		"rectangle":
			var r := _ordered(o["p1"], o["p2"])
			for x in range(r[0], r[2] + 1):
				cave.store_rc(x, r[1], o["element"], o["id"])
				cave.store_rc(x, r[3], o["element"], o["id"])
			for y in range(r[1], r[3] + 1):
				cave.store_rc(r[0], y, o["element"], o["id"])
				cave.store_rc(r[2], y, o["element"], o["id"])
		"fillrect":
			var r := _ordered(o["p1"], o["p2"])
			for y in range(r[1], r[3] + 1):
				for x in range(r[0], r[2] + 1):
					var border: bool = y == r[1] or y == r[3] or x == r[0] or x == r[2]
					cave.store_rc(x, y, o["element"] if border else o["fill"], o["id"])
		"raster":
			var r := _ordered(o["p1"], o["p2"])
			var dx: int = maxi(1, o["dist"].x)
			var dy: int = maxi(1, o["dist"].y)
			var y: int = r[1]
			while y <= r[3]:
				var x: int = r[0]
				while x <= r[2]:
					cave.store_rc(x, y, o["element"], o["id"])
					x += dx
				y += dy
		"join":
			_draw_join(o, cave)
		"boundaryfill":
			_draw_boundary_fill(o, cave)
		"floodfill":
			_draw_flood_fill(o, cave)
		"copypaste":
			_draw_copy_paste(o, cave)
		"randomfill":
			_draw_random_fill(o, cave)
		"maze":
			CaveMaze.draw(o, cave)


static func _ordered(p1: Vector2i, p2: Vector2i) -> Array[int]:
	return [mini(p1.x, p2.x), mini(p1.y, p2.y), maxi(p1.x, p2.x), maxi(p1.y, p2.y)]


static func _draw_line(o: Dictionary, cave: CaveRendered) -> void:
	var x1: int = o["p1"].x
	var y1: int = o["p1"].y
	var x2: int = o["p2"].x
	var y2: int = o["p2"].y
	var steep := absi(y2 - y1) > absi(x2 - x1)
	if steep:
		var t := x1; x1 = y1; y1 = t
		t = x2; x2 = y2; y2 = t
	if x1 > x2:
		var t := x1; x1 = x2; x2 = t
		t = y1; y1 = y2; y2 = t
	var dx := x2 - x1
	var dy := absi(y2 - y1)
	var error := 0
	var ystep := 1 if y1 < y2 else -1
	var y := y1
	for x in range(x1, x2 + 1):
		if steep:
			cave.store_rc(y, x, o["element"], o["id"])
		else:
			cave.store_rc(x, y, o["element"], o["id"])
		error += dy
		if error * 2 >= dx:
			y += ystep
			error -= dx


static func _draw_join(o: Dictionary, cave: CaveRendered) -> void:
	var d: Vector2i = o["dist"]
	if not o["backwards"]:
		for y in cave.h:
			for x in cave.w:
				if cave.map[y * cave.w + x] == o["search"]:
					cave.store_rc(x + d.x, y + d.y, o["put"], o["id"])
	else:
		for y in range(cave.h - 1, -1, -1):
			for x in range(cave.w - 1, -1, -1):
				if cave.map[y * cave.w + x] == o["search"]:
					cave.store_rc(x + d.x, y + d.y, o["put"], o["id"])


## Iterative versions of GDash's recursive fills; they visit cells in the same order.
static func _fill(cave: CaveRendered, start: Vector2i, o: Dictionary, stored: int, can_enter: Callable) -> void:
	var stack: Array[Vector2i] = [start]
	var steps: Array[int] = [0]
	cave.store_rc(start.x, start.y, stored, o["id"])
	while not stack.is_empty():
		var p: Vector2i = stack.back()
		var step: int = steps.back()
		if step >= 4:
			stack.pop_back()
			steps.pop_back()
			continue
		steps[steps.size() - 1] = step + 1
		var n := p
		match step:
			0:
				if p.x <= 0: continue
				n = Vector2i(p.x - 1, p.y)
			1:
				if p.y <= 0: continue
				n = Vector2i(p.x, p.y - 1)
			2:
				if p.x >= cave.w - 1: continue
				n = Vector2i(p.x + 1, p.y)
			3:
				if p.y >= cave.h - 1: continue
				n = Vector2i(p.x, p.y + 1)
		if can_enter.call(cave.map[n.y * cave.w + n.x]):
			cave.store_rc(n.x, n.y, stored, o["id"])
			stack.append(n)
			steps.append(0)


static func _draw_flood_fill(o: Dictionary, cave: CaveRendered) -> void:
	var s: Vector2i = o["start"]
	if s.x < 0 or s.y < 0 or s.x >= cave.w or s.y >= cave.h or o["search"] == o["fill"]:
		return
	var search: int = o["search"]
	_fill(cave, s, o, o["fill"], func(e: int) -> bool: return e == search)


static func _draw_boundary_fill(o: Dictionary, cave: CaveRendered) -> void:
	var s: Vector2i = o["start"]
	if s.x < 0 or s.y < 0 or s.x >= cave.w or s.y >= cave.h:
		return
	var border: int = o["border"]
	_fill(cave, s, o, border, func(e: int) -> bool: return e != border)
	for i in cave.map.size():
		if cave.objects_order[i] == o["id"]:
			cave.map[i] = o["fill"]


static func _draw_copy_paste(o: Dictionary, cave: CaveRendered) -> void:
	var r := _ordered(o["p1"], o["p2"])
	var w: int = r[2] - r[0] + 1
	var h: int = r[3] - r[1] + 1
	var clip := PackedInt32Array()
	clip.resize(w * h)
	for y in h:
		for x in w:
			clip[y * w + x] = cave.get_cell(x + r[0], y + r[1])
	var dest: Vector2i = o["dest"]
	for y in h:
		var ydisp: int = h - 1 - y if o["flip"] else y
		for x in w:
			var xdisp: int = w - 1 - x if o["mirror"] else x
			cave.store_rc(dest.x + xdisp, dest.y + ydisp, clip[y * w + x], o["id"])


static func _draw_random_fill(o: Dictionary, cave: CaveRendered) -> void:
	var s: int = o["seed"][cave.rendered_on]
	if s == -1:
		s = cave.random.rand_int()
	var rand := GlibRand.new(s)
	var c64rand := C64Rand.new()
	c64rand.set_seed(s)
	var r := _ordered(o["p1"], o["p2"])
	var fills: Array = o["fills"]
	var probs: Array = o["probs"]
	for y in range(r[1], r[3] + 1):
		for x in range(r[0], r[2] + 1):
			var randm: int = c64rand.random() if o["c64"] else rand.rand_int_range(0, 256)
			var element: int = o["initial"]
			for k in 4:
				if randm < probs[k]:
					element = fills[k]
			if o["replace_only"] == E.NONE or cave.get_cell(x, y) == o["replace_only"]:
				cave.store_rc(x, y, element, o["id"])


## Whitespace-separated reader that mimics C++ istream >> semantics (a failed read sets ok = false).
class Tokens:
	var words: PackedStringArray
	var i := 0
	var ok := true

	func _init(text: String) -> void:
		words = text.strip_edges().split(" ", false)
		var clean := PackedStringArray()
		for wd in words:
			for part in wd.split("\t", false):
				clean.append(part)
		words = clean

	func word() -> String:
		if i >= words.size():
			return ""
		i += 1
		return words[i - 1]

	func integer() -> int:
		var s := word()
		var m := RegEx.create_from_string("^[+-]?\\d+").search(s)
		if m == null:
			ok = false
			return 0
		return m.get_string().to_int()

	func coord() -> Vector2i:
		var x := integer()
		var y := integer()
		return Vector2i(x, y)

	func element() -> int:
		var e := CaveNames.element(word())
		if e < 0:
			ok = false
		return e

	func element_optional() -> int:
		var s := word()
		return -1 if s == "" else CaveNames.element(s)
