class_name DriftView3D
extends Node3D
## Marble Drift in 3D: the course is a shiny toy track floating in the sky (the DriftSky backdrop for its theme), built
## from its height field: a chequered top per cell (the surface shader reads the cell's kind from the vertex colour),
## walls rising as blocks, slab sides dropping into the abyss wherever the floor ends, pylons holding it up from
## below, checkpoint gates (a ring on the floor where they count, a beacon either side), an arch across the way into
## the goal. The marble is glass with a glowing swirl inside, rolling
## for real; the steelie is dark steel; hoppers bounce. The camera looks down the course from the classic diagonal,
## follows the marble with a little lead, pulls back at speed, watches a fall go down, and swings round at the goal.

const D = preload("res://games/marbledrift/engine/drift_engine.gd")
const M := "res://games/marbledrift/art/models/"
const SH := "res://games/marbledrift/shaders/"
const SKY := "res://games/marbledrift/view3d/drift_sky.gd"
const SLAB := 1.6            ## how deep the course's slab is under its top
const YAW := deg_to_rad(45.0)
const PITCH := deg_to_rad(48.0)

@export var game: DriftGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _stage: Node3D
var _sky: Node3D
var _marble: Node3D
var _marble_core: Node3D
var _marble_light: OmniLight3D
var _enemy_nodes: Array[Node3D] = []
var _beacons: Array[Node3D] = []
var _gate_rings: Array[MeshInstance3D] = []
var _goal: Node3D
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _orbit := 0.0
var _top_mat: Material
var _side_mat: Material


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.05, 0.06, 0.12)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.5, 0.55, 0.7)
	_env.ambient_light_energy = 0.6
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.7
	_env.ssao_enabled = true
	_env.ssr_enabled = true
	_we = WorldEnvironment.new()
	_we.environment = _env
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-50, -30, 0)
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 40.0
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 40
	camera.far = 4000.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	game.course_started.connect(_on_course)
	if game.engine:
		_on_course(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mat(col: Color, rough := 0.4, metal := 0.0, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	m.metallic = metal
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _shader_mat(name: String, fallback: Color) -> Material:
	if ResourceLoader.exists(SH + name + ".gdshader"):
		var m := ShaderMaterial.new()
		m.shader = load(SH + name + ".gdshader")
		return m
	var f := _mat(fallback, 0.25)
	f.vertex_color_use_as_albedo = false
	return f


func _on_course(e: DriftEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_enemy_nodes.clear()
	_beacons.clear()
	var c := e.course
	# the backdrop and its light
	_sky = null
	var pal := {}
	if ResourceLoader.exists(SKY):
		_sky = (load(SKY) as GDScript).new()
		_stage.add_child(_sky)
		_sky.call("build", c.theme, Vector3(c.w, 12, c.h))  # the scenery frames this course
		var d: Dictionary = _sky.call("environment_for", c.theme)
		_env = _sky.call("make_environment", d)
		_we.environment = _env
		_sky.call("setup_sun", _sun, d)
		pal = _sky.call("palette", c.theme)
	_top_mat = _shader_mat("course_top", Color(0.85, 0.85, 0.9))
	_side_mat = _shader_mat("course_side", Color(0.3, 0.32, 0.4))
	for k in pal:
		if _top_mat is ShaderMaterial:
			(_top_mat as ShaderMaterial).set_shader_parameter(k, pal[k])
		if _side_mat is ShaderMaterial:
			(_side_mat as ShaderMaterial).set_shader_parameter(k, pal[k])
	_build_course(c)
	_build_props(c)
	# the marble: glass, a glowing swirl inside, a little light of its own
	_marble = Node3D.new()
	var glass := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = D.R
	sm.height = D.R * 2.0
	sm.radial_segments = 48
	sm.rings = 24
	glass.mesh = sm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.75, 0.9, 1.0, 0.35)
	gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	gm.roughness = 0.02
	gm.metallic_specular = 1.0
	gm.clearcoat_enabled = true
	gm.clearcoat = 1.0
	gm.rim_enabled = true
	gm.rim = 0.8
	gm.refraction_enabled = true
	gm.refraction_scale = 0.08
	glass.material_override = gm
	_marble.add_child(glass)
	_marble_core = Node3D.new()
	for i in 3:
		var ribbon := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = D.R * 0.35
		tm.outer_radius = D.R * 0.62
		ribbon.mesh = tm
		ribbon.rotation = Vector3(i * 1.05, i * 0.7, 0)
		ribbon.material_override = _mat(Color.from_hsv(0.55 + i * 0.12, 0.8, 1.0), 0.3, 0.0, 1.6)
		ribbon.scale = Vector3(1, 0.35, 1)
		_marble_core.add_child(ribbon)
	_marble.add_child(_marble_core)
	_marble_light = OmniLight3D.new()
	_marble_light.light_color = Color(0.5, 0.85, 1.0)
	_marble_light.light_energy = 0.8
	_marble_light.omni_range = 2.2
	_marble.add_child(_marble_light)
	_stage.add_child(_marble)
	# enemies
	for en in e.enemies:
		var n := _scene(en["kind"])
		if n == null:
			if en["kind"] == "steelie":
				n = MeshInstance3D.new()
				var s2 := SphereMesh.new()
				s2.radius = D.R
				s2.height = D.R * 2.0
				(n as MeshInstance3D).mesh = s2
				(n as MeshInstance3D).material_override = _mat(Color(0.12, 0.12, 0.14), 0.15, 1.0)
			else:
				n = MeshInstance3D.new()
				var cy := CylinderMesh.new()
				cy.top_radius = 0.2
				cy.bottom_radius = 0.25
				cy.height = 0.6
				(n as MeshInstance3D).mesh = cy
				(n as MeshInstance3D).material_override = _mat(Color(1.0, 0.5, 0.2), 0.4, 0.0, 0.4)
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		if ap and ap.has_animation("hop"):
			ap.get_animation("hop").loop_mode = Animation.LOOP_LINEAR
			ap.play("hop")
		_stage.add_child(n)
		_enemy_nodes.append(n)
	_orbit = 0.0
	_place_camera(1.0, true)


## The course mesh: tops (two triangles a cell, the kind in the vertex colour), walls as blocks, slab sides.
func _build_course(c: DriftCourse) -> void:
	var top := SurfaceTool.new()
	top.begin(Mesh.PRIMITIVE_TRIANGLES)
	var side := SurfaceTool.new()
	side.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in c.h:
		for x in c.w:
			var k := c.kind(x, z)
			if k == "_":
				continue
			var lift := 1.5 if k == "#" else 0.0
			var y00 := c.vertex(x, z) + lift
			var y10 := c.vertex(x + 1, z) + lift
			var y01 := c.vertex(x, z + 1) + lift
			var y11 := c.vertex(x + 1, z + 1) + lift
			var col := Color(float(DriftCourse.KINDS.find(k)) / 6.0, 0, 0)
			var a := Vector3(x, y00, z)
			var b := Vector3(x + 1, y10, z)
			var cc := Vector3(x, y01, z + 1)
			var d := Vector3(x + 1, y11, z + 1)
			_quad(top, a, b, d, cc, col, true)
			# sides where the neighbour is void (down through the slab) or lower (a wall's flank)
			var edges := [[Vector2i(0, -1), a, b], [Vector2i(1, 0), b, d], [Vector2i(0, 1), d, cc], [Vector2i(-1, 0), cc, a]]
			for ed in edges:
				var nb: Vector2i = ed[0]
				var nk := c.kind(x + nb.x, z + nb.y)
				var p0: Vector3 = ed[1]
				var p1: Vector3 = ed[2]
				var low0 := p0.y - lift - SLAB
				var low1 := p1.y - lift - SLAB
				if nk == "_":
					pass
				elif k == "#" and nk != "#":
					low0 = p0.y - lift
					low1 = p1.y - lift
				else:
					continue
				_side(side, p0, p1, low0, low1)
	var mesh := ArrayMesh.new()
	top.generate_normals()
	top.commit(mesh)
	side.generate_normals()
	side.commit(mesh)
	mesh.surface_set_material(0, _top_mat)
	mesh.surface_set_material(1, _side_mat)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	_stage.add_child(mi)


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, d: Vector3, c: Vector3, col: Color, uv_xz: bool) -> void:
	for p in [a, b, d, a, d, c]:
		st.set_color(col)
		st.set_uv(Vector2(p.x, p.z) if uv_xz else Vector2.ZERO)
		st.add_vertex(p)


func _side(st: SurfaceTool, p0: Vector3, p1: Vector3, low0: float, low1: float) -> void:
	var q0 := Vector3(p0.x, low0, p0.z)
	var q1 := Vector3(p1.x, low1, p1.z)
	var along := p0.distance_to(p1)
	var pts := [[p0, Vector2(0, p0.y)], [q1, Vector2(along, low1)], [p1, Vector2(along, p1.y)],
		[p0, Vector2(0, p0.y)], [q0, Vector2(0, low0)], [q1, Vector2(along, low1)]]
	for pt in pts:
		st.set_color(Color(0, 0, 0))
		st.set_uv(pt[1])
		st.add_vertex(pt[0])


## Pylons under the course, beacons at the checkpoints, the goal arch.
func _build_props(c: DriftCourse) -> void:
	var placed := {}
	for z in range(2, c.h, 9):
		for x in range(1, c.w, 7):
			var k := c.kind(x, z)
			if k == "_" or k == "#":
				continue
			var key := Vector2i(x / 6, z / 9)
			if placed.has(key):
				continue
			placed[key] = true
			var py := _scene("pylon")
			if py == null:
				py = MeshInstance3D.new()
				var b := BoxMesh.new()
				b.size = Vector3(0.6, 12, 0.6)
				(py as MeshInstance3D).mesh = b
				(py as MeshInstance3D).material_override = _mat(Color(0.25, 0.27, 0.35), 0.4, 0.6)
				py.position.y = -6.0
				var holder := Node3D.new()
				holder.add_child(py)
				py = holder
			py.position = Vector3(x + 0.5, c.height_at(Vector2(x + 0.5, z + 0.5)) - SLAB, z + 0.5)
			_stage.add_child(py)
	# the checkpoints: a glowing ring on the floor shows where the gate counts, a beacon either side of the way
	_gate_rings.clear()
	var gates := c.gates()
	for i in gates:
		var r: Vector2 = c.route[i]
		var before: Vector2 = c.route[i - 1] if i > 0 else c.start
		var dir := (c.route[i + 1] - before).normalized()
		var perp := Vector2(-dir.y, dir.x)
		var gate := Node3D.new()
		gate.position = Vector3(r.x, c.height_at(r), r.y)
		_stage.add_child(gate)
		var ring := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = D.GATE_R - 0.12
		tm.outer_radius = D.GATE_R
		tm.rings = 48
		ring.mesh = tm
		ring.scale = Vector3(1.0, 0.25, 1.0)
		ring.position.y = 0.04
		ring.material_override = _mat(Color(0.45, 0.85, 1.0), 0.3, 0.0, 0.9)
		ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		gate.add_child(ring)
		_gate_rings.append(ring)
		var posts := Node3D.new()
		gate.add_child(posts)
		for sgn in [-1.0, 1.0]:
			var at := Vector2.ZERO
			for dist in [D.GATE_R + 0.2, D.GATE_R - 0.3, 1.0]:
				var q: Vector2 = r + perp * sgn * dist
				var k := c.kind(int(floor(q.x)), int(floor(q.y)))
				if k != "_" and k != "#" and absf(c.height_at(q) - c.height_at(r)) < 0.8:
					at = q
					break
			if at == Vector2.ZERO:
				continue
			var bn := _scene("beacon")
			if bn == null:
				bn = MeshInstance3D.new()
				var cy := CylinderMesh.new()
				cy.top_radius = 0.05
				cy.bottom_radius = 0.08
				cy.height = 1.0
				(bn as MeshInstance3D).mesh = cy
				(bn as MeshInstance3D).material_override = _mat(Color(0.6, 0.8, 1.0), 0.3, 0.0, 0.8)
			bn.position = Vector3(at.x - r.x, c.height_at(at) - c.height_at(r), at.y - r.y)
			posts.add_child(bn)
		_beacons.append(posts)
	# the goal arch stands across the way in, where the route first meets the goal, facing the marble's approach
	var last: Vector2 = c.route[c.route.size() - 1] if not c.route.is_empty() else c.start
	var from: Vector2 = c.route[c.route.size() - 2] if c.route.size() > 1 else c.start
	var gdir := (last - from).normalized()
	var entry := Vector2.INF
	var q := from
	for k in int(from.distance_to(last) / 0.1) + 40:
		if c.kind(int(floor(q.x)), int(floor(q.y))) == "G":
			entry = q
			break
		q += gdir * 0.1
	if entry != Vector2.INF:
		# the goal's width across the way, to size the arch
		var gperp := Vector2(-gdir.y, gdir.x)
		var span := [0.0, 0.0]
		for side in 2:
			var sg := 1.0 if side == 0 else -1.0
			var t := 0.0
			while t < 8.0 and c.kind(int(floor(entry.x + gperp.x * sg * (t + 0.1))), int(floor(entry.y + gperp.y * sg * (t + 0.1)))) == "G":
				t += 0.1
			span[side] = t
		var mid: Vector2 = entry + gperp * (span[0] - span[1]) * 0.5
		var width: float = span[0] + span[1]
		_goal = _scene("goal_arch")
		if _goal == null:
			_goal = MeshInstance3D.new()
			var tm := TorusMesh.new()
			tm.inner_radius = 1.2
			tm.outer_radius = 1.4
			(_goal as MeshInstance3D).mesh = tm
			(_goal as MeshInstance3D).material_override = _mat(Color(1.0, 0.85, 0.3), 0.2, 0.3, 1.5)
			_goal.rotation.x = PI * 0.5
			_goal.position.y = 1.3
		var holder := Node3D.new()
		holder.add_child(_goal)
		holder.position = Vector3(mid.x, c.height_at(mid + gdir * 0.3), mid.y) + Vector3(gdir.x, 0, gdir.y) * 0.3
		holder.rotation.y = atan2(-gdir.x, -gdir.y)   # the arch's front (+Z) towards the coming marble
		var k := maxf(1.0, (width + 0.6) / 3.0)
		holder.scale = Vector3(k, maxf(1.0, k * 0.8), 1.0)
		_stage.add_child(holder)
		var gl := OmniLight3D.new()
		gl.light_color = Color(1.0, 0.85, 0.4)
		gl.light_energy = 2.0
		gl.omni_range = 5.0
		gl.position = Vector3(0, 2.0, 0)
		holder.add_child(gl)
		_goal = holder


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"shatter":
			var p: Vector3 = d["pos"] + Vector3(0, D.R, 0)
			_fx.burst(p, Color(0.7, 0.9, 1.0), 40, 5.0, 1.0, 0.08, 1.0, -12.0, 1.0, "glow")
			_fx.burst(p, Color(1, 1, 1), 16, 3.0, 0.5, 0.12, 1.0, -6.0, 1.0, "glow")
			_fx.flash(p + Vector3(0, -1.0, 1.0), Color(0.7, 0.9, 1.0), 2.5)
			_shake = 0.6
		"acid":
			var p: Vector3 = d["pos"]
			_fx.burst(p, Color(0.5, 1.0, 0.3), 40, 2.0, 1.2, 0.12, 1.0, 2.0, 1.0, "glow")
			_fx.burst(p, Color(0.4, 0.6, 0.3), 20, 1.0, 1.5, 0.3, 0.0, 1.5, 1.0, "smoke")
		"land":
			var p: Vector3 = e.ball["pos"]
			_fx.burst(p, Color(0.8, 0.85, 1.0), 10, 2.0, 0.4, 0.07, 1.0, -4.0, 0.5, "glow")
			_shake = maxf(_shake, clampf(d["drop"] * 0.08, 0.0, 0.3))
		"bump":
			_shake = maxf(_shake, clampf(d["speed"] * 0.02, 0.0, 0.2))
		"knock":
			var p: Vector3 = e.ball["pos"]
			_fx.burst(p + Vector3(0, D.R, 0), Color(1.0, 0.8, 0.4), 14, 3.0, 0.4, 0.07, 1.0, -3.0, 1.0, "glow")
			_shake = maxf(_shake, 0.2)
		"checkpoint":
			var i: int = d["n"] - 1
			if i >= 0 and i < _beacons.size():
				var gate := _beacons[i].get_parent() as Node3D
				_fx.burst(gate.position + Vector3(0, 0.6, 0), Color(0.5, 0.9, 1.0), 30, 2.5, 0.7, 0.08, 1.0, 1.0, 1.0, "glow")
				_gate_rings[i].material_override = _mat(Color(0.5, 1.0, 0.75), 0.3, 0.0, 2.5)
				for bn in _beacons[i].get_children():
					var l := OmniLight3D.new()
					l.light_color = Color(0.5, 1.0, 0.8)
					l.light_energy = 1.5
					l.omni_range = 2.5
					l.position = Vector3(0, 1.2, 0)
					bn.add_child(l)
		"finish":
			var p: Vector3 = e.ball["pos"]
			for i in 6:
				_fx.burst(p + Vector3(randf_range(-2, 2), 2.0 + randf(), randf_range(-2, 2)), Color.from_hsv(i / 6.0, 0.7, 1.0), 30, 4.0, 1.2, 0.1, 1.0, -3.0, 1.0, "glow")
		"respawn":
			var p: Vector3 = e.ball["pos"]
			_fx.burst(p + Vector3(0, 0.5, 0), Color(0.7, 0.9, 1.0), 30, 1.5, 0.8, 0.08, 1.0, 1.0, 1.0, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _marble == null:
		return
	var b: Dictionary = e.ball
	var broken := e.phase == D.Phase.DYING and e.death in ["shatter", "acid"]
	_marble.visible = not broken
	_marble.position = b["pos"] + Vector3(0, D.R, 0)
	# it rolls: turn by the distance covered, about the axis across its motion
	var v: Vector3 = b["vel"]
	var hv := Vector2(v.x, v.z)
	if hv.length() > 0.01:
		var axis := Vector3(hv.y, 0, -hv.x).normalized()
		_marble.rotate(axis, hv.length() * delta / D.R)
	_marble_core.rotation.y += delta * 0.5
	_marble_light.light_energy = 0.6 + 0.4 * clampf(hv.length() / 8.0, 0.0, 1.0)
	# a sparkling trail at speed
	if hv.length() > 7.0 and not b["air"] and fmod(_time, 0.06) < delta:
		_fx.burst(b["pos"] + Vector3(0, 0.05, 0), Color(0.6, 0.85, 1.0), 2, 0.4, 0.4, 0.05, 1.0, 0.0, 1.0, "glow")
	for i in e.enemies.size():
		var en: Dictionary = e.enemies[i]
		var n := _enemy_nodes[i]
		n.visible = en["gone"] <= 0.0
		if en["kind"] == "steelie" and en.has("b"):
			n.position = en["b"]["pos"] + Vector3(0, D.R, 0)
			var sv: Vector3 = en["b"]["vel"]
			var sh := Vector2(sv.x, sv.z)
			if sh.length() > 0.01:
				n.rotate(Vector3(sh.y, 0, -sh.x).normalized(), sh.length() * delta / D.R)
		else:
			var p: Vector2 = en["pos"]
			n.position = Vector3(p.x, e.course.height_at(p), p.y)
	if _goal:
		var banner := _goal.find_child("banner", true, false) as Node3D
		if banner:
			banner.rotation.x = sin(_time * 3.0) * 0.08
	_shake = maxf(0.0, _shake - delta * 1.8)
	if e.phase == D.Phase.FINISHED:
		_orbit += delta * 0.6
	_place_camera(delta)


## The classic diagonal view, following the marble with a little lead along its motion, pulled back at speed, staying
## up to watch a fall, swinging round the goal at the finish.
func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var p: Vector3 = e.ball["pos"]
	var v: Vector3 = e.ball["vel"]
	# look ahead: down the course (+z) and along the marble's motion, so what comes next is in view
	var lead := Vector3(v.x, 0, v.z) * 0.4 + Vector3(0, 0, 2.0)
	var look := p + lead
	if e.ball["air"] or e.phase == D.Phase.DYING:
		# watch the fall from where it left the course
		look.y = maxf(look.y, e.ball.get("fall_from", p.y) - 2.0)
	var dist := 19.0 + clampf(Vector2(v.x, v.z).length() * 0.35, 0.0, 4.0)
	var yaw := YAW + _orbit
	var off := Vector3(sin(yaw) * cos(PITCH), sin(PITCH), cos(yaw) * cos(PITCH)) * dist
	var pos := look + off
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var k := 1.0 if snap else minf(1.0, delta * 4.0)
	_cam_pos = _cam_pos.lerp(pos, k)
	_cam_look = _cam_look.lerp(look, k)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
