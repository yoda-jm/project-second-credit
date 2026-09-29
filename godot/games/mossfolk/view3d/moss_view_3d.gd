class_name MossView3D
extends Node3D
## Mossfolk in 3D: the level is a thick block of rock standing in a deep cavern (MossSlab: a carved front face and
## walls extruded from the mask), seen a little from above; mosslings are little rigged creatures walking along its
## front lip, lit by their lanterns. Crystals, mushrooms and roots fill the cave, light falls in shafts through a
## haze behind, fireflies and spores drift. Pixel (x, y) of the level is world (x * 0.1, (h - y) * 0.1, 0).
##
## The camera: the player pans with the arrows or A/D (W/S when zoomed in), by dragging with the right or middle
## mouse button, or at the screen's left and right edges; the wheel zooms towards the cursor; Space jumps to the
## busiest mossling (again for the next); Home shows the whole height. The demo directs itself: it opens on the
## hatch, pulls back to the crowd and dollies in on whoever is digging, bashing, mining or building.
## The view breathes with a slow drift and kicks a little on big moments (a pop, the hatch opening).

const E = preload("res://games/mossfolk/engine/moss_engine.gd")
const M := "res://games/mossfolk/art/models/"
const TEX := "res://core/art/textures/"
const PX := 0.1
const ANIM := {"walk": "walk", "fall": "fall", "glide": "float", "climb": "climb", "dig": "dig", "bash": "bash",
	"mine": "mine", "build": "build", "block": "block", "shrug": "shrug", "panic": "panic", "splat": "splat",
	"exit": "exit", "drown": "drown"}
const WORK := ["dig", "bash", "mine", "build"]
const ZOOM_MIN := 0.85
const ZOOM_MAX := 3.2
const BAR := 0.18         ## the HUD's skill bar, the lower part of the screen
## per theme: earth, deep earth, moss, steel, cave light, backdrop
const THEMES := [
	{"earth": Color(0.5, 0.36, 0.24), "earth2": Color(0.33, 0.23, 0.16), "moss": Color(0.38, 0.66, 0.24), "steel": Color(0.36, 0.4, 0.46),
		"light": Color(0.55, 0.85, 1.0), "cave": Color(0.08, 0.1, 0.14)},
	{"earth": Color(0.56, 0.44, 0.34), "earth2": Color(0.38, 0.3, 0.26), "moss": Color(0.55, 0.62, 0.25), "steel": Color(0.4, 0.4, 0.44),
		"light": Color(1.0, 0.75, 0.45), "cave": Color(0.12, 0.09, 0.08)},
	{"earth": Color(0.4, 0.38, 0.44), "earth2": Color(0.26, 0.25, 0.32), "moss": Color(0.3, 0.6, 0.5), "steel": Color(0.34, 0.38, 0.46),
		"light": Color(0.6, 0.6, 1.0), "cave": Color(0.07, 0.07, 0.13)},
	{"earth": Color(0.62, 0.6, 0.58), "earth2": Color(0.42, 0.42, 0.44), "moss": Color(0.5, 0.72, 0.32), "steel": Color(0.4, 0.44, 0.5),
		"light": Color(0.8, 1.0, 0.75), "cave": Color(0.09, 0.12, 0.1)},
	{"earth": Color(0.52, 0.28, 0.2), "earth2": Color(0.3, 0.16, 0.12), "moss": Color(0.72, 0.5, 0.2), "steel": Color(0.3, 0.3, 0.34),
		"light": Color(1.0, 0.55, 0.3), "cave": Color(0.12, 0.06, 0.05)},
]

@export var game: MossGame

var camera: Camera3D
var cam_x := 0.0            ## where the view is headed: the centre of the play area, in level pixels
var cam_y := 0.0
var zoom := 1.0             ## 1: the level's height fills the play area
var _x := 0.0               ## where the view is now (smoothed)
var _y := 0.0
var _z := 1.0
var _pitch := 14.0
var _yaw := 0.0
var _pitch_to := 14.0
var _yaw_to := 0.0
var _drag := false
var _busy := 0
var _shot := "intro"        ## the demo's current shot: intro, wide, close
var _shot_t := 0.0
var _shot_id := -1
var _wide_for := 0.0
var _attr: CameraAttributesPractical
var _env: Environment
var _stage: Node3D
var _slab: MossSlab
var _mask: Image
var _mask_tex: ImageTexture
var _folk := {}             ## id -> {node, anim, last, label}
var _props: Array = []      ## [node, x, y]: sink out of sight when the ground under them is dug away
var _hatch: Node3D
var _hatch_light: OmniLight3D
var _burrow_light: OmniLight3D
var _water_mats: Array[StandardMaterial3D] = []
var _fx: Bursts
var _garden: MossGarden
var _punch := 0.0           ## a camera kick on big moments (a pop, the hatch), decaying
var _shake := Vector3.ZERO
var _time := 0.0
var _lv: MossLevel


func px(x: float, y: float, z := 0.0) -> Vector3:
	return Vector3(x * PX, (_lv.h - y) * PX, z)


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_energy = 0.4
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.1
	_env.glow_enabled = true
	_env.glow_intensity = 0.75
	_env.glow_bloom = 0.08
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_env.ssao_radius = 0.8
	_env.ssao_intensity = 1.6
	_env.ssil_enabled = true      # bounce light: lanterns and crystals tint the rock round them
	_env.ssil_intensity = 0.9
	_env.volumetric_fog_enabled = true   # a thin haze: halos round the lights, shafts behind
	_env.volumetric_fog_density = 0.004
	_env.volumetric_fog_length = 80.0
	_env.volumetric_fog_ambient_inject = 0.25
	_env.volumetric_fog_gi_inject = 0.0
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.1
	_env.adjustment_contrast = 1.05
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	# the key light from above and in front, and a cool rim from behind the slab
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-40, -28, 0)
	key.light_energy = 0.8
	key.shadow_enabled = true
	key.shadow_blur = 1.5
	key.directional_shadow_max_distance = 80.0
	key.light_color = Color(1.0, 0.94, 0.84)
	key.light_volumetric_fog_energy = 0.0
	add_child(key)
	var rim := DirectionalLight3D.new()
	rim.name = "Rim"
	rim.rotation_degrees = Vector3(-35, 160, 0)
	rim.light_energy = 0.45
	rim.light_volumetric_fog_energy = 0.0
	add_child(rim)
	camera = Camera3D.new()
	camera.fov = 30
	camera.current = true
	_attr = CameraAttributesPractical.new()
	_attr.dof_blur_far_enabled = true
	_attr.dof_blur_amount = 0.06
	camera.attributes = _attr
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 26.5   # this game's sizes: its median burst about 0.4 m across, a little more at birth
	add_child(_fx)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String, fallback := Vector3(0.6, 0.8, 0.4), col := Color(0.5, 0.7, 0.4)) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := CapsuleMesh.new()
	b.radius = fallback.x * 0.5
	b.height = fallback.y
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	b.material = m
	mi.mesh = b
	mi.position.y = fallback.y * 0.5
	n.add_child(mi)
	return n


func _on_level(e: MossEngine) -> void:
	e.event.connect(_on_event)
	_lv = e.level
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_folk.clear()
	_props.clear()
	_water_mats.clear()
	var th: Dictionary = THEMES[_lv.theme % THEMES.size()]
	_garden = MossGarden.new()
	_garden.fx = _fx
	_stage.add_child(_garden)
	_garden.build_backdrop(_lv.w, _lv.h, _lv.theme, _lv.name.hash())
	_env.background_color = (_garden.pal["top"] as Color)
	_env.ambient_light_color = th["light"].lerp(Color.WHITE, 0.4)
	_env.volumetric_fog_albedo = th["cave"].lerp(th["light"], 0.35)
	(get_node("Rim") as DirectionalLight3D).light_color = th["light"]
	# the terrain mask: R solid, G steel
	_mask = Image.create(_lv.w, _lv.h, false, Image.FORMAT_RG8)
	_refresh(Rect2i(0, 0, _lv.w, _lv.h), e)
	_mask_tex = ImageTexture.create_from_image(_mask)
	var shader: Shader = load("res://games/mossfolk/shaders/moss_terrain.gdshader")
	_slab = MossSlab.new()
	_stage.add_child(_slab)
	var grass := ShaderMaterial.new()
	grass.shader = load("res://games/mossfolk/shaders/moss_grass.gdshader")
	grass.set_shader_parameter("base_col", th["moss"].darkened(0.55))
	grass.set_shader_parameter("tip_col", th["moss"].lightened(0.25))
	grass.set_shader_parameter("glow", th["light"])
	_slab.setup(_lv.w, _lv.h, e.terrain, _lv.terrain, _terrain_mat(shader, th, false), _terrain_mat(shader, th, true), grass)
	_backdrop(th)
	_water(th)
	_haze(th)
	# hatch, burrow and traps
	_hatch = _scene("hatch", Vector3(2.0, 0.6, 1.0), Color(0.4, 0.3, 0.2))
	_hatch.position = px(_lv.entrance.x, _lv.entrance.y - 1, 0.05)
	_stage.add_child(_hatch)
	_hatch_light = _omni(_hatch, th["light"].lerp(Color(1.0, 0.8, 0.5), 0.5), 1.2, 3.5, Vector3(0, -0.4, 0.8), 1.5)
	var burrow := _scene("burrow", Vector3(2.0, 2.5, 1.0), Color(0.9, 0.7, 0.3))
	burrow.position = px(_lv.exit.x, _lv.exit.y + 1, 0.0)
	_stage.add_child(burrow)
	_play_loop(burrow, "glow")
	_burrow_light = _omni(burrow, Color(1.0, 0.72, 0.38), 2.4, 4.5, Vector3(0, 1.1, 1.0), 2.5)
	_motes(burrow, Color(1.6, 1.1, 0.5), Vector3(0.5, 0.2, 0.3), 24, Vector3(0, 0.5, 0.2), 0.25)
	for t in _lv.traps:
		var n := _scene("trap_" + t["kind"], Vector3(0.8, 1.0, 0.8), Color(0.6, 0.2, 0.3))
		n.position = px(t["pos"].x, t["pos"].y + 1, 0.05)
		_stage.add_child(n)
		_play_loop(n, "idle")
	# fireflies over the whole level, spores drifting down
	var ext := Vector3(_lv.w * PX * 0.5, _lv.h * PX * 0.5, 1.4)
	var mid := Vector3(_lv.w * PX * 0.5, _lv.h * PX * 0.5, -0.6)
	var ff := _motes(_stage, Color(2.0, 1.7, 0.7).lerp(th["light"] * 2.0, 0.3), ext, _lv.w / 3, Vector3(0, 0.05, 0), 0.07)
	ff.position = mid
	var sp := _motes(_stage, th["light"].lerp(Color.WHITE, 0.5) * 0.9, ext, _lv.w / 4, Vector3(0, -0.12, 0), 0.05)
	sp.position = mid
	# the view: the demo opens on the hatch, the player starts looking at it
	_x = _lv.entrance.x
	_y = _lv.h * 0.5
	_z = 1.0
	cam_x = _x
	cam_y = _y
	zoom = 1.0
	_busy = 0
	_shot = "intro"
	_shot_t = 0.0
	if game.demo:
		_z = 2.4
		_y = _lv.entrance.y + 10
		_pitch = 8.0
		_yaw = -14.0
	_place_camera(0.0)


func _omni(parent: Node3D, col: Color, energy: float, rng: float, at: Vector3, fog := 0.0) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = col
	l.light_energy = energy
	l.omni_range = rng
	l.omni_attenuation = 1.4
	l.position = at
	l.light_volumetric_fog_energy = fog
	parent.add_child(l)
	return l


## Drifting glowing specks: fireflies, spores, motes rising from the burrow.
func _motes(parent: Node3D, col: Color, extent: Vector3, amount: int, drift: Vector3, size: float) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = maxi(4, amount)
	p.lifetime = 7.0
	p.preprocess = 7.0
	p.use_fixed_seed = true
	p.fixed_fps = 30
	p.visibility_aabb = AABB(-extent - Vector3.ONE * 2.0, (extent + Vector3.ONE * 2.0) * 2.0)
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = extent
	pm.gravity = drift
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 180.0
	pm.initial_velocity_min = 0.02
	pm.initial_velocity_max = 0.15
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.6
	pm.turbulence_noise_scale = 3.0
	pm.turbulence_noise_speed_random = 0.3
	pm.scale_min = 0.556
	pm.scale_max = 1.44
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.2, 0.45, 0.55, 0.8, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0.35), Color(1, 1, 1, 1),
		Color(1, 1, 1, 0.8), Color(1, 1, 1, 0)])
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	q.material = Fx.material("glow", col)
	p.draw_pass_1 = q
	parent.add_child(p)
	return p


func _terrain_mat(shader: Shader, th: Dictionary, wall: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = shader
	m.set_shader_parameter("mask", _mask_tex)
	m.set_shader_parameter("mask_soft", _mask_tex)
	m.set_shader_parameter("size", Vector2(_lv.w, _lv.h))
	m.set_shader_parameter("wall", wall)
	m.set_shader_parameter("px_size", PX)
	m.set_shader_parameter("front", MossSlab.FRONT)
	m.set_shader_parameter("depth", MossSlab.DEPTH)
	m.set_shader_parameter("col_earth", th["earth"])
	m.set_shader_parameter("col_earth2", th["earth2"])
	m.set_shader_parameter("col_moss", th["moss"])
	m.set_shader_parameter("col_steel", th["steel"])
	m.set_shader_parameter("col_glow", th["light"])
	m.set_shader_parameter("seed", float(_lv.theme) * 7.3)
	for pair in [["rock", "rock"], ["soil", "soil"], ["moss", "grass_lush"], ["metal", "metal"]]:
		m.set_shader_parameter(pair[0] + "_albedo", load(TEX + pair[1] + "/albedo.jpg"))
		m.set_shader_parameter(pair[0] + "_normal", load(TEX + pair[1] + "/normal.jpg"))
	return m


func _refresh(r: Rect2i, e: MossEngine) -> void:
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			var v := e.terrain[y * _lv.w + x]
			_mask.set_pixel(x, y, Color(1.0 if v != E.AIR else 0.0, 1.0 if v == E.STEEL else 0.0, 0))


## The cave's dressing: glowing crystals and mushrooms along the ground, roots from the ceiling (the grotto beyond,
## the giant mushrooms and the light are MossGarden's).
func _backdrop(th: Dictionary) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = _lv.name.hash()
	# along the ground tops, on the slab's upper faces behind the mosslings' lane
	var props := ["mushroom_big", "mushroom_small", "crystal_cluster", "fern", "fern", "mushroom_small"]
	var x := 4
	while x < _lv.w - 4:
		x += rng.randi_range(12, 34)
		var y := _top(x)
		if y < 0:
			continue
		var kind: String = props[rng.randi_range(0, props.size() - 1)]
		var n := _scene(kind, Vector3(0.3, 0.4, 0.3), th["moss"])
		n.position = px(x, y, rng.randf_range(-MossSlab.DEPTH + 0.4, -0.6))
		n.rotation.y = rng.randf() * TAU
		n.scale = Vector3.ONE * rng.randf_range(0.8, 1.7)
		_stage.add_child(n)
		_props.append([n, x, y])
		if kind.begins_with("mushroom"):
			# the mushrooms are the stars of the ledges: bigger, glossy, bouncing, with a smaller one or two beside
			var big := kind == "mushroom_big"
			n.scale = Vector3.ONE * (rng.randf_range(1.5, 2.3) if big else rng.randf_range(1.8, 2.6))
			_garden.add_shroom(n, x, y, big, _stage)
			for j in rng.randi_range(1, 2):
				var xx := clampi(x + rng.randi_range(4, 9) * (1 if j == 1 else -1), 1, _lv.w - 2)
				var yy := _top(xx)
				if yy < 0 or absi(yy - y) > 6:
					continue
				var m := _scene("mushroom_small" if big else "mushroom_big", Vector3(0.3, 0.4, 0.3), th["moss"])
				m.position = px(xx, yy, n.position.z + rng.randf_range(-0.3, 0.4))
				m.rotation.y = rng.randf() * TAU
				m.scale = Vector3.ONE * rng.randf_range(0.9, 1.4)
				_stage.add_child(m)
				_props.append([m, xx, yy])
				_garden.add_shroom(m, xx, yy, not big, _stage)
		if kind == "crystal_cluster":
			_glow(n, th["light"], 0.45)
			_omni(n, th["light"], 1.0, 2.6, Vector3(0, 0.5, 0.2), 0.6)
	for i in _lv.w / 50:
		var r := _scene("root_hang", Vector3(0.1, 0.8, 0.1), th["earth2"])
		r.position = Vector3(rng.randf_range(0.0, _lv.w * PX), _lv.h * PX + 0.5, rng.randf_range(-MossSlab.DEPTH, -0.8))
		r.scale = Vector3.ONE * rng.randf_range(1.0, 2.0)
		_stage.add_child(r)
	_garden.add_giants(_lv.w, _lv.h, load(M + "mushroom_big.glb"))
	# big crystals deep in the cave, glowing through the haze
	for i in _lv.w / 90:
		var c := _scene("crystal_cluster", Vector3(0.3, 0.4, 0.3), th["light"])
		c.position = Vector3(rng.randf_range(-4.0, _lv.w * PX + 4.0), rng.randf_range(-2.0, _lv.h * PX * 0.5), rng.randf_range(-8.0, -6.5))
		c.scale = Vector3.ONE * rng.randf_range(2.2, 3.6)
		c.rotation = Vector3(rng.randf_range(-0.3, 0.3), rng.randf() * TAU, rng.randf_range(-0.3, 0.3))
		_stage.add_child(c)
		_glow(c, th["light"], 0.18)
		_omni(c, th["light"], 1.2, 5.0, Vector3(0, 0.4, 0.3), 1.0)
	# lanterns on posts here and there, on the ledges behind
	for i in _lv.w / 120:
		var xx := rng.randi_range(20, _lv.w - 20)
		var yy := _top(xx)
		if yy < 0:
			continue
		var lp := _scene("lantern_post", Vector3(0.1, 1.2, 0.1), Color(1.0, 0.8, 0.4))
		lp.position = px(xx, yy, -0.7)
		_stage.add_child(lp)
		_props.append([lp, xx, yy])
		_omni(lp, Color(1.0, 0.72, 0.4), 1.8, 4.0, Vector3(0, 1.1, 0.4), 2.0)


## Tones a model's glowing parts down (and into the theme's light), so the big crystals glow without glaring.
func _glow(n: Node, col: Color, energy: float) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		for i in mesh.get_surface_count():
			var m := mesh.surface_get_material(i) as StandardMaterial3D
			if m and m.emission_enabled:
				var d := m.duplicate() as StandardMaterial3D
				d.emission = d.emission.lerp(col, 0.5)
				d.emission_energy_multiplier *= energy
				(mi as MeshInstance3D).set_surface_override_material(i, d)


func _top(x: int) -> int:
	for y in range(1, _lv.h):
		if _lv.terrain[y * _lv.w + x] != E.AIR and _lv.terrain[(y - 1) * _lv.w + x] == E.AIR:
			return y
	return -1


## Light falling in shafts from cracks high in the cave, through a thicker haze behind the slab.
func _haze(th: Dictionary) -> void:
	var fv := FogVolume.new()
	fv.shape = RenderingServer.FOG_VOLUME_SHAPE_BOX
	fv.size = Vector3(_lv.w * PX + 40.0, _lv.h * PX + 20.0, 6.0)
	fv.position = Vector3(_lv.w * PX * 0.5, _lv.h * PX * 0.5, -MossSlab.DEPTH - 3.4)
	var fm := FogMaterial.new()
	fm.density = 0.06
	fm.albedo = th["cave"].lerp(th["light"], 0.6)
	fm.emission = th["light"] * 0.015
	var fn := FastNoiseLite.new()
	fn.frequency = 0.08
	# built here rather than by a NoiseTexture3D, whose generating thread can outlive a quick quit
	var layers := fn.get_image_3d(64, 64, 32)
	var nt := ImageTexture3D.new()
	nt.create(layers[0].get_format(), 64, 64, 32, false, layers)
	fm.density_texture = nt
	fv.material = fm
	_stage.add_child(fv)
	var rng := RandomNumberGenerator.new()
	rng.seed = _lv.name.hash() + 5
	for i in maxi(2, _lv.w / 200):
		var s := SpotLight3D.new()
		s.light_color = th["light"].lerp(Color(1.0, 0.95, 0.8), 0.5)
		s.light_energy = 3.0
		s.light_volumetric_fog_energy = 14.0
		s.spot_range = 40.0
		s.spot_angle = 6.0
		s.spot_attenuation = 0.6
		s.shadow_enabled = true
		var at := Vector3((i + 0.5 + rng.randf_range(-0.2, 0.2)) * _lv.w * PX / maxi(2, _lv.w / 200), _lv.h * PX + 14.0, -6.0)
		s.position = at
		_stage.add_child(s)
		s.look_at(at + Vector3(rng.randf_range(-5.0, 5.0), -20.0, 1.2), Vector3.FORWARD)


func _water(th: Dictionary) -> void:
	for r in _lv.water:
		var q := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3(r.size.x * PX, r.size.y * PX, MossSlab.FRONT + MossSlab.DEPTH - 0.04)
		q.mesh = b
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(th["light"].darkened(0.4), 0.7)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.emission_enabled = true
		m.emission = th["light"] * 0.3
		m.roughness = 0.05
		m.metallic_specular = 1.0
		m.normal_enabled = true
		m.normal_texture = load(TEX + "water/normal.png")
		m.normal_scale = 0.6
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true
		m.uv1_scale = Vector3.ONE * 0.4
		q.material_override = m
		_water_mats.append(m)
		q.position = px(r.position.x + r.size.x * 0.5, r.position.y + r.size.y * 0.5, (MossSlab.FRONT - MossSlab.DEPTH) * 0.5)
		_stage.add_child(q)


func _play_loop(n: Node, anim: String) -> void:
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR
		ap.play(anim)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hatch":
			var ap: AnimationPlayer = _hatch.find_child("AnimationPlayer", true, false)
			if ap and ap.has_animation("open"):
				ap.play("open")
			_hatch_light.light_energy = 5.0
			_garden.bump(_lv.entrance.x, _lv.entrance.y, 0.7, 2000.0, 1.0)   # a ripple of bounces along the level
			_punch = maxf(_punch, 0.5)
			_fx.burst(_hatch.position + Vector3(0, -0.3, 0.3), Color(1.0, 0.85, 0.5), 20, 1.5, 0.9, 0.08, 1.0, -1.0, -1.0, "glow")
		"stroke":
			var c: Dictionary = e.folk[d["id"]]
			var th: Dictionary = THEMES[_lv.theme % THEMES.size()]
			_fx.burst(px(c["x"] + c["dir"] * 4, c["y"] - 2, 0.3), th["earth2"], 6, 1.5, 0.5, 0.06, 0.0, -6.0, 0.8, "smoke")
		"pop":
			_fx.burst(px(d["x"], d["y"], 0.3), Color(1.0, 0.7, 0.3), 36, 4.0, 0.7, 0.14, 1.0, -4.0, 1.0, "glow")
			_fx.flash(px(d["x"], d["y"], 0.3) - Vector3(0, 2.5, -1.0), Color(1.0, 0.6, 0.3), 3.0)
			_garden.bump(d["x"], d["y"], 1.3, 90.0)
			_punch = maxf(_punch, 1.0)
		"death":
			if d["how"] == "drown":
				_fx.burst(px(d["x"], d["y"], 0.2), Color(0.6, 0.85, 1.0), 14, 1.2, 0.8, 0.06, 1.0, 1.0, 1.0, "glow")
			elif d["how"] == "splat":
				_fx.burst(px(d["x"], d["y"], 0.2), THEMES[_lv.theme % THEMES.size()]["moss"], 16, 2.0, 0.5, 0.07, 0.0, -6.0, 0.6)
		"saved":
			_fx.burst(px(_lv.exit.x, _lv.exit.y - 8, 0.4), Color(1.0, 0.85, 0.4), 12, 1.5, 0.6, 0.08, 1.0, 1.0, 1.0, "glow")
			_burrow_light.light_energy = 5.0
			_garden.bump(_lv.exit.x, _lv.exit.y, 0.5, 45.0)


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _lv == null:
		return
	if e.changed.size != Vector2i.ZERO:
		_refresh(e.changed, e)
		_slab.rebuild(e.changed)
		_sink_props(e.changed)
		e.changed = Rect2i()
		_mask_tex.update(_mask)
	_hatch_light.light_energy = move_toward(_hatch_light.light_energy, 1.2, delta * 3.0)
	_burrow_light.light_energy = move_toward(_burrow_light.light_energy, 2.4 + 0.5 * sin(_time * 2.2), delta * 4.0)
	for m in _water_mats:
		m.uv1_offset = Vector3(_time * 0.03, _time * 0.05, 0.0)
	for c in e.folk:
		var id: int = c["id"]
		var gone: bool = c["state"] == "gone"
		if not _folk.has(id):
			if gone:
				continue
			var n := _scene("mossling", Vector3(0.5, 0.9, 0.5), Color(0.4, 0.7, 0.35))
			_stage.add_child(n)
			var lb := Label3D.new()
			lb.font = HudKit.font(true)
			lb.font_size = 64
			lb.pixel_size = 0.006
			lb.outline_size = 12
			lb.position = Vector3(0, 1.45, 0.2)
			lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			lb.no_depth_test = true
			n.add_child(lb)
			var lantern := _omni(n, Color(1.0, 0.78, 0.42), 0.4, 2.2, Vector3(0.2, 1.1, 1.15), 0.3)  # its lantern, held out clear of the body
			lantern.omni_attenuation = 2.0
			_folk[id] = {"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": "", "label": lb,
				"pos": px(c["x"], c["y"] + 1)}
		var f: Dictionary = _folk[id]
		var node: Node3D = f["node"]
		if gone:
			node.queue_free()
			_folk.erase(id)
			continue
		# a landing shakes the mushrooms round it
		var st: String = c["state"]
		if f.get("st", "") in ["fall", "glide"] and st in ["walk", "shrug", "block"]:
			_garden.bump(c["x"], c["y"], 0.9 if f["st"] == "fall" else 0.6, 36.0)
		f["st"] = st
		var target := px(c["x"], c["y"] + 1, 0.0)
		f["pos"] = (f["pos"] as Vector3).lerp(target, minf(1.0, delta * 18.0))
		node.position = f["pos"]
		# the model faces +X with its tool side to the camera: walking left mirrors it
		var sx := 1.4 if c["dir"] > 0 else -1.4
		node.scale = Vector3(move_toward(node.scale.x, sx, delta * 18.0), 1.4, 1.4)
		var want: String = ANIM.get(c["state"], "walk")
		var ap: AnimationPlayer = f["anim"]
		if ap and f["last"] != want and ap.has_animation(want):
			f["last"] = want
			var a := ap.get_animation(want)
			a.loop_mode = Animation.LOOP_NONE if want in ["shrug", "splat", "exit", "drown"] else Animation.LOOP_LINEAR
			ap.play(want, 0.12)
		var lb: Label3D = f["label"]
		var b: int = c["bomb"]
		lb.visible = b >= 0 and c["state"] != "panic"
		if lb.visible:
			lb.text = str(5 - int(b * E.TICK))
			lb.modulate = Color(1.0, 0.85 - b / 170.0, 0.4)
	_garden.update(delta, e.folk)
	_place_camera(delta)


## Props standing on ground that has been dug away drop out of sight.
func _sink_props(r: Rect2i) -> void:
	var grown := r.grow(2)
	for p in _props:
		var n: Node3D = p[0]
		if n.visible and grown.has_point(Vector2i(p[1], p[2])) and game.engine.terrain[int(p[2]) * _lv.w + int(p[1])] == E.AIR:
			n.set_meta("sinking", true)
			var tw := n.create_tween()
			tw.tween_property(n, "scale", Vector3.ONE * 0.01, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
			tw.tween_callback(n.hide)


# --- the camera -----------------------------------------------------------------------------------------------

## Half the view's height on the level plane, in world units, at a zoom.
func _half_h(z: float) -> float:
	return _lv.h * PX * 0.5 / (1.0 - BAR) / z


## Keeps a view centre (level pixels) on the level, with a little room past its ends.
func _clamp_centre(p: Vector2, z: float) -> Vector2:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var hw := _half_h(z) * aspect / PX
	var hh := _half_h(z) * (1.0 - BAR) / PX
	var margin := 14.0
	var out := p
	out.x = _lv.w * 0.5 if _lv.w + margin * 2.0 <= hw * 2.0 else clampf(p.x, hw - margin, _lv.w - hw + margin)
	out.y = _lv.h * 0.5 if _lv.h + 12.0 <= hh * 2.0 else clampf(p.y, hh - 12.0, _lv.h - hh)
	return out


## Sends the view to a level pixel (the minimap, the busiest-mossling key).
func jump_to(x: float, y := -1.0) -> void:
	cam_x = x
	if y >= 0.0:
		cam_y = y


## World units per screen pixel on the level plane.
func _units_per_pixel() -> float:
	return _half_h(_z) * 2.0 / maxf(1.0, get_viewport().get_visible_rect().size.y)


func _unhandled_input(event: InputEvent) -> void:
	if game.demo or _lv == null:
		return
	if event is InputEventMouseButton:
		match event.button_index:
			MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE:
				_drag = event.pressed
				get_viewport().set_input_as_handled()
			MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN:
				if event.pressed:
					var f := 1.18 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.18
					_zoom_at(clampf(zoom * f, ZOOM_MIN, ZOOM_MAX), event.position)
					get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion and _drag:
		# grab the level: it follows the mouse one to one
		var k: float = _units_per_pixel() / PX
		cam_x -= event.relative.x * k
		cam_y -= event.relative.y * k
		var c := _clamp_centre(Vector2(cam_x, cam_y), zoom)
		cam_x = c.x
		cam_y = c.y
		_x = lerpf(_x, cam_x, 0.85)
		_y = lerpf(_y, cam_y, 0.85)
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_SPACE:
				_jump_busiest()
				get_viewport().set_input_as_handled()
			KEY_HOME:
				zoom = 1.0
				get_viewport().set_input_as_handled()


## Zooms keeping the level point under the cursor where it is.
func _zoom_at(z: float, screen: Vector2) -> void:
	var p := pixel_at(screen)
	if p.x < -900.0:
		zoom = z
		return
	var k := zoom / z
	cam_x = p.x + (cam_x - p.x) * k
	cam_y = p.y + (cam_y - p.y) * k
	zoom = z


## The busiest mossling: working ones first, then fallers, blockers, walkers; each press takes the next.
func _jump_busiest() -> void:
	var e := game.engine
	var list := []
	for c in e.folk:
		if c["state"] in ["gone", "exit", "splat", "drown"]:
			continue
		var score := 3 if c["state"] in WORK else (2 if c["state"] in ["fall", "glide", "climb", "panic"] else (1 if c["state"] == "block" else 0))
		list.append([score, c["x"], c["y"]])
	if list.is_empty():
		return
	list.sort_custom(func(a, b): return a[0] > b[0] or (a[0] == b[0] and a[1] < b[1]))
	_busy = _busy % list.size()
	jump_to(list[_busy][1], list[_busy][2] - 5)
	_busy += 1


func _place_camera(delta: float) -> void:
	var e := game.engine
	var vp := get_viewport().get_visible_rect().size
	var rate := 7.0
	if game.demo:
		rate = _direct(delta, e)
	else:
		_steer(delta, vp)
		_pitch_to = 14.0 - (_z - 1.0) * 2.5
		# a touch of turn as the view travels along the level, so the carved walls show their sides
		_yaw_to = clampf((_x - _lv.w * 0.5) / maxf(1.0, _lv.w * 0.5), -1.0, 1.0) * 6.0
	zoom = clampf(zoom, ZOOM_MIN, ZOOM_MAX)
	var c := _clamp_centre(Vector2(cam_x, cam_y), zoom)
	cam_x = c.x
	cam_y = c.y
	var k := 1.0 - exp(-rate * delta) if delta > 0.0 else 1.0
	_z = lerpf(_z, zoom, k)
	var now := _clamp_centre(Vector2(lerpf(_x, cam_x, k), lerpf(_y, cam_y, k)), _z)
	_x = now.x
	_y = now.y
	_pitch = lerpf(_pitch, _pitch_to, k * 0.6)
	_yaw = lerpf(_yaw, _yaw_to, k * 0.6)
	var hh := _half_h(_z)
	var dist := hh / tan(deg_to_rad(camera.fov * 0.5))
	# the play area is the screen above the bar: its centre sits a little above the screen's
	var look := Vector3(_x * PX, (_lv.h - _y) * PX - hh * BAR, 0.0)
	var off := Basis(Vector3.UP, deg_to_rad(_yaw)) * Basis(Vector3.RIGHT, deg_to_rad(-_pitch)) * Vector3(0, 0, dist)
	# a slow breathing drift, and a kick on big moments that settles in a moment
	_punch = maxf(0.0, _punch - delta * 2.5)
	if _punch > 0.0:
		_shake = Vector3(sin(_time * 53.0), sin(_time * 41.0 + 1.3), 0.0) * _punch * _punch * 0.06 * hh / 10.0
	else:
		_shake = Vector3.ZERO
	var drift := Vector3(sin(_time * 0.21), sin(_time * 0.17 + 1.1), 0.0) * 0.12 * hh / 10.0
	camera.position = look + off + drift + _shake
	camera.look_at(look + drift * 0.6, Vector3.UP)
	camera.fov = 30.0 - 1.2 * _punch * _punch
	# focus on the slab's front; the far cave softens
	_attr.dof_blur_far_distance = dist + 3.0
	_attr.dof_blur_far_transition = 6.0 + dist * 0.2


## The player's view: keys, screen edges (the drag and the wheel come through _unhandled_input).
func _steer(delta: float, vp: Vector2) -> void:
	var sx := 0.0
	var sy := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A): sx -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D): sx += 1.0
	if Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W): sy -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S): sy += 1.0
	if not _drag and _mouse_inside():
		# the edges: slow at first, faster the deeper the pointer goes (not over the skill bar)
		var mp := get_viewport().get_mouse_position()
		var m := 40.0
		if mp.y < vp.y * (1.0 - BAR):
			if mp.x < m: sx -= pow((m - mp.x) / m, 2.0)
			if mp.x > vp.x - m: sx += pow((mp.x - (vp.x - m)) / m, 2.0)
			if mp.y < m * 0.6: sy -= pow((m * 0.6 - mp.y) / (m * 0.6), 2.0)
	if sx == 0.0 and sy == 0.0:
		return
	# about two thirds of the view's width a second at full tilt
	var view_w := _half_h(_z) * 2.0 * vp.aspect() / PX
	var fast := 1.8 if Input.is_key_pressed(KEY_SHIFT) else 1.0
	cam_x += sx * view_w * 0.65 * fast * delta
	cam_y += sy * view_w * 0.65 * fast * delta / vp.aspect()


func _mouse_inside() -> bool:
	if not DisplayServer.window_is_focused():
		return false
	var wr := Rect2i(DisplayServer.window_get_position(), DisplayServer.window_get_size())
	return wr.has_point(DisplayServer.mouse_get_position())


## The demo's director: opens on the hatch, pulls back to the crowd, dollies in on someone at work, pulls back.
## Returns how quickly the camera eases towards its shot.
func _direct(delta: float, e: MossEngine) -> float:
	_shot_t += delta
	match _shot:
		"intro":
			cam_x = _lv.entrance.x
			cam_y = _lv.entrance.y + 12
			zoom = 2.2
			_pitch_to = 9.0
			_yaw_to = -12.0
			if _shot_t > 3.2:
				_cut("wide")
			return 0.6
		"close":
			var c := _folk_by_id(e, _shot_id)
			if c.is_empty() or c["state"] in ["gone", "exit", "splat", "drown"] or _shot_t > 6.0:
				_cut("wide")
			else:
				cam_x = c["x"] + c["dir"] * 6
				cam_y = c["y"] - 6
				zoom = 2.6
				_pitch_to = 8.0
				_yaw_to = -16.0 * c["dir"]
				return 1.1
	# wide: the crowd, weighted to those at work; after a while, dolly in on one of them
	var sum := Vector2.ZERO
	var n := 0.0
	var worker := -1
	for c in e.folk:
		if c["state"] in ["gone", "exit"]:
			continue
		var wgt := 4.0 if c["state"] in WORK or c["state"] in ["climb", "glide"] else 1.0
		sum += Vector2(c["x"], c["y"]) * wgt
		n += wgt
		if c["state"] in WORK and worker < 0:
			worker = c["id"]
	if n > 0.0:
		cam_x = sum.x / n
		cam_y = sum.y / n - 10.0
	else:
		cam_x = lerpf(cam_x, _lv.exit.x, delta * 0.3)
	zoom = 1.25
	_pitch_to = 15.0
	_yaw_to = 7.0 * sin(_time * 0.18)
	if worker >= 0 and _shot_t > 4.5:
		_shot_id = worker
		_cut("close")
	return 0.9


func _cut(to: String) -> void:
	_shot = to
	_shot_t = 0.0


func _folk_by_id(e: MossEngine, id: int) -> Dictionary:
	for c in e.folk:
		if c["id"] == id:
			return c
	return {}


## The level pixel under a screen point (for the cursor): where the ray meets the mosslings' plane, z = 0.
func pixel_at(screen: Vector2) -> Vector2:
	var o := camera.project_ray_origin(screen)
	var d := camera.project_ray_normal(screen)
	if absf(d.z) < 0.0001:
		return Vector2(-999, -999)
	var p := o + d * (-o.z / d.z)
	return Vector2(p.x / PX, _lv.h - p.y / PX)


## A mossling's screen position (for the HUD's cursor bracket).
func screen_of(c: Dictionary) -> Vector2:
	return camera.unproject_position(px(c["x"], c["y"] - 4, 0.0))
