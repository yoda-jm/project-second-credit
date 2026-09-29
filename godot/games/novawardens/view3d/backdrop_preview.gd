extends Node3D
## Shows the Nova Wardens night backdrop behind a mock field: the game's camera, the ground line, the cannon, rows of
## glowing invaders, shots and bombs as placeholder shapes, to judge depth and readability.
## tools/capture.sh -s res://games/novawardens/view3d/backdrop_preview.tscn  (CAPTURE_ARGS="--alarm=1 --flash")
## --alarm=<0..1> holds the alarm at that level (--alarm=ramp: it rises from 0 to 1 over 8 s); --flash: a flash every
## 3 s at the mothership's lane, 0.1 s before each whole 3 s (frames 180, 360... catch it); --bare: no placeholders; --hide=<prefix>,...: hides backdrop nodes by name (to time the
## parts); --stats: reports (as warnings, so capture.sh shows them) the draw calls, primitives and GPU time once a second.

var _bd: NovaBackdrop
var _t := 0.0
var _alarm := "0"
var _flash := false
var _stats := false
var _frames := 0
var _invaders: Array = []
var _shots: Array = []


func _ready() -> void:
	var hide: PackedStringArray = []
	var bare := false
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--alarm="):
			_alarm = arg.trim_prefix("--alarm=")
		elif arg == "--flash":
			_flash = true
		elif arg == "--stats":
			_stats = true
		elif arg == "--bare":
			bare = true
		elif arg.begins_with("--hide="):
			hide = arg.trim_prefix("--hide=").split(",")
	_bd = NovaBackdrop.new()
	add_child(_bd)
	_bd.build()
	for n in _bd.find_children("*", "Node3D", true, false):
		for h in hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false
	var d := _bd.environment_for()
	var we := WorldEnvironment.new()
	we.environment = NovaBackdrop.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	NovaBackdrop.setup_sun(sun, d)
	add_child(sun)
	var cam := Camera3D.new()
	cam.fov = 36.0
	cam.far = 4000.0
	# where the game puts its camera when the field is calm (nova_view_3d.gd, _place_camera)
	var look := Vector3(5.6, 6.4, 0.0)
	cam.position = look + Vector3(0.0, -1.2, 5.9 / tan(deg_to_rad(cam.fov * 0.5)))
	add_child(cam)
	cam.look_at(look)
	cam.current = true
	if not bare:
		_add_field()


func _glow_mat(col: Color, e: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.emission_enabled = true
	m.emission = col
	m.emission_energy_multiplier = e
	return m


func _add_field() -> void:
	# the ground line and the cannon
	var line := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(11.2, 0.05, 0.05)
	line.mesh = bm
	line.material_override = _glow_mat(Color("#3cff6a"), 2.5)
	line.position = Vector3(5.6, 1.1, 0)
	add_child(line)
	var cannon := MeshInstance3D.new()
	var cb := BoxMesh.new()
	cb.size = Vector3(0.75, 0.4, 0.4)
	cannon.mesh = cb
	cannon.material_override = _glow_mat(Color("#48ff7a"), 1.6)
	cannon.position = Vector3(4.2, 1.4, 0)
	add_child(cannon)
	# bunkers
	for i in 4:
		var b := MeshInstance3D.new()
		var bb := BoxMesh.new()
		bb.size = Vector3(1.1, 0.8, 0.3)
		b.mesh = bb
		b.material_override = _glow_mat(Color("#2fd05a"), 0.8)
		b.position = Vector3(1.4 + i * 2.8, 2.6, 0)
		add_child(b)
	# the invaders: 5 rows of 11
	var cols := [Color("#ff4df0"), Color("#39e6ff"), Color("#39e6ff"), Color("#ffe84a"), Color("#ffe84a")]
	for r in 5:
		for c in 11:
			var s := MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = 0.28
			sm.height = 0.4
			sm.radial_segments = 16
			sm.rings = 8
			s.mesh = sm
			s.material_override = _glow_mat(cols[r], 2.2)
			var p := Vector3(1.4 + c * 0.84, 10.2 - r * 0.8, 0)
			s.position = p
			add_child(s)
			_invaders.append([s, p])
	# the mothership
	var ms := MeshInstance3D.new()
	var mm := SphereMesh.new()
	mm.radius = 0.5
	mm.height = 0.36
	ms.mesh = mm
	ms.material_override = _glow_mat(Color("#ff3048"), 3.0)
	ms.position = Vector3(8.0, 11.7, 0)
	add_child(ms)
	_invaders.append([ms, ms.position, true])
	# a shot and two bombs
	for k in 3:
		var sh := MeshInstance3D.new()
		var cm := BoxMesh.new()
		cm.size = Vector3(0.06, 0.35, 0.06)
		sh.mesh = cm
		sh.material_override = _glow_mat(Color("#ffffff") if k == 0 else Color("#ff9a3a"), 4.0)
		var p := Vector3([4.2, 3.0, 8.3][k], [5.0, 6.5, 4.2][k], 0)
		sh.position = p
		add_child(sh)
		_shots.append([sh, p, 1.0 if k == 0 else -1.0])


func _process(delta: float) -> void:
	_t += delta
	var dx := fmod(_t * 0.6, 2.0)
	dx = dx if dx < 1.0 else 2.0 - dx
	for inv in _invaders:
		if inv.size() > 2:
			(inv[0] as Node3D).position = inv[1] + Vector3(-fmod(_t * 1.5, 14.0) + 5.0, 0, 0)
		else:
			(inv[0] as Node3D).position = inv[1] + Vector3(dx - 0.5, 0, 0)
	for s in _shots:
		var y: float = fposmod(s[1].y + _t * 3.0 * s[2] - 1.5, 9.0) + 1.5
		(s[0] as Node3D).position = Vector3(s[1].x, y, 0)
	if _alarm == "ramp":
		_bd.alarm(clampf(_t / 8.0, 0.0, 1.0))
	else:
		_bd.alarm(_alarm.to_float())
	if _flash and fmod(_t + 0.1, 3.0) < delta:
		_bd.flash(Vector3(8.0, 11.7, 0))
	_frames += 1
	if _stats and _frames % 60 == 0:
		var vp := get_viewport().get_viewport_rid()
		RenderingServer.viewport_set_measure_render_time(vp, true)
		push_warning("backdrop stats: draw calls %d, primitives %d, objects %d, GPU %.2f ms, CPU %.2f ms" % [
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			RenderingServer.viewport_get_measured_render_time_gpu(vp),
			RenderingServer.viewport_get_measured_render_time_cpu(vp)])
