class_name FizzView3D
extends Node3D
## Fizzlings in 3D: an underwater toybox seen straight on. Platforms are glossy tiles in the level's colour with light
## rippling over them, giant toys and kelp fade into the haze behind, god rays slant down from the surface. Empty
## bubbles are clear glass; a bubble with a toy inside glows gold with the toy lit up inside, struggling, and turns
## red and pulses when it is about to break free. The camera leans towards the heroes, punches in on chains, shakes
## on deaths and swoops on a cleared level. Tile (x, y) is world ((x - 16) / 2, (13 - y) / 2).

const E = preload("res://games/fizzlings/engine/fizz_engine.gd")
const M := "res://games/fizzlings/art/models/"
const SH := "res://games/fizzlings/view3d/"
const T := 0.5
const SKINS := [Color(1.0, 0.62, 0.72), Color(0.6, 0.7, 1.0)]
const TOY_MODELS := {"beetle": "toy_beetle", "spring": "toy_spring", "flyer": "toy_flyer"}
const FULL := Color(1.0, 0.72, 0.12)     ## a bubble with a toy inside
const WARN := Color(1.0, 0.1, 0.06)      ## ... about to break free
const WARN_T := 2.5                      ## seconds of warning before a toy breaks out
const TRAP_SCALE := 1.18
const TOY_IN_BUBBLE := 1.25

@export var game: FizzGame

var camera: Camera3D
var _env: Environment
var _attrs: CameraAttributesPractical
var _stage: Node3D
var _heroes: Array[Dictionary] = []
var _bubbles := {}    ## id -> {node, has, shell, halo, light, toy, born}
var _toys := {}       ## id -> {node, angry}
var _treats := {}     ## view key -> {node, ground, bounce, born}
var _treat_key := 0
var _ghost: Node3D
var _fx: FizzFx
var _time := 0.0
var _mats := {}
var _backdrop_mat: ShaderMaterial
var _skyline_mats: Array[ShaderMaterial] = []
var _timed: Array[ShaderMaterial] = []   ## materials that take "time_s"
var _tile_overlay: ShaderMaterial
var _hero_overlays: Array[ShaderMaterial] = []
var _toy_overlay: ShaderMaterial
var _angry_overlay: ShaderMaterial
var _sparkle_mat: ShaderMaterial
var _ghost_mat: ShaderMaterial
# camera state
var _dist := 25.0
var _lean := Vector2.ZERO
var _trauma := 0.0
var _punch := 0.0
var _intro := 1.0
var _chain_n := 0
var _chain_pos := Vector3.ZERO


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3((p.x - 16.0) * T, (13.0 - p.y) * T, z)


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.02, 0.08, 0.16)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.55, 0.8, 1.0)
	_env.ambient_light_energy = 0.42
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 0.95
	_env.glow_enabled = true
	_env.glow_intensity = 0.7
	_env.glow_strength = 1.05
	_env.glow_bloom = 0.0
	_env.glow_hdr_threshold = 1.2
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.15
	_env.adjustment_contrast = 1.05
	# the water hazes what lies behind the playfield, not the playfield itself
	_env.fog_enabled = true
	_env.fog_mode = Environment.FOG_MODE_DEPTH
	_env.fog_light_color = Color(0.04, 0.2, 0.36)
	_env.fog_density = 0.85
	_env.fog_depth_curve = 1.4
	_env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-58, 18, 0)
	sun.light_energy = 1.25
	sun.light_color = Color(0.92, 1.0, 1.0)
	sun.shadow_enabled = true
	add_child(sun)
	var fill := DirectionalLight3D.new()  # a cool light from below and behind: rims on the heroes and toys
	fill.rotation_degrees = Vector3(20, 160, 0)
	fill.light_energy = 0.45
	fill.light_color = Color(0.4, 0.8, 1.0)
	fill.light_specular = 0.6
	add_child(fill)
	camera = Camera3D.new()
	camera.fov = 32
	camera.current = true
	_attrs = CameraAttributesPractical.new()
	_attrs.dof_blur_far_enabled = true
	_attrs.dof_blur_far_transition = 6.0
	_attrs.dof_blur_amount = 0.05
	camera.attributes = _attrs
	add_child(camera)
	_fx = FizzFx.new()
	add_child(_fx)
	_make_materials()
	_build_backdrop()
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _shader(file: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + file)
	return m


func _make_materials() -> void:
	_tile_overlay = _shader("caustics.gdshader")
	_tile_overlay.set_shader_parameter("caustic_strength", 1.6)
	for s in SKINS:
		var h := _shader("caustics.gdshader")
		h.set_shader_parameter("caustic_strength", 0.25)
		h.set_shader_parameter("rim_strength", 1.1)
		h.set_shader_parameter("rim_color", (s as Color).lerp(Color(0.8, 1.0, 1.0), 0.45))
		_hero_overlays.append(h)
	_toy_overlay = _shader("caustics.gdshader")
	_toy_overlay.set_shader_parameter("caustic_strength", 0.25)
	_toy_overlay.set_shader_parameter("rim_strength", 0.6)
	_angry_overlay = _shader("caustics.gdshader")
	_angry_overlay.set_shader_parameter("caustic_strength", 0.15)
	_angry_overlay.set_shader_parameter("rim_strength", 1.6)
	_angry_overlay.set_shader_parameter("rim_color", Color(1.0, 0.2, 0.1))
	_sparkle_mat = _shader("sparkle.gdshader")
	_ghost_mat = _shader("ghost.gdshader")
	_timed.append_array([_ghost_mat, _tile_overlay, _toy_overlay, _angry_overlay, _sparkle_mat])
	_timed.append_array(_hero_overlays)


func _overlay(n: Node, mat: Material) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_overlay = mat


func _scene(name: String, size := Vector3(0.45, 0.45, 0.45), col := Color(0.8, 0.8, 0.9)) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := SphereMesh.new()
	b.radius = size.x
	b.height = size.x * 2.0
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	b.material = m
	mi.mesh = b
	mi.position.y = size.x
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color, emission := false) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = Color(col, t.albedo_color.a)
				if emission or t.emission_enabled:
					t.emission_enabled = true
					t.emission = col
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.08)


func _quad(size: Vector2, mat: Material, pos: Vector3) -> MeshInstance3D:
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = size
	q.mesh = qm
	q.material_override = mat
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	q.position = pos
	add_child(q)
	return q


func _sparkle(parent: Node3D, pos: Vector3, size: float, phase: float, col := Color(1.0, 0.95, 0.7)) -> MeshInstance3D:
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(size, size)
	q.mesh = qm
	q.material_override = _sparkle_mat
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	q.position = pos
	parent.add_child(q)
	q.set_instance_shader_parameter("phase", phase)
	q.set_instance_shader_parameter("rate", 0.8 + fmod(phase * 0.37, 0.6))
	return q


# ------------------------------------------------------------------ the backdrop

func _build_backdrop() -> void:
	# far water with a skyline of giant toys, then a nearer row of toy silhouettes, then kelp, coral and toys on sand
	_backdrop_mat = _shader("deep_water.gdshader")
	_backdrop_mat.set_shader_parameter("size", Vector2(84, 48))
	_quad(Vector2(84, 48), _backdrop_mat, Vector3(0, 0, -14.0))
	_timed.append(_backdrop_mat)
	for layer in 2:
		var sk := _shader("skyline.gdshader")
		var sz := Vector2(52, 12) if layer == 0 else Vector2(44, 7)
		sk.set_shader_parameter("size", sz)
		sk.set_shader_parameter("seed", float(layer) * 3.0 + 1.0)
		_quad(sz, sk, Vector3(0, -6.8 + sz.y * 0.5 - 0.3, -10.0 if layer == 0 else -7.0))
		_skyline_mats.append(sk)
	var rays := _shader("rays.gdshader")
	_quad(Vector2(46, 30), rays, Vector3(0, 1.5, -4.0))
	var rays_front := _shader("rays.gdshader")
	rays_front.set_shader_parameter("strength", 0.07)
	rays_front.set_shader_parameter("seed", 5.0)
	_quad(Vector2(34, 22), rays_front, Vector3(0, 1.0, 1.2))
	_timed.append_array([rays, rays_front])
	# the sand floor, caustics dancing over it
	var sand_floor := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(100, 44)
	sand_floor.mesh = pm
	var sand := StandardMaterial3D.new()
	sand.albedo_color = Color(0.62, 0.55, 0.42)
	sand.roughness = 0.9
	sand_floor.material_override = sand
	sand_floor.material_overlay = _tile_overlay
	sand_floor.position = Vector3(0, -6.85, 0.0)
	add_child(sand_floor)
	var rng := RandomNumberGenerator.new()
	rng.seed = 18
	var props := ["bg_kelp", "bg_kelp", "bg_coral", "bg_shell", "bg_toy_block", "bg_kelp", "bg_coral"]
	for i in 30:
		var kind: String = props[rng.randi_range(0, props.size() - 1)]
		var n := _scene(kind, Vector3(0.4, 1.0, 0.4), Color(0.3, 0.7, 0.5))
		var side := -1.0 if i % 2 == 0 else 1.0
		var x := rng.randf_range(-11.0, 11.0) if i < 18 else side * rng.randf_range(8.6, 14.0)
		n.position = Vector3(x, -6.8, rng.randf_range(-5.5, -1.8))
		n.rotation.y = rng.randf_range(-0.6, 0.6)
		n.scale = Vector3.ONE * rng.randf_range(0.8, 1.6) * (1.3 if i >= 18 else 1.0)
		add_child(n)
		_overlay(n, _tile_overlay)
		_play(n.find_child("AnimationPlayer", true, false), "sway", true)
	# giant toy blocks stacked beside the playfield
	for s in [[-11.8, 3.0, -4.5, 0.4], [-10.6, 2.2, -3.2, -0.3], [11.5, 3.4, -4.8, -0.5], [10.4, 2.0, -3.0, 0.2],
			[-12.2, 2.4, -4.5, 0.1]]:
		var b := _scene("bg_toy_block", Vector3(0.4, 0.4, 0.4), Color(0.4, 0.7, 0.9))
		b.position = Vector3(s[0], -6.8, s[2])
		b.scale = Vector3.ONE * s[1]
		b.rotation.y = s[3]
		add_child(b)
		_overlay(b, _tile_overlay)
	var top := _scene("bg_toy_block", Vector3(0.4, 0.4, 0.4), Color(0.4, 0.7, 0.9))
	top.position = Vector3(-11.6, -6.8 + 3.0 * 0.95, -4.5)
	top.scale = Vector3.ONE * 2.0
	top.rotation = Vector3(0, 1.1, 0.12)
	add_child(top)
	_overlay(top, _tile_overlay)
	for x in [-9.5, 9.5, -5.0, 5.5, -13.0, 12.8]:
		var col := _scene("bg_bubble_column", Vector3(0.2, 1, 0.2), Color(0.8, 0.9, 1.0))
		col.position = Vector3(x, -6.8, -2.5 if absf(x) < 12.0 else -4.0)
		add_child(col)
		_play(col.find_child("AnimationPlayer", true, false), "rise", true)
	# motes drifting in the water
	var snow := CPUParticles3D.new()
	snow.amount = 140
	snow.lifetime = 14.0
	snow.preprocess = 14.0
	snow.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	snow.emission_box_extents = Vector3(17, 10, 1.2)
	snow.position = Vector3(0, -1, -0.4)
	snow.direction = Vector3(0.2, 1, 0)
	snow.spread = 40.0
	snow.gravity = Vector3(0, 0.02, 0)
	snow.initial_velocity_min = 0.05
	snow.initial_velocity_max = 0.2
	snow.scale_amount_min = 0.025
	snow.scale_amount_max = 0.06
	var qm := QuadMesh.new()
	qm.size = Vector2(0.5, 0.5)
	snow.mesh = qm
	snow.material_override = Fx.material("glow", Color(0.6, 0.9, 1.0, 0.35))
	var fade := Gradient.new()
	fade.offsets = PackedFloat32Array([0.0, 0.2, 0.8, 1.0])
	fade.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 1), Color(1, 1, 1, 0)])
	snow.color_ramp = fade
	add_child(snow)


# ------------------------------------------------------------------ a level

func _on_level(e: FizzEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_heroes.clear()
	_bubbles.clear()
	_toys.clear()
	_treats.clear()
	_ghost = null
	_intro = 1.0
	var colour: Color = e.level.colour
	var face := Color.from_hsv(colour.h, minf(1.0, colour.s * 1.5 + 0.1), colour.v * 0.85)  # toy-bright tiles
	_backdrop_mat.set_shader_parameter("tint", colour)
	for sk in _skyline_mats:
		sk.set_shader_parameter("tint", colour)
	for y in E.H:
		for x in E.W:
			if not e.is_solid(x, y):
				continue
			var top := y > 0 and not e.is_solid(x, y - 1)
			var n := _scene("tile_top" if top else "tile_block", Vector3(0.25, 0.25, 0.25), colour)
			_tint(n, "tile_face", face.darkened(0.2 if x <= 1 or x >= E.W - 2 else 0.0))
			n.position = world(Vector2(x + 0.5, y + 0.5))  # tiles have their origin at the centre
			_overlay(n, _tile_overlay)
			_stage.add_child(n)
	for h in e.heroes:
		var n := _scene("axolotl", Vector3(0.3, 0.8, 0.3), SKINS[h["p"]])
		_tint(n, "fizz_skin", SKINS[h["p"]])
		_overlay(n, _hero_overlays[h["p"]])
		var glow := OmniLight3D.new()  # each hero carries a little light of their colour
		glow.light_color = SKINS[h["p"]]
		glow.light_energy = 0.9
		glow.omni_range = 1.6
		glow.light_specular = 0.2
		glow.position = Vector3(0.1, 0.45, 0.6)
		n.add_child(glow)
		_stage.add_child(n)
		_heroes.append({"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": "", "sq": 0.0,
			"sq_v": 0.0, "ground": true})


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"blow":
			if d["p"] < _heroes.size():
				_play(_heroes[d["p"]]["anim"], "blow")
				_heroes[d["p"]]["last"] = "blow"
				_heroes[d["p"]]["sq"] = 0.18
		"jump":
			if d["p"] < _heroes.size():
				_heroes[d["p"]]["sq"] = -0.3  # stretch up
		"bounce":
			if d["p"] < _heroes.size():
				_heroes[d["p"]]["sq"] = -0.35
				_fx.ring(world(d.get("pos", game.engine.heroes[d["p"]]["pos"]), 0.2), Color(0.7, 0.95, 1.0), 1.4, 0.35)
		"pop":
			var p := world(d["pos"], 0.3)
			if d["trapped"]:
				_fx.ring(p, Color(FULL, 1.0), 3.2, 0.55)
				_fx.droplets(p, Color(1.0, 0.9, 0.55), 26, 4.0)
				_fx.sparkles(p, Color(1.0, 0.8, 0.3), 18, 3.0)
				_fx.flash(p, FULL, 3.0)
				_chain_n += 1
				_chain_pos = p
			else:
				_fx.ring(p, Color(0.75, 0.95, 1.0, 0.8), 1.7, 0.35)
				_fx.droplets(p, Color(0.75, 0.95, 1.0), 12, 2.6)
		"trap":
			_fx.ring(world(d["pos"], 0.3), Color(FULL, 1.0), 2.2, 0.4)
			_fx.sparkles(world(d["pos"], 0.3), Color(1.0, 0.85, 0.4), 10, 1.8)
		"treat":
			var p := world(d["pos"] + Vector2(0, -0.5), 0.3)
			_fx.sparkles(p, Color(1.0, 0.9, 0.4), 18 if d["points"] < 1000 else 34, 2.4)
			_fx.ring(p, Color(1.0, 0.9, 0.5), 1.6 if d["points"] < 1000 else 2.6, 0.4)
			_fx.flash(p, Color(1.0, 0.85, 0.5), 1.5)
		"die":
			var p := world(d["pos"] + Vector2(0, -0.8), 0.3)
			_fx.burst(p, SKINS[d["p"]], 30, 3.0, 0.8, 0.09, 1.0, -2.0, 1.0, "glow")
			_fx.ring(p, SKINS[d["p"]], 3.0, 0.6)
			_fx.flash(p, SKINS[d["p"]], 3.0)
			_trauma = maxf(_trauma, 0.75)
		"escape":
			var p := world(d["pos"], 0.3)
			_fx.burst(p, Color(1.0, 0.35, 0.25), 20, 2.6, 0.5, 0.07, 1.0, 0.0, 1.0, "glow")
			_fx.ring(p, Color(1.0, 0.25, 0.15), 2.4, 0.45)
			_trauma = maxf(_trauma, 0.3)
		"ghost":
			_trauma = maxf(_trauma, 0.45)
		"cleared":
			for h in _heroes:
				_fx.sparkles((h["node"] as Node3D).position + Vector3(0, 0.5, 0.3), Color(1.0, 0.9, 0.5), 20, 2.5)


func _process(delta: float) -> void:
	_time += delta
	for m in _timed:
		m.set_shader_parameter("time_s", _time)
	var e := game.engine
	if e == null or _heroes.is_empty():
		return
	_update_heroes(e, delta)
	_update_bubbles(e)
	_update_toys(e)
	_update_treats(e, delta)
	_update_ghost(e)
	if _chain_n >= 2:  # a chain of full bubbles: punch in
		_punch = minf(1.0, _punch + 0.35 + 0.15 * _chain_n)
		_trauma = maxf(_trauma, minf(0.6, 0.15 * _chain_n))
		_fx.flash(_chain_pos, Color(1.0, 0.8, 0.4), 5.0)
	_chain_n = 0
	_place_camera(delta)


func _update_heroes(e: FizzEngine, delta: float) -> void:
	for i in e.heroes.size():
		var h: Dictionary = e.heroes[i]
		var v: Dictionary = _heroes[i]
		var n: Node3D = v["node"]
		n.visible = h["alive"] and not (h["inv"] > 0.0 and fmod(_time, 0.16) < 0.05)
		n.position = world(h["pos"])
		if h["ground"] and not v["ground"]:
			v["sq"] = 0.32  # land: squash
		v["ground"] = h["ground"]
		# a springy squash and stretch (feet stay put: the origin is at the feet)
		v["sq_v"] += (-180.0 * v["sq"] - 11.0 * v["sq_v"]) * delta
		v["sq"] += v["sq_v"] * delta
		var s: float = clampf(v["sq"], -0.4, 0.4)
		n.scale = Vector3(h["facing"] * (1.0 + s * 0.55), 1.0 - s * 0.7, 1.0 + s * 0.3)
		var want := "idle"
		if e.phase == E.Phase.CLEARED: want = "cheer"
		elif not h["ground"]: want = "jump" if h["vel"].y < 0.0 else "fall"
		elif absf(h["want_x"]) > 0.2: want = "walk"
		var ap: AnimationPlayer = v["anim"]
		if v["last"] == "blow" and ap and ap.is_playing():
			continue
		if v["last"] != want:
			v["last"] = want
			_play(ap, want, want in ["idle", "walk", "fall", "cheer"])


func _make_full_bubble(b: Dictionary) -> Dictionary:
	var n := Node3D.new()
	var shell := _scene("bubble_trap", Vector3(0.5, 0.5, 0.5), Color(1, 0.8, 0.3, 0.4))
	var glow := _shader("bubble_glow.gdshader")
	glow.set_shader_parameter("phase", float(b["id"]))
	var rim := StandardMaterial3D.new()
	rim.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rim.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	for mi in shell.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			var nm := mat.resource_name if mat else ""
			if nm == "bubble":
				m.set_surface_override_material(i, glow)
			elif nm.begins_with("bubble_rim"):
				m.set_surface_override_material(i, rim)
	n.add_child(shell)
	var toy := _scene(TOY_MODELS.get(b["trapped"]["kind"], "toy_beetle"))
	toy.scale = Vector3.ONE * TOY_IN_BUBBLE
	_overlay(toy, _toy_overlay)
	n.add_child(toy)  # the trapped pose is centred on the toy's origin: it sits at the bubble's centre
	_play(toy.find_child("AnimationPlayer", true, false), "trapped", true)
	var light := OmniLight3D.new()  # lit from inside (in front of the toy, so its visible side glows)
	light.position = Vector3(0, 0.1, 0.55)
	light.omni_range = 1.3
	light.light_energy = 1.0
	light.light_specular = 0.4
	n.add_child(light)
	var halo := MeshInstance3D.new()  # the outline ring and a soft halo, behind the bubble
	var q := QuadMesh.new()
	q.size = Vector2(1.75, 1.75)
	halo.mesh = q
	var hm := _shader("halo.gdshader")
	hm.set_shader_parameter("ring_r", 0.6)
	halo.material_override = hm
	halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	halo.position.z = -0.55
	n.add_child(halo)
	return {"node": n, "has": true, "glow": glow, "rim": rim, "light": light, "halo": hm, "toy": toy, "born": _time}


func _update_bubbles(e: FizzEngine) -> void:
	var live := {}
	for b in e.bubbles:
		live[b["id"]] = true
		var trapped: bool = not b["trapped"].is_empty()
		if not _bubbles.has(b["id"]) or _bubbles[b["id"]]["has"] != trapped:
			if _bubbles.has(b["id"]):
				(_bubbles[b["id"]]["node"] as Node3D).queue_free()
			var v: Dictionary
			if trapped:
				v = _make_full_bubble(b)
			else:
				v = {"node": _scene("bubble", Vector3(0.42, 0.42, 0.42), Color(0.8, 0.9, 1.0, 0.4)), "has": false}
			_stage.add_child(v["node"])
			_bubbles[b["id"]] = v
		var v: Dictionary = _bubbles[b["id"]]
		var node: Node3D = v["node"]
		var id := float(b["id"])
		node.position = world(b["pos"], 0.1)
		var grow := clampf(b["age"] / 0.12, 0.3, 1.0)
		if not trapped:
			var wob := 1.0 + sin(_time * 7.0 + id) * 0.04
			node.scale = Vector3(wob, 2.0 - wob, 1.0) * grow
			continue
		# full: gulp in, struggle, glow; turn red and pulse faster as it is about to break free
		var age := _time - float(v["born"])
		var gulp := 1.0 + 0.35 * exp(-age * 7.0) * sin(age * 28.0)
		var warn := clampf(1.0 - b["life"] / WARN_T, 0.0, 1.0)
		var pulse := 0.5 + 0.5 * sin(_time * lerpf(5.0, 24.0, warn))
		var kick := pow(maxf(0.0, sin(_time * 2.3 + id * 1.7)), 12.0)  # every so often the toy shoves at the wall
		var wob := 1.0 + sin(_time * 9.0 + id) * (0.05 + 0.04 * warn) + kick * 0.08
		var s := TRAP_SCALE * gulp * (1.0 + warn * pulse * 0.1)
		node.scale = Vector3(wob, 2.0 - wob, 1.0) * s
		node.rotation.z = sin(_time * 6.0 + id) * 0.1 + kick * 0.25 * signf(sin(id * 3.1)) \
			+ warn * sin(_time * 31.0) * 0.08
		var toy: Node3D = v["toy"]
		toy.position = Vector3(sin(_time * 5.0 + id) * 0.04, kick * 0.06, 0.0)
		var col := FULL.lerp(WARN, warn)
		var g: ShaderMaterial = v["glow"]
		g.set_shader_parameter("color", col)
		g.set_shader_parameter("glow", 2.2 + warn * pulse * 3.5)
		g.set_shader_parameter("time_s", _time)
		(v["rim"] as StandardMaterial3D).albedo_color = Color(col.r * 2.2, col.g * 2.2, col.b * 2.2, 0.9)
		var hm: ShaderMaterial = v["halo"]
		hm.set_shader_parameter("color", col)
		hm.set_shader_parameter("strength", 1.0 + warn * pulse * 1.5)
		var light: OmniLight3D = v["light"]
		light.light_color = Color(1.0, 0.97, 0.92).lerp(col, 0.1 + warn * 0.6)
		light.light_energy = 1.0 + warn * pulse * 1.5
	for id in _bubbles.keys():
		if not live.has(id):
			_bubbles[id]["node"].queue_free()
			_bubbles.erase(id)


func _update_toys(e: FizzEngine) -> void:
	var alive := {}
	for t in e.toys:
		alive[t["id"]] = true
		if not _toys.has(t["id"]):
			var n := _scene(TOY_MODELS.get(t["kind"], "toy_beetle"), Vector3(0.35, 0.7, 0.35), Color(0.9, 0.7, 0.3))
			_overlay(n, _toy_overlay)
			_stage.add_child(n)
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			_play(ap, "fly" if t["kind"] == "flyer" else "walk", true)
			_toys[t["id"]] = {"node": n, "angry": false}
		var v: Dictionary = _toys[t["id"]]
		var n: Node3D = v["node"]
		n.position = world(t["pos"])
		n.scale = Vector3(t["facing"], 1, 1)
		if t["angry"] != v["angry"]:
			v["angry"] = t["angry"]
			_tint(n, "toy_paint", Color(1.0, 0.25, 0.2) if t["angry"] else Color(1, 1, 1))
			_overlay(n, _angry_overlay if t["angry"] else _toy_overlay)
	for id in _toys.keys():
		if not alive.has(id):
			_toys[id]["node"].queue_free()
			_toys.erase(id)


func _update_treats(e: FizzEngine, delta: float) -> void:
	var seen := {}
	for tr in e.treats:
		if not tr.has("_view"):  # a key only the view reads, so each treat keeps its own node and bounce
			_treat_key += 1
			tr["_view"] = _treat_key
		var k: int = tr["_view"]
		seen[k] = true
		if not _treats.has(k):
			var n := _scene("treat_" + tr["kind"], Vector3(0.22, 0.4, 0.22), Color(1.0, 0.4, 0.4))
			_overlay(n, _toy_overlay)
			for s in 2:
				_sparkle(n, Vector3(0.18 - s * 0.36, 0.3 + s * 0.15, 0.25), 0.5, float(k) * 1.7 + s * 2.4)
			_stage.add_child(n)
			_treats[k] = {"node": n, "ground": false, "bounce": 9.0, "born": _time}
		var v: Dictionary = _treats[k]
		var n: Node3D = v["node"]
		if tr["ground"] and not v["ground"]:
			v["bounce"] = 0.0
		v["ground"] = tr["ground"]
		v["bounce"] += delta
		var bt: float = v["bounce"]
		var hop := absf(sin(bt * 11.0)) * 0.3 * exp(-bt * 5.0)
		var age := _time - float(v["born"])
		var pop := minf(1.0, age / 0.18) * (1.0 + 0.3 * exp(-age * 6.0) * sin(age * 20.0))
		var squash := 1.0 + 0.25 * exp(-bt * 8.0) * cos(bt * 22.0)
		n.position = world(tr["pos"], 0.05) + Vector3(0, 0.06 + hop + sin(_time * 3.0 + k) * 0.04, 0)
		n.scale = Vector3(squash, 2.0 - squash, 1.0) * pop * 1.15
		n.rotation.y = _time * 1.8 + k
	for k in _treats.keys():
		if not seen.has(k):
			_treats[k]["node"].queue_free()
			_treats.erase(k)


func _make_ghost() -> Node3D:
	var g := Node3D.new()
	var body := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.62
	sm.height = 1.3
	sm.radial_segments = 48
	sm.rings = 24
	body.mesh = sm
	body.material_override = _ghost_mat
	body.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	g.add_child(body)
	var eye_m := StandardMaterial3D.new()
	eye_m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	eye_m.albedo_color = Color(1.6, 0.25, 0.12)
	for sx in [-1.0, 1.0]:  # slanted, angry slits
		var eye := MeshInstance3D.new()
		var em := SphereMesh.new()
		em.radius = 0.1
		em.height = 0.2
		eye.mesh = em
		eye.material_override = eye_m
		eye.position = Vector3(sx * 0.2, 0.12, 0.58)
		eye.scale = Vector3(1.5, 0.45, 0.5)
		eye.rotation.z = sx * -0.45
		g.add_child(eye)
	var mouth := MeshInstance3D.new()  # a jagged grin
	var mm := PrismMesh.new()
	mm.size = Vector3(0.28, 0.1, 0.04)
	mouth.mesh = mm
	mouth.material_override = eye_m
	mouth.position = Vector3(0, -0.14, 0.6)
	mouth.rotation.z = PI
	g.add_child(mouth)
	var l := OmniLight3D.new()
	l.light_color = Color(0.6, 0.2, 1.0)
	l.light_energy = 3.0
	l.omni_range = 3.5
	l.light_specular = 0.2
	l.position.z = 0.6
	g.add_child(l)
	var trail := CPUParticles3D.new()
	trail.amount = 40
	trail.lifetime = 0.9
	trail.local_coords = false
	trail.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	trail.emission_sphere_radius = 0.4
	trail.gravity = Vector3(0, 0.4, 0)
	trail.initial_velocity_max = 0.3
	trail.scale_amount_min = 0.12
	trail.scale_amount_max = 0.3
	var qm := QuadMesh.new()
	qm.size = Vector2(0.5, 0.5)
	trail.mesh = qm
	trail.material_override = Fx.material("glow", Color(0.45, 0.12, 0.9, 0.7))
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 1))
	fade.set_color(1, Color(1, 1, 1, 0))
	trail.color_ramp = fade
	trail.scale_amount_curve = Fx.size_curve(false)
	g.add_child(trail)
	return g


func _update_ghost(e: FizzEngine) -> void:
	if not e.ghost.is_empty():
		if _ghost == null:
			_ghost = _make_ghost()
			_stage.add_child(_ghost)
			var p := world(e.ghost["pos"], 0.4)
			_fx.ring(p, Color(0.7, 0.2, 1.0), 4.0, 0.7)
			_fx.flash(p, Color(0.7, 0.25, 1.0), 4.0)
		var p := world(e.ghost["pos"], 0.4)
		var vel: Vector2 = e.ghost.get("vel", Vector2.ZERO)
		_ghost.position = p + Vector3(0, sin(_time * 2.5) * 0.08, 0)
		_ghost.rotation.z = clampf(-vel.x * 0.04, -0.4, 0.4)
		var breathe := 1.0 + sin(_time * 4.0) * 0.06
		_ghost.scale = Vector3(breathe, 2.0 - breathe, 1.0) * 1.15
	elif _ghost:
		_ghost.queue_free()
		_ghost = null


# ------------------------------------------------------------------ the camera

func _place_camera(delta := 0.0) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(E.H * T * 0.5 + 0.7, (E.W * T * 0.5 + 0.5) / aspect)
	_dist = need / tan(deg_to_rad(camera.fov * 0.5))
	# lean a little towards the heroes
	var focus := Vector2.ZERO
	var n := 0
	for h in e.heroes:
		if h["alive"]:
			var w := world(h["pos"])
			focus += Vector2(w.x, w.y)
			n += 1
	if n > 0:
		focus /= n
	var want := Vector2(clampf(focus.x * 0.06, -0.35, 0.35), clampf(focus.y * 0.04, -0.2, 0.2))
	_lean = _lean.lerp(want, minf(1.0, delta * 1.2))
	_trauma = maxf(0.0, _trauma - delta * 1.4)
	_punch = maxf(0.0, _punch - delta * 2.2)
	var yaw := 0.0
	var pitch := 0.0
	var zoom := 0.985 - 0.07 * _punch * _punch * (3.0 - 2.0 * _punch)
	var target := Vector3(_lean.x, _lean.y, 0.0)
	if e.phase == E.Phase.READY:
		# swoop in at the start of a level
		_intro = maxf(0.0, _intro - delta / 1.6)
		var k := _intro * _intro * (3.0 - 2.0 * _intro)
		zoom += 0.16 * k
		yaw -= 0.1 * k
		pitch += 0.05 * k
	elif e.phase == E.Phase.CLEARED:
		# swoop round the heroes on a cleared level
		var s := clampf(1.0 - e.phase_t / 2.5, 0.0, 1.0)
		var k := s * s * (3.0 - 2.0 * s)
		yaw += 0.13 * k
		pitch -= 0.03 * k
		zoom -= 0.1 * k
		target = target.lerp(Vector3(focus.x, focus.y, 0.0) * 0.25, k)
	var d := _dist * zoom
	var off := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * d
	var shake := _trauma * _trauma
	var jitter := Vector3(sin(_time * 37.0) + sin(_time * 23.0 + 1.3), sin(_time * 31.0 + 2.1) + sin(_time * 19.0), 0.0)
	camera.position = target * 1.8 + off + Vector3(0, 0.2, 0) + jitter * shake * 0.12 \
		+ Vector3(sin(_time * 0.21) * 0.12, sin(_time * 0.17) * 0.06, 0.0)
	camera.look_at(target + jitter * shake * 0.05, Vector3.UP)
	camera.rotate_object_local(Vector3.FORWARD, jitter.x * shake * 0.012)
	_attrs.dof_blur_far_distance = d + 3.0
	_env.fog_depth_begin = d + 0.6
	_env.fog_depth_end = d + 6.5
