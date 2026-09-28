class_name PopBackdrop
extends Node3D
## The scenery behind the Pop Voyage arena: one landmark diorama per stage theme (0-7, see stages/voyage.pop).
## build(theme) loads art/backdrops/backdrop_<theme>.glb (tools/blender/popvoyage_backdrops.py), swaps the materials
## the Blender script marks by name for the game's shaders (water, wind-swayed foliage, twinkling and pulsing
## lights, the lighthouse beam, the aurora, clouds), adds a sky dome and the living things (birds, mist, petals,
## embers, smoke, snow) and animates the named nodes in _process: sails, the beam, boats, icebergs, the ferry and
## the wheel. The view owns the WorldEnvironment and the sun: it reads environment_for(theme) (or calls
## make_environment() and setup_sun() with that dictionary).
##
## Space: arena x 0..16, y 0..10 on z = 0, camera near (8, 5, 22), fov 35; the backdrop fills z +9 .. -1300.
## The foreground strip's top is exactly y = 0 (the floor). Everything runs on the node's own clock (fixed-step safe).

const GLB := "res://games/popvoyage/art/backdrops/backdrop_%d.glb"
const SH := "res://games/popvoyage/shaders/"
const DOME_CENTRE := Vector3(8.0, 5.0, 22.0)
const DOME_RADIUS := 1500.0
const WHEEL_SPEED := -0.07  ## the harbour wheel, rad/s

## Per theme: sky dome colours (the dome is also where the fog ends), the environment the view applies, and the
## water, wind and light settings of the backdrop's own shaders.
const THEMES := [
	{   # 0 Lighthouse Point: bright morning, sun low from the front left
		"name": "Lighthouse Point",
		"sky_top": Color("#3f8fe0"), "sky_mid": Color("#86bff0"), "sky_horizon": Color("#dbeef8"),
		"ground_horizon": Color("#a9cadb"), "ground_bottom": Color("#6f97ad"),
		"sun_color": Color("#fff0d8"), "sun_rotation": Vector3(-34, -62, 0), "sun_energy": 1.7,
		"sun_sky": Vector3(-0.75, 0.16, -0.64), "sun_disc": 0.0, "sun_glow": 0.4,
		"ambient_color": Color("#b4cce6"), "ambient_energy": 0.5,
		"fog_color": Color("#cfe4f0"), "fog_density": 0.003, "fog_sun_scatter": 0.15,
		"exposure": 1.0, "glow_intensity": 0.45, "glow_threshold": 1.2, "saturation": 1.18, "contrast": 1.06,
		"clouds": 0.32, "cloud_shade": Color("#b8c9df"), "stars": 0.0, "moon": 0.0,
		"water": [Color("#0d5f8e"), Color("#4f96c0"), Color("#2fb4b0"), Color("#eef8fc")], "wave": 0.14,
		"wind": 0.035, "night": false,
	},
	{   # 1 Windmill Meadow: soft noon, sun high
		"name": "Windmill Meadow",
		"sky_top": Color("#3d86d8"), "sky_mid": Color("#8fc3ee"), "sky_horizon": Color("#e4f1f7"),
		"ground_horizon": Color("#b9d2c9"), "ground_bottom": Color("#7c9c8a"),
		"sun_color": Color("#fff5e2"), "sun_rotation": Vector3(-52, -35, 0), "sun_energy": 1.8,
		"sun_sky": Vector3(-0.3, 0.8, -0.5), "sun_disc": 0.0, "sun_glow": 0.3,
		"ambient_color": Color("#b8cfe8"), "ambient_energy": 0.45,
		"fog_color": Color("#d6e8f0"), "fog_density": 0.0035, "fog_sun_scatter": 0.1,
		"exposure": 1.0, "glow_intensity": 0.4, "glow_threshold": 1.2, "saturation": 1.15, "contrast": 1.06,
		"clouds": 0.4, "cloud_shade": Color("#bfd0e4"), "stars": 0.0, "moon": 0.0,
		"water": [Color("#3d6f7e"), Color("#9cc4d2"), Color("#5f9a8f"), Color("#e8f4fb")], "wave": 0.03,
		"wind": 0.03, "night": false,
	},
	{   # 2 Sandstone Arch: hot afternoon, sun from the right
		"name": "Sandstone Arch",
		"sky_top": Color("#3279cc"), "sky_mid": Color("#7fb3e0"), "sky_horizon": Color("#f2dcbc"),
		"ground_horizon": Color("#e1c29a"), "ground_bottom": Color("#c49d72"),
		"sun_color": Color("#ffe4b8"), "sun_rotation": Vector3(-36, 48, 0), "sun_energy": 1.85,
		"sun_sky": Vector3(0.8, 0.3, -0.5), "sun_disc": 0.0, "sun_glow": 0.6,
		"ambient_color": Color("#d8c4b0"), "ambient_energy": 0.45,
		"fog_color": Color("#efd8b8"), "fog_density": 0.0025, "fog_sun_scatter": 0.25,
		"exposure": 1.0, "glow_intensity": 0.4, "glow_threshold": 1.2, "saturation": 1.05, "contrast": 1.05,
		"clouds": 0.12, "cloud_shade": Color("#e6d2c0"), "stars": 0.0, "moon": 0.0,
		"water": [], "wave": 0.0, "wind": 0.02, "night": false,
	},
	{   # 3 Bamboo Temple: misty morning, soft pink-gold light
		"name": "Bamboo Temple",
		"sky_top": Color("#8fb3d6"), "sky_mid": Color("#cfdcea"), "sky_horizon": Color("#f6e6e0"),
		"ground_horizon": Color("#dcd8d4"), "ground_bottom": Color("#b8c2b8"),
		"sun_color": Color("#ffe0c4"), "sun_rotation": Vector3(-38, -40, 0), "sun_energy": 1.55,
		"sun_sky": Vector3(-0.7, 0.12, -0.7), "sun_disc": 0.6, "sun_glow": 0.7,
		"ambient_color": Color("#c8c8dc"), "ambient_energy": 0.4,
		"fog_color": Color("#e8e0e0"), "fog_density": 0.0035, "fog_sun_scatter": 0.1,
		"exposure": 0.95, "glow_intensity": 0.5, "glow_threshold": 1.1, "saturation": 1.12, "contrast": 1.05,
		"clouds": 0.18, "cloud_shade": Color("#e0d6dc"), "stars": 0.0, "moon": 0.0,
		"water": [Color("#4f7a78"), Color("#b9ccc8"), Color("#79a79a"), Color("#f4f4f0")], "wave": 0.02,
		"wind": 0.028, "night": false,
	},
	{   # 4 Glacier Bay: crisp blue day
		"name": "Glacier Bay",
		"sky_top": Color("#1f68d0"), "sky_mid": Color("#6eaef0"), "sky_horizon": Color("#cfeaf8"),
		"ground_horizon": Color("#9fc7de"), "ground_bottom": Color("#5a8cae"),
		"sun_color": Color("#fff6e8"), "sun_rotation": Vector3(-30, 40, 0), "sun_energy": 1.35,
		"sun_sky": Vector3(0.7, 0.35, -0.6), "sun_disc": 0.0, "sun_glow": 0.35,
		"ambient_color": Color("#a8c8ec"), "ambient_energy": 0.55,
		"fog_color": Color("#cfe6f4"), "fog_density": 0.0022, "fog_sun_scatter": 0.1,
		"exposure": 0.9, "glow_intensity": 0.35, "glow_threshold": 1.3, "saturation": 1.12, "contrast": 1.06,
		"clouds": 0.14, "cloud_shade": Color("#c6d6ea"), "stars": 0.0, "moon": 0.0,
		"water": [Color("#0a4a70"), Color("#3f86b0"), Color("#1f9aa8"), Color("#f2fbff")], "wave": 0.1,
		"wind": 0.02, "night": false,
	},
	{   # 5 Ember Peak: dusk, the sun gone down behind the right-hand ridge, the volcano glowing
		"name": "Ember Peak",
		"sky_top": Color("#1d1638"), "sky_mid": Color("#6a2f5e"), "sky_horizon": Color("#f07a3e"),
		"ground_horizon": Color("#8a4040"), "ground_bottom": Color("#3a2030"),
		"sun_color": Color("#ff9a5c"), "sun_rotation": Vector3(-14, 118, 0), "sun_energy": 1.2,
		"sun_sky": Vector3(0.85, 0.04, -0.5), "sun_disc": 0.0, "sun_glow": 0.9,
		"ambient_color": Color("#8a6a9a"), "ambient_energy": 0.75,
		"fog_color": Color("#80485a"), "fog_density": 0.0065, "fog_sun_scatter": 0.35,
		"exposure": 1.05, "glow_intensity": 0.65, "glow_threshold": 1.1, "saturation": 1.05, "contrast": 1.05,
		"clouds": 0.3, "cloud_shade": Color("#5a3050"), "stars": 0.25, "moon": 0.0,
		"water": [], "wave": 0.0, "wind": 0.02, "night": false,
	},
	{   # 6 Harbour Lights: night, moonlight from the front left, the town lit up
		"name": "Harbour Lights",
		"sky_top": Color("#050a1e"), "sky_mid": Color("#101c44"), "sky_horizon": Color("#35386a"),
		"ground_horizon": Color("#1a2248"), "ground_bottom": Color("#0a1028"),
		"sun_color": Color("#a8baff"), "sun_rotation": Vector3(-38, -30, 0), "sun_energy": 0.5,
		"sun_sky": Vector3(-0.5, 0.5, -0.7), "sun_disc": 0.0, "sun_glow": 0.0,
		"ambient_color": Color("#3c4c86"), "ambient_energy": 0.65,
		"fog_color": Color("#1e2650"), "fog_density": 0.005, "fog_sun_scatter": 0.0,
		"exposure": 1.1, "glow_intensity": 0.9, "glow_threshold": 0.9, "saturation": 1.08, "contrast": 1.04,
		"clouds": 0.15, "cloud_shade": Color("#1a2040"), "stars": 0.55, "moon": 1.0,
		"moon_dir": Vector3(-0.45, 0.42, -0.79),
		"water": [Color("#0a1430"), Color("#1c2650"), Color("#10203a"), Color("#8090c0")], "wave": 0.05,
		"wind": 0.02, "night": true,
	},
	{   # 7 Aurora Fields: night under the aurora
		"name": "Aurora Fields",
		"sky_top": Color("#030716"), "sky_mid": Color("#0a1a38"), "sky_horizon": Color("#1b4058"),
		"ground_horizon": Color("#16304a"), "ground_bottom": Color("#0a1628"),
		"sun_color": Color("#a6c8ff"), "sun_rotation": Vector3(-36, 25, 0), "sun_energy": 0.55,
		"sun_sky": Vector3(0.5, 0.4, -0.7), "sun_disc": 0.0, "sun_glow": 0.0,
		"ambient_color": Color("#3e6a90"), "ambient_energy": 0.7,
		"fog_color": Color("#15324a"), "fog_density": 0.0035, "fog_sun_scatter": 0.0,
		"exposure": 1.1, "glow_intensity": 0.8, "glow_threshold": 0.9, "saturation": 1.1, "contrast": 1.04,
		"clouds": 0.0, "cloud_shade": Color("#101828"), "stars": 1.0, "moon": 0.0,
		"water": [], "wave": 0.0, "wind": 0.015, "night": true,
	},
]

var theme := 0
var _t := 0.0
var _spin: Array = []    ## [node, local axis, rad/s]
var _bob: Array = []     ## [node, rest transform, height, rate, phase, roll]
var _drift: Array = []   ## [node, speed, x min, x max]
var _birds: Array = []   ## [node, centre, radii, angular speed, phase, wingbeat rate, size]
var _ferry: Node3D
var _ferry_x := 0.0
var _wheel: Node3D
var _wheel_rest: Transform3D
var _gondolas: Array = []  ## [node, pin offset from the hub]
var _mats := {}
var _sky: ShaderMaterial


## The environment the view applies for a theme. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color,
## for a ProceduralSkyMaterial: ambient and reflections; the dome covers the background), sun_color (Color),
## sun_rotation (Vector3, degrees, for the DirectionalLight3D), sun_energy, ambient_color, ambient_energy,
## fog_color, fog_density (exponential fog), fog_sun_scatter, exposure, glow_intensity, glow_threshold, saturation,
## contrast, night (bool: lamps and windows are lit, keep the arena's own lights on).
func environment_for(t: int) -> Dictionary:
	var d: Dictionary = THEMES[clampi(t, 0, THEMES.size() - 1)]
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_rotation", "sun_energy",
			"ambient_color", "ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure",
			"glow_intensity", "glow_threshold", "saturation", "contrast", "night"]:
		out[k] = d[k]
	return out


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
	sun.directional_shadow_max_distance = 60.0


func build(t: int) -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	theme = clampi(t, 0, THEMES.size() - 1)
	_t = 0.0
	_spin.clear()
	_bob.clear()
	_drift.clear()
	_birds.clear()
	_mats.clear()
	_ferry = null
	_wheel = null
	_gondolas.clear()
	var d: Dictionary = THEMES[theme]
	_add_sky(d)
	var packed := load(GLB % theme) as PackedScene
	if packed == null:
		push_error("PopBackdrop: missing %s" % (GLB % theme))
		return
	var root := packed.instantiate() as Node3D
	root.name = "diorama"
	add_child(root)
	_dress(root, d)
	_collect(root)
	match theme:
		0:
			_add_birds(7, Vector3(-6, 15, -24), Vector3(16, 3, 8), Color("#f4f4f2"), Color("#3a3e46"), 0.55, 1.0)
			_add_birds(3, Vector3(34, 20, -40), Vector3(7, 2, 5), Color("#f4f4f2"), Color("#3a3e46"), 0.7, 1.4)
		1:
			_add_birds(5, Vector3(0, 16, -40), Vector3(20, 3, 10), Color("#4a4a52"), Color("#2a2a30"), 0.35, 0.8)
		2:
			_add_birds(3, Vector3(-16, 34, -60), Vector3(9, 1.5, 7), Color("#3a2e2a"), Color("#1e1816"), 1.4, 0.35)
			_add_birds(2, Vector3(40, 30, -80), Vector3(8, 1.2, 6), Color("#3a2e2a"), Color("#1e1816"), 1.2, 0.35)
		3:
			_add_mist([[-40.0, 5.0, 0.2], [-66.0, 9.0, 0.3], [-115.0, 14.0, 0.45]], Color("#f3ecee"))
			_add_petals()
			_add_birds(3, Vector3(-12, 18, -50), Vector3(10, 2, 6), Color("#f2f0ea"), Color("#303036"), 0.8, 0.8)
		4:
			_add_birds(4, Vector3(-4, 17, -30), Vector3(14, 3, 8), Color("#f6f6f4"), Color("#2e3238"), 0.6, 1.0)
			_add_mist([[-100.0, 5.0, 0.3]], Color("#e4f2fa"))
		5:
			_add_smoke()
			_add_embers()
			_add_mist([[-70.0, 5.0, 0.3], [-120.0, 8.0, 0.35]], Color("#8a4a50"))
		6:
			_ferry = find_child("ferry", true, false) as Node3D
			if _ferry:
				_ferry_x = _ferry.position.x
		7:
			_add_snow()
			_add_chimney_smoke()


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
	_sky = _shader("pop_sky")
	_sky.set_shader_parameter("top_col", d["sky_top"])
	_sky.set_shader_parameter("mid_col", d["sky_mid"])
	_sky.set_shader_parameter("horizon_col", d["sky_horizon"])
	_sky.set_shader_parameter("ground_col", d["fog_color"])
	_sky.set_shader_parameter("sun_dir", (d["sun_sky"] as Vector3).normalized())
	_sky.set_shader_parameter("sun_col", d["sun_color"])
	_sky.set_shader_parameter("sun_disc", d["sun_disc"])
	_sky.set_shader_parameter("sun_glow", d["sun_glow"])
	_sky.set_shader_parameter("cloud_amount", d["clouds"])
	_sky.set_shader_parameter("cloud_col", (d["sky_horizon"] as Color).lerp(Color.WHITE, 0.6))
	_sky.set_shader_parameter("cloud_shade", d["cloud_shade"])
	_sky.set_shader_parameter("stars", d["stars"])
	_sky.set_shader_parameter("moon", d["moon"])
	if d.has("moon_dir"):
		_sky.set_shader_parameter("moon_dir", (d["moon_dir"] as Vector3).normalized())
	dome.material_override = _sky
	add_child(dome)


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	return m


## Swaps the named materials for the backdrop shaders; far scenery neither casts shadows nor takes GI.
func _dress(root: Node3D, d: Dictionary) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		var near := nm.begins_with("fg") or nm.begins_with("lm") or nm.begins_with("boat") or nm.begins_with("buoy")
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if near else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			mi.set_surface_override_material(i, _material_for(mn, src, d))


func _material_for(mn: String, src: Material, d: Dictionary) -> Material:
	if _mats.has(mn):
		return _mats[mn]
	var m: Material = null
	var base := Color.WHITE
	if src is BaseMaterial3D:
		base = (src as BaseMaterial3D).albedo_color
	var night: bool = d["night"]
	if mn == "water":
		var w := _shader("pop_water")
		var wc: Array = d["water"]
		w.set_shader_parameter("deep_col", wc[0])
		w.set_shader_parameter("far_col", wc[1])
		w.set_shader_parameter("shallow_col", wc[2])
		w.set_shader_parameter("foam_col", wc[3])
		w.set_shader_parameter("sheen_col", d["sky_horizon"])
		w.set_shader_parameter("wave_height", d["wave"])
		w.set_shader_parameter("gloss", 0.04 if night else 0.08)
		w.set_shader_parameter("foam", 0.2 if night else 1.0)
		w.set_shader_parameter("ripple", 0.6 if theme == 1 or theme == 3 else 1.0)
		m = w
	elif mn.contains("sway"):
		var s := _shader("pop_sway")
		var amp: float = d["wind"]
		if mn.begins_with("bamboo"):
			amp *= 0.6
		elif mn.begins_with("blossom"):
			amp *= 0.5
		s.set_shader_parameter("amp", amp)
		s.set_shader_parameter("rough", 0.6 if mn.begins_with("bamboo") else 0.85)
		m = s
	elif mn == "cloud":
		var c := _shader("pop_cloud")
		c.set_shader_parameter("tint", Color.WHITE if not night else Color(0.4, 0.45, 0.6))
		c.set_shader_parameter("self_light", 0.35 if theme != 5 else 0.15)
		m = c
	elif mn == "beam_glow":
		var b := _shader("pop_beam")
		b.set_shader_parameter("color", base)
		b.set_shader_parameter("strength", 0.07)
		m = b
	elif mn == "aurora_glow":
		m = _shader("pop_aurora")
	elif mn == "reflect_glow" or mn == "spill_glow":
		var r := _shader("pop_reflect")
		r.set_shader_parameter("color", Color(1, 1, 1))
		if mn == "spill_glow":
			r.set_shader_parameter("calm", 1.0)
			r.set_shader_parameter("strength", 0.45)
		m = r
	elif mn.contains("glow"):
		var g := _shader("pop_glow")
		var e := 1.0
		if src is BaseMaterial3D:
			e = (src as BaseMaterial3D).emission_energy_multiplier
		g.set_shader_parameter("color", base)
		match mn:
			"window_glow", "coolwindow_glow":
				g.set_shader_parameter("energy", 2.6 if night else 1.1)
				g.set_shader_parameter("twinkle", 0.35 if night else 0.0)
				g.set_shader_parameter("variety", 0.6)
				g.set_shader_parameter("cell", 0.7)
			"lamp_glow":
				g.set_shader_parameter("energy", 2.2 if night else 1.6)
				g.set_shader_parameter("flicker", 0.2)
				g.set_shader_parameter("cell", 3.0)
			"lava_glow":
				g.set_shader_parameter("energy", 1.9)
				g.set_shader_parameter("pulse", 1.0)
				g.set_shader_parameter("flow", 1.0)
			"blink_glow":
				g.set_shader_parameter("energy", 5.0)
				g.set_shader_parameter("blink", 1.0)
				g.set_shader_parameter("cell", 20.0)
			"bulb_glow":
				g.set_shader_parameter("energy", 3.0)
				g.set_shader_parameter("variety", 0.3)
				g.set_shader_parameter("flicker", 0.1)
				g.set_shader_parameter("cell", 0.9)
			_:
				g.set_shader_parameter("energy", maxf(1.5, e * 0.6))
		m = g
	elif src is BaseMaterial3D:
		# the colour lives in the vertex colours (the importer does not always flag it)
		var sm := (src as BaseMaterial3D).duplicate() as BaseMaterial3D
		sm.vertex_color_use_as_albedo = true
		match mn:
			"ice":
				sm.roughness = 0.12
				sm.metallic_specular = 0.7
			"snow":
				sm.roughness = 0.55
				sm.rim_enabled = true
				sm.rim = 0.25
				sm.rim_tint = 0.8
			"glass":
				sm.roughness = 0.1
				sm.metallic_specular = 0.8
		m = sm
	_mats[mn] = m
	return m


## The animated nodes the Blender script names.
func _collect(root: Node3D) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 23000 + theme
	for n in root.find_children("*", "Node3D", true, false):
		var node := n as Node3D
		var nm := String(node.name)
		if nm == "beam":
			_spin.append([node, Vector3.UP, 0.55])
		elif nm.begins_with("sails_"):
			_spin.append([node, Vector3.BACK, -0.45 - 0.12 * rng.randf()])
		elif nm == "wheel":
			_wheel = node
			_wheel_rest = node.transform
		elif nm.begins_with("boat_") or nm.begins_with("buoy_") or nm == "ferry":
			_bob.append([node, node.transform, 0.12, 0.9 + 0.4 * rng.randf(), rng.randf() * TAU, 0.035])
		elif nm.begins_with("berg_"):
			_bob.append([node, node.transform, 0.18, 0.35 + 0.15 * rng.randf(), rng.randf() * TAU, 0.012])
		elif nm.begins_with("floe_"):
			_bob.append([node, node.transform, 0.06, 0.7 + 0.3 * rng.randf(), rng.randf() * TAU, 0.03])
		elif nm.begins_with("gondola_"):
			_gondolas.append([node, node.position])
		elif nm.begins_with("cloud_"):
			var z := node.position.z
			var span := 0.5606 * (22.0 - z) * 1.9 + 60.0
			_drift.append([node, 0.6 + 0.5 * rng.randf(), 8.0 - span, 8.0 + span])


func _add_birds(count: int, centre: Vector3, radii: Vector3, body: Color, tip: Color, size: float, rate: float) -> void:
	var mesh := _bird_mesh()
	var mat := _shader("pop_bird")
	mat.set_shader_parameter("color", body)
	mat.set_shader_parameter("tip", tip)
	mat.set_shader_parameter("rate", 7.0 * rate)
	for i in count:
		var b := MeshInstance3D.new()
		b.name = "bird_%d" % i
		b.mesh = mesh
		b.material_override = mat
		b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		b.set_instance_shader_parameter("phase", fmod(i * 0.37, 1.0))
		b.set_instance_shader_parameter("glide", 0.7 if rate < 0.5 else 0.0)
		add_child(b)
		var sp := (0.12 + 0.05 * fmod(i * 0.71, 1.0)) * (1.0 if i % 2 == 0 else -1.0)
		_birds.append([b, centre + Vector3(fmod(i * 3.7, 5.0) - 2.5, fmod(i * 1.3, 2.0), fmod(i * 2.1, 3.0) - 1.5),
				radii * (0.7 + 0.3 * fmod(i * 0.43, 1.0)), sp, i * 1.9, rate, size * (0.8 + 0.4 * fmod(i * 0.618, 1.0))])
	_place_birds()


func _bird_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := [
		# body
		[Vector3(0, 0, -0.35), Vector3(0.06, 0, 0.25), Vector3(-0.06, 0, 0.25)],
		[Vector3(0, 0.05, -0.2), Vector3(0.05, 0, 0.1), Vector3(-0.05, 0, 0.1)],
		# wings: inner and outer panels (the outer ones beat most)
		[Vector3(0.04, 0, -0.1), Vector3(0.35, 0.03, -0.05), Vector3(0.04, 0, 0.12)],
		[Vector3(0.35, 0.03, -0.05), Vector3(0.7, 0.0, 0.12), Vector3(0.3, 0.02, 0.1)],
		[Vector3(0.04, 0, 0.12), Vector3(0.35, 0.03, -0.05), Vector3(0.3, 0.02, 0.1)],
		[Vector3(-0.04, 0, -0.1), Vector3(-0.35, 0.03, -0.05), Vector3(-0.04, 0, 0.12)],
		[Vector3(-0.35, 0.03, -0.05), Vector3(-0.7, 0.0, 0.12), Vector3(-0.3, 0.02, 0.1)],
		[Vector3(-0.04, 0, 0.12), Vector3(-0.35, 0.03, -0.05), Vector3(-0.3, 0.02, 0.1)],
		# tail
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
		basis = basis * Basis(Vector3.FORWARD, -0.35 * signf(b[3]))  # banking into the turn
		node.transform = Transform3D(basis.scaled_local(Vector3.ONE * b[6]), p)


## Soft vertical banks of mist: [z, height, density] each, spanning the view.
func _add_mist(banks: Array, col: Color) -> void:
	for i in banks.size():
		var bk: Array = banks[i]
		var z: float = bk[0]
		var w := 0.5606 * (22.0 - z) * 2.0 * 1.6 + 30.0
		var q := QuadMesh.new()
		q.size = Vector2(w, bk[1] * 2.0)
		var mi := MeshInstance3D.new()
		mi.name = "mist_%d" % i
		mi.mesh = q
		mi.position = Vector3(8.0, bk[1] * 0.75 - 1.0, z)
		var m := _shader("pop_mist")
		m.set_shader_parameter("color", col)
		m.set_shader_parameter("density", bk[2])
		m.set_shader_parameter("speed", 0.004 + 0.003 * i)
		m.set_shader_parameter("soft", 2.0 + 2.0 * i)
		mi.material_override = m
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)


func _particles(name_: String, amount: int, life: float, pos: Vector3, box: Vector3, shape: int, emit: float,
		size: float) -> Array:
	var p := GPUParticles3D.new()
	p.name = name_
	p.amount = amount
	p.lifetime = life
	p.preprocess = life
	p.fixed_fps = 30
	p.use_fixed_seed = true
	p.seed = 23 + theme
	p.position = pos
	p.visibility_aabb = AABB(-box - Vector3(10, 30, 10), (box + Vector3(10, 30, 10)) * 2.0)
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = box
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	var m := _shader("pop_particle")
	m.set_shader_parameter("shape", shape)
	m.set_shader_parameter("emit", emit)
	q.material = m
	p.draw_pass_1 = q
	p.process_material = pm
	add_child(p)
	return [p, pm]


func _add_petals() -> void:
	var r := _particles("petals", 70, 9.0, Vector3(8, 13, -3), Vector3(20, 1, 6), 1, 1.1, 0.16)
	var pm: ParticleProcessMaterial = r[1]
	pm.gravity = Vector3(0.35, -0.55, 0.1)
	pm.initial_velocity_min = 0.1
	pm.initial_velocity_max = 0.4
	pm.angle_min = -180
	pm.angle_max = 180
	pm.angular_velocity_min = -90
	pm.angular_velocity_max = 90
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.6
	pm.turbulence_noise_scale = 3.0
	pm.color = Color("#ffc2d6")
	pm.hue_variation_min = -0.03
	pm.hue_variation_max = 0.03
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0))
	ramp.add_point(0.1, Color(1, 1, 1, 0.9))
	ramp.add_point(0.85, Color(1, 1, 1, 0.9))
	ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0))
	var gt := GradientTexture1D.new()
	gt.gradient = ramp
	pm.color_ramp = gt


func _add_embers() -> void:
	for side in [-1.0, 1.0]:
		var r := _particles("embers", 36, 5.0, Vector3(8.0 + side * 16.0, 0.0, -6.0), Vector3(8, 0.5, 5), 0, 3.0, 0.09)
		var pm: ParticleProcessMaterial = r[1]
		pm.gravity = Vector3(0.2, 0.9, 0)
		pm.initial_velocity_min = 0.3
		pm.initial_velocity_max = 1.2
		pm.direction = Vector3(0, 1, 0)
		pm.spread = 30
		pm.turbulence_enabled = true
		pm.turbulence_noise_strength = 1.5
		pm.color = Color("#ff8a3a")
		var ramp := Gradient.new()
		ramp.set_color(0, Color(1, 0.9, 0.5, 0))
		ramp.add_point(0.1, Color(1, 0.8, 0.4, 1))
		ramp.set_color(ramp.get_point_count() - 1, Color(0.8, 0.2, 0.1, 0))
		var gt := GradientTexture1D.new()
		gt.gradient = ramp
		pm.color_ramp = gt


func _add_smoke() -> void:
	var a := find_child("smoke_anchor", true, false) as Node3D
	if a == null:
		return
	var r := _particles("smoke", 64, 34.0, _local_pos(a), Vector3(3, 1, 3), 2, 1.0, 36.0)
	var pm: ParticleProcessMaterial = r[1]
	pm.gravity = Vector3(1.2, 1.3, 0)
	pm.initial_velocity_min = 0.6
	pm.initial_velocity_max = 1.4
	pm.direction = Vector3(0.2, 1, 0)
	pm.spread = 15
	pm.angle_min = -180
	pm.angle_max = 180
	pm.angular_velocity_min = -6
	pm.angular_velocity_max = 6
	pm.scale_min = 0.6
	pm.scale_max = 1.0
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.5))
	sc.add_point(Vector2(1, 2.2))
	var ct := CurveTexture.new()
	ct.curve = sc
	pm.scale_curve = ct
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1.0, 0.45, 0.2, 0.0))
	ramp.add_point(0.05, Color(0.8, 0.34, 0.22, 0.6))
	ramp.add_point(0.3, Color(0.32, 0.2, 0.26, 0.5))
	ramp.set_color(ramp.get_point_count() - 1, Color(0.3, 0.22, 0.3, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = ramp
	pm.color_ramp = gt
	(r[0] as GPUParticles3D).visibility_aabb = AABB(Vector3(-60, -10, -60), Vector3(160, 140, 120))


## A descendant's position in this node's space (works before the backdrop enters the tree).
func _local_pos(n: Node3D) -> Vector3:
	var tr := n.transform
	var p := n.get_parent()
	while p != self and p is Node3D:
		tr = (p as Node3D).transform * tr
		p = p.get_parent()
	return tr.origin


func _add_snow() -> void:
	var r := _particles("snow", 120, 10.0, Vector3(8, 16, -6), Vector3(24, 1, 10), 3, 1.2, 0.07)
	var pm: ParticleProcessMaterial = r[1]
	pm.gravity = Vector3(0.15, -0.6, 0)
	pm.initial_velocity_min = 0.0
	pm.initial_velocity_max = 0.3
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.5
	pm.color = Color(0.85, 0.92, 1.0, 0.8)


func _add_chimney_smoke() -> void:
	var i := 0
	for n in find_children("smoke_*", "Node3D", true, false):
		var a := n as Node3D
		var r := _particles("chimney_%d" % i, 8, 7.0, _local_pos(a), Vector3(0.1, 0.1, 0.1), 2, 0.6, 1.4)
		var pm: ParticleProcessMaterial = r[1]
		pm.gravity = Vector3(0.25, 0.5, 0)
		pm.initial_velocity_min = 0.2
		pm.initial_velocity_max = 0.4
		pm.direction = Vector3(0, 1, 0)
		pm.spread = 10
		var sc := Curve.new()
		sc.add_point(Vector2(0, 0.4))
		sc.add_point(Vector2(1, 2.0))
		var ct := CurveTexture.new()
		ct.curve = sc
		pm.scale_curve = ct
		var ramp := Gradient.new()
		ramp.set_color(0, Color(0.7, 0.75, 0.85, 0.0))
		ramp.add_point(0.15, Color(0.6, 0.66, 0.78, 0.35))
		ramp.set_color(ramp.get_point_count() - 1, Color(0.5, 0.55, 0.7, 0.0))
		var gt := GradientTexture1D.new()
		gt.gradient = ramp
		pm.color_ramp = gt
		i += 1


func _process(delta: float) -> void:
	_t += delta
	for s in _spin:
		(s[0] as Node3D).rotate_object_local(s[1], s[2] * delta)
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
	if _ferry:
		_ferry.position.x = _ferry_x + fmod(_t * 1.1 + 60.0, 160.0) - 80.0
	if _wheel:
		var a := _t * WHEEL_SPEED
		_wheel.transform = _wheel_rest * Transform3D(Basis(Vector3.BACK, a), Vector3.ZERO)
		var hub := _wheel_rest.origin
		for g in _gondolas:
			(g[0] as Node3D).position = hub + ((g[1] as Vector3) - hub).rotated(Vector3.BACK, a)
	_place_birds()
