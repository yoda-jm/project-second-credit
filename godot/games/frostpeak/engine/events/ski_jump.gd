class_name SkiJump
extends WinterEvent
## K90 ski jump. On the in-run hold DOWN to tuck (faster). At the lip press ACTION: the closer to the edge, the better
## the take-off. In the air the body angle drifts: hold it in the ideal band with UP and DOWN; the better the angle,
## the more lift. Press ACTION just before touchdown for a telemark landing (worth style points); a wild body
## angle at touchdown, or landing far beyond the hill, is a fall.
## Distance points (60 at K, 2 per metre) plus style points (five judges, the best and the worst dropped).

const K := 90.0
const INRUN := 92.0  ## metres of in-run
const LIP_WINDOW := 0.35  ## seconds either side of the lip where a take-off counts
const IDEAL := 0.0  ## body angle offset from the ideal, radians
const HILL_SLOPE := 0.62  ## the landing hill drops this many metres per metre beyond the knoll

enum Stage { INRUN, FLIGHT, LANDED }

var stage := Stage.INRUN
var along := 0.0  ## metres down the in-run
var speed := 0.0
var tuck := 0.0  ## 0 upright .. 1 tucked
var takeoff := 0.0  ## quality 0..1
var angle := 0.0  ## body angle error in the air
var fly := Vector2.ZERO  ## flight position relative to the lip (x forward, y up)
var vel := Vector2.ZERO
var distance := 0.0
var telemark := false
var fell := false
var style := 0.0
var judges: Array[float] = []
var _lip_time := -1.0
var _land_press := -1.0


func hill_y(x: float) -> float:
	## Height of the landing hill below the lip (negative), a smooth knoll then a steady slope.
	return -(3.0 + x * HILL_SLOPE - 18.0 * exp(-x / 25.0) + 18.0) * 0.5


func run(_l: bool, _r: bool, a: bool) -> void:
	match stage:
		Stage.INRUN:
			tuck = move_toward(tuck, 1.0 if hold_down else 0.0, TICK * 3.0)
			var acc := 9.81 * 0.42 - (0.0042 - 0.0016 * tuck) * speed * speed
			speed += acc * TICK
			along += speed * TICK
			if a and _lip_time < 0.0:
				_lip_time = time
				var off := absf(along - INRUN) / maxf(speed, 1.0)
				takeoff = clampf(1.0 - off / LIP_WINDOW, 0.0, 1.0) if along > INRUN - speed * LIP_WINDOW else 0.0
			if along >= INRUN:
				if _lip_time < 0.0:
					takeoff = 0.15  # no jump: slides off the lip
				stage = Stage.FLIGHT
				vel = Vector2(speed * 0.96, 1.2 + 2.6 * takeoff)
				angle = rng.randf_range(-0.1, 0.1) + (1.0 - takeoff) * 0.25
				event.emit("takeoff", {"quality": takeoff, "speed_kmh": speed * 3.6})
		Stage.FLIGHT:
			# the angle wanders; the player leans it back
			angle += rng.randf_range(-0.9, 0.9) * TICK + angle * 0.6 * TICK
			if hold_up:
				angle -= 1.1 * TICK
			if hold_down:
				angle += 1.1 * TICK
			var lift := 0.17 * clampf(1.0 - absf(angle - IDEAL) / 0.5, 0.0, 1.0) * (0.6 + 0.4 * takeoff)
			var drag := 0.0009 + 0.002 * absf(angle)
			vel.y -= (9.81 - lift * vel.x) * TICK
			vel.x -= drag * vel.x * vel.x * TICK
			fly += vel * TICK
			if a and _land_press < 0.0:
				_land_press = time
			if fly.y <= hill_y(fly.x):
				_land()
		Stage.LANDED:
			pass


func _land() -> void:
	stage = Stage.LANDED
	distance = snappedf(fly.x, 0.5)
	var before := time - _land_press if _land_press >= 0.0 else 99.0
	telemark = before > 0.05 and before < 0.6
	fell = absf(angle) > 0.75 or distance > K + 25.0
	# five judges: 20 points each for a clean telemark, less for a poor flight or landing
	var base := 18.5 if telemark else 16.0
	if fell:
		base = 9.0
	base -= clampf(absf(angle) * 3.0, 0.0, 3.0)
	judges.clear()
	for i in 5:
		judges.append(snappedf(clampf(base + rng.randf_range(-0.8, 0.8), 0.0, 20.0), 0.5))
	var sorted := judges.duplicate()
	sorted.sort()
	style = sorted[1] + sorted[2] + sorted[3]
	var points := 60.0 + 2.0 * (distance - K) + style
	event.emit("landed", {"distance": distance, "telemark": telemark, "fell": fell, "judges": judges})
	finish(snappedf(points, 0.1), "%.1f m  -  %.1f points" % [distance, points])


func autoplay() -> void:
	if phase != Phase.RUN:
		return
	match stage:
		Stage.INRUN:
			hold_down = true
			var lead := lerpf(0.3, 0.05, skill) + rng.randf_range(-0.05, 0.05)
			if along >= INRUN - speed * lead and _lip_time < 0.0:
				press("action")
		Stage.FLIGHT:
			hold_up = angle > 0.08
			hold_down = angle < -0.08
			var t_to_ground := (fly.y - hill_y(fly.x)) / maxf(0.1, -vel.y)
			if t_to_ground < lerpf(0.5, 0.25, skill) and _land_press < 0.0:
				press("action")
