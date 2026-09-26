class_name KnucklesView3D
extends Node3D
## Neon Knuckles in 3D: a night city built along the stage (x), fighters on the street (z is depth), a side camera
## that follows the scroll. Three themes: the street (brick fronts with lit rooms, shop windows and neon signs in
## glass tubes, parked cars, lamps, hydrants and bins, a rain-wet road with puddles and steam from the manholes), the
## docks (a quay with bollards and floodlights, stacked containers, a moored freighter, harbour cranes and the city
## across the water) and the rooftops (parapets, water towers, vents, antennas, a billboard, string lights and the
## skyline). Weapons ride the fighters' hands (bone attachments).

const B = preload("res://games/knuckles/engine/brawl_engine.gd")
const M := "res://games/knuckles/art/models/"
const MODEL := {"thug": "thug", "knifer": "knifer", "bruiser": "bruiser", "boss": "boss"}
## the models' build (knuckles_fighters.py): the jog covers 3.0 m per cycle-second at scale 1, so it is played
## at the fighter's speed over this
const BUILD := {"knifer": 0.95, "bruiser": 1.25, "boss": 1.12}
const JOG_SPEED := 3.0
const NEON: Array[Color] = [Color(1.0, 0.2, 0.6), Color(0.2, 0.9, 1.0), Color(0.6, 0.3, 1.0), Color(1.0, 0.75, 0.2), Color(0.3, 1.0, 0.5),
	Color(1.0, 0.3, 0.2)]
## street buildings (knuckles_city.py): width in metres
const BLDG := {"bldg_0": 7.5, "bldg_1": 7.5, "bldg_2": 10.0, "bldg_3": 7.5, "bldg_4": 10.0, "bldg_5": 5.0, "bldg_6": 5.0, "bldg_7": 7.5}
const FRONT := -5.4  ## the building fronts on the street
const KERB := -4.0   ## the far kerb (parked cars stand just in front of it)
const NEAR := 3.2    ## the near kerb
const FIGHTER_LAYER := 2  ## fighters also sit on this render layer, for their own rim and key lights

@export var game: KnucklesGame

var _camera: Camera3D
var _env: Environment
var _sky_mat: ShaderMaterial
var _set: Node3D
var _fx: KnucklesEffects
var _rain: CPUParticles3D
var _nodes := {}  ## fighter id -> {node, anim, weapon_slot, weapon}
var _items := {}  ## item id -> node
var _cam_x := 8.0
var _time := 0.0
var _shake := 0.0
var _mats := {}
var _flicker: Array = []  ## [material, base energy, phase]


func _ready() -> void:
	_build_env()
	_fx = KnucklesEffects.new()
	add_child(_fx)
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _build_env() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_sky_mat = ShaderMaterial.new()
	_sky_mat.shader = load("res://games/knuckles/shaders/night_sky.gdshader")
	var sky := Sky.new()
	sky.sky_material = _sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.25, 0.28, 0.45)
	_env.ambient_light_energy = 0.8
	_env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.1
	_env.glow_enabled = true
	_env.glow_intensity = 0.9
	_env.glow_bloom = 0.12
	_env.glow_hdr_threshold = 0.9
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	_env.set_glow_level(2, 1.0)
	_env.set_glow_level(4, 0.8)
	_env.set_glow_level(5, 0.5)
	_env.ssao_enabled = true
	_env.ssr_enabled = true  # the wet street mirrors the neon
	_env.ssr_max_steps = 64
	_env.ssr_fade_in = 0.1
	_env.ssr_depth_tolerance = 0.3
	Look.fog(_env, Color(0.12, 0.1, 0.22), 0.012)
	_env.fog_sky_affect = 0.25
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.25
	_env.adjustment_contrast = 1.1
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-45, -30, 0)
	moon.light_color = Color(0.55, 0.62, 1.0)
	moon.light_energy = 0.3
	moon.shadow_enabled = true
	add_child(moon)
	# the fighters get their own soft key light from the camera side and a coloured rim from behind, so they stand
	# out from the busy set (lights on the fighter layer only)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-25, 20, 0)
	key.light_color = Color(1.0, 0.86, 0.75)
	key.light_energy = 0.55
	key.light_cull_mask = 1 << (FIGHTER_LAYER - 1)
	key.light_specular = 0.3
	add_child(key)
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-20, 160, 0)
	rim.light_color = Color(0.55, 0.7, 1.0)
	rim.light_energy = 1.4
	rim.light_cull_mask = 1 << (FIGHTER_LAYER - 1)
	add_child(rim)
	var rim2 := DirectionalLight3D.new()
	rim2.rotation_degrees = Vector3(-15, -150, 0)
	rim2.light_color = Color(1.0, 0.35, 0.75)
	rim2.light_energy = 1.0
	rim2.light_cull_mask = 1 << (FIGHTER_LAYER - 1)
	add_child(rim2)
	_camera = Camera3D.new()
	_camera.fov = 42
	_camera.far = 600.0
	_camera.current = true
	add_child(_camera)


# ------------------------------------------------------------------ helpers

func _scene(name: String) -> Node3D:
	return (load(M + name + ".glb") as PackedScene).instantiate()


func _put(name: String, pos: Vector3, rot_y: float = 0.0, parent: Node3D = null) -> Node3D:
	var n := _scene(name)
	n.position = pos
	n.rotation.y = rot_y
	(parent if parent else _set).add_child(n)
	return n


func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


## A long strip along the stage, cut into short boxes: each piece gets its own nearby lights (the compatibility
## renderer lights a mesh with its eight nearest lights only).
func _strip(L: float, y: float, z: float, size: Vector3, mat: Material) -> void:
	var seg := 12.0
	var x := -20.0
	while x < L:
		_box(_set, Vector3(x + seg * 0.5, y, z), Vector3(seg + 0.001, size.y, size.z), mat)
		x += seg


func _glow(c: Color, energy: float) -> StandardMaterial3D:
	var key := "glow%s%s" % [c, energy]
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.emission_enabled = energy > 0.0
	m.emission = c
	m.emission_energy_multiplier = energy
	_mats[key] = m
	return m


## Neon in glass tubes: a pale core and a strong coloured glow.
func _neon(c: Color, energy: float = 4.5) -> StandardMaterial3D:
	var key := "neon%s%s" % [c, energy]
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = c.lerp(Color.WHITE, 0.35)
	m.emission_enabled = true
	m.emission = c
	m.emission_energy_multiplier = energy
	m.roughness = 0.2
	_mats[key] = m
	return m


func _glass() -> StandardMaterial3D:
	if not _mats.has("glass"):
		var m := StandardMaterial3D.new()
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.albedo_color = Color(0.1, 0.13, 0.18, 0.22)
		m.roughness = 0.03
		m.metallic = 0.3
		m.metallic_specular = 1.0
		_mats["glass"] = m
	return _mats["glass"]


func _wet(c: Color, rough: float) -> StandardMaterial3D:
	var key := "wet%s%s" % [c, rough]
	if not _mats.has(key):
		var m := StandardMaterial3D.new()
		m.albedo_color = c
		m.roughness = rough
		m.metallic_specular = 1.0
		_mats[key] = m
	return _mats[key]


## Replaces the materials named in `map` (glTF material names from the Blender scripts) on every mesh of a model.
func _dress(n: Node, map: Dictionary) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		for i in mesh.get_surface_count():
			var m := mesh.surface_get_material(i)
			if m and map.has(m.resource_name):
				(mi as MeshInstance3D).set_surface_override_material(i, map[m.resource_name])


func _light(parent: Node3D, pos: Vector3, c: Color, energy: float, rng_: float) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.position = pos
	l.light_color = c
	l.light_energy = energy
	l.omni_range = rng_
	l.omni_attenuation = 1.4
	l.light_specular = 1.0
	parent.add_child(l)
	return l


func _pick(rng: RandomNumberGenerator, a: Array) -> Variant:
	return a[rng.randi_range(0, a.size() - 1)]


## Rising steam from a manhole or a vent: soft puffs that grow and fade.
func _steam(pos: Vector3, amount: int = 14, size: float = 1.0) -> void:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = 3.5
	p.preprocess = 3.5
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 0.3
	p.direction = Vector3(0.1, 1, 0)
	p.spread = 12.0
	p.initial_velocity_min = 0.5
	p.initial_velocity_max = 0.9
	p.gravity = Vector3(0.25, 0.15, 0)
	p.scale_amount_min = 1.2 * size
	p.scale_amount_max = 2.0 * size
	p.scale_amount_curve = Fx.size_curve(true)
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 0))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.2, Color(1, 1, 1, 0.22))
	g.add_point(0.6, Color(1, 1, 1, 0.12))
	p.color_ramp = g
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	p.mesh = q
	p.material_override = Fx.material("smoke", Color(0.75, 0.75, 0.85))
	p.position = pos
	_set.add_child(p)


## Rain streaks that follow the camera.
func _make_rain(amount: int, alpha: float) -> void:
	_rain = CPUParticles3D.new()
	_rain.amount = amount
	_rain.lifetime = 0.7
	_rain.preprocess = 1.0
	_rain.local_coords = false
	_rain.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_rain.emission_box_extents = Vector3(14, 0.5, 4.5)
	_rain.direction = Vector3(0.12, -1, 0.05)
	_rain.spread = 1.5
	_rain.initial_velocity_min = 15.0
	_rain.initial_velocity_max = 18.0
	_rain.gravity = Vector3(0, -6, 0)
	var q := QuadMesh.new()
	q.size = Vector2(0.008, 0.4)
	_rain.mesh = q
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	m.albedo_color = Color(0.7, 0.75, 0.95, alpha)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	_rain.material_override = m
	_set.add_child(_rain)


## Towers far away, with windows from the tower shader and a red light on top.
func _tower(pos: Vector3, size: Vector3, seed_: float, lit: float = 0.3) -> void:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	var key := "tower%s" % lit
	if not _mats.has(key):
		var m := ShaderMaterial.new()
		m.shader = load("res://games/knuckles/shaders/tower.gdshader")
		m.set_shader_parameter("lit_ratio", lit)
		_mats[key] = m
	mi.material_override = _mats[key]
	mi.set_instance_shader_parameter("seed", seed_)
	mi.position = pos + Vector3(0, size.y * 0.5, 0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_set.add_child(mi)


func _sky(zenith: Color, horizon: Color, glow: Color, clouds: float, stars: float) -> void:
	_sky_mat.set_shader_parameter("zenith", zenith)
	_sky_mat.set_shader_parameter("horizon", horizon)
	_sky_mat.set_shader_parameter("glow", glow)
	_sky_mat.set_shader_parameter("cloud_cover", clouds)
	_sky_mat.set_shader_parameter("star_amount", stars)


# ------------------------------------------------------------------ the set

func _on_stage(e: BrawlEngine) -> void:
	if _set:
		_set.queue_free()
	_set = Node3D.new()
	add_child(_set)
	_nodes.clear()
	_items.clear()
	_flicker.clear()
	_rain = null
	e.event.connect(_on_event)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(e.level.name)
	match e.level.theme:
		"docks": _build_docks(e, rng)
		"rooftops": _build_rooftops(e, rng)
		_: _build_street(e, rng)
	_cam_x = e.scroll + e.view_width * 0.5
	_place_camera(1.0, e)


func _build_street(e: BrawlEngine, rng: RandomNumberGenerator) -> void:
	var L := e.level.length + 30.0
	_sky(Color(0.01, 0.012, 0.035), Color(0.1, 0.05, 0.14), Color(0.5, 0.2, 0.32), 0.6, 0.5)
	Look.fog(_env, Color(0.14, 0.1, 0.24), 0.014)
	# the road: rain-wet asphalt, kerbs with a gutter of water, paving on both sides
	var asphalt := Pbr.material("dark_rock", Color(0.3, 0.3, 0.36), 0.5, 0.0, 0.32)
	var walk := Pbr.material("stone_bricks", Color(0.38, 0.37, 0.42), 0.7, 0.0, 0.55)
	var kerb := Pbr.material("rock", Color(0.55, 0.55, 0.58), 1.0, 0.0, 0.6)
	var water := _wet(Color(0.015, 0.015, 0.025), 0.02)
	_strip(L, -0.1, (KERB + NEAR) * 0.5, Vector3(0, 0.2, NEAR - KERB + 0.1), asphalt)
	_strip(L, 0.05, (FRONT - 4.0 + KERB) * 0.5, Vector3(0, 0.2, KERB - FRONT + 4.0), walk)
	_strip(L, 0.05, NEAR + 2.0, Vector3(0, 0.2, 4.0), walk)
	for z in [KERB + 0.08, NEAR - 0.08]:
		_strip(L, 0.06, z, Vector3(0, 0.22, 0.18), kerb)
	for z in [KERB + 0.3, NEAR - 0.3]:
		_strip(L, 0.002, z, Vector3(0, 0.01, 0.28), water)  # the gutters run with rain
	var paint := Pbr.material("rock", Color(0.85, 0.82, 0.7), 2.0, 0.0, 0.5)
	var yellow := Pbr.material("rock", Color(0.9, 0.7, 0.2), 2.0, 0.0, 0.5)
	var mid := (KERB + NEAR) * 0.5
	for i in int(L / 4.0) + 5:  # dashed centre line, solid edge lines
		_box(_set, Vector3(-18 + i * 4.0, 0.004, mid), Vector3(2.0, 0.01, 0.13), paint)
	_strip(L, 0.003, KERB + 1.95, Vector3(0, 0.01, 0.1), paint)  # the parking lane
	_strip(L, 0.003, NEAR - 0.5, Vector3(0, 0.01, 0.1), yellow)
	var cross_x := 40.0 + rng.randf_range(-6, 6)
	var z := KERB + 0.6
	while z < NEAR - 0.6:  # a zebra crossing
		_box(_set, Vector3(cross_x, 0.005, z), Vector3(3.0, 0.01, 0.45), paint)
		z += 0.9
	# puddles: glossy films that mirror the neon
	for i in int(L / 5.0):
		var p := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 1.0
		cm.bottom_radius = 1.0
		cm.height = 0.01
		cm.radial_segments = 24
		p.mesh = cm
		p.material_override = water
		p.position = Vector3(-12 + i * 5.0 + rng.randf_range(-2, 2), 0.004, rng.randf_range(KERB + 0.4, NEAR - 0.4))
		p.scale = Vector3(rng.randf_range(0.5, 1.6), 1, rng.randf_range(0.3, 0.7))
		p.rotation.y = rng.randf_range(-0.4, 0.4)
		_set.add_child(p)
	# manholes, a few breathing steam (outside the fighters' band)
	var mx := 8.0
	while mx < L:
		var mz := NEAR - 0.75 if rng.randf() < 0.6 else KERB + 1.4
		_put("manhole", Vector3(mx, 0.0, mz))
		if rng.randf() < 0.7:
			_steam(Vector3(mx, 0.1, mz))
		mx += rng.randf_range(16, 26)
	# the buildings: shop fronts with neon signs, lit rooms above; now and then an alley between them
	var x := -18.0
	var bag: Array = BLDG.keys()
	var k := 0
	while x < L:
		if k % bag.size() == 0:
			for i in range(bag.size() - 1, 0, -1):  # a fresh order of the fronts, from the stage's rng
				var j := rng.randi_range(0, i)
				var t: String = bag[i]
				bag[i] = bag[j]
				bag[j] = t
		var name: String = bag[k % bag.size()]
		k += 1
		var w: float = BLDG[name]
		_building(name, Vector3(x + w * 0.5, 0, FRONT), rng)
		x += w
		if rng.randf() < 0.25 and x < L - 10:
			_alley(x, rng)
			x += 3.0
	# lamps along the far kerb, their pools of light on the road
	var lx := 4.0
	while lx < L:
		_put("street_lamp", Vector3(lx, 0, KERB - 0.35), PI)
		var sl := SpotLight3D.new()
		sl.position = Vector3(lx, 5.0, KERB + 0.95)
		sl.rotation_degrees = Vector3(-90, 0, 0)
		sl.light_color = Color(1.0, 0.78, 0.5)
		sl.light_energy = 6.0
		sl.spot_range = 9.0
		sl.spot_angle = 50.0
		sl.spot_attenuation = 0.8
		sl.shadow_enabled = true
		_set.add_child(sl)
		_light(_set, Vector3(lx, 4.6, KERB + 1.0), Color(1.0, 0.8, 0.55), 0.8, 9.0)
		_light(_set, Vector3(lx + 7.0, 4.0, NEAR + 2.5), Color(1.0, 0.78, 0.55), 2.6, 10.0)  # the lamps behind the camera
		lx += 14.0
	# parked cars in the far lane, never in front of the fight
	var cx := 11.0
	while cx < L:
		_put("car_%d" % rng.randi_range(0, 2), Vector3(cx, 0, KERB + 0.95), 0.0 if rng.randf() < 0.5 else PI)
		cx += 7.0 * rng.randi_range(3, 5)
	# street furniture on the far sidewalk
	var fx := 2.0
	while fx < L:
		var what := rng.randi_range(0, 5)
		var at := Vector3(fx, 0.15, KERB - 0.4)
		match what:
			0: _put("hydrant", at, rng.randf_range(-0.3, 0.3))
			1: _put("bin", at + Vector3(0, 0, -0.05))
			2: _put("meter", at + Vector3(0, 0, 0.1))
			3: _put("sign_post", at + Vector3(0, 0, 0.1), PI * 0.5 if rng.randf() < 0.3 else 0.0)
			4:
				_put("trash_bags", Vector3(fx, 0.15, FRONT + 0.5))
				_put("trash_bags", Vector3(fx + 0.7, 0.15, FRONT + 0.4), 1.3)
			5:
				_put("barrel", Vector3(fx, 0.15, FRONT + 0.7))
				_light(_set, Vector3(fx, 1.5, FRONT + 1.2), Color(1.0, 0.5, 0.2), 1.6, 5.0)
		fx += rng.randf_range(4.0, 8.0)
	_make_rain(1600, 0.16)


## One street building, dressed: brick tint, the sign's two neon colours, the shop's glow, the awning's stripes.
func _building(name: String, pos: Vector3, rng: RandomNumberGenerator) -> void:
	var n := _put(name, pos)
	var tint := Color.from_hsv(rng.randf_range(0.0, 0.08), rng.randf_range(0.25, 0.5), rng.randf_range(0.4, 0.62))
	if rng.randf() < 0.25:  # a painted front now and then
		tint = Color.from_hsv(rng.randf_range(0.45, 0.62), 0.2, 0.45)
	var c1: Color = _pick(rng, NEON)
	var c2: Color = _pick(rng, NEON)
	while c2 == c1:
		c2 = _pick(rng, NEON)
	var shop := c1.lerp(Color(1.0, 0.9, 0.75), 0.45)
	var neon1 := _neon(c1, 5.0)
	if rng.randf() < 0.3:  # a sign with a tired transformer, buzzing on and off
		neon1 = neon1.duplicate()
		_flicker.append([neon1, 5.0, rng.randf() * 10.0])
	_dress(n, {"brick": Pbr.material("stone_bricks", tint, 0.5), "glass": _glass(), "neon": neon1, "neon2": _neon(c2, 4.0),
		"shop_glow": _glow(shop, 0.75), "awning_a": Pbr.material("planks", c2.darkened(0.45), 2.0), "awning_b": Pbr.material("planks", Color(0.8, 0.78, 0.72), 2.0)})
	_light(_set, pos + Vector3(0, 3.6, 1.6), c1, 2.4, 8.0)          # the sign lights the pavement
	_light(_set, pos + Vector3(rng.randf_range(-2, 2), 3.5, 5.6), c1.lerp(Color(0.6, 0.6, 1.0), 0.4), 1.4, 9.0)  # and the road
	_light(_set, pos + Vector3(0, 1.4, 1.4), shop, 1.2, 6.0)         # the shop window's spill
	_light(_set, pos + Vector3(0, 5.8, 1.0), Color(1.0, 0.7, 0.45), 0.5, 5.0)  # the lit rooms above


## A narrow alley: a back wall with a caged bulb, a dumpster, steam from a vent.
func _alley(x: float, rng: RandomNumberGenerator) -> void:
	var brick := Pbr.material("stone_bricks", Color(0.3, 0.22, 0.2), 0.5)
	_box(_set, Vector3(x + 1.5, 4.0, FRONT - 3.4), Vector3(3.2, 8.0, 0.4), brick)
	_box(_set, Vector3(x + 1.5, 0.05, FRONT - 1.6), Vector3(3.2, 0.2, 3.6), Pbr.material("dark_rock", Color(0.25, 0.25, 0.3), 0.5, 0.0, 0.4))
	_box(_set, Vector3(x + 1.5, 2.8, FRONT - 3.15), Vector3(0.18, 0.18, 0.12), _glow(Color(0.7, 1.0, 0.8), 6.0))
	_light(_set, Vector3(x + 1.5, 2.6, FRONT - 2.4), Color(0.55, 1.0, 0.75), 2.0, 5.5)
	_put("dumpster", Vector3(x + 1.5, 0.15, FRONT - 2.4), rng.randf_range(-0.15, 0.15))
	_steam(Vector3(x + 0.6, 0.2, FRONT - 1.2), 10)


func _build_docks(e: BrawlEngine, rng: RandomNumberGenerator) -> void:
	var L := e.level.length + 30.0
	_sky(Color(0.008, 0.015, 0.04), Color(0.06, 0.07, 0.13), Color(0.4, 0.22, 0.25), 0.5, 1.0)
	Look.fog(_env, Color(0.1, 0.11, 0.2), 0.006)
	var planks := Pbr.material("planks", Color(0.4, 0.36, 0.33), 0.7, 0.0, 0.4)
	var concrete := Pbr.material("rock", Color(0.42, 0.42, 0.45), 0.8, 0.0, 0.8)
	_strip(L, -0.1, -3.0, Vector3(0, 0.2, 19.0), planks)   # the pier deck, from the quay edge to past the camera
	_strip(L, -0.35, -12.6, Vector3(0, 0.7, 1.2), concrete)  # the quay's edge beam
	_strip(L, 0.02, -11.9, Vector3(0, 0.06, 0.25), _glow(Color(0.8, 0.6, 0.1), 0.05))  # the edge's yellow line
	var water := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(L + 400, 260)
	plane.subdivide_width = 120
	plane.subdivide_depth = 60
	water.mesh = plane
	var wm := ShaderMaterial.new()
	wm.shader = load("res://core/art/shaders/water.gdshader")
	wm.set_shader_parameter("normal_map", load("res://core/art/textures/water/normal.png"))
	wm.set_shader_parameter("deep", Color(0.005, 0.01, 0.025))
	wm.set_shader_parameter("mid", Color(0.01, 0.025, 0.05))
	wm.set_shader_parameter("shallow", Color(0.02, 0.04, 0.07))
	wm.set_shader_parameter("sky", Color(0.08, 0.07, 0.14))
	water.material_override = wm
	water.position = Vector3(L * 0.5, -1.4, -13.2 - 130)
	_set.add_child(water)
	# the quay: bollards with their ropes, hanging tyre fenders
	var bx := 3.0
	while bx < L:
		_put("bollard", Vector3(bx, 0.0, -11.6))
		bx += rng.randf_range(8, 12)
	var fender := StandardMaterial3D.new()
	fender.albedo_color = Color(0.03, 0.03, 0.03)
	fender.roughness = 0.7
	for i in int(L / 6.0):
		var t := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 0.22
		tm.outer_radius = 0.42
		t.mesh = tm
		t.material_override = fender
		t.position = Vector3(i * 6.0 + 1.5, -0.55, -13.25)
		t.rotation = Vector3(PI * 0.5, 0, 0)
		_set.add_child(t)
	# the freighter alongside, and ships and cranes across the basin
	var sx := 20.0
	while sx < L + 40:
		_put("ship", Vector3(sx, -1.4, -36.0), 0.0 if rng.randf() < 0.5 else PI)
		var hl := _light(_set, Vector3(sx, 6.0, -28.0), Color(1.0, 0.8, 0.5), 3.0, 20.0)
		hl.light_specular = 0.5
		sx += rng.randf_range(80, 100)
	_put("ship", Vector3(L * 0.9 + 40, -1.4, -75.0), PI)
	for cx in range(-10, int(L) + 60, 34):
		_put("crane", Vector3(cx + rng.randf_range(-4, 4), 0.0, -58.0 - rng.randf_range(0, 6)), rng.randf_range(-0.6, 0.6) + PI * 0.5)
	# the far quay and the city across the water
	_box(_set, Vector3(L * 0.5, -0.5, -62.0), Vector3(L + 300, 2.0, 12.0), concrete)
	for i in 26:
		var wx := -60.0 + i * (L + 150.0) / 26.0 + rng.randf_range(-3, 3)
		_tower(Vector3(wx, 0.0, -68.0 - rng.randf_range(0, 6)), Vector3(rng.randf_range(10, 16), rng.randf_range(5, 10), 8.0), float(i), 0.12)
	for i in 60:
		var tx := rng.randf_range(-100, L + 100)
		_tower(Vector3(tx, 0.0, rng.randf_range(-150, -110)), Vector3(rng.randf_range(6, 14), rng.randf_range(12, 60), rng.randf_range(6, 14)), 100.0 + i, 0.35)
	for i in 10:  # dock lights across the water, their reflections in the swell
		_box(_set, Vector3(-40 + i * (L + 80) / 10.0, 9.0, -64.0), Vector3(0.35, 0.15, 0.15), _glow(Color(1.0, 0.7, 0.35), 6.0))
	# stacks of containers behind the fight, with gaps that let the harbour show through
	var x := -14.0
	while x < L:
		var cols := rng.randi_range(1, 2)
		for c in cols:
			var h := 1 if rng.randf() < 0.45 else 2
			var z := -7.4 - rng.randf_range(0, 0.4)
			for k in h:
				var box := _put("container_%d" % rng.randi_range(0, 3), Vector3(x + c * 6.25, k * 2.6, z), PI if rng.randf() < 0.5 else 0.0)
				box.rotation.y += rng.randf_range(-0.02, 0.02)
		if rng.randf() < 0.5:  # one turned end-on, further back, doors to the camera
			_put("container_%d" % rng.randi_range(0, 3), Vector3(x + cols * 6.25 + 2.5, 0, -9.5), PI * 0.5)
		x += cols * 6.25 + rng.randf_range(10.0, 16.0)
	# floodlights on the pier, crates, drums and coiled rope
	var lx := 6.0
	while lx < L:
		_put("dock_light", Vector3(lx, 0, -3.9))
		_light(_set, Vector3(lx, 4.4, -2.8), Color(1.0, 0.68, 0.35), 2.8, 13.0)
		_light(_set, Vector3(lx + 8.0, 3.0, 5.0), Color(0.45, 0.6, 1.0), 1.2, 10.0)  # cold light off the water
		lx += 16.0
	for i in int(L / 9.0):
		var px := rng.randf_range(0, L - 5)
		match i % 4:
			0: _put("crate", Vector3(px, 0, -3.6), rng.randf_range(0, 1))
			1: _put("rope_coil", Vector3(px, 0, -3.5))
			2:
				_put("barrel", Vector3(px, 0, -3.7))
				_light(_set, Vector3(px, 1.5, -3.2), Color(1.0, 0.5, 0.2), 1.6, 5.0)
			3:
				_put("crate", Vector3(px, 0, -3.7), 0.3)
				_put("crate", Vector3(px + 0.1, 0.6, -3.7), 1.0)
	_make_rain(900, 0.12)


func _build_rooftops(e: BrawlEngine, rng: RandomNumberGenerator) -> void:
	var L := e.level.length + 30.0
	_sky(Color(0.02, 0.012, 0.05), Color(0.14, 0.07, 0.2), Color(0.6, 0.22, 0.4), 0.35, 1.0)
	Look.fog(_env, Color(0.16, 0.08, 0.24), 0.006)
	var tar := Pbr.material("rock", Color(0.3, 0.3, 0.34), 0.6, 0.0, 0.7)
	var brick := Pbr.material("stone_bricks", Color(0.45, 0.36, 0.34), 0.5)
	var coping := Pbr.material("rock", Color(0.6, 0.58, 0.55), 1.0)
	_strip(L, -0.1, 0.0, Vector3(0, 0.2, 14.0), tar)
	_strip(L, -10.0, -1.0, Vector3(0, 20.0, 10.0), brick)
	_strip(L, 0.55, -6.3, Vector3(0, 1.1, 0.35), brick)       # the parapet
	_strip(L, 1.15, -6.3, Vector3(0, 0.1, 0.5), coping)
	_strip(L, 0.08, -5.95, Vector3(0, 0.16, 0.3), coping)      # the flashing along its foot
	_strip(L, 0.3, 5.7, Vector3(0, 0.6, 0.3), brick)           # the low wall along the near edge
	_strip(L, 0.64, 5.7, Vector3(0, 0.08, 0.42), coping)
	# the kit between the fight and the parapet
	var x := -6.0
	var kinds := ["water_tank", "ac_unit", "vents", "antenna", "stair_hut", "ac_unit", "vents"]
	while x < L:
		var kind: String = _pick(rng, kinds)
		var zz := -4.6 if kind in ["water_tank", "stair_hut"] else -4.2
		var n := _put(kind, Vector3(x, 0, zz), 0.0 if kind in ["stair_hut", "water_tank"] else rng.randf_range(-0.2, 0.2))
		if kind == "stair_hut":
			_dress(n, {"brick": brick})
			_light(_set, Vector3(x, 2.4, zz + 2.0), Color(1.0, 0.8, 0.55), 1.5, 6.0)
		x += rng.randf_range(7.0, 12.0)
	# neon tubes on the parapet, each lighting its stretch of roof, and string lights sagging between poles
	var lx := 0.0
	var k := 0
	var tube := CylinderMesh.new()
	tube.top_radius = 0.035
	tube.bottom_radius = 0.035
	tube.height = 2.4
	tube.radial_segments = 10
	while lx < L:
		var c := NEON[k % NEON.size()]
		for j in 2:
			var t := MeshInstance3D.new()
			t.mesh = tube
			t.material_override = _neon(c if j == 0 else NEON[(k + 2) % NEON.size()], 5.0)
			t.position = Vector3(lx, 1.45 + j * 0.2, -6.08)
			t.rotation.z = PI * 0.5
			_set.add_child(t)
		_light(_set, Vector3(lx, 2.4, -4.5), c, 2.4, 11.0)
		_light(_set, Vector3(lx + 5.0, 5.0, 3.0), Color(0.55, 0.6, 1.0), 1.0, 12.0)  # moonlit fill
		_light(_set, Vector3(lx + 5.0, 2.5, 6.5), NEON[(k + 3) % NEON.size()].lerp(Color.WHITE, 0.3), 2.2, 9.0)  # signs behind the camera
		lx += 10.0
		k += 1
	_string_lights(L)
	# the near side of the roof: a pipe run on low stands
	var pipe := Pbr.material("metal", Color(0.45, 0.45, 0.5), 1.0, 0.8, 0.6)
	var pm := CylinderMesh.new()
	pm.top_radius = 0.09
	pm.bottom_radius = 0.09
	pm.height = 12.0
	pm.radial_segments = 12
	var px := -20.0
	while px < L:
		var pmi := MeshInstance3D.new()
		pmi.mesh = pm
		pmi.material_override = pipe
		pmi.position = Vector3(px + 6.0, 0.28, NEAR + 0.9)
		pmi.rotation.z = PI * 0.5
		_set.add_child(pmi)
		for sx in [px + 1.0, px + 6.0, px + 11.0]:
			_box(_set, Vector3(sx, 0.1, NEAR + 0.9), Vector3(0.08, 0.2, 0.3), pipe)
		px += 12.0
	# the neighbours' roofs, lower, with a billboard and water towers; then the skyline
	var nx := -20.0
	var b := 0
	while nx < L + 20:
		var w := rng.randf_range(14, 24)
		var h := rng.randf_range(-6.0, -2.0)
		_box(_set, Vector3(nx + w * 0.5, h - 20.0, -16.0), Vector3(w - 0.5, 40.0, 16.0), brick)
		_box(_set, Vector3(nx + w * 0.5, h + 0.5, -8.2), Vector3(w - 0.5, 1.0, 0.4), brick)
		if b % 2 == 0:
			var bb := _put("billboard_%d" % ((b / 2) % 2), Vector3(nx + w * 0.5, h, -14.0))
			var c: Color = _pick(rng, NEON)
			_dress(bb, {"neon": _neon(c, 5.0), "neon2": _neon(_pick(rng, NEON), 4.0)})
			_light(_set, Vector3(nx + w * 0.5, h + 4.0, -11.0), c, 3.0, 14.0)
		else:
			_put("water_tank", Vector3(nx + w * 0.3, h, -12.0))
			_put("water_tank", Vector3(nx + w * 0.65, h, -15.0))
		nx += w
		b += 1
	for i in 70:
		var tx := rng.randf_range(-40, L + 40)
		var th := rng.randf_range(20, 70)
		var tz := rng.randf_range(-80, -32)
		var tw := rng.randf_range(6, 12)
		_tower(Vector3(tx, -30.0, tz), Vector3(tw, th + 30.0, tw * rng.randf_range(0.7, 1.3)), float(i), 0.3)
		_box(_set, Vector3(tx, th + 0.15, tz), Vector3(0.3, 0.3, 0.3), _glow(Color(1, 0.1, 0.1), 6.0))
		if rng.randf() < 0.15:  # a neon crown on some towers
			_box(_set, Vector3(tx, th - 1.0, tz + tw * 0.5 + 0.1), Vector3(tw * 0.9, 0.25, 0.1), _neon(_pick(rng, NEON), 4.0))


## Warm bulbs on a wire, sagging between poles along the parapet (one multimesh).
func _string_lights(L: float) -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var s := SphereMesh.new()
	s.radius = 0.06
	s.height = 0.12
	s.radial_segments = 8
	s.rings = 4
	mm.mesh = s
	var span := 8.0
	var per := 14
	var n := int(L / span) + 2
	mm.instance_count = n * per
	for i in n:
		for j in per:
			var t := float(j) / per
			var px := -4.0 + (i + t) * span
			var py := 2.9 - 0.7 * 4.0 * t * (1.0 - t)
			mm.set_instance_transform(i * per + j, Transform3D(Basis(), Vector3(px, py, -5.9)))
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = _glow(Color(1.0, 0.8, 0.5), 5.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_set.add_child(mi)
	var wire := _glow(Color(0.05, 0.05, 0.05), 0.0)
	for i in n:
		_box(_set, Vector3(-4.0 + i * span, 1.6, -6.0), Vector3(0.06, 3.2, 0.06), wire)


# ------------------------------------------------------------------ fighters and items

func _fighter_node(f: Dictionary) -> Dictionary:
	var name: String = "hero_a" if f["player"] == 0 else ("hero_b" if f["player"] == 1 else MODEL.get(f["kind"], "thug"))
	var n := _scene(name)
	_set.add_child(n)
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	for a in ap.get_animation_list():
		ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "walk", "grab", "held"] else Animation.LOOP_NONE
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).layers = 1 | (1 << (FIGHTER_LAYER - 1))
	var skel: Skeleton3D = n.find_child("Skeleton3D", true, false)
	var slot: BoneAttachment3D = null
	if skel:
		slot = BoneAttachment3D.new()
		slot.bone_name = "hand.R"
		skel.add_child(slot)
	return {"node": n, "anim": ap, "slot": slot, "weapon": "", "wnode": null, "last": "", "build": BUILD.get(name, 1.0)}


func _set_weapon(d: Dictionary, kind: String) -> void:
	if d["weapon"] == kind:
		return
	if d["wnode"]:
		d["wnode"].queue_free()
		d["wnode"] = null
	d["weapon"] = kind
	if kind != "" and d["slot"]:
		var w := _scene(kind)
		w.position = Vector3(-0.012, 0.075, -0.07)  # in the fist: the grip runs along the hand's local +Z
		d["slot"].add_child(w)
		d["wnode"] = w


func _anim_for(f: Dictionary) -> String:
	match f["state"]:
		B.S.WALK: return "walk"
		B.S.JUMP: return "jump_kick" if f["attack"] == "jump_kick" else "jump"
		B.S.ATTACK:
			var a: String = f["attack"]
			return {"knife": "punch", "crate": "bat", "charge": "walk"}.get(a, a)
		B.S.HITSTUN: return "hit"
		B.S.DOWN: return "ko" if f["hp"] <= 0 else "down"
		B.S.GETUP: return "getup"
		B.S.GRABBED: return "held"
		B.S.GRABBING: return "grab"
		B.S.THROWN: return "thrown"
		B.S.DEAD: return "ko"
	return "idle"


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hit":
			_fx.hit(d["pos"] + Vector3(0, 0, 0.3), d["damage"] >= 14)
			_shake = 0.35 if d["damage"] >= 14 else 0.15
		"knockdown", "slam":
			_fx.dust(d["pos"] + Vector3(0, 0.1, 0))
			if kind == "slam":
				_shake = 0.6
		"ko":
			_fx.ko(d["pos"] + Vector3(0, 1.0, 0))
		"weapon_break":
			var f := e.by_id(d["id"])
			if not f.is_empty():
				_fx.splinters(f["pos"] + Vector3(f["facing"] * 0.8, 1.2, 0))


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	var e := game.engine
	if e == null or _set == null:
		return
	_time += delta
	var alive := {}
	for f in e.fighters:
		alive[f["id"]] = true
		if not _nodes.has(f["id"]):
			_nodes[f["id"]] = _fighter_node(f)
		var d: Dictionary = _nodes[f["id"]]
		var n: Node3D = d["node"]
		n.position = f["pos"]
		n.rotation.y = lerp_angle(n.rotation.y, PI * 0.5 * f["facing"], 1.0 - exp(-delta * 20.0))
		var a := _anim_for(f)
		var ap: AnimationPlayer = d["anim"]
		if a != d["last"] or (f["state"] == B.S.ATTACK and f["t"] < 0.02):
			ap.play(a, 0.06, 1.3 if f["state"] == B.S.ATTACK else 1.0)
			if a == "down" and d["last"] == "thrown":
				ap.seek(0.4, true)  # a throw lands straight into the fall's landing
			d["last"] = a
		if a == "walk":  # the jog's feet keep pace with the ground
			var v: Vector3 = f["vel"]
			ap.speed_scale = clampf(Vector2(v.x, v.z).length() / (JOG_SPEED * d["build"]), 0.6, 1.8)
		else:
			ap.speed_scale = 1.0
		_set_weapon(d, f["weapon"])
		# the fallen fade away; blinking while invulnerable
		n.visible = f["state"] != B.S.DEAD or ap.is_playing() or fmod(_time, 0.2) < 0.1
		if f["state"] == B.S.DEAD and not ap.is_playing():
			n.scale = n.scale.lerp(Vector3(1, 0.01, 1), delta * 2.0)
		if f["invuln"] > 0.0:
			n.visible = fmod(_time, 0.12) < 0.07
	# items on the ground
	var seen := {}
	for it in e.items:
		seen[it["id"]] = true
		if not _items.has(it["id"]):
			var n := _scene(it["kind"])
			n.position = it["pos"] + Vector3(0, 0.05, 0)
			n.rotation = Vector3(PI * 0.5 if it["kind"] != "crate" else 0.0, randf() * TAU, 0)
			_set.add_child(n)
			_items[it["id"]] = n
	for id in _items.keys():
		if not seen.has(id):
			_items[id].queue_free()
			_items.erase(id)
	for f in _flicker:  # buzzing signs: mostly on, dropping out in short stutters
		var ph: float = _time * 1.7 + f[2]
		var off := fmod(ph, 6.0) < 0.35 and sin(ph * 60.0) > -0.2
		(f[0] as StandardMaterial3D).emission_energy_multiplier = f[1] * (0.08 if off else 1.0)
	_place_camera(delta, e)
	if _rain:
		_rain.position = Vector3(_cam_x + 1.0, 8.5, -1.0)


func _place_camera(delta: float, e: BrawlEngine) -> void:
	_cam_x = lerpf(_cam_x, e.scroll + e.view_width * 0.5, 1.0 - exp(-delta * 4.0))
	_shake = maxf(0.0, _shake - delta * 3.0)
	var s := _shake * _shake * (0.25 if Settings.camera_shake else 0.0)
	var j := Vector3(sin(_time * 70.0), sin(_time * 61.0), 0) * s
	_camera.position = Vector3(_cam_x, 3.4, 10.5) + j
	_camera.look_at(Vector3(_cam_x, 1.1, -0.3) + j)
