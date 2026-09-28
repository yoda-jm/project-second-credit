class_name Bobsled
extends WinterEvent
## The four-man bobsled, one run down BobTrack. The push start: the crew runs the sled off the block with
## alternating LEFT and RIGHT pushes in rhythm (a stride meter, as on the ice: the green zone pushes hardest), and
## ACTION jumps them in, one after the other (in by the end of the start ramp, or they scramble in late). Then the
## pilot steers with LEFT and RIGHT down the ice channel. In every curve the sled is carried up the outside bank, as
## high as its speed asks (the wall's angle where the push outwards and gravity balance), and swings on the bank
## like a pendulum: steer into the curve as it climbs and against the swing to settle it. Letting it swing costs
## time (the runners scrub), coming out of a curve with the swing still on slams the sled into the low walls
## (more time), and a sled that overshoots the top of the bank flips: a crash, and no time. The clock runs from the
## first timing eye to the finish, with splits at the eyes on the way.

enum Stage { PUSH, LOAD, RIDE, CRASH }

const GREEN := Vector2(0.8, 1.0)
const PUSH_PERFECT := 1.2  ## m/s a push in the green adds (less as the sled speeds up, to nothing at V_PUSH)
const PUSH_GOOD := 0.75
const PUSH_WEAK := 0.2
const V_PUSH := 13.5
const LOAD_T := 1.0  ## seconds for the four to jump in, one after another
const LOAD_EARLIEST := 10.0  ## metres off the block before they can jump in
const MU := 0.0035  ## the runners on the ice
const DRAG := 0.00022  ## per (m/s)^2 (four crouched in, 630 kg)
const STEER_A := 10.0  ## m/s^2 across the channel at full steer
const STEER_LOSS := 0.04  ## m/s^2 lost while steering hard (the runners skid)
const LAT_DAMP := 0.4  ## the swing dies away by itself (1/s)
const GRIP := 0.9  ## and the runners' edges resist sliding across, the more the harder the sled is pressed (1/s per g)
const SCRUB := 0.08  ## m/s^2 lost per m/s of swing
const HIT_LOSS := 0.35  ## m/s lost per m/s the sled hits a wall with
const FLIP := deg_to_rad(82.0)  ## a sled this high on a bank tips over its top
const DANGER := deg_to_rad(72.0)  ## (the read-outs warn from here)
const CRASH_RESULT := 999.0
const CRASH_SLIDE := 4.0  ## seconds the upturned sled slides before the run is over

var stage := Stage.PUSH
var s := 0.0  ## metres down the run (the centre line)
var speed := 0.0  ## m/s along the sled's own path
var w := 0.0  ## across the channel (+ right): metres across the floor, then the wall's angle (see BobTrack.section)
var wv := 0.0  ## how fast the sled moves across, along the surface (m/s)
var steer := 0.0  ## -1 left .. 1 right, as held
var hold_left := false
var hold_right := false
var meter := 0.0  ## the push rhythm, 0..1+
var next_foot := "left"
var last_push := ""
var load_t := -1.0  ## seconds since the crew began to jump in (-1 before)
var late := false  ## the crew scrambled in past the ramp
var clock := 0.0  ## the race clock (from the first timing eye)
var timing := false
var splits: Array[float] = []
var hits := 0
var g_force := 1.0  ## what the crew feels (g)
var max_g := 1.0
var alpha := 0.0  ## the wall's angle under the sled (radians)
var crash_t := 0.0
var crashed := false
var _hist := PackedFloat32Array()  ## (auto) where the sled was, the last half second (the pilot reacts late)
var _load_at := 0.0  ## (auto) where the crew will jump in
var _aim_noise := 0.0


func _init(seed: int = 1) -> void:
	super(seed)


## A CPU crew's time for a form of 0..1, on the same scale as a player (every push perfect and a clean drive is
## about 38.6 s, a crew at seven in ten about 38.9 s, half and half about 39.3 s; measured with the model below).
static func cpu_time(form: float) -> float:
	return lerpf(40.8, 38.45, form)


func stride_time() -> float:
	return clampf(0.46 - speed * 0.013, 0.3, 0.46)


## How many of the four are aboard (the pilot first, the brakeman last).
func aboard() -> int:
	if stage == Stage.PUSH:
		return 0
	if stage == Stage.LOAD:
		return clampi(int(load_t / (LOAD_T / 4.0)) + 1, 1, 4)
	return 4


## The lateral position the sled settles at here at this speed (where the push outwards and gravity balance on the
## outside bank; the middle on a straight).
static func balance(at: float, v: float) -> float:
	var k := BobTrack.kappa(at)
	if absf(k) < 0.002:
		return 0.0
	return -signf(k) * (BobTrack.FLOOR + minf(atan(absf(k) * v * v / 9.81), PI * 0.5))


func early(_l: bool, _r: bool, _a: bool) -> void:
	pass  # the crew waits for the light: pushing early does nothing


func run(l: bool, r: bool, a: bool) -> void:
	match stage:
		Stage.PUSH:
			_push(l, r)
			if a and s >= LOAD_EARLIEST:
				_start_load()
			elif s >= BobTrack.PUSH_END:
				late = true
				speed = maxf(0.0, speed - 0.6)
				event.emit("late", {})
				_start_load()
		Stage.LOAD:
			load_t += TICK
			var out := 1.0 - float(aboard() - 1) / 4.0  # those still running push on
			speed += 1.1 * out * (1.0 - speed / V_PUSH) * TICK
			if load_t >= LOAD_T:
				stage = Stage.RIDE
				event.emit("loaded", {"late": late})
		Stage.RIDE:
			pass
		Stage.CRASH:
			crash_t += TICK
	_move()
	if not timing and s >= BobTrack.START_LINE:
		timing = true
		event.emit("clock", {})
	if timing:
		clock += TICK
	if splits.size() < BobTrack.SPLITS.size() and s >= BobTrack.SPLITS[splits.size()]:
		splits.append(snappedf(clock, 0.01))
		event.emit("split", {"index": splits.size() - 1, "time": splits[splits.size() - 1]})
	if stage == Stage.CRASH and (crash_t >= CRASH_SLIDE or speed < 0.5):
		finish(CRASH_RESULT, "CRASHED")
	elif s >= BobTrack.FINISH:
		finish(snappedf(clock, 0.01), "%.2f s" % clock)


func _push(l: bool, r: bool) -> void:
	meter += TICK / stride_time()
	var foot := "left" if l else ("right" if r else "")
	if foot == "":
		return
	if foot != next_foot:
		speed = maxf(0.0, speed - 0.4)
		last_push = "wrong"
		event.emit("stumble", {})
		return
	var gain := PUSH_WEAK
	last_push = "weak"
	if meter >= GREEN.x and meter <= GREEN.y + 0.08:
		gain = PUSH_PERFECT
		last_push = "perfect"
	elif meter >= 0.6:
		gain = PUSH_GOOD
		last_push = "good"
	if speed < 2.0:
		gain = maxf(gain, PUSH_GOOD)  # the first pushes off the block always bite
	speed += gain * clampf(1.0 - speed / V_PUSH, 0.0, 1.0)
	meter = 0.0
	next_foot = "right" if foot == "left" else "left"
	event.emit("stride", {"foot": foot, "quality": last_push})


func _start_load() -> void:
	stage = Stage.LOAD
	load_t = 0.0
	event.emit("load", {"at": s})


## The sled down the channel: along the run (gravity, the runners, the air, the swing's scrub), and across it (the
## push outwards in a curve, gravity down the wall, the pilot's steering, the swing's own damping). `wv` is the
## speed across, along the surface (m/s); on a wall it turns the wall's angle by wv / its radius.
func _move() -> void:
	var g := 9.81
	var k := BobTrack.kappa(s)
	var side := signf(w) if w != 0.0 else 1.0
	var on_wall := absf(w) > BobTrack.FLOOR
	alpha = absf(w) - BobTrack.FLOOR if on_wall else 0.0
	var riding := stage == Stage.RIDE
	steer = move_toward(steer, ((1.0 if hold_right else 0.0) - (1.0 if hold_left else 0.0)) if riding else 0.0, TICK * 6.0)
	var out_push := -k * speed * speed  # across the channel, + right (the curve throws the sled to its outside)
	if stage == Stage.CRASH:
		wv = move_toward(wv, 0.0, TICK * 4.0)
		w += wv * TICK / (BobTrack.wall_r(s, side) if on_wall else 1.0)
	else:
		var nx := lateral(s, speed, w, wv, steer)
		w = nx.x
		wv = nx.y
	# the walls: the top of a low wall stops the sled (a hit); too high on a bank, it tips over the top and flips
	var top := BobTrack.FLOOR + PI * 0.5
	var bank := BobTrack.wall(s, side) > BobTrack.WALL + 1.5
	if bank and absf(w) >= BobTrack.FLOOR + FLIP and wv * side > 0.0 and stage != Stage.CRASH:
		stage = Stage.CRASH
		crashed = true
		crash_t = 0.0
		event.emit("crash", {"at": s})
	if absf(w) >= top and stage != Stage.CRASH:
		if wv * side > 0.0:
			var hit := absf(wv)
			speed = maxf(0.0, speed - HIT_LOSS * hit)
			wv = -wv * 0.3
			hits += 1
			event.emit("wall", {"strength": hit, "side": side})
		w = side * top
	elif stage == Stage.CRASH:
		w = side * minf(absf(w), top)
	alpha = maxf(0.0, absf(w) - BobTrack.FLOOR)
	# what the sled presses into the ice with (the crew feels it), and the losses
	var toward := out_push * side  # how hard the curve pushes the sled into the wall it is on
	var press := g if absf(w) <= BobTrack.FLOOR else maxf(0.0, g * cos(alpha) + toward * sin(alpha))
	g_force = sqrt(g * g + out_push * out_push) / g if stage != Stage.CRASH else 1.0
	max_g = maxf(max_g, g_force)
	var mu := MU if stage != Stage.CRASH else 0.3
	var a := -g * BobTrack.grade(s) - mu * press - DRAG * speed * speed
	if stage == Stage.PUSH or stage == Stage.LOAD:
		a = -g * BobTrack.grade(s) - MU * g - DRAG * speed * speed
	if riding:
		a -= STEER_LOSS * absf(steer) + SCRUB * absf(wv) * press / g
	speed = maxf(0.0, speed + a * TICK)
	# along the centre line: up the outside bank the path is longer (and shorter low on the inside)
	var x := BobTrack.section(s, w).x
	s += speed * TICK / maxf(0.5, 1.0 - k * x)


## One tick of the sled's motion across the channel at s (no walls): the new lateral position and speed.
static func lateral(at: float, v: float, lw: float, lv: float, st: float) -> Vector2:
	var g := 9.81
	var side := signf(lw) if lw != 0.0 else 1.0
	var on_wall := absf(lw) > BobTrack.FLOOR
	var al := absf(lw) - BobTrack.FLOOR if on_wall else 0.0
	var out_push := -BobTrack.kappa(at) * v * v
	var pressed := g if not on_wall else maxf(0.0, g * cos(al) + out_push * side * sin(al))
	var acc := out_push * cos(al) - g * sin(al) * side + st * STEER_A - (LAT_DAMP + GRIP * pressed / g) * lv
	lv += acc * TICK
	lw += lv * TICK / (BobTrack.wall_r(at, side) if on_wall else 1.0)
	return Vector2(lw, lv)


## (auto) Where the sled will be over the next `n` ticks if the pilot holds `st`: the highest it climbs a bank
## (w, signed), and the low wall it would hit (+1, -1, or 0).
func _predict(from_w: float, from_v: float, st: float, n: int) -> Vector2:
	var at := s
	var lw := from_w
	var lv := from_v
	var peak := 0.0
	for i in n:
		var nx := lateral(at, speed, lw, lv, st)
		lw = nx.x
		lv = nx.y
		at += speed * TICK
		var side := signf(lw)
		if BobTrack.wall(at, side) > BobTrack.WALL + 1.5:
			if absf(lw) > absf(peak):
				peak = lw
		elif absf(lw) >= BobTrack.FLOOR + PI * 0.5 - 0.05:
			return Vector2(peak, side)
	return Vector2(peak, 0.0)


func autoplay() -> void:
	if phase != Phase.RUN:
		return
	match stage:
		Stage.PUSH:
			if _load_at == 0.0:
				_load_at = lerpf(30.0, 47.0, skill) + rng.randf_range(-4.0, 4.0) * (1.0 - skill)
			if s >= _load_at:
				press("action")
				return
			var aim_at := 0.84 + rng.randf_range(-0.35, 0.35) * (1.0 - skill)
			if meter >= aim_at:
				press(next_foot)
		Stage.RIDE:
			# the pilot reads the sled late (less so, the better they are), and steers for where it will settle
			# a little ahead, against its swing
			_hist.append(w)
			_hist.append(wv)
			var lag := int(lerpf(24.0, 4.0, skill)) * 2
			while _hist.size() > lag + 2:
				_hist = _hist.slice(2)
			var seen_w := _hist[0]
			var seen_v := _hist[1]
			if rng.randf() < TICK * 2.0:
				_aim_noise = rng.randf_range(-1.0, 1.0) * (1.0 - skill) * 0.12
			# the pilot feels where the sled is going: if it will climb above a safe line on the bank, steer down it
			# (into the curve); if it will slam a low wall, steer away; otherwise let it run
			var safe := BobTrack.FLOOR + lerpf(deg_to_rad(70.0), deg_to_rad(74.0), skill) + _aim_noise
			var n := int(lerpf(24.0, 50.0, skill))
			var p := _predict(seen_w, seen_v, 0.0, n)
			var u := 0.0
			if absf(p.x) > safe:
				u = -signf(p.x)
			elif p.y != 0.0:
				u = -p.y
			hold_right = u > 0.5
			hold_left = u < -0.5
		_:
			hold_left = false
			hold_right = false
