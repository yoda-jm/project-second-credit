class_name LinksPhysics
extends RefCounted
## The ball's physics on a hole, deterministic and side-effect free: the live game, the aiming guide, the CPU's
## look-ahead and the tests all run the same step. Gadgets are pure functions of the hole clock, so a shot can be
## simulated from any moment. A step appends [kind, data] events to `ev` when it is not null.
##
## Arcade first: the numbers are tuned for feel, not realism. The ball rolls on the hole's surface (slopes pull it,
## friction per surface stops it briskly), flies off lips and steps, bounces lively off banks, drops in a generous
## cup that forgives near-misses (only a really fast ball lips out), and is lost in water or down a chasm.

const B = preload("res://games/lanternlinks/engine/links_ball.gd")
const H = preload("res://games/lanternlinks/engine/links_hole.gd")

const TICK := 1.0 / 60.0
const R := 0.05              ## ball radius (m), a little over life size so it reads on screen
const G := 9.81
const ROLL_G := G * 5.0 / 7.0
const MAX_SPEED := 4.6       ## a full-power stroke (m/s)
const MAX_STEP := 0.035      ## the ball never moves more than this in one substep
const STOP_V := 0.06
const STEP_TOL := 0.025      ## a cell higher than the ball's bottom by more than this is a wall to it
const WALL_E := 0.8
const GROUND_E := 0.32
const CAPTURE_V := 1.9
const AIR_CAPTURE_V := 2.6
const FRICTION := {H.FELT: 0.7, H.SAND: 3.6, H.ICE: 0.12, H.WATER: 0.55, H.BOOST: 0.55, H.CHASM: 0.55}
const BOOST_A := 5.0
const BOOST_MAX := 4.0
const LOOP_R := 0.32
const LOOP_V := 2.4          ## the speed needed to go round the loop
const LOOP_SHIFT := 0.36     ## the loop's exit is this far past its entry
const LOOP_SIDE := 0.13      ## and this far to the side (the track passes itself)
const BLADES := 4
const BLADE_HALF := 0.28     ## a blade blocks the tunnel while within this angle (rad) of straight down
const PIPE_SPEED := 3.5      ## how fast the ball travels inside a pipe (m/s)


## Advances the ball by one tick (1/60 s) at hole time `clock`.
static func tick(hole: LinksHole, b: LinksBall, clock: float, ev) -> void:
	match b.mode:
		B.Mode.SUNK, B.Mode.LOST:
			b.t += TICK
			return
		B.Mode.LOOP:
			_loop(hole, b, ev)
			return
		B.Mode.PIPE:
			_pipe(hole, b, ev)
			return
	var speed := maxf(b.vel.length(), absf(b.vz) * 0.5)
	var n := clampi(ceili(speed * TICK / MAX_STEP), 1, 16)
	var dt := TICK / n
	for k in n:
		_substep(hole, b, clock + k * dt, dt, ev)
		if b.mode != B.Mode.ROLL and b.mode != B.Mode.AIR:
			return
	# at rest: slow, on the ground, and friction can hold it on the slope
	if b.mode == B.Mode.ROLL and b.vel.length() < STOP_V:
		var s := hole.surface(b.pos)
		var pull := ROLL_G * Vector2(s.y, s.z).length()
		var k2 := hole.kind_at(b.pos)
		if pull < FRICTION.get(k2, 0.55) * 0.95 and not hole.boost.has(hole.index(b.pos)) and not _pushed(hole, b, clock):
			b.vel = Vector2.ZERO
			if not b.at_rest:
				b.at_rest = true
				if ev != null:
					ev.append(["rest", {"pos": b.pos}])
			return
	b.at_rest = false


## Whether a moving gadget is touching the ball (a ball resting against a mover or a blade must not count as stopped).
static func _pushed(hole: LinksHole, b: LinksBall, clock: float) -> bool:
	for g in hole.gadgets:
		match g["type"]:
			"mover":
				var c := _mover_pos(g, clock)
				var q := b.pos.clamp(c - g["half"], c + g["half"])
				if q.distance_to(b.pos) < R + 0.01:
					return true
			"spinner":
				if _spinner_closest(g, clock, b.pos).distance_to(b.pos) < R + 0.04:
					return true
	return false


static func _substep(hole: LinksHole, b: LinksBall, t: float, dt: float, ev) -> void:
	var grounded := b.mode == B.Mode.ROLL
	var s := hole.surface(b.pos)
	var k := hole.kind_at(b.pos)
	if grounded:
		var grad := Vector2(s.y, s.z)
		b.vel += -ROLL_G * grad / (1.0 + grad.length_squared()) * dt
		var i := hole.index(b.pos)
		if hole.boost.has(i):
			var d: Vector2 = hole.boost[i]
			if b.vel.dot(d) < BOOST_MAX:
				b.vel += d * BOOST_A * dt
				if ev != null and not b.data.has("boost"):
					ev.append(["boost", {"pos": b.pos}])
			b.data["boost"] = true
		else:
			b.data.erase("boost")
		var sp := b.vel.length()
		if sp > 0.0:
			var f: float = FRICTION.get(k, 0.55)
			b.vel *= maxf(0.0, sp - f * dt) / sp
		var vz := grad.dot(b.vel)
		var np := b.pos + b.vel * dt
		var hn := hole.height(np)
		var fall := b.z + vz * dt - 0.5 * G * dt * dt
		b.pos = np
		if hn < fall - 0.002 and hn < b.z:
			# the ground drops away faster than the ball falls: it flies
			b.mode = B.Mode.AIR
			b.vz = vz - G * dt
			b.z = fall
			if ev != null and hn < b.z - 0.08:
				ev.append(["takeoff", {"pos": b.pos, "speed": b.vel.length()}])
		else:
			b.z = minf(hn, b.z + 0.03) if hn > b.z else hn
	else:
		b.vz -= G * dt
		b.pos += b.vel * dt
		b.z += b.vz * dt
		var hn2 := hole.height(b.pos)
		if b.z <= hn2:
			_land(hole, b, hn2, ev)
	_collide(hole, b, t, ev)
	_hazards_and_cup(hole, b, ev)


static func _land(hole: LinksHole, b: LinksBall, ground: float, ev) -> void:
	var s := hole.surface(b.pos)
	var n := Vector3(-s.y, 1.0, -s.z).normalized()
	var v := Vector3(b.vel.x, b.vz, b.vel.y)
	var vn := v.dot(n)
	b.z = ground
	if vn < 0.0:
		if ev != null and vn < -0.6:
			ev.append(["land", {"pos": b.pos, "speed": -vn}])
		var bounce := -vn * GROUND_E
		v -= vn * n   # keep the tangential part
		v *= 0.96
		if bounce > 0.5:
			v += n * bounce
			b.vel = Vector2(v.x, v.z)
			b.vz = v.y
			b.z = ground + 0.001
			return
	b.vel = Vector2(v.x, v.z)
	b.vz = 0.0
	b.mode = B.Mode.ROLL


## Walls, banks, steps up, and the gadgets.
static func _collide(hole: LinksHole, b: LinksBall, t: float, ev) -> void:
	var x0 := floori((b.pos.x - R) / H.CELL)
	var x1 := floori((b.pos.x + R) / H.CELL)
	var y0 := floori((b.pos.y - R) / H.CELL)
	var y1 := floori((b.pos.y + R) / H.CELL)
	var own := hole.index(b.pos)
	for cy in range(y0, y1 + 1):
		for cx in range(x0, x1 + 1):
			var i := cy * hole.w + cx
			var outside := cx < 0 or cy < 0 or cx >= hole.w or cy >= hole.h
			if not outside and hole.diag[i] != 0:
				_diag_hit(hole, b, cx, cy, hole.diag[i], ev)
				continue
			if i == own and not outside:
				continue
			var lo := Vector2(cx, cy) * H.CELL
			var q := b.pos.clamp(lo, lo + Vector2.ONE * H.CELL)
			var d := b.pos - q
			var dl := d.length()
			if dl >= R or dl < 1e-6:
				continue
			var blocks := outside or hole.kind[i] <= H.WALL
			if not blocks:
				# a higher cell is a wall to a ball below its top (its floor sampled just inside the boundary)
				var inside := q - d / dl * 0.001
				var top := hole.cell_floor(i, inside).x + hole.extras(inside).x
				blocks = top > b.z + STEP_TOL
			if blocks:
				_bounce(b, d / dl, R - dl, Vector2.ZERO, WALL_E, ev, "bank")
	for g in hole.gadgets:
		match g["type"]:
			"bumper":
				var d2: Vector2 = b.pos - g["pos"]
				var rr: float = g["r"] + R
				if d2.length_squared() < rr * rr and d2.length_squared() > 1e-8:
					var nrm := d2.normalized()
					var vn := b.vel.dot(nrm)
					b.pos = g["pos"] + nrm * rr
					if vn < 0.0:
						b.vel -= vn * nrm
						b.vel += nrm * maxf(1.5, -vn * 1.15)
						b.hits += 1
						if ev != null:
							ev.append(["bumper", {"pos": g["pos"], "speed": -vn}])
			"windmill":
				if windmill_blocked(g, t):
					var a: Vector2 = g["a"]
					var bb: Vector2 = g["b"]
					var q2 := Geometry2D.get_closest_point_to_segment(b.pos, a, bb)
					var d3 := b.pos - q2
					if d3.length() < R:
						var nrm2: Vector2 = d3.normalized() if d3.length() > 1e-6 else g["face"]
						_bounce(b, nrm2, R - d3.length(), nrm2 * 0.6, WALL_E, ev, "blade")
			"mover":
				var c := _mover_pos(g, t)
				var half: Vector2 = g["half"]
				var q3 := b.pos.clamp(c - half, c + half)
				var d4 := b.pos - q3
				if d4.length() < R:
					var nrm3: Vector2
					var depth: float
					if d4.length() > 1e-6:
						nrm3 = d4.normalized()
						depth = R - d4.length()
					else:
						# the centre is inside: out along the nearest face
						var o := b.pos - c
						var px := half.x - absf(o.x)
						var py := half.y - absf(o.y)
						nrm3 = Vector2(signf(o.x), 0) if px < py else Vector2(0, signf(o.y))
						depth = minf(px, py) + R
					_bounce(b, nrm3, depth, _mover_vel(g, t), WALL_E, ev, "mover")
			"spinner":
				var q4 := _spinner_closest(g, t, b.pos)
				var d5 := b.pos - q4
				var rr2 := R + 0.035
				if d5.length() < rr2 and d5.length() > 1e-6:
					var r := q4 - (g["pos"] as Vector2)
					var sv := Vector2(-r.y, r.x) * float(g["speed"])
					_bounce(b, d5.normalized(), rr2 - d5.length(), sv, 0.6, ev, "spinner")
			"loop":
				if b.mode == B.Mode.ROLL:
					var dir: Vector2 = g["dir"]
					var rel := b.pos - (g["pos"] as Vector2)
					var along := rel.dot(dir)
					var side := rel.dot(Vector2(-dir.y, dir.x))
					if along >= 0.0 and along < 0.08 and absf(side) < H.CELL * 0.5 and b.vel.dot(dir) > 0.05:
						b.mode = B.Mode.LOOP
						b.t = 0.0
						var v_in := b.vel.dot(dir)
						b.data = {"g": g, "v_in": v_in, "theta": 0.0, "back": false,
							"ok": v_in >= LOOP_V, "base": hole.height(g["pos"])}
						if ev != null:
							ev.append(["loop_in", {"pos": b.pos, "speed": v_in, "ok": v_in >= LOOP_V}])
			"pipe":
				if b.mode == B.Mode.ROLL and b.pos.distance_to(g["a"]) < H.PIPE_R:
					b.mode = B.Mode.PIPE
					b.t = 0.0
					b.data = {"g": g, "speed": b.vel.length(), "len": (g["a"] as Vector2).distance_to(g["b"])}
					if ev != null:
						ev.append(["pipe_in", {"pos": g["a"]}])


static func _bounce(b: LinksBall, nrm: Vector2, depth: float, surf_v: Vector2, e: float, ev, what: String) -> void:
	b.pos += nrm * depth
	var rel := b.vel - surf_v
	var vn := rel.dot(nrm)
	if vn < 0.0:
		var vt := rel - vn * nrm
		rel = vt * 0.94 - vn * e * nrm
		b.vel = rel + surf_v
		b.hits += 1
		if ev != null and -vn > 0.12:
			ev.append([what, {"pos": b.pos - nrm * R, "speed": -vn, "normal": nrm}])
	elif surf_v.dot(nrm) > 0.0 and b.vel.dot(nrm) < surf_v.dot(nrm):
		b.vel += nrm * (surf_v.dot(nrm) - b.vel.dot(nrm))


static func _diag_hit(hole: LinksHole, b: LinksBall, cx: int, cy: int, d: int, ev) -> void:
	var o := Vector2(cx, cy) * H.CELL
	var c := H.CELL
	var tri: PackedVector2Array
	match d:
		1: tri = [o, o + Vector2(c, 0), o + Vector2(0, c)]
		2: tri = [o + Vector2(c, 0), o + Vector2(c, c), o + Vector2(0, c)]
		3: tri = [o, o + Vector2(c, 0), o + Vector2(c, c)]
		_: tri = [o, o + Vector2(c, c), o + Vector2(0, c)]
	# the hypotenuse (the bank's face) is the first edge from vertex 1 to 2 for 1 and 2, 2 to 0 for 3 and 4
	var best := Vector2.ZERO
	var best_d := INF
	for k in 3:
		var q := Geometry2D.get_closest_point_to_segment(b.pos, tri[k], tri[(k + 1) % 3])
		var dd := b.pos.distance_to(q)
		if dd < best_d:
			best_d = dd
			best = q
	var inside := Geometry2D.is_point_in_polygon(b.pos, tri)
	if not inside and best_d >= R:
		return
	var a: Vector2
	var bb: Vector2
	match d:
		1, 2:
			a = o + Vector2(c, 0)
			bb = o + Vector2(0, c)
		_:
			a = o
			bb = o + Vector2(c, c)
	var nrm := (bb - a).orthogonal().normalized()
	# the face's normal points to the open half
	var centroid := (tri[0] + tri[1] + tri[2]) / 3.0
	if (centroid - a).dot(nrm) > 0.0:
		nrm = -nrm
	var q2 := Geometry2D.get_closest_point_to_segment(b.pos, a, bb)
	var dist := (b.pos - q2).dot(nrm)
	if inside or dist < R:
		if not inside and best.distance_to(q2) > 1e-4:
			# nearest to a cell edge rather than the face: that edge belongs to a wall cell, handled there
			var d2 := b.pos - best
			if d2.length() > 1e-6 and d2.length() < R:
				_bounce(b, d2.normalized(), R - d2.length(), Vector2.ZERO, WALL_E, ev, "bank")
			return
		_bounce(b, nrm, R - dist, Vector2.ZERO, WALL_E, ev, "bank")


static func _hazards_and_cup(hole: LinksHole, b: LinksBall, ev) -> void:
	var k := hole.kind_at(b.pos)
	if k == H.WATER and b.z <= hole.height(b.pos) + 0.005:
		b.mode = B.Mode.LOST
		b.t = 0.0
		if ev != null:
			ev.append(["splash", {"pos": b.pos, "speed": b.vel.length()}])
		return
	if b.z < -0.8 or k == H.OUT:
		b.mode = B.Mode.LOST
		b.t = 0.0
		if ev != null:
			ev.append(["fall", {"pos": b.pos}])
		return
	var dc := b.pos.distance_to(hole.cup)
	if b.lip_cool:
		if dc > H.CUP_R + R:
			b.lip_cool = false
		return
	if dc < H.CUP_R - R * 0.2 and b.z < hole.cup_h + 0.06:
		var sp := b.vel.length()
		if sp < (CAPTURE_V if b.mode == B.Mode.ROLL else AIR_CAPTURE_V):
			b.mode = B.Mode.SUNK
			b.t = 0.0
			if ev != null:
				ev.append(["sink", {"pos": hole.cup, "speed": sp}])
		else:
			# too fast: it catches the far lip, hops and is thrown aside
			var off := (b.pos - hole.cup).cross(b.vel.normalized()) / H.CUP_R
			b.vel = b.vel.rotated(-off * 0.5) * 0.82
			b.vz = sp * 0.16
			b.mode = B.Mode.AIR
			b.z += 0.002
			b.lip_cool = true
			if ev != null:
				ev.append(["lip", {"pos": hole.cup, "speed": sp}])


## Inside the loop: round the circle (speed falling with height), out past the entry; too slow, up and back.
static func _loop(hole: LinksHole, b: LinksBall, ev) -> void:
	var d: Dictionary = b.data
	var g: Dictionary = d["g"]
	var v_in: float = d["v_in"]
	var k := (LOOP_V * LOOP_V - 1.0) * 0.5
	var th: float = d["theta"]
	var v2 := v_in * v_in - k * (1.0 - cos(th))
	var v := sqrt(maxf(v2, 0.0))
	b.t += TICK
	if d["ok"]:
		th += maxf(v, 0.6) / LOOP_R * TICK
		if th >= TAU:
			var dir: Vector2 = g["dir"]
			b.mode = B.Mode.ROLL
			b.pos = loop_point(g, TAU)
			b.z = hole.height(b.pos)
			b.vel = dir * v_in * 0.9
			b.data = {}
			if ev != null:
				ev.append(["loop_out", {"pos": b.pos, "speed": v_in}])
			return
	else:
		if not d["back"]:
			th += maxf(v, 0.25) / LOOP_R * TICK
			if v2 <= 0.0 or th > PI * 0.95:
				d["back"] = true
		else:
			th -= maxf(v, 0.25) / LOOP_R * TICK
			if th <= 0.0:
				var dir2: Vector2 = g["dir"]
				b.mode = B.Mode.ROLL
				b.pos = (g["pos"] as Vector2) - dir2 * 0.01
				b.z = hole.height(b.pos)
				b.vel = -dir2 * v_in * 0.75
				b.data = {}
				if ev != null:
					ev.append(["loop_back", {"pos": b.pos}])
				return
	d["theta"] = th
	b.pos = loop_point(g, th)
	b.z = float(d["base"]) + LOOP_R * (1.0 - cos(th))


## A point on the loop's track in plan view: forward around the circle, drifting forward and aside as it goes.
static func loop_point(g: Dictionary, th: float) -> Vector2:
	var dir: Vector2 = g["dir"]
	var side := Vector2(-dir.y, dir.x)
	var f := th / TAU
	return (g["pos"] as Vector2) + dir * (LOOP_R * sin(th) + LOOP_SHIFT * f) + side * LOOP_SIDE * (f - 0.5) * 2.0 * minf(1.0, th)


static func _pipe(hole: LinksHole, b: LinksBall, ev) -> void:
	var d: Dictionary = b.data
	var g: Dictionary = d["g"]
	b.t += TICK
	var dur: float = 0.35 + float(d["len"]) / PIPE_SPEED
	var f := minf(1.0, b.t / dur)
	b.pos = (g["a"] as Vector2).lerp(g["b"], f)
	b.z = -0.3
	if b.t >= dur:
		var dir: Vector2 = g["dir"]
		b.pos = (g["b"] as Vector2) + dir * (H.PIPE_R + R + 0.01)
		b.z = hole.height(b.pos)
		b.vel = dir * clampf(float(d["speed"]) * 0.9, 1.2, 3.2)
		b.vz = 0.9
		b.z += 0.01
		b.mode = B.Mode.AIR
		b.data = {}
		if ev != null:
			ev.append(["pipe_out", {"pos": g["b"]}])


# --- gadgets as functions of the hole clock ---

static func windmill_angle(g: Dictionary, t: float) -> float:
	return TAU * t / float(g["period"])


static func windmill_blocked(g: Dictionary, t: float) -> bool:
	var a := fposmod(windmill_angle(g, t), TAU / BLADES)
	return a < BLADE_HALF or a > TAU / BLADES - BLADE_HALF


static func _mover_pos(g: Dictionary, t: float) -> Vector2:
	var s := 0.5 - 0.5 * cos(TAU * t / float(g["period"]))
	return (g["p0"] as Vector2).lerp(g["p1"], s)


static func mover_pos(g: Dictionary, t: float) -> Vector2:
	return _mover_pos(g, t)


static func _mover_vel(g: Dictionary, t: float) -> Vector2:
	var w := TAU / float(g["period"])
	return ((g["p1"] as Vector2) - (g["p0"] as Vector2)) * 0.5 * w * sin(w * t)


static func spinner_angle(g: Dictionary, t: float) -> float:
	return float(g["speed"]) * t


static func _spinner_closest(g: Dictionary, t: float, p: Vector2) -> Vector2:
	var a := spinner_angle(g, t)
	var d := Vector2(cos(a), sin(a)) * float(g["len"])
	var c: Vector2 = g["pos"]
	return Geometry2D.get_closest_point_to_segment(p, c - d, c + d)


## Simulates a shot from `b` at hole time `clock` until the ball rests, drops or is lost (or `max_t` passes).
## Returns the final ball; `path` (if given) collects its 3D points every `every` ticks.
static func simulate(hole: LinksHole, b: LinksBall, clock: float, max_t := 12.0, path = null, every := 3) -> LinksBall:
	var s := b.copy()
	s.at_rest = false
	var n := int(max_t / TICK)
	for i in n:
		tick(hole, s, clock + i * TICK, null)
		if path != null and i % every == 0:
			path.append(s.world(R))
		if s.mode == B.Mode.SUNK or s.mode == B.Mode.LOST or s.at_rest:
			break
	return s
