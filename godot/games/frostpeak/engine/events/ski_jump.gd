class_name SkiJump
extends WinterEvent
## Large-hill ski jump (K 120, HS 134; the hill is SkiHill). On the in-run hold DOWN to tuck (less drag, faster).
## At the lip press ACTION: the closer to the edge, the stronger the jump. In the air the body angle drifts: hold it
## in the ideal band with UP and DOWN; the better the angle, the more lift and the less drag. Press ACTION just
## before touchdown for a telemark landing (worth style points); a wild body angle at touchdown, or landing far
## beyond the hill size, is a fall. Distance points (60 at K, 1.8 per metre, as on large hills) plus style points
## (five judges, the best and the worst dropped).

const K := SkiHill.K
const HS := SkiHill.HS
const INRUN := SkiHill.INRUN  ## metres of in-run, from the gate to the lip
const LIP_WINDOW := 0.35  ## seconds either side of the lip where a take-off counts
const IDEAL := 0.0  ## body angle offset from the ideal, radians
const METRE_POINTS := 1.8
const LIFT := 0.005  ## lift and drag per metre (times speed squared), for an ideal body angle
const DRAG := 0.0035

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
	return SkiHill.ground_y(x)


## The distance flown so far: along the hill, under the jumper (the TV read-out).
func current_distance() -> float:
	if stage == Stage.LANDED:
		return distance
	if stage == Stage.FLIGHT:
		return SkiHill.distance_at(fly.x)
	return 0.0


func run(_l: bool, _r: bool, a: bool) -> void:
	match stage:
		Stage.INRUN:
			tuck = move_toward(tuck, 1.0 if hold_down else 0.0, TICK * 3.0)
			var slope := SkiHill.inrun_angle(along)
			var acc := 9.81 * (sin(slope) - 0.03 * cos(slope)) - (0.003 - 0.0016 * tuck) * speed * speed
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
				fly = Vector2(cos(SkiHill.ALPHA), -sin(SkiHill.ALPHA)) * (along - INRUN)  # just past the lip
				# along the table (11 degrees down), plus the jump's push square to it
				var push := 1.0 + 1.8 * takeoff
				var ta := SkiHill.ALPHA
				vel = Vector2(speed * cos(ta) + push * sin(ta), -speed * sin(ta) + push * cos(ta))
				angle = rng.randf_range(-0.1, 0.1) + (1.0 - takeoff) * 0.25
				event.emit("takeoff", {"quality": takeoff, "speed_kmh": speed * 3.6})
		Stage.FLIGHT:
			# the angle wanders; the player leans it back
			angle += rng.randf_range(-0.9, 0.9) * TICK + angle * 0.6 * TICK
			if hold_up:
				angle -= 1.1 * TICK
			if hold_down:
				angle += 1.1 * TICK
			# lift square to the flight path, drag along it; a poor body angle loses lift and adds drag
			var err := (angle - IDEAL) / 0.6
			var lift := LIFT * maxf(0.0, 1.0 - err * err) * (0.85 + 0.15 * takeoff)
			var drag := DRAG + 0.006 * (angle - IDEAL) * (angle - IDEAL)
			var v := vel.length()
			var along_v := vel / maxf(v, 0.01)
			var up := Vector2(-along_v.y, along_v.x)
			vel += (up * lift - along_v * drag) * v * v * TICK + Vector2(0.0, -9.81) * TICK
			fly += vel * TICK
			if a and _land_press < 0.0:
				_land_press = time
			if fly.y <= hill_y(fly.x):
				_land()
		Stage.LANDED:
			pass


func _land() -> void:
	stage = Stage.LANDED
	distance = snappedf(SkiHill.distance_at(fly.x), 0.5)
	var before := time - _land_press if _land_press >= 0.0 else 99.0
	telemark = before > 0.05 and before < 0.6
	fell = absf(angle) > 0.75 or distance > HS + 8.0
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
	var points := maxf(0.0, 60.0 + METRE_POINTS * (distance - K)) + style
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
			# how fast the jumper closes on the slope, which falls away beneath them
			var ground_dy := (hill_y(fly.x + 0.5) - hill_y(fly.x)) / 0.5 * vel.x
			var t_to_ground := (fly.y - hill_y(fly.x)) / maxf(0.1, ground_dy - vel.y)
			if t_to_ground < lerpf(0.5, 0.25, skill) and _land_press < 0.0:
				press("action")
