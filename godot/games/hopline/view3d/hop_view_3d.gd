class_name HopView3D
extends Node3D
## Hopline in 3D: a toy canal town seen from behind the start bank. The road is lined with lamps, the canal glints,
## logs bob and turtles dip under, the frog springs from cell to cell, and the hedge at the top holds the five bays.
## Cell (x, row) is world (x - 7, 0, row - 6): the frog hops towards -Z.
## Each stage has its time of day (a golden afternoon, a sunset, a night with the lamps, the lit windows and the
## headlights on), eased from one to the next. The camera follows the frog up the board, punches in on a frog home,
## swoops over the hedge when all five bays fill and shakes on a squash.

const E = preload("res://games/hopline/engine/hop_engine.gd")
const M := "res://games/hopline/art/models/"
const PAINTS := [Color(0.9, 0.25, 0.2), Color(0.2, 0.5, 0.9), Color(0.95, 0.75, 0.2), Color(0.3, 0.75, 0.4), Color(0.9, 0.5, 0.75)]
const LOGS := {3.0: "log_short", 4.0: "log_mid", 6.0: "log_long"}
const LAMP_HEAD := Vector3(0, 1.68, 0)
## Times of day, one per stage in turn. night: 0 the lamps are off, 1 full night (lamps, windows, headlights).
const MOODS := [
	{"name": "GOLDEN AFTERNOON", "sun": Vector3(-38, -32, 0), "sun_col": Color(1.0, 0.84, 0.6), "sun_e": 1.2,
		"top": Color(0.3, 0.52, 0.86), "hor": Color(1.0, 0.82, 0.62), "gnd": Color(0.55, 0.5, 0.42), "amb": 0.38,
		"night": 0.0, "deep": Color(0.03, 0.19, 0.24), "shallow": Color(0.12, 0.42, 0.42), "sky": Color(0.6, 0.76, 0.9),
		"sparkle": 0.5, "exposure": 1.0, "glow": 0.55, "fog": Color(1.0, 0.85, 0.65)},
	{"name": "SUNSET", "sun": Vector3(-15, -62, 0), "sun_col": Color(1.0, 0.6, 0.34), "sun_e": 1.6,
		"top": Color(0.22, 0.26, 0.52), "hor": Color(1.0, 0.64, 0.42), "gnd": Color(0.35, 0.28, 0.3), "amb": 0.42,
		"night": 0.4, "deep": Color(0.05, 0.12, 0.25), "shallow": Color(0.14, 0.24, 0.4), "sky": Color(0.6, 0.48, 0.62),
		"sparkle": 1.2, "exposure": 1.0, "glow": 0.7, "fog": Color(1.0, 0.55, 0.4)},
	{"name": "NIGHT", "sun": Vector3(-52, 28, 0), "sun_col": Color(0.55, 0.66, 1.0), "sun_e": 0.42,
		"top": Color(0.02, 0.03, 0.09), "hor": Color(0.07, 0.09, 0.2), "gnd": Color(0.03, 0.03, 0.05), "amb": 1.4,
		"night": 1.0, "deep": Color(0.02, 0.06, 0.12), "shallow": Color(0.05, 0.15, 0.22), "sky": Color(0.2, 0.28, 0.5),
		"sparkle": 0.25, "exposure": 1.05, "glow": 0.9, "fog": Color(0.1, 0.12, 0.25)},
]
## Emissive materials by name: [night-0 factor, night-1 factor] on their imported strength.
const GLOWS := {"lamp_post_glow": [0.06, 1.3], "lamp_post_glass": [0.1, 1.4], "house_a_glow": [0.05, 1.1],
	"house_b_glow": [0.05, 1.1], "_tail": [0.35, 1.6], "home_bay_glow": [0.25, 1.3], "_glow": [0.2, 1.4]}

@export var game: HopGame

var camera: Camera3D
var mood := 0
var _env: Environment
var _sky: ProceduralSkyMaterial
var _sun: DirectionalLight3D
var _water: ShaderMaterial
var _stage: Node3D
var _objs: Array = []        ## per lane: Array of nodes (one per object)
var _frog: Node3D
var _frog_anim: AnimationPlayer
var _frog_light: OmniLight3D
var _homes: Array[Node3D] = []
var _fly: Node3D
var _fly_light: OmniLight3D
var _croc: Node3D
var _lady: Node3D
var _fx: HopFx
var _time := 0.0
var _mats := {}
var _glow_mats: Array = []   ## [material, base energy, [day, night]]
var _lamps: Array[OmniLight3D] = []
var _lamp_pos: Array[Vector3] = []
var _heads: Array = []       ## [SpotLight3D, beam MeshInstance3D, beam material]
var _mood_from := {}
var _mood_now := {}
var _mood_k := 1.0
var _probe_t := -1.0
# the camera
var _cam_target := Vector3(0, 0, -1.0)
var _cam_dist := 30.0
var _cam_yaw := 0.0
var _cam_el := 51.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _trauma := 0.0
# juice
var _squash := 0.0
var _squash_v := 0.0
var _rings: Array = []       ## [x, z, age, strength]
var _honk_t := 6.0
var _honk_cool := 0.0
var _bubble_t := 0.0


static func cell(x: float, row: float, y := 0.0) -> Vector3:
	return Vector3(x - 7.0, y, row - 6.0)


func _ready() -> void:
	_env = Environment.new()
	var sky := Sky.new()
	_sky = ProceduralSkyMaterial.new()
	sky.sky_material = _sky
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_normalized = true
	_env.glow_bloom = 0.04
	_env.glow_hdr_threshold = 1.0
	_env.glow_hdr_scale = 2.0
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	for i in 7:
		_env.set_glow_level(i, 1.0 if i in [1, 2, 3, 4] else 0.0)
	_env.ssao_enabled = true
	_env.ssao_intensity = 1.6
	_env.ssr_enabled = true
	_env.ssr_max_steps = 48
	_env.ssr_fade_in = 0.1
	_env.ssr_fade_out = 1.5
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.12
	_env.adjustment_contrast = 1.04
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.shadow_blur = 1.2
	_sun.directional_shadow_max_distance = 42.0
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 40
	camera.current = true
	add_child(camera)
	_fx = HopFx.new()
	add_child(_fx)
	_mood_now = MOODS[0].duplicate()
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String, size := Vector3(0.8, 0.4, 0.6), col := Color(0.5, 0.6, 0.4)) -> Node3D:
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


## Recolours the car paint (a glossy clear coat over it).
func _tint(n: Node, match_name: String, col: Color) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = col
				t.roughness = 0.22
				t.metallic = 0.25
				t.metallic_specular = 0.7
				t.clearcoat_enabled = true
				t.clearcoat = 1.0
				t.clearcoat_roughness = 0.04
				t.rim_enabled = true
				t.rim = 0.25
				t.rim_tint = 0.6
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


## Emissive materials (lamps, windows, headlights, rear lights) get a shared copy each, dimmed by day.
func _collect_glows(root: Node) -> void:
	var by_name := {}
	for g in _glow_mats:
		by_name[(g[0] as StandardMaterial3D).resource_name] = g[0]
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null:
			continue
		for i in m.mesh.get_surface_count():
			var mat := m.get_active_material(i) as StandardMaterial3D
			if mat == null or not mat.emission_enabled:
				continue
			var nm := mat.resource_name
			var rule: Array = []
			for k in GLOWS:
				if nm == k or (k.begins_with("_") and nm.ends_with(k)):
					rule = GLOWS[k]
					break
			if rule.is_empty() or nm.begins_with("fly") or nm.begins_with("frog") or nm.begins_with("lady"):
				continue
			if not by_name.has(nm):
				var t := mat.duplicate() as StandardMaterial3D
				by_name[nm] = t
				_glow_mats.append([t, mat.emission_energy_multiplier, rule, mat.albedo_color, nm.begins_with("house")])
			m.set_surface_override_material(i, by_name[nm])


func _on_stage(e: HopEngine) -> void:
	e.event.connect(_on_event)
	var first := _stage == null
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_objs.clear()
	_homes.clear()
	_glow_mats.clear()
	_lamps.clear()
	_lamp_pos.clear()
	_heads.clear()
	_rings.clear()
	# the time of day eases in from the last stage's
	mood = game.stage % MOODS.size()
	_mood_from = _mood_now.duplicate()
	_mood_k = 1.0 if first else 0.0
	if first:
		_mood_now = MOODS[mood].duplicate()
	_fx.set_air(mood)
	_build_ground(e)
	for r in E.ROWS:
		var nodes: Array = []
		var ln: Dictionary = e.lanes[r]
		var i := 0
		for o in ln["objs"]:
			var n := _object(o, ln, i)
			_stage.add_child(n)
			nodes.append(n)
			i += 1
		_objs.append(nodes)
	_frog = _scene("frog", Vector3(0.5, 0.35, 0.6), Color(0.3, 0.8, 0.3))
	_stage.add_child(_frog)
	_frog_anim = _frog.find_child("AnimationPlayer", true, false)
	_play(_frog_anim, "idle", true)
	_frog_light = OmniLight3D.new()
	_frog_light.position = Vector3(0, 0.9, 0.3)
	_frog_light.light_color = Color(0.8, 1.0, 0.8)
	_frog_light.omni_range = 2.2
	_frog_light.light_specular = 0.2
	_frog.add_child(_frog_light)
	for b in 5:
		var h := _scene("frog", Vector3(0.5, 0.35, 0.6), Color(0.3, 0.8, 0.3))
		h.position = cell(E.BAYS[b], 0, 0.02)
		h.rotation.y = PI
		h.visible = false
		_stage.add_child(h)
		_homes.append(h)
	_fly = _scene("fly", Vector3(0.2, 0.2, 0.2), Color(1.0, 1.0, 0.5))
	_fly.visible = false
	_play(_fly.find_child("AnimationPlayer", true, false), "buzz", true)
	_fly_light = OmniLight3D.new()
	_fly_light.position = Vector3(0, 0.35, 0)
	_fly_light.light_color = Color(0.85, 1.0, 0.4)
	_fly_light.omni_range = 1.6
	_fly.add_child(_fly_light)
	_stage.add_child(_fly)
	_croc = _scene("croc", Vector3(0.8, 0.3, 0.8), Color(0.3, 0.5, 0.2))
	_croc.visible = false
	_croc.rotation.y = PI * 0.5
	_stage.add_child(_croc)
	_lady = _scene("lady_frog", Vector3(0.4, 0.3, 0.5), Color(1.0, 0.5, 0.7))
	_lady.visible = false
	_stage.add_child(_lady)
	_collect_glows(_stage)
	_probe_t = 0.1 if first else 2.8
	# the camera sweeps in from above the town
	var full := _full_dist()
	if first:
		_cam_dist = full * 1.35
		_cam_target = Vector3(0, 0, -2.0)
		_cam_el = 62.0
	_apply_mood(0.0)
	_place_camera(0.0)


func _object(o: Dictionary, ln: Dictionary, i: int) -> Node3D:
	var type: String = o["type"]
	var n: Node3D
	if type.begins_with("turtle"):
		n = Node3D.new()
		for k in int(o["len"]):
			var t := _scene("turtle", Vector3(0.8, 0.3, 0.8), Color(0.3, 0.55, 0.3))
			t.position.x = k + 0.5 - o["len"] * 0.5
			t.rotation.y = PI if ln["dir"] < 0 else 0.0
			var ap: AnimationPlayer = t.find_child("AnimationPlayer", true, false)
			_play(ap, "swim", true)
			if ap:
				ap.seek(randf_range(0.0, 1.0), true)
			n.add_child(t)
	elif ln["river"]:
		n = _scene(LOGS.get(o["len"], "log_mid"), Vector3(o["len"], 0.4, 0.7), Color(0.5, 0.35, 0.2))
		n.rotation.y = 0.0 if i % 2 == 0 else PI  # vary the look of logs (they are symmetric enough)
	else:
		n = _scene(type, Vector3(o["len"], 0.6, 0.7), PAINTS[i % PAINTS.size()])
		_tint(n, "paint", PAINTS[(i + type.length()) % PAINTS.size()])
		n.rotation.y = 0.0 if ln["dir"] > 0 else PI
		# headlights for the night: a spot on the road and a soft beam in the air
		var front: float = o["len"] * 0.5
		var spot := SpotLight3D.new()
		spot.position = Vector3(front, 0.32, 0)
		spot.rotation = Vector3(deg_to_rad(-12), -PI * 0.5, 0)
		spot.rotation_order = EULER_ORDER_YXZ
		spot.light_color = Color(1.0, 0.85, 0.6)
		spot.spot_range = 4.5
		spot.spot_angle = 34.0
		spot.spot_attenuation = 0.8
		spot.light_specular = 0.4
		spot.visible = false
		n.add_child(spot)
		var beam := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.06
		cm.bottom_radius = 0.6
		cm.height = 2.6
		cm.radial_segments = 16
		cm.rings = 1
		cm.cap_top = false
		cm.cap_bottom = false
		beam.mesh = cm
		var bm := ShaderMaterial.new()
		bm.shader = preload("res://games/hopline/view3d/beam.gdshader")
		beam.material_override = bm
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		beam.position = Vector3(front + 1.25, 0.28, 0)
		beam.rotation = Vector3(0, 0, PI * 0.5 + 0.06)   # the tip at the car, the mouth ahead, dipped a little
		beam.visible = false
		n.add_child(beam)
		_heads.append([spot, beam, bm])
	return n


## Banks, road, median, the canal and the hedge, a few cells wider than the board on each side, and the town around.
func _build_ground(e: HopEngine) -> void:
	for r in E.ROWS:
		for x in range(-16, E.W + 17):
			var tile := ""
			if r == 12 or r == 6:
				tile = "bank_tile" if r == 12 else "median_tile"
			elif r >= 7:
				tile = "road_tile_line" if r != 7 and ResourceLoader.exists(M + "road_tile_line.glb") else "road_tile"
			else:
				continue
			var t := _scene(tile, Vector3(1, 0.05, 1), Color(0.3, 0.3, 0.32) if r >= 7 and r <= 11 else Color(0.4, 0.65, 0.3))
			t.position = cell(x + 0.5, r, 0.0)
			_stage.add_child(t)
	# the canal: one sheet of water below the banks, with stone edges
	var water := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(E.W + 34, 5.0)
	pm.subdivide_width = 120
	pm.subdivide_depth = 20
	water.mesh = pm
	_water = ShaderMaterial.new()
	_water.shader = load("res://games/hopline/view3d/canal.gdshader")
	_water.set_shader_parameter("normal_map", load("res://core/art/textures/water/normal.png"))
	water.material_override = _water
	water.position = cell(7.0, 3.0, -0.1)
	_stage.add_child(water)
	for x in range(-16, E.W + 17):
		for r in [5.5, 0.5]:
			var edge := _scene("water_edge", Vector3(1, 0.15, 0.15), Color(0.6, 0.58, 0.55))
			edge.position = cell(x + 0.5, r, 0.0)
			edge.rotation.y = 0.0 if r > 3 else PI
			_stage.add_child(edge)
	# the hedge row with its bays
	for x in range(-16, E.W + 17):
		var xc := float(x)
		if E.BAYS.has(xc):
			var b := _scene("home_bay", Vector3(1, 0.2, 1), Color(0.3, 0.5, 0.35))
			b.position = cell(xc, 0, 0.0)
			_stage.add_child(b)
		else:
			var h := _scene("hedge_block", Vector3(1, 0.8, 1), Color(0.2, 0.45, 0.2))
			h.position = cell(xc, 0, 0.0)
			_stage.add_child(h)
	# the town: houses behind the hedge and behind the start bank, lamps along the road, trees
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	# houses only behind the hedge: in front they would hide the start bank
	for x in range(-8, E.W + 9, 2):
		var n := _scene("house_a" if rng.randf() < 0.5 else "house_b", Vector3(1.6, 1.8, 1.4), Color(0.85, 0.7, 0.55))
		n.position = cell(x + rng.randf_range(-0.2, 0.2), -1.9, 0.0)
		_stage.add_child(n)
	# a second row further back, taller, and trees between: a skyline for the swoop over the hedge
	for x in range(-19, E.W + 20, 2):
		var n := _scene("house_b" if rng.randf() < 0.5 else "house_a", Vector3(1.6, 1.8, 1.4), Color(0.85, 0.7, 0.55))
		n.position = cell(x + rng.randf_range(-0.2, 0.2), -4.3, 0.0)
		n.scale = Vector3(1.0, rng.randf_range(1.05, 1.4), 1.0)
		n.rotation.y = PI if rng.randf() < 0.3 else 0.0
		_stage.add_child(n)
	for i in 14:
		var t := _scene("tree", Vector3(0.6, 1.5, 0.6), Color(0.25, 0.55, 0.25))
		t.position = cell(rng.randf_range(-16, E.W + 16), -6.4, 0.0)
		t.scale = Vector3.ONE * rng.randf_range(1.2, 1.7)
		_stage.add_child(t)
	# a grass verge in front of the start bank
	var verge := MeshInstance3D.new()
	var vm := PlaneMesh.new()
	vm.size = Vector2(E.W + 14, 4.0)
	verge.mesh = vm
	verge.material_override = Pbr.material("grass", Color(0.75, 0.9, 0.6), 0.5)
	verge.position = cell(7.0, 14.5, -0.02)
	_stage.add_child(verge)
	# and the land all round, under everything
	var land := MeshInstance3D.new()
	var lm := PlaneMesh.new()
	lm.size = Vector2(80, 60)
	land.mesh = lm
	land.material_override = Pbr.material("grass", Color(0.6, 0.75, 0.5), 0.5)
	land.position = cell(7.0, 4.0, -0.4)
	_stage.add_child(land)
	for x in range(-4, E.W + 5, 3):
		for r in [6.45, 12.45]:
			var l := _scene("lamp_post", Vector3(0.1, 1.6, 0.1), Color(0.2, 0.2, 0.2))
			l.position = cell(x, r, 0.0)
			_stage.add_child(l)
			# its light, lit at dusk: a warm pool on the pavement
			var ol := OmniLight3D.new()
			ol.position = l.position + LAMP_HEAD
			ol.light_color = Color(1.0, 0.72, 0.4)
			ol.omni_range = 3.6
			ol.omni_attenuation = 1.1
			ol.light_specular = 0.35
			ol.visible = false
			_stage.add_child(ol)
			_lamps.append(ol)
			if r < 7.0:
				_lamp_pos.append(l.position + LAMP_HEAD)
	for i in 10:
		var t := _scene("tree", Vector3(0.6, 1.5, 0.6), Color(0.25, 0.55, 0.25))
		var front := i % 2 == 0
		t.position = cell(rng.randf_range(-5, E.W + 5) if not front else [-3.5, -2.0, E.W + 2.0, E.W + 3.5, -4.5][i / 2], 13.4 if front else -0.9, 0.0)
		_stage.add_child(t)


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.05)


func _ring(p: Vector3, strength := 1.0) -> void:
	_rings.append([p.x, p.z, 0.0, strength])
	if _rings.size() > 8:
		_rings.pop_front()


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hop":
			_play(_frog_anim, "hop")
			_squash_v += 7.0   # stretch on take-off
			if not e.lanes[int(e.hop_from.y)]["river"]:
				_fx.dust(cell(e.hop_from.x, e.hop_from.y, 0.0))
		"land":
			var r: int = d["row"]
			_squash = -0.28     # squash on landing
			_squash_v = 0.0
			var p := cell(e.x, e.row, 0.0)
			if e.lanes[r]["river"]:
				_fx.splash(p + Vector3(0, 0.1, 0))
				_ring(p, 0.7)
			elif r != 0:
				_fx.dust(p)
				_near_miss(e, r)
		"die":
			var p := cell(d["x"], d["row"], 0.2)
			if d["how"] in ["drown", "swept"]:
				_play(_frog_anim, "drown")
				_fx.splash(p, true)
				_ring(p, 1.2)
				_fx.bubbles(p + Vector3(0, -0.1, 0), 10)
				_trauma = maxf(_trauma, 0.35)
			elif d["how"] == "croc":
				_play(_frog_anim, "splat")
				_fx.splash(p, true)
				_trauma = maxf(_trauma, 0.7)
			elif d["how"] == "time":
				_play(_frog_anim, "splat")
				_fx.burst(p, Color(0.8, 0.8, 0.85, 0.7), 14, 1.2, 0.8, 0.3, 0.0, 0.3, 1.0, "smoke")
				_trauma = maxf(_trauma, 0.3)
			else:
				_play(_frog_anim, "splat")
				_fx.burst(p, Color(0.4, 0.8, 0.3), 20, 2.0, 0.5, 0.07, 0.0, -6.0, 1.0)
				_fx.burst(p, Color(1.0, 1.0, 0.8), 12, 3.0, 0.3, 0.1, 1.0, -2.0, 0.6, "glow")
				_trauma = maxf(_trauma, 0.8)
		"home":
			var b: int = d["bay"]
			var hp := cell(E.BAYS[b], 0, 0.4)
			_homes[b].visible = true
			_play(_homes[b].find_child("AnimationPlayer", true, false), "home")
			_fx.burst(hp, Color(1.0, 0.85, 0.4), 26, 2.4, 0.7, 0.09, 1.0, -2.0, 1.0, "glow")
			_fx.sparkle(hp + Vector3(0, 0.3, 0), Color(1.0, 1.0, 0.8), 10)
			_fx.flash(hp, Color(1.0, 0.85, 0.5), 3.0)
			_punch = 1.0
			_punch_at = hp
			if game.streak >= 3:
				_fx.confetti(hp + Vector3(0, 0.2, 0.5), false)
		"fly":
			_fx.sparkle(cell(e.x, 0, 0.6), Color(0.8, 1.0, 0.4), 30)
		"lady":
			_fx.sparkle(_frog.position + Vector3(0, 0.4, 0), Color(1.0, 0.55, 0.8), 18)
		"lady_home":
			_fx.sparkle(cell(e.x, 0, 0.7), Color(1.0, 0.55, 0.8), 30)
		"extra_life":
			_fx.sparkle(_frog.position + Vector3(0, 0.5, 0), Color(0.5, 1.0, 0.5), 30)
		"turtle_dive":
			var r: int = d["row"]
			for i in e.lanes[r]["objs"].size():
				var o: Dictionary = e.lanes[r]["objs"][i]
				if o["dive"] >= 0.0 and e.sunk(o, e.time) > 0.0 and e.sunk(o, e.time - 0.1) == 0.0:
					var c := cell(e.obj_x(r, o, e.time) + o["len"] * 0.5, r, -0.05)
					for k in int(o["len"]):
						_fx.bubbles(c + Vector3(k + 0.5 - o["len"] * 0.5, 0, 0), 5)
					_ring(c, 0.8)
		"all_home":
			for i in 5:
				_fx.burst(cell(E.BAYS[i], 0, 0.6), Color(1.0, 0.8, 0.4), 16, 3.0, 0.8, 0.08, 1.0, -3.0, 1.0, "glow")
			_fx.confetti(cell(7.0, 1.0, 0.3))
			_fx.fireworks(cell(7.0, -2.5, 0.0), 12, 2.6)


## A car the frog lands just in front of honks at it.
func _near_miss(e: HopEngine, r: int) -> void:
	if _honk_cool > 0.0:
		return
	var ln: Dictionary = e.lanes[r]
	for i in ln["objs"].size():
		var o: Dictionary = ln["objs"][i]
		var ox := e.obj_x(r, o, e.time)
		var gap: float = (e.x - (ox + o["len"])) if ln["dir"] > 0 else (ox - e.x)
		if gap > 0.2 and gap < 2.6:
			_honk(r, i, true)
			return


func _honk(r: int, i: int, near: bool) -> void:
	var e := game.engine
	var n: Node3D = _objs[r][i]
	var o: Dictionary = e.lanes[r]["objs"][i]
	var dir: float = e.lanes[r]["dir"]
	n.set_meta("bump", 1.0)
	_honk_cool = 1.2
	var front := n.position + Vector3(dir * o["len"] * 0.5, 0.5, 0)
	_fx.honk(front, dir)
	game.fx.emit("honk", {"pos": front, "near": near, "big": o["len"] > 2.0})


func _full_dist() -> float:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(8.2, 10.5 / aspect)
	return need / tan(deg_to_rad(40.0 * 0.5))


func _lerp_mood(a: Dictionary, b: Dictionary, k: float) -> Dictionary:
	var out := {}
	for key in b:
		var va = a.get(key, b[key])
		var vb = b[key]
		if vb is float or vb is Color or vb is Vector3:
			out[key] = lerp(va, vb, k)
		else:
			out[key] = vb
	return out


func _apply_mood(delta: float) -> void:
	if _mood_k < 1.0:
		_mood_k = minf(1.0, _mood_k + delta / 2.5)
		_mood_now = _lerp_mood(_mood_from, MOODS[mood], _mood_k * _mood_k * (3.0 - 2.0 * _mood_k))
	var m := _mood_now
	var night: float = m["night"]
	_sun.rotation_degrees = m["sun"]
	_sun.light_color = m["sun_col"]
	_sun.light_energy = m["sun_e"]
	_sky.sky_top_color = m["top"]
	_sky.sky_horizon_color = m["hor"]
	_sky.ground_horizon_color = m["hor"].darkened(0.3)
	_sky.ground_bottom_color = m["gnd"]
	Look.sky_ambient(_env, (m["top"] as Color).lerp(m["hor"], 0.5), m["amb"])
	_env.tonemap_exposure = m["exposure"]
	_env.glow_intensity = m["glow"]
	_env.glow_hdr_threshold = lerpf(1.05, 0.8, night)
	_water.set_shader_parameter("deep", m["deep"])
	_water.set_shader_parameter("shallow", m["shallow"])
	_water.set_shader_parameter("sky", m["sky"])
	_water.set_shader_parameter("sun_col", m["sun_col"])
	# the glitter is staged: always as if the sun were ahead, low over the town, on its side of the sky
	var sd := _sun.global_transform.basis.z
	_water.set_shader_parameter("sun_dir", Vector3(sd.x * 0.15, 0.78, -0.62).normalized())
	_water.set_shader_parameter("sparkle", m["sparkle"])
	var lamp_e := smoothstep(0.15, 1.0, night)
	for l in _lamps:
		l.visible = lamp_e > 0.02
		l.light_energy = lamp_e * (1.4 if l.position.z > 3.0 else 2.2)
	var lp := PackedVector4Array()
	for p in _lamp_pos:
		lp.append(Vector4(p.x, p.y, p.z, lamp_e))
	_water.set_shader_parameter("lamps", lp)
	_water.set_shader_parameter("lamp_count", lp.size())
	for g in _glow_mats:
		var rule: Array = g[2]
		var gm := g[0] as StandardMaterial3D
		gm.emission_energy_multiplier = g[1] * lerpf(rule[0], rule[1], night)
		if g[4]:
			# lit windows: the pane goes dark and the warm light inside shows
			gm.albedo_color = (g[3] as Color).lerp(Color(0.12, 0.08, 0.05), night)
			gm.emission = Color(1.0, 0.72, 0.35).lerp(Color(1.0, 0.58, 0.24), night)
	var head_e := smoothstep(0.3, 1.0, night)
	for h in _heads:
		(h[0] as SpotLight3D).visible = head_e > 0.02
		(h[0] as SpotLight3D).light_energy = head_e * 2.2
		(h[1] as MeshInstance3D).visible = head_e > 0.02
		(h[2] as ShaderMaterial).set_shader_parameter("strength", head_e * 0.08)
	_frog_light.light_energy = night * 0.9
	_fly_light.light_energy = 0.4 + night * 1.6


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _frog == null:
		return
	_apply_mood(delta)
	if _probe_t > 0.0:
		_probe_t -= delta
		if _probe_t <= 0.0 and _mood_k >= 1.0:
			_add_probe()
		elif _probe_t <= 0.0:
			_probe_t = 0.2
	# lanes
	var riders := PackedVector4Array()
	var rider_v := PackedFloat32Array()
	for r in E.ROWS:
		var ln: Dictionary = e.lanes[r]
		var nodes: Array = _objs[r]
		for i in nodes.size():
			var o: Dictionary = ln["objs"][i]
			var n: Node3D = nodes[i]
			var ox := e.obj_x(r, o, e.time)
			var bob := 0.0
			var np: Vector3
			if ln["river"]:
				var sunk := e.sunk(o, e.time)
				bob = -0.1 + sin(_time * 2.0 + i + r) * 0.03 - sunk * 0.45
				np = cell(ox + o["len"] * 0.5, r, bob)
				if o["type"].begins_with("turtle"):
					# nose down going under, nose up coming back
					var going := e.sunk(o, e.time + 0.1) - sunk
					var tilt := clampf(going * 8.0, -1.0, 1.0) * 0.45
					for t in n.get_children():
						(t as Node3D).rotation.z = lerpf((t as Node3D).rotation.z, -tilt, minf(1.0, delta * 10.0))
				else:
					n.rotation.x = sin(_time * 1.3 + i * 2.0 + r) * 0.04
				riders.append(Vector4(np.x, np.z, o["len"] * 0.5 - (0.1 if o["type"].begins_with("turtle") else 0.0), 1.0 - sunk))
				rider_v.append(ln["dir"] * ln["speed"])
			else:
				np = cell(ox + o["len"] * 0.5, r, 0.0)
				if n.has_meta("last"):
					# roll the wheels by the distance travelled
					var dist: float = np.x - (n.get_meta("last") as Vector3).x
					for w in n.find_children("wheel_*", "Node3D", true, false):
						(w as Node3D).rotation.z -= dist / 0.14 * (1.0 if ln["dir"] > 0 else -1.0)
				n.set_meta("last", np)
				# a honk makes the car jump on its springs
				var b: float = n.get_meta("bump", 0.0)
				if b > 0.0:
					b = maxf(0.0, b - delta * 2.5)
					n.set_meta("bump", b)
					var k := 1.0 - b
					np.y += sin(k * PI) * 0.16 * b
					var sq := sin(k * PI * 3.0) * 0.12 * b
					n.scale = Vector3(1.0 - sq * 0.5, 1.0 + sq, 1.0 - sq * 0.5)
				else:
					n.scale = Vector3.ONE
			n.position = np
			n.visible = ox + o["len"] > -5.5 and ox < E.W + 5.5
	_water.set_shader_parameter("riders", riders)
	_water.set_shader_parameter("rider_v", rider_v)
	_water.set_shader_parameter("rider_count", riders.size())
	# splash rings
	var rings := PackedVector4Array()
	for rg in _rings:
		rg[2] += delta
		rings.append(Vector4(rg[0], rg[1], rg[2], rg[3]))
	_rings = _rings.filter(func(rg): return rg[2] < 1.4)
	while rings.size() < 8:
		rings.append(Vector4(0, 0, 0, 0))
	_water.set_shader_parameter("rings", rings)
	# bubbles over the turtles that are under
	_bubble_t -= delta
	if _bubble_t <= 0.0:
		_bubble_t = 0.35
		for r in [5, 2]:
			for i in e.lanes[r]["objs"].size():
				var o: Dictionary = e.lanes[r]["objs"][i]
				if e.sunk(o, e.time) > 0.5:
					var n: Node3D = _objs[r][i]
					_fx.bubbles(n.global_position + Vector3(randf_range(-0.5, 0.5) * o["len"], 0.25, randf_range(-0.2, 0.2)), 2)
	# the frog: an arc while in the air
	var p := cell(e.x, e.row, 0.0)
	if e.hop_left > 0:
		var k := 1.0 - float(e.hop_left) / E.HOP_TICKS
		p = cell(e.hop_from.x, e.hop_from.y, 0.0).lerp(cell(e.x, e.row, 0.0), k)
		p.y = sin(k * PI) * 0.22  # the hop animation adds its own spring
		if e.lanes[e.row]["river"]:
			p.y += k * 0.1
	elif e.lanes[e.row]["river"]:
		p.y = 0.1 + sin(_time * 2.0) * 0.03  # riding a log or a turtle's back
	_frog.position = p
	var f := Vector2(e.facing)
	_frog.rotation.y = lerp_angle(_frog.rotation.y, atan2(-f.x, -f.y), minf(1.0, delta * 25.0))
	_frog.visible = not (e.phase == E.Phase.DYING and e.phase_t < 0.6)
	# squash and stretch: a spring on the frog's scale
	_squash_v += (-_squash * 320.0 - _squash_v * 16.0) * delta
	_squash += _squash_v * delta
	var sq := clampf(_squash, -0.35, 0.35)
	_frog.scale = Vector3(1.0 - sq * 0.55, 1.0 + sq, 1.0 - sq * 0.55)
	if e.phase == E.Phase.PLAY and e.hop_left == 0 and _frog_anim and not _frog_anim.is_playing():
		_play(_frog_anim, "idle", true)
	if e.phase == E.Phase.READY and _frog_anim and _frog_anim.current_animation in ["splat", "drown"]:
		_play(_frog_anim, "idle", true)
	for b in 5:
		_homes[b].visible = e.filled[b]
	_fly.visible = e.fly_bay >= 0
	if _fly.visible:
		_fly.position = cell(E.BAYS[e.fly_bay] + sin(_time * 2.3) * 0.12, 0, 0.35 + sin(_time * 6.0) * 0.08)
	_fx.fly_trail(_fly.visible, _fly.position + Vector3(0, 0.32, 0))
	_croc.visible = e.croc_bay >= 0
	if _croc.visible:
		_croc.position = cell(E.BAYS[e.croc_bay], 0, -0.35 + e.croc_rise * 0.35)
	_lady.visible = not e.lady.is_empty()
	if _lady.visible:
		if e.lady.get("on", false):
			_lady.position = _frog.position + Vector3(0, 0.25, 0.05)
			_lady.rotation.y = _frog.rotation.y
		else:
			var o: Dictionary = e.lanes[e.lady["row"]]["objs"][e.lady["obj"]]
			_lady.position = cell(e.obj_x(e.lady["row"], o, e.time) + o["len"] * 0.5, e.lady["row"], 0.25)
	# now and then a driver honks for nothing
	_honk_cool = maxf(0.0, _honk_cool - delta)
	_honk_t -= delta
	if _honk_t <= 0.0:
		_honk_t = randf_range(7.0, 15.0)
		var r := randi_range(7, 11)
		var i: int = randi() % (_objs[r] as Array).size()
		if (_objs[r][i] as Node3D).visible and absf((_objs[r][i] as Node3D).position.x) < 8.0:
			_honk(r, i, false)
	_place_camera(delta)


## The reflections of the town on the glossy paint and the water, taken once the light has settled.
func _add_probe() -> void:
	var probe := ReflectionProbe.new()
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	probe.size = Vector3(34, 12, 22)
	probe.position = Vector3(0, 3.0, 0.0)
	probe.origin_offset = Vector3(0, -1.5, 0)
	probe.box_projection = true
	probe.intensity = 0.5
	probe.max_distance = 40.0
	_stage.add_child(probe)


func _place_camera(delta: float) -> void:
	var e := game.engine
	var full := _full_dist()
	var frog := _frog.position if _frog else Vector3(0, 0, 6)
	# follow the frog up the board: lean towards it, a little closer than the whole board
	var want_t := Vector3(clampf(frog.x * 0.32, -2.4, 2.4), 0.0, lerpf(0.2, frog.z, 0.36))
	var want_d := full * 0.78
	var want_yaw := clampf(-frog.x * 0.012, -0.08, 0.08)
	var want_el := 51.0
	if e and e.phase == E.Phase.CLEARED:
		# all home: swoop low over the hedge to watch the fireworks, then rise
		var s := clampf(1.0 - e.phase_t / 3.0, 0.0, 1.0)
		want_t = Vector3(0, 1.5, -4.0)
		want_d = full * (0.78 + 0.12 * s)
		want_yaw = sin(s * PI) * 0.32
		want_el = 30.0
	elif e and e.phase == E.Phase.DYING:
		want_t = want_t.lerp(frog * Vector3(1, 0, 1), 0.25)
		want_d *= 0.94
	var k := 1.0 - exp(-delta * 2.6)
	_cam_target = _cam_target.lerp(want_t, k)
	_cam_dist = lerpf(_cam_dist, want_d, k)
	_cam_yaw = lerpf(_cam_yaw, want_yaw, k)
	_cam_el = lerpf(_cam_el, want_el, k)
	# a frog home: a quick punch in on its bay, easing back out
	_punch = maxf(0.0, _punch - delta / 1.0)
	var age := 1.0 - _punch
	var pk := (age / 0.1) if age < 0.1 else pow(_punch / 0.9, 2.0)
	pk = clampf(pk, 0.0, 1.0) if _punch > 0.0 else 0.0
	var t2 := _cam_target.lerp(_punch_at, 0.28 * pk)
	var d2 := _cam_dist * (1.0 - 0.13 * pk)
	# shake: trauma squared, smooth noise
	_trauma = maxf(0.0, _trauma - delta * 1.6)
	var amp := _trauma * _trauma * (0.35 if Settings.camera_shake else 0.0)
	var j := Vector3(sin(_time * 47.0) + sin(_time * 29.0) * 0.5, sin(_time * 53.0) * 0.6, cos(_time * 41.0)) * amp
	var el := deg_to_rad(_cam_el)
	var dir := Vector3(0, sin(el), cos(el)).rotated(Vector3.UP, _cam_yaw)
	camera.position = t2 + dir * d2 + j
	camera.look_at(t2 + j * 0.5, Vector3.UP)
	camera.fov = 40.0 - 1.5 * pk
