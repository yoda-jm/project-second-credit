class_name WhiskerView3D
extends Node3D
## Whisker Alley in 3D, seen from the side (2.5D): the street in front, trash cans, the fence, the washing lines and
## the building behind, at night. Engine (x, y) maps to (x, y, depth); the cat moves between depth layers as it
## climbs. Each room is its own lit interior set, swapped in while the cat is inside.

const E = preload("res://games/whisker/engine/whisker_engine.gd")
const M := "res://games/whisker/art/models/"
const Z_STREET := 1.0
const Z_CAN := 0.55
const Z_FENCE := -0.2
const Z_LINE := -1.3
const Z_WALL := -2.6
const WASHING := ["shirt", "socks", "towel", "dress"]
const ROOF_Y := 13.9  ## top of the building's parapet: above it, the chimneys, the city and the moon

@export var game: WhiskerGame

var _camera: Camera3D
var _env: Environment
var _sky_night: Sky
var _sky_room: Sky
var _moon: DirectionalLight3D
var _fx: WhiskerEffects
var _alley := Node3D.new()
var _room_set: Node3D
var _cat: Node3D
var _cat_anim: AnimationPlayer
var _dog: Node3D
var _dog_anim: AnimationPlayer
var _windows: Array[Dictionary] = []  ## {node, glow: MeshInstance3D, light: OmniLight3D, left: Node3D, right: Node3D, open: float}
var _washing: Array[Dictionary] = []  ## {node, line, x}
var _shoes := {}  ## index -> node (rebuilt each frame from the engine list)
var _shoe_pool: Array[Node3D] = []
var _room_things := {}  ## per-room entity nodes
var _sets := {}  ## room kind -> {node, things}, built once
var _warm := 0  ## frames drawn since the start (the prebuilt rooms hide after the first few)
var _cat_z := Z_STREET
var _time := 0.0
var _shake := 0.0
var _cam_alley := Transform3D()
var _cam_room := Transform3D()
var _cam_hearts := Transform3D()
var _catch_t := 0.0
var _land_t := 0.0


func _ready() -> void:
	_build_world()
	_fx = WhiskerEffects.new()
	add_child(_fx)
	add_child(_alley)
	_build_alley()
	_prebuild_rooms()
	game.started.connect(_on_started)
	if game.engine:
		_on_started(game.engine)


func _on_started(e: WhiskerEngine) -> void:
	if not e.event.is_connected(_on_event):
		e.event.connect(_on_event)
	_leave_room_set()


# ------------------------------------------------------------------ world

func _build_world() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.02, 0.03, 0.09)
	sky_mat.sky_horizon_color = Color(0.12, 0.13, 0.25)
	sky_mat.ground_horizon_color = Color(0.08, 0.08, 0.14)
	sky_mat.ground_bottom_color = Color(0.02, 0.02, 0.04)
	_sky_night = Sky.new()
	_sky_night.sky_material = sky_mat
	var room_mat := ProceduralSkyMaterial.new()  # indoors: what brass and glass reflect is a warm, dim room
	room_mat.sky_top_color = Color(0.2, 0.15, 0.1)
	room_mat.sky_horizon_color = Color(0.45, 0.33, 0.22)
	room_mat.ground_horizon_color = Color(0.3, 0.2, 0.13)
	room_mat.ground_bottom_color = Color(0.12, 0.08, 0.05)
	_sky_room = Sky.new()
	_sky_room.sky_material = room_mat
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_env.sky = _sky_night
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.3, 0.35, 0.55)
	_env.ambient_light_energy = 0.55
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.05
	_env.glow_enabled = true
	_env.glow_intensity = 0.6
	_env.glow_bloom = 0.1
	_env.glow_hdr_threshold = 0.9
	_env.ssao_enabled = true
	_env.fog_enabled = true
	_env.fog_light_color = Color(0.15, 0.17, 0.3)
	_env.fog_density = 0.004
	_env.ssr_enabled = true  # the puddles in the alley mirror the lamps (rooms turn it off)
	_env.ssr_max_steps = 48
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.2
	_env.adjustment_contrast = 1.1
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	_moon = DirectionalLight3D.new()
	_moon.rotation_degrees = Vector3(-38, 28, 0)
	_moon.light_color = Color(0.65, 0.72, 1.0)
	_moon.light_energy = 0.8
	_moon.shadow_enabled = true
	_moon.shadow_bias = 0.05
	_moon.directional_shadow_max_distance = 60.0
	add_child(_moon)
	_camera = Camera3D.new()
	_camera.fov = 36
	_camera.current = true
	add_child(_camera)
	_cam_alley = _fit(Vector3(E.W * 0.5, E.H * 0.5 - 0.3, 0), Vector2(E.W + 1.0, E.H + 0.5), Vector3(0, 0.12, 1))
	_cam_room = _fit(Vector3(8.0, 4.3, 0), Vector2(16.5, 9.2), Vector3(0, 0.1, 1))
	_cam_hearts = _fit(Vector3(8.0, 6.8, 0), Vector2(16.5, 14.2), Vector3(0, 0.05, 1))
	_camera.transform = _cam_alley


## A camera transform looking at `center` along `dir` from the distance that fits `size` (width, height).
func _fit(center: Vector3, size: Vector2, dir: Vector3) -> Transform3D:
	var aspect := 16.0 / 9.0
	var half_h := maxf(size.y * 0.5, size.x * 0.5 / aspect) * 1.12  # room for the HUD
	var dist := half_h / tan(deg_to_rad(_camera.fov * 0.5))
	var t := Transform3D(Basis(), center + dir.normalized() * dist)
	return t.looking_at(center + Vector3(0, 0.4, 0))


func _scene(name: String) -> Node3D:
	var n: Node3D = (load(M + name + ".glb") as PackedScene).instantiate()
	_dress(n)
	return n


static func _dress(node: Node) -> void:
	var swap := {
		"wood": Pbr.local("planks", Color(0.75, 0.55, 0.38), 0.9),
		"wood_dark": Pbr.local("planks", Color(0.52, 0.33, 0.21), 1.3),
		"metal": Pbr.local("metal", Color(0.6, 0.62, 0.66), 1.2, 0.8, 0.6),
	}
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and swap.has(mat.resource_name):
				m.set_surface_override_material(i, swap[mat.resource_name])
			elif mat is BaseMaterial3D and mat.resource_name.ends_with("_vc"):
				(mat as BaseMaterial3D).vertex_color_use_as_albedo = true  # fur and clothes painted as vertex colours


func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


func _build_alley() -> void:
	var cobbles := Pbr.material("stone_bricks", Color(0.62, 0.6, 0.66), 0.8, 0.0, 0.55)
	var brick := Pbr.material("stone_bricks", Color(0.82, 0.46, 0.36), 0.45)
	var dark_wall := Pbr.material("dark_rock", Color(0.3, 0.3, 0.36), 1.0)
	# street, building, the neighbours' walls and a skyline
	_box(_alley, Vector3(E.W * 0.5, -0.25, -1.0), Vector3(E.W + 30, 0.5, 9.0), cobbles)
	_box(_alley, Vector3(E.W * 0.5, (ROOF_Y - 0.5) * 0.5, Z_WALL - 0.3), Vector3(E.W + 4, ROOF_Y + 0.5, 0.6), brick)
	_build_facade()
	_box(_alley, Vector3(-6.0, 5.0, Z_WALL + 1.0), Vector3(8, 10, 1), dark_wall)
	_box(_alley, Vector3(E.W + 6.0, 6.5, Z_WALL + 1.0), Vector3(8, 13, 1), dark_wall)
	var rng := RandomNumberGenerator.new()
	rng.seed = 44
	var sil := StandardMaterial3D.new()
	sil.albedo_color = Color(0.05, 0.05, 0.1)
	for i in 14:  # rooftops far behind, with a few lit windows
		var w := rng.randf_range(3.0, 6.0)
		var h := rng.randf_range(14.5, 19.5)
		var x := -12.0 + i * 4.2
		_box(_alley, Vector3(x, h * 0.5, -14.0), Vector3(w, h, 1.0), sil)
		for k in rng.randi_range(1, 4):
			var lit := StandardMaterial3D.new()
			lit.albedo_color = Color(1.0, 0.8, 0.45)
			lit.emission_enabled = true
			lit.emission = Color(1.0, 0.75, 0.4)
			lit.emission_energy_multiplier = rng.randf_range(0.6, 1.6)
			_box(_alley, Vector3(x + rng.randf_range(-w * 0.35, w * 0.35), rng.randf_range(4.0, h - 1.0), -13.4), Vector3(0.5, 0.7, 0.1), lit)
	var moon := MeshInstance3D.new()
	var ms := SphereMesh.new()
	ms.radius = 1.6
	ms.height = 3.2
	moon.mesh = ms
	var mm := StandardMaterial3D.new()
	mm.albedo_color = Color(0.95, 0.93, 0.8)
	mm.emission_enabled = true
	mm.emission = Color(1.0, 0.97, 0.85)
	mm.emission_energy_multiplier = 2.5
	moon.material_override = mm
	moon.position = Vector3(E.W - 3.0, E.H + 5.0, -20.0)
	_alley.add_child(moon)
	# fence panels
	var boards := Pbr.local("planks", Color(0.72, 0.52, 0.36), 1.0).duplicate() as StandardMaterial3D
	boards.uv1_scale = Vector3(1.4, 0.22, 1.4)  # the grain runs up the boards, not across them
	for i in int(E.W / 2.0):
		var f := _scene("fence")
		_recolor(f, "wood", boards)
		f.position = Vector3(1.0 + i * 2.0, 0, Z_FENCE)
		_alley.add_child(f)
	# trash cans
	for x in E.CAN_X:
		var c := _scene("trash_can")
		c.position = Vector3(x, 0, Z_CAN)
		c.set_meta("x", x)
		_alley.add_child(c)
	# washing lines between two poles, with the washing that rides them
	var rope := StandardMaterial3D.new()
	rope.albedo_color = Color(0.85, 0.82, 0.75)
	for i in E.LINE_Y.size():
		var y: float = E.LINE_Y[i]
		var r := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.025
		cm.bottom_radius = 0.025
		cm.height = E.W + 1.0
		r.mesh = cm
		r.material_override = rope
		r.rotation.z = PI * 0.5
		r.position = Vector3(E.W * 0.5, y, Z_LINE)
		_alley.add_child(r)
		for k in 7:
			var n := _scene(WASHING[(i + k) % WASHING.size()])
			_alley.add_child(n)
			_washing.append({"node": n, "line": i, "x": k * (E.W / 7.0) + i * 1.3})
	for x in [-0.3, E.W + 0.3]:
		_box(_alley, Vector3(x, (E.LINE_Y[2] + 0.4) * 0.5, Z_LINE), Vector3(0.18, E.LINE_Y[2] + 0.4, 0.18), Pbr.material("planks", Color(0.5, 0.36, 0.24), 2.0))
	# windows with shutters, a dark room behind and a warm light when open
	var frame_paint := StandardMaterial3D.new()
	frame_paint.albedo_color = Color(0.8, 0.77, 0.7)
	frame_paint.roughness = 0.55
	var shutter_paint := Pbr.local("planks", Color(0.32, 0.55, 0.45), 2.5, 0.0, 0.9)
	for i in E.WINDOW_X.size() * E.WINDOW_Y.size():
		var col := i % E.WINDOW_X.size()
		var row := i / E.WINDOW_X.size()
		var base := Vector3(E.WINDOW_X[col], E.WINDOW_Y[row], Z_WALL)
		var node := _scene("window")
		node.position = base
		_alley.add_child(node)
		var glow := MeshInstance3D.new()
		var gq := QuadMesh.new()
		gq.size = Vector2(1.6, 1.5)
		glow.mesh = gq
		var gm := ShaderMaterial.new()
		gm.shader = load("res://games/whisker/shaders/interior.gdshader")
		glow.material_override = gm
		glow.position = base + Vector3(0, 0.75, 0.012)
		_alley.add_child(glow)
		_recolor(node, "window_frame", frame_paint)
		var left := _scene("shutter")
		_recolor(left, "shutter", shutter_paint)
		left.position = base + Vector3(-0.8, 0, 0.05)
		_alley.add_child(left)
		var right := _scene("shutter")
		_recolor(right, "shutter", shutter_paint)
		right.position = base + Vector3(0.8, 0, 0.05)
		right.rotation.y = PI
		_alley.add_child(right)
		var light := OmniLight3D.new()
		light.position = base + Vector3(0, 0.8, 0.8)
		light.light_color = Color(1.0, 0.75, 0.45)
		light.omni_range = 4.0
		light.light_energy = 0.0
		_alley.add_child(light)
		_windows.append({"glow": glow, "light": light, "left": left, "right": right, "open": 0.0})
	# street lamps
	for x in [5.2, 18.8]:
		var l := _scene("lamp")
		l.position = Vector3(x, 0, Z_STREET + 0.9)
		_alley.add_child(l)
		var ol := OmniLight3D.new()
		ol.position = Vector3(x, 3.9, Z_STREET + 0.2)
		ol.light_color = Color(1.0, 0.78, 0.5)
		ol.light_energy = 2.2
		ol.omni_range = 9.0
		ol.shadow_enabled = true
		_alley.add_child(ol)
		var cone := MeshInstance3D.new()  # the lamp's light in the damp air
		var cq := QuadMesh.new()
		cq.size = Vector2(3.4, 3.9)
		cone.mesh = cq
		var cm := ShaderMaterial.new()
		cm.shader = load("res://games/whisker/shaders/beam.gdshader")
		cm.set_shader_parameter("tint", Color(1.0, 0.72, 0.4))
		cm.set_shader_parameter("strength", 0.4)
		cm.set_shader_parameter("spread", 0.85)
		cone.material_override = cm
		cone.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		cone.position = Vector3(x, 1.95, Z_STREET + 1.55)
		_alley.add_child(cone)
		var moths := CPUParticles3D.new()
		moths.amount = 7
		moths.lifetime = 1.4
		moths.preprocess = 2.0
		moths.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
		moths.emission_sphere_radius = 0.35
		moths.position = Vector3(x, 3.85, Z_STREET + 1.6)
		moths.spread = 180.0
		moths.gravity = Vector3.ZERO
		moths.initial_velocity_min = 0.3
		moths.initial_velocity_max = 0.9
		var mq := QuadMesh.new()
		mq.size = Vector2(0.06, 0.06)
		moths.mesh = mq
		moths.material_override = Fx.material("glow", Color(1.0, 0.85, 0.6, 0.8))
		_alley.add_child(moths)
	# the cat and the dog
	_cat = _scene("cat")
	_cat.scale = Vector3.ONE * 1.25
	add_child(_cat)
	_cat_anim = _cat.find_child("AnimationPlayer", true, false)
	_dog = _scene("bulldog")
	_dog.scale = Vector3.ONE * 1.3
	_alley.add_child(_dog)
	_dog_anim = _dog.find_child("AnimationPlayer", true, false)
	for p in [_cat_anim, _dog_anim]:
		for a in ["idle", "walk", "run", "swim", "fall"]:
			if p.has_animation(a):
				p.get_animation(a).loop_mode = Animation.LOOP_LINEAR
	for i in 6:
		var b := _scene("boot")
		b.visible = false
		b.scale = Vector3.ONE * 1.4
		_alley.add_child(b)
		_shoe_pool.append(b)


## Dresses the building: a stone cornice with dentils and a parapet, chimney stacks, drainpipes, soot and rain
## streaks on the brick, puddles in the street and the starry sky with the moon's halo behind the roofs.
func _build_facade() -> void:
	var stone := Pbr.material("sand", Color(0.85, 0.82, 0.78), 1.2)
	var brick := Pbr.material("stone_bricks", Color(0.62, 0.36, 0.3), 0.45)
	var w := E.W + 4.0
	var z := Z_WALL
	_box(_alley, Vector3(E.W * 0.5, ROOF_Y - 0.95, z + 0.12), Vector3(w, 0.22, 0.24), stone)
	_box(_alley, Vector3(E.W * 0.5, ROOF_Y - 0.62, z + 0.25), Vector3(w, 0.3, 0.5), stone)
	_box(_alley, Vector3(E.W * 0.5, ROOF_Y - 0.12, z - 0.05), Vector3(w, 0.24, 0.6), stone)
	var n := int(w / 0.42)
	for i in n:  # dentils
		_box(_alley, Vector3(-2.0 + (i + 0.5) * w / n, ROOF_Y - 0.8, z + 0.14), Vector3(0.2, 0.16, 0.2), stone)
	for cx in [2.5, 11.0, 20.5]:  # chimney stacks with pots
		_box(_alley, Vector3(cx, ROOF_Y + 0.9, z - 1.2), Vector3(1.4, 2.0, 0.9), brick)
		_box(_alley, Vector3(cx, ROOF_Y + 1.95, z - 1.2), Vector3(1.55, 0.14, 1.0), stone)
		for k in 2:
			var pot := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.13
			cm.bottom_radius = 0.17
			cm.height = 0.5
			cm.radial_segments = 12
			pot.mesh = cm
			pot.material_override = Pbr.material("soil", Color(0.85, 0.5, 0.35), 2.0)
			pot.position = Vector3(cx - 0.3 + k * 0.6, ROOF_Y + 2.27, z - 1.2)
			_alley.add_child(pot)
	var iron := Pbr.material("metal", Color(0.22, 0.24, 0.26), 2.0, 0.7, 0.8)
	for px in [1.5, 22.5]:  # drainpipes from the gutter to the street
		var pipe := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.08
		cm.bottom_radius = 0.08
		cm.height = ROOF_Y - 1.0
		cm.radial_segments = 12
		pipe.mesh = cm
		pipe.material_override = iron
		pipe.position = Vector3(px, (ROOF_Y - 1.0) * 0.5, z + 0.14)
		_alley.add_child(pipe)
		_box(_alley, Vector3(px, ROOF_Y - 1.25, z + 0.18), Vector3(0.36, 0.4, 0.3), iron)  # the hopper head
		for k in int((ROOF_Y - 1.5) / 1.6):
			_box(_alley, Vector3(px, 0.9 + k * 1.6, z + 0.12), Vector3(0.24, 0.06, 0.2), iron)
	var grime := MeshInstance3D.new()
	var gq := QuadMesh.new()
	gq.size = Vector2(w, ROOF_Y - 0.9)
	grime.mesh = gq
	var gm := ShaderMaterial.new()
	gm.shader = load("res://games/whisker/shaders/grime.gdshader")
	gm.set_shader_parameter("top", ROOF_Y - 1.05)
	grime.material_override = gm
	grime.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	grime.position = Vector3(E.W * 0.5, (ROOF_Y - 1.05) * 0.5, z + 0.004)
	_alley.add_child(grime)
	var wet := StandardMaterial3D.new()  # puddles catch the lamps
	wet.albedo_color = Color(0.04, 0.045, 0.06)
	wet.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR  # stays opaque, so screen-space reflections apply
	wet.alpha_scissor_threshold = 0.5
	wet.roughness = 0.0
	wet.metallic_specular = 1.0
	var disc := GradientTexture2D.new()
	disc.fill = GradientTexture2D.FILL_RADIAL
	disc.fill_from = Vector2(0.5, 0.5)
	disc.fill_to = Vector2(1.0, 0.5)
	var dg := Gradient.new()
	dg.set_color(0, Color(1, 1, 1, 1))
	dg.set_color(1, Color(1, 1, 1, 0))
	dg.add_point(0.7, Color(1, 1, 1, 0.9))
	disc.gradient = dg
	wet.albedo_texture = disc
	for pd in [Vector3(5.6, 0, 1.6), Vector3(10.2, 0, 1.9), Vector3(18.3, 0, 1.5)]:
		var pud := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(2.2, 0.9)
		pud.mesh = pm
		pud.material_override = wet
		pud.position = pd + Vector3(0, 0.006, 0)
		_alley.add_child(pud)
	var sky := MeshInstance3D.new()  # stars and the moon's halo, far behind the roofs
	var sq := QuadMesh.new()
	sq.size = Vector2(90.0, 40.0)
	sky.mesh = sq
	var sm := ShaderMaterial.new()
	sm.shader = load("res://games/whisker/shaders/night.gdshader")
	sm.set_shader_parameter("aspect", 2.25)
	sm.set_shader_parameter("moon", Vector2(0.62, 0.42))
	sm.set_shader_parameter("moon_size", 0.0)
	sm.set_shader_parameter("skyline", 3.0)
	sm.set_shader_parameter("sky_energy", 0.3)
	sky.material_override = sm
	sky.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	sky.position = Vector3(12.0, 18.0, -30.0)
	_alley.add_child(sky)


# ------------------------------------------------------------------ rooms

## Room sets are built once (from a template room of each kind) and reused: building one on the way in made the
## game stall. At start they are all drawn once behind the building, so their shaders compile during the loading
## screen, then hidden.
func _prebuild_rooms() -> void:
	var dummy := WhiskerEngine.new(1)
	for kind in 5:
		var r: WhiskerRoom = [FishbowlRoom, MiceRoom, BirdcageRoom, DogbowlsRoom, HeartsRoom][kind].new()
		r.kind = kind
		r.setup(dummy)
		var set := _build_room_set(r)
		set["node"].position = Vector3(0, 0, -60)  # behind the building: drawn (and compiled) but unseen
		_sets[kind] = set
		r.cleanup(dummy)


func _enter_room_set(e: WhiskerEngine) -> void:
	_leave_room_set()
	_alley.visible = false
	var r := e.room
	var set: Dictionary = _sets[r.kind]
	_room_set = set["node"]
	_room_things = set["things"]
	_room_set.position = Vector3.ZERO
	_room_set.visible = true
	_reset_room_things(r)
	_env.ambient_light_color = Color(0.5, 0.42, 0.38)
	_env.ambient_light_energy = 0.4
	_env.sky = _sky_room
	_env.ssr_enabled = false
	_moon.visible = false


## An eel that is easy to spot: bigger, with crackling sparks and a flickering blue glow.
func _make_eel() -> Node3D:
	var n := _scene("eel")
	n.scale = Vector3.ONE * 2.0
	var sparks := CPUParticles3D.new()
	sparks.amount = 24
	sparks.lifetime = 0.25
	sparks.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	sparks.emission_box_extents = Vector3(0.6, 0.1, 0.1)
	sparks.spread = 180.0
	sparks.initial_velocity_min = 0.5
	sparks.initial_velocity_max = 1.5
	sparks.gravity = Vector3.ZERO
	var q := QuadMesh.new()
	q.size = Vector2(0.08, 0.08)
	sparks.mesh = q
	sparks.material_override = Fx.material("glow", Color(0.6, 0.85, 1.0))
	sparks.scale_amount_curve = Fx.size_curve(false)
	n.add_child(sparks)
	var glow := OmniLight3D.new()
	glow.light_color = Color(0.5, 0.8, 1.0)
	glow.light_energy = 1.5
	glow.omni_range = 2.2
	glow.name = "Glow"
	n.add_child(glow)
	return n


func _reset_room_things(r: WhiskerRoom) -> void:
	var t := _room_things
	match r.kind:
		E.RoomKind.FISHBOWL:
			var fr := r as FishbowlRoom
			for pool in ["fish", "eels"]:
				var need: int = fr.fish.size() if pool == "fish" else fr.eels.size()
				while t[pool].size() < need:
					var n := _scene("goldfish") if pool == "fish" else _make_eel()
					if pool == "fish":
						n.scale = Vector3.ONE * 1.6
					_room_set.add_child(n)
					t[pool].append(n)
				for i in t[pool].size():
					t[pool][i].visible = i < need
		E.RoomKind.MICE:
			for n in t["mice"].values():
				n.queue_free()
			t["mice"].clear()
		E.RoomKind.BIRDCAGE:
			(t["chain"] as Node3D).visible = true
			(t["bird"] as Node3D).visible = true
		E.RoomKind.HEARTS:
			for a in t["arrows"]:
				a.visible = false
	(t["broom"] as Node3D).visible = false


## Per room kind (FISHBOWL, MICE, BIRDCAGE, DOGBOWLS, HEARTS): wallpaper, curtains, rug (field, border) and the
## wall dressing: [model, x, y, painting style] (y 0 = on the floor, against the wall). Placed around the furniture,
## never on a walkable top.
const ROOM_LOOK := [
	{"paper": Color(0.3, 0.46, 0.5), "curtain": Color(0.45, 0.08, 0.1), "rug": [Color(0.5, 0.13, 0.12), Color(0.12, 0.16, 0.3)], "pendant": 8.0,
		"decor": [["frame_tall", 4.9, 7.4, 1], ["frame_wide", 14.2, 5.2, 0], ["clock", 11.6, 7.7], ["sconce", 3.9, 5.7], ["sconce", 12.1, 5.7], ["plant", 12.1, 0.0]]},
	{"paper": Color(0.7, 0.52, 0.3), "curtain": Color(0.12, 0.3, 0.2), "rug": [Color(0.2, 0.3, 0.42), Color(0.5, 0.14, 0.12)], "pendant": 8.0,
		"decor": [["frame_tall", 3.2, 4.8, 1], ["frame_wide", 12.9, 5.6, 3], ["clock", 15.0, 6.3], ["sconce", 5.3, 6.0], ["sconce", 10.7, 6.0], ["plant", 13.0, 0.0]]},
	{"paper": Color(0.55, 0.37, 0.45), "curtain": Color(0.62, 0.45, 0.14), "rug": [Color(0.18, 0.3, 0.25), Color(0.45, 0.12, 0.2)], "pendant": 8.2,
		"decor": [["frame_tall", 3.6, 4.7, 2], ["frame_wide", 9.6, 5.8, 0], ["clock", 7.1, 5.8], ["frame_tall", 15.0, 4.7, 1], ["sconce", 13.5, 5.6], ["plant", 5.75, 0.0]]},
	{"paper": Color(0.44, 0.52, 0.36), "curtain": Color(0.42, 0.1, 0.16), "rug": [Color(0.55, 0.35, 0.15), Color(0.15, 0.22, 0.35)], "pendant": 8.7,
		"decor": [["frame_tall", 3.4, 5.1, 2], ["frame_wide", 13.6, 5.3, 0], ["clock", 6.4, 6.4], ["sconce", 4.6, 6.4], ["sconce", 11.1, 6.2], ["plant", 2.2, 0.0]]},
	{"paper": Color(0.34, 0.13, 0.27), "curtain": Color(0.5, 0.05, 0.12), "rug": [Color(0.45, 0.08, 0.2), Color(0.2, 0.08, 0.2)], "pendant": -1.0,
		"decor": [["frame_tall", 1.2, 10.4, 2], ["frame_tall", 14.8, 10.4, 1], ["sconce", 3.0, 6.6], ["sconce", 13.0, 6.6], ["plant", 14.8, 0.0]]},
]
const WALL_Z := -1.05  ## the room's back wall face
const ENTRY_WINDOW := Rect2(0.3, 5.4, 1.8, 1.8)  ## the window the cat comes in through (opening)
const HEARTS_WINDOW := Rect2(5.48, 8.4, 5.04, 5.04)  ## the tall window behind the lady cat


func _build_room_set(r: WhiskerRoom) -> Dictionary:
	var saved_set := _room_set
	var saved_things := _room_things
	_room_set = Node3D.new()
	_room_things = {}
	add_child(_room_set)
	var look: Dictionary = ROOM_LOOK[r.kind]
	var hearts := r.kind == E.RoomKind.HEARTS
	_build_shell(look, hearts)
	# furniture where the engine's platforms are
	for p in r.platforms:
		var k: String = p["kind"]
		if k in ["floor", "cheese", "heart", "top"]:
			continue
		var rect: Rect2 = p["rect"]
		if rect.position.y > 0.1:  # a floating shelf: a moulded plank on two brass brackets
			_floating_shelf(rect)
			continue
		var name := k if ResourceLoader.exists(M + k + ".glb") else "cabinet"
		var n := _scene(name)
		n.position = Vector3(rect.get_center().x, 0, -0.2)
		var src := _natural_size(name)
		n.scale = Vector3(rect.size.x / src.x, rect.end.y / src.y, 1.0)
		_room_set.add_child(n)
	for d in look["decor"]:
		var n := _scene(d[0])
		var on_floor: bool = d[2] == 0.0
		n.position = Vector3(d[1], d[2], -0.75 if on_floor else WALL_Z)
		if d[0] == "plant":
			n.scale = Vector3.ONE * 1.3
		if d.size() > 3:
			_paint(n, d[3])
		_room_set.add_child(n)
		if d[0] == "sconce":
			var l := OmniLight3D.new()
			l.position = n.position + Vector3(0, 0.35, 0.45)
			l.light_color = Color(1.0, 0.72, 0.42)
			l.light_energy = 0.9
			l.omni_range = 3.2
			l.omni_attenuation = 1.6
			_room_set.add_child(l)
	_light_room(look, hearts)
	_room_things.clear()
	match r.kind:
		E.RoomKind.FISHBOWL:
			var bowl := _scene("bowl")
			bowl.position = Vector3(FishbowlRoom.BOWL.get_center().x, FishbowlRoom.BOWL.position.y, 0.0)
			_room_set.add_child(bowl)
			var water := MeshInstance3D.new()
			var wb := BoxMesh.new()
			wb.size = Vector3(FishbowlRoom.BOWL.size.x - 0.1, FishbowlRoom.BOWL.size.y - 0.3, 1.5)
			water.mesh = wb
			var wm := StandardMaterial3D.new()
			wm.albedo_color = Color(0.3, 0.62, 0.8, 0.3)
			wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			wm.roughness = 0.04
			wm.metallic_specular = 0.9
			wm.normal_enabled = true
			wm.normal_texture = load("res://core/art/textures/water/normal.png")
			wm.normal_scale = 0.4
			wm.uv1_triplanar = true
			wm.uv1_scale = Vector3.ONE * 0.4
			wm.emission_enabled = true
			wm.emission = Color(0.05, 0.16, 0.22)
			water.material_override = wm
			water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			water.position = Vector3(FishbowlRoom.BOWL.get_center().x, FishbowlRoom.BOWL.position.y + wb.size.y * 0.5 + 0.2, 0.0)
			_room_set.add_child(water)
			var under := OmniLight3D.new()  # the water glows a little, and throws a cool light on the wall behind
			under.position = Vector3(FishbowlRoom.BOWL.get_center().x, FishbowlRoom.BOWL.position.y + 1.2, -0.3)
			under.light_color = Color(0.45, 0.8, 1.0)
			under.light_energy = 0.8
			under.omni_range = 5.0
			_room_set.add_child(under)
			var bubbles := CPUParticles3D.new()  # a stream of bubbles from the castle
			bubbles.amount = 24
			bubbles.lifetime = 2.6
			bubbles.preprocess = 3.0
			bubbles.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
			bubbles.emission_sphere_radius = 0.08
			bubbles.position = Vector3(FishbowlRoom.BOWL.get_center().x + 2.0, FishbowlRoom.BOWL.position.y + 1.3, -0.25)
			bubbles.direction = Vector3.UP
			bubbles.spread = 8.0
			bubbles.gravity = Vector3(0, 0.6, 0)
			bubbles.initial_velocity_min = 0.6
			bubbles.initial_velocity_max = 1.0
			var bs := SphereMesh.new()
			bs.radius = 0.04
			bs.height = 0.08
			bs.radial_segments = 8
			bs.rings = 4
			bubbles.mesh = bs
			bubbles.scale_amount_min = 0.6
			bubbles.scale_amount_max = 1.5
			var bmat := StandardMaterial3D.new()
			bmat.albedo_color = Color(0.85, 0.95, 1.0, 0.35)
			bmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			bmat.roughness = 0.0
			bmat.rim_enabled = true
			bmat.rim = 1.0
			bubbles.material_override = bmat
			_room_set.add_child(bubbles)
			var fr := r as FishbowlRoom
			_room_things["fish"] = []
			for f in fr.fish:
				var n := _scene("goldfish")
				n.scale = Vector3.ONE * 1.6
				_room_set.add_child(n)
				_room_things["fish"].append(n)
			_room_things["eels"] = []
			for eel in fr.eels:
				var n := _make_eel()
				_room_set.add_child(n)
				_room_things["eels"].append(n)
		E.RoomKind.MICE:
			var ch := _scene("cheese")
			ch.position = Vector3((MiceRoom.CHEESE_X.x + MiceRoom.CHEESE_X.y) * 0.5, 0, -0.3)
			_room_set.add_child(ch)
			for x in [MiceRoom.CHEESE_X.x, MiceRoom.CHEESE_X.y]:  # the mouse holes in the skirting board
				_mouse_hole(x)
			_room_things["mice"] = {}
		E.RoomKind.BIRDCAGE:
			var cage := _scene("cage")
			_room_set.add_child(cage)
			_room_things["cage"] = cage
			var top := BirdcageRoom.CAGE.end.y + 0.2
			var chain := _box(_room_set, Vector3(BirdcageRoom.CAGE.get_center().x, (top + 10.2) * 0.5, 0), Vector3(0.04, 10.2 - top, 0.04), Pbr.material("metal", Color(0.9, 0.75, 0.4), 2.0, 1.0, 0.4))
			_room_things["chain"] = chain
			var bird := _scene("canary")
			bird.scale = Vector3.ONE * 1.6
			_room_set.add_child(bird)
			_room_things["bird"] = bird
		E.RoomKind.DOGBOWLS:
			_room_things["bowls"] = []
			_room_things["dogs"] = []
			for i in DogbowlsRoom.BOWL_X.size():
				var b := _scene("milk_bowl")
				b.position = Vector3(DogbowlsRoom.BOWL_X[i], 0, 0.6)
				b.scale = Vector3.ONE * 1.3
				_room_set.add_child(b)
				var milk := MeshInstance3D.new()
				var disc := CylinderMesh.new()
				disc.top_radius = 0.4
				disc.bottom_radius = 0.36
				disc.height = 0.03
				milk.mesh = disc
				var mm := StandardMaterial3D.new()
				mm.albedo_color = Color(0.97, 0.96, 0.92)
				mm.roughness = 0.15
				mm.subsurf_scatter_enabled = true
				mm.subsurf_scatter_strength = 0.4
				milk.material_override = mm
				milk.position = Vector3(0, 0.18, 0)
				b.add_child(milk)
				_room_things["bowls"].append({"bowl": b, "milk": milk})
				var dog := _scene("bulldog")
				dog.scale = Vector3.ONE * 1.3
				_room_set.add_child(dog)
				var zz := Label3D.new()
				zz.text = "z"
				var sf := SystemFont.new()
				sf.font_names = PackedStringArray(["DejaVu Sans", "Arial", "Helvetica", "sans-serif"])
				sf.font_weight = 700
				zz.font = sf
				zz.font_size = 96
				zz.modulate = Color(0.85, 0.9, 1.0)
				zz.outline_size = 18
				zz.outline_modulate = Color(0.1, 0.12, 0.25, 0.8)
				zz.billboard = BaseMaterial3D.BILLBOARD_ENABLED
				_room_set.add_child(zz)
				_room_things["dogs"].append({"node": dog, "anim": dog.find_child("AnimationPlayer", true, false), "zz": zz})
		E.RoomKind.HEARTS:
			var hr := r as HeartsRoom
			_room_things["hearts"] = []
			for h in hr.hearts:
				var n := _scene("heart")
				_room_set.add_child(n)
				_room_things["hearts"].append(n)
			_balcony()
			var lady := _scene("lady_cat")
			lady.position = Vector3(hr.lady.x, HeartsRoom.TOP_Y, 0.2)
			lady.scale = Vector3.ONE * 1.25
			lady.rotation.y = -PI * 0.3
			_room_set.add_child(lady)
			var la: AnimationPlayer = lady.find_child("AnimationPlayer", true, false)
			la.get_animation("idle").loop_mode = Animation.LOOP_LINEAR
			la.play("idle")
			_room_things["lady"] = lady
			_room_things["arrows"] = []
			for i in 4:
				var a := _scene("arrow")
				a.scale = Vector3.ONE * 1.5
				a.visible = false
				_room_set.add_child(a)
				_room_things["arrows"].append(a)
			var rose := OmniLight3D.new()  # a rosy glow around the lady
			rose.position = Vector3(8, HeartsRoom.TOP_Y + 1.0, 2.0)
			rose.light_color = Color(1.0, 0.6, 0.8)
			rose.light_energy = 2.0
			rose.omni_range = 8.0
			_room_set.add_child(rose)
	var broom := _scene("broom")
	broom.scale = Vector3.ONE * 1.6
	broom.visible = false
	_room_set.add_child(broom)
	_room_things["broom"] = broom
	var out := {"node": _room_set, "things": _room_things}
	_room_set = saved_set
	_room_things = saved_things
	return out


## Walls (with the window openings cut out), side walls or stage drapes, floor, skirting, cornice and ceiling, the
## windows with their curtains and the night behind them, and a rug.
func _build_shell(look: Dictionary, hearts: bool) -> void:
	var ceil_y := 16.2 if hearts else 10.2
	var x0 := -9.0 if hearts else -0.8
	var x1 := 25.0 if hearts else 16.8
	var paper_col: Color = look["paper"]
	var paper := _paper(paper_col, false, ceil_y)
	var holes: Array[Rect2] = [ENTRY_WINDOW]
	if hearts:
		holes.append(HEARTS_WINDOW)
	_wall_with_holes(x0, x1, ceil_y, holes, paper)
	var floor_mat := Pbr.material("planks", Color(0.62, 0.42, 0.28), 0.55, 0.0, 0.8)
	_box(_room_set, Vector3((x0 + x1) * 0.5, -0.25, 1.5), Vector3(x1 - x0 + 2.0, 0.5, 6.0), floor_mat)
	var trim := StandardMaterial3D.new()
	trim.albedo_color = Color(0.9, 0.87, 0.8)
	trim.roughness = 0.4
	var ceiling := StandardMaterial3D.new()
	ceiling.albedo_color = Color(0.85, 0.8, 0.72)
	ceiling.roughness = 0.9
	# skirting board with a top bead, cornice and a ceiling
	_box(_room_set, Vector3((x0 + x1) * 0.5, 0.18, WALL_Z + 0.04), Vector3(x1 - x0, 0.36, 0.08), trim)
	_rod(Vector3(x0, 0.37, WALL_Z + 0.07), Vector3(x1, 0.37, WALL_Z + 0.07), 0.03, trim)
	_box(_room_set, Vector3((x0 + x1) * 0.5, ceil_y - 0.2, WALL_Z + 0.12), Vector3(x1 - x0, 0.4, 0.24), trim)
	_box(_room_set, Vector3((x0 + x1) * 0.5, ceil_y - 0.48, WALL_Z + 0.05), Vector3(x1 - x0, 0.16, 0.1), trim)
	_rod(Vector3(x0, ceil_y - 0.4, WALL_Z + 0.17), Vector3(x1, ceil_y - 0.4, WALL_Z + 0.17), 0.05, trim)
	_box(_room_set, Vector3((x0 + x1) * 0.5, ceil_y + 0.1, 2.0), Vector3(x1 - x0 + 2.0, 0.2, 7.0), ceiling)
	if not hearts:  # side walls: the corners of the room
		var side := _paper(paper_col.darkened(0.12), true, ceil_y)
		for sx in [x0, x1]:
			var dir: float = 1.0 if sx < 8.0 else -1.0
			_box(_room_set, Vector3(sx - dir * 0.15, ceil_y * 0.5, 1.8), Vector3(0.3, ceil_y, 6.0), side)
			_box(_room_set, Vector3(sx + dir * 0.04, 0.18, 1.8), Vector3(0.08, 0.36, 6.0), trim)
			_box(_room_set, Vector3(sx + dir * 0.12, ceil_y - 0.2, 1.8), Vector3(0.24, 0.4, 6.0), trim)
	# windows: frame, glass, curtains and the night outside
	var velvet := StandardMaterial3D.new()
	velvet.albedo_color = look["curtain"]
	velvet.roughness = 0.9
	velvet.rim_enabled = true  # the sheen of velvet
	velvet.rim = 0.6
	velvet.rim_tint = 0.4
	for i in holes.size():
		var h: Rect2 = holes[i]
		var s := h.size.x / 1.8
		var night := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(h.size.x * 2.6, h.size.y * 2.0)
		night.mesh = q
		var nm := ShaderMaterial.new()
		nm.shader = load("res://games/whisker/shaders/night.gdshader")
		nm.set_shader_parameter("aspect", q.size.x / q.size.y)
		nm.set_shader_parameter("seed", float(i) * 3.0 + 1.0)
		nm.set_shader_parameter("moon", Vector2(0.62, 0.3) if i == 0 else Vector2(0.5, 0.32))
		nm.set_shader_parameter("moon_size", 0.07 if i == 0 else 0.1)
		night.material_override = nm
		night.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		night.position = Vector3(h.get_center().x, h.get_center().y, WALL_Z - 1.6 * s)
		_room_set.add_child(night)
		var glass := MeshInstance3D.new()
		var gq := QuadMesh.new()
		gq.size = h.size
		glass.mesh = gq
		var gm := StandardMaterial3D.new()
		gm.albedo_color = Color(0.5, 0.6, 0.8, 0.04)
		gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		gm.roughness = 0.06
		gm.metallic_specular = 0.35
		glass.material_override = gm
		glass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		glass.position = Vector3(h.get_center().x, h.get_center().y, WALL_Z - 0.27 * s)
		_room_set.add_child(glass)
		var win := _scene("room_window")
		win.position = Vector3(h.get_center().x, h.position.y, WALL_Z)
		win.scale = Vector3.ONE * s
		_room_set.add_child(win)
		for side in [-1.0, 1.0]:
			var c := _scene("curtain" if side < 0.0 else "curtain_r")
			c.scale = Vector3(s, 0.8 * s, s)
			c.position = Vector3(h.get_center().x + side * 1.35 * s, h.position.y + 2.32 * s - 2.4 * s, WALL_Z + 0.25 * s)
			_recolor(c, "curtain", velvet)
			_room_set.add_child(c)
	if hearts:  # heavy stage drapes frame the tower on both sides
		for side in [-1.0, 1.0]:
			var c := _scene("drape" if side < 0.0 else "drape_r")
			c.position = Vector3(8.0 + side * 11.0, -0.2, 0.8)
			_recolor(c, "curtain", velvet)
			_room_set.add_child(c)
		_box(_room_set, Vector3(8.0, ceil_y - 0.9, 0.9), Vector3(34.0, 1.4, 0.3), velvet)  # the valance
	# the rug
	var rug := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(12.0, 3.0)
	rug.mesh = pm
	var rm := ShaderMaterial.new()
	rm.shader = load("res://games/whisker/shaders/rug.gdshader")
	rm.set_shader_parameter("field", look["rug"][0])
	rm.set_shader_parameter("border", look["rug"][1])
	rm.set_shader_parameter("size", pm.size)
	rug.material_override = rm
	rug.position = Vector3(8.0, 0.012, 0.45)
	_room_set.add_child(rug)
	if look["pendant"] > 0.0:
		var p := _scene("pendant")
		p.position = Vector3(look["pendant"], ceil_y - 1.15, 0.9)
		for mi in p.find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_room_set.add_child(p)


## The light projector for the moonlight: the panes of a sash window, with a soft edge.
func _panes_texture() -> ImageTexture:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	for j in n:
		for i in n:
			var u := float(i) / (n - 1)
			var v := float(j) / (n - 1)
			var bar := absf(fmod(u * 3.0, 1.0) - 0.5) > 0.44 or absf(fmod(v * 2.0, 1.0) - 0.5) > 0.44
			var edge := clampf(minf(minf(u, 1.0 - u), minf(v, 1.0 - v)) * 12.0, 0.0, 1.0)
			var k := (0.08 if bar else 1.0) * edge
			img.set_pixel(i, j, Color(k, k, k))
	return ImageTexture.create_from_image(img)


func _paper(col: Color, along_z: bool, ceil_y: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://games/whisker/shaders/wallpaper.gdshader")
	m.set_shader_parameter("base", col)
	m.set_shader_parameter("stripe", col.lightened(0.12))
	m.set_shader_parameter("motif", col.darkened(0.28))
	m.set_shader_parameter("wainscot", Color(0.9, 0.87, 0.8))
	m.set_shader_parameter("along_z", along_z)
	m.set_shader_parameter("ceiling", ceil_y)
	return m


## The back wall from x0 to x1, with rectangular openings (which must not overlap in x).
func _wall_with_holes(x0: float, x1: float, top: float, holes: Array[Rect2], mat: Material) -> void:
	var z := WALL_Z - 0.15
	var xs: Array[float] = [x0, x1]
	for h in holes:
		xs.append(h.position.x)
		xs.append(h.end.x)
	xs.sort()
	for i in xs.size() - 1:
		var a := xs[i]
		var b := xs[i + 1]
		if b - a < 0.001:
			continue
		var cx := (a + b) * 0.5
		var hole := Rect2()
		for h in holes:
			if cx > h.position.x and cx < h.end.x:
				hole = h
		if hole.size == Vector2.ZERO:
			_box(_room_set, Vector3(cx, top * 0.5, z), Vector3(b - a, top, 0.3), mat)
		else:
			_box(_room_set, Vector3(cx, hole.position.y * 0.5, z), Vector3(b - a, hole.position.y, 0.3), mat)
			_box(_room_set, Vector3(cx, (hole.end.y + top) * 0.5, z), Vector3(b - a, top - hole.end.y, 0.3), mat)


func _rod(a: Vector3, b: Vector3, radius: float, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = radius
	c.bottom_radius = radius
	c.height = a.distance_to(b)
	c.radial_segments = 12
	c.rings = 1
	mi.mesh = c
	mi.material_override = mat
	mi.position = (a + b) * 0.5
	mi.basis = Basis(Quaternion(Vector3.UP, (b - a).normalized()))
	_room_set.add_child(mi)
	return mi


## Swaps every surface using the named material (from the Blender script) for `mat`.
func _recolor(node: Node, mat_name: String, mat: Material) -> void:
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var sm := m.mesh.surface_get_material(i)
			if sm and sm.resource_name == mat_name:
				m.set_surface_override_material(i, mat)


func _paint(frame: Node3D, style: int) -> void:
	var m := ShaderMaterial.new()
	m.shader = load("res://games/whisker/shaders/painting.gdshader")
	m.set_shader_parameter("style", style)
	_recolor(frame, "canvas", m)


func _floating_shelf(rect: Rect2) -> void:
	var wood := Pbr.material("planks", Color(0.5, 0.32, 0.2), 2.0)
	_box(_room_set, Vector3(rect.get_center().x, rect.end.y - 0.1, -0.6), Vector3(rect.size.x, 0.2, 1.0), wood)
	_box(_room_set, Vector3(rect.get_center().x, rect.end.y - 0.24, -0.62), Vector3(rect.size.x - 0.12, 0.08, 0.9), wood)
	var brass := Pbr.material("metal", Color(0.95, 0.72, 0.38), 2.0, 1.0, 0.45)
	for sx in [-0.33, 0.33]:
		var x: float = rect.get_center().x + sx * rect.size.x
		_box(_room_set, Vector3(x, rect.end.y - 0.55, WALL_Z + 0.03), Vector3(0.08, 0.7, 0.06), brass)
		var arm := _box(_room_set, Vector3(x, rect.end.y - 0.45, -0.7), Vector3(0.06, 0.06, 0.75), brass)
		arm.rotation.x = -0.75
		_box(_room_set, Vector3(x, rect.end.y - 0.26, -0.62), Vector3(0.07, 0.05, 0.9), brass)


func _mouse_hole(x: float) -> void:
	var dark := StandardMaterial3D.new()
	dark.albedo_color = Color(0.02, 0.015, 0.01)
	dark.roughness = 1.0
	var hole := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.22
	cm.bottom_radius = 0.22
	cm.height = 0.1
	hole.mesh = cm
	hole.material_override = dark
	hole.rotation.x = PI * 0.5
	hole.position = Vector3(x, 0.02, WALL_Z + 0.06)
	_room_set.add_child(hole)
	var trim := StandardMaterial3D.new()
	trim.albedo_color = Color(0.55, 0.42, 0.3)
	var arch := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.22
	tm.outer_radius = 0.27
	arch.mesh = tm
	arch.material_override = trim
	arch.rotation.x = PI * 0.5
	arch.position = Vector3(x, 0.02, WALL_Z + 0.08)
	_room_set.add_child(arch)


## The lady cat's balcony at the top of the heart tower: a stone slab on corbels, a balustrade behind her.
func _balcony() -> void:
	var stone := StandardMaterial3D.new()  # pale pink marble
	stone.albedo_color = Color(0.95, 0.86, 0.86)
	stone.roughness = 0.35
	stone.normal_enabled = true
	stone.normal_texture = load("res://core/art/textures/rock/normal.jpg")
	stone.normal_scale = 0.3
	stone.uv1_triplanar = true
	var y := HeartsRoom.TOP_Y
	_box(_room_set, Vector3(8.0, y - 0.2, 0), Vector3(2.8, 0.4, 1.3), stone)
	_box(_room_set, Vector3(8.0, y - 0.03, 0), Vector3(3.0, 0.08, 1.45), stone)
	for sx in [-1.1, -0.4, 0.4, 1.1]:
		_box(_room_set, Vector3(8.0 + sx, y - 0.62, -0.1), Vector3(0.28, 0.5, 0.9), stone)  # corbels
	_box(_room_set, Vector3(8.0, y + 0.95, -0.55), Vector3(3.0, 0.12, 0.3), stone)
	for i in 9:
		var b := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.07
		cm.bottom_radius = 0.1
		cm.height = 0.85
		cm.radial_segments = 12
		b.mesh = cm
		b.material_override = stone
		b.position = Vector3(6.75 + i * 0.31, y + 0.45, -0.55)
		_room_set.add_child(b)


## Layered light: the pendant (or the moon, in the tower) as key with shadows, a soft warm fill from the front,
## moonlight falling through the window, and dust drifting in the air.
func _light_room(look: Dictionary, hearts: bool) -> void:
	var px: float = look["pendant"]
	if px > 0.0:
		var key := OmniLight3D.new()
		key.position = Vector3(px, 10.2 - 1.3, 0.9)
		key.light_color = Color(1.0, 0.78, 0.52)
		key.light_energy = 2.7
		key.omni_range = 15.0
		key.omni_attenuation = 0.9
		key.shadow_enabled = true
		key.shadow_blur = 1.5
		_room_set.add_child(key)
	var fill := OmniLight3D.new()
	fill.position = Vector3(8, 6.0 if not hearts else 9.0, 7.0)
	fill.light_color = Color(1.0, 0.86, 0.7)
	fill.light_energy = 1.1 if not hearts else 1.6
	fill.omni_range = 22.0
	fill.omni_attenuation = 0.6
	_room_set.add_child(fill)
	var h := HEARTS_WINDOW if hearts else ENTRY_WINDOW
	var s := h.size.x / 1.8
	var from := Vector3(h.get_center().x, h.get_center().y + 0.3 * s, WALL_Z + 0.05)
	var target := Vector3(h.get_center().x + (0.0 if hearts else 2.2), 0.0, 0.4)
	var moon := SpotLight3D.new()  # moonlight through the glazing bars, a pattern of panes on the floor
	moon.transform = Transform3D(Basis.looking_at(target - from), from)
	moon.light_color = Color(0.6, 0.7, 1.0)
	moon.light_energy = 5.0
	moon.spot_range = 16.0
	moon.spot_angle = 16.0 if not hearts else 22.0
	moon.spot_attenuation = 0.4
	moon.spot_angle_attenuation = 0.6
	moon.light_projector = _panes_texture()
	moon.shadow_enabled = true
	_room_set.add_child(moon)
	var beam := MeshInstance3D.new()  # and the shaft of light itself, with the dust drifting in it
	var bq := QuadMesh.new()
	var length := from.distance_to(target)
	bq.size = Vector2(1.7 * s, length)
	beam.mesh = bq
	var bm := ShaderMaterial.new()
	bm.shader = load("res://games/whisker/shaders/beam.gdshader")
	bm.set_shader_parameter("strength", 0.14 if not hearts else 0.1)
	beam.material_override = bm
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var y := (from - target).normalized()
	var x := y.cross(Vector3(0, 0, 1)).normalized()
	beam.transform = Transform3D(Basis(x, y, x.cross(y)), (from + target) * 0.5)
	_room_set.add_child(beam)
	var motes := CPUParticles3D.new()
	motes.amount = 70
	motes.lifetime = 12.0
	motes.preprocess = 12.0
	motes.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	motes.emission_box_extents = Vector3(7.5, 4.5 if not hearts else 7.0, 1.2)
	motes.position = Vector3(8, 5.0 if not hearts else 7.5, 0.6)
	motes.direction = Vector3(0.2, 1, 0)
	motes.spread = 180.0
	motes.gravity = Vector3(0, -0.01, 0)
	motes.initial_velocity_min = 0.02
	motes.initial_velocity_max = 0.1
	var q := QuadMesh.new()
	q.size = Vector2(0.035, 0.035)
	motes.mesh = q
	motes.material_override = Fx.material("glow", Color(1.0, 0.9, 0.72, 0.45))
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0))
	ramp.add_point(0.2, Color(1, 1, 1, 1))
	ramp.add_point(0.8, Color(1, 1, 1, 1))
	ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0))
	motes.color_ramp = ramp
	_room_set.add_child(motes)


func _natural_size(name: String) -> Vector2:
	match name:
		"chair": return Vector2(1.4, 1.8)
		"cabinet": return Vector2(1.6, 3.4)
		"dresser": return Vector2(1.6, 2.4)
		"table": return Vector2(7.2, 1.0)
		"stool": return Vector2(1.6, 1.4)
		"shelf": return Vector2(1.5, 2.8)
		"bookcase": return Vector2(1.4, 3.0)
	return Vector2(1.0, 1.0)


func _leave_room_set() -> void:
	if _room_set:
		_room_set.visible = false
		_room_set = null
	_room_things = {}
	_alley.visible = true
	_env.ambient_light_color = Color(0.3, 0.35, 0.55)
	_env.ambient_light_energy = 0.55
	_env.sky = _sky_night
	_env.ssr_enabled = true
	_moon.visible = true


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"enter_room":
			_enter_room_set(e)
			_camera.transform = _room_cam(e)
		"leave_room":
			_leave_room_set()
			_camera.transform = _cam_alley
		"bounce":
			for c in _alley.get_children():
				if c.has_meta("x") and is_equal_approx(c.get_meta("x"), d["x"]):
					var tw := create_tween()
					tw.tween_property(c, "scale", Vector3(1.1, 0.85, 1.1), 0.06)
					tw.tween_property(c, "scale", Vector3.ONE, 0.25).set_trans(Tween.TRANS_ELASTIC)
		"land":
			_land_t = 0.18
			if d["kind"] == "ground":
				_fx.dust(_v(d["pos"], Z_STREET), 5)
		"shoe_hit":
			_fx.stars(_v(d["pos"], _cat_z))
			_shake = 0.4
		"shoe_land":
			_fx.dust(_v(d["pos"], Z_STREET), 6)
		"death":
			_fx.stars(_v(d["pos"], _cat_z))
			_shake = 0.6
		"splash":
			if _room_set:
				_fx.splash(Vector3(d["pos"].x, FishbowlRoom.BOWL.end.y, 0.3))
		"catch":
			_catch_t = 0.5
			_fx.sparkle(Vector3(d["pos"].x, d["pos"].y + 0.3, 0.4))
		"zap":
			_fx.zap(Vector3(d["pos"].x, d["pos"].y, 0.2))
			_shake = 0.5
		"cage_crash":
			_fx.dust(Vector3(d["pos"].x, 0.2, 0.2), 14)
			_shake = 0.4
		"room_won":
			_fx.confetti(Vector3(8, 6, 1))


func _room_cam(e: WhiskerEngine) -> Transform3D:
	return _cam_hearts if e.room and e.room.kind == E.RoomKind.HEARTS else _cam_room


func _v(p: Vector2, z: float) -> Vector3:
	return Vector3(p.x, p.y, z)


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	_warm += 1
	if _warm == 3:  # the loading screen has drawn them: park the prebuilt rooms out of sight
		for set in _sets.values():
			if set["node"] != _room_set:
				set["node"].visible = false
				set["node"].position = Vector3.ZERO
	var e := game.engine
	if e == null:
		return
	_time += delta
	_catch_t = maxf(0.0, _catch_t - delta)
	_land_t = maxf(0.0, _land_t - delta)
	_update_cat(e, delta)
	if _room_set:
		_update_room(e, delta)
	else:
		_update_alley(e, delta)
	_shake = maxf(0.0, _shake - delta * 2.0)
	var base := _room_cam(e) if _room_set else _cam_alley
	var s := _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var sway := Vector3(sin(_time * 0.2) * 0.05, sin(_time * 0.15) * 0.03, 0)  # barely: fine textures shimmer when the view moves
	_camera.transform = Transform3D(base.basis, base.origin + sway + Vector3(sin(_time * 60.0), sin(_time * 53.0), 0) * s)


func _layer_z(e: WhiskerEngine) -> float:
	if e.room:
		return 0.2
	if e.cat.on_ground:
		match e.cat.ground.get("kind", ""):
			"ground": return Z_STREET
			"can": return Z_CAN
			"fence": return Z_FENCE
			"line": return Z_LINE
	var y := e.cat.pos.y
	if y > E.LINE_Y[0] - 0.2:
		return Z_LINE
	if y > E.FENCE_TOP - 0.2:
		return Z_FENCE
	return _cat_z


func _update_cat(e: WhiskerEngine, delta: float) -> void:
	_cat_z = lerpf(_cat_z, _layer_z(e), 1.0 - exp(-delta * 6.0))
	var swimming: bool = e.room != null and e.room.swimming(e)
	_cat.position = Vector3(e.cat.pos.x, e.cat.pos.y, _cat_z)
	var yaw := PI * 0.5 * e.facing
	_cat.rotation.y = lerp_angle(_cat.rotation.y, yaw, 1.0 - exp(-delta * 14.0))
	var state := "idle"
	var speed := 1.0
	if e.phase == E.Phase.DYING:
		state = "die"
	elif swimming:
		state = "swim"
	elif _catch_t > 0.0:
		state = "catch"
	elif not e.cat.on_ground:
		state = "jump" if e.cat.vel.y > 0.0 else "fall"
	elif absf(e.cat.vel.x) > 0.1:
		state = "run"
		speed = 1.1
	var squash := 1.0 - _land_t * 0.8
	_cat.scale = Vector3(1.25 * (2.0 - squash), 1.25 * squash, 1.25)
	if _cat_anim.current_animation != state:
		_cat_anim.play(state, 0.1, speed)
	_cat.visible = e.phase != E.Phase.GAME_OVER and (e.stunned <= 0.0 or fmod(_time, 0.12) < 0.07)  # blinks when hit


func _update_alley(e: WhiskerEngine, delta: float) -> void:
	# windows: shutters swing open, the room lights up
	for i in _windows.size():
		var w := _windows[i]
		var target := 1.0 if e.windows[i]["open"] else 0.0
		w["open"] = move_toward(w["open"], target, delta * 3.0)
		var k: float = smoothstep(0.0, 1.0, w["open"])
		(w["left"] as Node3D).rotation.y = -k * 1.9
		(w["right"] as Node3D).rotation.y = PI + k * 1.9
		var m := (w["glow"] as MeshInstance3D).material_override as ShaderMaterial
		m.set_shader_parameter("open", k)
		m.set_shader_parameter("flicker", 1.0 + 0.06 * sin(_time * 7.0 + i))
		m.set_shader_parameter("paper", ROOM_LOOK[e.windows[i]["room"]]["paper"])
		(w["light"] as OmniLight3D).light_energy = k * 1.2
	# the washing rides its line
	for wsh in _washing:
		var line: int = wsh["line"]
		wsh["x"] = fposmod(wsh["x"] + E.LINE_SPEED[line] * delta, E.W + 1.0)
		var n: Node3D = wsh["node"]
		n.position = Vector3(wsh["x"] - 0.5, E.LINE_Y[line] - 0.02, Z_LINE - 0.15)
		n.rotation.z = sin(_time * 2.0 + wsh["x"]) * 0.06
	# the dog
	var d := e.dog
	_dog.position = Vector3(d["x"], 0, Z_STREET - 0.1)
	_dog.rotation.y = lerp_angle(_dog.rotation.y, PI * 0.5 * d["dir"], 1.0 - exp(-delta * 10.0))
	var ds := "run" if d["chasing"] and d["alert"] <= 0.0 else ("bark" if d["chasing"] else "walk")
	if _dog_anim.current_animation != ds:
		_dog_anim.play(ds, 0.15)
	# shoes
	for i in _shoe_pool.size():
		var b := _shoe_pool[i]
		b.visible = i < e.shoes.size()
		if b.visible:
			var s: Dictionary = e.shoes[i]
			b.position = Vector3(s["pos"].x, s["pos"].y, Z_FENCE + 0.4)
			b.rotation.z += s["spin"] * delta


func _update_room(e: WhiskerEngine, delta: float) -> void:
	var r := e.room
	if r == null:
		return
	match r.kind:
		E.RoomKind.FISHBOWL:
			var fr := r as FishbowlRoom
			var fish: Array = _room_things.get("fish", [])
			for i in fish.size():
				var n: Node3D = fish[i]
				n.visible = i < fr.fish.size()
				if n.visible:
					var f: Dictionary = fr.fish[i]
					n.position = Vector3(f["pos"].x, f["pos"].y, 0.1)
					n.rotation.y = 0.0 if f["vel"].x < 0.0 else PI
					n.rotation.z = sin(_time * 12.0 + i) * 0.15
			var eels: Array = _room_things.get("eels", [])
			for i in eels.size():
				if i < fr.eels.size():
					var n: Node3D = eels[i]
					n.position = Vector3(fr.eels[i]["pos"].x, fr.eels[i]["pos"].y, 0.1)
					n.rotation.y = PI if cos(fr.eels[i]["phase"]) * fr.eels[i]["dir"] > 0 else 0.0
					n.rotation.x = sin(_time * 9.0) * 0.3
					var glow := n.get_node_or_null("Glow") as OmniLight3D
					if glow:
						glow.light_energy = 1.0 + 1.2 * absf(sin(_time * 23.0 + i * 3.0) * sin(_time * 7.0))  # crackling
		E.RoomKind.MICE:
			var mr := r as MiceRoom
			var nodes: Dictionary = _room_things["mice"]
			var alive := {}
			for m in mr.mice:
				alive[m["id"]] = true
				if not nodes.has(m["id"]):
					var n := _scene("mouse")
					n.scale = Vector3.ONE * 2.0
					_room_set.add_child(n)
					nodes[m["id"]] = n
				var mn: Node3D = nodes[m["id"]]
				mn.position = Vector3(m["x"], mr.mouse_pos(m).y, 0.9)
				mn.rotation.y = 0.0 if m["dir"] < 0 else PI
				mn.position.y += absf(sin(_time * 30.0)) * 0.05
			for id in nodes.keys():
				if not alive.has(id):
					nodes[id].queue_free()
					nodes.erase(id)
		E.RoomKind.BIRDCAGE:
			var br := r as BirdcageRoom
			var cage: Node3D = _room_things["cage"]
			cage.position = Vector3(BirdcageRoom.CAGE.get_center().x, br.cage_y, 0.0)
			cage.rotation.z = 0.0 if not br.cage_down else sin(_time * 20.0) * 0.1 * br.cage_y
			(_room_things["chain"] as Node3D).visible = not br.cage_down
			var bird: Node3D = _room_things["bird"]
			bird.visible = r.status == 0
			bird.position = Vector3(br.bird["pos"].x, br.bird["pos"].y, 0.3)
			bird.rotation.z = sin(_time * 25.0) * (0.3 if br.bird["free"] else 0.05)
		E.RoomKind.DOGBOWLS:
			var dr := r as DogbowlsRoom
			for i in dr.bowls.size():
				var level: float = dr.bowls[i]
				var milk: MeshInstance3D = _room_things["bowls"][i]["milk"]
				milk.visible = level > 0.0
				milk.position.y = 0.09 + 0.09 * level
				milk.scale = Vector3(0.85 + 0.15 * level, 1.0, 0.85 + 0.15 * level)
				var dd: Dictionary = _room_things["dogs"][i]
				var dog: Node3D = dd["node"]
				var awake: bool = dr.dogs[i]["awake"] > 0.0
				dog.position = Vector3(dr.dogs[i]["x"], 0, 0.3)
				dog.rotation.y = lerp_angle(dog.rotation.y, PI * 0.5 * dr.dogs[i]["dir"] if awake else -PI * 0.5, 1.0 - exp(-delta * 8.0))
				var st := "run" if awake else "idle"
				var anim: AnimationPlayer = dd["anim"]
				if anim.current_animation != st:
					anim.play(st, 0.2, 1.0 if awake else 0.3)
				dog.scale = Vector3(1.3, 1.3 * (1.0 if awake else 0.9 + 0.03 * sin(_time * 2.0 + i)), 1.3)  # snoring
				var zz: Label3D = dd["zz"]
				zz.visible = not awake
				var zt := fmod(_time * 0.6 + i * 0.3, 1.0)
				zz.position = Vector3(dr.dogs[i]["x"] + 0.3 + zt * 0.5, 1.4 + zt * 1.2, 0.5)
				zz.modulate.a = 1.0 - zt
				zz.font_size = int(60 + zt * 60)
		E.RoomKind.HEARTS:
			var hr := r as HeartsRoom
			for i in hr.hearts.size():
				var n: Node3D = _room_things["hearts"][i]
				var rect: Rect2 = hr.hearts[i]["rect"]
				n.position = Vector3(rect.get_center().x, rect.end.y, 0.0)
				n.rotation.z = sin(_time * 1.5 + i) * 0.05
			var arrows: Array = _room_things["arrows"]
			for i in arrows.size():
				var a: Node3D = arrows[i]
				a.visible = i < hr.arrows.size()
				if a.visible:
					a.position = Vector3(hr.arrows[i]["pos"].x, hr.arrows[i]["pos"].y, 0.4)
					a.rotation.y = 0.0 if hr.arrows[i]["dir"] < 0 else PI
	var broom: Node3D = _room_things["broom"]
	broom.visible = r.time_left < 5.0
	if broom.visible:  # the broom sweeps in from the right toward the cat
		var k := 1.0 - r.time_left / 5.0
		broom.position = Vector3(lerpf(17.0, e.cat.pos.x + 0.8, k), 0.0, 0.5)
		broom.rotation.z = 0.35 + sin(_time * 14.0) * 0.25
