class_name TinTrack
extends RefCounted
## A Tinplate Turbo track: a closed, smooth centreline (a Catmull-Rom curve through hand-placed points) sampled every
## half metre, each sample with its place, direction, the track's width, its height (a bridge lifts the road where a
## figure-eight crosses itself), and how sharply it bends (for the racing line). Hazards sit on it: oil, puddles, jump
## ramps. Format (`tracks/*.tin`, our text format):
##   [track]  name=  theme=  laps=  width=  points=x,z[,height] x,z ...  oil=x,z  puddle=x,z  ramp=x,z

const STEP := 0.5

var name := ""
var theme := 0
var laps := 4
var width := 4.6
var points: Array[Vector3] = []          ## x, z, height
var oil: Array[Vector2] = []
var puddles: Array[Vector2] = []
var ramps: Array[int] = []               ## sample indices
var _ramp_at: Array[Vector2] = []
## the samples
var pos := PackedVector2Array()
var dir := PackedVector2Array()
var height := PackedFloat32Array()
var bend := PackedFloat32Array()         ## signed curvature (1/m), + turning left
var length := 0.0


static func parse_file(text: String) -> Array[TinTrack]:
	var out: Array[TinTrack] = []
	var cur: TinTrack = null
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.begins_with(";") or line.is_empty():
			continue
		if line == "[track]":
			if cur:
				cur.build()
			cur = TinTrack.new()
			out.append(cur)
			continue
		if cur == null or not line.contains("="):
			continue
		var k := line.get_slice("=", 0).strip_edges()
		var v := line.substr(line.find("=") + 1).strip_edges()
		match k:
			"name": cur.name = v
			"theme": cur.theme = int(v)
			"laps": cur.laps = int(v)
			"width": cur.width = float(v)
			"points":
				for tok in v.split(" ", false):
					var f := tok.split(",")
					cur.points.append(Vector3(float(f[0]), float(f[1]), float(f[2]) if f.size() > 2 else 0.0))
			"oil": cur.oil.append(_v2(v))
			"puddle": cur.puddles.append(_v2(v))
			"ramp": cur._ramp_at.append(_v2(v))
	if cur:
		cur.build()
	return out


static func _v2(v: String) -> Vector2:
	var f := v.split(",")
	return Vector2(float(f[0]), float(f[1]))


static func _cr(a: Vector3, b: Vector3, c: Vector3, d: Vector3, t: float) -> Vector3:
	var t2 := t * t
	var t3 := t2 * t
	return 0.5 * ((2.0 * b) + (-a + c) * t + (2.0 * a - 5.0 * b + 4.0 * c - d) * t2 + (-a + 3.0 * b - 3.0 * c + d) * t3)


func build() -> void:
	# a dense polyline along the curve, then resampled evenly
	var dense: Array[Vector3] = []
	var n := points.size()
	for i in n:
		var a := points[(i - 1 + n) % n]
		var b := points[i]
		var c := points[(i + 1) % n]
		var d := points[(i + 2) % n]
		for k in 40:
			dense.append(_cr(a, b, c, d, k / 40.0))
	var cum := [0.0]
	for i in range(1, dense.size() + 1):
		var p := dense[i % dense.size()]
		var q := dense[i - 1]
		cum.append(cum[i - 1] + Vector2(p.x, p.y).distance_to(Vector2(q.x, q.y)))
	length = cum[dense.size()]
	var count := int(length / STEP)
	pos.resize(count)
	height.resize(count)
	var j := 0
	for s in count:
		var want := s * length / count
		while j < dense.size() - 1 and cum[j + 1] < want:
			j += 1
		var f: float = (want - cum[j]) / maxf(0.0001, cum[j + 1] - cum[j])
		var p := dense[j].lerp(dense[(j + 1) % dense.size()], f)
		pos[s] = Vector2(p.x, p.y)
		height[s] = maxf(0.0, p.z)
	dir.resize(count)
	bend.resize(count)
	for s in count:
		dir[s] = (pos[(s + 1) % count] - pos[(s - 1 + count) % count]).normalized()
	for s in count:
		var a := dir[(s - 4 + count) % count]
		var b := dir[(s + 4) % count]
		bend[s] = a.angle_to(b) / (8.0 * STEP)
	ramps.clear()
	for r in _ramp_at:
		ramps.append(nearest_global(r))


func count() -> int:
	return pos.size()


## The nearest sample to p anywhere on the track (ignoring height: for setup only).
func nearest_global(p: Vector2) -> int:
	var best := 0
	var bd := INF
	for s in pos.size():
		var d := pos[s].distance_squared_to(p)
		if d < bd:
			bd = d
			best = s
	return best


## The nearest sample to p within `span` samples of `around` (so a car follows its own road where the track crosses).
func nearest_near(p: Vector2, around: int, span := 30) -> int:
	var n := pos.size()
	var best := around
	var bd := INF
	for k in range(-span, span + 1):
		var s := (around + k + n) % n
		var d := pos[s].distance_squared_to(p)
		if d < bd:
			bd = d
			best = s
	return best


## The signed offset of p from the centreline at sample s (+ to the left of the direction of travel).
func offset(p: Vector2, s: int) -> float:
	var d := dir[s]
	return (p - pos[s]).dot(Vector2(-d.y, d.x))


func left_normal(s: int) -> Vector2:
	var d := dir[s]
	return Vector2(-d.y, d.x)
