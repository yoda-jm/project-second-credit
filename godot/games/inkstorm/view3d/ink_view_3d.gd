class_name InkView3D
extends Node3D
## Inkstorm in 3D: a map on a table, seen from above at an angle. The open ground is dark parchment under drifting
## ink; land rises from it as a painted relief when it is claimed, in a golden wave sweeping out from the line, with
## a bounce, rings of light, sparkles, and trees, houses, boats and flowers popping up. The line being drawn is a
## tube of polished gold (silver-blue when slow) lighting the board, the pen sheds sparks, a fuse burns along it with
## smoke, and a line the storm touches shatters into golden shards. The storm is a knot of ink ribbons lighting the
## parchment violet; sparks run along the gilt edges. A gentle camera leans towards the pen and punches in on claims.
## Cell (x, y) is centred at world ((x + 0.5) * 0.1 - 6.4, 0, (y + 0.5) * 0.1 - 4.8).

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

const GLOW := preload("res://games/inkstorm/shaders/ink_glow.gdshader")
const TUBE_R := 0.058
const GOLD := Color(1.0, 0.74, 0.3)
const SILVER := Color(0.6, 0.8, 1.0)
const VIOLET := Color(0.6, 0.32, 1.0)
const INTERIOR := (E.W - 2) * (E.H - 2)
const MAX_FLOWERS := 1600

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
var _vt := PackedFloat32Array()     ## the view's claim time per cell: later further from the line (the wave)
# the line
var _trail_mesh: ImmediateMesh
var _trail_mat: ShaderMaterial
var _under_mat: ShaderMaterial
var _trail_len := -1
var _trail_slow := true
var _trail_s := PackedFloat32Array()  ## distance along the line at each trail cell
var _trail_pts: Array[Vector3] = []
var _last_trail: Array[Vector2i] = []
var _trail_lights: Array[OmniLight3D] = []
var _break := {}                      ## a line shattering: {c, r, order: [[dist, pos]], next}
# the fuse
var _fuse: Node3D
var _fuse_light: OmniLight3D
var _fuse_sparks: CPUParticles3D
var _fuse_smoke: CPUParticles3D
# the storms and sparks
var _storm_mesh: ImmediateMesh
var _storm_lights: Array[OmniLight3D] = []
var _storm_glows: Array[MeshInstance3D] = []
var _sparks: Array[Node3D] = []
# the pen
var _marker: Node3D
var _marker_light: OmniLight3D
var _halo: MeshInstance3D
var _halo_mat: ShaderMaterial
var _pen_sparks: CPUParticles3D
# growth
var _props: Array[Dictionary] = []   ## {node, cell, at, s}
var _flowers: MultiMesh
var _flower_anim: Array[Dictionary] = []  ## {i, cell, at, s, col}
var _fx: InkFx
var _time := 0.0
var _shake := 0.0
var _land: Dictionary
# the camera
var _lean := Vector3.ZERO
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _punch_tilt := 0.0


static func world(c: Vector2, y := 0.0) -> Vector3:
	return Vector3(c.x * CELL - BOARD.x * 0.5, y, c.y * CELL - BOARD.y * 0.5)


## The land's rise: a damped spring overshooting by about 15% (as in the board shader).
static func spring(s: float) -> float:
	return 0.0 if s <= 0.0 else 1.0 - exp(-6.0 * s) * cos(10.0 * s)


func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.05, 0.035, 0.03)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.5, 0.45)
	env.ambient_light_energy = 0.4
	# a warm room for the gold to reflect (not seen: the background stays the dark table)
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.5, 0.36, 0.22)
	sky_mat.sky_horizon_color = Color(1.0, 0.78, 0.5)
	sky_mat.ground_horizon_color = Color(0.5, 0.34, 0.2)
	sky_mat.ground_bottom_color = Color(0.12, 0.08, 0.06)
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env.sky = sky
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.glow_bloom = 0.06
	env.glow_hdr_threshold = 1.0
	env.ssao_enabled = true
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.08
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()  # low and warm, so the risen land throws long shadows
	sun.rotation_degrees = Vector3(-40, -40, 0)
	sun.light_energy = 1.35
	sun.light_color = Color(1.0, 0.9, 0.76)
	sun.shadow_enabled = true
	sun.shadow_blur = 1.0
	sun.shadow_bias = 0.03
	sun.directional_shadow_max_distance = 32.0
	add_child(sun)
	var lamp := OmniLight3D.new()  # a warm lamp over the table
	lamp.position = Vector3(-5, 5, -3)
	lamp.light_color = Color(1.0, 0.7, 0.4)
	lamp.light_energy = 1.2
	lamp.omni_range = 14.0
	add_child(lamp)
	var rim := DirectionalLight3D.new()  # a cool fill from the far side catches the gilt and the relief's rims
	rim.rotation_degrees = Vector3(-25, 150, 0)
	rim.light_color = Color(0.55, 0.65, 1.0)
	rim.light_energy = 0.35
	rim.light_specular = 0.0
	add_child(rim)
	camera = Camera3D.new()
	camera.fov = 36
	camera.current = true
	add_child(camera)
	_fx = InkFx.new()
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


func _glow_quad(size: float, col: Color, energy: float, mode: int, billboard: bool) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	if not billboard:
		q.orientation = PlaneMesh.FACE_Y
	mi.mesh = q
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := ShaderMaterial.new()
	m.shader = GLOW
	m.set_shader_parameter("color", col)
	m.set_shader_parameter("energy", energy)
	m.set_shader_parameter("mode", mode)
	m.set_shader_parameter("billboard", billboard)
	mi.material_override = m
	return mi


func _particles(kind: String, col: Color, amount: int, life: float, size: float) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = life
	p.local_coords = false
	p.emitting = false
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	p.mesh = q
	p.material_override = Fx.material(kind, col)
	p.scale_amount_curve = Fx.size_curve(kind == "smoke")
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 1))
	fade.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = fade
	return p


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
	# the line: a gold tube and a soft glow laid under it
	_trail_mesh = ImmediateMesh.new()
	var tm := MeshInstance3D.new()
	tm.mesh = _trail_mesh
	tm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_trail_mat = ShaderMaterial.new()
	_trail_mat.shader = load("res://games/inkstorm/shaders/ink_trail.gdshader")
	_under_mat = ShaderMaterial.new()
	_under_mat.shader = GLOW
	_under_mat.set_shader_parameter("mode", 0)
	_under_mat.set_shader_parameter("energy", 0.4)
	add_child(tm)
	for i in 3:
		var l := OmniLight3D.new()
		l.light_color = GOLD
		l.light_energy = 0.0
		l.omni_range = 1.8
		l.omni_attenuation = 1.4
		l.light_specular = 0.3
		add_child(l)
		_trail_lights.append(l)
	# the fuse: a white-hot spark, shedding sparks and smoke
	_fuse = Node3D.new()
	var fh := _glow_quad(0.9, Color(1.0, 0.75, 0.4), 3.0, 1, true)
	var fm_ := fh.material_override as ShaderMaterial
	fm_.set_shader_parameter("rays", 1.2)
	fm_.set_shader_parameter("spin", 3.0)
	_fuse.add_child(fh)
	_fuse_light = OmniLight3D.new()
	_fuse_light.light_color = Color(1.0, 0.55, 0.2)
	_fuse_light.light_energy = 2.0
	_fuse_light.omni_range = 1.6
	_fuse_light.position.y = 0.15
	_fuse.add_child(_fuse_light)
	_fuse.visible = false
	add_child(_fuse)
	_fuse_sparks = _particles("glow", Color(1.0, 0.6, 0.2), 50, 0.5, 0.06)
	_fuse_sparks.direction = Vector3.UP
	_fuse_sparks.spread = 80.0
	_fuse_sparks.initial_velocity_min = 0.6
	_fuse_sparks.initial_velocity_max = 1.8
	_fuse_sparks.gravity = Vector3(0, -4.0, 0)
	add_child(_fuse_sparks)
	_fuse_smoke = _particles("smoke", Color(0.62, 0.56, 0.52, 0.65), 36, 1.6, 0.45)
	_fuse_smoke.direction = Vector3.UP
	_fuse_smoke.spread = 20.0
	_fuse_smoke.initial_velocity_min = 0.3
	_fuse_smoke.initial_velocity_max = 0.6
	_fuse_smoke.gravity = Vector3(0.15, 0.25, 0)
	add_child(_fuse_smoke)
	# the pen's sparks
	_pen_sparks = _particles("glow", GOLD, 70, 0.7, 0.05)
	_pen_sparks.direction = Vector3.UP
	_pen_sparks.spread = 70.0
	_pen_sparks.initial_velocity_min = 0.2
	_pen_sparks.initial_velocity_max = 0.9
	_pen_sparks.gravity = Vector3(0, -2.5, 0)
	_pen_sparks.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	_pen_sparks.emission_sphere_radius = 0.04
	add_child(_pen_sparks)
	# the storms
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
	_storm_glows.clear()
	_flower_anim.clear()
	_break = {}
	_trail_mat.set_shader_parameter("break_r", -1.0)
	_last_trail.clear()
	_fx.clear()
	_vt = e.claim_time.duplicate()
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
	_marker_light = OmniLight3D.new()
	_marker_light.light_color = Color(1.0, 0.8, 0.45)
	_marker_light.light_energy = 1.2
	_marker_light.omni_range = 1.8
	_marker_light.position.y = 0.3
	_marker.add_child(_marker_light)
	_loop_anims(_marker)
	_marker.scale = Vector3.ONE * 1.4
	_halo = _glow_quad(1.0, GOLD, 1.0, 1, true)
	_halo_mat = _halo.material_override as ShaderMaterial
	_halo_mat.set_shader_parameter("spin", 0.8)
	_stage_node.add_child(_halo)
	for s in e.storms:
		var l := OmniLight3D.new()
		l.light_color = VIOLET
		l.light_energy = 3.0
		l.omni_range = 3.6
		l.omni_attenuation = 1.3
		l.light_specular = 0.2
		_stage_node.add_child(l)
		_storm_lights.append(l)
		var g := _glow_quad(E.STORM_R * CELL * 5.0, Color(0.45, 0.2, 0.9), 0.7, 1, false)
		_stage_node.add_child(g)
		_storm_glows.append(g)
	# flowers: small bright blooms on the new meadows
	_flowers = MultiMesh.new()
	_flowers.transform_format = MultiMesh.TRANSFORM_3D
	_flowers.use_colors = true
	var fm := SphereMesh.new()
	fm.radius = 0.028
	fm.height = 0.035
	fm.radial_segments = 8
	fm.rings = 4
	var fmat := StandardMaterial3D.new()
	fmat.vertex_color_use_as_albedo = true
	fmat.roughness = 0.6
	fmat.emission_enabled = true
	fmat.emission = Color(0.12, 0.1, 0.08)
	fm.material = fmat
	_flowers.mesh = fm
	_flowers.instance_count = MAX_FLOWERS
	_flowers.visible_instance_count = 0
	var fmi := MultiMeshInstance3D.new()
	fmi.multimesh = _flowers
	fmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage_node.add_child(fmi)
	_trail_len = -1
	_place_camera(0.0)


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
			_at.set_pixel(x, y, Color(_vt[i], 0, 0))
	_mask_tex.update(_mask)
	_at_tex.update(_at)


## Height of the land at a cell once risen (as the shader has it).
func land_y(c: Vector2i, e: InkEngine) -> float:
	if e.at(c) != E.CLAIMED:
		return 0.0
	var t: float = _vt[c.y * E.W + c.x]
	var r := spring((e.time - t) / 0.9)
	var h := _height.get_pixel(clampi(c.x * 2, 0, 255), clampi(c.y * 2, 0, 191)).r
	return r * LAND_HEIGHT * (0.25 + maxf(h, WATER) * 0.9)


func _relief(c: Vector2i) -> float:
	return _height.get_pixel(clampi(c.x * 2, 0, 255), clampi(c.y * 2, 0, 191)).r


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"claim":
			var delays := _wave(e, d["region"])
			_refresh_mask(e)
			_grow(e, d["region"], delays)
			_celebrate(e, d, delays)
		"die":
			var at := world(Vector2(d["cell"]) + Vector2(0.5, 0.5), 0.2)
			if e.drawing() and e.trail.size() > 1:
				_shatter(e, d["how"])
				_fx.later(0.3, _death_burst.bind(at))
			else:
				_death_burst(at)
			_shake = 0.35
		"spark_spawn":
			var at := world(Vector2(d["cell"]) + Vector2(0.5, 0.5), 0.3)
			_fx.burst(at, Color(1.0, 0.6, 0.2), 20, 2.0, 0.5, 0.12, 1.0, 0.0, 1.0, "glow")
			_fx.star(at, 0.2, 0.9, Color(1.0, 0.6, 0.25), 0.5, 2.0)
		"cleared":
			_shake = 0.25
			_punch = 1.0
			_punch_at = Vector3.ZERO
			for i in 8:
				var p := Vector3(randf_range(-5.0, 5.0), randf_range(1.2, 2.4), randf_range(-3.5, 3.5))
				_fx.later(0.15 + i * 0.22, func():
					_fx.burst(p, [GOLD, Color(1.0, 0.95, 0.8), Color(1.0, 0.55, 0.3)][i % 3], 40, 2.2, 1.1, 0.1, 1.0, -2.5, 0.0, "glow")
					_fx.star(p, 0.3, 1.6, GOLD, 0.6, 2.5)
					_fx.flash(p, GOLD, 2.0))
			_fx.ring(Vector3(0, 0.5, 0), 0.5, 9.0, GOLD, 1.6, 2.5, 0.25)


func _death_burst(at: Vector3) -> void:
	_fx.burst(at, Color(0.35, 0.15, 0.6), 40, 3.0, 0.9, 0.2, 1.0, -2.0, 1.0, "glow")
	_fx.flash(at + Vector3(0, -2.2, 0), Color(0.6, 0.3, 1.0), 3.0)
	_fx.star(at, 0.3, 1.8, VIOLET, 0.6, 2.5)
	_shake = maxf(_shake, 0.5)


## The claim wave: each new cell rises later the further it lies from the line that closed it.
func _wave(e: InkEngine, region: Array) -> Dictionary:
	var t0 := e.time
	var dist := {}
	var q: Array[Vector2i] = []
	for c in _last_trail:
		if e.at(c) == E.CLAIMED and absf(e.claim_time[c.y * E.W + c.x] - t0) < 0.004:
			dist[c] = 0
			q.append(c)
	var inside := {}
	for c in region:
		inside[c] = true
	if q.is_empty() and not region.is_empty():
		q.append(region[0])
		dist[region[0]] = 0
	var head := 0
	var far := 1
	while head < q.size():
		var c := q[head]
		head += 1
		for dd in E.DIRS:
			var n: Vector2i = c + dd
			if inside.has(n) and not dist.has(n):
				dist[n] = dist[c] + 1
				far = maxi(far, dist[n])
				q.append(n)
	var span := clampf(far / 45.0, 0.45, 1.4)
	var delays := {}
	for i in E.W * E.H:
		if absf(e.claim_time[i] - t0) < 0.004:
			var c := Vector2i(i % E.W, i / E.W)
			var dl: float = float(dist.get(c, far)) / far * span
			_vt[i] = t0 + dl
			delays[c] = dl
	return delays


## Light, rings and sparkles as the wave passes; a camera punch towards the new land; much more for a big claim.
func _celebrate(e: InkEngine, d: Dictionary, delays: Dictionary) -> void:
	var region: Array = d["region"]
	var pct := float(d["cells"]) / INTERIOR * 100.0
	var big := pct > 10.0
	var col := SILVER if d["slow"] else GOLD
	var cells: Array = region if not region.is_empty() else delays.keys()
	if cells.is_empty():
		return
	var sum := Vector2.ZERO
	for c in cells:
		sum += Vector2(c)
	var mid: Vector2 = sum / cells.size() + Vector2(0.5, 0.5)
	var reach := 0.0
	for c in cells:
		reach = maxf(reach, (Vector2(c) - mid).length())
	var centre := world(mid, 0.35)
	var rw := reach * CELL
	# a flash where the line closed, a ring of light spreading over the land
	_fx.flash(centre, col, 1.6 if big else 0.8)
	_fx.ring(centre, 0.2, maxf(0.8, rw * 1.1), col, 1.1, 1.5, 0.1)
	_fx.star(world(Vector2(e.pos) + Vector2(0.5, 0.5), 0.35), 0.2, 1.4, col, 0.5, 3.0)
	# sparkles as the wave passes
	var rng := RandomNumberGenerator.new()
	rng.seed = cells.size() * 31 + e.stage
	var n := clampi(cells.size() / 150, 3, 14 if big else 7)
	for i in n:
		var c: Vector2i = cells[rng.randi_range(0, cells.size() - 1)]
		var p := world(Vector2(c) + Vector2(0.5, 0.5), 0.35)
		_fx.later(delays.get(c, 0.0) + 0.05, func():
			_fx.burst(p, col, 8, 1.4, 0.8, 0.045, 1.0, -1.5, 1.0, "glow"))
	if big:
		# a grand claim: a second ring, a column of flares rising, fireworks over the land, a harder punch
		_fx.later(0.35, func(): _fx.ring(centre, 0.3, rw * 1.2 + 0.6, Color(1.0, 0.85, 0.55), 1.3, 1.4, 0.14))
		_fx.star(centre + Vector3(0, 0.4, 0), 0.4, 3.2, col, 0.9, 3.0, 1.5)
		for i in 5:
			var p := centre + Vector3(rng.randf_range(-rw, rw) * 0.6, rng.randf_range(1.2, 2.2), rng.randf_range(-rw, rw) * 0.5)
			_fx.later(0.25 + i * 0.18, func():
				_fx.burst(p, [col, Color(1.0, 0.95, 0.8), Color(1.0, 0.6, 0.35)][i % 3], 36, 2.0, 1.0, 0.09, 1.0, -2.5, 0.0, "glow")
				_fx.star(p, 0.2, 1.2, col, 0.5, 2.0))
	_punch = 1.0 if big else clampf(0.35 + pct * 0.06, 0.35, 0.8)
	_punch_at = world(mid)
	_punch_tilt = (0.025 if mid.x < E.W * 0.5 else -0.025) * _punch
	_shake = maxf(_shake, 0.2 if big else 0.07)


## Trees, houses and boats grow on newly claimed land (a few per claim, in the land's style) as the wave reaches
## them, and flowers bloom over the meadows.
func _grow(e: InkEngine, region: Array, delays: Dictionary) -> void:
	if region.is_empty():
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = region.size() * 7919 + e.stage
	if _props.size() <= 260:
		var n := clampi(region.size() / 90, 1, 30)
		var kinds: Array = _land["props"]
		for i in n:
			var c: Vector2i = region[rng.randi_range(0, region.size() - 1)]
			# keep off the edges
			if e.is_edge(c) or e.is_edge(c + Vector2i(2, 0)) or e.is_edge(c - Vector2i(2, 0)) or e.is_edge(c + Vector2i(0, 2)) or e.is_edge(c - Vector2i(0, 2)):
				continue
			var h := _relief(c)
			var kind: String = "boat" if h < WATER else kinds[rng.randi_range(0, kinds.size() - 1)]
			if h > 0.66 and kind != "boat":
				kind = "rock"
			if kind == "boat" and rng.randf() < 0.6:
				continue
			var p := _scene(kind, 0.06, Color(0.3, 0.5, 0.25))
			p.rotation.y = rng.randf() * TAU
			var s := rng.randf_range(0.8, 1.2)
			p.scale = Vector3.ONE * 0.001
			_stage_node.add_child(p)
			_loop_anims(p)
			_props.append({"node": p, "cell": c, "at": e.time + float(delays.get(c, 0.0)) + 0.35 + rng.randf_range(0.0, 0.4), "s": s})
	# flowers on the low meadows
	var blooms: Array = [Color(1.0, 0.85, 0.3), Color(1.0, 0.45, 0.5), Color(0.95, 0.95, 1.0), Color(0.75, 0.5, 1.0)]
	if e.stage % LANDS.size() == 4:
		blooms = [Color(1.0, 0.5, 0.15), Color(1.0, 0.75, 0.3)]  # embers on the ash
	elif e.stage % LANDS.size() == 3:
		blooms = [Color(0.8, 0.9, 1.0), Color(1.0, 1.0, 1.0)]    # frost flowers
	var nf := clampi(region.size() / 22, 0, 160)
	for i in nf:
		if _flowers.visible_instance_count >= MAX_FLOWERS:
			break
		var c: Vector2i = region[rng.randi_range(0, region.size() - 1)]
		var h := _relief(c)
		if h < WATER + 0.03 or h > 0.58 or e.is_edge(c):
			continue
		var idx := _flowers.visible_instance_count
		_flowers.visible_instance_count += 1
		var col: Color = blooms[rng.randi_range(0, blooms.size() - 1)]
		_flowers.set_instance_color(idx, col)
		_flowers.set_instance_transform(idx, Transform3D(Basis().scaled(Vector3.ONE * 0.001), world(Vector2(c) + Vector2(0.5, 0.5))))
		var off := Vector2(rng.randf_range(0.2, 0.8), rng.randf_range(0.2, 0.8))
		_flower_anim.append({"i": idx, "cell": c, "off": off, "at": e.time + float(delays.get(c, 0.0)) + 0.25 + rng.randf_range(0.0, 0.5),
			"s": rng.randf_range(0.7, 1.3)})


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _marker == null:
		return
	_mat.set_shader_parameter("now", e.time)
	var drawing := e.drawing()
	if drawing:
		_last_trail = e.trail.duplicate()
	# the pen: brighter when down, pulsing, shedding sparks as it draws
	var mp := world(Vector2(e.pos) + Vector2(0.5, 0.5), land_y(e.pos, e) + 0.02)
	_marker.position = _marker.position.lerp(mp, minf(1.0, delta * 30.0))
	_marker.visible = not (e.phase == E.Phase.DYING and fmod(_time, 0.2) < 0.1)
	var pen_down := drawing or game.pen or e.draw_fast or e.draw_slow
	var slow := (drawing and e.trail_slow) or (not drawing and e.draw_slow and not e.draw_fast)
	var pc := SILVER if slow else GOLD
	var pulse := 0.5 + 0.5 * sin(_time * (9.0 if drawing else 5.0))
	_halo.visible = _marker.visible
	_halo.position = _marker.position + Vector3(0, 0.12, 0)
	_halo.scale = Vector3.ONE * ((0.75 + pulse * 0.15) if drawing else (0.55 + pulse * 0.08) if pen_down else 0.45)
	_halo_mat.set_shader_parameter("color", pc)
	_halo_mat.set_shader_parameter("energy", (1.5 + pulse * 0.9) if drawing else (1.0 + pulse * 0.4) if pen_down else 0.55)
	_halo_mat.set_shader_parameter("rays", 1.0 if drawing else 0.0)
	_marker_light.light_color = pc
	_marker_light.light_energy = (2.2 + pulse * 0.8) if pen_down else 1.0
	_pen_sparks.emitting = drawing and e.phase == E.Phase.PLAY
	_pen_sparks.position = _marker.position + Vector3(0, 0.05, 0)
	_pen_sparks.material_override = Fx.material("glow", pc)
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
	# the line, breaking or drawn
	if not _break.is_empty():
		_run_break(delta)
	elif e.trail.size() != _trail_len or e.trail_slow != _trail_slow:
		_trail_len = e.trail.size()
		_trail_slow = e.trail_slow
		_draw_trail(e)
	_update_trail_lights(e)
	_update_fuse(e, delta)
	_draw_storms(e)
	# props and flowers pop up with an overshoot
	for p in _props:
		var n: Node3D = p["node"]
		var c: Vector2i = p["cell"]
		var k: float = (e.time - p["at"]) / 0.45
		if k > 3.0 and n.scale.x >= p["s"] * 0.999:
			continue
		n.position = world(Vector2(c) + Vector2(0.5, 0.5), land_y(c, e))
		n.scale = Vector3.ONE * maxf(0.001, spring(k) * p["s"]) * Vector3(1.0, 1.0 + 0.3 * sin(clampf(k, 0.0, 1.0) * PI), 1.0)
	var i := 0
	while i < _flower_anim.size():
		var f: Dictionary = _flower_anim[i]
		var k: float = (e.time - f["at"]) / 0.35
		var c: Vector2i = f["cell"]
		var sc := maxf(0.001, spring(k) * f["s"])
		_flowers.set_instance_transform(f["i"], Transform3D(Basis().scaled(Vector3.ONE * sc),
			world(Vector2(c) + f["off"], land_y(c, e) + 0.01)))
		if k > 3.0 and e.time - _vt[c.y * E.W + c.x] > 2.0:
			_flower_anim.remove_at(i)
		else:
			i += 1
	_shake = maxf(0.0, _shake - delta * 1.5)
	_punch = maxf(0.0, _punch - delta * 0.9)
	_place_camera(delta)


func _polyline(e: InkEngine) -> void:
	_trail_pts.clear()
	_trail_s.resize(e.trail.size())
	var s := 0.0
	var prev := Vector3.ZERO
	for i in e.trail.size():
		var c: Vector2i = e.trail[i]
		var p := world(Vector2(c) + Vector2(0.5, 0.5), TUBE_R * 0.8 + land_y(c, e))
		if i > 0:
			s += p.distance_to(prev)
		_trail_s[i] = s
		_trail_pts.append(p)
		prev = p


func _draw_trail(e: InkEngine) -> void:
	_trail_mesh.clear_surfaces()
	if e.trail.size() < 2:
		return
	_polyline(e)
	_build_tube(_trail_pts, _trail_s, e.trail_slow)


## The tube: straight runs between the corners, eight sides round, UV.x the distance along the line.
func _build_tube(pts: Array[Vector3], ss: PackedFloat32Array, slow_: bool) -> void:
	var keep: Array[int] = [0]
	for i in range(1, pts.size() - 1):
		var a := (pts[i] - pts[i - 1]).normalized()
		var b := (pts[i + 1] - pts[i]).normalized()
		if a.dot(b) < 0.999:
			keep.append(i)
	keep.append(pts.size() - 1)
	var total: float = ss[ss.size() - 1]
	_trail_mat.set_shader_parameter("slow", 1.0 if slow_ else 0.0)
	_trail_mat.set_shader_parameter("length_", total)
	_under_mat.set_shader_parameter("color", SILVER if slow_ else GOLD)
	_under_mat.set_shader_parameter("energy", 0.25 if slow_ else 0.4)
	var sides := 8
	_trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES, _trail_mat)
	for k in keep.size() - 1:
		var ia := keep[k]
		var ib := keep[k + 1]
		var a: Vector3 = pts[ia]
		var b: Vector3 = pts[ib]
		var t := (b - a).normalized()
		var side := t.cross(Vector3.UP).normalized()
		if side.length() < 0.5:
			side = Vector3.RIGHT
		var up := side.cross(t).normalized()
		# run on past the corners so the joins close
		var a2 := a - t * (TUBE_R if k > 0 else 0.0)
		var b2 := b + t * TUBE_R
		var sa: float = ss[ia] - (TUBE_R if k > 0 else 0.0)
		var sb: float = ss[ib] + TUBE_R
		for j in sides:
			var f0 := float(j) / sides
			var f1 := float(j + 1) / sides
			var n0 := up * cos(f0 * TAU) + side * sin(f0 * TAU)
			var n1 := up * cos(f1 * TAU) + side * sin(f1 * TAU)
			var quad := [[a2, n0, sa, f0], [b2, n0, sb, f0], [b2, n1, sb, f1], [a2, n0, sa, f0], [b2, n1, sb, f1], [a2, n1, sa, f1]]
			for v in quad:
				_trail_mesh.surface_set_normal(v[1])
				_trail_mesh.surface_set_uv(Vector2(v[2], v[3]))
				_trail_mesh.surface_add_vertex(v[0] + v[1] * TUBE_R)
	# a rounded cap at the start
	var t0 := (pts[1] - pts[0]).normalized()
	var cs := t0.cross(Vector3.UP).normalized()
	var cu := cs.cross(t0).normalized()
	for j in sides:
		var f0 := float(j) / sides
		var f1 := float(j + 1) / sides
		var n0 := cu * cos(f0 * TAU) + cs * sin(f0 * TAU)
		var n1 := cu * cos(f1 * TAU) + cs * sin(f1 * TAU)
		for v in [[pts[0], -t0], [pts[0] + n1 * TUBE_R, n1], [pts[0] + n0 * TUBE_R, n0]]:
			_trail_mesh.surface_set_normal(v[1])
			_trail_mesh.surface_set_uv(Vector2(0.0, f0))
			_trail_mesh.surface_add_vertex(v[0])
	_trail_mesh.surface_end()
	# the glow on the board under it
	_trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES, _under_mat)
	var w := 0.2
	for i in pts.size() - 1:
		var a := pts[i]
		var b := pts[i + 1]
		a.y = maxf(a.y - TUBE_R * 0.8, 0.0) + 0.012
		b.y = maxf(b.y - TUBE_R * 0.8, 0.0) + 0.012
		var t := (b - a).normalized()
		var sd := t.cross(Vector3.UP).normalized() * w
		var ext := t * w * 0.5
		a -= ext
		b += ext
		var sa: float = ss[i]
		var sb: float = ss[i + 1]
		for v in [[a - sd, sa, 0.0], [b - sd, sb, 0.0], [b + sd, sb, 1.0], [a - sd, sa, 0.0], [b + sd, sb, 1.0], [a + sd, sa, 1.0]]:
			_trail_mesh.surface_set_uv(Vector2(v[1], v[2]))
			_trail_mesh.surface_add_vertex(v[0])
	_trail_mesh.surface_end()


func _update_trail_lights(e: InkEngine) -> void:
	var on := _trail_pts.size() >= 2 and (e.drawing() or not _break.is_empty())
	for i in _trail_lights.size():
		var l := _trail_lights[i]
		if not on:
			l.light_energy = 0.0
			continue
		var at := clampi(int((i * 2 + 1) / 6.0 * _trail_pts.size()), 0, _trail_pts.size() - 1)
		l.position = _trail_pts[at] + Vector3(0, 0.25, 0)
		l.light_color = SILVER if _trail_slow else GOLD
		l.light_energy = clampf(_trail_pts.size() / 20.0, 0.2, 1.0) * (1.1 + 0.2 * sin(_time * 6.0 + i * 2.0)) * (0.6 if _trail_slow else 1.0)


func _update_fuse(e: InkEngine, delta: float) -> void:
	var lit := e.fuse >= 0.0 and e.drawing() and _break.is_empty() and e.trail.size() >= 2 and _trail_s.size() == e.trail.size()
	_fuse.visible = lit
	_fuse_sparks.emitting = lit
	_fuse_smoke.emitting = lit
	if not lit:
		_trail_mat.set_shader_parameter("burnt", -1.0)
		return
	var i := clampi(int(e.fuse), 0, e.trail.size() - 2)
	var f := clampf(e.fuse - i, 0.0, 1.0)
	var p := _trail_pts[i].lerp(_trail_pts[i + 1], f)
	_fuse.position = p + Vector3(0, 0.05, 0)
	_fuse.scale = Vector3.ONE * (0.8 + 0.3 * randf())
	_fuse_light.light_energy = 1.8 + randf() * 1.2
	_fuse_sparks.position = p
	_fuse_smoke.position = p + Vector3(0, 0.08, 0)
	_trail_mat.set_shader_parameter("burnt", lerpf(_trail_s[i], _trail_s[i + 1], f))


## The storm (or a spark, or the fuse) broke the line: it shatters from where it was hit, shards of gold flying.
func _shatter(e: InkEngine, how: String) -> void:
	if _trail_s.size() != e.trail.size():
		_polyline(e)
		_trail_mesh.clear_surfaces()
		_build_tube(_trail_pts, _trail_s, e.trail_slow)
	var hit := _trail_pts.size() - 1
	if how == "storm" and not e.storms.is_empty():
		var best := INF
		for st in e.storms:
			var sp := world(st["pos"])
			for j in _trail_pts.size():
				var dd := Vector2(_trail_pts[j].x - sp.x, _trail_pts[j].z - sp.z).length_squared()
				if dd < best:
					best = dd
					hit = j
	var c: float = _trail_s[hit]
	var order: Array = []
	for j in _trail_pts.size():
		order.append([absf(_trail_s[j] - c), j])
	order.sort_custom(func(a, b): return a[0] < b[0])
	_break = {"c": c, "r": 0.0, "order": order, "next": 0, "col": SILVER if e.trail_slow else GOLD,
		"from": _trail_pts[hit], "end": _trail_s[_trail_s.size() - 1]}
	_trail_mat.set_shader_parameter("break_c", c)
	_trail_mat.set_shader_parameter("break_r", 0.0)
	_trail_mat.set_shader_parameter("burnt", -1.0)
	var hp := _trail_pts[hit] + Vector3(0, 0.1, 0)
	_fx.star(hp, 0.2, 1.3, Color(1.0, 0.85, 0.5), 0.35, 2.2, 1.2)
	_fx.flash(hp, Color(1.0, 0.8, 0.4), 2.0)
	_fx.burst(hp, Color(1.0, 0.85, 0.5), 30, 2.5, 0.6, 0.08, 1.0, -3.0, 1.0, "glow")


func _run_break(delta: float) -> void:
	var b := _break
	b["r"] += delta * 9.0
	_trail_mat.set_shader_parameter("break_r", b["r"])
	var order: Array = b["order"]
	var col: Color = b["col"]
	var from: Vector3 = b["from"]
	while b["next"] < order.size() and order[b["next"]][0] <= b["r"]:
		var j: int = order[b["next"]][1]
		b["next"] += 1
		var p := _trail_pts[j]
		var out := p - from
		out.y = 0.0
		out = out.normalized() if out.length() > 0.01 else Vector3(randf() - 0.5, 0, randf() - 0.5).normalized()
		for k in 3:
			var v := out * randf_range(0.6, 2.2) + Vector3(randf_range(-0.8, 0.8), randf_range(1.2, 3.0), randf_range(-0.8, 0.8))
			_fx.shard(p + Vector3(randf_range(-0.03, 0.03), 0, randf_range(-0.03, 0.03)), v, col.lerp(Color.WHITE, randf() * 0.3))
		if b["next"] % 6 == 0:
			_fx.burst(p, col, 6, 1.2, 0.4, 0.05, 1.0, -2.0, 1.0, "glow")
	if b["next"] >= order.size():
		_break = {}
		_trail_mat.set_shader_parameter("break_r", -1.0)
		_trail_mesh.clear_surfaces()
		_trail_pts.clear()
		_trail_s.resize(0)
		_trail_len = -1


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
			_storm_lights[si].position = centre + Vector3(0, 0.7, 0)
			_storm_lights[si].light_energy = 2.8 + 0.8 * sin(_time * 3.0 + si) + 0.6 * sin(_time * 7.3 + si * 2.0)
			_storm_glows[si].position = centre + Vector3(0, 0.015, 0)
			_storm_glows[si].rotation.y = _time * 0.4
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


## A gentle camera: the whole board in view, leaning a little towards the pen, swaying slowly, punching in and
## tilting towards new land for a moment.
func _place_camera(delta: float) -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(BOARD.y * 0.5 + 1.0, (BOARD.x * 0.5 + 1.2) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var goal := Vector3.ZERO
	if _marker:
		goal = Vector3(_marker.position.x * 0.07, 0, _marker.position.z * 0.06)
	_lean = _lean.lerp(goal, minf(1.0, delta * 1.2)) if delta > 0.0 else goal
	var p := _punch * _punch * (3.0 - 2.0 * _punch)  # eased
	var target := Vector3(0, 0, 0.35) + _lean + (_punch_at - _lean) * 0.04 * p
	dist *= 1.0 - 0.025 * p
	var yaw := sin(_time * 0.11) * 0.03 + _lean.x * 0.012 + _punch_tilt * p
	var dir := Vector3(0, 0.86, 0.5).normalized().rotated(Vector3.UP, yaw)
	dir = dir.rotated(dir.cross(Vector3.UP).normalized(), sin(_time * 0.07) * 0.015 - 0.03 * p)
	var j := Vector3(sin(_time * 50.0), 0, cos(_time * 43.0)) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	camera.position = target + dir * dist + j
	camera.look_at(target + j, Vector3.UP)
