extends Node3D
## Shows Ridgefire backdrop N (user argument --theme=N) behind a mock field: the game's camera framing, a flat slab
## of terrain at y = 12 in the theme's colours (--hills: a rolling profile with a deep valley, to see what shows
## where the terrain is low) and two tanks, to judge depth and readability.
## tools/capture.sh -s res://games/ridgefire/view3d/backdrop_preview.tscn  (CAPTURE_ARGS="--theme=3")
## --flash pops flash() over the field every second (--shake also shakes); --hide=<prefix>,... hides backdrop nodes
## by name (to time the parts); --stats reports (as warnings, so capture.sh shows them) the draw calls, primitives
## and GPU time once a second; --wide frames a 21:9 view's width (fov 30); --vis shows the baked sunlight.

var _cam: Camera3D
var _bd: RidgeBackdrop
var _t := 0.0
var _stats := false
var _frames := 0
var _flash := false
var _shake := false


func _ready() -> void:
	var theme := 0
	var hills := false
	var wide := false
	var vis := false
	var hide: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--theme="):
			theme = arg.trim_prefix("--theme=").to_int()
		elif arg == "--stats":
			_stats = true
		elif arg == "--flash":
			_flash = true
		elif arg == "--shake":
			_shake = true
		elif arg == "--hills":
			hills = true
		elif arg == "--wide":
			wide = true
		elif arg == "--vis":
			vis = true
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	_bd = RidgeBackdrop.new()
	add_child(_bd)
	if theme >= 0:
		_bd.build(theme)  # --theme=-1: the same lighting with no backdrop (a baseline for --stats)
	if vis:
		for m in _bd._land_mats:
			(m as ShaderMaterial).set_shader_parameter("debug_vis", true)
	for n in _bd.find_children("*", "Node3D", true, false):
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := _bd.environment_for(maxi(theme, 0))
	var we := WorldEnvironment.new()
	we.environment = RidgeBackdrop.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	RidgeBackdrop.setup_sun(sun, d)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 38.0
	_cam.near = 0.3
	_cam.far = 1400.0
	_cam.position = Vector3(48.0, 26.0, 72.0)
	add_child(_cam)
	_cam.look_at(Vector3(48.0, 18.0, 0.0))
	_cam.current = true
	if wide:
		_cam.fov = 30.0
	_mock_field(d["terrain"], hills)


func _profile(x: float, hills: bool) -> float:
	if not hills:
		return 12.0
	return 14.0 + 7.0 * sin(x * 0.09) + 4.0 * sin(x * 0.23 + 1.0) - 12.0 * exp(-pow((x - 40.0) / 9.0, 2.0))


func _mock_field(tc: Dictionary, hills: bool) -> void:
	var top := StandardMaterial3D.new()
	top.albedo_color = tc["top"]
	top.roughness = 0.9
	var soil := StandardMaterial3D.new()
	soil.albedo_color = tc["soil"]
	soil.roughness = 0.95
	var strata := StandardMaterial3D.new()
	strata.albedo_color = tc["strata"]
	strata.roughness = 0.95
	var deep := StandardMaterial3D.new()
	deep.albedo_color = tc["deep"]
	deep.roughness = 0.95
	var bottom := -8.0
	for i in 96:
		var x := float(i) + 0.5
		var h := _profile(x, hills)
		var bands := [[bottom, h * 0.3, deep], [h * 0.3, h * 0.55, soil], [h * 0.55, h * 0.68, strata],
				[h * 0.68, h - 1.2, soil], [h - 1.2, h, top]]
		for b in bands:
			var y0: float = b[0]
			var y1: float = b[1]
			if y1 <= y0:
				continue
			var mi := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(1.0, y1 - y0, 8.0)
			mi.mesh = bm
			mi.material_override = b[2]
			mi.position = Vector3(x, (y0 + y1) / 2.0, -1.0)
			add_child(mi)
	var tank := StandardMaterial3D.new()
	tank.albedo_color = Color("#3a5a8a")
	tank.metallic = 0.4
	tank.roughness = 0.4
	var tank2 := StandardMaterial3D.new()
	tank2.albedo_color = Color("#a83a2a")
	tank2.metallic = 0.4
	tank2.roughness = 0.4
	for p in [[14.0, tank], [80.0, tank2]]:
		var x: float = p[0]
		var b := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(3.2, 1.2, 2.0)
		b.mesh = bm
		b.material_override = p[1]
		b.position = Vector3(x, _profile(x, hills) + 0.6, 0.0)
		add_child(b)
		var tu := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.15
		cm.bottom_radius = 0.15
		cm.height = 2.4
		tu.mesh = cm
		tu.material_override = p[1]
		tu.position = b.position + Vector3(0.0, 1.0, 0.0)
		tu.rotation_degrees = Vector3(0, 0, -50.0 if x < 48.0 else 50.0)
		add_child(tu)


func _process(delta: float) -> void:
	_t += delta
	if _flash and int(_t) != int(_t - delta):
		var x := 10.0 + fmod(float(int(_t)) * 37.0, 76.0)
		_bd.flash(Vector3(x, _profile(x, false) + 1.0, 0.0), 1.0 + fmod(_t, 3.0))
		if _shake:
			_bd.shake(0.8)
	_frames += 1
	if _stats and _frames % 60 == 0:
		var vp := get_viewport().get_viewport_rid()
		RenderingServer.viewport_set_measure_render_time(vp, true)
		push_warning("backdrop stats: draw calls %d, primitives %d, objects %d, GPU %.2f ms, CPU %.2f ms, video mem %.0f MB" % [
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			RenderingServer.viewport_get_measured_render_time_gpu(vp),
			RenderingServer.viewport_get_measured_render_time_cpu(vp),
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
