class_name FrostpeakFlight
extends RefCounted
## A scripted aerial camera move: a smooth spline through waypoints (position and look target), flown at an
## even speed with a gentle start and stop. The path is sampled once, and wherever it would pass lower than
## `clearance` allows (terrain, trees, towers), it is lifted smoothly, so the camera never goes through anything.

const SAMPLES := 900

var duration := 8.0
var t := 0.0
var _pos := PackedVector3Array()
var _look := PackedVector3Array()
var _len := PackedFloat32Array()  ## cumulative arc length at each sample


## `pts` and `looks` have the same size (the first is where the camera is now). `clearance(p)` returns the lowest
## height allowed over p (or -INF); the first and last `hold` of the path keep their heights (they start and end
## by design close to the ground).
func _init(pts: Array[Vector3], looks: Array[Vector3], seconds: float, clearance := Callable(), hold := 0.06) -> void:
	duration = seconds
	var n := pts.size()
	for i in SAMPLES + 1:
		var u := float(i) / SAMPLES * (n - 1)
		var k := mini(int(u), n - 2)
		var f := u - k
		_pos.append(_catmull(pts, k, f))
		_look.append(_catmull(looks, k, f))
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
		for i in SAMPLES + 1:
			_pos[i].y += maxf(spread[i], lift[i])
	_len.append(0.0)
	for i in range(1, SAMPLES + 1):
		_len.append(_len[i - 1] + _pos[i].distance_to(_pos[i - 1]))


## Centripetal-free Catmull-Rom (uniform), with the ends repeated.
func _catmull(p: Array[Vector3], k: int, f: float) -> Vector3:
	var p0 := p[maxi(k - 1, 0)]
	var p1 := p[k]
	var p2 := p[k + 1]
	var p3 := p[mini(k + 2, p.size() - 1)]
	var f2 := f * f
	var f3 := f2 * f
	return 0.5 * ((2.0 * p1) + (-p0 + p2) * f + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * f2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * f3)


func done() -> bool:
	return t >= duration


## Advances the flight and returns [position, look target].
func step(delta: float) -> Array[Vector3]:
	t = minf(t + delta, duration)
	var u := t / duration
	var e := u * u * u * (u * (u * 6.0 - 15.0) + 10.0)  # smootherstep: eases in and out
	var target := e * _len[SAMPLES]
	var lo := 0
	var hi := SAMPLES
	while hi - lo > 1:
		var m := (lo + hi) >> 1
		if _len[m] < target:
			lo = m
		else:
			hi = m
	var seg := maxf(_len[hi] - _len[lo], 0.0001)
	var f := clampf((target - _len[lo]) / seg, 0.0, 1.0)
	return [_pos[lo].lerp(_pos[hi], f), _look[lo].lerp(_look[hi], f)]

