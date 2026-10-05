extends Node3D
## Shows a Biosurge cavern (user argument --theme=N, 0-4) built from a sample wall profile (narrowings, an S-bend,
## islands, a near-closing squeeze) and scrolls slowly through it with the game's framing (camera at y 26, tilted
## 15 degrees towards -Z, fov 40), with a stand-in ship and shots to judge readability.
## tools/capture.sh -s res://games/biosurge/view3d/world_preview.tscn -r 1280x720  (CAPTURE_ARGS="--theme=3")
## --z=Z starts the camera at z = Z (e.g. -60 for the first narrowing, -215 for the islands); --speed=S (m/s,
## default 3); --flash pops flash() on the walls every second; --stats reports (as warnings, so capture.sh shows
## them) draw calls, primitives and GPU time once a second; --hide=<prefix>,... hides chunk children by name.

const LENGTH := 360

var _world: BioWorld
var _cam: Camera3D
var _ship: Node3D
var _z := 0.0
var _speed := 3.0
var _t := 0.0
var _stats := false
var _flash := false
var _frames := 0
var _hide: PackedStringArray = []
var _left := PackedFloat32Array()
var _right := PackedFloat32Array()
var _shots: Array[MeshInstance3D] = []


func _ready() -> void:
	var theme := 0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--theme="):
			theme = arg.trim_prefix("--theme=").to_int()
		elif arg.begins_with("--z="):
			_z = arg.trim_prefix("--z=").to_float()
		elif arg.begins_with("--speed="):
			_speed = arg.trim_prefix("--speed=").to_float()
		elif arg == "--stats":
			_stats = true
		elif arg == "--flash":
			_flash = true
		elif arg.begins_with("--hide="):
			_hide = arg.trim_prefix("--hide=").split(",")
	var islands := _profile()
	_world = BioWorld.new()
	add_child(_world)
	_world.build(theme, _left, _right, islands, LENGTH)
	var d := _world.environment_for(theme)
	var we := WorldEnvironment.new()
	we.environment = BioWorld.make_environment(d)
	add_child(we)
	var sun := DirectionalLight3D.new()
	BioWorld.setup_sun(sun, d)
	add_child(sun)
	_cam = Camera3D.new()
	_cam.fov = 40.0
	_cam.near = 1.0
	_cam.far = 120.0
	_cam.rotation_degrees = Vector3(-75.0, 0.0, 0.0)
	add_child(_cam)
	_cam.current = true
	_mock_ship()
	_apply_hide()
	_place_camera()


## A sample profile: a wide start, a narrowing, an S-bend, two islands, a near-closing squeeze.
func _profile() -> Array:
	var noise := FastNoiseLite.new()
	noise.seed = 5
	noise.frequency = 0.05
	_left.resize(LENGTH + 1)
	_right.resize(LENGTH + 1)
	for i in LENGTH + 1:
		var z := float(i)
		var c := 8.0
		var half := 7.0
		half -= 3.6 * _bump(z, 70.0, 14.0)            # the first narrowing
		c += 3.5 * sin(clampf((z - 120.0) / 60.0, 0.0, 1.0) * TAU) # an S-bend 120..180
		half -= 1.5 * _bump(z, 150.0, 30.0)
		half += 1.0 * _bump(z, 225.0, 20.0)           # wide round the islands
		half -= 5.2 * _bump(z, 300.0, 10.0)           # nearly closing
		c -= 2.0 * _bump(z, 300.0, 16.0)
		half += noise.get_noise_1d(z) * 0.8
		_left[i] = clampf(c - half + noise.get_noise_1d(z + 500.0) * 0.6, 0.0, 15.0)
		_right[i] = clampf(c + half + noise.get_noise_1d(z + 900.0) * 0.6, _left[i] + 1.5, 16.0)
	return [Rect2(6.0, 212.0, 4.0, 10.0), Rect2(3.0, 238.0, 2.5, 3.0), Rect2(11.0, 240.0, 3.0, 5.0)]


func _bump(z: float, at: float, w: float) -> float:
	return exp(-pow((z - at) / w, 2.0))


func _mock_ship() -> void:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("#e8eef8")
	m.metallic = 0.6
	m.roughness = 0.3
	var e := StandardMaterial3D.new()
	e.albedo_color = Color("#60d8ff")
	e.emission_enabled = true
	e.emission = Color("#60d8ff")
	e.emission_energy_multiplier = 3.0
	_ship = Node3D.new()
	add_child(_ship)
	var body := MeshInstance3D.new()
	var pm := PrismMesh.new()
	pm.size = Vector3(1.2, 1.6, 0.35)
	body.mesh = pm
	body.material_override = m
	body.rotation_degrees = Vector3(-90, 0, 0)
	_ship.add_child(body)
	var jet := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.18
	sm.height = 0.36
	jet.mesh = sm
	jet.material_override = e
	jet.position = Vector3(0, 0, 0.85)
	_ship.add_child(jet)
	var s := StandardMaterial3D.new()
	s.albedo_color = Color("#fff4a0")
	s.emission_enabled = true
	s.emission = Color("#ffe060")
	s.emission_energy_multiplier = 4.0
	for i in 6:
		var b := MeshInstance3D.new()
		var cm := CapsuleMesh.new()
		cm.radius = 0.08
		cm.height = 0.5
		b.mesh = cm
		b.material_override = s
		b.rotation_degrees = Vector3(-90, 0, 0)
		add_child(b)
		_shots.append(b)


func _apply_hide() -> void:
	if _hide.is_empty():
		return
	for n in _world.find_children("*", "Node3D", true, false):
		for h in _hide:
			if String(n.name).begins_with(h):
				(n as Node3D).visible = false


func _place_camera() -> void:
	_cam.position = Vector3(8.0, 26.0, _z)
	var sz := _z - 4.5
	var i := clampi(int(-sz), 0, LENGTH)
	var mid := (_left[i] + _right[i]) * 0.5
	_ship.position = Vector3(mid + sin(_t * 0.9) * 1.2, 0.0, sz)
	for j in _shots.size():
		var a := fmod(_t * 3.0 + j / 6.0, 1.0)
		_shots[j].position = _ship.position + Vector3(0.0 if j % 2 == 0 else 0.4, 0.0, -1.0 - a * 14.0)


func _process(delta: float) -> void:
	_t += delta
	_z -= _speed * delta
	_place_camera()
	_world.update(_z, delta)
	if _flash and int(_t) != int(_t - delta):
		var i := clampi(int(-(_z - 8.0)), 0, LENGTH)
		_world.flash(Vector3(_left[i] if int(_t) % 2 == 0 else _right[i], 0.0, _z - 8.0), Color("#ffb060"))
	_frames += 1
	if _stats and _frames % 60 == 0:
		var vp := get_viewport().get_viewport_rid()
		RenderingServer.viewport_set_measure_render_time(vp, true)
		push_warning("world stats: draw calls %d, primitives %d, objects %d, GPU %.2f ms, CPU %.2f ms, video mem %.0f MB" % [
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			RenderingServer.viewport_get_measured_render_time_gpu(vp),
			RenderingServer.viewport_get_measured_render_time_cpu(vp),
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
