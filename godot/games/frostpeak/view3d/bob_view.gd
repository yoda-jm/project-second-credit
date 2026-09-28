class_name FrostpeakBobView
extends RefCounted
## The four-man bob on the run, and the cameras that follow it. At the start the crew stands at the sled's handles,
## runs it off the block (their stride in time with the pushes) and jumps in one after the other; the pilot sits
## up to steer, the three behind tuck down. On the run the sled rides the channel where the rules put it: up the
## banks in the curves, tilted to the wall under it, drifting a little with its swing; a hit throws up ice, a crash
## rolls it onto its side. Past the finish it brakes on the run-out and the crew throws their arms up.
##
## The camera is television: a dolly running beside the start, then the on-board chase camera behind and above the
## sled that leans into the banks with it, and trackside cameras at the horseshoe, the labyrinth and the finish.
## Between them the picture only ever changes under a dressed wipe (the view's wipe, with the curve's name on it).

## the crew's seats along the sled (z, + forward; the pilot first) and where each pushes from (x + left, z): the
## pilot on the left front handle, number two on the right one, number three on the left rear handle, the
## brakeman at the bar across the tail; and which way their hands reach for the grip (the animations' suffix)
const SEATS: Array[float] = [0.75, 0.02, -0.7, -1.42]
const SLOTS: Array[Vector3] = [Vector3(0.865, 0.0, 0.04), Vector3(-0.865, 0.0, 0.04), Vector3(0.865, 0.0, -1.16), Vector3(0.0, 0.0, -2.82)]
const GRIP: Array[String] = ["_l", "_r", "_l", ""]
## the push handles' housings on the sled (x + left, y, z): front left, front right, rear left, rear right; who holds
## each (it slides in once they are aboard)
const HANDLES: Array[Vector3] = [Vector3(0.335, 0.46, 0.6), Vector3(-0.335, 0.46, 0.6), Vector3(0.335, 0.42, -0.6), Vector3(-0.335, 0.42, -0.6)]
const HANDLE_OF: Array[int] = [0, 1, 2, 2]
const TUCK_IN := 0.24  ## how far the handles slide in
const LEVER := Vector3(0.0, 0.15, -1.62)  ## the brake lever's pivot
## at the bottom, each their own joy: [animation, speed, seconds after the sled stops]
const JOY: Array = [["wave_seat", 1.0, 0.1], ["pump", 1.18, 0.45], ["hug", 0.9, 0.8], ["cheer", 1.06, 0.25]]
const SEAT_Y := 0.12  ## the tub's floor above the ice
const PUSH_STRIDE := 4.9  ## m/s the push animation runs at, at its own speed
const BRAKE := 10.0  ## m/s^2 on the run-out
## the trackside cameras: [name, from s, to s]; the chase camera everywhere else on the run
const TV := [["horseshoe", 352.0, 468.0], ["labyrinth", 628.0, 742.0], ["finish", 902.0, 99999.0]]

## A sled and its crew.
class Crew:
	var rig: Node3D  ## at the sled's frame: the sled model and the four
	var sled: Node3D
	var men: Array[Node3D] = []
	var handles: Array[Node3D] = []
	var lever: Node3D
	var tucked: Array[float] = [0.0, 0.0, 0.0, 0.0]  ## how far each handle has slid in (0..1)

	func _init(v: FrostpeakView3D) -> void:
		rig = Node3D.new()
		rig.name = "Bob"
		v.add_child(rig)
		sled = v._scene("bobsled")
		rig.add_child(sled)
		for i in 4:
			var h := v._scene("bob_handle")
			sled.add_child(h)
			handles.append(h)
		lever = v._scene("bob_brake")
		lever.position = FrostpeakBobView.LEVER
		sled.add_child(lever)
		for mi in sled.find_children("*", "VisualInstance3D", true, false):
			(mi as VisualInstance3D).layers |= FrostpeakView3D.RIM_LAYER
		place_handles()
		for i in 4:
			var m := v._athlete("bobber")
			v.remove_child(m)
			rig.add_child(m)
			men.append(m)
		rig.visible = false

	func dress(v: FrostpeakView3D, nation: int) -> void:
		v._dress(rig, nation)

	## The handles, slid out by what is left of `tucked`; the brake lever pulled back by `pull` (0..1).
	func place_handles(pull := 0.0) -> void:
		for i in 4:
			var at: Vector3 = FrostpeakBobView.HANDLES[i]
			var side := signf(at.x)
			var k := smoothstep(0.0, 1.0, tucked[i])
			handles[i].transform = Transform3D(Basis.IDENTITY.scaled(Vector3(side, 1.0, 1.0)), at - Vector3(side * FrostpeakBobView.TUCK_IN * k, 0, 0))
		lever.transform = Transform3D(Basis(Vector3.RIGHT, -0.75 * pull), FrostpeakBobView.LEVER)

	## Everyone at the handles, ready (before the start), the handles out and the brake off.
	func at_handles(v: FrostpeakView3D) -> void:
		tucked = [0.0, 0.0, 0.0, 0.0]
		place_handles()
		for i in 4:
			men[i].position = FrostpeakBobView.SLOTS[i]
			men[i].rotation = Vector3.ZERO
			v._anim(men[i], "ready" + FrostpeakBobView.GRIP[i])


var v: FrostpeakView3D
var venue: FrostpeakBobVenue
var racer: Crew
var waiting: Crew  ## the next crew, at the start while the camera comes back
var rig: Node3D  ## the racer's rig
var pos := Vector3.ZERO  ## the sled on the run
var bank := 0.0  ## how far the sled leans on the wall (radians, + to its right)
var cam_mode := "start"
var wipe_label := ""  ## what the wipe shows (the curve the next camera is at)
var _pending := ""
var _cut := false
var _after := 0.0  ## past the finish: metres braked on
var _after_v := -1.0
var _yaw := 0.0  ## the sled's drift (radians)
var _cam := Vector3.ZERO
var _cam_v := Vector3.ZERO
var _look := Vector3.ZERO
var _look_v := Vector3.ZERO
var _roll := 0.0
var _roll_v := 0.0
var _have := false
var _shake := 0.0
var _t := 0.0
var _s := 0.0  ## the sled's s as drawn
var _w := 0.0
var _dust: GPUParticles3D
var _spray: GPUParticles3D
var _brake_ice: GPUParticles3D  ## the brake's claw throwing up ice past the finish, and a few sparks
var _sparks: GPUParticles3D
var _stop_t := -1.0  ## seconds since the sled stopped on the run-out
var shown_speed := 0.0  ## the speed as drawn (braking past the finish)
var _seen_crash := false


func _init(view: FrostpeakView3D, vn: FrostpeakBobVenue) -> void:
	v = view
	venue = vn
	racer = Crew.new(v)
	waiting = Crew.new(v)
	rig = racer.rig
	# fine ice dust off the runners, trailing behind
	_dust = GPUParticles3D.new()
	_dust.amount = 70
	_dust.lifetime = 0.9
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.35, 0.02, 0.2)
	pm.direction = Vector3(0, 0.4, -1)
	pm.spread = 20.0
	pm.initial_velocity_min = 0.5
	pm.initial_velocity_max = 1.5
	pm.gravity = Vector3(0, -1.0, 0)
	pm.scale_min = 0.5
	pm.scale_max = 1.2
	pm.scale_curve = _curve_tex(Fx.size_curve(true))
	_dust.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.12, 0.12)
	_dust.draw_pass_1 = q
	_dust.material_override = Fx.material("soft", Color(0.9, 0.95, 1.0, 0.45))
	_dust.position = Vector3(0, 0.05, -1.9)
	_dust.local_coords = false
	_dust.emitting = false
	rig.add_child(_dust)
	# a burst of ice where the sled hits a wall
	_spray = GPUParticles3D.new()
	_spray.amount = 60
	_spray.lifetime = 0.8
	_spray.one_shot = true
	_spray.explosiveness = 0.9
	var sp := ParticleProcessMaterial.new()
	sp.direction = Vector3(0, 1, 0)
	sp.spread = 60.0
	sp.initial_velocity_min = 1.5
	sp.initial_velocity_max = 4.0
	sp.gravity = Vector3(0, -6, 0)
	sp.scale_min = 0.5
	sp.scale_max = 1.3
	sp.scale_curve = _curve_tex(Fx.size_curve(true))
	_spray.process_material = sp
	var q2 := QuadMesh.new()
	q2.size = Vector2(0.1, 0.1)
	_spray.draw_pass_1 = q2
	_spray.material_override = Fx.material("soft", Color(0.95, 0.98, 1.0, 0.85))
	_spray.emitting = false
	venue.root.add_child(_spray)
	_brake_ice = _emitter(160, 0.8, Vector3(0, 0.9, -0.6), 40.0, Vector2(2.0, 5.0), Vector3(0, -6, 0), Vector2(0.16, 0.16), Color(0.85, 0.92, 1.0, 0.9))
	_sparks = _emitter(70, 0.4, Vector3(0, 0.5, -1), 30.0, Vector2(3.0, 7.0), Vector3(0, -9, 0), Vector2(0.05, 0.05), Color(1.0, 0.72, 0.3, 1.0))
	_sparks.material_override = Fx.material("glow", Color(1.0, 0.72, 0.3, 1.0))
	for e in [_brake_ice, _sparks]:
		e.position = Vector3(0, 0.05, -1.75)
		rig.add_child(e)


func _emitter(amount: int, life: float, dir: Vector3, spread: float, vel: Vector2, grav: Vector3, size: Vector2, col: Color) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = amount
	p.lifetime = life
	p.local_coords = false
	var m := ParticleProcessMaterial.new()
	m.direction = dir
	m.spread = spread
	m.initial_velocity_min = vel.x
	m.initial_velocity_max = vel.y
	m.gravity = grav
	m.scale_curve = _curve_tex(Fx.size_curve(true))
	p.process_material = m
	var q := QuadMesh.new()
	q.size = size
	p.draw_pass_1 = q
	p.material_override = Fx.material("soft", col)
	p.emitting = false
	return p


func _curve_tex(c: Curve) -> CurveTexture:
	var t := CurveTexture.new()
	t.curve = c
	return t


# ------------------------------------------------------------------ the sled on the run

## The sled's frame at (s, w): on the channel's surface there, facing down the run, tilted to the wall under it.
func sled_frame(s: float, w: float, yaw := 0.0, roll := 0.0) -> Transform3D:
	var q := BobTrack.section(maxf(s, 0.0), w)
	var c := FrostpeakBobVenue.centre(s)
	var rt := BobTrack.right(maxf(s, 0.0))
	var side := signf(w) if w != 0.0 else 1.0
	var n := Vector3.UP * cos(q.z) - rt * (sin(q.z) * side)
	var d := BobTrack.dir(maxf(s, 0.0))
	var f := Vector3(d.x, BobTrack.grade(maxf(s, 0.0)), d.y).normalized()
	var z := (f - n * f.dot(n)).normalized()
	var b := Basis(n.cross(z), n, z)
	if yaw != 0.0:
		b = Basis(n, yaw) * b
	if roll != 0.0:
		b = Basis(b.z, roll) * b
	return Transform3D(b.orthonormalized(), c + rt * q.x + Vector3(0, q.y, 0))


## The next crew waits at the start (a sled of their own, so the one that has just finished stays put).
func wait_at_start(nation: int) -> void:
	waiting.dress(v, nation)
	waiting.rig.visible = true
	waiting.rig.transform = sled_frame(0.0, 0.0)
	waiting.at_handles(v)


## The crew at the start, ready: the racing rig takes the waiting crew's place, in the same poses.
func at_start(nation: int) -> void:
	racer.dress(v, nation)
	rig.visible = true
	rig.transform = sled_frame(0.0, 0.0)
	racer.at_handles(v)
	if waiting.rig.visible:
		for i in 4:
			var a: AnimationPlayer = racer.men[i].find_child("AnimationPlayer", true, false)
			var b: AnimationPlayer = waiting.men[i].find_child("AnimationPlayer", true, false)
			a.play(b.current_animation, 0.0)
			a.seek(b.current_animation_position, true)
		waiting.rig.visible = false
	pos = rig.transform.origin
	_after = 0.0
	_after_v = -1.0
	_yaw = 0.0
	_have = false
	cam_mode = "start"
	_pending = ""
	_seen_crash = false
	_shake = 0.0
	_stop_t = -1.0


## The camera's pose over the crew waiting at the start (the intro flight ends there).
func start_pose() -> Array[Vector3]:
	var pl := _start_cam(0.0)
	return [pl[0], pl[1]]


func on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"wall":
			_shake = maxf(_shake, clampf(float(d["strength"]) * 0.25, 0.2, 1.0))
			var side: float = d["side"]
			_spray.global_position = rig.global_transform.origin + BobTrack.right(maxf(_s, 0.0)) * (side * 0.5) + Vector3(0, 0.3, 0)
			_spray.restart()
		"crash":
			_shake = 1.4


func update(b: Bobsled, delta: float, result: bool) -> void:
	_t += delta
	rig.visible = true
	var s: float = v._between("bob_s", b.s)
	var w: float = v._between("bob_w", b.w)
	if result and not b.crashed:  # past the finish the brakeman pulls the brake and the sled stops on the run-out
		if _after_v < 0.0:
			_after_v = b.speed
			_after = s
		else:
			_after_v = maxf(0.0, _after_v - delta * BRAKE * (0.6 + 0.4 * smoothstep(0.0, 1.5, _after_v)))
			_after = minf(_after + _after_v * delta, BobTrack.length() - 3.0)
		s = _after
		w = lerpf(w, 0.0, 1.0 - exp(-delta * 2.0))
	_s = s
	_w = w
	var sp := b.speed if not result else maxf(_after_v, 0.0)
	shown_speed = sp
	# the sled: drifting a little with its swing; on its side after a crash, sliding on down
	_yaw = lerpf(_yaw, clampf(atan2(b.wv, maxf(sp, 3.0)) * 0.6, -0.3, 0.3), 1.0 - exp(-delta * 8.0))
	var roll := 0.0
	if b.crashed:
		roll = -signf(b.w) * PI * 0.5 * smoothstep(0.0, 0.5, b.crash_t)
	var f := sled_frame(s, w, _yaw, roll)
	if b.crashed:
		f.origin += f.basis.y * 0.2 * smoothstep(0.0, 0.5, b.crash_t)
	rig.transform = f
	pos = f.origin
	var q := BobTrack.section(maxf(s, 0.0), w)
	bank = q.z * (signf(w) if w != 0.0 else 1.0)
	_crew(b, delta, result, sp)
	_dust.emitting = b.stage == Bobsled.Stage.RIDE and sp > 8.0 and not result or (b.crashed and sp > 2.0)
	(_dust.process_material as ParticleProcessMaterial).initial_velocity_max = 1.0 + sp * 0.06
	_shake = maxf(0.0, _shake - delta * 1.6)


func _crew(b: Bobsled, delta: float, result: bool, sp: float) -> void:
	var braking := result and not b.crashed and _after_v > 0.6
	if result and not b.crashed and _after_v <= 0.6:
		_stop_t = maxf(_stop_t, 0.0) + delta
	for i in 4:
		var m := racer.men[i]
		if b.phase == WinterEvent.Phase.READY:
			m.position = SLOTS[i]
			v._anim(m, "ready" + GRIP[i])
			continue
		if b.stage == Bobsled.Stage.PUSH or (b.stage == Bobsled.Stage.LOAD and b.load_t < i * Bobsled.LOAD_T / 4.0):
			m.position = SLOTS[i]
			v._anim(m, "push" + GRIP[i], clampf(sp / PUSH_STRIDE, 0.4, 2.6))
			continue
		# jumping in: a hop from the handle up and over the side, down into the seat
		var t := 1.0
		if b.stage == Bobsled.Stage.LOAD:
			t = clampf((b.load_t - i * Bobsled.LOAD_T / 4.0) / 0.4, 0.0, 1.0)
		var seat := Vector3(0.0, SEAT_Y, SEATS[i])
		var e := t * t * (3.0 - 2.0 * t)
		m.position = SLOTS[i].lerp(seat, e) + Vector3(0, sin(PI * t) * 0.45, 0)
		# aboard, their handle slides in
		for h in 4:
			if HANDLE_OF[h] == i and t > 0.5:
				racer.tucked[h] = minf(1.0, racer.tucked[h] + delta / 0.35)
		var sit := "sit" if i == 0 else "tuck"
		var speed := 1.0
		if braking and i == 3:
			sit = "brake"  # the brakeman sits up and hauls the lever
		elif _stop_t >= float(JOY[i][2]):
			sit = JOY[i][0]
			speed = JOY[i][1]
		elif result and not b.crashed and i > 0:
			sit = "sit"  # the run is over: heads up
		if t > 0.3:
			v._anim(m, sit, speed)
	# the brake: pulled past the line, the claw throwing up ice and a few sparks
	var pull := 0.0
	if result and not b.crashed:
		pull = 1.0 if _stop_t < 0.0 else maxf(0.0, 1.0 - _stop_t)
	racer.place_handles(pull)
	_brake_ice.emitting = braking
	_sparks.emitting = braking and _after_v > 6.0


# ------------------------------------------------------------------ the cameras

## The dolly beside the start: level with the crew, a little ahead, running with them down the start ramp.
func _start_cam(s: float) -> Array:
	var at := clampf(s, 0.0, 52.0)
	var f := venue.frame(at + 4.5, -2.4, 2.5)  # over the ramp's left wall, under its roof
	var look := FrostpeakBobVenue.centre(at - 0.6) + Vector3(0, 0.6, 0)
	return [f.origin, look, 50.0]


## Behind and above the sled, riding the run's centre a few metres back, following the sled a little across the
## channel, and leaning with it on the banks.
func _chase(b: Bobsled, sp: float) -> Array:
	var back := lerpf(4.6, 6.6, clampf(sp / 35.0, 0.0, 1.0))
	var sc := maxf(_s - back, 0.0)
	var q := BobTrack.section(sc, _w * 0.42)
	var c := FrostpeakBobVenue.centre(sc)
	var rt := BobTrack.right(sc)
	var cam := c + rt * q.x + Vector3(0, q.y + 1.35 + sp * 0.008, 0)
	var d := BobTrack.dir(maxf(_s, 0.0))
	var look := pos + Vector3(d.x, 0.0, d.y) * 4.0 + Vector3(0, 0.55, 0)
	return [cam, look, 62.0 + sp * 0.3]


## A trackside camera: [camera, look, lens] for the sled at the moment.
func _tv(name: String, result := false) -> Array:
	var cam := venue.tv_spot(name)
	if name == "runout":  # a camera car beside the run-out, a little ahead of the braking sled and above it
		cam = venue.frame(minf(_s + 3.5, BobTrack.length() - 1.0), -5.0, 4.4).origin
	var half: float = {"horseshoe": 3.4, "labyrinth": 2.6, "finish": 3.2, "runout": 2.5}.get(name, 3.0)
	var look := pos + Vector3(0, 0.5, 0)
	if name == "runout":  # the crew, framed low, under the result
		look = pos + Vector3(0, 1.5, 0)
	var dist := maxf(4.0, cam.distance_to(look))
	return [cam, look, clampf(rad_to_deg(2.0 * atan(half / dist)), 6.0, 55.0)]


## Which camera the moment wants.
func _want(b: Bobsled, result: bool) -> String:
	if b.stage == Bobsled.Stage.PUSH or b.stage == Bobsled.Stage.LOAD or b.phase == WinterEvent.Phase.READY:
		return "start"
	if cam_mode == "start" and b.s < BobTrack.PUSH_END + 2.0:
		return "start"  # the dolly sees them in and away down the ramp
	if b.crashed:  # the camera that saw it stays on the upturned sled
		return cam_mode if cam_mode != "start" else "chase"
	if result:
		return "runout"  # past the line: a camera car ahead of the braking sled, close on the crew as it stops
	for tv in TV:
		if _s >= tv[1] and _s < tv[2]:
			return tv[0]
	return "chase"


## [camera, look, lens, roll, cut, max turn] for this frame.
func camera(b: Bobsled, delta: float, result: bool) -> Array:
	var want := _want(b, result)
	if want != cam_mode and _pending == "":
		_pending = want
		v._wipe_t = 0.0
		wipe_label = {"chase": "ON BOARD", "horseshoe": "HORSESHOE", "labyrinth": "LABYRINTH", "finish": "FINISH", "start": "START", "runout": "FINISH"}.get(want, "")
	if _pending != "" and v._wipe_t >= FrostpeakView3D.WIPE_COVER:
		cam_mode = _pending
		_pending = ""
		_cut = true
		_have = false
	var sp := b.speed if not result else maxf(_after_v, 0.0)
	var pl: Array
	match cam_mode:
		"start":
			pl = _start_cam(_s)
		"chase":
			pl = _chase(b, sp)
		_:
			pl = _tv(cam_mode, result)
	var cam: Vector3 = pl[0]
	var look: Vector3 = pl[1]
	var roll := 0.0
	if cam_mode == "chase" and not b.crashed:
		roll = -bank * 0.45
	# a little softness on the chase camera, so the swing across the channel reads as a lean, not a jolt
	if not _have or cam_mode != "chase":
		_cam = cam - pos
		_look = look - pos
		_cam_v = Vector3.ZERO
		_look_v = Vector3.ZERO
		_roll = roll
		_roll_v = 0.0
		_have = true
	else:
		# (softened relative to the sled, so the camera keeps up with it at any speed)
		var w := 9.0 if cam_mode == "chase" else 30.0
		var a := FrostpeakView3D._spring3(_cam, _cam_v, cam - pos, w, delta)
		_cam = a[0]
		_cam_v = a[1]
		var l := FrostpeakView3D._spring3(_look, _look_v, look - pos, w * 1.5, delta)
		_look = l[0]
		_look_v = l[1]
		var r := FrostpeakJumpCam.spring(_roll, _roll_v, roll, 5.0, delta)
		_roll = r.x
		_roll_v = r.y
	var shake := Vector3(sin(_t * 47.0), sin(_t * 53.0 + 1.0), sin(_t * 41.0 + 2.0)) * _shake * 0.06
	var cut := _cut
	_cut = false
	return [pos + _cam + shake, pos + _look, pl[2], _roll, cut, 1.2 if cam_mode == "chase" or cam_mode == "start" else 5.0]
