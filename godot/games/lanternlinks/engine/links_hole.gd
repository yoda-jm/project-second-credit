class_name LinksHole
extends RefCounted
## One mini-golf hole read from our text format (see docs/games/lanternlinks.md): a grid of 0.5 m cells with a kind
## and a height each, ramps between flat cells, smooth bumps, the tee, the cup and the gadgets. Answers the surface
## height and slope anywhere, which the ball physics and the view's meshes both use, so what you see is what the ball
## rolls on. Positions are in metres: x east, y south (the grid's rows), heights up.

enum { OUT, WALL, FELT, SAND, ICE, WATER, CHASM, BOOST }

const CELL := 0.5
const CHASM_H := -3.0
const CUP_R := 0.13
const DIP_R := 0.45    ## the cup's gentle dip, so a dying putt curls in
const DIP_D := 0.035
const PIPE_R := 0.1

var name := ""
var par := 3
var w := 0
var h := 0
var kind := PackedByteArray()
var base := PackedFloat32Array()   ## flat height per cell
var ramp := {}                     ## cell index -> [axis (0 x, 1 y), from (m), to (m), h_from, h_to]
var diag := PackedByteArray()      ## 0, or which triangle is solid: 1 NW, 2 SE, 3 NE, 4 SW
var boost := {}                    ## cell index -> direction
var tee := Vector2.ZERO
var cup := Vector2.ZERO
var cup_h := 0.0
var bumps: Array = []              ## [centre, radius, height]
var gadgets: Array[Dictionary] = []


static func parse_course(text: String) -> Array[LinksHole]:
	var out: Array[LinksHole] = []
	var cur: Array[String] = []
	for line in text.split("\n"):
		if line.begins_with("hole ="):
			if not cur.is_empty():
				out.append(LinksHole.parse(cur))
			cur = []
		if line.begins_with("hole =") or not cur.is_empty():
			cur.append(line)
	if not cur.is_empty():
		out.append(LinksHole.parse(cur))
	return out


static func parse(lines: Array[String]) -> LinksHole:
	var hole := LinksHole.new()
	var map: Array[String] = []
	var hgt: Array[String] = []
	var block := ""
	var props: Array[PackedStringArray] = []
	for raw in lines:
		var line := raw.rstrip(" \r")
		if line.begins_with(";"):
			continue
		if line == "map:" or line == "height:":
			block = line.trim_suffix(":")
			continue
		var eq := line.find(" = ")
		if eq > 0 and line.substr(0, eq).is_valid_identifier():
			block = ""
			var key := line.substr(0, eq)
			var val := line.substr(eq + 3).strip_edges()
			match key:
				"hole": hole.name = val
				"par": hole.par = int(val)
				_:
					var p := PackedStringArray([key])
					p.append_array(val.split(" ", false))
					props.append(p)
			continue
		if line.strip_edges() == "":
			block = ""
			continue
		if block == "map":
			map.append(line)
		elif block == "height":
			hgt.append(line)
	hole.h = map.size()
	for r in map:
		hole.w = maxi(hole.w, r.length())
	var n := hole.w * hole.h
	hole.kind.resize(n)
	hole.base.resize(n)
	hole.diag.resize(n)
	for y in hole.h:
		for x in hole.w:
			var c := map[y][x] if x < map[y].length() else " "
			var i := y * hole.w + x
			var hc := hgt[y][x] if y < hgt.size() and x < hgt[y].length() else "0"
			hole.base[i] = _height_of(hc)
			var k := FELT
			match c:
				" ": k = OUT
				"#": k = WALL
				"s": k = SAND
				"i": k = ICE
				"w": k = WATER
				"_": k = CHASM
				">", "<", "^", "v":
					k = BOOST
					hole.boost[i] = {">": Vector2.RIGHT, "<": Vector2.LEFT, "^": Vector2.UP, "v": Vector2.DOWN}[c]
				"T": hole.tee = hole.centre(x, y)
				"O": hole.cup = hole.centre(x, y)
			hole.kind[i] = k
			if hc == "/":
				hole.ramp[i] = []
	# diagonal banks: the solid half is the one against the walls
	for y in hole.h:
		for x in hole.w:
			var c := map[y][x] if x < map[y].length() else " "
			if c != "/" and c != "\\":
				continue
			var i := y * hole.w + x
			if c == "/":
				hole.diag[i] = 1 if hole._solid(x, y - 1) or hole._solid(x - 1, y) else 2
			else:
				hole.diag[i] = 3 if hole._solid(x, y - 1) or hole._solid(x + 1, y) else 4
	for i in hole.ramp.keys():
		hole._resolve_ramp(i)
	for p in props:
		hole._prop(p)
	hole.cup_h = hole.height(hole.cup)
	return hole


static func _height_of(c: String) -> float:
	if c >= "0" and c <= "9":
		return float(c.unicode_at(0) - 48) * 0.1
	if c >= "a" and c <= "z":
		return 1.0 + float(c.unicode_at(0) - 97) * 0.1
	return 0.0


func centre(x: int, y: int) -> Vector2:
	return Vector2((x + 0.5) * CELL, (y + 0.5) * CELL)


func _solid(x: int, y: int) -> bool:
	return x < 0 or y < 0 or x >= w or y >= h or kind[y * w + x] <= WALL


func _is_ramp(x: int, y: int) -> bool:
	return x >= 0 and y >= 0 and x < w and y < h and ramp.has(y * w + x)


## A ramp cell runs between the nearest flat, open cells on either side, along the axis whose ends differ most.
func _resolve_ramp(i: int) -> void:
	var x := i % w
	var y := i / w
	var best: Array = []
	var best_d := -1.0
	for axis in 2:
		var d := Vector2i(1, 0) if axis == 0 else Vector2i(0, 1)
		var a := Vector2i(x, y) - d
		while _is_ramp(a.x, a.y):
			a -= d
		var b := Vector2i(x, y) + d
		while _is_ramp(b.x, b.y):
			b += d
		if _solid(a.x, a.y) or _solid(b.x, b.y):
			continue
		var ha := base[a.y * w + a.x]
		var hb := base[b.y * w + b.x]
		var from := (float(a[axis]) + 1.0) * CELL
		var to := float(b[axis]) * CELL
		if absf(hb - ha) > best_d:
			best_d = absf(hb - ha)
			best = [axis, from, to, ha, hb]
	if best.is_empty():
		ramp.erase(i)
	else:
		ramp[i] = best


func _prop(p: PackedStringArray) -> void:
	var f := func(k: int) -> float: return float(p[k]) if k < p.size() else 0.0
	var at := func(k: int) -> Vector2: return Vector2(float(p[k]), float(p[k + 1])) * CELL
	match p[0]:
		"bump":
			bumps.append([at.call(1), f.call(3) * CELL, f.call(4)])
		"bumper":
			gadgets.append({"type": "bumper", "pos": at.call(1), "r": f.call(3)})
		"windmill":
			# the tunnel cell, the side the blades face (n, e, s, w), seconds per turn
			var c := Vector2i(int(p[1]), int(p[2]))
			var face: Vector2 = {"n": Vector2.UP, "e": Vector2.RIGHT, "s": Vector2.DOWN, "w": Vector2.LEFT}[p[3]]
			var mid := centre(c.x, c.y) + face * CELL * 0.5
			var side := Vector2(-face.y, face.x) * CELL * 0.5
			gadgets.append({"type": "windmill", "cell": c, "face": face, "a": mid - side, "b": mid + side,
				"hub": mid, "period": f.call(4)})
		"mover":
			# a block sliding between two centres (cells), its size (cells), seconds for a round trip
			gadgets.append({"type": "mover", "p0": at.call(1), "p1": at.call(3),
				"half": Vector2(f.call(5), f.call(6)) * CELL * 0.5, "period": f.call(7)})
		"spinner":
			# a bar turning about its centre (cells): half length (m), turns per second (negative: clockwise)
			gadgets.append({"type": "spinner", "pos": at.call(1), "len": f.call(3), "speed": f.call(4) * TAU})
		"pipe":
			# in at one mouth, out of the other heading (n, e, s, w)
			var d: Vector2 = {"n": Vector2.UP, "e": Vector2.RIGHT, "s": Vector2.DOWN, "w": Vector2.LEFT}[p[5]]
			gadgets.append({"type": "pipe", "a": at.call(1), "b": at.call(3), "dir": d})
		"loop":
			# the loop's entry (a point on the lane's centre line, cells) and the way in (n, e, s, w)
			var d2: Vector2 = {"n": Vector2.UP, "e": Vector2.RIGHT, "s": Vector2.DOWN, "w": Vector2.LEFT}[p[3]]
			gadgets.append({"type": "loop", "pos": at.call(1), "dir": d2})


func index(p: Vector2) -> int:
	var x := floori(p.x / CELL)
	var y := floori(p.y / CELL)
	if x < 0 or y < 0 or x >= w or y >= h:
		return -1
	return y * w + x


func kind_at(p: Vector2) -> int:
	var i := index(p)
	return OUT if i < 0 else kind[i]


## Whether a point is inside solid ground (a wall cell or a bank's solid half).
func solid_at(p: Vector2) -> bool:
	var i := index(p)
	if i < 0 or kind[i] <= WALL:
		return true
	return diag[i] != 0 and _in_diag(diag[i], p / CELL - Vector2(i % w, i / w))


static func _in_diag(d: int, f: Vector2) -> bool:
	match d:
		1: return f.x + f.y < 1.0
		2: return f.x + f.y > 1.0
		3: return f.x > f.y
		_: return f.x < f.y


## The floor height of cell i at p (p may lie just outside it): flat, ramp or chasm, without bumps.
func cell_floor(i: int, p: Vector2) -> Vector3:
	if kind[i] == CHASM:
		return Vector3(CHASM_H, 0, 0)
	var r: Array = ramp.get(i, [])
	if r.is_empty():
		return Vector3(base[i], 0, 0)
	var axis: int = r[0]
	var a: float = r[1]
	var b: float = r[2]
	var ha: float = r[3]
	var hb: float = r[4]
	var s := (p[axis] - a) / (b - a)
	var slope := (hb - ha) / (b - a)
	var hh := lerpf(ha, hb, clampf(s, 0.0, 1.0))
	return Vector3(hh, slope if axis == 0 else 0.0, slope if axis == 1 else 0.0)


## Height and slope (h, dh/dx, dh/dy) of the surface at p, in the cell under p (bumps and the cup's dip added).
func surface(p: Vector2) -> Vector3:
	var i := index(p)
	if i < 0 or kind[i] <= WALL:
		return Vector3(1000.0, 0, 0)
	return cell_floor(i, p) + extras(p, kind[i] != CHASM)


## The smooth additions: bumps (a (1 - d²/r²)² mound each) and the dip around the cup.
func extras(p: Vector2, with_bumps := true) -> Vector3:
	var out := Vector3.ZERO
	if with_bumps:
		for b in bumps:
			out += _mound(p, b[0], b[1], b[2])
	var dc := p.distance_squared_to(cup)
	if dc < DIP_R * DIP_R:
		out += _mound(p, cup, DIP_R, -DIP_D)
	return out


static func _mound(p: Vector2, c: Vector2, r: float, hh: float) -> Vector3:
	var d := p - c
	var q := 1.0 - d.length_squared() / (r * r)
	if q <= 0.0:
		return Vector3.ZERO
	var g := -4.0 * hh * q / (r * r)
	return Vector3(hh * q * q, g * d.x, g * d.y)


func height(p: Vector2) -> float:
	return surface(p).x


func has_gadget(t: String) -> bool:
	return gadgets.any(func(g): return g["type"] == t)


func moving() -> bool:
	return gadgets.any(func(g): return g["type"] in ["windmill", "mover", "spinner"])
