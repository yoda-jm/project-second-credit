class_name HenView3D
extends Node3D
## Henhouse Heist in 3D: a farmyard diorama at golden hour seen from the side. Brick platforms with grass on top,
## wooden ladders, the lifts on their ropes, eggs in straw nests that twinkle, grain sacks that glint; a barn, a silo,
## a windmill and fields behind, rolling hills fading into the haze, soft clouds and the low sun, which sinks and
## reddens as the bonus clock runs down. A warm key light with long shadows, a rim light from the sun behind.
## The camera frames the whole level and leans gently towards the farmhand; it opens close on the farmhand and pulls
## out, punches in on a streak of eggs or a sack of grain, looks at the goose bursting out of its cage, shakes on a
## death and pulls back on a cleared level.
## Tile (x, y) is world ((x - 16) / 2, (13 - y) / 2), y up.

const E = preload("res://games/henhouse/engine/hen_engine.gd")
const M := "res://games/henhouse/art/models/"
const SH := "res://games/henhouse/view3d/"
const T := 0.5
const HERO_SCALE := 0.647
const HEN_SCALE := 0.6
const GOOSE_SCALE := 0.55
const GROUND_Y := -6.62
## hen colours: feather, speckle (the same as the feather hides the speckles)
const FEATHERS := [[Color(1.0, 0.98, 0.94), Color(1.0, 0.98, 0.94)], [Color(0.62, 0.32, 0.12), Color(0.62, 0.32, 0.12)],
	[Color(0.62, 0.62, 0.6), Color(0.08, 0.08, 0.08)], [Color(0.95, 0.8, 0.55), Color(0.95, 0.8, 0.55)]]
## where the sun sits (a direction from the camera): low on the right, behind the hills
const SUN_DIR := Vector3(0.36, 0.035, -0.93)

@export var game: HenGame

var camera: Camera3D
var _attrs: CameraAttributesPractical
var _env: Environment
var _sky_mat: ShaderMaterial
var _sun: DirectionalLight3D
var _rim: DirectionalLight3D
var _halo: MeshInstance3D
var _halo_mat: ShaderMaterial
var _clouds: Array[ShaderMaterial] = []
var _sparkle_mat: ShaderMaterial
var _glint_mat: ShaderMaterial
var _stage: Node3D
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _hero_last := ""
var _hens: Array[Dictionary] = []
var _eggs := {}
var _grain := {}
var _lifts: Array[Node3D] = []
var _goose: Node3D
var _goose_anim: AnimationPlayer
var _goose_pos := Vector3.ZERO
var _cage: Node3D
var _fx: HenFx
var _time := 0.0
var _mats := {}
var _dusk := 0.0
# the farmhand's feel: a squash on landing, a stretch on take-off
var _squash := 0.0
var _gust_t := 0.0
# camera state
var _dist := 25.0
var _lean := Vector2.ZERO
var _focus := Vector2.ZERO       ## where a punch-in looks (world x, y)
var _punch := 0.0
var _trauma := 0.0
var _intro := 1.0
var _intro_len := 1.6
var _goose_look := 0.0
var _goose_at := Vector2.ZERO
var _top_extra := 0.0         ## the goose's cage stands above the top row: frame it too
var _streak := 0
var _streak_t := 0.0
var _was := -1
var _sat := 1.0


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3((p.x - 16.0) * T, (13.0 - p.y) * T, z)


func _ready() -> void:
	_env = Environment.new()
	var sky := Sky.new()
	_sky_mat = _shader("sky.gdshader")
	_sky_mat.set_shader_parameter("sun_dir", SUN_DIR.normalized())
	sky.sky_material = _sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.ambient_light_energy = 0.42
	_env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 0.92
	_env.tonemap_white = 6.0
	_env.glow_enabled = true
	_env.glow_intensity = 0.55
	_env.glow_strength = 1.0
	_env.glow_bloom = 0.02
	_env.glow_hdr_threshold = 1.25
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	_env.ssao_enabled = true  # contact shadows under the ladders, in the brick joints and round the nests
	_env.ssao_radius = 0.7
	_env.ssao_intensity = 1.4
	_env.ssao_power = 1.4
	_env.ssao_light_affect = 0.15
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.15
	_env.adjustment_contrast = 1.1
	_env.fog_enabled = true  # the golden haze: the farm and fields behind stay back, the playfield stays crisp
	_env.fog_mode = Environment.FOG_MODE_DEPTH
	_env.fog_light_color = Color(0.96, 0.66, 0.46)
	_env.fog_sun_scatter = 0.25
	_env.fog_depth_begin = 29.0
	_env.fog_depth_end = 100.0
	_env.fog_depth_curve = 0.9
	_env.fog_density = 0.75
	_env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	# the key: the low sun, warm, from the right and a little in front, long shadows across the yard
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-24, 52, 0)
	_sun.light_energy = 1.8
	_sun.light_color = Color(1.0, 0.8, 0.56)
	_sun.shadow_enabled = true
	_sun.shadow_blur = 1.5
	_sun.shadow_bias = 0.04
	_sun.shadow_normal_bias = 1.2
	_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	_sun.directional_shadow_max_distance = 70.0
	_sun.directional_shadow_split_1 = 0.45
	add_child(_sun)
	# the rim: the same sun from behind (where the sky shows it), gilding every silhouette's edge
	_rim = DirectionalLight3D.new()
	_rim.light_energy = 1.6
	_rim.light_color = Color(1.0, 0.72, 0.4)
	_rim.light_specular = 1.4
	add_child(_rim)
	_rim.look_at_from_position(Vector3.ZERO, -SUN_DIR, Vector3.UP)
	# a cool fill from the sky on the left, so the shadowed sides read blue, not muddy
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-35, -70, 0)
	fill.light_energy = 0.28
	fill.light_color = Color(0.6, 0.72, 1.0)
	fill.light_specular = 0.0
	add_child(fill)
	camera = Camera3D.new()
	camera.fov = 32
	camera.far = 400.0
	camera.current = true
	# a soft far blur: the farm behind melts a little, the playfield stays sharp (a diorama's depth)
	_attrs = CameraAttributesPractical.new()
	_attrs.dof_blur_far_enabled = true
	_attrs.dof_blur_far_transition = 14.0
	_attrs.dof_blur_amount = 0.045
	camera.attributes = _attrs
	add_child(camera)
	_fx = HenFx.new()
	add_child(_fx)
	_sparkle_mat = _shader("sparkle.gdshader")
	_glint_mat = _shader("sparkle.gdshader")
	_glint_mat.set_shader_parameter("color", Color(1.0, 0.85, 0.45))
	_build_backdrop()
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _shader(file: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + file)
	return m


func _scene(name: String, size := Vector3(0.4, 0.4, 0.4), col := Color(0.8, 0.6, 0.4)) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	b.material = m
	mi.mesh = b
	mi.position.y = size.y * 0.5
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color, emit := 0.0) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col, emit]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = col
				if emit > 0.0:
					t.emission_enabled = true
					t.emission = col
					t.emission_energy_multiplier = emit
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _play(ap: AnimationPlayer, anim: String, loop := false, blend := 0.15) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, blend)


func _quad(size: Vector2, mat: Material, pos: Vector3, parent: Node = self) -> MeshInstance3D:
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = size
	q.mesh = qm
	q.material_override = mat
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	q.position = pos
	parent.add_child(q)
	return q


func _no_shadow(n: Node) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _sparkle(parent: Node3D, pos: Vector3, size: float, phase: float, mat: Material) -> MeshInstance3D:
	var q := _quad(Vector2(size, size), mat, pos, parent)
	q.set_instance_shader_parameter("phase", phase)
	return q


# ------------------------------------------------------------------ the backdrop

func _build_backdrop() -> void:
	# the fields: a patchwork running back to the hills, the trodden yard just behind the playfield
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(240, 120)
	ground.mesh = pm
	ground.material_override = _shader("fields.gdshader")
	ground.position = Vector3(0, GROUND_Y, -48)
	add_child(ground)
	# the far country: two ranges of hills (the nearer with poplars), then the clouds and the sun's halo
	var far := _shader("far_hills.gdshader")
	far.set_shader_parameter("size", Vector2(260, 34))
	far.set_shader_parameter("seed", 4.0)
	far.set_shader_parameter("layers_near", 0.0)
	far.set_shader_parameter("far_col", Color(0.78, 0.56, 0.6))
	far.set_shader_parameter("near_col", Color(0.62, 0.5, 0.46))
	far.set_shader_parameter("sun_x", 0.62)
	_quad(Vector2(260, 34), far, Vector3(0, GROUND_Y + 17.0 - 1.0, -104))
	var near := _shader("far_hills.gdshader")
	near.set_shader_parameter("size", Vector2(200, 22))
	near.set_shader_parameter("sun_x", 0.66)
	_quad(Vector2(200, 22), near, Vector3(0, GROUND_Y + 11.0 - 0.6, -86))
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in 4:
		var c := _shader("clouds.gdshader")
		c.set_shader_parameter("seed", float(i) * 1.7 + 0.3)
		c.set_shader_parameter("cover", 0.5 + 0.05 * i)
		c.set_shader_parameter("sun_uv", Vector2(0.8 - 0.25 * (i % 2), 0.9))
		c.set_shader_parameter("opacity", 0.9 - 0.12 * i)
		var sz := Vector2(rng.randf_range(90, 140), rng.randf_range(12, 20))
		_quad(sz, c, Vector3(rng.randf_range(-40, 40), 16.0 + i * 6.0 + rng.randf_range(-2, 2), -120.0 - i * 10.0))
		_clouds.append(c)
	_halo_mat = _shader("halo.gdshader")
	_halo_mat.set_shader_parameter("color", Color(1.0, 0.66, 0.36))
	_halo_mat.set_shader_parameter("strength", 0.3)
	_halo = _quad(Vector2(46, 46), _halo_mat, Vector3.ZERO)
	# the farm: the barn, silo and windmill, trees, bales and fences, spread over the yard behind the playfield
	for spec in [["bg_hill", Vector3(-6, 0, -12), 1.6], ["bg_hill", Vector3(8, 0, -14), 1.8], ["bg_barn", Vector3(-11, 0, -7), 1.0],
			["bg_silo", Vector3(-8.2, 0, -8), 1.0], ["bg_windmill", Vector3(11, 0, -9), 1.1], ["bg_tree", Vector3(6.5, 0, -5), 1.2],
			["bg_tree", Vector3(-3, 0, -9), 1.4], ["bg_haybale", Vector3(9.5, 0, -3), 1.0], ["bg_haybale", Vector3(-9.8, 0, -2.6), 1.0],
			["bg_fence", Vector3(-6, 0, -2.2), 1.0], ["bg_fence", Vector3(-4, 0, -2.2), 1.0], ["bg_fence", Vector3(5, 0, -2.2), 1.0],
			["bg_tree", Vector3(-14, 0, -12), 1.5], ["bg_tree", Vector3(15, 0, -13), 1.6], ["bg_tree", Vector3(1.5, 0, -15), 1.3],
			["bg_haybale", Vector3(3.2, 0, -6), 0.9], ["bg_haybale", Vector3(-1.5, 0, -4.2), 0.9], ["bg_tree", Vector3(-19, 0, -6), 1.3],
			["bg_tree", Vector3(19.5, 0, -6), 1.4]]:
		var n := _scene(spec[0], Vector3(2, 3, 2), Color(0.7, 0.3, 0.2))
		var sp: Vector3 = spec[1]
		n.position = Vector3(sp.x * 1.6, GROUND_Y, sp.z * 1.8 - 4.0)
		n.scale = Vector3.ONE * spec[2]
		n.rotation.y = rng.randf_range(-0.3, 0.3) if spec[0] in ["bg_tree", "bg_haybale"] else 0.0
		add_child(n)
		_play(n.find_child("AnimationPlayer", true, false), "turn", true)


# ------------------------------------------------------------------ a level

func _on_level(e: HenEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_fx.clear()
	_hens.clear()
	_eggs.clear()
	_grain.clear()
	_lifts.clear()
	_goose = null
	_cage = null
	_top_extra = 0.0
	_streak = 0
	_punch = 0.0
	_trauma = 0.0
	_goose_look = 0.0
	_intro = 1.0
	_intro_len = 1.6
	_was = -1
	var lv := e.level
	for y in E.H:
		for x in E.W:
			var c := Vector2(x + 0.5, y + 0.5)
			if lv.solid[y * E.W + x] == 1:
				var top := y == 0 or lv.solid[(y - 1) * E.W + x] == 0
				var n := _scene("brick", Vector3(0.5, 0.5, 0.5), Color(0.75, 0.35, 0.25))
				# a few shades of brick, so a platform is not one flat red
				var v := 0.9 + 0.2 * float((x * 7 + y * 13) % 5) / 4.0
				_tint(n, "brick_face", Color(0.68 * v, 0.29 * v, 0.19 * v))
				var grass := n.find_child("brick_top", true, false)
				if grass and not top:
					(grass as Node3D).visible = false  # grass only where the sky is above
				n.position = world(c)
				_stage.add_child(n)
			elif lv.ladder[y * E.W + x] == 1:
				var n := _scene("ladder", Vector3(0.45, 0.5, 0.05), Color(0.6, 0.4, 0.2))
				n.position = world(Vector2(x + 0.5, y + 1.0), 0.3)
				_stage.add_child(n)
	var k := 0
	for c in e.eggs:
		var n := _scene("egg", Vector3(0.2, 0.25, 0.2), Color(0.9, 0.75, 0.55))
		n.position = world(Vector2(c) + Vector2(0.5, 1.0), 0.5)
		n.scale = Vector3.ONE * 1.3
		_no_shadow(n)
		_stage.add_child(n)
		_sparkle(n, Vector3(0.05, 0.22, 0.14), 0.7, float(k) * 0.37, _sparkle_mat)
		_eggs[c] = n
		k += 1
	for c in e.grain:
		var n := _scene("grain", Vector3(0.25, 0.25, 0.25), Color(0.9, 0.8, 0.4))
		n.position = world(Vector2(c) + Vector2(0.5, 1.0), 0.5)
		n.scale = Vector3.ONE * 1.2
		_no_shadow(n)
		_stage.add_child(n)
		_sparkle(n, Vector3(-0.06, 0.2, 0.16), 0.5, float(k) * 0.53, _glint_mat)
		_grain[c] = n
		k += 1
	for i in e.lifts.size():
		var n := _scene("lift", Vector3(1.0, 0.1, 0.5), Color(0.6, 0.45, 0.3))
		_stage.add_child(n)
		_lifts.append(n)
	if lv.cage.x >= 0:
		_cage = _scene("cage", Vector3(1.0, 1.2, 0.6), Color(0.6, 0.5, 0.35))
		# the cage stands on the platform below its cell (if there is one close), not in mid-air
		var floor_row := lv.cage.y + 2
		for r in range(lv.cage.y + 2, mini(lv.cage.y + 6, E.H)):
			if lv.solid[r * E.W + lv.cage.x] == 1:
				floor_row = r
				break
		_cage.position = world(Vector2(lv.cage.x + 1.0, floor_row), -0.1)
		_cage.scale = Vector3.ONE * 0.85
		_stage.add_child(_cage)
		_goose_at = Vector2(_cage.position.x, _cage.position.y + 0.9)
		if lv.goose:
			_goose = _scene("goose", Vector3(0.6, 0.9, 0.5), Color(0.95, 0.95, 0.95))
			_goose.scale = Vector3.ONE * GOOSE_SCALE
			_stage.add_child(_goose)
			_goose_anim = _goose.find_child("AnimationPlayer", true, false)
			_play(_goose_anim, "idle", true)
			_goose.position = _cage.position + Vector3(-0.15, 0.12, 0.0)
			_goose_pos = _goose.position
		_top_extra = maxf(0.0, _cage.position.y + 2.5 * 0.85 - E.H * T * 0.5)
	for hn in e.hens:
		var n := _scene("hen", Vector3(0.4, 0.4, 0.3), Color(0.95, 0.95, 0.9))
		var fc: Array = FEATHERS[(hn["id"] + e.stage) % FEATHERS.size()]
		_tint(n, "hen_feather", fc[0])
		_tint(n, "hen_speckle", fc[1])
		n.scale = Vector3.ONE * HEN_SCALE
		_stage.add_child(n)
		_hens.append({"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": "", "col": fc[0], "face": 1.0,
			"bob": 0.0})
	_hero = _scene("farmhand", Vector3(0.4, 1.0, 0.3), Color(0.3, 0.5, 0.8))
	_hero.scale = Vector3.ONE * HERO_SCALE
	_stage.add_child(_hero)
	_hero_anim = _hero.find_child("AnimationPlayer", true, false)
	_hero_last = ""
	_place_camera(0.0)


func _hero_world() -> Vector3:
	return world(game.engine.hero["pos"], 0.5)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"egg":
			var c: Vector2i = d["cell"]
			if _eggs.has(c):
				var p: Vector3 = _eggs[c].position + Vector3(0, 0.18, 0.2)
				_fx.egg_pop(p)
				_eggs[c].queue_free()
				_eggs.erase(c)
				# a run of eggs in quick succession: the camera leans in closer each time
				_streak = _streak + 1 if _streak_t > 0.0 else 1
				_streak_t = 2.6
				if _streak >= 2:
					_punch = minf(1.0, _punch + 0.25 + 0.12 * _streak)
					_focus = Vector2(p.x, p.y)
				if d["left"] == 0:
					_punch = 0.0
		"grain":
			var c: Vector2i = d["cell"]
			if _grain.has(c):
				var p: Vector3 = _grain[c].position + Vector3(0, 0.15, 0.2)
				_fx.grain(p)
				_fx.flash(p - Vector3(0, 1.8, 0), Color(1.0, 0.8, 0.4), 2.5)
				_grain[c].queue_free()
				_grain.erase(c)
				_punch = minf(1.0, _punch + 0.6)
				_focus = Vector2(p.x, p.y)
		"peck", "cluck":
			var i: int = d["id"]
			if i < _hens.size():
				var v: Dictionary = _hens[i]
				var n: Node3D = v["node"]
				_fx.feathers(n.position + Vector3(0, 0.3, 0.1), v["col"], 5 if kind == "peck" else 2, 1.2 if kind == "peck" else 0.8)
				if kind == "peck":
					_fx.burst(n.position + Vector3(0.15 * v["face"], 0.05, 0.1), Color(0.98, 0.82, 0.38), 6, 1.2, 0.5, 0.04, 0.0, -8.0)
		"jump":
			_squash = -0.5
			_fx.dust(_hero_world() + Vector3(0, 0.02, 0.1))
		"land":
			_squash = 1.0
			_fx.dust(_hero_world() + Vector3(0, 0.02, 0.1), true)
		"goose_free":
			if _cage:
				_play(_cage.find_child("AnimationPlayer", true, false), "open", false, 0.0)
				var cp := _cage.position + Vector3(0, 0.6, 0.4)
				_fx.feathers(cp, Color(1, 1, 1), 16, 3.2, Vector3(0, 1, 0.6))
				_fx.dust(cp - Vector3(0, 0.5, 0), true)
				_fx.burst(cp, Color(1.0, 0.9, 0.7, 0.8), 14, 3.5, 0.6, 0.35, 0.0, -0.5, 0.3, "smoke")
				_fx.flash(cp - Vector3(0, 1.5, 0), Color(1.0, 0.6, 0.3), 4.0)
			_play(_goose_anim, "fly", true)
			_goose_look = 1.0
			_trauma = maxf(_trauma, 0.45)
		"die":
			_play(_hero_anim, "die")
			_hero_last = "die"
			var p := world(d["pos"] + Vector2(0, -0.9), 0.4)
			_fx.burst(p, Color(1.0, 0.9, 0.7), 18, 2.0, 0.6, 0.07, 1.0, -3.0, 1.0, "glow")
			_fx.dust(world(d["pos"], 0.5), true)
			if d["how"] in ["hen", "goose"]:
				_fx.feathers(p, Color(1, 0.97, 0.9), 12, 2.6)
			_fx.flash(p - Vector3(0, 1.8, 0), Color(1.0, 0.4, 0.25), 3.0)
			_trauma = 1.0
			_punch = 0.0
			_focus = Vector2(p.x, p.y)
			_streak = 0
		"extra_life":
			var p := _hero_world() + Vector3(0, 0.6, 0.3)
			_fx.burst(p, Color(0.6, 1.0, 0.5), 24, 2.6, 0.8, 0.08, 1.0, -1.5, 1.0, "glow")
			_fx.flash(p - Vector3(0, 1.8, 0), Color(0.6, 1.0, 0.5), 2.5)
		"cleared":
			_play(_hero_anim, "cheer", true)
			_hero_last = "cheer"
			_fx.confetti(_hero_world() + Vector3(0, 0.6, 0.4))
			_fx.egg_pop(_hero_world() + Vector3(0, 0.8, 0.3))
			_punch = 0.0


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	if e.phase != _was:
		if e.phase == E.Phase.READY and _was == E.Phase.DYING:
			_intro = 1.0  # back from a death: open close on the farmhand again, quicker
			_intro_len = 1.0
		_was = e.phase
	_streak_t = maxf(0.0, _streak_t - delta)
	# some grain is eaten by hens: drop it from the view too
	for c in _grain.keys():
		if not e.grain.has(c):
			_grain[c].queue_free()
			_grain.erase(c)
	_update_hero(e, delta)
	_update_hens(e, delta)
	for i in _lifts.size():
		_lifts[i].position = world(Vector2(e.level.lift_col + 1.0, e.lifts[i]), 0.2)
		var rope := _lifts[i].find_child("rope", true, false) as Node3D
		if rope:
			# the rope reaches up to the top of the shaft
			var top_y := (13.0 - E.LIFT_TOP) * T
			rope.scale.y = maxf(0.01, top_y - (_lifts[i].position.y + 1.72))
	for c in _eggs:
		var n: Node3D = _eggs[c]
		n.rotation.y = sin(_time * 2.0 + c.x) * 0.3
	for c in _grain:
		var n: Node3D = _grain[c]
		n.scale = Vector3.ONE * 1.2 * (1.0 + 0.04 * sin(_time * 3.0 + c.x * 1.3))
	_update_goose(e, delta)
	_update_light(e, delta)
	_place_camera(delta)


func _update_hero(e: HenEngine, delta: float) -> void:
	var h := e.hero
	_hero.position = world(h["pos"], 0.5)
	# squash on landing, stretch on take-off, easing back
	_squash = move_toward(_squash, 0.0, delta * 5.0)
	var sq := _squash * 0.12
	_hero.scale = Vector3(HERO_SCALE * h["facing"] * (1.0 + sq * 0.6), HERO_SCALE * (1.0 - sq), HERO_SCALE * (1.0 + sq * 0.6))
	if e.phase == E.Phase.PLAY:
		var st: String = h["state"]
		var want := "idle"
		match st:
			"walk": want = "walk" if absf(e.move_x) > 0.1 else "idle"
			"climb": want = "climb"
			"jump": want = "jump"
			"fall": want = "fall"
		if want != _hero_last:
			var blend := 0.08 if want in ["jump", "fall"] or _hero_last in ["jump", "fall"] else 0.18
			_hero_last = want
			_play(_hero_anim, want, want != "jump", blend)
		if _hero_anim:
			# the cycles at the engine's speeds (the model's stride: walk 1.75 units/s, climb 0.94 units/s)
			if st == "climb":
				_hero_anim.speed_scale = (E.CLIMB * T / 0.94) if (e.up or e.down) else 0.0
			else:
				_hero_anim.speed_scale = E.WALK * T / 1.75 if want == "walk" else 1.0
	elif e.phase == E.Phase.READY and _hero_last in ["die", "cheer", ""]:
		_hero_last = "idle"
		_play(_hero_anim, "idle", true, 0.0)
		if _hero_anim:
			_hero_anim.speed_scale = 1.0


func _update_hens(e: HenEngine, delta: float) -> void:
	for i in e.hens.size():
		var hn: Dictionary = e.hens[i]
		var v: Dictionary = _hens[i]
		var n: Node3D = v["node"]
		n.position = world(hn["pos"], 0.5)
		if hn["dir"].x != 0:
			v["face"] = float(hn["dir"].x)
		n.scale = Vector3(HEN_SCALE * v["face"], HEN_SCALE, HEN_SCALE)
		var want := "peck" if hn["peck"] > 0.0 else ("climb" if hn["climb"] else "walk")
		if v["last"] != want:
			v["last"] = want
			_play(v["anim"], want, true, 0.2)
			if v["anim"]:
				(v["anim"] as AnimationPlayer).speed_scale = hn["speed"] * T / 0.73 if want == "walk" else 1.0
		# a loose feather now and then from a hen on the move
		v["bob"] -= delta
		if v["bob"] <= 0.0:
			v["bob"] = 2.5 + fmod(float(i) * 1.37 + _time * 0.61, 2.0)
			if want != "peck":
				_fx.feathers(n.position + Vector3(0, 0.3, 0.05), v["col"], 1, 0.5)


func _update_goose(e: HenEngine, delta: float) -> void:
	if _goose == null or e.goose.is_empty():
		return
	var gp: Vector2 = e.goose["pos"]
	var gv: Vector2 = e.goose["vel"]
	# eased, so it lifts out of the cage instead of popping to its first position
	_goose_pos = _goose_pos.lerp(world(gp + Vector2(0, 0.8), 0.6), minf(1.0, delta * 10.0))
	_goose.position = _goose_pos + Vector3(0, sin(_time * 9.0) * 0.06, 0)
	var face := signf(gv.x) if absf(gv.x) > 0.05 else signf(_goose.scale.x)
	# a bank into its turns and a lift with each wing beat
	_goose.scale = Vector3(GOOSE_SCALE * face, GOOSE_SCALE, GOOSE_SCALE)
	_goose.rotation.z = clampf(-gv.y * 0.12, -0.35, 0.35) * face
	_gust_t -= delta
	if _gust_t <= 0.0:
		_gust_t = 0.45
		_fx.gust(_goose.position + Vector3(-0.3 * face, 0.1, 0.0), -face)
		if fmod(_time, 2.2) < 0.45:
			_fx.feathers(_goose.position + Vector3(0, 0.2, 0.1), Color(1, 1, 1), 1, 0.6)


## the light follows the bonus clock: the sun sinks and reddens as it runs down; grain holds it
func _update_light(e: HenEngine, delta: float) -> void:
	var want := clampf(1.0 - e.clock / maxf(1.0, e.level.time_limit), 0.0, 1.0)
	if e.phase == E.Phase.READY and e.time < 0.1:
		_dusk = want
	_dusk = lerpf(_dusk, want, minf(1.0, delta * 2.0))
	var d := _dusk * _dusk
	_sky_mat.set_shader_parameter("dusk", d)
	_sun.light_color = Color(1.0, 0.8, 0.56).lerp(Color(1.0, 0.56, 0.34), d)
	_sun.light_energy = lerpf(1.8, 1.4, d)
	_rim.light_color = Color(1.0, 0.72, 0.4).lerp(Color(1.0, 0.48, 0.26), d)
	_env.fog_light_color = Color(0.96, 0.66, 0.46).lerp(Color(0.95, 0.52, 0.42), d)
	_env.ambient_light_energy = lerpf(0.42, 0.34, d)
	# grain holds the clock: the world takes a golden glow while it lasts; a death drains the colour for a moment
	var glow := 0.55 + (0.25 if e.freeze > 0.0 else 0.0)
	_env.glow_intensity = lerpf(_env.glow_intensity, glow, minf(1.0, delta * 3.0))
	var sat := 0.7 if e.phase == E.Phase.DYING else 1.15
	_sat = lerpf(_sat, sat, minf(1.0, delta * 4.0))
	_env.adjustment_saturation = _sat
	for c in _clouds:
		c.set_shader_parameter("time_s", _time)
	_halo_mat.set_shader_parameter("time_s", _time)
	_halo_mat.set_shader_parameter("strength", 0.3 + 0.15 * d)


# ------------------------------------------------------------------ the camera

func _place_camera(delta: float) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(E.H * T * 0.5 + 0.55 + _top_extra * 0.5, (E.W * T * 0.5 + 0.35) / aspect)
	_dist = need / tan(deg_to_rad(camera.fov * 0.5))
	var hw := _hero_world() if _hero else Vector3.ZERO
	var hero := Vector2(hw.x, hw.y + 0.4)
	# lean a little towards the farmhand: the level always stays in view
	var want := Vector2(clampf(hero.x * 0.05, -0.4, 0.4), clampf(hero.y * 0.05, -0.3, 0.3))
	_lean = _lean.lerp(want, minf(1.0, delta * 1.5))
	_trauma = maxf(0.0, _trauma - delta * 1.1)
	_punch = maxf(0.0, _punch - delta * 0.9)
	_goose_look = maxf(0.0, _goose_look - delta / 1.8)
	var target := Vector3(_lean.x, _lean.y + _top_extra * 0.5, 0.0)
	var zoom := 1.0
	var yaw := hero.x * 0.006 + sin(_time * 0.13) * 0.012
	var pitch := 0.035
	# a punch-in (a streak of eggs, a sack of grain): closer, towards what happened, for a moment
	var pk := _punch * _punch * (3.0 - 2.0 * _punch)
	zoom -= 0.2 * pk
	target = target.lerp(Vector3(_focus.x, _focus.y, 0.0), 0.4 * pk)
	if e == null:
		pass
	elif e.phase == E.Phase.READY:
		# open close on the farmhand, then pull out to the whole level
		_intro = maxf(0.0, _intro - delta / _intro_len)
		var k := _intro * _intro * (3.0 - 2.0 * _intro)
		var s := 0.6 if _intro_len > 1.2 else 0.4
		zoom -= s * k
		target = target.lerp(Vector3(hero.x, hero.y, 0.0), k * 0.9)
		yaw += 0.1 * k
		pitch += 0.03 * k
	elif e.phase == E.Phase.DYING:
		# a hold on the fall: in towards it, then back out
		var s := clampf(e.phase_t / 2.0, 0.0, 1.0)
		var k := sin(s * PI)
		zoom -= 0.22 * k
		target = target.lerp(Vector3(_focus.x, _focus.y, 0.0), 0.5 * k)
	elif e.phase == E.Phase.CLEARED:
		# pull back and swing round a little on a cleared level
		var s := clampf(1.0 - e.phase_t / 3.0, 0.0, 1.0)
		var k := s * s * (3.0 - 2.0 * s)
		zoom += 0.1 * k
		yaw -= 0.12 * k
		pitch += 0.05 * k
	if _goose_look > 0.0:
		# the goose bursts out: a look at the cage
		var g := sin(minf(1.0, (1.0 - _goose_look) * 1.6) * PI * 0.5) * _goose_look
		g = clampf(g * 1.6, 0.0, 1.0)
		zoom -= 0.25 * g
		target = target.lerp(Vector3(_goose_at.x, _goose_at.y, 0.0), 0.7 * g)
	var dd := _dist * zoom
	var off := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * dd
	var shake := _trauma * _trauma
	var jitter := Vector3(sin(_time * 37.0) + sin(_time * 23.0 + 1.3), sin(_time * 31.0 + 2.1) + sin(_time * 19.0), 0.0)
	camera.position = target + off + jitter * shake * 0.14 + Vector3(0, 0.1, 0)
	camera.look_at(target + jitter * shake * 0.05, Vector3.UP)
	camera.rotate_object_local(Vector3.FORWARD, jitter.x * shake * 0.015)
	# the sun's halo sits on the line from the camera to the sun, just behind the far hills
	var sd := (SUN_DIR + Vector3(0, -_dusk * _dusk * 0.08, 0)).normalized()
	_halo.position = camera.position + sd * 100.0
	_attrs.dof_blur_far_distance = dd + 6.0
