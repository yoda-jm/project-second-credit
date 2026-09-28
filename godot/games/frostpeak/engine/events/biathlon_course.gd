class_name BiathlonCourse
extends RefCounted
## The biathlon venue, one shared definition for the rules and the picture (like SkiHill): the rolling ground of the
## venue, the loop of the course over it, the range beside the stadium straight and the penalty loop.
## World metres (the valley's frame: y up, the valley floor at 0). The loop starts at the start and finish line on
## the stadium straight (heading +x) and is measured in metres `s` along it (0 .. LAP); its height is the ground's.

const LINE := Vector2(-360.0, -200.0)  ## the start and finish line, on the stadium straight
const AREA := Vector2(-330.0, -250.0)  ## the venue's middle
const AREA_R := 230.0  ## its ground fades into the valley's over the last 60 m of this radius
## The loop's waypoints (x, z), a closed centripetal spline through them: the stadium straight, a climb to the east,
## over the shoulder of the hill behind the range, down through the woods and back into the stadium from the west.
const PTS: Array[Vector2] = [Vector2(-360, -200), Vector2(-310, -200), Vector2(-272, -201), Vector2(-250, -218),
	Vector2(-243, -248), Vector2(-258, -278), Vector2(-296, -292), Vector2(-345, -290), Vector2(-385, -274),
	Vector2(-408, -246), Vector2(-404, -217), Vector2(-388, -201)]
const RANGE_S := 22.0  ## the shooter's mat is beside the straight here (s), MAT_OFF to the north
const MAT_OFF := 7.0
const TARGET_DIST := 50.0  ## from the mats to the targets
const PEN_S := 64.0  ## the penalty loop leaves (and rejoins) the straight here
const PEN_A := 11.0  ## the penalty loop: an ellipse south of the straight, tangent to it at PEN_S
const PEN_B := 6.5
const DS := 0.5

static var _pts: PackedVector2Array  ## the loop every DS metres
static var _len := 0.0
static var _ds := DS


static func _build() -> void:
	if not _pts.is_empty():
		return
	var dense: Array[Vector2] = []
	var n := PTS.size()
	for k in n:
		for i in 40:
			dense.append(_catmull(PTS[(k - 1 + n) % n], PTS[k], PTS[(k + 1) % n], PTS[(k + 2) % n], i / 40.0))
	dense.append(dense[0])
	# resample evenly by arc length
	var cum := PackedFloat32Array([0.0])
	for i in range(1, dense.size()):
		cum.append(cum[i - 1] + dense[i].distance_to(dense[i - 1]))
	_len = cum[cum.size() - 1]
	var steps := int(round(_len / DS))
	_ds = _len / steps  # exactly even, so the loop closes without a short last step
	var j := 0
	for k in steps:
		var s := k * _ds
		while cum[j + 1] < s:
			j += 1
		_pts.append(dense[j].lerp(dense[j + 1], (s - cum[j]) / maxf(cum[j + 1] - cum[j], 0.0001)))
	_pts.append(dense[0])


## Centripetal Catmull-Rom between b and c.
static func _catmull(a: Vector2, b: Vector2, c: Vector2, d: Vector2, f: float) -> Vector2:
	var t1 := sqrt(a.distance_to(b))
	var t2 := t1 + sqrt(b.distance_to(c))
	var t3 := t2 + sqrt(c.distance_to(d))
	var t := lerpf(t1, t2, f)
	var a1 := a * ((t1 - t) / t1) + b * (t / t1)
	var a2 := b * ((t2 - t) / (t2 - t1)) + c * ((t - t1) / (t2 - t1))
	var a3 := c * ((t3 - t) / (t3 - t2)) + d * ((t - t2) / (t3 - t2))
	var b1 := a1 * ((t2 - t) / t2) + a2 * (t / t2)
	var b2 := a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
	return b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1))


## The loop's length.
static func lap() -> float:
	_build()
	return _len


## The loop's centre line at s (x, z), any s (wraps round).
static func xz(s: float) -> Vector2:
	_build()
	var f := fposmod(s, _len) / _ds
	var i := mini(int(f), _pts.size() - 2)
	return _pts[i].lerp(_pts[i + 1], f - i)


## The direction of travel at s (x, z), unit.
static func dir(s: float) -> Vector2:
	return (xz(s + 1.0) - xz(s - 1.0)).normalized()


## A point on the loop (on the ground).
static func point(s: float) -> Vector3:
	var p := xz(s)
	return Vector3(p.x, ground(p.x, p.y), p.y)


## The slope at s: rise per metre along the loop (+ uphill).
static func slope(s: float) -> float:
	return (point(s + 1.5).y - point(s - 1.5).y) / 3.0


## How much of the venue's own ground there is at (x, z): 1 inside, fading to 0 at its edge.
static func mask(x: float, z: float) -> float:
	return 1.0 - smoothstep(AREA_R - 60.0, AREA_R, Vector2(x, z).distance_to(AREA))


## The venue's ground: flat in the stadium, a hill to the north-east the course climbs over, a lower rise to the
## north-west, a hollow between them.
static func ground(x: float, z: float) -> float:
	var h := 0.0
	h += 8.5 * exp(-(pow(x + 262.0, 2.0) + pow(z + 305.0, 2.0)) / (62.0 * 62.0))
	h += 5.0 * exp(-(pow(x + 430.0, 2.0) + pow(z + 330.0, 2.0)) / (70.0 * 70.0))
	h += 4.0 * exp(-(pow(x + 330.0, 2.0) + pow(z + 400.0, 2.0)) / (90.0 * 90.0))
	h -= 2.2 * exp(-(pow(x + 330.0, 2.0) + pow(z + 300.0, 2.0)) / (35.0 * 35.0))  # the hollow behind the targets
	# the stadium is level
	var flat := 1.0 - smoothstep(30.0, 68.0, Vector2((x + 330.0) / 1.9, z + 200.0).length())
	return h * (1.0 - flat) * mask(x, z)


## The shooter's mat.
static func mat() -> Vector3:
	var p := point(RANGE_S)
	return p + Vector3(0, 0, -MAT_OFF)


## The centre of the target plate for a lane at the mat (targets face south, towards the range).
static func targets() -> Vector3:
	var m := mat()
	return Vector3(m.x, 0.0, m.z - TARGET_DIST)


static var _pen := PackedFloat32Array()  ## the ellipse's angle every metre round it


## The penalty loop's length.
static func pen_loop() -> float:
	_build_pen()
	return _pen.size() - 1.0


static func _ellipse(a: float) -> Vector2:
	return Vector2(PEN_A * sin(a), -PEN_B * cos(a))


static func _build_pen() -> void:
	if not _pen.is_empty():
		return
	var cum := PackedFloat32Array([0.0])
	var n := 720
	for i in range(1, n + 1):
		cum.append(cum[i - 1] + _ellipse(TAU * i / n).distance_to(_ellipse(TAU * (i - 1) / n)))
	var total := cum[n]
	var j := 0
	var d := 0.0
	var steps := int(round(total))
	for k in steps + 1:
		d = total * k / steps
		while j < n - 1 and cum[j + 1] < d:
			j += 1
		_pen.append(TAU * (j + clampf((d - cum[j]) / maxf(cum[j + 1] - cum[j], 0.0001), 0.0, 1.0)) / n)


## A point on the penalty loop, `u` metres round it from where it leaves the straight (east, round to the south,
## back west, and up to the straight again).
static func pen_point(u: float) -> Vector3:
	_build_pen()
	var f := fposmod(u, pen_loop()) * (_pen.size() - 1.0) / pen_loop()
	var i := mini(int(f), _pen.size() - 2)
	var a := lerpf(_pen[i], _pen[i + 1], f - i)
	var p := xz(PEN_S)
	var q := Vector2(p.x, p.y + PEN_B) + _ellipse(a)
	return Vector3(q.x, ground(q.x, q.y), q.y)
