class_name SkiHill
extends RefCounted
## The large jump hill (K 120, HS 134), one shared definition for the rules and the picture, laid out like a FIS
## hill: a 35 degree in-run, a transition curve (radius 100 m) into an 11 degree take-off table 6.5 m long; the
## knoll, the landing slope steepening to 37.4 degrees at P, 35.5 at the K point and 32.1 at the hill size (L),
## then a curve (radius 105 m) into the flat outrun, which ends in a gentle counter-slope.
## 2D, metres, origin at the take-off edge (the lip): x forward (downhill), y up. The in-run is measured in metres
## "along" from the start gate (0) to the lip (INRUN); the landing profile by its arc length s from the foot of
## the table (distances are measured along it, as on a real hill).

const K := 120.0
const HS := 134.0
const P := 100.0  ## start of the landing area
const INRUN := 94.0  ## from the start gate to the lip
const TOP := -14.0  ## the in-run is built this far above the gate (higher gates, the start platform)
const GAMMA := deg_to_rad(35.0)  ## in-run angle
const ALPHA := deg_to_rad(11.0)  ## take-off table angle (downwards)
const R1 := 100.0  ## in-run transition radius
const TABLE := 6.5  ## take-off table length
const TABLE_H := 3.0  ## height of the lip above the knoll
const BETA_0 := deg_to_rad(6.0)  ## the knoll's angle at the foot of the table
const KNOLL := 90.0  ## the knoll curves down over this arc length
const BETA_P := deg_to_rad(37.4)
const BETA_K := deg_to_rad(35.5)
const BETA_L := deg_to_rad(32.1)
const R2 := 105.0  ## transition radius into the outrun
const COUNTER_AT := 250.0  ## the outrun's counter-slope starts here
const COUNTER := deg_to_rad(4.0)
const END := 330.0  ## the profile's last metre
const DS := 0.25

static var _land: PackedVector2Array  ## landing profile points every DS metres of arc
static var _inrun: PackedVector2Array  ## in-run points every DS metres, from TOP to INRUN


## The in-run's slope (radians, downwards) `along` metres from the gate.
static func inrun_angle(along: float) -> float:
	if along >= INRUN - TABLE:
		return ALPHA
	var curve := R1 * (GAMMA - ALPHA)
	if along >= INRUN - TABLE - curve:
		return ALPHA + (INRUN - TABLE - along) / R1
	return GAMMA


## The landing profile's slope (radians, downwards; negative on the counter-slope) at arc length s.
static func land_angle(s: float) -> float:
	if s < KNOLL:
		var u := s / KNOLL
		return BETA_0 + (BETA_P - BETA_0) * (1.0 - pow(1.0 - u, 2.2))
	if s < P:
		return BETA_P
	if s < K:
		return lerpf(BETA_P, BETA_K, (s - P) / (K - P))
	if s < HS:
		return lerpf(BETA_K, BETA_L, (s - K) / (HS - K))
	var a := maxf(0.0, BETA_L - (s - HS) / R2)
	if s > COUNTER_AT:
		var u := clampf((s - COUNTER_AT) / 50.0, 0.0, 1.0)
		a -= COUNTER * sin(u * PI)  # up, and level again
	return a


static func _build() -> void:
	if not _land.is_empty():
		return
	var p := Vector2(0.0, -TABLE_H)
	_land.append(p)
	var s := 0.0
	while s < END:
		var a := land_angle(s + DS * 0.5)
		p += Vector2(cos(a), -sin(a)) * DS
		s += DS
		_land.append(p)
	# the in-run, integrated back up from the lip
	var n := int((INRUN - TOP) / DS)
	var pts: Array[Vector2] = [Vector2.ZERO]
	var q := Vector2.ZERO
	for i in n:
		var along := INRUN - (i + 0.5) * DS
		var a := inrun_angle(along)
		q += Vector2(-cos(a), sin(a)) * DS
		pts.append(q)
	pts.reverse()
	_inrun = PackedVector2Array(pts)


## A point on the landing profile at arc length s (clamped to the profile).
static func land_point(s: float) -> Vector2:
	_build()
	var f := clampf(s, 0.0, END) / DS
	var i := mini(int(f), _land.size() - 2)
	return _land[i].lerp(_land[i + 1], f - i)


## A point on the in-run `along` metres from the gate (TOP .. INRUN).
static func inrun_point(along: float) -> Vector2:
	_build()
	var f := (clampf(along, TOP, INRUN) - TOP) / DS
	var i := mini(int(f), _inrun.size() - 2)
	return _inrun[i].lerp(_inrun[i + 1], f - i)


## The index of the profile segment under x (x >= 0).
static func _seg(x: float) -> int:
	_build()
	var lo := 0
	var hi := _land.size() - 1
	while hi - lo > 1:
		var m := (lo + hi) >> 1
		if _land[m].x < x:
			lo = m
		else:
			hi = m
	return lo


## The ground's height under x (0 .. the end of the outrun); the table's foot for x < 0.
static func ground_y(x: float) -> float:
	if x <= 0.0:
		return -TABLE_H
	var i := _seg(x)
	var a := _land[i]
	var b := _land[i + 1]
	return lerpf(a.y, b.y, clampf((x - a.x) / maxf(b.x - a.x, 0.0001), 0.0, 1.0))


## The distance (arc length along the profile) of the ground point under x.
static func distance_at(x: float) -> float:
	if x <= 0.0:
		return 0.0
	var i := _seg(x)
	var a := _land[i]
	var b := _land[i + 1]
	return (i + clampf((x - a.x) / maxf(b.x - a.x, 0.0001), 0.0, 1.0)) * DS


## Where the flat outrun meets the counter-slope, and its height (below the lip).
static func outrun_y() -> float:
	return land_point(COUNTER_AT).y
