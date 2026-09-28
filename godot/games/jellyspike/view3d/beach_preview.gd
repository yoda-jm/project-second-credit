extends Node3D
## Shows the Jelly Spike beach (user argument --variant=N) round a mock court: the game's camera framing with a gentle
## drift, two coloured jelly stand-ins and a ball arcing over the net, to judge depth and readability.
## tools/capture.sh -s res://games/jellyspike/view3d/beach_preview.tscn  (CAPTURE_ARGS="--variant=2")
## --cheer makes the spectators celebrate every 3 s; --stats reports (as warnings, so capture.sh shows them) the draw
## calls, primitives and GPU time once a second; --hide=<prefix>,... hides beach nodes by name (to time the parts).

var _cam: Camera3D
var _t := 0.0
var _beach: SpikeBeach
var _ball: MeshInstance3D
var _blobs: Array = []
var _stats := false
var _cheer := false
var _frames := 0


func _ready() -> void:
	var v := 0
	var hide: PackedStringArray = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--variant="):
			v = arg.trim_prefix("--variant=").to_int()
		elif arg == "--stats":
			_stats = true
		elif arg == "--cheer":
			_cheer = true
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	_beach = SpikeBeach.new()
	add_child(_beach)
	_beach.build(v)
	for n in _beach.find_children("*", "Node3D", true, false):
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := _beach.environment_for(v)
	var we := WorldEnvironment.new()
	we.environment = SpikeBeach.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	SpikeBeach.setup_sun(sun, d)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 36.0
	_cam.far = 4000.0
	add_child(_cam)
	_cam.current = true
	for i in 2:
		var s := MeshInstance3D.new()
		var m := SphereMesh.new()
		m.radius = 0.62
		m.height = 1.24
		s.mesh = m
		var mat := StandardMaterial3D.new()
		mat.albedo_color = [Color("#ff4f9a"), Color("#3fd07a")][i]
		mat.roughness = 0.15
		mat.clearcoat_enabled = true
		mat.rim_enabled = true
		mat.rim = 0.4
		s.material_override = mat
		add_child(s)
		_blobs.append(s)
	_ball = MeshInstance3D.new()
	var bm := SphereMesh.new()
	bm.radius = 0.36
	bm.height = 0.72
	_ball.mesh = bm
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color("#fff4d0")
	bmat.roughness = 0.2
	_ball.material_override = bmat
	add_child(_ball)
	_place()


func _place() -> void:
	# the ball arcs back and forth over the net; the camera follows it up a little
	var ph := fmod(_t / 2.4, 2.0)
	var dir := 1.0 if ph < 1.0 else -1.0
	var k := fmod(ph, 1.0)
	var bx := 3.2 + 9.6 * k if dir > 0.0 else 12.8 - 9.6 * k
	var by := 1.8 + 7.5 * 4.0 * k * (1.0 - k)
	_ball.position = Vector3(bx, by, 0)
	_blobs[0].position = Vector3(3.0 + sin(_t * 0.9) * 1.2, 0.62 + absf(sin(_t * 2.1)) * 0.5, 0)
	_blobs[1].position = Vector3(13.0 + sin(_t * 0.8 + 1.0) * 1.2, 0.62 + absf(sin(_t * 1.9 + 0.5)) * 0.5, 0)
	var rise := maxf(0.0, by - 7.0) * 0.25
	_cam.position = Vector3(8.0 + sin(_t * 0.3) * 0.4, 4.5 + rise, 20.0)
	_cam.look_at(Vector3(8.0, 4.2 + rise, 0.0))


func _process(delta: float) -> void:
	_t += delta
	_place()
	_frames += 1
	if _cheer and _frames % 180 == 60:
		_beach.cheer(0)
	if _stats and _frames % 60 == 0:
		var vp := get_viewport().get_viewport_rid()
		RenderingServer.viewport_set_measure_render_time(vp, true)
		push_warning("beach stats: draw calls %d, primitives %d, objects %d, GPU %.2f ms, CPU %.2f ms, video mem %.0f MB" % [
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			RenderingServer.viewport_get_measured_render_time_gpu(vp),
			RenderingServer.viewport_get_measured_render_time_cpu(vp),
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
