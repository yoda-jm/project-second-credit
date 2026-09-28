class_name Biathlon
extends WinterEvent
## Biathlon, our short sprint: two laps of the course (BiathlonCourse) with five prone shots at the range between
## them. Ski with alternating LEFT and RIGHT pushes, in rhythm: a stride meter fills, and a push as it reaches the
## green goes furthest (the rhythm quickens on the climbs); hold DOWN on the descents to tuck. Every push lifts the
## heart rate, a rushed one most; gliding, tucking and lying at the range bring it down. At the range the rifle sways
## with the pulse: steer the sight with the arrows and press ACTION to fire at each of the five targets in turn.
## Each miss is a lap of the penalty loop. The lowest time wins.

enum Stage { SKI, RANGE, PENALTY }

const LAPS := 2
const SHOTS := 5
const TARGET_R := 0.0225  ## a prone target's hit zone (radius, metres at 50 m)
const SPACING := 0.12  ## between the targets' centres on the plate
const SETTLE := 2.2  ## seconds to come into the mat, lie down and load
const RISE := 1.8  ## to get up and shoulder the rifle
const RELOAD := 0.45  ## the bolt, between shots
const GREEN := Vector2(0.8, 1.0)
const PERFECT := 0.95  ## m/s a push in the green adds (at a jog; less when already fast)
const GOOD := 0.45
const WEAK := 0.1
const MU := 0.035  ## the snow's friction
const DRAG := 0.008  ## upright, per (m/s)^2
const TUCK_DRAG := 0.004
const HR_REST := 72.0
const HR_MAX := 195.0

var stage := Stage.SKI
var dist := 0.0  ## metres raced along the course (the penalty loop apart)
var speed := 0.0
var meter := 0.0  ## the stride: 0..1+, 1 is its end
var next_foot := "left"
var tuck := 0.0
var hr := 96.0  ## heart rate, beats a minute
var last_push := ""
var hold_left := false
var hold_right := false
# the range
var range_t := 0.0  ## seconds since reaching the mat
var shot := 0  ## shots fired
var hits: Array[bool] = []
var base := Vector2.ZERO  ## where the rifle points (metres on the target plate, from the plate's centre), sway apart
var aim := Vector2.ZERO  ## where it points, sway and all
var _base_to := Vector2.ZERO  ## the next target, the rifle swings over
var _reload := 0.0
var _sway_t := 0.0
var _beat := 0.0  ## the heart's phase (one per beat)
var _kick := Vector2.ZERO  ## the last beat's twitch and the recoil, dying away
var _phase := Vector2.ZERO
var _shot_at := -9.0
var misses := 0
var shooting_done := false
# the penalty loop
var pen_done := 0.0
var pen_total := 0.0
var _drift := Vector2.ZERO
var _wait := 0.0  ## (auto) how long the sight has been steady on the target
var _err := Vector2.ZERO  ## (auto) where the CPU thinks the target is, off by its skill


## Where the target `i` sits on the plate (metres from its centre).
static func target(i: int) -> Vector2:
	return Vector2((i - 2) * SPACING, 0.0)


static func lap_len() -> float:
	return BiathlonCourse.lap()


## A CPU biathlete's time for a form of 0..1, on the same scale as a player (every push perfect and five hits is about
## 119 s, seven in ten about 121 s, half about 150 s; measured with the model below), before their penalty loops;
## and how many they miss.
static func cpu_time(form: float) -> float:
	return lerpf(150.0, 117.0, form)


static func cpu_misses(form: float, rng: RandomNumberGenerator) -> int:
	var m := 0
	for i in SHOTS:
		if rng.randf() > lerpf(0.55, 0.93, form):
			m += 1
	return m


## Seconds a lap of the penalty loop costs, near enough (at a CPU's pace).
static func pen_seconds() -> float:
	return BiathlonCourse.pen_loop() / 6.6


func lap_s() -> float:
	return fposmod(dist, lap_len())


func lap() -> int:
	return mini(int(dist / lap_len()), LAPS - 1)


## The slope under the skier (rise per metre).
func slope() -> float:
	if stage == Stage.PENALTY:
		return 0.0
	return BiathlonCourse.slope(lap_s())


func stride_time() -> float:
	return clampf(0.8 - slope() * 2.2, 0.54, 0.98)


## How far the sway carries the sight at this heart rate (metres at the target).
func sway() -> float:
	return 0.006 + 0.03 * pow(clampf((hr - 70.0) / 110.0, 0.0, 1.0), 1.3)


func early(_l: bool, _r: bool, _a: bool) -> void:
	pass  # an interval start: pushing before the beep does nothing


func run(l: bool, r: bool, a: bool) -> void:
	match stage:
		Stage.SKI, Stage.PENALTY:
			_ski(l, r)
		Stage.RANGE:
			_range(a)
	_heart()


func _ski(l: bool, r: bool) -> void:
	var sl := slope()
	meter += TICK / stride_time()
	tuck = move_toward(tuck, 1.0 if hold_down and speed > 3.0 else 0.0, TICK * 3.0)
	var foot := "left" if l else ("right" if r else "")
	if foot != "":
		tuck = 0.0
		if foot != next_foot:
			speed = maxf(0.0, speed - 0.3)
			last_push = "wrong"
			hr += 3.0
			event.emit("stumble", {})
		else:
			var gain := WEAK
			last_push = "weak"
			if meter >= GREEN.x and meter <= GREEN.y + 0.08:
				gain = PERFECT
				last_push = "perfect"
			elif meter >= 0.6:
				gain = GOOD
				last_push = "good"
			if speed < 2.0:
				gain = maxf(gain, 0.7)  # the first pushes off the line always bite (and a stalled skier can always climb)
			speed += gain * clampf(1.5 - speed / 12.0, 0.3, 1.25)
			hr += {"perfect": 2.5, "good": 3.3, "weak": 5.0}[last_push] + maxf(0.0, sl) * 12.0
			meter = 0.0
			next_foot = "right" if foot == "left" else "left"
			event.emit("stride", {"foot": foot, "quality": last_push})
	var drag := lerpf(DRAG, TUCK_DRAG, tuck)
	speed += (-9.81 * sl - MU * 9.81 - drag * speed * speed) * TICK
	speed = maxf(0.0, speed)
	if stage == Stage.PENALTY:
		pen_done += speed * TICK
		if pen_done >= pen_total:
			stage = Stage.SKI
			event.emit("penalty_done", {})
		return
	# into the range after the first lap: the skier coasts to a stop on the mat
	var at := lap_len() + BiathlonCourse.RANGE_S
	if not shooting_done and dist > at - 18.0:
		speed = minf(speed, sqrt(2.0 * 2.2 * maxf(0.0, at - dist)) + 0.4)
	dist += speed * TICK
	if not shooting_done and dist >= at:
		dist = at
		speed = 0.0
		meter = 0.0
		tuck = 0.0
		stage = Stage.RANGE
		range_t = 0.0
		base = Vector2(-0.07, 0.1)
		_base_to = target(0)
		_phase = Vector2(rng.randf() * TAU, rng.randf() * TAU)
		event.emit("range", {})
		return
	if shooting_done and misses > 0 and pen_total == 0.0 and dist >= lap_len() + BiathlonCourse.PEN_S:
		dist = lap_len() + BiathlonCourse.PEN_S
		pen_total = misses * BiathlonCourse.pen_loop()
		pen_done = 0.0
		stage = Stage.PENALTY
		event.emit("penalty", {"loops": misses})
	if dist >= LAPS * lap_len():
		var m := int(time / 60.0)
		finish(snappedf(time, 0.1), "%d:%04.1f  -  %d / %d" % [m, time - m * 60.0, SHOTS - misses, SHOTS])


func _range(fire: bool) -> void:
	range_t += TICK
	if shooting_done:
		if range_t >= _shot_at + RISE:
			stage = Stage.SKI
			meter = 0.0
			event.emit("leave_range", {})
		return
	# the rifle swings towards the next target, the shooter steers it, the pulse and the breath move it
	var steer := Vector2((1.0 if hold_right else 0.0) - (1.0 if hold_left else 0.0), (1.0 if hold_up else 0.0) - (1.0 if hold_down else 0.0))
	_base_to += steer * 0.075 * TICK
	# the aim wanders off slowly (the breath, a tired arm): it has to be held on
	_drift = _drift.lerp(Vector2(rng.randf() - 0.5, rng.randf() - 0.5) * 0.035, TICK * 0.8)
	_base_to += _drift * TICK
	base = base.move_toward(_base_to, TICK * (0.09 if range_t > 0.6 else 0.05))
	_sway_t += TICK
	var a := sway()
	var s := Vector2(sin(_sway_t * 1.31 + _phase.x) * 0.85 + sin(_sway_t * 0.53 + _phase.y) * 0.3,
		sin(_sway_t * 2.07 + _phase.y) * 0.55 + cos(_sway_t * 0.71 + _phase.x) * 0.35) * a
	_kick = _kick.lerp(Vector2.ZERO, 1.0 - exp(-TICK * 9.0))
	aim = base + s + _kick
	_reload = maxf(0.0, _reload - TICK)
	if fire and range_t > SETTLE and _reload <= 0.0:
		var hit := aim.distance_to(target(shot)) <= TARGET_R
		hits.append(hit)
		if not hit:
			misses += 1
		event.emit("shot", {"index": shot, "hit": hit, "aim": aim})
		shot += 1
		_reload = RELOAD
		_kick += Vector2(rng.randf_range(-0.01, 0.01), 0.035)  # the recoil
		_shot_at = range_t
		if shot >= SHOTS:
			shooting_done = true
			event.emit("range_done", {"misses": misses})
		else:
			_base_to = base - s * 0.3 + (target(shot) - target(shot - 1))  # on to the next, roughly


func _heart() -> void:
	var rest := HR_REST if stage == Stage.RANGE else 88.0
	var k := 0.16 if stage == Stage.RANGE else 0.05
	hr += (rest - hr) * k * TICK
	hr = clampf(hr, HR_REST - 5.0, HR_MAX)
	var before := _beat
	_beat += hr / 60.0 * TICK
	if int(_beat) != int(before) and stage == Stage.RANGE:
		_kick += Vector2(0.0, sway() * 0.22)  # each beat twitches the sight
		event.emit("beat", {})


func autoplay() -> void:
	if phase != Phase.RUN:
		return
	match stage:
		Stage.SKI, Stage.PENALTY:
			var sl := slope()
			var coast := sl < -0.035 and speed > 6.5
			hold_down = coast
			if coast:
				return
			# ease off when the heart races, most of all on the way into the range
			var into := stage == Stage.SKI and not shooting_done and dist > lap_len() - 140.0
			var limit := lerpf(178.0, 186.0, skill) - (lerpf(40.0, 22.0, skill) if into else 0.0)
			var aim_at := 0.84 + rng.randf_range(-0.35, 0.35) * (1.0 - skill)
			if hr > limit:
				aim_at += 0.35
			if meter >= aim_at:
				press(next_foot)
		Stage.RANGE:
			if shooting_done:
				return
			# steer onto the target, then wait for the sway to cross it
			var t := target(shot) + _err
			var off := t - base
			hold_right = off.x > 0.004
			hold_left = off.x < -0.004
			hold_up = off.y > 0.004
			hold_down = off.y < -0.004
			if range_t <= SETTLE or _reload > 0.0:
				_wait = 0.0
				_err = Vector2(rng.randf_range(-1.0, 1.0), rng.randf_range(-1.0, 1.0)) * TARGET_R * 1.1 * (1.0 - skill)
				return
			_wait += TICK
			var need := TARGET_R * lerpf(1.1, 0.45, skill)
			if aim.distance_to(t) < need or _wait > lerpf(2.0, 4.5, skill):
				press("action")
				_wait = 0.0
