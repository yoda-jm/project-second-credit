class_name FrostpeakBiathlonView
extends RefCounted
## The biathlete on the course, and the one camera that follows them. The skier skates with a double pole push on
## every stride, in step with the player's pushes (the animation chases the stride, it never jumps), tucks on the
## descents, coasts into the range, turns to the targets and lies down; the rifle comes off the back into the hands
## and goes back after the fifth shot. The poles are placed each frame from the hands (planted on the snow, or under
## the arms in a tuck). The camera rides with the skier from angles picked for each stretch of the course, and at the
## range goes over the shooter's shoulder and on down the line of fire into the sight; its sway is the rifle's.

const START := {"az": 2.65, "el": 0.22, "dist": 7.5, "pitch": 0.0, "ahead": 0.0, "lift": 1.0, "fov": 46.0}
## the camera round the skier on each stretch of the course: [from s, az, el, dist]
const SHOTS := [[0.0, 1.35, 0.18, 9.0], [92.0, 0.55, 0.3, 7.5], [128.0, 2.3, 0.24, 7.0], [178.0, 1.0, 0.3, 7.5],
	[215.0, 1.3, 0.12, 8.5], [292.0, 0.6, 0.3, 7.5], [372.0, 1.35, 0.18, 9.0]]

## One biathlete with the rifle and the poles.
class Skier:
	var node: Node3D
	var skel: Skeleton3D
	var ap: AnimationPlayer
	var rifle: Node3D
	var poles: Array[Node3D] = []
	var rifle_w := 0.0  ## 0 on the back, 1 in the hands
	var tuck_w := 0.0

	func _init(v: FrostpeakView3D) -> void:
		node = v._athlete("biathlete")
		node.visible = false
		skel = node.find_children("*", "Skeleton3D", true, false)[0]
		ap = node.find_child("AnimationPlayer", true, false)
		rifle = v._scene("rifle")
		skel.add_child(rifle)
		for i in 2:
			var p := v._scene("ski_pole")
			skel.add_child(p)
			poles.append(p)
		for n in [rifle, poles[0], poles[1]]:
			for mi in n.find_children("*", "VisualInstance3D", true, false):
				(mi as VisualInstance3D).layers |= FrostpeakView3D.RIM_LAYER

	## The rifle (on the back, or in the hands at the range, aimed at `plate`) and the poles (from the hands,
	## planted on the snow; under the arms in a tuck; laid beside the mat while shooting).
	func props(delta: float, plate: Vector3) -> void:
		var prone := ap.current_animation == "prone"
		rifle_w = move_toward(rifle_w, 1.0 if prone else 0.0, delta * 1.4)
		tuck_w = move_toward(tuck_w, 1.0 if ap.current_animation == "tuck" else 0.0, delta * 4.0)
		var bone := func(n: String) -> Transform3D: return skel.get_bone_global_pose(skel.find_bone(n))
		var chest: Transform3D = bone.call("chest")
		var back := chest * Transform3D(Basis(Vector3.UP, 0.18) * Basis(Vector3.RIGHT, -PI * 0.5) * Basis(Vector3.FORWARD, 0.25),
			Vector3(0.06, -0.26, -0.17))
		var shoulder: Vector3 = (bone.call("arm.R") as Transform3D).origin
		var target := skel.global_transform.affine_inverse() * plate
		var dir := (target - shoulder).normalized()
		var aim_b := Basis.looking_at(-dir, Vector3.UP)  # the rifle's +Z down the line of fire
		var hands := Transform3D(aim_b, shoulder + aim_b * Vector3(-0.02, -0.02, -0.06))
		rifle.transform = back.interpolate_with(hands, smoothstep(0.0, 1.0, rifle_w))
		for i in 2:
			var side := "L" if i == 0 else "R"
			var hand: Transform3D = bone.call("hand." + side)
			var fore: Transform3D = bone.call("forearm." + side)
			var grip := hand.origin + hand.basis.y.normalized() * 0.05
			var pole_dir := ((hand.origin - fore.origin).normalized() + Vector3(0, -0.45, 0)).normalized()
			var tuck_dir := Vector3(0.12 * (1.0 if i == 0 else -1.0), 0.3, -1.0).normalized()
			pole_dir = pole_dir.lerp(tuck_dir, tuck_w).normalized()
			var tip := grip + pole_dir * 1.6
			if tip.y < 0.03:  # planted: swing it up until the tip rests on the snow
				var dy := clampf((0.03 - grip.y) / 1.6, -0.999, 0.999)
				var hz := Vector2(pole_dir.x, pole_dir.z).normalized() * sqrt(1.0 - dy * dy)
				pole_dir = Vector3(hz.x, dy, hz.y)
			var xf := Transform3D(FrostpeakBiathlonView._along(-pole_dir), grip)
			if rifle_w > 0.0:  # (laid in the athlete's own frame: forward along the mat, beside the legs)
				var to_skel := skel.global_transform.affine_inverse() * node.global_transform
				var lay := to_skel * Transform3D(Basis(Vector3.RIGHT, -PI * 0.5), Vector3(0.6 * (1.0 if i == 0 else -1.0), 0.03, 0.05))
				xf = xf.interpolate_with(lay, clampf(rifle_w * 1.5, 0.0, 1.0))
			poles[i].transform = xf


var v: FrostpeakView3D
var venue: FrostpeakBiathlon
var racer: Skier
var waiting: Skier  ## the next skier, at the start while the camera comes back
var athlete: Node3D  ## the racer's model
var ap: AnimationPlayer
var cam: FrostpeakJumpCam
var frame := Transform3D()  ## the camera rig's frame: at the skier, x along their heading
var scope_k := 0.0  ## how far into the rifle's sight the camera is (the HUD's scope mask follows)
var pos := Vector3.ZERO  ## the skier's feet
var _heading := 0.0  ## the rig's heading (radians, smoothed)
var _head_v := 0.0
var _yaw := 0.0  ## the skier's facing
var _yaw_v := 0.0
var _range_w := 0.0  ## the camera over the shoulder (0 riding with the skier)
var _since_shot := 99.0  ## seconds since the fifth shot
var _after := 0.0  ## past the finish: metres glided on
var _after_v := -1.0
var _spray: GPUParticles3D
var _puff: GPUParticles3D
var _hits: Array = []  ## [seconds to go, target] for shots on their way


func _init(view: FrostpeakView3D, vn: FrostpeakBiathlon) -> void:
	v = view
	venue = vn
	racer = Skier.new(v)
	waiting = Skier.new(v)
	athlete = racer.node
	ap = racer.ap
	cam = FrostpeakJumpCam.new(func(x: float, z: float) -> float:
		var w := frame * Vector3(x, 0.0, z)
		return venue.height(w.x, w.z) - frame.origin.y)
	# snow kicked up behind the skis
	_spray = GPUParticles3D.new()
	_spray.amount = 60
	_spray.lifetime = 0.7
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.25, 0.02, 0.3)
	pm.direction = Vector3(0, 0.6, -1)
	pm.spread = 30.0
	pm.initial_velocity_min = 1.0
	pm.initial_velocity_max = 2.5
	pm.gravity = Vector3(0, -4, 0)
	pm.scale_min = 0.571
	pm.scale_max = 1.43
	pm.scale_curve = _curve_tex(Fx.size_curve(true))
	_spray.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.14, 0.14)
	_spray.draw_pass_1 = q
	_spray.material_override = Fx.material("soft", Color(1, 1, 1, 0.55))
	_spray.position = Vector3(0, 0.05, -0.4)
	_spray.emitting = false
	athlete.add_child(_spray)
	# a puff of snow where a miss hits the berm
	_puff = GPUParticles3D.new()
	_puff.amount = 24
	_puff.lifetime = 0.9
	_puff.one_shot = true
	_puff.explosiveness = 0.95
	var pp := ParticleProcessMaterial.new()
	pp.direction = Vector3(0, 0.5, 1)
	pp.spread = 50.0
	pp.initial_velocity_min = 0.3
	pp.initial_velocity_max = 1.1
	pp.gravity = Vector3(0, -1.5, 0)
	pp.scale_curve = _curve_tex(Fx.size_curve(true))
	_puff.process_material = pp
	var q2 := QuadMesh.new()
	q2.size = Vector2(0.08, 0.08)
	_puff.draw_pass_1 = q2
	_puff.material_override = Fx.material("soft", Color(1, 1, 1, 0.8))
	_puff.emitting = false
	venue.root.add_child(_puff)


func _curve_tex(c: Curve) -> CurveTexture:
	var t := CurveTexture.new()
	t.curve = c
	return t


# ------------------------------------------------------------------ where the skier is

## Where the skier is `d` metres into the race: on the course, drawn aside to the mat around the range, and on along
## the straight past the finish.
func path_point(b: Biathlon, d: float) -> Vector3:
	var lap := BiathlonCourse.lap()
	var s := fposmod(d, lap) if d < Biathlon.LAPS * lap else d - Biathlon.LAPS * lap
	var p := BiathlonCourse.point(s)
	var at := lap + BiathlonCourse.RANGE_S
	var off := 0.0
	if not b.shooting_done:
		off = smoothstep(at - 16.0, at - 0.5, d)
	else:
		off = 1.0 - smoothstep(at + 0.5, at + 16.0, d)
	p.z -= off * BiathlonCourse.MAT_OFF
	p.y = venue.height(p.x, p.z)
	return p


## The next skier waits on the start line (a model of their own, so the one who has just finished stays put).
func wait_at_start(nation: int) -> void:
	v._dress(waiting.node, nation)
	waiting.node.visible = true
	waiting.node.transform = Transform3D(Basis(Vector3.UP, PI * 0.5), BiathlonCourse.point(0.0))
	v._anim(waiting.node, "ready")
	waiting.props(0.0, venue.plate())


func update_waiting(delta: float) -> void:
	if waiting.node.visible:
		waiting.props(delta, venue.plate())


## The skier on the start line, ready: the racer takes the waiting skier's place, in the same pose.
func at_start(nation: int) -> void:
	v._dress(athlete, nation)
	athlete.visible = true
	if waiting.node.visible:
		waiting.node.visible = false
		ap.play("ready", 0.0)
		ap.seek(waiting.ap.current_animation_position, true)
	pos = BiathlonCourse.point(0.0)
	_yaw = PI * 0.5
	_yaw_v = 0.0
	_heading = 0.0
	_head_v = 0.0
	_after = 0.0
	_after_v = -1.0
	_since_shot = 99.0
	racer.rifle_w = 0.0
	_range_w = 0.0
	scope_k = 0.0
	_hits.clear()
	venue.reset_targets()
	athlete.transform = Transform3D(Basis(Vector3.UP, _yaw), pos)
	v._anim(athlete, "ready")
	frame = Transform3D(Basis.IDENTITY, pos)
	cam.reset(START)
	_place_props(0.0)


## The camera's pose over the skier waiting at the start (the intro flight ends there).
func start_pose() -> Array[Vector3]:
	frame = Transform3D(Basis.IDENTITY, BiathlonCourse.point(0.0))
	var pl := cam.pose(Vector3.ZERO, START)
	return [frame * pl[0], frame * pl[1]]


func on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot":
			_hits.append([0.16, int(d["index"]), bool(d["hit"]), d["aim"]])  # 50 m of flight
		"range_done":
			_since_shot = 0.0


static func _wrap(a: float) -> float:
	return fposmod(a + PI, TAU) - PI


func update(b: Biathlon, delta: float, result: bool) -> void:
	athlete.visible = true
	var lap := BiathlonCourse.lap()
	var d: float = v._between("biathlon_d", b.dist)
	if result:  # past the finish the skier glides on and stops
		if _after_v < 0.0:
			_after_v = b.speed
			_after = d - Biathlon.LAPS * lap  # from where the skier was drawn (gliding from the next frame)
		else:
			_after_v = maxf(0.0, _after_v - delta * (0.8 + _after_v * 0.1))
			_after += _after_v * delta
		d = Biathlon.LAPS * lap + _after
	var h := Vector3.ZERO
	if b.stage == Biathlon.Stage.PENALTY:
		var u: float = v._between("biathlon_pen", b.pen_done)
		pos = BiathlonCourse.pen_point(u)
		h = BiathlonCourse.pen_point(u + 0.6) - BiathlonCourse.pen_point(u - 0.6)
	else:
		pos = path_point(b, d)
		h = path_point(b, d + 0.6) - path_point(b, d - 0.6)
	var hxz := Vector2(h.x, h.z)
	var heading := atan2(hxz.y, hxz.x) if hxz.length() > 0.01 else _heading
	var slope := h.y / maxf(hxz.length(), 0.01)
	# the skier's facing: along the track, to the targets at the range
	var face := atan2(h.x, h.z) if hxz.length() > 0.01 else _yaw
	var ranged := b.stage == Biathlon.Stage.RANGE
	if ranged and b.range_t > 0.35 and not (b.shooting_done and b.range_t > b._shot_at + 1.0):
		face = PI
	var r := FrostpeakJumpCam.spring(_yaw, _yaw_v, _yaw + _wrap(face - _yaw), 7.0, delta)
	_yaw = r.x
	_yaw_v = r.y
	var pitch := -atan(slope) * (0.0 if ranged else 0.8)
	athlete.transform = Transform3D(Basis(Vector3.UP, _yaw) * Basis(Vector3.RIGHT, pitch), pos)
	_animate(b, delta, ranged)
	_place_props(delta)
	# the shots: a hit closes its flap as the bullet arrives, a miss throws up snow on the berm
	for sh in _hits:
		sh[0] -= delta
		if sh[0] <= 0.0:
			if sh[2]:
				venue.hit(sh[1])
			else:
				var a: Vector2 = sh[3]
				_puff.global_position = venue.plate() + Vector3(a.x, a.y, -2.0)
				_puff.restart()
	_hits = _hits.filter(func(sh): return sh[0] > 0.0)
	if b.shooting_done:
		_since_shot += delta
	_spray.emitting = b.stage != Biathlon.Stage.RANGE and b.speed > 3.0 and not result
	(_spray.process_material as ParticleProcessMaterial).initial_velocity_max = 1.0 + b.speed * 0.2
	# the camera rig follows the heading, smoothly
	var hr := FrostpeakJumpCam.spring(_heading, _head_v, _heading + _wrap(heading - _heading), 2.2, delta)
	_heading = hr.x
	_head_v = hr.y
	frame = Transform3D(Basis(Vector3.UP, -_heading), pos)
	_aim_rig(b, slope, result)


func _animate(b: Biathlon, delta: float, ranged: bool) -> void:
	if b.phase == WinterEvent.Phase.READY:
		v._anim(athlete, "ready")
		return
	if b.phase == WinterEvent.Phase.DONE:
		v._anim(athlete, "celebrate" if _after_v < 1.5 else "ready")
		return
	if ranged:
		var up := b.shooting_done and b.range_t > b._shot_at + 0.5
		v._anim(athlete, "prone" if b.range_t > 0.55 and not up else "ready")
		return
	if b.tuck > 0.5:
		v._anim(athlete, "tuck")
		return
	if b.meter > 1.3 and b.speed > 2.0:
		v._anim(athlete, "ready")
		return
	# the stride: the animation chases the push rhythm (0 is the start of the left push, 0.5 the right)
	var length := ap.get_animation("skate").length
	var want := (0.0 if b.next_foot == "right" else 0.5) + 0.5 * clampf(b.meter, 0.0, 1.0)
	var now := ap.current_animation_position / length if ap.current_animation == "skate" else want
	var err := fposmod(want - now + 0.5, 1.0) - 0.5
	var nominal := length / (2.0 * b.stride_time())
	v._anim(athlete, "skate", nominal * clampf(1.0 + err * 4.0, 0.4, 2.0))


func _place_props(delta: float) -> void:
	racer.props(delta, venue.plate())


## A basis whose +Y points along `y` (the pole's grip is its origin, the shaft runs down -Y).
static func _along(y: Vector3) -> Basis:
	var yy := y.normalized()
	var x := Vector3.UP.cross(yy)
	if x.length() < 0.01:
		x = Vector3.RIGHT
	x = x.normalized()
	return Basis(x, yy, x.cross(yy).normalized())


# ------------------------------------------------------------------ the camera

func _aim_rig(b: Biathlon, slope: float, result: bool) -> void:
	var c := cam
	if b.phase == WinterEvent.Phase.READY:
		c.aim("az", 1.55, 0.7)
		c.aim("el", 0.18, 0.7)
		c.aim("dist", 8.0, 0.7)
		c.aim("ahead", 2.0, 0.7)
		c.aim("lift", 1.0, 0.7)
		c.aim("fov", 46.0, 0.8)
		return
	if result:
		c.aim("az", 2.3, 0.6)
		c.aim("el", 0.14, 0.6)
		c.aim("dist", 7.0, 0.6)
		c.aim("ahead", 0.0, 0.6)
		c.aim("lift", 1.2 + 7.0 * tan(deg_to_rad(44.0 * 0.28)), 1.0)
		c.aim("fov", 44.0, 0.6)
		return
	var s := fposmod(b.dist, BiathlonCourse.lap())
	var shot: Array = SHOTS[0]
	for sh in SHOTS:
		if s >= sh[0]:
			shot = sh
	if b.stage == Biathlon.Stage.PENALTY:
		shot = [0.0, 1.6, 0.35, 9.0]
	c.aim("az", shot[1], 0.55)
	c.aim("el", shot[2], 0.7)
	c.aim("dist", shot[3] + b.speed * 0.08, 0.7)
	c.aim("pitch", -atan(slope), 2.0)
	c.aim("ahead", 2.5, 0.8)
	c.aim("lift", 1.0, 0.8)
	c.aim("fov", 48.0 + b.speed * 0.3, 0.8)


## [camera, look, lens] for this frame: the rig, blended over the shoulder and into the sight at the range.
func camera(b: Biathlon, delta: float) -> Array:
	cam.step(delta)
	var pl := cam.pose(Vector3.ZERO)
	var c: Vector3 = frame * pl[0]
	var l: Vector3 = frame * pl[1]
	var f: float = cam.value["fov"]
	var mat := BiathlonCourse.mat()
	# over the shoulder: behind the shooter's right shoulder, the range and the targets ahead
	var sc := mat + Vector3(0.85, 1.25, 1.9)
	var sl := mat + Vector3(-0.1, 0.1, -12.0)
	# in the sight: halfway down the line of fire, looking where the rifle points
	var eye := mat + Vector3(0.0, 0.42, -1.3)
	var aim_pt := venue.on_plate(b.aim)
	var zc := eye.lerp(aim_pt, 0.5)
	# how far along: over the shoulder as the skier comes to the mat, into the sight once lying down
	var into := 0.0
	var over := 0.0
	if b.stage == Biathlon.Stage.RANGE or (b.shooting_done and _since_shot < 4.0):
		var t := b.range_t
		if b.shooting_done:
			over = 1.0 - smoothstep(1.2, 3.2, _since_shot)
			into = 1.0 - smoothstep(0.35, 1.2, _since_shot)
		else:
			over = lerpf(0.35, 1.0, smoothstep(0.0, 1.5, t))
			into = smoothstep(1.35, 2.3, t)
	elif b.stage == Biathlon.Stage.SKI and not b.shooting_done:
		var left := BiathlonCourse.lap() + BiathlonCourse.RANGE_S - b.dist
		over = 0.35 * smoothstep(22.0, 0.0, left)
	_range_w = over
	scope_k = into
	var ow := over * over * (3.0 - 2.0 * over)
	c = c.lerp(sc, ow)
	l = l.lerp(sl, ow)
	f = lerpf(f, 50.0, ow)
	var iw := into * into * (3.0 - 2.0 * into)
	c = c.lerp(zc, iw)
	l = l.lerp(aim_pt, iw)
	var zoom := 2.0 * rad_to_deg(atan(0.42 / zc.distance_to(aim_pt)))  # the plate and a little round it
	f = lerpf(f, zoom, pow(iw, 0.6))
	return [c, l, f]
