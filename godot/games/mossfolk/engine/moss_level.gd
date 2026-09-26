class_name MossLevel
extends RefCounted
## A Mossfolk level in our text format (a file holds several, each after [level]):
##
##   [level]
##   name=Down We Go
##   size=480x160            pixels (a mossling is about 10 tall)
##   folk=10 save=8 rate=50 minutes=4
##   skills=dig:2 build:1    climb glide pop block build bash mine dig
##   entrance=60,20          where they drop from
##   exit=400,120            the burrow door (bottom centre)
##   water=0,150,480,10      x,y,w,h (any number)
##   trap=snapper,300,120    kind,x,y (the trap's base)
##   theme=0
##   solution=40:0:dig @246:1:build @100:*:climb    what the demo plays: at a frame, or when a creature (or every
##                           creature, *) walks to an x, give it a skill
##   rect x y w h | ellipse cx cy rx ry | poly x,y x,y ... | steel x y w h | cut rect ... | cut ellipse ... | cut poly ...

const AIR := 0
const EARTH := 1
const STEEL := 2

var name := ""
var w := 320
var h := 160
var count := 10
var save := 5
var rate := 50
var minutes := 5.0
var skills := {}
var entrance := Vector2i(40, 20)
var exit := Vector2i(280, 140)
var water: Array[Rect2i] = []
var traps: Array[Dictionary] = []
var theme := 0
var solution: Array = []   ## [when ("120" or "@246"), creature ("3" or "*"), skill]
var terrain := PackedByteArray()


func _init() -> void:
	terrain.resize(w * h)


static func parse_file(text: String) -> Array[MossLevel]:
	var out: Array[MossLevel] = []
	var cur: MossLevel = null
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line == "" or line.begins_with(";"):
			continue
		if line == "[level]":
			if cur:
				out.append(cur)
			cur = MossLevel.new()
			continue
		if cur:
			cur._line(line)
	if cur:
		out.append(cur)
	return out


func _line(line: String) -> void:
	if line.contains("=") and not line.begins_with("cut") and not line.begins_with("rect"):
		for part in line.split(" ", false):
			if not part.contains("="):
				continue
			var k := part.get_slice("=", 0)
			var v := part.substr(k.length() + 1)
			_field(k, v, line)
			if k in ["name", "skills", "solution"]:
				return
		return
	var words := line.split(" ", false)
	var cut := words[0] == "cut"
	if cut:
		words = words.slice(1)
	var v := AIR if cut else EARTH
	match words[0]:
		"rect", "steel":
			_rect(int(words[1]), int(words[2]), int(words[3]), int(words[4]), STEEL if words[0] == "steel" else v)
		"ellipse":
			_ellipse(float(words[1]), float(words[2]), float(words[3]), float(words[4]), v)
		"poly":
			var pts := PackedVector2Array()
			for p in words.slice(1):
				pts.append(Vector2(float(p.get_slice(",", 0)), float(p.get_slice(",", 1))))
			_poly(pts, v)


func _field(k: String, v: String, line: String) -> void:
	match k:
		"name": name = line.substr(5).strip_edges()
		"size":
			w = int(v.get_slice("x", 0))
			h = int(v.get_slice("x", 1))
			terrain.resize(w * h)
			terrain.fill(AIR)
		"folk": count = int(v)
		"save": save = int(v)
		"rate": rate = int(v)
		"minutes": minutes = float(v)
		"theme": theme = int(v)
		"entrance": entrance = Vector2i(int(v.get_slice(",", 0)), int(v.get_slice(",", 1)))
		"exit": exit = Vector2i(int(v.get_slice(",", 0)), int(v.get_slice(",", 1)))
		"water":
			var p := v.split(",")
			water.append(Rect2i(int(p[0]), int(p[1]), int(p[2]), int(p[3])))
		"trap":
			var p := v.split(",")
			traps.append({"kind": p[0], "pos": Vector2i(int(p[1]), int(p[2]))})
		"skills":
			for s in line.substr(7).split(" ", false):
				skills[s.get_slice(":", 0)] = int(s.get_slice(":", 1))
		"solution":
			for s in line.substr(9).split(" ", false):
				var p := s.split(":")
				solution.append([p[0], p[1], p[2]])


func _put(x: int, y: int, v: int) -> void:
	if x < 0 or y < 0 or x >= w or y >= h:
		return
	terrain[y * w + x] = v


func _rect(x: int, y: int, rw: int, rh: int, v: int) -> void:
	for yy in range(y, y + rh):
		for xx in range(x, x + rw):
			_put(xx, yy, v)


func _ellipse(cx: float, cy: float, rx: float, ry: float, v: int) -> void:
	for yy in range(int(cy - ry), int(cy + ry) + 1):
		for xx in range(int(cx - rx), int(cx + rx) + 1):
			var dx := (xx + 0.5 - cx) / rx
			var dy := (yy + 0.5 - cy) / ry
			if dx * dx + dy * dy <= 1.0:
				_put(xx, yy, v)


func _poly(pts: PackedVector2Array, v: int) -> void:
	var r := Rect2(pts[0], Vector2.ZERO)
	for p in pts:
		r = r.expand(p)
	for yy in range(int(r.position.y), int(r.end.y) + 1):
		for xx in range(int(r.position.x), int(r.end.x) + 1):
			if Geometry2D.is_point_in_polygon(Vector2(xx + 0.5, yy + 0.5), pts):
				_put(xx, yy, v)
