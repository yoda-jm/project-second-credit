extends Node3D
## Shows Fuseflight backdrop N (user argument --theme=N) behind a mock arena: the game's camera framing, the stage's
## platforms (plain dark slabs) and fireworks to collect (glowing spheres) and the hero's stand-in, to judge depth
## and readability.
## tools/capture.sh -s res://games/fuseflight/view3d/backdrop_preview.tscn  (CAPTURE_ARGS="--theme=3")
## --celebrate=S calls celebrate() after S seconds; --flash pops flash() at a firework every second;
## --hide=<prefix>,... hides backdrop nodes by name (to time the parts); --stats reports (as warnings, so capture.sh
## shows them) the draw calls, primitives and GPU time once a second.

const STAGES := "res://games/fuseflight/stages/festival.fuse"

var _cam: Camera3D
var _bd: FuseBackdrop
var _t := 0.0
var _stats := false
var _frames := 0
var _celebrate := -1.0
var _flash := false
var _bombs: Array = []


func _ready() -> void:
	var theme := 0
	var hide: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--theme="):
			theme = arg.trim_prefix("--theme=").to_int()
		elif arg == "--stats":
			_stats = true
		elif arg == "--flash":
			_flash = true
		elif arg.begins_with("--celebrate="):
			_celebrate = arg.trim_prefix("--celebrate=").to_float()
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	_bd = FuseBackdrop.new()
	add_child(_bd)
	if theme >= 0:
		_bd.build(theme)  # --theme=-1: the same lighting with no backdrop (a baseline for --stats)
	for n in _bd.find_children("*", "Node3D", true, false):
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := _bd.environment_for(maxi(theme, 0))
	var we := WorldEnvironment.new()
	we.environment = FuseBackdrop.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	FuseBackdrop.setup_sun(sun, d)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 38.0
	_cam.far = 400.0
	_cam.position = Vector3(8.0, 6.0, 21.0)
	add_child(_cam)
	_cam.look_at(Vector3(8.0, 6.0, 0.0))
	_cam.current = true
	_mock_arena(maxi(theme, 0))


func _mock_arena(theme: int) -> void:
	var stage: FuseStage = null
	var f := FileAccess.open(STAGES, FileAccess.READ)
	if f:
		for s in FuseStage.parse_file(f.get_as_text()):
			if s.theme == theme:
				stage = s
				break
	var slab := StandardMaterial3D.new()
	slab.albedo_color = Color("#3a3440")
	slab.roughness = 0.6
	var edge := StandardMaterial3D.new()
	edge.albedo_color = Color("#ffcf7a")
	edge.emission_enabled = true
	edge.emission = Color("#ffb04a")
	edge.emission_energy_multiplier = 1.5
	var bomb := StandardMaterial3D.new()
	bomb.albedo_color = Color("#d0302a")
	bomb.emission_enabled = true
	bomb.emission = Color("#ff4a2a")
	bomb.emission_energy_multiplier = 2.0
	bomb.roughness = 0.3
	if stage:
		for r in stage.platforms:
			var b := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(r.size.x, r.size.y, 1.2)
			b.mesh = bm
			b.material_override = slab
			b.position = Vector3(r.position.x + r.size.x / 2, r.position.y + r.size.y / 2, 0)
			add_child(b)
			var e := MeshInstance3D.new()
			var em := BoxMesh.new()
			em.size = Vector3(r.size.x, 0.05, 1.22)
			e.mesh = em
			e.material_override = edge
			e.position = Vector3(r.position.x + r.size.x / 2, r.position.y + r.size.y, 0)
			add_child(e)
		for p in stage.bombs:
			var s := MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = 0.3
			sm.height = 0.6
			sm.radial_segments = 16
			sm.rings = 8
			s.mesh = sm
			s.material_override = bomb
			s.position = Vector3(p.x, p.y, 0)
			add_child(s)
			_bombs.append(s.position)
	var hero := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.35
	cap.height = 1.3
	hero.mesh = cap
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color("#3a7cff")
	hero.material_override = hm
	hero.position = Vector3(stage.start.x if stage else 8.0, 0.65, 0)
	add_child(hero)


func _process(delta: float) -> void:
	_t += delta
	if _celebrate >= 0.0 and _t >= _celebrate:
		_celebrate = -1.0
		_bd.celebrate()
	if _flash and not _bombs.is_empty() and int(_t) != int(_t - delta):
		_bd.flash(_bombs[int(_t) % _bombs.size()])
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
