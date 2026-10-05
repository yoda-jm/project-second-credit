class_name RidgeBackdrop
extends Node3D
## The landscapes behind the Ridgefire field, one per theme: 0 Mesa Dusk, 1 Alpine Front, 2 Moonfall, 3 Ember Isle,
## 4 Frozen Wastes. build(theme) loads art/backdrops/backdrop_<theme>.glb (tools/blender/ridgefire_backdrops.py),
## swaps the materials the Blender script marks by name for the game's shaders (the land with its baked long shadows
## and aerial haze, water, the frozen sea, lava, a waterfall, mist, lit windows, beacons, the glass of domes), adds the
## sky dome (sunset glow, clouds, stars, the planet, the aurora, the ash cloud), the omni lights the script marks with
## empties, and what rises: the volcano's plume and embers, steam, blowing snow. It animates what moves (a train over
## the trestle, gliding hawks, a cable car, a rover and a lander, a radar, wind wheels) and the volcano's lightning.
## Everything runs on the node's own clock in _process (fixed-step safe, deterministic: seeded per theme).
##
## The game reacts through flash(pos, energy) (an explosion at pos: a brief light there and a glow in the sky behind
## it) and shake(amount) (a big blast: the lights of the base or the station flicker, the plants quiver).
## The view owns the WorldEnvironment and the sun: it reads environment_for(theme) (PopBackdrop's keys, plus
## `terrain`: the colours for its slab) and may call make_environment() and setup_sun() with that dictionary.
##
## Space: the field is x 0..96 on z = 0 (the slab z -5..+3, heights 0..40), the camera near (48, 26, 72), fov 38.
## Camera3D.far must reach the sky dome: 1300 or more. The scenery fills z -6 .. -1000.

const GLB := "res://games/ridgefire/art/backdrops/backdrop_%d.glb"
const SH := "res://games/ridgefire/shaders/"
const CAMERA := Vector3(48.0, 26.0, 72.0)
const DOME_RADIUS := 1150.0
const LIGHTS := 3   ## the explosions' flash lights (a ring)

## Per theme: the environment the view applies (sun_dir points towards the light: it gives sun_rotation and the
## baked shadows agree with it), the colours of the field's slab, the sky shader's settings, the haze of the land
## (it should end in the sky's horizon colour), the water, and what moves.
const THEMES := [
	{   # 0 Mesa Dusk: the low sun from the right behind the viewer sets the red rock aglow; the pink belt of evening
		"name": "Mesa Dusk",
		"sky_top": Color("#36477e"), "sky_horizon": Color("#eaa286"), "ground_horizon": Color("#b0704e"),
		"ground_bottom": Color("#4a2a1e"),
		"sun_dir": Vector3(0.9, 0.23, 0.36), "sun_color": Color("#ffa86c"), "sun_energy": 3.3,
		"ambient_color": Color("#7a6aa0"), "ambient_energy": 0.36,
		"fog_color": Color("#d49c8a"), "fog_density": 0.0003, "fog_sun_scatter": 0.1,
		"exposure": 1.0, "glow_intensity": 0.55, "glow_threshold": 1.2, "saturation": 1.08, "contrast": 1.05,
		"night": false,
		"terrain": {"top": Color("#c98a5a"), "soil": Color("#a4532f"), "strata": Color("#e2b48a"), "deep": Color("#5a2a1c")},
		"sky": {"top_col": Color("#1e2866"), "mid_col": Color("#6a5a9e"), "horizon_col": Color("#f4a07e"),
				"below_col": Color("#6a3a2c"), "mid_height": 0.24,
				"glow_dir": Vector3(1.0, 0.0, -0.45), "glow_col": Color("#ffb05a"), "glow": 1.0, "glow_spread": 2.0,
				"glow_rise": 6.0, "belt_col": Color("#ec8ea8"), "belt": 0.55,
				"stars": 0.3, "clouds": 0.5, "cloud_streak": 1.0, "cloud_scale": 0.8,
				"cloud_col": Color("#ffc8a0"), "cloud_shade": Color("#6e5488"), "cloud_lit": Color("#ff8a50"),
				"cloud_light": Vector3(1.0, 0.1, -0.3)},
		"haze": {"haze_col": Color("#c08aa0"), "haze_sun_col": Color("#f6aa80"), "haze_start": 160.0,
				"haze_scale": 700.0, "haze_max": 0.58, "haze_sun_pow": 3.0, "sun_dir": Vector3(1.0, 0.05, -0.3)},
		"water": {},
		"train": {"dist": 450.0, "speed": 13.0, "pause": 20.0},
	},
	{   # 1 Alpine Front: a bright late morning, the sun high on the left behind the viewer, cumulus over the peaks
		"name": "Alpine Front",
		"sky_top": Color("#2a5cb0"), "sky_horizon": Color("#c4dcf0"), "ground_horizon": Color("#6a7a5a"),
		"ground_bottom": Color("#2a3220"),
		"sun_dir": Vector3(-0.5, 0.62, 0.6), "sun_color": Color("#fff0da"), "sun_energy": 2.2,
		"ambient_color": Color("#8ab0e0"), "ambient_energy": 0.48,
		"fog_color": Color("#b0c8e0"), "fog_density": 0.0003, "fog_sun_scatter": 0.0,
		"exposure": 1.0, "glow_intensity": 0.4, "glow_threshold": 1.4, "saturation": 1.06, "contrast": 1.04,
		"night": false,
		"terrain": {"top": Color("#5f8a3a"), "soil": Color("#6b4f36"), "strata": Color("#9a8a6e"), "deep": Color("#4a4a52")},
		"sky": {"top_col": Color("#2456ac"), "mid_col": Color("#5e96dc"), "horizon_col": Color("#c6def2"),
				"below_col": Color("#4a5a40"), "mid_height": 0.3,
				"clouds": 0.72, "cloud_streak": 0.0, "cloud_scale": 1.0,
				"cloud_col": Color("#ffffff"), "cloud_shade": Color("#9aaac4"), "cloud_lit": Color("#fff6e8"),
				"cloud_light": Vector3(-0.5, 0.62, 0.6)},
		"haze": {"haze_col": Color("#a8c2e2"), "haze_sun_col": Color("#d0def0"), "haze_start": 180.0,
				"haze_scale": 650.0, "haze_max": 0.58, "haze_sun_pow": 4.0, "sun_dir": Vector3(-0.5, 0.3, -0.6)},
		"water": {"deep": Color("#0e2a30"), "far": Color("#3a5a6a"), "sky": Color("#8ab0d0"), "shallow": Color("#2a5a5a"),
				"foam": Color("#e0f0f0"), "wave_height": 0.0, "ripple": 1.4, "flow": 1.5},
		"gondola": {"period": 70.0},
	},
	{   # 2 Moonfall: hard sunlight low from the right on grey dust, the black sky, the home world huge on the left
		"name": "Moonfall",
		"sky_top": Color("#000000"), "sky_horizon": Color("#06070c"), "ground_horizon": Color("#3a3a3c"),
		"ground_bottom": Color("#18181a"),
		"sun_dir": Vector3(0.8, 0.22, 0.56), "sun_color": Color("#fff6ea"), "sun_energy": 2.6,
		"ambient_color": Color("#3c4c70"), "ambient_energy": 0.45,
		"fog_color": Color("#000000"), "fog_density": 0.0, "fog_sun_scatter": 0.0,
		"exposure": 1.0, "glow_intensity": 0.7, "glow_threshold": 1.0, "saturation": 1.0, "contrast": 1.08,
		"night": false,
		"terrain": {"top": Color("#9c9a96"), "soil": Color("#74726e"), "strata": Color("#4e4c4a"), "deep": Color("#38363a")},
		"sky": {"top_col": Color("#000002"), "mid_col": Color("#010206"), "horizon_col": Color("#04050a"),
				"below_col": Color("#0a0a0c"), "mid_height": 0.2,
				"stars": 1.0, "dust": 1.0, "dust_axis": Vector3(0.6, 0.45, 0.65),
				"planet": 1.0, "planet_dir": Vector3(-0.33, 0.075, -0.94), "planet_size": 0.135,
				"planet_light": Vector3(0.85, 0.15, 0.5), "planet_spin": 0.006},
		"haze": {"haze_col": Color("#08090e"), "haze_sun_col": Color("#08090e"), "haze_start": 200.0,
				"haze_scale": 900.0, "haze_max": 0.3, "haze_sun_pow": 4.0, "sun_dir": Vector3(0.8, 0.22, 0.56)},
		"water": {},
		"rover": {"dist": 70.0, "speed": 2.4},
		"lander": {"height": 90.0, "period": 60.0},
	},
	{   # 3 Ember Isle: night, the cone erupting on the right, lava running into the sea, the ash cloud lit red
		"name": "Ember Isle",
		"sky_top": Color("#05040a"), "sky_horizon": Color("#3a1812"), "ground_horizon": Color("#1a0c0a"),
		"ground_bottom": Color("#080406"),
		"sun_dir": Vector3(-0.55, 0.5, 0.67), "sun_color": Color("#9aaee0"), "sun_energy": 0.95,
		"ambient_color": Color("#5a4258"), "ambient_energy": 0.85,
		"fog_color": Color("#2a1210"), "fog_density": 0.0006, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.5, "glow_threshold": 1.6, "saturation": 1.08, "contrast": 1.06,
		"night": true,
		"terrain": {"top": Color("#5a524e"), "soil": Color("#4e3028"), "strata": Color("#8a4426"), "deep": Color("#2a2020")},
		"sky": {"top_col": Color("#03030a"), "mid_col": Color("#0c0814"), "horizon_col": Color("#2a1218"),
				"below_col": Color("#0a0606"), "mid_height": 0.2,
				"glow_dir": Vector3(0.3, 0.0, -0.95), "glow_col": Color("#a8301a"), "glow": 0.3, "glow_spread": 16.0,
				"glow_rise": 14.0, "stars": 0.55, "dust": 0.25,
				"moon": 1.0, "moon_dir": Vector3(-0.42, 0.15, -0.9), "moon_size": 0.016, "moon_col": Color("#e8dcc8"),
				"ash": 1.0, "ash_dir": Vector3(0.22, 0.16, -0.96), "ash_col": Color("#08070a"), "ash_lit": Color("#4a160c")},
		"haze": {"haze_col": Color("#2a1210"), "haze_sun_col": Color("#6a2210"), "haze_start": 120.0,
				"haze_scale": 600.0, "haze_max": 0.6, "haze_sun_pow": 6.0, "sun_dir": Vector3(0.36, 0.1, -0.93)},
		"water": {"deep": Color("#020306"), "far": Color("#0c0608"), "sky": Color("#3a1410"), "shallow": Color("#1a1210"),
				"foam": Color("#c06040"), "wave_height": 0.4, "ripple": 1.0, "flow": 0.0},
		"glows": [Color(1.0, 0.36, 0.08) * 1.6, Color(1.0, 0.45, 0.12) * 1.4, Color(1.0, 0.4, 0.1) * 0.9],
		"moon_glint": Vector4(-0.42, 0.15, -0.9, 0.0),
		"lightning": true,
	},
	{   # 4 Frozen Wastes: the arctic night, the aurora over the frozen sea, the station's lights on the shore
		"name": "Frozen Wastes",
		"sky_top": Color("#030612"), "sky_horizon": Color("#123050"), "ground_horizon": Color("#2a3a52"),
		"ground_bottom": Color("#101622"),
		"sun_dir": Vector3(-0.75, 0.35, 0.56), "sun_color": Color("#9ab8f0"), "sun_energy": 0.55,
		"ambient_color": Color("#2c4c66"), "ambient_energy": 0.65,
		"fog_color": Color("#122840"), "fog_density": 0.0004, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.8, "glow_threshold": 0.95, "saturation": 1.08, "contrast": 1.05,
		"night": true,
		"terrain": {"top": Color("#e6eef6"), "soil": Color("#8aa2b8"), "strata": Color("#c4dae8"), "deep": Color("#3a4656")},
		"sky": {"top_col": Color("#02040c"), "mid_col": Color("#06122a"), "horizon_col": Color("#123050"),
				"below_col": Color("#0a1424"), "mid_height": 0.22,
				"stars": 0.9, "dust": 0.5, "dust_axis": Vector3(-0.5, 0.3, 0.8),
				"aurora": 1.0, "aurora_low": Color("#2cff8a"), "aurora_high": Color("#9a40ff"),
				"aurora_dir": Vector3(0.15, 0.0, -1.0)},
		"haze": {"haze_col": Color("#163454"), "haze_sun_col": Color("#1c4060"), "haze_start": 120.0,
				"haze_scale": 650.0, "haze_max": 0.7, "haze_sun_pow": 4.0, "sun_dir": Vector3(0.2, 0.3, -1.0)},
		"water": {"deep": Color("#010309"), "far": Color("#06101e"), "sky": Color("#1a5a50"), "shallow": Color("#0a1420"),
				"foam": Color("#a0b8d0"), "wave_height": 0.05, "ripple": 0.7, "flow": 0.0},
		"seaice": {"ice": Color("#8aaccc"), "snow": Color("#d4e0ee"), "crack": Color("#16243a"), "sky": Color("#1e8a66")},
	},
]

var theme := 0
var _t := 0.0
var _mats := {}
var _land_mats: Array = []   ## materials that take the haze and the tremor
var _glow_mats: Array = []   ## materials that flicker with the tremor
var _sky: ShaderMaterial
var _clocked: Array = []     ## shader materials that read `clock`
var _spin: Array = []        ## [node, rest transform, local axis, rad/s]
var _slide: Array = []       ## [node, rest position, offset (Vector3), kind ("loop" | "ping"), period, pause]
var _hawks: Array = []       ## [node, rest transform, rad/s, phase]
var _lander: Array = []      ## [node, rest position, height, period, thrust node, its rest position]
var _lights: Array = []      ## [OmniLight3D, base energy, flicker]
var _flash_lights: Array = []  ## [OmniLight3D, start time, peak energy]
var _flash_slot := 0
var _booms: Array = []       ## [time, direction, colour, size, strength]
var _tremor := 0.0
var _rng := RandomNumberGenerator.new()
var _bolt_next := 6.0
var _bolts: Array = []       ## [time, strength, direction]
var _bolt_light: OmniLight3D
var _smoke_mats: Array = []
var _lava_mats: Array = []
var _bolt_pos := Vector3.ZERO


## The environment the view applies for a theme. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color, for
## a ProceduralSkyMaterial: ambient and reflections; the dome covers the background), sun_color, sun_rotation
## (Vector3, degrees, for the DirectionalLight3D), sun_energy, ambient_color, ambient_energy, fog_color, fog_density
## (exponential fog), fog_sun_scatter, exposure, glow_intensity, glow_threshold, saturation, contrast, night (true:
## keep the field's own lights on), name, and terrain: {top, soil, strata, deep} (Colors for the field's slab).
func environment_for(t: int) -> Dictionary:
	var d: Dictionary = THEMES[clampi(t, 0, THEMES.size() - 1)]
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_energy",
			"ambient_color", "ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure",
			"glow_intensity", "glow_threshold", "saturation", "contrast", "name", "night"]:
		out[k] = d[k]
	var s: Vector3 = (d["sun_dir"] as Vector3).normalized()
	out["sun_rotation"] = Vector3(rad_to_deg(asin(-s.y)), rad_to_deg(atan2(s.x, s.z)), 0.0)
	out["terrain"] = (d["terrain"] as Dictionary).duplicate()
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
	sm.sun_angle_max = 10.0
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
	env.fog_enabled = d["fog_density"] > 0.0
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = d["fog_color"]
	env.fog_density = d["fog_density"]
	env.fog_sun_scatter = d["fog_sun_scatter"]
	env.fog_sky_affect = 0.0
	env.glow_enabled = true
	env.glow_intensity = d["glow_intensity"]
	env.glow_hdr_threshold = d["glow_threshold"]
	env.glow_bloom = 0.02
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.set_glow_level(1, 0.6)
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.85)
	env.set_glow_level(4, 0.6)
	env.set_glow_level(5, 0.3)
	env.adjustment_enabled = true
	env.adjustment_saturation = d["saturation"]
	env.adjustment_contrast = d["contrast"]
	return env


## The sun (or the moon): its direction agrees with the shadows baked into the backdrop.
static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 240.0
	sun.directional_shadow_split_1 = 0.12
	sun.directional_shadow_split_2 = 0.3
	sun.directional_shadow_split_3 = 0.55
	sun.shadow_bias = 0.05
	sun.shadow_normal_bias = 1.5
	sun.shadow_blur = 1.5


## An explosion at pos (the field: z near 0), energy about 1 for a shell: a brief warm light there, a glow in the sky
## behind it.
func flash(pos: Vector3, energy: float = 1.0) -> void:
	if _flash_lights.is_empty():
		return
	var fl: Array = _flash_lights[_flash_slot]
	_flash_slot = (_flash_slot + 1) % _flash_lights.size()
	var l: OmniLight3D = fl[0]
	l.position = pos + Vector3(0.0, 2.5, 3.0)
	l.omni_range = 22.0 + 14.0 * sqrt(maxf(energy, 0.0))
	fl[1] = _t
	fl[2] = 5.0 * clampf(energy, 0.2, 4.0)
	var to := pos - CAMERA
	_booms.push_front([_t, to.normalized(), Color(1.0, 0.6, 0.3), clampf(0.05 + 0.04 * energy, 0.04, 0.2),
			0.12 * clampf(energy, 0.2, 3.0)])
	if _booms.size() > 4:
		_booms.resize(4)


## A big blast shakes the ground: the far lights flicker, the plants quiver (amount about 0..1).
func shake(amount: float) -> void:
	_tremor = maxf(_tremor, clampf(amount, 0.0, 1.0))


func build(t: int) -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	theme = clampi(t, 0, THEMES.size() - 1)
	_t = 0.0
	_mats.clear()
	_land_mats.clear()
	_glow_mats.clear()
	_clocked.clear()
	_spin.clear()
	_slide.clear()
	_hawks.clear()
	_lander.clear()
	_lights.clear()
	_flash_lights.clear()
	_booms.clear()
	_smoke_mats.clear()
	_lava_mats.clear()
	_bolts.clear()
	_tremor = 0.0
	_rng.seed = 300000 + theme * 977
	_bolt_next = 4.0
	var d: Dictionary = THEMES[theme]
	_add_sky(d)
	var packed := load(GLB % theme) as PackedScene
	if packed == null:
		push_error("RidgeBackdrop: missing %s" % (GLB % theme))
		return
	var root := packed.instantiate() as Node3D
	root.name = "landscape"
	add_child(root)
	_dress(root, d)
	_collect(root, d)
	_add_risers(d)
	_add_flash_lights()


func _add_sky(d: Dictionary) -> void:
	var dome := MeshInstance3D.new()
	dome.name = "sky"
	var m := SphereMesh.new()
	m.radius = DOME_RADIUS
	m.height = DOME_RADIUS * 2.0
	m.radial_segments = 64
	m.rings = 32
	dome.mesh = m
	dome.position = CAMERA
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dome.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	dome.custom_aabb = AABB(Vector3(-1, -1, -1) * DOME_RADIUS, Vector3(2, 2, 2) * DOME_RADIUS)
	_sky = _shader("ridge_sky")
	var sk: Dictionary = d["sky"]
	for k in sk:
		var v = sk[k]
		if v is Vector3:   # every vector the sky takes is a direction
			v = (v as Vector3).normalized()
		_sky.set_shader_parameter(k, v)
	dome.material_override = _sky
	add_child(dome)


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	return m


## Swaps the named materials for the backdrop shaders; the near props cast shadows.
func _dress(root: Node3D, d: Dictionary) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		var cast := nm.begins_with("near_") and nm != "near_lip"
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast else \
				GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			mi.set_surface_override_material(i, _material_for(mn, src, d))
	var hz: Dictionary = d["haze"]
	for m in _land_mats:
		for k in hz:
			var v = hz[k]
			if k == "sun_dir":
				v = (v as Vector3).normalized()
			(m as ShaderMaterial).set_shader_parameter(k, v)


func _land(rough: float) -> ShaderMaterial:
	var m := _shader("ridge_land")
	m.set_shader_parameter("rough", rough)
	_land_mats.append(m)
	return m


func _glow(col: Color, energy: float) -> ShaderMaterial:
	var g := _shader("ridge_glow")
	g.set_shader_parameter("color", col)
	g.set_shader_parameter("energy", energy)
	_glow_mats.append(g)
	return g


func _lava(energy: float) -> ShaderMaterial:
	var l := _shader("ridge_lava")
	l.set_shader_parameter("energy", energy)
	_lava_mats.append(l)
	return l


func _material_for(mn: String, src: Material, d: Dictionary) -> Material:
	if _mats.has(mn):
		return _mats[mn]
	var m: Material = null
	match mn:
		"ground":
			m = _land(0.95)
		"rock":
			m = _land(0.88)
		"wood":
			m = _land(0.8)
		"paint":
			var p := _land(0.6)
			p.set_shader_parameter("spec", 0.15)
			m = p
		"roof":
			var p := _land(0.5)
			p.set_shader_parameter("spec", 0.25)
			m = p
		"metal":
			var p := _land(0.4)
			p.set_shader_parameter("spec", 0.6)
			p.set_shader_parameter("shininess", 30.0)
			m = p
		"glass":
			var p := _land(0.1)
			p.set_shader_parameter("spec", 1.4)
			p.set_shader_parameter("shininess", 90.0)
			m = p
		"snow":
			var p := _land(0.75)
			p.set_shader_parameter("sparkle", 0.6 if d["night"] else 1.6)
			p.set_shader_parameter("spec", 0.12)
			p.set_shader_parameter("shininess", 12.0)
			m = p
		"ice":
			var p := _land(0.3)
			p.set_shader_parameter("spec", 0.7)
			p.set_shader_parameter("shininess", 50.0)
			p.set_shader_parameter("translucency", 0.3)
			m = p
		"foliage_sway":
			var p := _land(0.85)
			p.set_shader_parameter("sway", 0.008)
			p.set_shader_parameter("translucency", 0.2)
			m = p
		"flag_sway":
			var p := _land(0.8)
			p.set_shader_parameter("flutter", 1.0)
			p.set_shader_parameter("translucency", 0.3)
			m = p
		"water":
			var w := _shader("ridge_water")
			var wd: Dictionary = d["water"]
			for k in ["deep:deep_col", "far:far_col", "sky:sky_col", "shallow:shallow_col", "foam:foam_col",
					"wave_height:wave_height", "ripple:ripple", "flow:flow"]:
				var kv: PackedStringArray = k.split(":")
				if wd.has(kv[0]):
					w.set_shader_parameter(kv[1], wd[kv[0]])
			_land_mats.append(w)
			m = w
		"seaice":
			var s := _shader("ridge_ice")
			var sd: Dictionary = d.get("seaice", {})
			for k in ["ice:ice_col", "snow:snow_col", "crack:crack_col", "sky:sky_col"]:
				var kv: PackedStringArray = k.split(":")
				if sd.has(kv[0]):
					s.set_shader_parameter(kv[1], sd[kv[0]])
			_land_mats.append(s)
			m = s
		"waterfall":
			m = _shader("ridge_fall")
		"mist":
			var s := _shader("ridge_mist")
			var md: Dictionary = d.get("mist", {})
			for k in md:
				s.set_shader_parameter(k, md[k])
			m = s
		"window_glow":
			var g := _glow(Color(1.0, 0.72, 0.42), 2.2)
			g.set_shader_parameter("twinkle", 0.15)
			g.set_shader_parameter("variety", 0.5)
			g.set_shader_parameter("cell", 2.0)
			m = g
		"lamp_glow":
			var g := _glow(Color(1.0, 0.85, 0.6), 4.0)
			g.set_shader_parameter("cell", 3.0)
			m = g
		"beacon_glow":
			var g := _glow(Color(1.0, 0.18, 0.12), 7.0)
			g.set_shader_parameter("blink", 1.0)
			g.set_shader_parameter("blink_rate", 0.6)
			g.set_shader_parameter("cell", 6.0)
			m = g
		"dome_glow":
			var g := _glow(Color(0.78, 0.86, 1.0), 1.1)
			g.set_shader_parameter("dome", 1.0)
			m = g
		"headlight_glow":
			m = _glow(Color(1.0, 0.95, 0.82), 9.0)
		"lava_glow":
			var l := _lava(3.2)
			l.set_shader_parameter("speed", 1.6)
			m = l
		"crater_glow":
			var l := _lava(4.0)
			l.set_shader_parameter("pool", 1.0)
			l.set_shader_parameter("plate", 9.0)
			l.set_shader_parameter("crust", 0.45)
			m = l
		"crack_glow":
			var l := _lava(2.4)
			l.set_shader_parameter("cracks", 1.0)
			l.set_shader_parameter("plate", 3.0)
			l.set_shader_parameter("crust", 0.75)
			m = l
		_:
			m = _land(0.9)
	_mats[mn] = m
	return m


## The animated nodes and the light empties the Blender script names.
func _collect(root: Node3D, d: Dictionary) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 30100 + theme
	for n in root.find_children("*", "Node3D", true, false):
		var node := n as Node3D
		var nm := String(node.name)
		if nm.begins_with("hawk_"):
			_hawks.append([node, node.transform, (0.16 + 0.06 * rng.randf()) * (1.0 if rng.randf() < 0.5 else -1.0),
					rng.randf() * TAU])
		elif nm.begins_with("rotor_"):
			_spin.append([node, node.transform, Vector3.BACK, 1.1 + 0.5 * rng.randf()])
		elif nm == "radar":
			_spin.append([node, node.transform, Vector3.UP, 0.7])
		elif nm == "train":
			var td: Dictionary = d["train"]
			_slide.append([node, node.position, Vector3(td["dist"], 0, 0), "loop", td["dist"] / td["speed"], td["pause"]])
		elif nm == "rover":
			var rd: Dictionary = d["rover"]
			_slide.append([node, node.position, Vector3(rd["dist"], 0, 0), "ping", rd["dist"] / rd["speed"], 6.0])
		elif nm == "gondola":
			var end := root.find_child("cable_end", true, false) as Node3D
			if end:
				_slide.append([node, node.position, end.position - node.position, "ping", d["gondola"]["period"] * 0.5, 8.0])
		elif nm == "lander":
			var ld: Dictionary = d["lander"]
			var th := root.find_child("lander_thrust", true, false) as Node3D
			_lander.append([node, node.position, ld["height"], ld["period"], th, th.position if th else Vector3.ZERO])
		elif nm.begins_with("light_"):
			var l := OmniLight3D.new()
			l.shadow_enabled = false
			var flick := 0.0
			if nm.begins_with("light_lava"):
				l.light_color = Color(1.0, 0.42, 0.12)
				l.light_energy = 6.0
				l.omni_range = 160.0
				flick = 0.6
			elif nm.begins_with("light_cool"):
				l.light_color = Color(0.8, 0.88, 1.0)
				l.light_energy = 3.0
				l.omni_range = 30.0
			elif nm.begins_with("light_red"):
				l.light_color = Color(1.0, 0.25, 0.15)
				l.light_energy = 2.0
				l.omni_range = 20.0
			else:
				l.light_color = Color(1.0, 0.68, 0.38)
				l.light_energy = 3.0
				l.omni_range = 30.0
			l.omni_attenuation = 1.3
			node.add_child(l)
			_lights.append([l, l.light_energy, flick])
	# the water mirrors the glowing things (the crater, the lava's mouth) and the moon
	var glows: Array = d.get("glows", [])
	if not glows.is_empty() or d.has("moon_glint"):
		var pos := PackedVector4Array()
		var col := PackedVector4Array()
		var k := 0
		for n in root.find_children("glow_*", "Node3D", true, false):
			if k >= glows.size():
				break
			var p := _local_pos(n as Node3D)
			var c: Color = glows[k]
			pos.append(Vector4(p.x, p.y, p.z, 30.0))
			col.append(Vector4(c.r, c.g, c.b, 0.8))
			k += 1
		if d.has("moon_glint"):
			var mg: Vector4 = d["moon_glint"]
			pos.append(Vector4(mg.x, mg.y, mg.z, -1.0))
			col.append(Vector4(0.25, 0.27, 0.35, 0.3))
		while pos.size() < 4:
			pos.append(Vector4())
			col.append(Vector4())
		if _mats.has("water"):
			(_mats["water"] as ShaderMaterial).set_shader_parameter("glow_pos", pos)
			(_mats["water"] as ShaderMaterial).set_shader_parameter("glow_col", col)


## The volcano's plume and embers, steam, blowing snow, from the empties the Blender script names.
func _add_risers(d: Dictionary) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 30200 + theme
	var adds := {}    # kind -> [instances]   (additive: 0 ember, 1 lava bomb, 2 snow)
	var smokes := {}  # kind -> [instances]   (blended: 0 plume, 1 steam, 2 chimney)
	for n in find_children("*", "Node3D", true, false):
		var nm := String(n.name)
		var p := _local_pos(n as Node3D)
		if nm.begins_with("ember_"):
			var l: Array = adds.get(0, [])
			for i in 160:
				var o := Vector3(rng.randf_range(-14, 14), rng.randf_range(-2, 6), rng.randf_range(-10, 10))
				l.append([p + o, rng.randf_range(1.0, 2.4), rng.randf(), rng.randf_range(5.0, 9.0),
						rng.randf_range(60.0, 140.0), Color.WHITE])
			adds[0] = l
			var b: Array = adds.get(1, [])
			for i in 36:
				var o := Vector3(rng.randf_range(-8, 8), 0, rng.randf_range(-6, 6))
				b.append([p + o, rng.randf_range(1.6, 3.2), rng.randf(), rng.randf_range(4.0, 7.0),
						rng.randf_range(30.0, 55.0), Color.WHITE])
			adds[1] = b
		elif nm.begins_with("snow_"):
			var l: Array = adds.get(2, [])
			for i in 240:
				var o := Vector3(rng.randf_range(-160, 160), rng.randf_range(0, 18), rng.randf_range(-60, 40))
				l.append([p + o, rng.randf_range(0.18, 0.4), rng.randf(), rng.randf_range(5.0, 9.0),
						rng.randf_range(-3.0, 3.0), Color(0.85, 0.9, 1.0)])
			adds[2] = l
		elif nm.begins_with("smoke_"):
			var l: Array = smokes.get(0, [])
			for i in 90:
				l.append([p + Vector3(rng.randf_range(-10, 10), 0, rng.randf_range(-8, 8)), rng.randf_range(22.0, 36.0),
						rng.randf(), rng.randf_range(38.0, 52.0), rng.randf_range(260.0, 340.0), rng.randf_range(2.2, 3.6)])
			smokes[0] = l
		elif nm.begins_with("steam_"):
			var l: Array = smokes.get(1, [])
			for i in 34:
				l.append([p + Vector3(rng.randf_range(-14, 14), 0, rng.randf_range(-8, 8)), rng.randf_range(12.0, 20.0),
						rng.randf(), rng.randf_range(12.0, 18.0), rng.randf_range(90.0, 140.0), rng.randf_range(1.5, 2.5)])
			smokes[1] = l
		elif nm.begins_with("chimney_"):
			var l: Array = smokes.get(2, [])
			for i in 14:
				l.append([p, rng.randf_range(1.2, 2.0), rng.randf(), rng.randf_range(9.0, 13.0),
						rng.randf_range(16.0, 24.0), rng.randf_range(2.0, 3.0)])
			smokes[2] = l
	for kind in adds:
		var mi := _multimesh(adds[kind], float(kind), ["embers", "lava_bombs", "snow"][kind])
		var m := _shader("ridge_rise")
		m.set_shader_parameter("energy", [3.0, 4.0, 0.5][kind])
		m.set_shader_parameter("wind", [Vector3(-30.0, 0, 0), Vector3(-8.0, 0, 0), Vector3(60.0, 0, 8.0)][kind])
		mi.material_override = m
		_clocked.append(m)
		add_child(mi)
	for kind in smokes:
		var list: Array = smokes[kind]
		var mi := _multimesh(list, -1.0, ["plume", "steam", "chimney_smoke"][kind])
		var m := _shader("ridge_smoke")
		match kind:
			0:
				m.set_shader_parameter("wind", Vector3(-340.0, 0, -40.0))
				m.set_shader_parameter("glow_col", Color(0.9, 0.26, 0.06))
				m.set_shader_parameter("glow_reach", 0.22)
				m.set_shader_parameter("shade_col", Color(0.03, 0.025, 0.03))
				m.set_shader_parameter("lit_col", Color(0.1, 0.08, 0.1))
				m.set_shader_parameter("opacity", 0.85)
			1:
				m.set_shader_parameter("wind", Vector3(-50.0, 0, 0))
				m.set_shader_parameter("glow_col", Color(1.0, 0.45, 0.2))
				m.set_shader_parameter("glow_reach", 0.6)
				m.set_shader_parameter("shade_col", Color(0.22, 0.18, 0.2))
				m.set_shader_parameter("lit_col", Color(0.5, 0.45, 0.5))
				m.set_shader_parameter("opacity", 0.55)
			2:
				m.set_shader_parameter("wind", Vector3(8.0, 0, 0))
				m.set_shader_parameter("glow_col", Color(0, 0, 0))
				m.set_shader_parameter("shade_col", Color(0.5, 0.52, 0.56))
				m.set_shader_parameter("lit_col", Color(0.85, 0.86, 0.9))
				m.set_shader_parameter("opacity", 0.45)
		mi.material_override = m
		_clocked.append(m)
		_smoke_mats.append(m)
		add_child(mi)


## One MultiMesh of camera-facing quads: entries [position, size, phase, period, rise, colour or growth].
func _multimesh(list: Array, kind: float, nm: String) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.use_custom_data = true
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	mm.mesh = q
	mm.instance_count = list.size()
	for i in list.size():
		var e: Array = list[i]
		mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * e[1]), e[0]))
		if kind >= 0.0:
			mm.set_instance_color(i, e[5])
			mm.set_instance_custom_data(i, Color(e[2], e[3], e[4], kind))
		else:
			mm.set_instance_color(i, Color.WHITE)
			mm.set_instance_custom_data(i, Color(e[2], e[3], e[4], e[5]))
	var mi := MultiMeshInstance3D.new()
	mi.name = nm
	mi.multimesh = mm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	mi.custom_aabb = AABB(Vector3(-1200, -50, -1200), Vector3(2400, 1200, 2400))
	return mi


func _add_flash_lights() -> void:
	for i in LIGHTS:
		var l := OmniLight3D.new()
		l.name = "flash_light_%d" % i
		l.shadow_enabled = false
		l.omni_attenuation = 1.1
		l.light_color = Color(1.0, 0.62, 0.3)
		l.light_energy = 0.0
		l.visible = false
		add_child(l)
		_flash_lights.append([l, -100.0, 0.0])
	if THEMES[theme].get("lightning", false):
		_bolt_light = OmniLight3D.new()
		_bolt_light.name = "lightning"
		_bolt_light.shadow_enabled = false
		_bolt_light.light_color = Color(0.75, 0.78, 1.0)
		_bolt_light.omni_range = 420.0
		_bolt_light.omni_attenuation = 0.8
		_bolt_light.light_energy = 0.0
		_bolt_light.visible = false
		add_child(_bolt_light)
		var smoke := find_child("smoke_*", true, false) as Node3D
		_bolt_pos = (_local_pos(smoke) if smoke else Vector3(200, 100, -480)) + Vector3(-40.0, 160.0, 0.0)


## A descendant's position in this node's space (works before the backdrop enters the tree).
func _local_pos(n: Node3D) -> Vector3:
	var tr := n.transform
	var p := n.get_parent()
	while p != self and p is Node3D:
		tr = (p as Node3D).transform * tr
		p = p.get_parent()
	return tr.origin


func _process(delta: float) -> void:
	_t += delta
	for s in _spin:
		var rest: Transform3D = s[1]
		(s[0] as Node3D).transform = rest * Transform3D(Basis(s[2], _t * s[3]), Vector3.ZERO)
	for h in _hawks:
		var rest: Transform3D = h[1]
		var a: float = _t * h[2] + h[3]
		var tr := Transform3D(Basis(Vector3.UP, a), Vector3.ZERO)
		tr.origin.y = sin(_t * 0.23 + h[3]) * 2.5
		(h[0] as Node3D).transform = rest * tr
	for s in _slide:
		var node: Node3D = s[0]
		var run: float = s[4]
		var pause: float = s[5]
		var u := 0.0
		if s[3] == "loop":
			var ph := fmod(_t + run * 0.5, run + pause)
			u = clampf(ph / run, 0.0, 1.0)
			node.visible = ph < run
		else:
			var ph := fmod(_t, 2.0 * (run + pause))
			if ph < run:
				u = smoothstep(0.0, 1.0, ph / run)
			elif ph < run + pause:
				u = 1.0
			elif ph < 2.0 * run + pause:
				u = 1.0 - smoothstep(0.0, 1.0, (ph - run - pause) / run)
		node.position = (s[1] as Vector3) + (s[2] as Vector3) * u
	for l in _lander:
		var node: Node3D = l[0]
		var period: float = l[3]
		var ph := fmod(_t + period * 0.15, period) / period
		# rests on the pad, lifts off, hovers high, comes down slowly and settles
		var hgt := 0.0
		if ph > 0.2 and ph < 0.5:
			hgt = smoothstep(0.2, 0.5, ph)
		elif ph >= 0.5 and ph < 0.62:
			hgt = 1.0
		elif ph >= 0.62 and ph < 0.92:
			hgt = 1.0 - smoothstep(0.62, 0.92, ph)
		var lift := Vector3(0, hgt * hgt * float(l[2]), 0)
		node.position = (l[1] as Vector3) + lift
		var flame := l[4] as Node3D
		if flame:
			flame.position = (l[5] as Vector3) + lift
			flame.visible = ph > 0.18 and ph < 0.93
			flame.scale = Vector3(1.0, 0.8 + 0.25 * sin(_t * 37.0) + 0.1 * sin(_t * 61.0), 1.0)
	for l in _lights:
		var f := 1.0
		if l[2] > 0.0:
			f = 1.0 - l[2] * 0.3 + l[2] * 0.3 * (0.6 + 0.25 * sin(_t * 3.1) + 0.15 * sin(_t * 7.7 + 1.3))
		if _tremor > 0.05:
			f *= 1.0 - _tremor * 0.7 * float(_rng.randf() < 0.5)
		(l[0] as OmniLight3D).light_energy = l[1] * f
	for m in _clocked:
		(m as ShaderMaterial).set_shader_parameter("clock", _t)
	_tremor = maxf(_tremor - delta * 1.4, 0.0)
	for m in _glow_mats:
		(m as ShaderMaterial).set_shader_parameter("tremor", _tremor)
	for m in _land_mats:
		(m as ShaderMaterial).set_shader_parameter("tremor", _tremor)
	if _mats.has("seaice"):   # the aurora's light on the ice breathes with the sky's
		(_mats["seaice"] as ShaderMaterial).set_shader_parameter("sky_pulse", 0.5 + 0.5 * sin(_t * 0.21))
	_update_lightning()
	_update_sky()


func _update_lightning() -> void:
	if _bolt_light == null:
		return
	while _t >= _bolt_next:
		var dir := Vector3(_rng.randf_range(-60, 60), _rng.randf_range(-30, 90), 0.0)
		_bolts.append([_bolt_next, _rng.randf_range(0.6, 1.0), _bolt_pos + dir])
		if _rng.randf() < 0.45:
			_bolts.append([_bolt_next + _rng.randf_range(0.12, 0.3), _rng.randf_range(0.4, 0.8), _bolt_pos + dir])
		_bolt_next += _rng.randf_range(3.5, 11.0)
	var e := 0.0
	var at := _bolt_pos
	var i := 0
	while i < _bolts.size():
		var b: Array = _bolts[i]
		var age: float = _t - b[0]
		if age > 0.6:
			_bolts.remove_at(i)
			continue
		if age >= 0.0:
			var k: float = b[1] * exp(-age * 14.0) * (0.7 + 0.3 * sin(age * 90.0))
			if k > e:
				e = k
				at = b[2]
		i += 1
	_bolt_light.light_energy = e * 5.0
	_bolt_light.visible = e > 0.02
	_bolt_light.position = at
	_sky.set_shader_parameter("bolt", e)
	_sky.set_shader_parameter("bolt_dir", (at - CAMERA).normalized())
	for m in _smoke_mats:
		(m as ShaderMaterial).set_shader_parameter("flash", e)
		(m as ShaderMaterial).set_shader_parameter("flash_pos", at)


func _update_sky() -> void:
	_sky.set_shader_parameter("clock", _t)
	var dirs := PackedVector4Array()
	var cols := PackedVector4Array()
	for b in _booms:
		var age: float = _t - b[0]
		var dn: Vector3 = b[1]
		var c: Color = b[2]
		var k: float = b[4] * exp(-age * 3.0) if age >= 0.0 else 0.0
		dirs.append(Vector4(dn.x, dn.y, dn.z, b[3]))
		cols.append(Vector4(c.r * k, c.g * k, c.b * k, 0.0))
	while dirs.size() < 4:
		dirs.append(Vector4(0, 1, 0, 0))
		cols.append(Vector4())
	_sky.set_shader_parameter("boom_dir", dirs)
	_sky.set_shader_parameter("boom_col", cols)
	for fl in _flash_lights:
		var l: OmniLight3D = fl[0]
		var age: float = _t - fl[1]
		var e: float = fl[2] * exp(-age * 5.0) if age >= 0.0 else 0.0
		l.light_energy = e
		l.visible = e > 0.05
