class_name FrostpeakFlight
extends RefCounted
## A scripted aerial camera move: a smooth spline through waypoints (position and look target), flown at an
## even speed with a gentle start and stop, or (with `paces`) fast over the far stretches and slow on the approach,
## never turning or braking hard. The path is sampled once, and wherever it would pass lower than `clearance` allows
## (terrain, trees, towers), it is lifted smoothly, so the camera never goes through anything.

const SAMPLES := 900
const MAX_TURN := 0.7  ## with paces: where the camera would turn faster than this (radians a second), it slows down
const MAX_ACCEL := 26.0  ## with paces: and it never speeds up or brakes harder than this (m/s^2)
const MAX_SIDE := 30.0  ## nor corners harder than this (m/s^2)

var duration := 8.0
var t := 0.0
var _pos := PackedVector3Array()
var _look := PackedVector3Array()
var _len := PackedFloat32Array()  ## cumulative arc length at each sample
var _tt := PackedFloat32Array()  ## with paces: the second each sample is reached at


## `pts` and `looks` have the same size (the first is where the camera is now). `clearance(p)` returns the lowest
## height allowed over p (or -INF); the first and last `hold` of the path keep their heights (they start and end
## by design close to the ground).
## `paces` (one per waypoint) are relative speeds: the flight slows smoothly wherever the pace is low, so a long
## glide over the valley can end in a slow, even approach.
func _init(pts: Array[Vector3], looks: Array[Vector3], seconds: float, clearance := Callable(), hold := 0.06,
		paces: Array[float] = []) -> void:
	duration = seconds
	var n := pts.size()
	for i in SAMPLES + 1:
		var u := float(i) / SAMPLES * (n - 1)
		var k := mini(int(u), n - 2)
		var f := u - k
		_pos.append(_catmull(pts, k, f))
		_look.append(_catmull(looks, k, f))
	_smooth(3)
	if clearance.is_valid():
		# lift: how far each sample is under its allowed height, spread smoothly along the path
		var lift := PackedFloat32Array()
		lift.resize(SAMPLES + 1)
		for i in SAMPLES + 1:
			var w := smoothstep(0.0, hold, float(i) / SAMPLES) * smoothstep(1.0, 1.0 - hold, float(i) / SAMPLES)
			var need: float = clearance.call(_pos[i])
			lift[i] = maxf(0.0, need - _pos[i].y) * w
		var spread := lift.duplicate()
		for i in SAMPLES + 1:  # a wide max filter, then a blur, so the camera climbs early and eases over
			var m := 0.0
			for j in range(maxi(0, i - 60), mini(SAMPLES, i + 60) + 1):
				m = maxf(m, lift[j] * (1.0 - absf(j - i) / 70.0))
			spread[i] = m
		for pass_ in 3:
			var b := spread.duplicate()
			for i in range(1, SAMPLES):
				b[i] = (spread[i - 1] + spread[i] * 2.0 + spread[i + 1]) * 0.25
			spread = b
		for i in SAMPLES + 1:  # (the held ends stay put: the lift fades in and out over them too)
			var w := smoothstep(0.0, hold, float(i) / SAMPLES) * smoothstep(1.0, 1.0 - hold, float(i) / SAMPLES)
			_pos[i].y += maxf(spread[i] * w, lift[i])
	_smooth(2)  # (again: the lift over the obstacles leaves corners of its own)
	_len.append(0.0)
	for i in range(1, SAMPLES + 1):
		_len.append(_len[i - 1] + _pos[i].distance_to(_pos[i - 1]))
	if paces.size() == n:
		var pace := PackedFloat32Array()  # paces blend smoothly between the waypoints
		pace.resize(SAMPLES + 1)
		for i in SAMPLES + 1:
			var u := float(i) / SAMPLES * (n - 1)
			var k := mini(int(u), n - 2)
			var f := u - k
			pace[i] = maxf(lerpf(paces[k], paces[k + 1], f * f * (3.0 - 2.0 * f)), 0.001)
		_profile(pace)


## The flight's clock with paces, planned like a camera operator would: the speed follows the paces, but never
## turns the lens faster than MAX_TURN, never speeds up or slows down harder than MAX_ACCEL, and starts and ends at
## rest; one overall scale makes the whole flight last `duration`.
func _profile(pace: PackedFloat32Array) -> void:
	var ds := PackedFloat32Array()
	var cap := PackedFloat32Array()  # the most speed each sample allows for the turn it makes
	ds.resize(SAMPLES + 1)
	cap.resize(SAMPLES + 1)
	for i in range(1, SAMPLES + 1):
		ds[i] = _len[i] - _len[i - 1]
		# (the turn of the whole lens, which looking steeply down turns further than its line of sight moves)
		var a := Basis.looking_at(_look[i - 1] - _pos[i - 1], Vector3.UP).get_rotation_quaternion()
		var b := Basis.looking_at(_look[i] - _pos[i], Vector3.UP).get_rotation_quaternion()
		var ang := a.angle_to(b)
		cap[i] = MAX_TURN * ds[i] / ang if ang > 0.000001 else INF
		if i > 1:  # and never swings round a bend harder than MAX_SIDE
			var bend := (_pos[i - 1] - _pos[i - 2]).angle_to(_pos[i] - _pos[i - 1])
			if bend > 0.000001:
				cap[i] = minf(cap[i], sqrt(MAX_SIDE * ds[i] / bend))
	var lo := 0.0001
	var hi := 10000.0
	var v := PackedFloat32Array()
	for it in 40:
		var sc := sqrt(lo * hi)
		v = _speeds(pace, ds, cap, sc)
		if _total(ds, v) > duration:
			lo = sc
		else:
			hi = sc
	v = _speeds(pace, ds, cap, hi)
	var total := _total(ds, v)
	_tt.resize(SAMPLES + 1)
	_tt[0] = 0.0
	for i in range(1, SAMPLES + 1):
		_tt[i] = _tt[i - 1] + ds[i] / maxf((v[i - 1] + v[i]) * 0.5, 0.0001)
	for i in SAMPLES + 1:  # (if it could not fit, it runs a little faster everywhere)
		_tt[i] *= duration / maxf(total, 0.0001)


func _speeds(pace: PackedFloat32Array, ds: PackedFloat32Array, cap: PackedFloat32Array, sc: float) -> PackedFloat32Array:
	var v := PackedFloat32Array()
	v.resize(SAMPLES + 1)
	for i in SAMPLES + 1:
		v[i] = minf(pace[i] * sc, cap[i] if i > 0 else INF)
		if i > 0:
			v[i] = minf(v[i], cap[mini(i + 1, SAMPLES)])
	v[0] = 0.0
	v[SAMPLES] = 0.0
	for pass_ in 2:  # the pull and the brake, gently: a speed limit from both ends, then smoothed
		for i in range(1, SAMPLES + 1):
			v[i] = minf(v[i], sqrt(v[i - 1] * v[i - 1] + 2.0 * MAX_ACCEL * ds[i]))
		for i in range(SAMPLES - 1, -1, -1):
			v[i] = minf(v[i], sqrt(v[i + 1] * v[i + 1] + 2.0 * MAX_ACCEL * ds[i + 1]))
		var b := v.duplicate()
		for i in range(1, SAMPLES):
			b[i] = minf(v[i], (v[i - 1] + v[i] * 2.0 + v[i + 1]) * 0.25)
		v = b
	for i in range(1, SAMPLES):
		v[i] = maxf(v[i], 0.02)
	return v


func _total(ds: PackedFloat32Array, v: PackedFloat32Array) -> float:
	var t := 0.0
	for i in range(1, SAMPLES + 1):
		t += ds[i] / maxf((v[i - 1] + v[i]) * 0.5, 0.0001)
	return t


## Eases every corner: a moving average along the path, the ends pinned (they are poses the camera must reach).
func _smooth(passes: int) -> void:
	for pass_ in passes:
		var sm := _pos.duplicate()
		var sl := _look.duplicate()
		for i in range(1, SAMPLES):
			var pin := smoothstep(0.0, 0.05, float(i) / SAMPLES) * smoothstep(1.0, 0.95, float(i) / SAMPLES)
			var w := int(18.0 * pin)
			var pin_l := smoothstep(0.0, 0.03, float(i) / SAMPLES) * smoothstep(1.0, 0.985, float(i) / SAMPLES)
			var wl := int(45.0 * pin_l)  # the gaze changes more gently still, nearly to the end
			if w >= 1:
				var a := Vector3.ZERO
				for j in range(i - w, i + w + 1):
					a += _pos[clampi(j, 0, SAMPLES)]
				sm[i] = a / (2 * w + 1)
			if wl >= 1:
				var b := Vector3.ZERO
				for j in range(i - wl, i + wl + 1):
					b += _look[clampi(j, 0, SAMPLES)]
				sl[i] = b / (2 * wl + 1)
		_pos = sm
		_look = sl


## Centripetal Catmull-Rom (Barry and Goldman's form, knots spaced by the square root of the distances), with the
## ends repeated: unlike the uniform form it never loops or overshoots where waypoints are unevenly spaced.
func _catmull(p: Array[Vector3], k: int, f: float) -> Vector3:
	var p1 := p[k]
	var p2 := p[k + 1]
	var p0 := p[k - 1] if k > 0 else p1 - (p2 - p1)
	var p3 := p[k + 2] if k + 2 < p.size() else p2 + (p2 - p1)
	var t1 := sqrt(maxf(p0.distance_to(p1), 0.0001))
	var t2 := t1 + sqrt(maxf(p1.distance_to(p2), 0.0001))
	var t3 := t2 + sqrt(maxf(p2.distance_to(p3), 0.0001))
	var t := lerpf(t1, t2, f)
	var a1 := p0 * ((t1 - t) / t1) + p1 * (t / t1)
	var a2 := p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
	var a3 := p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
	var b1 := a1 * ((t2 - t) / t2) + a2 * (t / t2)
	var b2 := a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
	return b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1))


func done() -> bool:
	return t >= duration


## Advances the flight and returns [position, look target].
func step(delta: float) -> Array[Vector3]:
	t = minf(t + delta, duration)
	return sample(t)


## Where the flight is `at` seconds in: [position, look target].
func sample(at: float) -> Array[Vector3]:
	var u := clampf(at / duration, 0.0, 1.0)
	var table := _len
	var target := 0.0
	if _tt.is_empty():
		var e := u * u * u * (u * (u * 6.0 - 15.0) + 10.0)  # smootherstep: eases in and out
		target = e * _len[SAMPLES]
	else:
		target = u * duration
		table = _tt
	var lo := 0
	var hi := SAMPLES
	while hi - lo > 1:
		var m := (lo + hi) >> 1
		if table[m] < target:
			lo = m
		else:
			hi = m
	var seg := maxf(table[hi] - table[lo], 0.0001)
	var f := clampf((target - table[lo]) / seg, 0.0, 1.0)
	return [_pos[lo].lerp(_pos[hi], f), _look[lo].lerp(_look[hi], f)]

