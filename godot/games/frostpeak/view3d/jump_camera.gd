class_name FrostpeakJumpCam
extends RefCounted
## The ski jump's live TV camera: one continuous move, never a cut. It rides with the jumper like a cable camera,
## placed round them by a few numbers (how far round from behind, how high, how far, which way "ahead" points), and
## every number glides to its next value on a critically damped spring. So the camera settles behind the jumper on
## the bar, follows down the in-run, swings round to a three-quarter side view as they leave the table, tracks the
## flight and the landing, and comes round in front as they stop in the arena, all in one smooth move.
## Everything is in the hill's frame (x downhill, y up, z across; the side cameras look from +z).

## Where the camera is round the jumper. `az`: 0 behind, PI/2 beside (+z), PI in front; `el`: up from the path;
## `dist`: metres; `pitch`: the path's slope (radians, down); `ahead`: the look point, metres along the path;
## `lift`: and up from the jumper; `fov`: the lens.
const KEYS := ["az", "el", "dist", "pitch", "ahead", "lift", "fov"]
## the pose on arrival at the gate (the flight in ends here)
const GATE := {"az": 0.62, "el": 0.52, "dist": 8.5, "pitch": deg_to_rad(35.0), "ahead": 6.0, "lift": 0.9, "fov": 52.0}

var value := {}
var vel := {}
var target := {}
var omega := {}  ## how quickly each number follows (1/s)
var ground := Callable()  ## ground height (hill frame) under x, z


func _init(ground_y: Callable) -> void:
	ground = ground_y
	reset(GATE)


func reset(pose: Dictionary) -> void:
	for k in KEYS:
		value[k] = pose[k]
		vel[k] = 0.0
		target[k] = pose[k]
		omega[k] = 2.0


## The critically damped spring (exact for any step): no overshoot, no jolt when the target moves.
static func spring(x: float, v: float, to: float, w: float, dt: float) -> Vector2:
	var d := x - to
	var e := exp(-w * dt)
	var tmp := (v + w * d) * dt
	return Vector2(to + (d + tmp) * e, (v - w * tmp) * e)


func aim(k: String, to: float, w: float) -> void:
	target[k] = to
	omega[k] = w


func step(dt: float) -> void:
	for k in KEYS:
		var r := spring(value[k], vel[k], target[k], omega[k], dt)
		value[k] = r.x
		vel[k] = r.y


## [camera, look target] round a jumper at `p` for a pose (the current one if none is given).
func pose(p: Vector3, v: Dictionary = {}) -> Array[Vector3]:
	if v.is_empty():
		v = value
	var pitch: float = v["pitch"]
	var fwd := Vector3(cos(pitch), -sin(pitch), 0.0)
	var up := Vector3(sin(pitch), cos(pitch), 0.0)
	var az: float = v["az"]
	var el: float = v["el"]
	var d: float = v["dist"]
	var cam := p + (-fwd * cos(az) * cos(el) + up * sin(el)) * d + Vector3(0, 0, sin(az) * cos(el) * d)
	if ground.is_valid():  # never into the snow: a soft floor two metres over it
		var g: float = ground.call(cam.x, cam.z) + 2.0
		var h := clampf(0.5 + 0.5 * (cam.y - g) / 1.5, 0.0, 1.0)  # a smooth max, so the floor never kinks the path
		cam.y = lerpf(g, cam.y, h) + 1.5 * h * (1.0 - h)
	var look := p + fwd * float(v["ahead"]) + Vector3(0, float(v["lift"]), 0)
	return [cam, look]
