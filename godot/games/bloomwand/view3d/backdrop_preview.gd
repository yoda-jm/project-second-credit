extends Node3D
## Shows Bloomwand backdrop N (user argument --theme=N) behind a mock level: the game's camera framing, 1 m blocks in
## the theme's style and tint (a floor and a few platforms), ladders, a fairy and two creatures as stand-ins, to judge
## depth, calm and readability.
## tools/capture.sh -s res://games/bloomwand/view3d/backdrop_preview.tscn  (CAPTURE_ARGS="--theme=3")
## --celebrate=S calls celebrate() after S seconds; --flash pops flash() at a block every second; --empty leaves the
## level out; --hide=<prefix>,... hides backdrop nodes by name; --stats reports (as warnings, so capture.sh shows
## them) the draw calls, primitives and GPU time once a second.

const LAYOUT := [
	"....................",
	"....................",
	"..####........####..",
	"....H..........H....",
	"....H..######..H....",
	"....H.....H....H....",
	"#####.....H.....####",
	"..........H.........",
	"....###########.....",
	"....H.........H.....",
	"....H.........H.....",
	"######......########",
	"..H...........H.....",
	"..H...........H.....",
	"####################",
]

var _cam: Camera3D
var _bd: BloomBackdrop
var _t := 0.0
var _stats := false
var _frames := 0
var _celebrate := -1.0
var _flash := false
var _blocks: Array = []


func _ready() -> void:
	var theme := 0
	var empty := false
	var hide: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--theme="):
			theme = arg.trim_prefix("--theme=").to_int()
		elif arg == "--stats":
			_stats = true
		elif arg == "--flash":
			_flash = true
		elif arg == "--empty":
			empty = true
		elif arg.begins_with("--celebrate="):
			_celebrate = arg.trim_prefix("--celebrate=").to_float()
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	_bd = BloomBackdrop.new()
	add_child(_bd)
	if theme >= 0:
		_bd.build(theme)  # --theme=-1: the same lighting with no backdrop (a baseline for --stats)
	for n in _bd.find_children("*", "Node3D", true, false):
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := _bd.environment_for(maxi(theme, 0))
	var we := WorldEnvironment.new()
	we.environment = BloomBackdrop.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	BloomBackdrop.setup_sun(sun, d)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 36.0
	_cam.far = 400.0
	_cam.position = Vector3(10.0, 7.5, 27.0)
	add_child(_cam)
	_cam.look_at(Vector3(10.0, 7.5, 0.0))
	_cam.current = true
	if not empty:
		_mock_level(d)


func _mock_level(d: Dictionary) -> void:
	var tint: Color = d["tint"]
	var block := StandardMaterial3D.new()
	match String(d["blocks"]):
		"wood":
			block.albedo_color = Color("#9a6a40") * tint
			block.roughness = 0.75
		"crystal":
			block.albedo_color = Color("#9ac8f0") * tint
			block.roughness = 0.15
			block.metallic_specular = 0.9
			block.emission_enabled = true
			block.emission = Color("#3a6aa0") * tint
			block.emission_energy_multiplier = 0.4
		_:
			block.albedo_color = Color("#a8a098") * tint
			block.roughness = 0.85
	var ladder := StandardMaterial3D.new()
	ladder.albedo_color = Color("#c89a5a")
	ladder.roughness = 0.7
	var bm := BoxMesh.new()
	bm.size = Vector3(0.96, 0.96, 1.0)
	for row in LAYOUT.size():
		var line: String = LAYOUT[row]
		var y := float(LAYOUT.size() - 1 - row)
		for col in line.length():
			var c := line[col]
			if c == "#":
				var b := MeshInstance3D.new()
				b.mesh = bm
				b.material_override = block
				b.position = Vector3(col + 0.5, y + 0.5, 0)
				add_child(b)
				_blocks.append(b.position)
			elif c == "H":
				for s in [-0.32, 0.32]:
					var rail := MeshInstance3D.new()
					var rm := BoxMesh.new()
					rm.size = Vector3(0.08, 1.0, 0.08)
					rail.mesh = rm
					rail.material_override = ladder
					rail.position = Vector3(col + 0.5 + s, y + 0.5, 0.3)
					add_child(rail)
				for r in 3:
					var rung := MeshInstance3D.new()
					var gm := BoxMesh.new()
					gm.size = Vector3(0.64, 0.06, 0.06)
					rung.mesh = gm
					rung.material_override = ladder
					rung.position = Vector3(col + 0.5, y + 0.17 + r * 0.33, 0.3)
					add_child(rung)
	var fairy := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.3
	cap.height = 0.9
	fairy.mesh = cap
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color("#ff7ab8")
	fm.emission_enabled = true
	fm.emission = Color("#ff4a9a")
	fm.emission_energy_multiplier = 0.4
	fairy.material_override = fm
	fairy.position = Vector3(3.5, 1.45, 0)
	add_child(fairy)
	for p in [Vector3(14.5, 4.4, 0), Vector3(8.5, 7.4, 0)]:
		var m := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.4
		sm.height = 0.8
		m.mesh = sm
		var mm := StandardMaterial3D.new()
		mm.albedo_color = Color("#6ad04a")
		m.material_override = mm
		m.position = p
		add_child(m)


func _process(delta: float) -> void:
	_t += delta
	if _celebrate >= 0.0 and _t >= _celebrate:
		_celebrate = -1.0
		_bd.celebrate()
	if _flash and not _blocks.is_empty() and int(_t) != int(_t - delta):
		_bd.flash(_blocks[(int(_t) * 7) % _blocks.size()])
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
