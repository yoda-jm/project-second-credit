class_name BobTrack
extends RefCounted
## The bobsled run, one shared definition for the rules and the picture (like SkiHill and BiathlonCourse): an ice
## channel down a forested spur at the north of the valley, eleven named curves, from the start house at the top to
## the finish and the uphill run-out at the foot. World metres (the valley's frame: y up, the valley floor at 0).
## Distances `s` are metres along the centre line from the start block.
##
## The line is built like a real track is surveyed: straights and circular curves joined by transition spirals (the
## curvature ramps in over RAMP metres), so the rules can ask for the curvature anywhere. Its height follows a
## designed profile (a gentle push stretch, then 8 to 15 %). The channel's section: a flat floor FLOOR metres either
## side of the centre, then a wall that curves up to vertical over `wall(s, side)` metres of surface: low (WALL) on
## straights and on the inside of curves, a tall banked wall (BANK) on the outside of every curve, where the sled
## rides up at speed. Lateral positions `w`: see `section`.

const START := Vector2(30.0, -1135.0)  ## the start block (x, z)
const HEADING := 15.0  ## the start straight's heading, degrees (0 = +x, 90 = +z, south, down the valley)
const RAMP := 14.0  ## the transition spirals into and out of every curve
## The line: [metres] of straight, or [turn degrees (+ right), radius].
const LINE: Array = [[60.0], [50.0, 50.0], [50.0], [70.0, 30.0], [40.0], [-120.0, 27.0], [45.0], [165.0, 25.0], [40.0],
	[-100.0, 30.0], [20.0], [-45.0, 32.0], [8.0], [70.0, 30.0], [8.0], [-60.0, 30.0], [30.0], [110.0, 27.0], [45.0],
	[-75.0, 29.0], [20.0], [15.0, 80.0], [55.0]]
## The curves' names, in order.
const NAMES: Array[String] = ["LARCH", "CHAPEL", "FOX HOLLOW", "HORSESHOE", "STAG", "LABYRINTH I", "LABYRINTH II",
	"LABYRINTH III", "GLACIER BEND", "LAST LOOK", "FINISH BEND"]
## The height profile: [s, y] knots, joined by a monotone cubic.
const PROFILE: Array = [[0.0, 110.0], [50.0, 108.8], [90.0, 105.0], [150.0, 96.0], [250.0, 82.0], [330.0, 70.0],
	[400.0, 60.0], [470.0, 52.0], [540.0, 46.0], [600.0, 40.0], [680.0, 30.5], [760.0, 21.0], [840.0, 12.5], [900.0, 7.5],
	[950.0, 4.0], [975.0, 2.6], [1000.0, 2.5], [1045.0, 4.2]]
const START_LINE := 15.0  ## the clock starts here (the first timing eye)
const PUSH_END := 55.0  ## the crew must be in by here (the start ramp's end)
const FINISH := 965.0  ## the finish line; the run-out climbs gently beyond it
const SPLITS: Array[float] = [65.0, 360.0, 660.0]  ## intermediate timing eyes (s), before the finish
const FLOOR := 0.7  ## the flat floor, either side of the centre
const WALL := 1.2  ## the low wall's surface, floor to vertical (straights, the inside of curves)
const BANK := 5.0  ## the outer wall in a curve, floor to vertical
const BANK_R := 45.0  ## curves this tight or tighter get the full bank
const DS := 0.25

static var _xz := PackedVector2Array()  ## the centre line every DS
static var _th := PackedFloat32Array()  ## heading (radians)
static var _k := PackedFloat32Array()  ## curvature (1/m, + right)
static var _y := PackedFloat32Array()
static var _curves: Array = []  ## [s in, s out, turn (radians, + right), radius, name]


static func _build() -> void:
	if not _xz.is_empty():
		return
	var ks := PackedFloat32Array()
	var n := int(RAMP / DS)
	var ci := 0
	var s := 0.0
	for seg in LINE:
		if seg.size() == 1:
			for i in int(round(seg[0] / DS)):
				ks.append(0.0)
			s += seg[0]
			continue
		var a := deg_to_rad(seg[0])
		var r: float = seg[1]
		var k := signf(a) / r
		var lc := absf(a) * r - RAMP  # the constant part (the spirals turn RAMP / r between them)
		var s0 := ks.size() * DS
		for i in n:
			ks.append(k * (i + 0.5) / n)
		for i in int(round(lc / DS)):
			ks.append(k)
		for i in n:
			ks.append(k * (1.0 - (i + 0.5) / n))
		_curves.append([s0, ks.size() * DS, a, r, NAMES[ci] if ci < NAMES.size() else "CURVE %d" % (ci + 1)])
		ci += 1
	var th := deg_to_rad(HEADING)
	var p := START
	_xz.append(p)
	_th.append(th)
	_k.append(0.0)
	for k in ks:
		th += k * DS
		p += Vector2(cos(th), sin(th)) * DS
		_xz.append(p)
		_th.append(th)
		_k.append(k)
	# the profile: a monotone cubic through the knots (Fritsch-Carlson), sampled every DS
	var m := PackedFloat32Array()
	var d := PackedFloat32Array()
	for i in PROFILE.size() - 1:
		d.append((PROFILE[i + 1][1] - PROFILE[i][1]) / (PROFILE[i + 1][0] - PROFILE[i][0]))
	m.append(d[0])
	for i in range(1, PROFILE.size() - 1):
		m.append(0.0 if d[i - 1] * d[i] <= 0.0 else 2.0 / (1.0 / d[i - 1] + 1.0 / d[i]))
	m.append(d[d.size() - 1])
	var j := 0
	for i in _xz.size():
		var t := i * DS
		while j < PROFILE.size() - 2 and t > PROFILE[j + 1][0]:
			j += 1
		var h: float = PROFILE[j + 1][0] - PROFILE[j][0]
		var u := clampf((t - PROFILE[j][0]) / h, 0.0, 1.0)
		var u2 := u * u
		var u3 := u2 * u
		_y.append((2.0 * u3 - 3.0 * u2 + 1.0) * PROFILE[j][1] + (u3 - 2.0 * u2 + u) * h * m[j]
			+ (-2.0 * u3 + 3.0 * u2) * PROFILE[j + 1][1] + (u3 - u2) * h * m[j + 1])


## The whole run's length (to the end of the run-out).
static func length() -> float:
	_build()
	return (_xz.size() - 1) * DS


static func _f(s: float) -> Vector2:
	var f := clampf(s, 0.0, length()) / DS
	var i := mini(int(f), _xz.size() - 2)
	return Vector2(i, f - i)


## The centre line at s (x, z).
static func xz(s: float) -> Vector2:
	_build()
	var f := _f(s)
	var i := int(f.x)
	return _xz[i].lerp(_xz[i + 1], f.y)


## The heading at s (radians: 0 = +x, PI/2 = +z).
static func heading(s: float) -> float:
	_build()
	var f := _f(s)
	return lerpf(_th[int(f.x)], _th[int(f.x) + 1], f.y)


## The direction of travel at s (x, z), unit.
static func dir(s: float) -> Vector2:
	var h := heading(s)
	return Vector2(cos(h), sin(h))


## The curvature at s (1/m, + turning right).
static func kappa(s: float) -> float:
	_build()
	var f := _f(s)
	return lerpf(_k[int(f.x)], _k[int(f.x) + 1], f.y)


## The centre line's height at s.
static func y(s: float) -> float:
	_build()
	var f := _f(s)
	return lerpf(_y[int(f.x)], _y[int(f.x) + 1], f.y)


## The slope: rise per metre along the run (negative downhill).
static func grade(s: float) -> float:
	return (y(s + 0.5) - y(s - 0.5))


## The centre of the channel's floor at s.
static func point(s: float) -> Vector3:
	var p := xz(s)
	return Vector3(p.x, y(s), p.y)


## The horizontal unit vector to the right of the direction of travel at s.
static func right(s: float) -> Vector3:
	var h := heading(s)
	return Vector3(-sin(h), 0.0, cos(h))


## How much of the tall bank the outside wall has at s (0 on straights, 1 in a curve of BANK_R or tighter).
static func bank_k(s: float) -> float:
	return smoothstep(0.0, 1.0, absf(kappa(s)) * BANK_R)


## The wall's surface length (floor to vertical) on one side (+1 right, -1 left) at s: the outside of a curve banks
## up (the curve's bank starts to rise a little before the curvature does, so the sled finds it there).
static func wall(s: float, side: float) -> float:
	var k := kappa(s)
	var ahead := kappa(s + 6.0)
	var kk := k if absf(k) > absf(ahead) else ahead
	if kk * side >= 0.0:  # the inside (the side the curve turns to) keeps the low wall
		return WALL
	return lerpf(WALL, BANK, smoothstep(0.0, 1.0, absf(kk) * BANK_R))


## Where a lateral position `w` sits in the channel's section at s. `w` is metres across the floor from the centre
## (+ right) out to FLOOR, and past that the wall's angle in radians added on (FLOOR + PI/2 is the top of the wall,
## where it stands vertical), so a sled high on a bank stays at the same angle as the bank shrinks under it at the
## curve's exit, and slides down with it. Returns x across (+ right), y up from the floor, and the wall's angle.
static func section(s: float, w: float) -> Vector3:
	var a := absf(w)
	var side := signf(w) if w != 0.0 else 1.0
	if a <= FLOOR:
		return Vector3(w * floor_half(s) / FLOOR, 0.0, 0.0)
	var al := minf(a - FLOOR, PI * 0.5)
	var q := profile(s, side, al)
	return Vector3(side * q.x, q.y, al)


## The wall's shape on one side (+1 right, -1 left): at angle `al` up it (radians), how far out from the centre
## and how high above the floor it is (a quarter circle of the wall's length).
static func profile(s: float, side: float, al: float) -> Vector2:
	var rb := wall(s, side) / (PI * 0.5)
	return Vector2(floor_half(s) + rb * sin(al), rb * (1.0 - cos(al)))


## Half the floor's width: wide on the start ramp (the crew runs beside the sled), FLOOR from the first curve on.
static func floor_half(s: float) -> float:
	return lerpf(1.5, FLOOR, smoothstep(PUSH_END, PUSH_END + 20.0, s))


## The wall's radius on a side at s (metres): its length over a quarter turn.
static func wall_r(s: float, side: float) -> float:
	return wall(s, side) / (PI * 0.5)


## A point on the channel's surface at (s, w), in the world.
static func surface(s: float, w: float) -> Vector3:
	var q := section(s, w)
	return point(s) + right(s) * q.x + Vector3(0, q.y, 0)


## The lateral position at the top of the wall on a side (+1 right, -1 left).
static func lip(side: float) -> float:
	return side * (FLOOR + PI * 0.5)


## The curves: [s in, s out, turn (radians, + right), radius, name].
static func curves() -> Array:
	_build()
	return _curves


## The curve at s (its index), or -1 on a straight.
static func curve_at(s: float) -> int:
	_build()
	for i in _curves.size():
		if s >= _curves[i][0] and s <= _curves[i][1]:
			return i
	return -1
