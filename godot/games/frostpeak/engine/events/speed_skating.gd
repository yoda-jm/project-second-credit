class_name SpeedSkating
extends WinterEvent
## 500 m speed skating against a rival in the other lane. Push with alternating left and right strides: each
## stride fills a rhythm meter; the next push is strongest when the meter is in its green zone. The wrong foot,
## or pushing too early, costs speed. Going before the gun is a false start (one allowed).

const DISTANCE := 500.0
const PERFECT := 1.7  ## m/s gained by a push in the green zone (meter 0.8 .. 1.0)
const GOOD := 0.55  ## a little early (0.62 .. 0.8) or late (after 1.0)
const WEAK := 0.1  ## too early: the stride is wasted
const GREEN := Vector2(0.8, 1.0)
const DRAG := 0.012  ## per (m/s)^2
const FRICTION := 0.12

var pos := 0.0
var speed := 0.0
var meter := 0.0  ## 0..1+ : 1 is the end of the stride
var next_foot := "left"
var rival_pos := 0.0
var rival_speed := 0.0
var rival_skill := 0.75
var false_starts := 0
var last_push := ""  ## "perfect", "good", "weak", "wrong"


func stride_time() -> float:
	return clampf(0.9 - speed * 0.015, 0.6, 0.9)


func early(l: bool, r: bool, a: bool) -> void:
	if l or r:
		false_starts += 1
		phase_left = 3.0
		event.emit("false_start", {"count": false_starts})
		if false_starts >= 2:
			finish(99.99, "DISQUALIFIED")


func run(l: bool, r: bool, _a: bool) -> void:
	meter += TICK / stride_time()
	var foot := "left" if l else ("right" if r else "")
	if foot != "":
		if foot != next_foot:
			speed = maxf(0.0, speed - 0.6)
			last_push = "wrong"
			event.emit("stumble", {})
		else:
			var gain := WEAK
			last_push = "weak"
			if meter >= GREEN.x and meter <= GREEN.y:
				gain = PERFECT
				last_push = "perfect"
			elif meter >= 0.62:
				gain = GOOD
				last_push = "good"
			if speed < 3.0:
				gain = maxf(gain, GOOD)  # the first strides off the line always bite
			speed += gain
			meter = 0.0
			next_foot = "right" if foot == "left" else "left"
			event.emit("stride", {"foot": foot, "quality": last_push})
	speed = maxf(0.0, speed - (DRAG * speed * speed + FRICTION) * TICK)
	pos += speed * TICK
	# the rival: a steady, skill-shaped race
	var target := lerpf(12.0, 14.6, rival_skill) * minf(1.0, time / 4.5)
	rival_speed = move_toward(rival_speed, target, 4.0 * TICK)
	rival_pos += rival_speed * TICK
	if pos >= DISTANCE:
		finish(snappedf(time, 0.01), "%.2f s" % time)


func autoplay() -> void:
	if phase != Phase.RUN:
		return
	var aim := 0.83 + rng.randf_range(-0.35, 0.35) * (1.0 - skill)  # the best push early in the green zone
	if meter >= aim:
		press(next_foot)
