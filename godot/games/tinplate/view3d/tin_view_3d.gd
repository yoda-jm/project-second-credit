class_name TinView3D
extends Node3D
## Tinplate Turbo in 3D: each track is a tabletop diorama seen from above through a tilt-shift lens: a printed-tin road
## with kerbs and striped tin barriers, a bridge where a figure-eight crosses itself, a garden, a canyon, snow, a
## harbour by night, a neon city, autumn woods around it, toys scattered about. The tin cars roll on spinning wheels,
## lean in the slides, fly off ramps, leave skid marks and puffs of dust, splash through puddles and slither on oil;
## the start gantry counts down. World = the board (x 0..48, z 0..28), the road at y = 0 (higher on the bridge).

const T = preload("res://games/tinplate/engine/tin_engine.gd")
const M := "res://games/tinplate/art/models/"
const ROAD_SHADER := preload("res://games/tinplate/shaders/tin_road.gdshader")
const BARRIER_SHADER := preload("res://games/tinplate/shaders/tin_barrier.gdshader")
const CAR_R := 0.21              ## wheel radius, for their spin
## per theme: ground texture, its tint, sky colour, sun colour, sun pitch/yaw, sun energy, ambient, night, barrier colour
const THEMES := [
	["grass_lush", Color(0.78, 0.95, 0.5), Color(0.55, 0.75, 0.95), Color(1.0, 0.96, 0.88), Vector2(-55, -30), 1.3, Color(0.75, 0.8, 0.9), false, Color(0.85, 0.18, 0.15)],
	["sand", Color(1.0, 0.84, 0.68), Color(0.95, 0.7, 0.5), Color(1.0, 0.82, 0.6), Vector2(-35, 40), 1.4, Color(0.9, 0.75, 0.65), false, Color(0.2, 0.45, 0.85)],
	["beach_sand", Color(1.05, 1.08, 1.15), Color(0.75, 0.8, 0.9), Color(0.92, 0.95, 1.0), Vector2(-60, -50), 1.0, Color(0.8, 0.85, 0.95), false, Color(0.15, 0.5, 0.3)],
	["planks", Color(0.6, 0.55, 0.5), Color(0.05, 0.07, 0.15), Color(0.6, 0.7, 1.0), Vector2(-50, 30), 0.25, Color(0.3, 0.35, 0.55), true, Color(0.95, 0.75, 0.15)],
	["stone_bricks", Color(0.3, 0.3, 0.4), Color(0.03, 0.02, 0.08), Color(0.7, 0.6, 1.0), Vector2(-50, -30), 0.15, Color(0.3, 0.25, 0.45), true, Color(0.1, 0.9, 1.0)],
	["grass", Color(1.0, 0.75, 0.45), Color(0.95, 0.65, 0.4), Color(1.0, 0.75, 0.5), Vector2(-22, 60), 1.3, Color(0.85, 0.7, 0.55), false, Color(0.9, 0.45, 0.1)],
]

@export var game: TinGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _stage: Node3D
var _cars: Array[Node3D] = []
var _wheels: Array = []          ## per car: [fl, fr, rl, rr]
var _keys: Array = []
var _lights: Array = []          ## per car headlight
var _wrench: Node3D
var _gantry_mats: Array[StandardMaterial3D] = []
var _skids: Array = []           ## [a, b, c, d, age]
var _skid_mesh: MeshInstance3D
var _skid_im: ImmediateMesh
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _theme := 0
var _windmills: Array[Node3D] = []
var _air := []


func _ready() -> void:
	_we = WorldEnvironment.new()
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 90.0
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 34
	camera.far = 600.0
	camera.current = true
	var ca := CameraAttributesPractical.new()
	ca.dof_blur_far_enabled = true
	ca.dof_blur_near_enabled = true
	ca.dof_blur_amount = 0.07
	camera.attributes = ca
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 22.0
	add_child(_fx)
	game.race_started.connect(_on_race)
	if game.engine:
		_on_race(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mat(col: Color, rough := 0.5, metal := 0.0, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	m.metallic = metal
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _box(size: Vector3, col: Color, at := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = _mat(col, 0.4, 0.4)
	mi.position = at
	return mi


# ------------------------------------------------------------------ a race

func _on_race(e: TinEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_theme = e.track.theme
	_skids.clear()
	_windmills.clear()
	_air = [false, false, false, false]
	_build_environment(e)
	_build_ground(e)
	_build_road(e.track)
	_build_barriers(e.track)
	_build_bridge(e.track)
	_build_hazards(e.track)
	_build_props(e.track)
	_build_cars(e)
	_skid_im = ImmediateMesh.new()
	_skid_mesh = MeshInstance3D.new()
	_skid_mesh.mesh = _skid_im
	var sm := _mat(Color(0.05, 0.05, 0.05, 0.55), 0.9)
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.vertex_color_use_as_albedo = true
	_skid_mesh.material_override = sm
	_skid_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage.add_child(_skid_mesh)
	_wrench = null
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


func _build_environment(e: TinEngine) -> void:
	var th: Array = THEMES[_theme % THEMES.size()]
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = th[2]
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = th[6]
	_env.ambient_light_energy = 0.42 if not th[7] else 0.4
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.0
	_env.glow_enabled = true
	_env.glow_intensity = 0.6 if not th[7] else 1.0
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_env.ssr_enabled = th[7]
	_env.fog_enabled = true
	_env.fog_light_color = th[2]
	_env.fog_density = 0.0012
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.18
	_env.adjustment_contrast = 1.08
	_we.environment = _env
	var rot: Vector2 = th[4]
	_sun.rotation_degrees = Vector3(rot.x, rot.y, 0)
	_sun.light_color = th[3]
	_sun.light_energy = th[5]


func _build_ground(e: TinEngine) -> void:
	var th: Array = THEMES[_theme % THEMES.size()]
	var g := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(120, 80)
	g.mesh = pm
	g.position = Vector3(24, -0.02, 14)
	g.material_override = Pbr.material(th[0], th[1], 0.12)
	_stage.add_child(g)
	# the board's tin edge: a raised rim round the diorama
	for side in [[Vector3(24, 0.15, -6.5), Vector3(66, 0.3, 0.6)], [Vector3(24, 0.15, 34.5), Vector3(66, 0.3, 0.6)],
			[Vector3(-9.5, 0.15, 14), Vector3(0.6, 0.3, 41.6)], [Vector3(57.5, 0.15, 14), Vector3(0.6, 0.3, 41.6)]]:
		var rim := _box(side[1], Color(0.75, 0.72, 0.68), side[0])
		(rim.material_override as StandardMaterial3D).metallic = 0.8
		(rim.material_override as StandardMaterial3D).roughness = 0.25
		_stage.add_child(rim)
	match _theme:
		2:
			_add_weather(Color(1, 1, 1, 0.9), Vector3(0, -1.5, 0), 0.12, 300)
		5:
			_add_weather(Color(0.95, 0.5, 0.15, 0.95), Vector3(0.6, -0.8, 0.3), 0.18, 90)
		4:
			_add_weather(Color(0.6, 0.4, 1.0, 0.5), Vector3(0, 0.3, 0), 0.06, 120)


func _add_weather(col: Color, grav: Vector3, size: float, amount: int) -> void:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = 8.0
	p.preprocess = 8.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(32, 0.5, 20)
	p.position = Vector3(24, 10, 14)
	p.direction = Vector3(0, -1, 0)
	p.initial_velocity_min = 0.3
	p.initial_velocity_max = 0.8
	p.gravity = grav
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.2
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	p.mesh = q
	p.material_override = Fx.material("soft", col)
	_stage.add_child(p)


## The road: a ribbon along the samples, the width across, following the bridge's height; UV.x across, UV.y metres.
func _build_road(t: TinTrack) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := t.count()
	for s in n:
		var a := s
		var b := (s + 1) % n
		var la := t.pos[a] + t.left_normal(a) * t.width * 0.5
		var ra := t.pos[a] - t.left_normal(a) * t.width * 0.5
		var lb := t.pos[b] + t.left_normal(b) * t.width * 0.5
		var rb := t.pos[b] - t.left_normal(b) * t.width * 0.5
		var ya := t.height[a] + 0.01
		var yb := t.height[b] + 0.01
		var va := s * TinTrack.STEP
		var vb := (s + 1) * TinTrack.STEP
		# clockwise seen from above (Godot's front faces)
		var quad := [[Vector3(ra.x, ya, ra.y), Vector2(0, va)], [Vector3(lb.x, yb, lb.y), Vector2(1, vb)], [Vector3(la.x, ya, la.y), Vector2(1, va)],
			[Vector3(ra.x, ya, ra.y), Vector2(0, va)], [Vector3(rb.x, yb, rb.y), Vector2(0, vb)], [Vector3(lb.x, yb, lb.y), Vector2(1, vb)]]
		for v in quad:
			st.set_normal(Vector3.UP)
			st.set_uv(v[1])
			st.add_vertex(v[0])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = ROAD_SHADER
	var night: bool = THEMES[_theme % THEMES.size()][7]
	m.set_shader_parameter("night", 1.0 if night else 0.0)
	m.set_shader_parameter("start_y", (t.count() - 2) * TinTrack.STEP)
	mi.material_override = m
	_stage.add_child(mi)


## Striped tin barriers along both edges (lower ones duck under the bridge's deck, which has its own railings).
func _build_barriers(t: TinTrack) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := t.count()
	var hgt := 0.42
	for side in [-1.0, 1.0]:
		for s in n:
			var a := s
			var b := (s + 1) % n
			var off := t.width * 0.5 + 0.12
			var pa: Vector2 = t.pos[a] + t.left_normal(a) * off * side
			var pb: Vector2 = t.pos[b] + t.left_normal(b) * off * side
			var ya := t.height[a]
			var yb := t.height[b]
			var va := s * TinTrack.STEP
			var vb := (s + 1) * TinTrack.STEP
			var A := Vector3(pa.x, ya, pa.y)
			var B := Vector3(pb.x, yb, pb.y)
			var up := Vector3(0, hgt, 0)
			var nrm: Vector3 = Vector3(t.left_normal(a).x, 0, t.left_normal(a).y) * -side
			for v in [[A, Vector2(0, va)], [B + up, Vector2(1, vb)], [B, Vector2(0, vb)], [A, Vector2(0, va)], [A + up, Vector2(1, va)], [B + up, Vector2(1, vb)]]:
				st.set_normal(nrm)
				st.set_uv(v[1])
				st.add_vertex(v[0])
			# the rolled top
			var tw: Vector3 = Vector3(t.left_normal(a).x, 0, t.left_normal(a).y) * side * 0.1
			for v in [[A + up, Vector2(1, va)], [B + up + tw, Vector2(1, vb)], [B + up, Vector2(1, vb)], [A + up, Vector2(1, va)], [A + up + tw, Vector2(1, va)], [B + up + tw, Vector2(1, vb)]]:
				st.set_normal(Vector3.UP)
				st.set_uv(v[1])
				st.add_vertex(v[0])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = BARRIER_SHADER
	m.set_shader_parameter("col_b", THEMES[_theme % THEMES.size()][8])
	m.set_shader_parameter("glow", [0.0, 0.0, 0.0, 0.25, 1.6, 0.0][_theme % 6])
	mi.material_override = m
	_stage.add_child(mi)


## Where the road is lifted: a deck edge, pillars down to the ground every few metres.
func _build_bridge(t: TinTrack) -> void:
	var n := t.count()
	var pillar := _mat(Color(0.8, 0.78, 0.72), 0.5, 0.5)
	var deck := _mat(Color(0.35, 0.35, 0.4), 0.4, 0.6)
	for s in n:
		var h := t.height[s]
		if h < 0.4:
			continue
		# the deck's underside: a slab under the road
		var d := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(TinTrack.STEP * 1.05, 0.25, t.width + 0.6)
		d.mesh = bm
		d.material_override = deck
		d.position = Vector3(t.pos[s].x, h - 0.13, t.pos[s].y)
		d.rotation.y = -t.dir[s].angle()
		_stage.add_child(d)
		if s % 7 == 0 and h > 1.0:
			for side in [-1.0, 1.0]:
				var p: Vector2 = t.pos[s] + t.left_normal(s) * side * (t.width * 0.5 + 0.1)
				var c := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.18
				cm.bottom_radius = 0.24
				cm.height = h
				c.mesh = cm
				c.material_override = pillar
				c.position = Vector3(p.x, h * 0.5 - 0.1, p.y)
				_stage.add_child(c)


func _build_hazards(t: TinTrack) -> void:
	for o in t.oil:
		var n := _scene("oil")
		if n == null:
			n = MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 1.1
			cm.bottom_radius = 1.1
			cm.height = 0.02
			(n as MeshInstance3D).mesh = cm
			(n as MeshInstance3D).material_override = _mat(Color(0.03, 0.03, 0.04), 0.05, 0.6)
		var s := t.nearest_global(o)
		n.position = Vector3(o.x, t.height[s] + 0.02, o.y)
		n.rotation.y = randf() * TAU
		_stage.add_child(n)
	for w in t.puddles:
		var n := _scene("puddle")
		if n == null:
			n = MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 1.2
			cm.bottom_radius = 1.2
			cm.height = 0.02
			(n as MeshInstance3D).mesh = cm
			(n as MeshInstance3D).material_override = _mat(Color(0.35, 0.5, 0.65), 0.02, 0.3)
		var s := t.nearest_global(w)
		n.position = Vector3(w.x, t.height[s] + 0.02, w.y)
		_stage.add_child(n)
	for r in t.ramps:
		var n := _scene("ramp")
		if n == null:
			n = _box(Vector3(3.0, 0.3, t.width - 0.4), Color(0.95, 0.65, 0.15), Vector3(0, 0.15, 0))
		var holder := Node3D.new()
		holder.add_child(n)
		# its lip (local x = 1.5) where the jump happens; its deck as wide as the road
		holder.position = Vector3(t.pos[r].x, t.height[r], t.pos[r].y) - Vector3(t.dir[r].x, 0, t.dir[r].y) * 1.5
		holder.rotation.y = -t.dir[r].angle()
		holder.scale = Vector3(1.0, 1.0, (t.width - 0.3) / 2.2)
		_stage.add_child(holder)


## Toys and scenery round the road: a few big pieces on the straights (the start gantry, a grandstand), then a scatter
## by theme where the road is far enough away.
func _build_props(t: TinTrack) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(t.name)
	_gantry_mats.clear()
	var g := _scene("start_gantry")
	var s0 := t.count() - 2
	if g:
		g.position = Vector3(t.pos[s0].x, t.height[s0], t.pos[s0].y)
		g.rotation.y = -t.dir[s0].angle() + PI * 0.5
		var k := (t.width + 1.6) / 10.0
		g.scale = Vector3(maxf(k, 0.6), maxf(k, 0.6), maxf(k, 0.6))
		_stage.add_child(g)
		for li in 5:
			var lamp := g.find_child("light_%d" % li, true, false)
			if lamp == null:
				continue
			var lm := _mat(Color(1.0, 0.15, 0.1), 0.4, 0.0, 3.0)
			for mi in ([lamp] if lamp is MeshInstance3D else []) + lamp.find_children("*", "MeshInstance3D", true, false):
				(mi as MeshInstance3D).material_override = lm
			_gantry_mats.append(lm)
	# the grandstand along the longest straight's outside
	var best := 0
	var run := 0
	var best_run := 0
	for s in t.count():
		if absf(t.bend[s]) < 0.02:
			run += 1
			if run > best_run:
				best_run = run
				best = s - run / 2
		else:
			run = 0
	var stand := _scene("grandstand")
	if stand:
		var p: Vector2 = t.pos[best] + t.left_normal(best) * (t.width * 0.5 + 3.5)
		if not _clear(t, p, 4.5):
			p = t.pos[best] - t.left_normal(best) * (t.width * 0.5 + 3.5)
		if _clear(t, p, 4.0):
			stand.position = Vector3(p.x, 0, p.y)
			var to := t.pos[best] - p
			stand.rotation.y = -to.angle() + PI * 0.5
			_stage.add_child(stand)
	# the scatter
	var kinds: Array = [["tree", "tree_round", "house", "windmill_toy", "hay_bale"], ["rock", "rock", "tyre_stack", "cone", "hay_bale", "rock"],
		["tree", "tree_round", "house", "tyre_stack"], ["house", "tyre_stack", "cone", "barrier"], ["house", "tyre_stack", "cone"],
		["tree", "tree_round", "tree", "hay_bale", "house"]][_theme % 6]
	var night: bool = THEMES[_theme % THEMES.size()][7]
	var lamps := 0
	var x := -7.0
	while x < 56.0:
		var z := -5.0
		while z < 34.0:
			var p := Vector2(x + rng.randf_range(-1.0, 1.0), z + rng.randf_range(-1.0, 1.0))
			z += 3.2
			var near := _road_dist(t, p)
			if near < t.width * 0.5 + 1.8:
				continue
			if night and lamps < 12 and near < t.width * 0.5 + 3.0 and rng.randf() < 0.3:
				_lamp(p)
				lamps += 1
				continue
			if rng.randf() > (0.35 if near < 8.0 else 0.55):
				continue
			var kind: String = kinds[rng.randi() % kinds.size()]
			var n := _rock(rng) if kind == "rock" else _scene(kind)
			if n == null:
				continue
			n.position = Vector3(p.x, 0, p.y)
			n.rotation.y = rng.randf() * TAU
			var sc := rng.randf_range(0.85, 1.2)
			n.scale = Vector3(sc, sc, sc)
			_stage.add_child(n)
			if kind == "windmill_toy":
				var sails := n.find_child("sails", true, false) as Node3D
				if sails:
					_windmills.append(sails)
			if night and kind == "house":
				var l := OmniLight3D.new()
				l.light_color = Color(1.0, 0.75, 0.4)
				l.light_energy = 0.8
				l.omni_range = 3.0
				l.position = Vector3(0, 1.0, 0)
				n.add_child(l)
		x += 3.2


## A desert boulder: a squashed, lumpy sphere of red rock.
func _rock(rng: RandomNumberGenerator) -> Node3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.8
	sm.height = 1.2
	sm.radial_segments = 10
	sm.rings = 6
	mi.mesh = sm
	mi.material_override = Pbr.material("rock", Color(0.95, 0.62, 0.45), 0.4)
	mi.scale = Vector3(rng.randf_range(0.7, 1.6), rng.randf_range(0.5, 1.1), rng.randf_range(0.7, 1.4))
	mi.position.y = 0.2
	var n := Node3D.new()
	n.add_child(mi)
	return n


func _lamp(p: Vector2) -> void:
	var post := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.06
	cm.bottom_radius = 0.09
	cm.height = 3.0
	post.mesh = cm
	post.material_override = _mat(Color(0.2, 0.2, 0.22), 0.4, 0.8)
	post.position = Vector3(p.x, 1.5, p.y)
	_stage.add_child(post)
	var bulb := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.22
	sm.height = 0.44
	bulb.mesh = sm
	var col: Color = Color(1.0, 0.8, 0.5) if _theme != 4 else [Color(1.0, 0.2, 0.8), Color(0.1, 0.9, 1.0), Color(0.6, 0.3, 1.0)][int(p.x) % 3]
	bulb.material_override = _mat(col, 0.3, 0.0, 4.0)
	bulb.position = Vector3(p.x, 3.05, p.y)
	_stage.add_child(bulb)
	var l := OmniLight3D.new()
	l.light_color = col
	l.light_energy = 2.2
	l.omni_range = 9.0
	l.position = Vector3(p.x, 3.0, p.y)
	_stage.add_child(l)


func _road_dist(t: TinTrack, p: Vector2) -> float:
	var best := INF
	for s in range(0, t.count(), 2):
		best = minf(best, t.pos[s].distance_to(p))
	return best


func _clear(t: TinTrack, p: Vector2, r: float) -> bool:
	return _road_dist(t, p) > t.width * 0.5 + r


func _build_cars(e: TinEngine) -> void:
	_cars.clear()
	_wheels.clear()
	_keys.clear()
	_lights.clear()
	var night: bool = THEMES[_theme % THEMES.size()][7]
	for c in e.cars:
		var root := Node3D.new()
		var body := _scene("car")
		var col: Color = T.COLOURS[c["i"]]
		if body == null:
			body = Node3D.new()
			body.add_child(_box(Vector3(1.9, 0.45, 0.95), col, Vector3(0, 0.4, 0)))
			body.add_child(_box(Vector3(0.8, 0.35, 0.8), col.lightened(0.2), Vector3(-0.1, 0.8, 0)))
		else:
			for mi in body.find_children("*", "MeshInstance3D", true, false):
				var m := mi as MeshInstance3D
				for k in m.mesh.get_surface_count():
					var sm := m.mesh.surface_get_material(k)
					if sm and sm.resource_name.contains("car_paint"):
						var pm := _mat(col, 0.22, 0.55)
						pm.clearcoat_enabled = true
						pm.clearcoat = 1.0
						pm.clearcoat_roughness = 0.05
						m.set_surface_override_material(k, pm)
		body.name = "body"
		root.add_child(body)
		var wl := []
		for wn in ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"]:
			wl.append(body.find_child(wn, true, false))
		_wheels.append(wl)
		_keys.append(body.find_child("key", true, false))
		var hl: SpotLight3D = null
		if night:
			hl = SpotLight3D.new()
			hl.light_color = Color(1.0, 0.95, 0.8)
			hl.light_energy = 3.0
			hl.spot_range = 9.0
			hl.spot_angle = 32.0
			hl.position = Vector3(1.0, 0.5, 0)
			hl.rotation = Vector3(0, -PI * 0.5, 0)
			hl.rotate_object_local(Vector3.RIGHT, -0.25)
			root.add_child(hl)
		_lights.append(hl)
		# a soft blob shadow follows it onto the road when it flies
		_stage.add_child(root)
		_cars.append(root)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"bump":
			var c := e.cars[d["car"]]
			var p := _at(c) + Vector3(0, 0.4, 0)
			_fx.burst(p, Color(1.0, 0.85, 0.5), 10 + int(d["speed"] * 2), 3.0, 0.4, 0.06, 1.0, -8.0, 1.0, "glow")
			_shake = maxf(_shake, clampf(d["speed"] * 0.03, 0.05, 0.3))
		"knock":
			var a := _at(e.cars[d["a"]])
			var b := _at(e.cars[d["b"]])
			_fx.burst((a + b) * 0.5 + Vector3(0, 0.4, 0), Color(1.0, 0.9, 0.6), 14, 3.0, 0.3, 0.06, 1.0, -6.0, 1.0, "glow")
		"oil":
			var c := e.cars[d["car"]]
			_fx.burst(_at(c), Color(0.1, 0.1, 0.12), 12, 2.0, 0.6, 0.12, 0.0, -6.0, 0.5)
		"splash":
			var c := e.cars[d["car"]]
			_fx.burst(_at(c) + Vector3(0, 0.1, 0), Color(0.75, 0.88, 1.0), 26, 3.5, 0.6, 0.1, 1.0, -12.0, 1.0, "glow")
		"jump":
			_air[d["car"]] = true
		"land":
			var c := e.cars[d["car"]]
			_fx.burst(_at(c), Color(0.85, 0.8, 0.7), 16, 2.5, 0.6, 0.2, 0.0, -2.0, 0.4, "smoke")
			_shake = maxf(_shake, 0.25)
		"wrench":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, 0.8, p.y), Color(1.0, 0.85, 0.3), 30, 4.0, 0.7, 0.08, 1.0, -4.0, 1.0, "glow")
			_fx.flash(Vector3(p.x, 0.5, p.y), Color(1.0, 0.85, 0.4), 2.5)
		"finish":
			var c := e.cars[d["car"]]
			if d["place"] == 1:
				for k in 5:
					_fx.burst(_at(c) + Vector3(randf_range(-2, 2), 2.5, randf_range(-2, 2)), Color.from_hsv(k / 5.0, 0.7, 1.0), 30, 4.0, 1.2, 0.08, 1.0, -3.0, 1.0, "glow")


func _at(c: Dictionary) -> Vector3:
	var p: Vector2 = c["pos"]
	return Vector3(p.x, c["y"], p.y)


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 2.0)
	var e := game.engine
	if e == null or _stage == null or _cars.size() != e.cars.size():
		return
	for i in e.cars.size():
		_place_car(e, i, delta)
	_place_wrench(e, delta)
	_gantry(e)
	for w in _windmills:
		w.rotation.x += delta * 2.0
	_draw_skids(delta)
	_place_camera(delta)


func _place_car(e: TinEngine, i: int, delta: float) -> void:
	var c := e.cars[i]
	var n := _cars[i]
	var p: Vector2 = c["pos"]
	n.position = Vector3(p.x, c["y"], p.y)
	var body := n.get_node("body") as Node3D
	n.rotation.y = -float(c["heading"])
	var v: Vector2 = c["vel"]
	var speed := v.length()
	var fwd := Vector2.from_angle(c["heading"])
	var along := v.dot(fwd)
	# lean into the slide, pitch with the throttle; in the air, nose up then down
	var lat := v.dot(Vector2(-fwd.y, fwd.x))
	body.rotation.x = lerpf(body.rotation.x, clampf(lat * 0.025, -0.18, 0.18), minf(1.0, delta * 8.0))
	var pitch: float = -0.04 * c["throttle"] if not c["air"] else clampf(c["vy"] * 0.03, -0.3, 0.3)
	body.rotation.z = lerpf(body.rotation.z, pitch, minf(1.0, delta * 6.0))
	var wl: Array = _wheels[i]
	for k in wl.size():
		var w := wl[k] as Node3D
		if w == null:
			continue
		w.rotation.z -= along / CAR_R * delta
		if k < 2:
			w.rotation.y = -float(c["steer"]) * 0.45
	var key := _keys[i] as Node3D
	if key:
		key.rotation.x += (2.0 + speed * 0.4) * delta
	# skid marks and dust where the tyres slide
	if c["slide"] > 2.2 and not c["air"] and speed > 4.0:
		var side := Vector2(-fwd.y, fwd.x)
		for s in [-1.0, 1.0]:
			var wp: Vector2 = p - fwd * 0.65 + side * s * 0.42
			var prev: Vector2 = c.get("skid_%d" % int(s), Vector2.INF)
			if prev != Vector2.INF and prev.distance_to(wp) < 1.5:
				_skids.append([prev, wp, side * 0.09, c["y"] + 0.025, 0.0])
			c["skid_%d" % int(s)] = wp
		if randf() < 0.3:
			_fx.burst(n.position - Vector3(fwd.x, 0, fwd.y) * 0.8 + Vector3(0, 0.15, 0), Color(0.85, 0.82, 0.78), 2, 0.8, 0.8, 0.25, 0.0, 0.6, 0.6, "smoke")
	else:
		c.erase("skid_-1")
		c.erase("skid_1")


func _draw_skids(delta: float) -> void:
	for sk in _skids:
		sk[4] += delta
	_skids = _skids.filter(func(sk): return sk[4] < 9.0)
	if _skids.size() > 700:
		_skids = _skids.slice(_skids.size() - 700)
	_skid_im.clear_surfaces()
	if _skids.is_empty():
		return
	_skid_im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for sk in _skids:
		var a: Vector2 = sk[0]
		var b: Vector2 = sk[1]
		var w: Vector2 = sk[2]
		var y: float = sk[3]
		var al := clampf(1.0 - sk[4] / 9.0, 0.0, 1.0) * 0.55
		_skid_im.surface_set_color(Color(0.05, 0.05, 0.05, al))
		for q in [a - w, b - w, b + w, a - w, b + w, a + w]:
			_skid_im.surface_add_vertex(Vector3(q.x, y, q.y))
	_skid_im.surface_end()


func _place_wrench(e: TinEngine, _delta: float) -> void:
	if e.wrench.is_empty():
		if _wrench:
			_wrench.queue_free()
			_wrench = null
		return
	if _wrench == null:
		_wrench = _scene("wrench")
		if _wrench == null:
			_wrench = _box(Vector3(0.6, 0.12, 0.18), Color(0.8, 0.82, 0.85))
		_stage.add_child(_wrench)
		_fx.burst(Vector3(e.wrench["pos"].x, 0.6, e.wrench["pos"].y), Color(1.0, 0.85, 0.4), 20, 2.0, 0.5, 0.06, 1.0, -2.0, 1.0, "glow")
	var p: Vector2 = e.wrench["pos"]
	_wrench.position = Vector3(p.x, e.wrench["y"] + 0.55 + 0.12 * sin(_time * 4.0), p.y)
	_wrench.rotation.y = _time * 2.5
	_wrench.scale = Vector3.ONE * (1.3 + 0.1 * sin(_time * 8.0))


## The start gantry's lights: red through the countdown, green at the go.
func _gantry(e: TinEngine) -> void:
	# the reds come on one by one through the countdown, then all go green
	var lit := int((3.0 - e.phase_t) / 3.0 * _gantry_mats.size()) + 1
	for k in _gantry_mats.size():
		var col := Color(0.2, 1.0, 0.3)
		if e.phase == T.Phase.COUNTDOWN:
			col = Color(1.0, 0.12, 0.08) if k < lit else Color(0.18, 0.03, 0.02)
		var m := _gantry_mats[k]
		m.albedo_color = col
		m.emission = col
		m.emission_energy_multiplier = 3.0 if col.r + col.g > 0.5 else 0.2


func _place_camera(delta: float, snap := false) -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_v := tan(deg_to_rad(camera.fov * 0.5))
	var el := deg_to_rad(57.0)
	var dist := maxf(17.0 / half_v, 27.5 / (half_v * aspect))
	var look := Vector3(24.0, 0.0, 14.8)
	var pos := look + Vector3(sin(_time * 0.05) * 0.8, sin(el), cos(el)) * Vector3(1, dist, dist)
	pos.x = look.x + sin(_time * 0.05) * 0.8
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.5 if Settings.camera_shake else 0.0)
	var k := 1.0 if snap else minf(1.0, delta * 2.0)
	_cam_pos = _cam_pos.lerp(pos, k)
	_cam_look = _cam_look.lerp(look, k)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
	var ca := camera.attributes as CameraAttributesPractical
	var focus := _cam_pos.distance_to(_cam_look)
	ca.dof_blur_far_distance = focus + 9.0
	ca.dof_blur_far_transition = 14.0
	ca.dof_blur_near_distance = focus - 9.0
	ca.dof_blur_near_transition = 10.0
