extends Node3D
## Shows Marble Drift backdrop N (user argument --theme=N, 0-5) round a small test course built here with the
## course shaders: platforms, ramps, walls, glass, rough floor, acid, voids and a goal, and a glass marble rolling down
## it with the camera following as the game's does (yaw 45, pitch 48: from +x +z of the marble, looking back up the
## course, which runs down along +z; --pitch=deg and --dist=units change the framing).
## tools/capture.sh -s res://games/marbledrift/view3d/sky_preview.tscn  (CAPTURE_ARGS="--theme=3")
## --hide=<prefix>,... hides backdrop nodes by name (to time the parts); --still keeps the camera at the start; --stats reports draw calls, primitives and GPU time once a second (as
## warnings, so capture.sh shows them); --theme=-1 lights the course with theme 0 but builds no backdrop (a baseline).

const KINDS := ".#_~G=^"
const W := 14
const H := 46
const SLAB := 1.6        ## the course slab's depth under its floor (as in drift_view_3d.gd)
const YAW := 45.0        ## the game's camera: at +x +z of the marble, looking back up the course
const PITCH := 48.0
const DIST := 21.0

var _cells := PackedByteArray()
var _v := PackedFloat32Array()      ## (W + 1) * (H + 1) vertex heights
var _cam: Camera3D
var _marble: MeshInstance3D
var _t := 0.0
var _still := false
var _stats := false
var _frames := 0
var _bare := false
var _pitch := PITCH
var _dist := DIST


func _ready() -> void:
	var theme := 0
	var hide: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--theme="):
			theme = arg.trim_prefix("--theme=").to_int()
		elif arg.begins_with("--pitch="):
			_pitch = arg.trim_prefix("--pitch=").to_float()
		elif arg.begins_with("--dist="):
			_dist = arg.trim_prefix("--dist=").to_float()
		elif arg == "--bare":
			_bare = true
		elif arg == "--still":
			_still = true
		elif arg == "--stats":
			_stats = true
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	_make_course()
	var sky := DriftSky.new()
	sky.name = "sky"
	add_child(sky)
	if theme >= 0:
		sky.build(theme, Vector3(W, 9, H))
	for n in sky.find_children("*", "Node3D", true, false):  # --hide=abyss,clouds: to time the parts
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := sky.environment_for(maxi(theme, 0))
	var we := WorldEnvironment.new()
	we.environment = DriftSky.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	DriftSky.setup_sun(sun, d)
	add_child(sun)
	var mats := sky.course_materials(maxi(theme, 0))
	var course := MeshInstance3D.new()
	course.name = "course"
	course.mesh = _course_mesh()
	course.set_surface_override_material(0, mats[0])
	course.set_surface_override_material(1, mats[1])
	add_child(course)
	course.visible = not _bare   # --bare: no course (to time the rest)
	_marble = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.45
	sm.height = 0.9
	sm.radial_segments = 48
	sm.rings = 24
	_marble.mesh = sm
	var gm := StandardMaterial3D.new()
	gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	gm.albedo_color = Color(0.75, 0.88, 1.0, 0.28)
	gm.roughness = 0.02
	gm.metallic_specular = 1.0
	gm.refraction_enabled = true
	gm.refraction_scale = 0.08
	gm.rim_enabled = true
	gm.rim = 0.6
	gm.clearcoat_enabled = true
	gm.emission_enabled = true
	gm.emission = Color(0.25, 0.4, 0.6)
	gm.emission_energy_multiplier = 0.25
	_marble.material_override = gm
	_marble.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(_marble)
	_cam = Camera3D.new()
	_cam.fov = 40.0
	_cam.near = 0.3
	_cam.far = 3000.0
	add_child(_cam)
	_cam.current = true
	_place()


# --- a little course -------------------------------------------------------------------------------------------

func _kind(x: int, z: int) -> String:
	if x < 0 or z < 0 or x >= W or z >= H:
		return "_"
	return char(_cells[z * W + x])


func _vert(x: int, z: int) -> float:
	return _v[clampi(z, 0, H) * (W + 1) + clampi(x, 0, W)]


func _plat(x0: int, z0: int, x1: int, z1: int, y: float, k := ".") -> void:
	for z in range(z0, z1 + 1):
		for x in range(x0, x1 + 1):
			_cells[z * W + x] = k.unicode_at(0)
	for z in range(z0, z1 + 2):
		for x in range(x0, x1 + 2):
			_v[z * (W + 1) + x] = y


func _ramp(x0: int, z0: int, x1: int, z1: int, ya: float, yb: float, k := ".") -> void:
	for z in range(z0, z1 + 1):
		for x in range(x0, x1 + 1):
			_cells[z * W + x] = k.unicode_at(0)
	for z in range(z0, z1 + 2):
		for x in range(x0, x1 + 2):
			_v[z * (W + 1) + x] = lerpf(ya, yb, float(z - z0) / (z1 + 1 - z0))


func _mark(x: int, z: int, k: String) -> void:
	_cells[z * W + x] = k.unicode_at(0)


func _make_course() -> void:
	_cells.resize(W * H)
	_cells.fill("_".unicode_at(0))
	_v.resize((W + 1) * (H + 1))
	_v.fill(0.0)
	_plat(3, 0, 10, 7, 9.0)
	for z in range(0, 8):
		_mark(3, z, "#")
		_mark(10, z, "#")
	for x in range(5, 9):
		for z in range(3, 6):
			_mark(x, z, "=")
	_ramp(4, 8, 9, 14, 9.0, 6.0)
	_plat(1, 15, 12, 23, 6.0)
	for x in range(1, 13):
		_mark(x, 23, "#")
	_mark(6, 23, ".")
	_mark(7, 23, ".")
	for x in range(2, 5):
		for z in range(17, 21):
			_mark(x, z, "~")
	for x in range(9, 12):
		for z in range(16, 22):
			_mark(x, z, "^")
	_ramp(6, 24, 7, 30, 6.0, 3.0, "=")
	_plat(3, 31, 11, 45, 3.0)
	for x in range(3, 12):
		for z in range(31, 46):
			if (x == 5 or x == 9) and z >= 34 and z <= 38:
				_mark(x, z, "_")
	for x in range(5, 10):
		for z in range(41, 45):
			_mark(x, z, "G")


func _top(x: int, z: int) -> Array:
	var add := 1.5 if _kind(x, z) == "#" else 0.0
	return [_vert(x, z) + add, _vert(x + 1, z) + add, _vert(x, z + 1) + add, _vert(x + 1, z + 1) + add]


## Two surfaces, as the game's view builds them: 0 the tops (UV = x, z; COLOR.r = kind / 6), 1 the sides (UV.x along
## the edge, UV.y = height): a slab SLAB deep under the floor where it meets the void, and the flanks of walls.
func _course_mesh() -> ArrayMesh:
	var top := SurfaceTool.new()
	top.begin(Mesh.PRIMITIVE_TRIANGLES)
	var side := SurfaceTool.new()
	side.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in H:
		for x in W:
			var k := _kind(x, z)
			if k == "_":
				continue
			var lift := 1.5 if k == "#" else 0.0
			var h: Array = _top(x, z)
			var col := Color(KINDS.find(k) / 6.0, 0, 0)
			var p00 := Vector3(x, h[0], z)
			var p10 := Vector3(x + 1, h[1], z)
			var p01 := Vector3(x, h[2], z + 1)
			var p11 := Vector3(x + 1, h[3], z + 1)
			_quad(top, p00, p10, p11, p01, col, true)
			var edges := [[0, -1, p00, p10], [1, 0, p10, p11], [0, 1, p11, p01], [-1, 0, p01, p00]]
			for e in edges:
				var nk := _kind(x + e[0], z + e[1])
				var a: Vector3 = e[2]
				var b: Vector3 = e[3]
				var lo_a := a.y - lift - SLAB
				var lo_b := b.y - lift - SLAB
				if nk == "_":
					pass
				elif k == "#" and nk != "#":
					lo_a = a.y - lift
					lo_b = b.y - lift
				else:
					continue
				_side_quad(side, a, b, lo_a, lo_b, Vector3(e[0], 0, e[1]))
	var mesh := top.commit()
	side.commit(mesh)
	return mesh


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color, up: bool) -> void:
	for tri in [[a, b, c], [a, c, d]]:
		var p0: Vector3 = tri[0]
		var p1: Vector3 = tri[1]
		var p2: Vector3 = tri[2]
		var n := (p2 - p0).cross(p1 - p0)
		if (n.y < 0.0) == up:
			var tmp := p1
			p1 = p2
			p2 = tmp
			n = -n
		n = n.normalized()
		for p in [p0, p1, p2]:
			st.set_normal(n)
			st.set_color(col)
			st.set_uv(Vector2(p.x, p.z))
			st.add_vertex(p)


func _side_quad(st: SurfaceTool, a: Vector3, b: Vector3, lo_a: float, lo_b: float, out: Vector3) -> void:
	var a0 := Vector3(a.x, lo_a, a.z)
	var b0 := Vector3(b.x, lo_b, b.z)
	var len := a.distance_to(b)
	for tri in [[a0, b0, b], [a0, b, a]]:
		var p0: Vector3 = tri[0]
		var p1: Vector3 = tri[1]
		var p2: Vector3 = tri[2]
		var n := (p2 - p0).cross(p1 - p0)
		if n.dot(out) < 0.0:
			var tmp := p1
			p1 = p2
			p2 = tmp
		for p in [p0, p1, p2]:
			st.set_normal(out)
			st.set_uv(Vector2(len if p.is_equal_approx(b) or p.is_equal_approx(b0) else 0.0, p.y))
			st.add_vertex(p)


func _floor_at(x: float, z: float) -> float:
	var cx := clampi(int(floor(x)), 0, W - 1)
	var cz := clampi(int(floor(z)), 0, H - 1)
	var fx := x - cx
	var fz := z - cz
	var a := lerpf(_vert(cx, cz), _vert(cx + 1, cz), fx)
	var b := lerpf(_vert(cx, cz + 1), _vert(cx + 1, cz + 1), fx)
	return lerpf(a, b, fz)


# --- camera and marble -----------------------------------------------------------------------------------------

func _place() -> void:
	var z := 3.0 if _still else fmod(3.0 + _t * 2.2, 42.0)
	var x := 7.0 + sin(z * 0.25) * 1.2
	var y := _floor_at(x, z) + 0.45
	_marble.position = Vector3(x, y, z)
	_marble.rotation = Vector3(z / 0.45, 0, 0)
	var look := Vector3(x, y, z + 2.0)
	var yaw := deg_to_rad(YAW)
	var pitch := deg_to_rad(_pitch)
	_cam.position = look + Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * _dist
	_cam.look_at(look, Vector3.UP)


func _process(delta: float) -> void:
	_t += delta
	_place()
	_frames += 1
	if _stats and _frames % 60 == 0:
		var vp := get_viewport().get_viewport_rid()
		RenderingServer.viewport_set_measure_render_time(vp, true)
		push_warning("sky stats: draw calls %d, primitives %d, objects %d, GPU %.2f ms, CPU %.2f ms" % [
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			RenderingServer.viewport_get_measured_render_time_gpu(vp),
			RenderingServer.viewport_get_measured_render_time_cpu(vp)])
