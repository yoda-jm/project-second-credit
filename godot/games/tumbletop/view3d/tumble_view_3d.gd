class_name TumbleView3D
extends Node3D
## Tumbletop in 3D: a pyramid of polished cubes floating over a sea of clouds, one sky per level (dawn, candy noon,
## sunset, starlight). Cube tops flip to their new colour with a sheen and a spray of sparkles; the cube dips under
## each landing. Pip hops with squash and stretch, the balls bounce, the serpent coils after him, discs spin with
## rainbow light. The camera drifts and leans towards Pip, swings round the pyramid when a round is cleared, rises with
## the disc, and closes in with a shake when he is caught.

const T = preload("res://games/tumbletop/engine/tumble_engine.gd")
const M := "res://games/tumbletop/art/models/"
const TOP := Vector3(0, 0.5, 0)
const HOP_H := 0.65
const CHAR_SCALE := 1.35  ## the characters a size up, so they read at the camera's distance
## per level: sky top / horizon / ground glow, cloud colours, sun colour and angle, cube sides, the three top colours
const THEMES := [
	{"name": "Dawn Isles", "sky": Color(0.32, 0.5, 0.85), "hor": Color(1.0, 0.78, 0.62), "cloud": Color(1.0, 0.72, 0.6),
		"cloud_low": Color(0.36, 0.34, 0.62), "sun": Color(1.0, 0.8, 0.6), "sun_rot": Vector3(-26, 30, 0),
		"side": Color(0.2, 0.24, 0.42), "tops": [Color(0.22, 0.36, 0.78), Color(0.3, 0.75, 0.9), Color(1.0, 0.78, 0.2)]},
	{"name": "Candy Noon", "sky": Color(0.35, 0.65, 1.0), "hor": Color(0.85, 0.93, 1.0), "cloud": Color(1.0, 1.0, 1.0),
		"cloud_low": Color(0.45, 0.58, 0.85), "sun": Color(1.0, 0.97, 0.9), "sun_rot": Vector3(-55, 25, 0),
		"side": Color(0.62, 0.3, 0.5), "tops": [Color(0.95, 0.35, 0.55), Color(0.4, 0.9, 0.7), Color(1.0, 0.95, 0.35)]},
	{"name": "Sunset Reach", "sky": Color(0.3, 0.2, 0.5), "hor": Color(1.0, 0.5, 0.3), "cloud": Color(1.0, 0.62, 0.45),
		"cloud_low": Color(0.45, 0.28, 0.5), "sun": Color(1.0, 0.6, 0.35), "sun_rot": Vector3(-14, 40, 0),
		"side": Color(0.3, 0.28, 0.45), "tops": [Color(0.1, 0.55, 0.6), Color(0.95, 0.45, 0.6), Color(1.0, 0.55, 0.25)]},
	{"name": "Starlight", "sky": Color(0.02, 0.03, 0.1), "hor": Color(0.2, 0.12, 0.35), "cloud": Color(0.4, 0.35, 0.7),
		"cloud_low": Color(0.06, 0.05, 0.15), "sun": Color(0.6, 0.7, 1.0), "sun_rot": Vector3(-40, -30, 0),
		"side": Color(0.14, 0.12, 0.25), "tops": [Color(0.3, 0.15, 0.6), Color(0.2, 0.85, 1.0), Color(1.0, 0.3, 0.85)]},
]

@export var game: TumbleGame

var camera: Camera3D
var _env: Environment
var _sky: ProceduralSkyMaterial
var _sun: DirectionalLight3D
var _stage: Node3D
var _cubes := {}            ## cell -> {cube, plate, mat, dip, flash}
var _hero: Node3D
var _hero_body: Node3D
var _hero_anim: AnimationPlayer  ## the model's player (idle, hop, fall, cheer, die), null for the fallback
var _discs: Array[Node3D] = []
var _enemy_nodes := {}      ## enemy dictionary id -> node
var _serpent_trail: Array[Vector3] = []
var _clouds: MeshInstance3D
var _cloud_mat: ShaderMaterial
var _stars: GPUParticles3D
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _swing := 0.0            ## the round-clear swing round the pyramid, 1 -> 0
var _focus := 0.0            ## closing in on Pip when he is caught
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _next_id := 0
var _land := 0.0             ## Pip's landing squash
var _theme: Dictionary
var _cube_shader: Shader = preload("res://games/tumbletop/shaders/cube.gdshader")
var _plate_shader: Shader = preload("res://games/tumbletop/shaders/plate.gdshader")


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_sky = ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = _sky
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.ambient_light_energy = 0.45
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 0.95
	_env.glow_enabled = true
	_env.glow_intensity = 0.8
	_env.glow_bloom = 0.06
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_env.ssao_intensity = 1.4
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.light_energy = 1.3
	_sun.directional_shadow_max_distance = 40.0
	_sun.shadow_blur = 1.5
	add_child(_sun)
	var rim := DirectionalLight3D.new()  # a cool light from behind, outlining the pyramid against the sky
	rim.rotation_degrees = Vector3(-20, 225, 0)
	rim.light_energy = 0.45
	rim.light_color = Color(0.7, 0.8, 1.0)
	add_child(rim)
	camera = Camera3D.new()
	camera.fov = 34
	camera.current = true
	camera.far = 400.0
	add_child(camera)
	# the sea of clouds
	_clouds = MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(460, 460)
	_clouds.mesh = pm
	_cloud_mat = ShaderMaterial.new()
	_cloud_mat.shader = preload("res://games/tumbletop/shaders/cloud_sea.gdshader")
	_clouds.material_override = _cloud_mat
	_clouds.position = Vector3(3, -26, 3)
	_clouds.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_clouds)
	_motes()
	_fx = Bursts.new()
	add_child(_fx)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


## Drifting motes (dust in the sun, fireflies by night) around the pyramid.
func _motes() -> void:
	_stars = GPUParticles3D.new()
	_stars.amount = 160
	_stars.lifetime = 12.0
	_stars.preprocess = 12.0
	_stars.visibility_aabb = AABB(Vector3(-30, -30, -30), Vector3(60, 60, 60))
	var pr := ParticleProcessMaterial.new()
	pr.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pr.emission_box_extents = Vector3(14, 8, 14)
	pr.gravity = Vector3(0, 0.05, 0)
	pr.initial_velocity_min = 0.05
	pr.initial_velocity_max = 0.2
	pr.spread = 180.0
	pr.turbulence_enabled = true
	pr.turbulence_noise_strength = 0.4
	pr.scale_min = 0.5
	pr.scale_max = 1.2
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0))
	fade.add_point(0.2, Color(1, 1, 1, 1))
	fade.add_point(0.8, Color(1, 1, 1, 1))
	fade.set_color(fade.get_point_count() - 1, Color(1, 1, 1, 0))
	var gt := GradientTexture1D.new()
	gt.gradient = fade
	pr.color_ramp = gt
	_stars.process_material = pr
	var q := QuadMesh.new()
	q.size = Vector2(0.03, 0.03)
	_stars.draw_pass_1 = q
	_stars.position = Vector3(2, -3, 2)
	add_child(_stars)


func _mat(col: Color, rough := 0.5, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _ball(r: float, col: Color, rough := 0.3, emit := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = 24
	s.rings = 12
	mi.mesh = s
	mi.material_override = _mat(col, rough, emit)
	return mi


## Big cartoon eyes looking along -Z.
func _eyes(parent: Node3D, at: Vector3, r: float, gap: float) -> void:
	for sx in [-1.0, 1.0]:
		var w := _ball(r, Color(1, 1, 1), 0.2)
		w.position = at + Vector3(sx * gap, 0, 0)
		parent.add_child(w)
		var p := _ball(r * 0.5, Color(0.05, 0.05, 0.08), 0.1)
		p.position = Vector3(0, 0, -r * 0.62)
		w.add_child(p)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


## Pip: an orange fuzzball with a long snout and big eyes, on two feet (the model when there is one).
func _make_hero() -> Node3D:
	var root := Node3D.new()
	var body := _scene("pip")
	if body == null:
		body = Node3D.new()
		var b := _ball(0.27, Color(1.0, 0.55, 0.12), 0.75)
		b.position = Vector3(0, 0.3, 0)
		body.add_child(b)
		var snout := MeshInstance3D.new()
		var cy := CylinderMesh.new()
		cy.top_radius = 0.085
		cy.bottom_radius = 0.11
		cy.height = 0.3
		snout.mesh = cy
		snout.material_override = _mat(Color(1.0, 0.5, 0.1), 0.7)
		snout.rotation_degrees = Vector3(-80, 0, 0)
		snout.position = Vector3(0, 0.24, -0.3)
		body.add_child(snout)
		var nose := _ball(0.1, Color(0.2, 0.08, 0.05), 0.3)
		nose.position = Vector3(0, 0.26, -0.45)
		body.add_child(nose)
		_eyes(body, Vector3(0, 0.43, -0.16), 0.085, 0.1)
		for sx in [-1.0, 1.0]:
			var f := _ball(0.1, Color(0.95, 0.4, 0.1), 0.7)
			f.scale = Vector3(0.9, 0.5, 1.4)
			f.position = Vector3(sx * 0.13, 0.04, -0.06)
			body.add_child(f)
	root.add_child(body)
	_hero_body = body
	_hero_anim = body.find_child("AnimationPlayer", true, false)
	_play(_hero_anim, "idle", true, 0.0)
	var l := OmniLight3D.new()  # a warm glow of his own, so he never disappears in a shadow
	l.light_color = Color(1.0, 0.7, 0.4)
	l.light_energy = 0.5
	l.omni_range = 1.4
	l.position = Vector3(0, 0.6, 0.3)
	root.add_child(l)
	return root


func _play(ap: AnimationPlayer, anim: String, loop := false, blend := 0.12) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, blend)


func _make_enemy(kind: String) -> Node3D:
	var n := _scene(kind)
	if n:
		_play(n.find_child("AnimationPlayer", true, false), {"imp": "bounce", "serpent": "hiss"}.get(kind, ""), true, 0.0)
		if kind == "serpent":
			n.set_meta("segments", [])
			for i in 5:
				var s := _scene("serpent_segment")
				if s == null:
					s = _ball(0.17, Color(0.55, 0.2, 0.8), 0.35)
				s.scale = Vector3.ONE * (0.17 - i * 0.02) / 0.17
				add_child(s)  # segments follow the head's trail in world space
				n.get_meta("segments").append(s)
		return n
	n = Node3D.new()
	match kind:
		"red":
			var b := _ball(0.22, Color(0.95, 0.12, 0.1), 0.15)
			b.position = Vector3(0, 0.22, 0)
			n.add_child(b)
		"green":
			var b := _ball(0.22, Color(0.3, 1.0, 0.4), 0.15, 1.6)
			b.position = Vector3(0, 0.22, 0)
			n.add_child(b)
			var l := OmniLight3D.new()
			l.light_color = Color(0.4, 1.0, 0.5)
			l.light_energy = 1.0
			l.omni_range = 1.6
			l.position = Vector3(0, 0.3, 0)
			n.add_child(l)
		"purple":
			var b := _ball(0.25, Color(0.55, 0.2, 0.85), 0.2)
			b.position = Vector3(0, 0.25, 0)
			n.add_child(b)
			var spot := _ball(0.08, Color(0.85, 0.6, 1.0), 0.2, 0.8)
			spot.position = Vector3(0.12, 0.38, -0.12)
			n.add_child(spot)
		"serpent":
			var head := _ball(0.2, Color(0.6, 0.2, 0.85), 0.35)
			head.position = Vector3(0, 0.62, 0)
			head.scale = Vector3(1.0, 0.85, 1.2)
			n.add_child(head)
			_eyes(head, Vector3(0, 0.1, -0.12), 0.07, 0.08)
			var jaw := _ball(0.12, Color(0.85, 0.55, 0.95), 0.4)
			jaw.position = Vector3(0, -0.08, -0.14)
			jaw.scale = Vector3(1.1, 0.5, 1.2)
			head.add_child(jaw)
			n.set_meta("segments", [])
			for i in 5:
				var s := _ball(0.17 - i * 0.02, Color(0.55, 0.2, 0.8).lerp(Color(0.3, 0.1, 0.55), i / 5.0), 0.35)
				add_child(s)  # segments follow the head's trail in world space
				n.get_meta("segments").append(s)
		"imp":
			var b := _ball(0.18, Color(0.35, 0.85, 0.3), 0.5)
			b.position = Vector3(0, 0.2, 0)
			n.add_child(b)
			_eyes(b, Vector3(0, 0.06, -0.1), 0.06, 0.07)
			for sx in [-1.0, 1.0]:
				var h := MeshInstance3D.new()
				var c := CylinderMesh.new()
				c.top_radius = 0.0
				c.bottom_radius = 0.05
				c.height = 0.16
				h.mesh = c
				h.material_override = _mat(Color(1.0, 0.9, 0.5), 0.4)
				h.position = Vector3(sx * 0.09, 0.2, 0)
				h.rotation_degrees = Vector3(0, 0, -sx * 20)
				b.add_child(h)
	return n


func _make_disc() -> Node3D:
	var n := _scene("disc")
	if n:
		var gl := OmniLight3D.new()  # recoloured through the rainbow by _process
		gl.light_energy = 1.4
		gl.omni_range = 2.2
		gl.position = Vector3(0, 0.3, 0)
		n.add_child(gl)
		return n
	n = Node3D.new()
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.26
	tm.outer_radius = 0.4
	ring.mesh = tm
	ring.material_override = _mat(Color(1.0, 0.85, 0.4), 0.2, 1.2)
	n.add_child(ring)
	var core := MeshInstance3D.new()
	var cy := CylinderMesh.new()
	cy.top_radius = 0.3
	cy.bottom_radius = 0.3
	cy.height = 0.04
	core.mesh = cy
	core.material_override = _mat(Color(0.6, 0.9, 1.0), 0.1, 1.8)
	n.add_child(core)
	var l := OmniLight3D.new()
	l.light_energy = 1.4
	l.omni_range = 2.2
	l.position = Vector3(0, 0.3, 0)
	n.add_child(l)
	return n


func _on_level(e: TumbleEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	for k in _enemy_nodes:
		_free_enemy(_enemy_nodes[k])
	_enemy_nodes.clear()
	_stage = Node3D.new()
	add_child(_stage)
	_cubes.clear()
	_discs.clear()
	_theme = THEMES[e.level % THEMES.size()]
	var th := _theme
	_sky.sky_top_color = th["sky"]
	_sky.sky_horizon_color = th["hor"]
	_sky.ground_horizon_color = th["hor"]
	_sky.ground_bottom_color = th["cloud_low"]
	_sky.sun_angle_max = 20.0
	_sky.sky_energy_multiplier = 1.0
	_sun.light_color = th["sun"]
	_sun.rotation_degrees = th["sun_rot"]
	_cloud_mat.set_shader_parameter("top_color", th["cloud"])
	_cloud_mat.set_shader_parameter("low_color", th["cloud_low"])
	_cloud_mat.set_shader_parameter("horizon", th["hor"])
	_env.fog_enabled = true
	_env.fog_light_color = th["hor"]
	_env.fog_density = 0.0015
	var night: bool = e.level % THEMES.size() == 3
	(_stars.draw_pass_1 as QuadMesh).material = Fx.material("glow", Color(0.6, 0.9, 1.0) if night else Color(1.0, 0.95, 0.8))
	_stars.amount = 260 if night else 120
	var side_mat := ShaderMaterial.new()
	side_mat.shader = _cube_shader
	side_mat.set_shader_parameter("side_color", th["side"])
	side_mat.set_shader_parameter("edge_color", th["hor"].lerp(Color.WHITE, 0.5))
	side_mat.set_shader_parameter("edge_glow", 0.6 if night else 0.25)
	var box := BoxMesh.new()
	box.size = Vector3.ONE * 0.98
	var plate_mesh := BoxMesh.new()
	plate_mesh.size = Vector3(0.94, 0.06, 0.94)
	for c in TumbleEngine.cells():
		var cube := MeshInstance3D.new()
		cube.mesh = box
		cube.material_override = side_mat
		cube.position = TumbleEngine.cube3(c)
		_stage.add_child(cube)
		var plate := MeshInstance3D.new()
		plate.mesh = plate_mesh
		var pm := ShaderMaterial.new()
		pm.shader = _plate_shader
		pm.set_shader_parameter("time_offset", float(c.x * 3 + c.y))
		plate.material_override = pm
		plate.position = Vector3(0, 0.5, 0)
		cube.add_child(plate)
		_cubes[c] = {"cube": cube, "plate": plate, "mat": pm, "dip": 0.0, "flash": 0.0, "pop": 0.0}
		_set_top(c, e.tiles[TumbleEngine.index(c)])
	for d in e.discs:
		var n := _make_disc()
		_stage.add_child(n)
		_discs.append(n)
	_hero = _make_hero()
	_hero.scale = Vector3.ONE * CHAR_SCALE
	_stage.add_child(_hero)
	_serpent_trail.clear()
	_swing = 0.0
	_focus = 0.0
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


func _top_color(state: int) -> Color:
	var e := game.engine
	var tops: Array = _theme["tops"]
	if state <= 0:
		return tops[0]
	if state >= e.target():
		return tops[2]
	return tops[1]


func _set_top(c: Vector2i, state: int) -> void:
	var m: ShaderMaterial = _cubes[c]["mat"]
	m.set_shader_parameter("color", _top_color(state))
	m.set_shader_parameter("glow", 0.55 if state >= game.engine.target() else 0.08)


func _disc_pos(i: int) -> Vector3:
	var d: Dictionary = game.engine.discs[i]
	var c := Vector2i(d["row"], -1) if d["side"] < 0 else Vector2i(d["row"], d["row"] + 1)
	return TumbleEngine.cube3(c) + Vector3(0, 0.35, 0)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"paint":
			var c: Vector2i = d["cell"]
			_set_top(c, d["state"])
			_cubes[c]["flash"] = 1.0
			_cubes[c]["pop"] = 1.0
			var col := _top_color(d["state"])
			var p := TumbleEngine.cube3(c) + TOP
			_fx.burst(p + Vector3(0, 0.1, 0), col.lerp(Color.WHITE, 0.3), 18 if d["done"] else 10, 2.6, 0.6, 0.09, 1.0, -4.0, 1.0, "glow")
			if d["done"]:
				_fx.flash(p + Vector3(0, -2.0, 0), col, 1.2)
		"undo":
			var c: Vector2i = d["cell"]
			_set_top(c, e.tiles[TumbleEngine.index(c)])
			_cubes[c]["flash"] = 0.6
			_fx.burst(TumbleEngine.cube3(c) + TOP, Color(0.5, 0.5, 0.6), 10, 1.5, 0.5, 0.08, 0.0, -3.0, 1.0, "smoke")
		"land":
			if d["who"] == "hero" and _cubes.has(d["cell"]):
				_cubes[d["cell"]]["dip"] = 1.0
				_land = 1.0
		"die":
			_shake = 0.8
			_focus = 1.0
			var p := _hero.global_position + Vector3(0, 0.3, 0)
			_fx.burst(p, Color(1.0, 0.6, 0.3), 30, 3.0, 0.8, 0.1, 1.0, -3.0, 1.0, "glow")
		"freeze":
			_fx.burst(_hero.global_position + Vector3(0, 0.4, 0), Color(0.5, 1.0, 0.6), 40, 4.0, 1.0, 0.1, 1.0, 0.0, 1.0, "glow")
			_fx.flash(Vector3(1.5, -3, 1.5), Color(0.5, 1.0, 0.6), 2.0)
		"catch":
			_fx.burst(_hero.global_position + Vector3(0, 0.4, 0), Color(0.5, 1.0, 0.4), 24, 3.0, 0.7, 0.09, 1.0, -3.0, 1.0, "glow")
		"lure":
			_shake = 0.3
		"hatch":
			_serpent_trail.clear()
		"disc":
			_fx.burst(_hero.global_position + Vector3(0, 0.3, 0), Color(0.7, 0.9, 1.0), 30, 3.0, 0.8, 0.09, 1.0, -1.0, 1.0, "glow")
		"hop":
			if d["who"] == "hero" and _hero_anim:
				_play(_hero_anim, "hop", false, 0.04)
				_hero_anim.seek(0.0, true)
		"cleared":
			_play(_hero_anim, "cheer", true)
			_swing = 1.0
			for c in _cubes:
				_cubes[c]["flash"] = 1.0 + c.x * 0.15
			_fx.burst(Vector3(0, 1.5, 0), Color(1.0, 0.9, 0.5), 60, 6.0, 1.4, 0.12, 1.0, -3.0, 1.0, "glow")
			_fx.flash(Vector3(1.5, -2, 1.5), _theme["tops"][2], 3.0)


func _free_enemy(n: Node3D) -> void:
	if n.has_meta("segments"):
		for s in n.get_meta("segments"):
			(s as Node3D).queue_free()
	n.queue_free()


static func _yaw(dir: String) -> float:
	return {"ur": 0.0, "ul": PI * 0.5, "dr": -PI * 0.5, "dl": PI}.get(dir, PI)


## Where an actor hopping from a to b is at progress t, with its hop's arc.
static func _arc(a: Vector2i, b: Vector2i, t: float) -> Vector3:
	var pa := TumbleEngine.cube3(a) + TOP
	var pb := TumbleEngine.cube3(b) + TOP
	return pa.lerp(pb, t) + Vector3(0, sin(t * PI) * HOP_H, 0)


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	# cubes: the dip under a landing, the top's sheen and pop
	for c in _cubes:
		var cd: Dictionary = _cubes[c]
		cd["dip"] = maxf(0.0, cd["dip"] - delta * 5.0)
		cd["flash"] = maxf(0.0, cd["flash"] - delta * 2.2)
		cd["pop"] = maxf(0.0, cd["pop"] - delta * 4.0)
		var cube: Node3D = cd["cube"]
		cube.position = TumbleEngine.cube3(c) + Vector3(0, -sin(cd["dip"] * PI) * 0.07, 0)
		(cd["mat"] as ShaderMaterial).set_shader_parameter("flash", clampf(cd["flash"], 0.0, 1.0))
		(cd["plate"] as Node3D).scale = Vector3.ONE * (1.0 + sin(cd["pop"] * PI) * 0.08)
	# discs spin and bob; a used one is gone (the ride carries it)
	for i in _discs.size():
		var dn := _discs[i]
		var used: bool = e.discs[i]["used"]
		var riding: bool = e.phase == T.Phase.RIDE and e._ride.get("disc", -1) == i
		dn.visible = not used or riding
		if not riding:
			dn.position = _disc_pos(i) + Vector3(0, sin(_time * 2.0 + i) * 0.06, 0)
		dn.rotation.y = _time * 3.0
		for ch in dn.get_children():
			if ch is OmniLight3D:
				(ch as OmniLight3D).light_color = Color.from_hsv(fmod(_time * 0.25 + i * 0.5, 1.0), 0.6, 1.0)
	_place_hero(e, delta)
	_place_enemies(e)
	_shake = maxf(0.0, _shake - delta * 1.6)
	_swing = maxf(0.0, _swing - delta / 3.0)
	_focus = maxf(0.0, _focus - delta * 0.6)
	_land = maxf(0.0, _land - delta * 6.0)
	_place_camera(delta)


func _place_hero(e: TumbleEngine, delta: float) -> void:
	var h := e.hero
	var p: Vector3
	var squash := 1.0
	if e.phase == T.Phase.RIDE:
		var i: int = e._ride["disc"]
		var k := 1.0 - e.phase_t / T.RIDE_TIME
		var a := _disc_pos(i)
		var top := TopPos()
		var mid := a.lerp(top, 0.5) + Vector3(0, 3.0, 0)
		var s := smoothstep(0.0, 1.0, k)
		p = a.lerp(mid, s).lerp(mid.lerp(top + Vector3(0, 0.3, 0), s), s)
		_discs[i].position = p - Vector3(0, 0.05, 0)
		p += Vector3(0, 0.08, 0)
	elif h["state"] == "fall":
		var ft: float = h["fall_t"]
		p = _arc(h["at"], h["to"], 1.0) - Vector3(0, ft * ft * 9.0, 0)
		_hero.rotation.z = ft * 6.0
	else:
		var t: float = h["t"]
		p = _arc(h["at"], h["to"], t) if t < 1.0 else TumbleEngine.cube3(h["to"]) + TOP
		squash = 1.0 + (0.18 * sin(t * PI) if t < 1.0 else -0.22 * sin(_land * PI))
		_hero.rotation.z = 0.0
	_hero.position = p
	if _hero_anim:
		squash = 1.0  # the model squashes and stretches in its own hop
		var cur := _hero_anim.current_animation
		if e.phase == T.Phase.DYING and h["state"] != "fall":
			if cur != "die":
				_play(_hero_anim, "die", false, 0.08)
		elif h["state"] == "fall":
			if cur != "fall":
				_play(_hero_anim, "fall", true, 0.1)
		elif e.phase == T.Phase.CLEARED:
			if cur != "cheer":
				_play(_hero_anim, "cheer", true)
		elif cur == "" or cur == "fall" or cur == "die" or cur == "cheer":
			_play(_hero_anim, "idle", true, 0.15)
	var want := _yaw(h["dir"])
	_hero.rotation.y = lerp_angle(_hero.rotation.y, want, minf(1.0, delta * 18.0))
	_hero_body.scale = Vector3(1.0 / sqrt(squash), squash, 1.0 / sqrt(squash))
	_hero.visible = not (e.phase == T.Phase.DYING and fmod(_time, 0.2) < 0.1 and h["state"] != "fall")


func TopPos() -> Vector3:
	return TumbleEngine.cube3(Vector2i(0, 0)) + TOP


func _place_enemies(e: TumbleEngine) -> void:
	var live := {}
	for en in e.enemies:
		var id: int = en.get_or_add("id", _next_id + 1)
		_next_id = maxi(_next_id, id)
		live[id] = true
		var n: Node3D = _enemy_nodes.get(id)
		if n == null or n.get_meta("kind", "") != en["kind"]:
			if n:
				_free_enemy(n)
			n = _make_enemy(en["kind"])
			n.set_meta("kind", en["kind"])
			n.scale = Vector3.ONE * CHAR_SCALE
			_stage.add_child(n)
			_enemy_nodes[id] = n
		var from: Vector2i = en.get("from_cell", en["to"])
		var t: float = en["t"]
		var p := _arc(from, en["to"], t)
		if en.get("drop", 0.0) > 0.0:
			p += Vector3(0, en["drop"] * en["drop"] * 14.0, 0)
		if en.has("fall_t"):
			p -= Vector3(0, en["fall_t"] * en["fall_t"] * 9.0, 0)
		n.position = p
		if en["kind"] in ["red", "green", "purple"]:
			var land := clampf(1.0 - absf(t - 1.0) * 8.0, 0.0, 1.0) if t >= 0.95 else 0.0
			n.scale = Vector3(1.0 + land * 0.2, 1.0 - land * 0.3 + 0.12 * sin(t * PI), 1.0 + land * 0.2) * CHAR_SCALE
		if e.frozen > 0.0:
			n.position += Vector3(sin(_time * 40.0) * 0.02, 0, 0)
		if en["kind"] in ["serpent", "imp"]:
			var d: Vector2i = en["to"] - from
			for k in T.DIRS:
				if T.DIRS[k] == d:
					n.rotation.y = lerp_angle(n.rotation.y, _yaw(k), 0.3)
		if n.has_meta("segments"):
			_trail(n)
	for id in _enemy_nodes.keys():
		if not live.has(id):
			var n: Node3D = _enemy_nodes[id]
			_fx.burst(n.global_position + Vector3(0, 0.2, 0), Color(1, 1, 1), 8, 1.5, 0.4, 0.07, 0.0, -2.0, 1.0, "smoke")
			_free_enemy(n)
			_enemy_nodes.erase(id)


## The serpent's body follows the path its head took.
func _trail(n: Node3D) -> void:
	var head := n.global_position + Vector3(0, 0.25, 0)
	if _serpent_trail.is_empty() or _serpent_trail[0].distance_to(head) > 0.04:
		_serpent_trail.push_front(head)
		if _serpent_trail.size() > 200:
			_serpent_trail.resize(200)
	var segs: Array = n.get_meta("segments")
	var gap := 0.22
	var want := gap
	var acc := 0.0
	var j := 0
	for i in range(1, _serpent_trail.size()):
		acc += _serpent_trail[i].distance_to(_serpent_trail[i - 1])
		while j < segs.size() and acc >= want:
			(segs[j] as Node3D).global_position = _serpent_trail[i] - Vector3(0, j * 0.03, 0)
			j += 1
			want += gap
	for k in range(j, segs.size()):
		(segs[k] as Node3D).global_position = head - Vector3(0, 0.1 + k * 0.05, 0)


## The camera looks at the pyramid from the front diagonal, drifting a little and leaning towards Pip; it swings
## round when a round is cleared, closes in when he is caught, and rises with a disc ride.
func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var centre := Vector3(1.6, -2.9, 1.6)
	var hp := _hero.position if _hero else centre
	var yaw := deg_to_rad(45.0 + sin(_time * 0.21) * 4.0)
	if _swing > 0.0:
		# a full turn round the pyramid, eased in and out
		yaw += TAU * (1.0 - smoothstep(0.0, 1.0, _swing))
	var pitch := deg_to_rad(24.0 + sin(_time * 0.17) * 1.5)
	var dist := 16.5
	var aspect := get_viewport().get_visible_rect().size.aspect()
	if aspect < 1.5:
		dist *= 1.5 / aspect
	var look := centre.lerp(hp, 0.22)
	if e and e.phase == T.Phase.RIDE:
		look = centre.lerp(hp, 0.5)
	dist *= 1.0 - 0.3 * smoothstep(0.0, 1.0, _focus)
	dist *= 1.0 + 0.35 * sin(_swing * PI)  # wider while it swings round
	look = look.lerp(hp, 0.5 * smoothstep(0.0, 1.0, _focus))
	var dir := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))
	var pos := look + dir * dist
	var j := Vector3(sin(_time * 47.0), cos(_time * 39.0), 0) * _shake * _shake * (0.25 if Settings.camera_shake else 0.0)
	var k := 1.0 if snap else minf(1.0, delta * 3.5)
	_cam_pos = _cam_pos.lerp(pos, k)
	_cam_look = _cam_look.lerp(look, k)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
