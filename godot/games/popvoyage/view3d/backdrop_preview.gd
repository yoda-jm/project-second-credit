extends Node3D
## Shows Pop Voyage backdrop N (user argument --theme=N) behind a mock arena: the game's camera framing with a
## gentle drift, a few glossy balloons and the traveller's stand-in, to judge depth and readability.
## tools/capture.sh -s res://games/popvoyage/view3d/backdrop_preview.tscn  (CAPTURE_ARGS="--theme=3")
## --hide=<prefix>,... hides backdrop nodes by name (to time the parts); --stats reports (as warnings, so capture.sh shows them) the draw calls, primitives and GPU time once a second.

var _cam: Camera3D
var _t := 0.0
var _balloons: Array = []
var _stats := false
var _frames := 0


func _ready() -> void:
	var theme := 0
	var hide: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--theme="):
			theme = arg.trim_prefix("--theme=").to_int()
		elif arg == "--stats":
			_stats = true
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	var bd := PopBackdrop.new()
	add_child(bd)
	if theme >= 0:
		bd.build(theme)  # --theme=-1: the same lighting with no backdrop (a baseline for --stats)
	for n in bd.find_children("*", "Node3D", true, false):  # --hide=sky,mid_sea: to time the parts
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := bd.environment_for(maxi(theme, 0))
	var we := WorldEnvironment.new()
	we.environment = PopBackdrop.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	PopBackdrop.setup_sun(sun, d)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 35.0
	_cam.far = 4000.0
	add_child(_cam)
	_cam.current = true
	var cols := [Color("#ff3b4e"), Color("#2f8cff"), Color("#34d96b"), Color("#ffc93a"), Color("#c04dff")]
	var spots := [[4.0, 6.5, 1.3], [12.0, 7.0, 1.3], [8.0, 4.0, 0.8], [2.5, 2.0, 0.45], [14.0, 3.0, 0.45]]
	for i in spots.size():
		var s := MeshInstance3D.new()
		var m := SphereMesh.new()
		m.radius = spots[i][2]
		m.height = spots[i][2] * 2.0
		s.mesh = m
		var mat := StandardMaterial3D.new()
		mat.albedo_color = cols[i]
		mat.roughness = 0.12
		mat.clearcoat_enabled = true
		mat.rim_enabled = true
		mat.rim = 0.3
		s.material_override = mat
		s.position = Vector3(spots[i][0], spots[i][1], 0)
		add_child(s)
		_balloons.append([s, s.position, i])
	var hero := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.35
	cap.height = 1.3
	hero.mesh = cap
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color("#f5f0e0")
	hero.material_override = hm
	hero.position = Vector3(8, 0.65, 0)
	add_child(hero)
	_place()


func _place() -> void:
	_cam.position = Vector3(8.0 + sin(_t * 0.4) * 0.8, 5.0 + sin(_t * 0.27) * 0.3, 22.0)
	_cam.look_at(Vector3(8.0 + sin(_t * 0.4) * 0.3, 5.0, 0.0))
	for b in _balloons:
		var s: MeshInstance3D = b[0]
		var p: Vector3 = b[1]
		s.position = p + Vector3(sin(_t * 0.9 + b[2]) * 0.8, absf(sin(_t * 1.6 + b[2])) * 0.8, 0)


func _process(delta: float) -> void:
	_t += delta
	_place()
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
