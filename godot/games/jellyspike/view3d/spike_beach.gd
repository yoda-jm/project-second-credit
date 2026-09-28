class_name SpikeBeach
extends Node3D
## The tropical beach round the Jelly Spike court: one diorama (art/beach/beach_scene.glb, made by
## tools/blender/jellyspike_beach.py) lit three ways, one per variant, which the game cycles per match:
## 0 Noon (high sun, turquoise sea), 1 Golden Hour (the sun low over the sea, torches lit), 2 Moonlit Luau (night:
## lanterns, tiki torches and the bonfire). build(variant) loads the diorama, swaps the materials the Blender script
## marks by name for the beach shaders (sand grain, the sea and its breakers, the swash on the sand, the net, palms and
## flags in the breeze, clouds, lanterns, flames), adds the sky dome, seagulls, sparks and lights, and animates the
## spectators (crabs scuttle, gulls turn and hop; cheer(side) makes them celebrate), boats and clouds in _process.
## The view owns the WorldEnvironment and the sun: it reads environment_for(variant) (the same keys as PopBackdrop)
## and may call make_environment() and setup_sun() with that dictionary.
##
## Space: court x 0..16 on the sand (y = 0), play plane z = 0, the net at x = 8 (top 2.4, posts at z -4.4 and +2.0);
## camera near (8, 4.5, 20), fov 36. The area right behind the court is kept calm; the colour is at the sides.
## score_anchor() is where the blank scoreboard's face is (left of the court): the view may write the score there.
## Everything runs on the node's own clock (fixed-step safe).

const GLB := "res://games/jellyspike/art/beach/beach_scene.glb"
const SH := "res://games/jellyspike/shaders/"
const DOME_CENTRE := Vector3(8.0, 4.5, 20.0)
const DOME_RADIUS := 1500.0
const BOARD_SIZE := Vector2(2.8, 1.5)  ## the scoreboard's dark face, metres

const VARIANTS := [
	{   # 0 Noon: the sun high behind the camera on the left, a bright turquoise sea
		"name": "Noon",
		"sky_top": Color("#2a7fe0"), "sky_mid": Color("#79bdf2"), "sky_horizon": Color("#d8f1fb"),
		"ground_horizon": Color("#c4e2ea"), "ground_bottom": Color("#e6d4a8"),
		"sun_color": Color("#fff3dc"), "light_from": Vector3(-0.45, 0.78, 0.45), "sun_energy": 1.85,
		"sun_sky": Vector3(-0.4, 0.8, 0.45), "sun_disc": 0.0, "sun_glow": 0.3,
		"ambient_color": Color("#b8d4ee"), "ambient_energy": 0.5,
		"fog_color": Color("#cfeaf6"), "fog_density": 0.0022, "fog_sun_scatter": 0.1,
		"exposure": 1.0, "glow_intensity": 0.4, "glow_threshold": 1.25, "saturation": 1.15, "contrast": 1.05,
		"clouds": 0.22, "cloud_shade": Color("#b9cde4"), "stars": 0.0, "moon": 0.0,
		"water": [Color("#0a6aa6"), Color("#5aa8d4"), Color("#34d0c4"), Color("#e8d4a4"), Color("#f6fcff")],
		"wave": 0.12, "wind": 0.03, "lanterns": 0.0, "fire": false, "night": false,
	},
	{   # 1 Golden Hour: the sun low over the sea on the right, warm side light, the torches just lit
		"name": "Golden Hour",
		"sky_top": Color("#2f4a92"), "sky_mid": Color("#b77a9a"), "sky_horizon": Color("#ffbf72"),
		"ground_horizon": Color("#e0a27a"), "ground_bottom": Color("#9a6a5a"),
		"sun_color": Color("#ffb46e"), "light_from": Vector3(0.86, 0.26, -0.05), "sun_energy": 1.55,
		"sun_sky": Vector3(0.28, 0.065, -0.96), "sun_disc": 1.0, "sun_glow": 0.95,
		"ambient_color": Color("#b890a8"), "ambient_energy": 0.7,
		"fog_color": Color("#eaa47e"), "fog_density": 0.0035, "fog_sun_scatter": 0.3,
		"exposure": 1.0, "glow_intensity": 0.6, "glow_threshold": 1.1, "saturation": 1.12, "contrast": 1.05,
		"clouds": 0.3, "cloud_shade": Color("#9a6a8a"), "stars": 0.0, "moon": 0.0,
		"water": [Color("#1d4f7c"), Color("#c89088"), Color("#3fa8a8"), Color("#c8a07a"), Color("#fff0dc")],
		"wave": 0.1, "wind": 0.025, "lanterns": 1.4, "fire": true, "night": false,
	},
	{   # 2 Moonlit Luau: night; moonlight from behind the camera, lanterns, torches and the bonfire
		"name": "Moonlit Luau",
		"sky_top": Color("#040a20"), "sky_mid": Color("#0d1c48"), "sky_horizon": Color("#2c3c74"),
		"ground_horizon": Color("#1a2450"), "ground_bottom": Color("#10142a"),
		"sun_color": Color("#a4b8ff"), "light_from": Vector3(-0.35, 0.6, 0.72), "sun_energy": 0.4,
		"sun_sky": Vector3(-0.3, 0.6, 0.7), "sun_disc": 0.0, "sun_glow": 0.0,
		"ambient_color": Color("#3a4c8c"), "ambient_energy": 0.75,
		"fog_color": Color("#18244e"), "fog_density": 0.0035, "fog_sun_scatter": 0.0,
		"exposure": 1.1, "glow_intensity": 0.85, "glow_threshold": 0.95, "saturation": 1.08, "contrast": 1.04,
		"clouds": 0.12, "cloud_shade": Color("#161c38"), "stars": 1.0, "moon": 1.0,
		"moon_dir": Vector3(-0.3, 0.2, -0.93),
		"water": [Color("#061430"), Color("#1c2a5a"), Color("#0e4458"), Color("#4a4a62"), Color("#9eb4e0")],
		"wave": 0.08, "wind": 0.02, "lanterns": 3.2, "fire": true, "night": true,
	},
]

var variant := 0
var _t := 0.0
var _bob: Array = []      ## [node, rest transform, height, rate, phase, roll]
var _drift: Array = []    ## [node, speed, x min, x max]
var _birds: Array = []    ## [node, centre, radii, angular speed, phase, wingbeat rate, size]
var _crabs: Array = []    ## [node, rest transform, phase, range]
var _gulls: Array = []    ## [node, rest transform, phase]
var _lights: Array = []   ## [OmniLight3D, base energy, phase]
var _cheer_t := -10.0
var _cheer_side := 0
var _mats := {}
var _board := Transform3D()


## The environment the view applies for a variant. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color,
## for a ProceduralSkyMaterial: ambient and reflections; the dome covers the background), sun_color (Color),
## sun_rotation (Vector3, degrees, for the DirectionalLight3D), sun_energy, ambient_color, ambient_energy,
## fog_color, fog_density (exponential fog), fog_sun_scatter, exposure, glow_intensity, glow_threshold, saturation,
## contrast, night (bool: keep the court's own lights on), plus name (String).
func environment_for(v: int) -> Dictionary:
	var d: Dictionary = VARIANTS[clampi(v, 0, VARIANTS.size() - 1)]
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_energy",
			"ambient_color", "ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure",
			"glow_intensity", "glow_threshold", "saturation", "contrast", "night", "name"]:
		out[k] = d[k]
	# the light travels away from light_from
	var l := (d["light_from"] as Vector3).normalized()
	out["sun_rotation"] = Vector3(rad_to_deg(asin(-l.y)), rad_to_deg(atan2(l.x, l.z)), 0.0)
	return out


static func variant_count() -> int:
	return VARIANTS.size()


## A ready Environment from environment_for()'s dictionary (the view may use it as is or copy the values).
static func make_environment(d: Dictionary) -> Environment:
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = d["sky_top"]
	sm.sky_horizon_color = d["sky_horizon"]
	sm.ground_horizon_color = d["ground_horizon"]
	sm.ground_bottom_color = d["ground_bottom"]
	sm.sun_angle_max = 20.0
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = d["ambient_color"]
	env.ambient_light_energy = d["ambient_energy"]
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = d["exposure"]
	env.tonemap_white = 6.0
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = d["fog_color"]
	env.fog_density = d["fog_density"]
	env.fog_sun_scatter = d["fog_sun_scatter"]
	env.fog_sky_affect = 0.0
	env.glow_enabled = true
	env.glow_intensity = d["glow_intensity"]
	env.glow_hdr_threshold = d["glow_threshold"]
	env.glow_bloom = 0.03
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.8)
	env.set_glow_level(4, 0.5)
	env.adjustment_enabled = true
	env.adjustment_saturation = d["saturation"]
	env.adjustment_contrast = d["contrast"]
	return env


static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 55.0


## The scoreboard's blank face in this node's space: origin at its centre, basis x along the board, -z into it
## (write text facing +z). The face is BOARD_SIZE metres; it is split in two halves by a thin line at the centre.
func score_anchor() -> Transform3D:
	return _board


## The spectators celebrate a point for a side (crabs hop, gulls flap up).
func cheer(side: int) -> void:
	_cheer_t = _t
	_cheer_side = side


func build(v: int) -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	variant = clampi(v, 0, VARIANTS.size() - 1)
	_t = 0.0
	_bob.clear()
	_drift.clear()
	_birds.clear()
	_crabs.clear()
	_gulls.clear()
	_lights.clear()
	_mats.clear()
	var d: Dictionary = VARIANTS[variant]
	_add_sky(d)
	var packed := load(GLB) as PackedScene
	if packed == null:
		push_error("SpikeBeach: missing %s" % GLB)
		return
	var root := packed.instantiate() as Node3D
	root.name = "diorama"
	add_child(root)
	_dress(root, d)
	_collect(root, d)
	var night: bool = d["night"]
	var gull_body := Color("#f4f4f2") if not night else Color("#8a92b0")
	var gull_tip := Color("#3a3e46") if not night else Color("#1a1e2a")
	if variant != 2:
		_add_birds(3, Vector3(-9, 10.5, -16), Vector3(6, 1.5, 4), gull_body, gull_tip, 0.5, 1.0)
		_add_birds(3, Vector3(26, 11.5, -20), Vector3(6, 1.5, 4), gull_body, gull_tip, 0.5, 1.0)
		_add_birds(4, Vector3(60, 22, -120), Vector3(18, 3, 12), gull_body, gull_tip, 0.9, 0.8)
	if d["fire"]:
		_add_sparks()


func _add_sky(d: Dictionary) -> void:
	var dome := MeshInstance3D.new()
	dome.name = "sky"
	var m := SphereMesh.new()
	m.radius = DOME_RADIUS
	m.height = DOME_RADIUS * 2.0
	m.radial_segments = 48
	m.rings = 24
	dome.mesh = m
	dome.position = DOME_CENTRE
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dome.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	var sky := _shader("beach_sky")
	sky.set_shader_parameter("top_col", d["sky_top"])
	sky.set_shader_parameter("mid_col", d["sky_mid"])
	sky.set_shader_parameter("horizon_col", d["sky_horizon"])
	sky.set_shader_parameter("ground_col", d["fog_color"])
	sky.set_shader_parameter("sun_dir", (d["sun_sky"] as Vector3).normalized())
	sky.set_shader_parameter("sun_col", d["sun_color"])
	sky.set_shader_parameter("sun_disc", d["sun_disc"])
	sky.set_shader_parameter("sun_size", 0.05)
	sky.set_shader_parameter("sun_glow", d["sun_glow"])
	sky.set_shader_parameter("cloud_amount", d["clouds"])
	sky.set_shader_parameter("cloud_col", (d["sky_horizon"] as Color).lerp(Color.WHITE, 0.6))
	sky.set_shader_parameter("cloud_shade", d["cloud_shade"])
	sky.set_shader_parameter("stars", d["stars"])
	sky.set_shader_parameter("moon", d["moon"])
	if d.has("moon_dir"):
		sky.set_shader_parameter("moon_dir", (d["moon_dir"] as Vector3).normalized())
	dome.material_override = sky
	add_child(dome)


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	return m


## Swaps the named materials for the beach shaders; only the near props cast shadows.
func _dress(root: Node3D, d: Dictionary) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		var casts := nm.begins_with("near_") and not nm in ["near_sand", "near_swash", "near_prints", "near_court",
				"near_netmesh"]
		casts = casts or nm.begins_with("crab_") or nm.begins_with("gull_")
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if casts else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			mi.set_surface_override_material(i, _material_for(mn, src, d))


func _material_for(mn: String, src: Material, d: Dictionary) -> Material:
	if _mats.has(mn):
		return _mats[mn]
	var m: Material = null
	var night: bool = d["night"]
	var wc: Array = d["water"]
	match mn:
		"sand":
			var s := _shader("beach_sand")
			s.set_shader_parameter("sparkle", 1.0 if variant == 0 else (0.5 if variant == 1 else 0.0))
			s.set_shader_parameter("tint", Color.WHITE if not night else Color(0.8, 0.84, 1.0))
			m = s
		"sea":
			var w := _shader("beach_sea")
			w.set_shader_parameter("deep_col", wc[0])
			w.set_shader_parameter("far_col", wc[1])
			w.set_shader_parameter("shallow_col", wc[2])
			w.set_shader_parameter("sand_col", wc[3])
			w.set_shader_parameter("foam_col", wc[4])
			w.set_shader_parameter("sheen_col", d["sky_horizon"])
			w.set_shader_parameter("wave_height", d["wave"])
			w.set_shader_parameter("gloss", 0.04 if night else 0.06)
			w.set_shader_parameter("foam", 0.55 if night else 1.0)
			if variant == 1:
				w.set_shader_parameter("glint_dir", (d["sun_sky"] as Vector3).normalized())
				w.set_shader_parameter("glint_col", Color("#ffc47a"))
				w.set_shader_parameter("glint", 1.0)
			elif d.has("moon_dir"):
				w.set_shader_parameter("glint_dir", (d["moon_dir"] as Vector3).normalized())
				w.set_shader_parameter("glint_col", Color("#c8d4ff"))
				w.set_shader_parameter("glint", 0.7)
			m = w
		"swash":
			var s := _shader("beach_swash")
			s.set_shader_parameter("water_col", (wc[2] as Color).lerp(wc[4], 0.25))
			s.set_shader_parameter("foam_col", wc[4])
			s.set_shader_parameter("wet_col", (wc[3] as Color) * 0.62)
			s.set_shader_parameter("foam", 0.6 if night else 1.0)
			m = s
		"net":
			var s := _shader("beach_net")
			s.set_shader_parameter("cord", Color("#1c2230") if not night else Color("#2a3048"))
			m = s
		"cloud":
			var c := _shader("beach_cloud")
			c.set_shader_parameter("tint", Color.WHITE if not night else Color(0.5, 0.56, 0.78))
			c.set_shader_parameter("self_light", 0.3 if variant == 0 else (0.15 if variant == 1 else 0.22))
			m = c
		"palm_sway", "foliage_sway", "flag_sway", "bunting_sway":
			var s := _shader("beach_sway")
			var wind: float = d["wind"]
			s.set_shader_parameter("kind", {"palm_sway": 1, "foliage_sway": 0, "flag_sway": 2, "bunting_sway": 3}[mn])
			s.set_shader_parameter("amp", wind * (0.6 if mn == "foliage_sway" else 1.0))
			s.set_shader_parameter("rough", 0.75)
			s.set_shader_parameter("translucency", 0.3 if mn == "palm_sway" else 0.2)
			m = s
		"lantern_glow", "bulb_glow":
			var g := _shader("beach_glow")
			g.set_shader_parameter("energy", d["lanterns"])
			g.set_shader_parameter("flicker", 0.12)
			m = g
		"ember_glow":
			if d["fire"]:
				var g := _shader("beach_glow")
				g.set_shader_parameter("energy", 2.5 if night else 1.6)
				g.set_shader_parameter("flicker", 0.3)
				g.set_shader_parameter("pulse", 1.0)
				g.set_shader_parameter("cell", 0.2)
				m = g
			else:
				var ash := StandardMaterial3D.new()
				ash.albedo_color = Color("#5a5450")
				ash.roughness = 1.0
				m = ash
		"fire_glow":
			var f := _shader("beach_fire")
			f.set_shader_parameter("energy", 3.2 if night else 2.2)
			m = f
		_:
			if src is BaseMaterial3D:
				# the colour lives in the vertex colours (the importer does not always flag it)
				var sm := (src as BaseMaterial3D).duplicate() as BaseMaterial3D
				sm.vertex_color_use_as_albedo = true
				match mn:
					"critter":
						sm.roughness = 0.5
						sm.rim_enabled = true
						sm.rim = 0.2
					"board":
						sm.roughness = 0.95
					"metal":
						sm.metallic = 0.5
						sm.roughness = 0.35
				m = sm
			else:
				m = src
	_mats[mn] = m
	return m


## A descendant's transform in this node's space (works before the beach enters the tree).
func _local_xform(n: Node3D) -> Transform3D:
	var tr := n.transform
	var p := n.get_parent()
	while p != self and p is Node3D:
		tr = (p as Node3D).transform * tr
		p = p.get_parent()
	return tr


## The animated nodes, lights and anchors the Blender script names.
func _collect(root: Node3D, d: Dictionary) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 24000 + variant
	var fire: bool = d["fire"]
	var night: bool = d["night"]
	for n in root.find_children("*", "Node3D", true, false):
		var node := n as Node3D
		var nm := String(node.name)
		if nm.begins_with("boat_"):
			_bob.append([node, node.transform, 0.14, 0.8 + 0.4 * rng.randf(), rng.randf() * TAU, 0.04])
		elif nm.begins_with("cloud_"):
			var z := node.position.z
			var span := 0.578 * (20.0 - z) * 1.9 + 60.0
			_drift.append([node, 0.5 + 0.5 * rng.randf(), 8.0 - span, 8.0 + span])
		elif nm.begins_with("crab_"):
			_crabs.append([node, node.transform, rng.randf() * TAU, 0.5 + 0.4 * rng.randf()])
		elif nm.begins_with("gull_"):
			_gulls.append([node, node.transform, rng.randf() * TAU])
		elif nm.begins_with("flame_") or nm == "bonfire_flame":
			node.visible = fire
		elif nm == "score_board":
			_board = _local_xform(node)
		elif nm.begins_with("light_") and fire:
			var p := _local_xform(node).origin
			if nm.begins_with("light_torch_"):
				_add_light(p, Color("#ffa24a"), 2.2 if night else 1.2, 9.0 if night else 6.0)
			elif nm == "light_fire":
				_add_light(p, Color("#ff8a3a"), 4.0 if night else 2.0, 12.0 if night else 8.0)
			elif nm.begins_with("light_lantern_") and night:
				_add_light(p, Color("#ffc47a"), 1.2, 6.0)


func _add_light(p: Vector3, col: Color, energy: float, rng_: float) -> void:
	var l := OmniLight3D.new()
	l.position = p
	l.light_color = col
	l.light_energy = energy
	l.omni_range = rng_
	l.omni_attenuation = 1.4
	l.shadow_enabled = false
	add_child(l)
	_lights.append([l, energy, float(_lights.size()) * 1.7])


func _add_birds(count: int, centre: Vector3, radii: Vector3, body: Color, tip: Color, size: float, rate: float) -> void:
	var mesh := _bird_mesh()
	var mat := _shader("beach_bird")
	mat.set_shader_parameter("color", body)
	mat.set_shader_parameter("tip", tip)
	mat.set_shader_parameter("rate", 7.0 * rate)
	for i in count:
		var b := MeshInstance3D.new()
		b.name = "bird_%d" % _birds.size()
		b.mesh = mesh
		b.material_override = mat
		b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		b.set_instance_shader_parameter("phase", fmod(i * 0.37, 1.0))
		b.set_instance_shader_parameter("glide", 0.6 if i % 2 == 0 else 0.0)
		add_child(b)
		var sp := (0.14 + 0.05 * fmod(i * 0.71, 1.0)) * (1.0 if i % 2 == 0 else -1.0)
		_birds.append([b, centre + Vector3(fmod(i * 3.7, 5.0) - 2.5, fmod(i * 1.3, 2.0), fmod(i * 2.1, 3.0) - 1.5),
				radii * (0.7 + 0.3 * fmod(i * 0.43, 1.0)), sp, i * 1.9, rate, size * (0.8 + 0.4 * fmod(i * 0.618, 1.0))])
	_place_birds()


func _bird_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := [
		[Vector3(0, 0, -0.35), Vector3(0.06, 0, 0.25), Vector3(-0.06, 0, 0.25)],
		[Vector3(0, 0.05, -0.2), Vector3(0.05, 0, 0.1), Vector3(-0.05, 0, 0.1)],
		[Vector3(0.04, 0, -0.1), Vector3(0.35, 0.03, -0.05), Vector3(0.04, 0, 0.12)],
		[Vector3(0.35, 0.03, -0.05), Vector3(0.7, 0.0, 0.12), Vector3(0.3, 0.02, 0.1)],
		[Vector3(0.04, 0, 0.12), Vector3(0.35, 0.03, -0.05), Vector3(0.3, 0.02, 0.1)],
		[Vector3(-0.04, 0, -0.1), Vector3(-0.35, 0.03, -0.05), Vector3(-0.04, 0, 0.12)],
		[Vector3(-0.35, 0.03, -0.05), Vector3(-0.7, 0.0, 0.12), Vector3(-0.3, 0.02, 0.1)],
		[Vector3(-0.04, 0, 0.12), Vector3(-0.35, 0.03, -0.05), Vector3(-0.3, 0.02, 0.1)],
		[Vector3(0, 0, 0.2), Vector3(0.1, 0, 0.38), Vector3(-0.1, 0, 0.38)],
	]
	for tri in pts:
		for p in tri:
			st.set_normal(Vector3.UP)
			st.add_vertex(p * 2.0)
	return st.commit()


func _place_birds() -> void:
	for b in _birds:
		var node: Node3D = b[0]
		var c: Vector3 = b[1]
		var r: Vector3 = b[2]
		var a: float = _t * b[3] + b[4]
		var p := c + Vector3(cos(a) * r.x, sin(a * 2.3 + b[4]) * r.y * 0.3, sin(a) * r.z)
		var ahead := c + Vector3(cos(a + signf(b[3]) * 0.05) * r.x, p.y - c.y, sin(a + signf(b[3]) * 0.05) * r.z)
		var basis := Basis.looking_at(ahead - p, Vector3.UP) if ahead.distance_to(p) > 0.001 else Basis()
		basis = basis * Basis(Vector3.FORWARD, -0.35 * signf(b[3]))
		node.transform = Transform3D(basis.scaled_local(Vector3.ONE * b[6]), p)


func _add_sparks() -> void:
	var a := find_child("smoke_fire", true, false) as Node3D
	if a == null:
		return
	var p := GPUParticles3D.new()
	p.name = "sparks"
	p.amount = 40
	p.lifetime = 2.2
	p.preprocess = 2.2
	p.fixed_fps = 30
	p.use_fixed_seed = true
	p.seed = 24 + variant
	p.position = _local_xform(a).origin
	p.visibility_aabb = AABB(Vector3(-4, -2, -4), Vector3(8, 10, 8))
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.3, 0.1, 0.25)
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 20
	pm.initial_velocity_min = 0.6
	pm.initial_velocity_max = 1.6
	pm.gravity = Vector3(0.25, 0.7, 0)
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 1.6
	pm.turbulence_noise_scale = 2.0
	pm.scale_min = 0.5
	pm.scale_max = 1.0
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 0.9, 0.5, 0))
	ramp.add_point(0.08, Color(1, 0.75, 0.3, 1))
	ramp.set_color(ramp.get_point_count() - 1, Color(0.9, 0.25, 0.05, 0))
	var gt := GradientTexture1D.new()
	gt.gradient = ramp
	pm.color_ramp = gt
	var q := QuadMesh.new()
	q.size = Vector2(0.06, 0.06)
	var m := _shader("beach_particle")
	m.set_shader_parameter("shape", 0)
	m.set_shader_parameter("emit", 4.0)
	q.material = m
	p.draw_pass_1 = q
	p.process_material = pm
	add_child(p)


func _process(delta: float) -> void:
	_t += delta
	for b in _bob:
		var node: Node3D = b[0]
		var rest: Transform3D = b[1]
		var ph: float = _t * b[3] + b[4]
		var tr := rest
		tr.origin.y += sin(ph) * b[2]
		tr.basis = rest.basis * Basis(Vector3.BACK, sin(ph * 0.8 + 1.0) * b[5]) * Basis(Vector3.RIGHT, sin(ph * 0.6) * b[5] * 0.6)
		node.transform = tr
	for c in _drift:
		var node: Node3D = c[0]
		node.position.x += c[1] * delta
		if node.position.x > c[3]:
			node.position.x = c[2]
	var ch := _t - _cheer_t  # seconds since the last cheer
	for c in _crabs:
		var node: Node3D = c[0]
		var rest: Transform3D = c[1]
		var ph: float = c[2]
		# crabs walk sideways (their local z), in bursts, pausing between
		var cyc := _t * 0.35 + ph
		var walk := sin(cyc) + 0.3 * sin(cyc * 2.7)
		var side := rest.basis.z.normalized() * walk * float(c[3])
		var scut := absf(cos(cyc)) * 0.012 * absf(sin(_t * 26.0 + ph))
		var hop := 0.0
		if ch >= 0.0 and ch < 1.4:
			hop = absf(sin(ch * 9.0)) * 0.14 * (1.0 - ch / 1.4)
		var tr := rest
		tr.origin += side + Vector3(0, scut + hop, 0)
		tr.basis = rest.basis * Basis(Vector3.RIGHT, sin(_t * 1.3 + ph) * 0.06)
		node.transform = tr
	for g in _gulls:
		var node: Node3D = g[0]
		var rest: Transform3D = g[1]
		var ph: float = g[2]
		# every few seconds a gull looks about (a quick turn) and sometimes hops
		var slot := floorf(_t / 2.6 + ph)
		var look := (fmod(slot * 0.618 + ph, 1.0) - 0.5) * 1.4
		var k := smoothstep(0.0, 0.15, fmod(_t / 2.6 + ph, 1.0))
		var prev := (fmod((slot - 1.0) * 0.618 + ph, 1.0) - 0.5) * 1.4
		var yaw := lerpf(prev, look, k)
		var lift := 0.0
		if ch >= 0.0 and ch < 1.2:
			lift = sin(ch / 1.2 * PI) * 0.35
		elif fmod(slot, 3.0) == 0.0:
			lift = maxf(0.0, sin(fmod(_t / 2.6 + ph, 1.0) * PI * 4.0)) * 0.05
		var tr := rest
		tr.basis = Basis(Vector3.UP, yaw) * rest.basis
		tr.origin.y += lift
		node.transform = tr
	for l in _lights:
		var light: OmniLight3D = l[0]
		light.light_energy = l[1] * (1.0 + 0.12 * sin(_t * 11.0 + l[2]) + 0.08 * sin(_t * 17.3 + l[2] * 2.0))
	_place_birds()
