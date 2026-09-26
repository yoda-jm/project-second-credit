class_name InkView3D
extends Node3D
## Inkstorm in 3D: a map on a table, seen from above at an angle. The open ground is dark parchment under drifting
## ink; land rises from it as a painted relief when it is claimed, trees, houses and boats growing on it. The line
## being drawn glows gold (fast) or silver-blue (slow), a fuse burns along it, the storm is a knot of ink ribbons,
## sparks run along the gilt edges. Cell (x, y) is centred at world ((x + 0.5) * 0.1 - 6.4, 0, (y + 0.5) * 0.1 - 4.8).

const E = preload("res://games/inkstorm/engine/ink_engine.gd")
const M := "res://games/inkstorm/art/models/"
const CELL := 0.1
const BOARD := Vector2(12.8, 9.6)
const LAND_HEIGHT := 0.42
const WATER := 0.3
## per stage: water, low, mid, high, peak, cliff, props
const LANDS := [
	{"name": "Spring Meadows", "water": Color(0.2, 0.45, 0.66), "low": Color(0.52, 0.72, 0.3), "mid": Color(0.3, 0.55, 0.22),
		"high": Color(0.56, 0.52, 0.42), "peak": Color(0.95, 0.95, 0.92), "cliff": Color(0.45, 0.32, 0.2),
		"props": ["tree_round", "tree_round", "house", "windmill", "bush", "tree_pine", "rock"]},
	{"name": "Autumn Vale", "water": Color(0.2, 0.36, 0.5), "low": Color(0.78, 0.58, 0.25), "mid": Color(0.66, 0.34, 0.16),
		"high": Color(0.5, 0.42, 0.36), "peak": Color(0.9, 0.88, 0.84), "cliff": Color(0.38, 0.26, 0.18),
		"props": ["tree_round", "tree_pine", "house", "tower", "bush", "rock"]},
	{"name": "Sun Dunes", "water": Color(0.15, 0.55, 0.62), "low": Color(0.9, 0.76, 0.46), "mid": Color(0.84, 0.6, 0.34),
		"high": Color(0.7, 0.44, 0.28), "peak": Color(0.95, 0.85, 0.7), "cliff": Color(0.6, 0.38, 0.24),
		"props": ["rock", "rock", "tower", "bush", "house"]},
	{"name": "Winter March", "water": Color(0.3, 0.5, 0.66), "low": Color(0.86, 0.9, 0.94), "mid": Color(0.66, 0.76, 0.8),
		"high": Color(0.5, 0.54, 0.6), "peak": Color(1.0, 1.0, 1.0), "cliff": Color(0.36, 0.38, 0.44),
		"props": ["tree_pine", "tree_pine", "house", "tower", "rock"]},
	{"name": "Ember Isles", "water": Color(0.9, 0.35, 0.1), "low": Color(0.3, 0.26, 0.24), "mid": Color(0.4, 0.3, 0.26),
		"high": Color(0.28, 0.22, 0.2), "peak": Color(0.95, 0.6, 0.3), "cliff": Color(0.2, 0.14, 0.12),
		"props": ["rock", "rock", "tower", "tree_pine"]},
]

@export var game: InkGame

var camera: Camera3D
var _board: MeshInstance3D
var _mat: ShaderMaterial
var _mask: Image
var _mask_tex: ImageTexture
var _at: Image
var _at_tex: ImageTexture
var _height: Image
var _stage_node: Node3D
var _trail_mesh: ImmediateMesh
var _trail_mat: StandardMaterial3D
var _trail_len := -1
var _trail_slow := true
var _fuse: Node3D
var _storm_mesh: ImmediateMesh
var _storm_lights: Array[OmniLight3D] = []
var _marker: Node3D
var _sparks: Array[Node3D] = []
var _props: Array[Dictionary] = []   ## {node, at (claim time), base}
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _land: Dictionary


static func world(c: Vector2, y := 0.0) -> Vector3:
	return Vector3(c.x * CELL - BOARD.x * 0.5, y, c.y * CELL - BOARD.y * 0.5)


func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.05, 0.035, 0.03)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.5, 0.45)
	env.ambient_light_energy = 0.45
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	env.ssao_enabled = true
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -35, 0)
	sun.light_energy = 1.3
	sun.light_color = Color(1.0, 0.93, 0.82)
	sun.shadow_enabled = true
	sun.shadow_blur = 1.2
	sun.directional_shadow_max_distance = 30.0
	add_child(sun)
	var lamp := OmniLight3D.new()  # a warm lamp over the table
	lamp.position = Vector3(-5, 5, -3)
	lamp.light_color = Color(1.0, 0.7, 0.4)
	lamp.light_energy = 1.2
	lamp.omni_range = 14.0
	add_child(lamp)
	camera = Camera3D.new()
	camera.fov = 36
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	_build_table()
	_build_board()
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String, fallback_r := 0.12, fallback_col := Color.WHITE) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = fallback_r
	s.height = fallback_r * 2.0
	var m := StandardMaterial3D.new()
	m.albedo_color = fallback_col
	m.emission_enabled = true
	m.emission = fallback_col
	s.material = m
	mi.mesh = s
	mi.position.y = fallback_r
	n.add_child(mi)
	return n


func _build_table() -> void:
	var table := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(40, 28)
	table.mesh = pm
	table.position.y = -0.35
	table.material_override = Pbr.material("planks", Color(0.3, 0.2, 0.15), 0.25)
	add_child(table)
	if ResourceLoader.exists(M + "frame.glb"):
		add_child(_scene("frame"))
	if ResourceLoader.exists(M + "inkwell.glb"):
		var iw := _scene("inkwell")
		iw.position = Vector3(7.7, -0.35, -3.5)
		add_child(iw)


func _build_board() -> void:
	_board = MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = BOARD
	pm.subdivide_width = 255
	pm.subdivide_depth = 191
	_board.mesh = pm
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://games/inkstorm/shaders/ink_board.gdshader")
	_board.material_override = _mat
	add_child(_board)
	_mask = Image.create(E.W, E.H, false, Image.FORMAT_L8)
	_at = Image.create(E.W, E.H, false, Image.FORMAT_RF)
	_mask_tex = ImageTexture.create_from_image(_mask)
	_at_tex = ImageTexture.create_from_image(_at)
	_mat.set_shader_parameter("mask", _mask_tex)
	_mat.set_shader_parameter("claimed_at", _at_tex)
	var paper := NoiseTexture2D.new()
	paper.seamless = true
	paper.width = 256
	paper.height = 256
	var pn := FastNoiseLite.new()
	pn.frequency = 0.05
	paper.noise = pn
	_mat.set_shader_parameter("paper", paper)
	_mat.set_shader_parameter("land_height", LAND_HEIGHT)
	_mat.set_shader_parameter("water_level", WATER)
	_trail_mesh = ImmediateMesh.new()
	var tm := MeshInstance3D.new()
	tm.mesh = _trail_mesh
	tm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_trail_mat = StandardMaterial3D.new()
	_trail_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_trail_mat.albedo_color = Color(1.0, 0.8, 0.35)
	_trail_mat.emission_enabled = true
	_trail_mat.emission = Color(1.0, 0.7, 0.3)
	_trail_mat.emission_energy_multiplier = 2.5
	tm.material_override = _trail_mat
	add_child(tm)
	_fuse = _scene("spark", 0.08, Color(1.0, 0.5, 0.2))
	var fl := OmniLight3D.new()
	fl.light_color = Color(1.0, 0.55, 0.2)
	fl.light_energy = 1.5
	fl.omni_range = 1.2
	_fuse.add_child(fl)
	_fuse.scale = Vector3.ONE * 0.7
	add_child(_fuse)
	_storm_mesh = ImmediateMesh.new()
	var sm := MeshInstance3D.new()
	sm.mesh = _storm_mesh
	sm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var smat := StandardMaterial3D.new()
	smat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	smat.vertex_color_use_as_albedo = true
	smat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	smat.cull_mode = BaseMaterial3D.CULL_DISABLED
	sm.material_override = smat
	add_child(sm)


func _on_stage(e: InkEngine) -> void:
	e.event.connect(_on_event)
	if _stage_node:
		_stage_node.queue_free()
	_stage_node = Node3D.new()
	add_child(_stage_node)
	_props.clear()
	_sparks.clear()
	_storm_lights.clear()
	_land = LANDS[e.stage % LANDS.size()]
	for k in ["water", "low", "mid", "high", "peak", "cliff"]:
		_mat.set_shader_parameter("col_" + k, _land[k])
	# this land's relief
	var n := FastNoiseLite.new()
	n.seed = 7 + e.stage * 13
	n.frequency = 0.018
	n.fractal_octaves = 4
	_height = Image.create(256, 192, false, Image.FORMAT_RF)
	for y in 192:
		for x in 256:
			var v := 0.44 + n.get_noise_2d(x, y) * 0.62
			_height.set_pixel(x, y, Color(clampf(v, 0.0, 1.0), 0, 0))
	_mat.set_shader_parameter("height_map", ImageTexture.create_from_image(_height))
	_refresh_mask(e)
	_marker = _scene("marker", 0.12, Color(1.0, 0.85, 0.4))
	_stage_node.add_child(_marker)
	var ml := OmniLight3D.new()
	ml.light_color = Color(1.0, 0.8, 0.45)
	ml.light_energy = 1.2
	ml.omni_range = 1.6
	ml.position.y = 0.4
	_marker.add_child(ml)
	_loop_anims(_marker)
	_marker.scale = Vector3.ONE * 1.4
	for s in e.storms:
		var l := OmniLight3D.new()
		l.light_color = Color(0.6, 0.35, 1.0)
		l.light_energy = 1.6
		l.omni_range = 2.2
		_stage_node.add_child(l)
		_storm_lights.append(l)
	_trail_len = -1
	_place_camera()


func _loop_anims(n: Node) -> void:
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap:
		for a in ap.get_animation_list():
			ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR
		var list := ap.get_animation_list()
		if not list.is_empty():
			ap.play(list[0])


func _refresh_mask(e: InkEngine) -> void:
	for y in E.H:
		for x in E.W:
			var i := y * E.W + x
			var claimed := e.grid[i] == E.CLAIMED
			_mask.set_pixel(x, y, Color(1, 1, 1) if claimed else Color(0, 0, 0))
			_at.set_pixel(x, y, Color(e.claim_time[i], 0, 0))
	_mask_tex.update(_mask)
	_at_tex.update(_at)


## Height of the land at a cell once risen (as the shader has it).
func land_y(c: Vector2i, e: InkEngine) -> float:
	if e.at(c) != E.CLAIMED:
		return 0.0
	var t: float = e.claim_time[c.y * E.W + c.x]
	var r := clampf((e.time - t) / 0.9, 0.0, 1.0)
	r = r * r * (3.0 - 2.0 * r)
	var h := _height.get_pixel(clampi(c.x * 2, 0, 255), clampi(c.y * 2, 0, 191)).r
	return r * LAND_HEIGHT * (0.25 + maxf(h, WATER) * 0.9)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"claim":
			_refresh_mask(e)
			_grow(e, d["region"])
			_shake = 0.15 if d["cells"] > 600 else 0.05
		"die":
			_fx.burst(world(Vector2(d["cell"]) + Vector2(0.5, 0.5), 0.2), Color(0.35, 0.15, 0.6), 40, 3.0, 0.9, 0.2, 1.0, -2.0, 1.0, "glow")
			_fx.flash(world(Vector2(d["cell"]) + Vector2(0.5, 0.5), -2.0), Color(0.6, 0.3, 1.0), 3.0)
			_shake = 0.5
		"spark_spawn":
			_fx.burst(world(Vector2(d["cell"]) + Vector2(0.5, 0.5), 0.3), Color(1.0, 0.6, 0.2), 20, 2.0, 0.5, 0.12, 1.0, 0.0, 1.0, "glow")
		"cleared":
			_shake = 0.2


## Trees, houses and boats grow on newly claimed land (a few per claim, in the land's style).
func _grow(e: InkEngine, region: Array) -> void:
	if region.is_empty() or _props.size() > 260:
		return
	var n := clampi(region.size() / 90, 1, 30)
	var rng := RandomNumberGenerator.new()
	rng.seed = region.size() * 7919 + e.stage
	var kinds: Array = _land["props"]
	for i in n:
		var c: Vector2i = region[rng.randi_range(0, region.size() - 1)]
		# keep off the edges
		if e.is_edge(c) or e.is_edge(c + Vector2i(2, 0)) or e.is_edge(c - Vector2i(2, 0)) or e.is_edge(c + Vector2i(0, 2)) or e.is_edge(c - Vector2i(0, 2)):
			continue
		var h := _height.get_pixel(clampi(c.x * 2, 0, 255), clampi(c.y * 2, 0, 191)).r
		var kind: String = "boat" if h < WATER else kinds[rng.randi_range(0, kinds.size() - 1)]
		if h > 0.66 and kind != "boat":
			kind = "rock"
		if kind == "boat" and rng.randf() < 0.6:
			continue
		var p := _scene(kind, 0.06, Color(0.3, 0.5, 0.25))
		p.rotation.y = rng.randf() * TAU
		var s := rng.randf_range(0.8, 1.2)
		p.set_meta("s", s)
		p.scale = Vector3.ONE * 0.001
		_stage_node.add_child(p)
		_loop_anims(p)
		_props.append({"node": p, "cell": c, "at": e.time + rng.randf_range(0.5, 1.2), "s": s})


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _marker == null:
		return
	_mat.set_shader_parameter("now", e.time)
	# the marker
	var mp := world(Vector2(e.pos) + Vector2(0.5, 0.5), land_y(e.pos, e) + 0.02)
	_marker.position = _marker.position.lerp(mp, minf(1.0, delta * 30.0))
	_marker.visible = not (e.phase == E.Phase.DYING and fmod(_time, 0.2) < 0.1)
	# sparks
	while _sparks.size() < e.sparks.size():
		var sp := _scene("spark_super" if e.sparks[_sparks.size()]["super"] else "spark", 0.1, Color(1.0, 0.55, 0.2))
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.55, 0.25)
		l.light_energy = 1.0
		l.omni_range = 1.0
		l.position.y = 0.2
		sp.add_child(l)
		_loop_anims(sp)
		_stage_node.add_child(sp)
		_sparks.append(sp)
	for i in _sparks.size():
		var on := i < e.sparks.size()
		_sparks[i].visible = on
		if on:
			var c: Vector2i = e.sparks[i]["cell"]
			var tp := world(Vector2(c) + Vector2(0.5, 0.5), land_y(c, e) + (0.28 if e.sparks[i]["super"] else 0.2))
			_sparks[i].position = _sparks[i].position.lerp(tp, minf(1.0, delta * 25.0)) if _sparks[i].position.distance_to(tp) < 1.0 else tp
	# the trail and the fuse
	if e.trail.size() != _trail_len or e.trail_slow != _trail_slow:
		_trail_len = e.trail.size()
		_trail_slow = e.trail_slow
		_draw_trail(e)
	_fuse.visible = e.fuse >= 0.0 and e.drawing()
	if _fuse.visible:
		var i := clampi(int(e.fuse), 0, e.trail.size() - 1)
		_fuse.position = world(Vector2(e.trail[i]) + Vector2(0.5, 0.5), 0.15)
	_draw_storms(e)
	# props grow
	for p in _props:
		var k := clampf((e.time - p["at"]) / 0.5, 0.0, 1.0)
		var n: Node3D = p["node"]
		var c: Vector2i = p["cell"]
		n.position = world(Vector2(c) + Vector2(0.5, 0.5), land_y(c, e))
		var ease_ := 1.0 + 0.25 * sin(k * PI) if k < 1.0 else 1.0
		n.scale = Vector3.ONE * maxf(0.001, k * ease_ * p["s"])
	_shake = maxf(0.0, _shake - delta * 1.5)
	_place_camera()


func _draw_trail(e: InkEngine) -> void:
	_trail_mesh.clear_surfaces()
	var col := Color(0.55, 0.8, 1.0) if e.trail_slow else Color(1.0, 0.75, 0.3)
	_trail_mat.albedo_color = col
	_trail_mat.emission = col
	if e.trail.size() < 2:
		return
	_trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var w := 0.035
	for i in e.trail.size() - 1:
		var a := world(Vector2(e.trail[i]) + Vector2(0.5, 0.5), 0.03 + (land_y(e.trail[i], e) if i == 0 else 0.0))
		var b := world(Vector2(e.trail[i + 1]) + Vector2(0.5, 0.5), 0.03)
		var side := (b - a).cross(Vector3.UP).normalized() * w
		var ext := (b - a).normalized() * w
		a -= ext
		b += ext
		for v in [a - side, a + side, b + side, a - side, b + side, b - side]:
			_trail_mesh.surface_add_vertex(v)
	_trail_mesh.surface_end()


## Each storm: six ink ribbons looping round its heart, dark in the middle, violet at the rims.
func _draw_storms(e: InkEngine) -> void:
	_storm_mesh.clear_surfaces()
	if e.storms.is_empty():
		return
	_storm_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for si in e.storms.size():
		var s: Dictionary = e.storms[si]
		var centre := world(s["pos"], 0.0)
		if si < _storm_lights.size():
			_storm_lights[si].position = centre + Vector3(0, 0.6, 0)
		var r := E.STORM_R * CELL * 1.4
		for k in 6:
			var ph := k * 1.047 + si * 0.5
			var prev := Vector3.ZERO
			var steps := 28
			for j in steps + 1:
				var t := float(j) / steps * TAU
				var p := centre + Vector3(sin(t * 2.0 + ph + _time * (1.6 + k * 0.2)) * r * (0.6 + 0.4 * sin(_time * 0.7 + k)),
					0.18 + 0.12 * sin(t * 3.0 + _time * 2.0 + k),
					cos(t * 3.0 + ph * 1.3 + _time * (1.2 + k * 0.15)) * r * (0.6 + 0.4 * cos(_time * 0.9 + k)))
				if j > 0:
					var up := Vector3(0, 0.08 + 0.05 * sin(t * 5.0 + k), 0)
					var ca := Color(0.08, 0.04, 0.14, 0.9)
					var cb := Color(0.7, 0.4, 1.0, 0.85)
					var quad := [[prev - up, ca], [prev + up, cb], [p + up, cb], [prev - up, ca], [p + up, cb], [p - up, ca]]
					for q in quad:
						_storm_mesh.surface_set_color(q[1])
						_storm_mesh.surface_add_vertex(q[0])
				prev = p
	_storm_mesh.surface_end()


func _place_camera() -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(BOARD.y * 0.5 + 0.7, (BOARD.x * 0.5 + 0.9) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var j := Vector3(sin(_time * 50.0), 0, cos(_time * 43.0)) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var target := Vector3(0, 0, 0.35)
	camera.position = target + Vector3(0, 0.86, 0.5).normalized() * dist + j
	camera.look_at(target + j, Vector3.UP)
