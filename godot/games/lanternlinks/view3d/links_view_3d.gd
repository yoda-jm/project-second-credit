class_name LinksView3D
extends Node3D
## Lantern Links in 3D: the garden (LinksGarden) and the hole (LinksCourse) rebuilt for each hole; the ball (glossy,
## dimpled, rolling for real, with a glowing trail in the player's colour and its own little light at night); the
## aiming guide (dots along the shot's first line and its first bank), the putter drawn back as you pull and
## swinging through; effects for every contact; and a directing camera: a fly-over of each new hole, behind the
## ball while aiming (orbiting as you aim), chasing the rolling ball, swooping to the cup when it drops, the
## overview on Tab, an orbit over the scorecard.

const H = preload("res://games/lanternlinks/engine/links_hole.gd")
const B = preload("res://games/lanternlinks/engine/links_ball.gd")
const P = preload("res://games/lanternlinks/engine/links_physics.gd")
const E = preload("res://games/lanternlinks/engine/links_engine.gd")
const C = preload("res://games/lanternlinks/view3d/links_course.gd")
const M := "res://games/lanternlinks/art/models/"
const GUIDE_DOTS := 36
const TRAIL := 14

@export var game: LinksGame

var camera: Camera3D
var garden: LinksGarden
var course: LinksCourse
var fx: LinksFx
var _ball: MeshInstance3D
var _ball_light: OmniLight3D
var _ball_mat: StandardMaterial3D
var _trail: MeshInstance3D
var _trail_mat: StandardMaterial3D
var _trail_pts: Array[Vector3] = []
var _dots: MultiMeshInstance3D
var _dot_mat: StandardMaterial3D
var _putter: Node3D
var _putter_swing := 0.0
var _putter_angle := 0.0
var _guide_key := ""
var _guide: PackedVector3Array = []
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _chase_dir := Vector3.FORWARD
var _time := 0.0
var _shake := 0.0
var _squash := 0.0
var _prev_ball := Vector3.ZERO
var _sink_t := 0.0
var _lost_at := Vector3.ZERO
var _loop_base := 0.0
var _cam_snap := true
var _intro_t := 0.0
var _splash_t := 10.0


func _ready() -> void:
	garden = LinksGarden.new()
	add_child(garden)
	garden.build()
	course = LinksCourse.new()
	add_child(course)
	fx = LinksFx.new()
	add_child(fx)
	camera = Camera3D.new()
	camera.fov = 50.0
	camera.near = 0.03
	camera.far = 900.0
	camera.current = true
	add_child(camera)
	_build_ball()
	_build_guide()
	game.game_started.connect(_on_game)
	# before a round starts (the seats screen) the camera drifts over the first hole
	if not game.holes.is_empty():
		_show_hole(game.first_hole, true)


func _build_ball() -> void:
	_ball = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = P.R
	sm.height = P.R * 2.0
	sm.radial_segments = 32
	sm.rings = 16
	_ball.mesh = sm
	_ball_mat = StandardMaterial3D.new()
	_ball_mat.albedo_color = Color(0.97, 0.97, 0.95)
	_ball_mat.roughness = 0.25
	_ball_mat.clearcoat_enabled = true
	_ball_mat.clearcoat = 0.8
	_ball_mat.clearcoat_roughness = 0.1
	# dimples: a cellular noise as a normal map, mapped in the ball's own space so they roll with it
	var nt := NoiseTexture2D.new()
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_CELLULAR
	fn.frequency = 0.09
	fn.cellular_return_type = FastNoiseLite.RETURN_DISTANCE
	nt.noise = fn
	nt.width = 256
	nt.height = 128
	nt.seamless = true
	nt.as_normal_map = true
	nt.bump_strength = 6.0
	_ball_mat.normal_enabled = true
	_ball_mat.normal_texture = nt
	_ball_mat.normal_scale = 0.5
	_ball_mat.emission_enabled = true
	_ball_mat.emission = Color(1, 1, 1)
	_ball_mat.emission_energy_multiplier = 0.0
	_ball.material_override = _ball_mat
	add_child(_ball)
	_ball_light = OmniLight3D.new()
	_ball_light.omni_range = 0.9
	_ball_light.light_energy = 0.0
	_ball_light.shadow_enabled = false
	add_child(_ball_light)
	_trail = MeshInstance3D.new()
	_trail.mesh = ImmediateMesh.new()
	_trail_mat = StandardMaterial3D.new()
	_trail_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_trail_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_trail_mat.vertex_color_use_as_albedo = true
	_trail_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_trail_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_trail.material_override = _trail_mat
	_trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_trail)
	var ps: PackedScene = load(M + "putter.glb") if ResourceLoader.exists(M + "putter.glb") else null
	if ps:
		_putter = ps.instantiate()
	else:
		_putter = Node3D.new()
		var shaft := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.007
		cm.bottom_radius = 0.007
		cm.height = 0.9
		shaft.mesh = cm
		shaft.position = Vector3(0, 0.45, 0)
		shaft.material_override = Pbr.local("metal", Color(0.9, 0.9, 0.95), 1.0, 0.9)
		_putter.add_child(shaft)
		var head := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.025, 0.03, 0.11)
		head.mesh = bm
		head.position = Vector3(0, 0.015, 0)
		head.material_override = shaft.material_override
		_putter.add_child(head)
	_putter.visible = false
	add_child(_putter)


func _build_guide() -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sm := SphereMesh.new()
	sm.radius = 0.014
	sm.height = 0.028
	sm.radial_segments = 8
	sm.rings = 4
	mm.mesh = sm
	mm.instance_count = GUIDE_DOTS
	_dots = MultiMeshInstance3D.new()
	_dots.multimesh = mm
	_dot_mat = StandardMaterial3D.new()
	_dot_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_dot_mat.vertex_color_use_as_albedo = true
	_dot_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_dots.material_override = _dot_mat
	_dots.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_dots)


func _on_game(e: LinksEngine) -> void:
	e.event.connect(_on_event)
	_show_hole(e.hole_i, true)


## Builds hole i and its garden; the evening moves on to its hour (at once for the round's first hole).
func _show_hole(i: int, snap_time := false) -> void:
	course.build(game.holes[i])
	garden.dress(course, i)
	var n := maxi(1, game.holes.size() - 1)
	garden.set_time(float(i) / n, snap_time)
	_intro_t = 0.0
	_cam_snap = true
	_trail_pts.clear()


func _col() -> Color:
	var e := game.engine
	if e == null:
		return Color.WHITE
	return e.player()["color"]


# --- events ---

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hole":
			_show_hole(d["index"])
		"tee", "replace":
			_trail_pts.clear()
			var p := e.ball.world(P.R)
			fx.burst(p, _col().lerp(Color.WHITE, 0.4), 16, 0.8, 0.5, 0.04, 1.0, -1.0, 1.0, "glow")
			fx.ring(Vector3(p.x, p.y - P.R + 0.004, p.z), _col(), 0.35, 0.6)
			_cam_snap = kind == "tee"
		"shot":
			_putter_swing = 1.0
			_putter_angle = d["angle"]
			_trail_pts.clear()
			_shake = maxf(_shake, float(d["power"]) * 0.12)
		"bank", "blade", "mover", "spinner":
			var sp: float = d["speed"]
			_squash = maxf(_squash, clampf(sp / 3.0, 0.0, 0.6))
			if sp > 0.6:
				var p2: Vector2 = d["pos"]
				var at := Vector3(p2.x, e.ball.z + P.R, p2.y)
				fx.burst(at, Color(1.0, 0.9, 0.7), int(4 + sp * 3), 0.8 + sp * 0.3, 0.35, 0.03, 1.0, -3.0, 1.0, "glow")
		"bumper":
			var bp: Vector2 = d["pos"]
			var at2 := Vector3(bp.x, e.hole.height(bp) + 0.12, bp.y)
			fx.burst(at2, Color(1.0, 0.5, 0.35), 26, 2.2, 0.45, 0.05, 1.0, -2.0, 1.0, "glow")
			fx.ring(Vector3(bp.x, e.hole.height(bp) + 0.01, bp.y), Color(1.0, 0.6, 0.4), 0.6, 0.35)
			fx.flash(at2, Color(1.0, 0.5, 0.35), 1.6)
			_squash = 0.6
			_shake = maxf(_shake, 0.15)
		"land":
			var lp: Vector2 = d["pos"]
			var s2: float = d["speed"]
			var ground := Vector3(lp.x, e.hole.height(lp) + 0.01, lp.y)
			fx.burst(ground, Color(0.7, 0.9, 0.6), int(6 + s2 * 4), 0.6 + s2 * 0.2, 0.4, 0.03, 0.0, -3.0, 1.0, "soft")
			fx.ring(ground, Color(0.8, 1.0, 0.7, 0.6), 0.4, 0.4)
			_squash = maxf(_squash, clampf(s2 / 3.0, 0.2, 0.7))
			_shake = maxf(_shake, clampf(s2 * 0.05, 0.0, 0.2))
		"sink":
			_sink_t = 0.0
			var cp := Vector3(e.hole.cup.x, e.hole.cup_h + 0.02, e.hole.cup.y)
			fx.burst(cp, Color(0.7, 0.55, 0.28), 22, 1.4, 0.8, 0.03, 1.0, -1.5, 1.0, "glow")
			fx.ring(cp, Color(1.0, 0.85, 0.5), 0.8, 0.7)
			fx.flash(cp + Vector3(0, 0.4, 0), Color(1.0, 0.8, 0.5), 1.2)
		"holed":
			var cp2 := Vector3(e.hole.cup.x, e.hole.cup_h + 0.05, e.hole.cup.y)
			var over: int = int(d["strokes"]) - int(d["par"])
			if d["strokes"] == 1:
				fx.confetti(cp2, 120, 1.2)
				for k in 6:
					var a := TAU * k / 6.0
					fx.firework(cp2 + Vector3(cos(a) * 3.0, -0.5, sin(a) * 3.0), randf_range(4.0, 6.5), randf_range(1.0, 1.6),
						Vector3(randf_range(-0.6, 0.6), 0, randf_range(-0.6, 0.6)))
				_shake = 0.35
			elif over < 0:
				fx.confetti(cp2, 60, 0.8)
				fx.firework(cp2 + Vector3(2.5, -0.5, -2.0), 5.0, 1.2)
			elif over == 0:
				fx.confetti(cp2, 24, 0.5)
		"lip":
			var cp3 := Vector3(e.hole.cup.x, e.hole.cup_h + 0.02, e.hole.cup.y)
			fx.burst(cp3, Color(1.0, 0.9, 0.7), 10, 0.8, 0.3, 0.03, 1.0, -2.0, 1.0, "glow")
		"splash":
			var wp: Vector2 = d["pos"]
			var wl := e.hole.height(wp) - C.WATER
			var at3 := Vector3(wp.x, wl, wp.y)
			_lost_at = at3
			fx.burst(at3, Color(0.8, 0.9, 1.0), 40, 1.8, 0.7, 0.05, 0.0, -6.0, 1.0, "soft")
			fx.ring(at3 + Vector3(0, 0.005, 0), Color(0.7, 0.9, 1.0, 0.8), 0.9, 0.9)
			course.water_mat.set_shader_parameter("splash_pos", at3)
			_splash_t = 0.0
		"fall":
			var fp: Vector2 = d["pos"]
			_lost_at = Vector3(fp.x, C.RAVINE, fp.y)
		"pipe_in", "pipe_out":
			var pp: Vector2 = d["pos"]
			var at4 := Vector3(pp.x, e.hole.height(pp) + 0.03, pp.y)
			fx.burst(at4, Color(0.5, 0.9, 1.0), 18, 1.2, 0.45, 0.04, 1.0, -2.0, 1.0, "glow")
			fx.ring(at4, Color(0.5, 0.9, 1.0), 0.5, 0.4)
		"loop_in":
			_loop_base = e.hole.height(d["pos"])
		"boost":
			var bo: Vector2 = d["pos"]
			fx.burst(Vector3(bo.x, e.hole.height(bo) + 0.03, bo.y), Color(1.0, 0.6, 0.2), 12, 1.0, 0.35, 0.04, 1.0, 0.0, 1.0, "glow")
		"takeoff":
			_squash = 0.3


# --- per frame ---

func _process(delta: float) -> void:
	_time += delta
	_intro_t += delta
	var e := game.engine
	var clock := e.clock if e else _time
	var bpos := _ball_pos()
	var near := e != null and bpos.distance_to(Vector3(e.hole.cup.x, e.hole.cup_h, e.hole.cup.y)) < 0.9
	course.update(clock, delta, near)
	_update_ball(delta, bpos)
	_update_guide()
	_update_putter(delta, bpos)
	_splash_t += delta
	course.water_mat.set_shader_parameter("splash_t", _splash_t)
	_shake = maxf(0.0, _shake - delta * 1.5)
	_place_camera(delta, bpos)


## The ball's centre in the world, following the loop's track and the glass pipe when it is in them.
func _ball_pos() -> Vector3:
	var e := game.engine
	if e == null:
		var h := game.holes[0]
		return Vector3(h.tee.x, h.height(h.tee) + P.R, h.tee.y)
	var b := e.ball
	match b.mode:
		B.Mode.LOOP:
			var d: Dictionary = b.data
			return C.loop_ball(d["g"], d["theta"], float(d["base"]))
		B.Mode.PIPE:
			var d2: Dictionary = b.data
			var path := course.pipe_path(d2["g"])
			var dur: float = 0.35 + float(d2["len"]) / P.PIPE_SPEED
			var f := clampf(b.t / dur, 0.0, 1.0) * (path.size() - 1)
			var k := mini(int(f), path.size() - 2)
			return path[k].lerp(path[k + 1], f - k)
		B.Mode.SUNK:
			var cup := Vector3(e.hole.cup.x, e.hole.cup_h, e.hole.cup.y)
			var drop := minf(b.t * 3.0, 1.0)
			return cup + Vector3(0, P.R - drop * 0.1, 0)
		B.Mode.LOST:
			if e.hole.kind_at(b.pos) == H.WATER:
				return _lost_at - Vector3(0, minf(b.t * 0.3, 0.2), 0)
	return b.world(P.R)


func _update_ball(delta: float, p: Vector3) -> void:
	var e := game.engine
	var col := _col()
	var showing := e != null and e.phase not in [E.Phase.CARD, E.Phase.FINAL, E.Phase.INTRO] \
		and not (e.phase == E.Phase.PICKUP and e.phase_t > 0.3) and not (e.ball.mode == B.Mode.PIPE)
	if e == null:
		showing = true
	_ball.visible = showing
	var moved := p - _prev_ball
	_prev_ball = p
	if showing and moved.length() > 1e-5 and moved.length() < 1.0:
		# roll: about the axis across the motion, by distance over radius
		var flat := Vector3(moved.x, 0, moved.z)
		if flat.length() > 1e-5:
			var axis := Vector3.UP.cross(flat.normalized())
			_ball.transform.basis = Basis(axis, flat.length() / P.R) * _ball.transform.basis
			_ball.transform.basis = _ball.transform.basis.orthonormalized()
	_squash = maxf(0.0, _squash - delta * 4.0)
	var sq := 1.0 - _squash * 0.25
	_ball.position = p
	_ball.scale = Vector3(1.0 + (1.0 - sq) * 0.5, sq, 1.0 + (1.0 - sq) * 0.5)
	var lamp := garden.lamp_level()
	_ball_mat.emission = col.lerp(Color.WHITE, 0.5)
	_ball_mat.emission_energy_multiplier = maxf(0.0, lamp - 0.3) * 0.3
	_ball_light.visible = showing
	_ball_light.position = p + Vector3(0, 0.08, 0)
	_ball_light.light_color = col.lerp(Color.WHITE, 0.3)
	_ball_light.light_energy = maxf(0.0, lamp - 0.3) * 0.45
	# the trail: recent positions while the ball moves fast
	var speed := moved.length() / maxf(delta, 1e-4)
	if showing and speed > 0.4:
		_trail_pts.append(p)
	elif not _trail_pts.is_empty():
		for k in mini(3, _trail_pts.size()):
			_trail_pts.pop_front()
	while _trail_pts.size() > TRAIL:
		_trail_pts.pop_front()
	var im := _trail.mesh as ImmediateMesh
	im.clear_surfaces()
	if _trail_pts.size() >= 2:
		var cam_fwd := -camera.global_transform.basis.z
		im.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
		for i in _trail_pts.size():
			var q := _trail_pts[i]
			var nxt := _trail_pts[mini(i + 1, _trail_pts.size() - 1)]
			var prv := _trail_pts[maxi(i - 1, 0)]
			var dirv := (nxt - prv)
			if dirv.length() < 1e-5:
				dirv = Vector3.RIGHT
			var side := dirv.cross(cam_fwd).normalized()
			var f := float(i) / (_trail_pts.size() - 1)
			var wdt := P.R * 0.45 * f
			var c := Color(col.r, col.g, col.b, f * f * (0.1 + lamp * 0.2))
			im.surface_set_color(c)
			im.surface_add_vertex(q + side * wdt)
			im.surface_set_color(c)
			im.surface_add_vertex(q - side * wdt)
		im.surface_end()


## The guide: dots along where the shot would go, until its first contact and a short way after.
func _update_guide() -> void:
	var e := game.engine
	var show := e != null and e.phase == E.Phase.AIM and not game.cpu_thinking
	_dots.visible = show
	if not show:
		_guide_key = ""
		return
	var power := game.aim_power if game.charging else 0.45
	var key := "%.3f|%.2f|%.2f|%.1f" % [game.aim_angle, power, e.ball.pos.x + e.ball.pos.y, e.clock if e.hole.moving() else 0.0]
	if key != _guide_key:
		_guide_key = key
		_guide = _trace(e, game.aim_angle, power)
	var mm := _dots.multimesh
	var col := _col()
	var n := _guide.size()
	for i in GUIDE_DOTS:
		if i < n:
			var f := float(i) / GUIDE_DOTS
			var s := 1.0 - f * 0.6
			mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * s), _guide[i] - Vector3(0, P.R * 0.6, 0)))
			var pulse := 0.75 + 0.25 * sin(_time * 6.0 - i * 0.5)
			mm.set_instance_color(i, Color(col.r, col.g, col.b, (1.0 - f) * pulse))
		else:
			mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))


func _trace(e: LinksEngine, angle: float, power: float) -> PackedVector3Array:
	var b := e.ball.copy()
	b.vel = Vector2.from_angle(angle) * maxf(power, 0.12) * P.MAX_SPEED
	b.at_rest = false
	var out := PackedVector3Array()
	var ev: Array = []
	var last := b.world(P.R)
	var travelled := 0.0
	var after := -1.0
	var spacing := 0.11
	var acc := 0.0
	for i in 400:
		P.tick(e.hole, b, e.clock + i * P.TICK, ev)
		var p := b.world(P.R)
		var step := p.distance_to(last)
		travelled += step
		acc += step
		last = p
		if acc >= spacing:
			acc = 0.0
			out.append(p)
		if after < 0.0 and b.hits > 0:
			after = travelled
		if b.mode != B.Mode.ROLL and b.mode != B.Mode.AIR:
			break
		if b.at_rest or out.size() >= GUIDE_DOTS or travelled > 3.2:
			break
		if after >= 0.0 and travelled - after > 0.45:
			break
	return out


func _update_putter(delta: float, bpos: Vector3) -> void:
	var e := game.engine
	var aiming := e != null and e.phase == E.Phase.AIM
	if _putter_swing > 0.0:
		_putter_swing = maxf(0.0, _putter_swing - delta * 2.5)
	_putter.visible = (aiming or _putter_swing > 0.0) and e != null
	if not _putter.visible:
		return
	var ang := game.aim_angle if aiming else _putter_angle
	var dir := Vector3(cos(ang), 0, sin(ang))
	var back: float
	if aiming:
		back = 0.06 + (game.aim_power if game.charging else 0.0) * 0.32
	else:
		# the follow-through: from behind the ball to past where it was
		var k := 1.0 - _putter_swing
		back = lerpf(0.06, -0.3, smoothstep(0.0, 0.35, k))
	var base := bpos - Vector3(0, P.R, 0)
	var at := base - dir * (back + P.R + 0.02)
	_putter.position = at
	# the head's face (its +X) faces along the shot; the shaft leans back over the golfer's hands
	_putter.basis = Basis(Vector3.UP, -ang)
	var fade := 1.0 if aiming else clampf(_putter_swing * 3.0, 0.0, 1.0)
	_putter.scale = Vector3.ONE * 0.78 * (0.6 + 0.4 * fade)


# --- the camera ---

func _place_camera(delta: float, bpos: Vector3) -> void:
	var e := game.engine
	var h := course.hole
	var size := maxf(h.w, h.h) * H.CELL
	var centre := Vector3(h.w * H.CELL * 0.5, 0.0, h.h * H.CELL * 0.5)
	var pos: Vector3
	var look: Vector3
	var rate := 2.5
	var phase := e.phase if e else E.Phase.INTRO
	if e == null or game.setup:
		var a := _time * 0.08
		pos = centre + Vector3(cos(a) * size * 0.9, size * 0.55 + 1.2, sin(a) * size * 0.9)
		look = centre
		rate = 1.0
	elif game.overview and phase == E.Phase.AIM:
		pos = centre + Vector3(0, size * 0.95 + 1.0, size * 0.55)
		look = centre
		rate = 4.0
	else:
		match phase:
			E.Phase.INTRO:
				# a sweep over the hole from the cup's side round to the tee
				var k := clampf(_intro_t / E.INTRO_T, 0.0, 1.0)
				var tee := Vector3(h.tee.x, 0, h.tee.y)
				var cup := Vector3(h.cup.x, 0, h.cup.y)
				var a0 := atan2(cup.z - centre.z, cup.x - centre.x)
				var a1 := atan2(tee.z - centre.z, tee.x - centre.x)
				var a := lerp_angle(a0 + 0.6, a1, smoothstep(0.0, 1.0, k))
				var r := size * lerpf(0.95, 0.75, k) + 1.5
				pos = centre + Vector3(cos(a) * r, lerpf(size * 0.6 + 2.0, size * 0.4 + 1.2, k), sin(a) * r)
				look = centre.lerp(cup, 0.3 * (1.0 - k))
				rate = 3.0 if not _cam_snap else 100.0
			E.Phase.TEE, E.Phase.AIM:
				var dir := Vector3(cos(game.aim_angle), 0, sin(game.aim_angle))
				var dist := 2.1 * game.zoom
				pos = bpos - dir * dist + Vector3(0, 0.75 * game.zoom + 0.35, 0)
				look = bpos + dir * (0.9 + game.aim_power * 0.6) - Vector3(0, 0.05, 0)
				rate = 6.0 if not _cam_snap else 100.0
				_chase_dir = dir
			E.Phase.ROLL:
				var v := Vector3(e.ball.vel.x, 0, e.ball.vel.y)
				if v.length() > 0.3:
					_chase_dir = _chase_dir.lerp(v.normalized(), 1.0 - exp(-delta * 1.2)).normalized()
				var dist2 := 2.4 * game.zoom + minf(v.length(), 4.0) * 0.25
				pos = bpos - _chase_dir * dist2 + Vector3(0, 1.0 * game.zoom + 0.35, 0)
				look = bpos + _chase_dir * 0.6 + Vector3(0, -0.05, 0)
				rate = 3.0
			E.Phase.SUNK:
				var cup2 := Vector3(h.cup.x, h.cup_h, h.cup.y)
				var a2 := atan2(_cam_pos.z - cup2.z, _cam_pos.x - cup2.x) + delta * 0.25
				pos = cup2 + Vector3(cos(a2) * 1.0, 0.85, sin(a2) * 1.0)
				look = cup2 + Vector3(0, 0.05, 0)
				rate = 2.0
			E.Phase.LOST, E.Phase.PICKUP:
				pos = _cam_pos
				look = bpos
				rate = 1.5
			_:
				var a3 := _time * 0.1
				pos = centre + Vector3(cos(a3) * size * 0.85, size * 0.6 + 1.4, sin(a3) * size * 0.85)
				look = centre
				rate = 1.5
	# inside the lantern posts round the course, and never under the felt
	var inner := Rect2(0, 0, h.w * H.CELL, h.h * H.CELL).grow(0.9)
	if phase != E.Phase.INTRO and phase != E.Phase.CARD and phase != E.Phase.FINAL and e != null and not game.setup:
		pos.x = clampf(pos.x, inner.position.x, inner.end.x)
		pos.z = clampf(pos.z, inner.position.y, inner.end.y)
	# over the windmill, never through it
	for g in h.gadgets:
		if g["type"] == "windmill":
			var d := Vector2(pos.x, pos.z).distance_to(g["hub"])
			if d < 2.0:
				pos.y = maxf(pos.y, lerpf(3.1, pos.y, smoothstep(0.6, 2.0, d)))
	var ground := -10.0
	var p2 := Vector2(pos.x, pos.z)
	if h.index(p2) >= 0 and not h.solid_at(p2):
		ground = h.height(p2)
	pos.y = maxf(pos.y, ground + 0.25)
	var k2 := 1.0 if _cam_snap else 1.0 - exp(-delta * rate)
	_cam_snap = false
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), sin(_time * 37.0)) * _shake * _shake * (0.12 if Settings.camera_shake else 0.0)
	camera.position = _cam_pos + j
	if camera.position.distance_to(_cam_look) > 0.01:
		camera.look_at(_cam_look, Vector3.UP)
