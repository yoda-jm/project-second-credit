class_name BloomBackdrop
extends Node3D
## The fairy-tale scenes behind the Bloomwand levels, one per theme (0-5): Bluebell Glade, Mushroom Ring, Crystal
## Grotto, Cloud Castle, Winter Hollow, Thorn Tower. build(theme) loads art/backdrops/backdrop_<theme>.glb
## (tools/blender/bloomwand_backdrops.py), swaps the materials the Blender script marks by name for the game's shaders
## (water, ice and the glowing pool, lanterns and windows, glowing mushrooms, glow-worms, crystals, clouds, the
## waterfall, sunbeams, mist, foliage in the breeze), adds the sky dome (sun, moon, stars, clouds, rainbow, aurora,
## storm and lightning), the omni lights the script marks with empties, and the small living things: butterflies,
## petals, fireflies, wisps, snow, rain, birds, dust in the sunbeams. Everything runs on the node's own clock in
## _process (fixed-step safe, deterministic: seeded per theme).
##
## The game reacts through celebrate() (a level cleared: bursts of sparkles, petals or fireworks in the theme's
## colours) and flash(pos) (a quick pop of light at pos in the play space).
## The view owns the WorldEnvironment and the key light: it reads environment_for(theme) (Pop Voyage's keys, plus
## name, blocks and tint) and may call make_environment() and setup_sun() with that dictionary.
##
## Space: the level is x 0..20, y 0..15 on z = 0 (blocks 1 m deep), the camera near (10, 7.5, 27), fov 36
## (Camera3D.far must reach the sky dome: 400 is safe). The scenery fills z -1.5 .. -205; under the level's floor a
## bank of earth (or cloud, or rock) runs down out of view. The middle is kept soft; the framing is at the sides.

const GLB := "res://games/bloomwand/art/backdrops/backdrop_%d.glb"
const SH := "res://games/bloomwand/shaders/"
const CAMERA := Vector3(10.0, 7.5, 27.0)
const DOME_RADIUS := 230.0
const POOL := 24               ## burst slots (a ring: the oldest is reused)
const SPARKS := 90             ## quads per burst

## Per theme: the environment the view applies, the sky, the water, the beams and mist, the lights, the motes and
## the celebration. Motes: kind (see bloom_mote.gdshaderinc), count, either "box" ([x0, x1, y0, y1, z0, z1], world)
## or "at" (the prefix of the empties they gather round) with "spread", size and period ranges, span, wind, colours,
## glow (additive), energy.
const THEMES := [
	{   # 0 Bluebell Glade: a spring morning, the sun high on the left through the canopy
		"name": "Bluebell Glade", "blocks": "wood", "tint": Color("#f4ead8"), "night": false,
		"sky_top": Color("#4f8ad0"), "sky_mid": Color("#8ab8e0"), "sky_horizon": Color("#d8ecd8"), "below": Color("#7a9a70"),
		"ground_horizon": Color("#8aa878"), "ground_bottom": Color("#3a5030"),
		"sun_dir": Vector3(-0.45, 0.6, -0.65), "sun_disc": 0.0, "sun_glow": 0.35, "sky_sun": Color("#fff2c8"),
		"clouds": 0.35, "cloud_col": Color("#f0f4f8"), "cloud_lit": Color("#fff8e0"),
		"sun_color": Color("#fff0cc"), "sun_rotation": Vector3(-38, -35, 0), "sun_energy": 1.35,
		"ambient_color": Color("#a8c4b4"), "ambient_energy": 0.75,
		"fog_color": Color("#b8d4c8"), "fog_density": 0.0028, "fog_sun_scatter": 0.15,
		"exposure": 1.0, "glow_intensity": 0.55, "glow_threshold": 1.1, "saturation": 1.12, "contrast": 1.04,
		"water": {"deep": Color("#1e3a34"), "shallow": Color("#4a6a3a"), "sky": Color("#b8d8e0")},
		"beam": [Color("#fff0b8"), 0.14], "mist": [0.35, 1.0],
		"motes": [
			{"kind": 4, "at": "butterfly_", "count": 3, "spread": 1.5, "size": [0.22, 0.32], "period": [1, 1], "span": 1.6,
				"colors": [Color("#ffc040"), Color("#f0f0ff"), Color("#7ab8ff"), Color("#ff9ad0")], "energy": 1.0},
			{"kind": 4, "box": [-4, 24, 1, 6, -6, -22], "count": 8, "size": [0.18, 0.26], "period": [1, 1], "span": 2.0,
				"colors": [Color("#ffc040"), Color("#f0f0ff"), Color("#ffe070")], "energy": 1.0},
			{"kind": 3, "at": "petal_", "count": 40, "spread": 5.0, "size": [0.08, 0.13], "period": [7, 11], "span": 10.0,
				"wind": Vector3(3.0, 0, 1.0), "colors": [Color("#fff0f4"), Color("#ffd8e4")], "energy": 1.1},
			{"kind": 8, "at": "sparkle_", "count": 18, "spread": 3.0, "size": [0.04, 0.07], "period": [20, 30], "span": 1.5,
				"colors": [Color("#fff4c0")], "glow": true, "energy": 1.4},
			{"kind": 6, "box": [-2, 22, 0.5, 4, -3, -14], "count": 30, "size": [0.06, 0.1], "period": [1, 1], "span": 1.0,
				"colors": [Color("#fff8d0"), Color("#d8f0ff")], "glow": true, "energy": 1.5},
		],
		"burst": {"kinds": [0, 1], "colors": [Color("#ffe080"), Color("#ff9ad0"), Color("#a8a0ff"), Color("#fff8f0")],
				"spread": 0.25, "sky": Color("#fff0c0")},
	},
	{   # 1 Mushroom Ring: twilight, the afterglow low on the left, a big moon rising on the right
		"name": "Mushroom Ring", "blocks": "wood", "tint": Color("#cfc0e8"), "night": true,
		"sky_top": Color("#141640"), "sky_mid": Color("#3a2e6a"), "sky_horizon": Color("#d88a8a"), "below": Color("#2a2448"),
		"ground_horizon": Color("#3a3058"), "ground_bottom": Color("#141228"),
		"sun_dir": Vector3(-0.8, 0.02, -0.6), "sun_disc": 0.0, "sun_glow": 0.55, "sky_sun": Color("#ff9a6a"),
		"moon": 1.0, "moon_from": Vector3(0.17, 0.15, -0.97), "moon_to": Vector3(0.17, 0.25, -0.97), "moon_rise": 180.0,
		"moon_size": 0.07, "stars": 0.7, "clouds": 0.25, "cloud_col": Color("#2a2450"), "cloud_lit": Color("#b86a7a"),
		"sun_color": Color("#b8b0ff"), "sun_rotation": Vector3(-32, 30, 0), "sun_energy": 0.6,
		"ambient_color": Color("#5a4c8c"), "ambient_energy": 0.65,
		"fog_color": Color("#3a3468"), "fog_density": 0.0055, "fog_sun_scatter": 0.0,
		"exposure": 1.1, "glow_intensity": 0.85, "glow_threshold": 0.95, "saturation": 1.12, "contrast": 1.04,
		"water": {}, "glow_light": Color("#5af0d0"), "mist": [0.4, 1.1],
		"motes": [
			{"kind": 0, "box": [-6, 26, 0.5, 6, -3, -40], "count": 120, "size": [0.08, 0.14], "period": [1, 1], "span": 1.2,
				"colors": [Color("#d8ff7a"), Color("#a8ff9a"), Color("#fff08a")], "glow": true, "energy": 2.2},
			{"kind": 0, "at": "firefly_", "count": 10, "spread": 2.0, "size": [0.1, 0.16], "period": [1, 1], "span": 1.0,
				"colors": [Color("#d8ff7a")], "glow": true, "energy": 2.4},
			{"kind": 7, "at": "wisp_", "count": 60, "spread": 6.0, "size": [0.08, 0.16], "period": [5, 9], "span": 5.0,
				"colors": [Color("#5af0d8"), Color("#b08aff"), Color("#ff8ad8")], "glow": true, "energy": 2.0},
		],
		"burst": {"kinds": [0, 0, 1], "colors": [Color("#5af0d8"), Color("#b08aff"), Color("#ff8ad8"), Color("#d8ff7a")],
				"spread": 0.3, "sky": Color("#8a6aff")},
	},
	{   # 2 Crystal Grotto: deep underground, the light coming from the crystals, the pool and a crack overhead
		"name": "Crystal Grotto", "blocks": "crystal", "tint": Color("#bfe4ff"), "night": true,
		"sky_top": Color("#05060c"), "sky_mid": Color("#080a14"), "sky_horizon": Color("#0c1020"), "below": Color("#06070c"),
		"ground_horizon": Color("#1a2240"), "ground_bottom": Color("#0a0c18"),
		"sun_dir": Vector3(0, 1, 0), "sun_disc": 0.0, "sun_glow": 0.0, "sky_sun": Color("#000000"),
		"sun_color": Color("#a8d8ff"), "sun_rotation": Vector3(-55, 12, 0), "sun_energy": 0.45,
		"ambient_color": Color("#4a5288"), "ambient_energy": 0.85,
		"fog_color": Color("#121e3c"), "fog_density": 0.0045, "fog_sun_scatter": 0.0,
		"exposure": 1.15, "glow_intensity": 1.0, "glow_threshold": 0.9, "saturation": 1.15, "contrast": 1.05,
		"water": {"deep": Color("#062030"), "shallow": Color("#0a3a48"), "sky": Color("#3a6a9a"), "glow": Color("#3ae8ff")},
		"beam": [Color("#b8e0ff"), 0.11], "mist": [0.55, 1.4],
		"motes": [
			{"kind": 0, "box": [-6, 26, 1, 14, -4, -50], "count": 90, "size": [0.05, 0.1], "period": [1, 1], "span": 1.6,
				"colors": [Color("#7aeaff"), Color("#c8a0ff"), Color("#a0ffd8")], "glow": true, "energy": 1.8},
			{"kind": 7, "at": "wisp_", "count": 50, "spread": 7.0, "size": [0.06, 0.12], "period": [6, 10], "span": 6.0,
				"colors": [Color("#7aeaff"), Color("#a0fff0")], "glow": true, "energy": 2.0},
			{"kind": 8, "at": "sparkle_", "count": 14, "spread": 2.5, "size": [0.04, 0.07], "period": [20, 30], "span": 1.2,
				"colors": [Color("#d8f0ff")], "glow": true, "energy": 1.6},
		],
		"burst": {"kinds": [0, 0, 3], "colors": [Color("#7ae8ff"), Color("#c890ff"), Color("#ff8ae0"), Color("#a0ffd8")],
				"spread": 0.25, "sky": Color("#3a8aff")},
	},
	{   # 3 Cloud Castle: above the clouds at sunset, the sun sinking on the left, a rainbow on the right
		"name": "Cloud Castle", "blocks": "stone", "tint": Color("#fff2e4"), "night": false,
		"sky_top": Color("#3a3c8a"), "sky_mid": Color("#a86a9a"), "sky_horizon": Color("#ffb878"), "below": Color("#b88aa8"),
		"ground_horizon": Color("#e0a8a0"), "ground_bottom": Color("#7a6a9a"),
		"sun_dir": Vector3(-0.4, 0.07, -0.92), "sun_disc": 1.0, "sun_size": 0.035, "sun_glow": 0.9, "sky_sun": Color("#ffc080"),
		"clouds": 0.4, "cloud_col": Color("#b07aa0"), "cloud_lit": Color("#ffc890"), "cloud_scale": 0.8,
		"rainbow": 0.9, "rainbow_dir": Vector3(0.45, -0.2, -0.87), "rainbow_radius": 0.52,
		"sun_color": Color("#ffc890"), "sun_rotation": Vector3(-24, -48, 0), "sun_energy": 1.4,
		"ambient_color": Color("#c8a0c0"), "ambient_energy": 0.7,
		"fog_color": Color("#f0b8a8"), "fog_density": 0.002, "fog_sun_scatter": 0.3,
		"exposure": 1.0, "glow_intensity": 0.7, "glow_threshold": 1.0, "saturation": 1.1, "contrast": 1.03,
		"water": {}, "mist": [0.35, 1.0], "cloud_rim": Color("#ffb070"),
		"motes": [
			{"kind": 5, "box": [-10, 30, 11, 18, -30, -70], "count": 12, "size": [0.35, 0.6], "period": [26, 40], "span": 34.0,
				"colors": [Color("#4a3a5a")], "energy": 1.0},
			{"kind": 3, "at": "petal_", "count": 30, "spread": 3.0, "size": [0.07, 0.11], "period": [8, 12], "span": 12.0,
				"wind": Vector3(4.0, 0, 1.0), "colors": [Color("#ffe0ec"), Color("#ffc8d8")], "energy": 1.1},
			{"kind": 6, "box": [-4, 24, 1, 15, -5, -20], "count": 20, "size": [0.06, 0.1], "period": [1, 1], "span": 1.0,
				"colors": [Color("#fff0d0")], "glow": true, "energy": 1.2},
		],
		"burst": {"kinds": [2, 0, 2], "colors": [Color("#ffd070"), Color("#ff7ab0"), Color("#7ad0ff"), Color("#c8a0ff")],
				"spread": 0.3, "sky": Color("#ffb070")},
	},
	{   # 4 Winter Hollow: a clear snowy night, the aurora over the mountains, lanterns in the trees
		"name": "Winter Hollow", "blocks": "crystal", "tint": Color("#dceeff"), "night": true,
		"sky_top": Color("#03061a"), "sky_mid": Color("#0c1838"), "sky_horizon": Color("#26386a"), "below": Color("#1a2448"),
		"ground_horizon": Color("#2a3a6a"), "ground_bottom": Color("#0c1228"),
		"sun_dir": Vector3(0, 1, 0), "sun_disc": 0.0, "sun_glow": 0.0, "sky_sun": Color("#000000"),
		"moon": 1.0, "moon_from": Vector3(-0.3, 0.27, -0.91), "moon_size": 0.04,
		"stars": 1.0, "aurora": 0.75, "snow_glow": 0.22, "aurora_low": Color("#3aff9a"), "aurora_high": Color("#8a4aff"),
		"sun_color": Color("#a8c4ff"), "sun_rotation": Vector3(-35, -30, 0), "sun_energy": 0.7,
		"ambient_color": Color("#42548a"), "ambient_energy": 0.7,
		"fog_color": Color("#1a2648"), "fog_density": 0.005, "fog_sun_scatter": 0.0,
		"exposure": 1.1, "glow_intensity": 0.9, "glow_threshold": 0.95, "saturation": 1.08, "contrast": 1.04,
		"water": {"deep": Color("#2a3a5a"), "shallow": Color("#7a8ab8"), "sky": Color("#4a6aaa"), "ice": true},
		"mist": [0.35, 0.9],
		"motes": [
			{"kind": 1, "box": [-8, 28, 4, 22, -2, -14], "count": 360, "size": [0.05, 0.09], "period": [7, 12], "span": 18.0,
				"wind": Vector3(1.2, 0, 0.3), "colors": [Color("#ffffff"), Color("#e0ecff")], "energy": 1.1},
			{"kind": 1, "box": [-25, 45, 6, 30, -14, -60], "count": 600, "size": [0.1, 0.16], "period": [9, 14], "span": 24.0,
				"wind": Vector3(2.0, 0, 0.5), "colors": [Color("#e8f0ff")], "energy": 0.9},
			{"kind": 6, "at": "sparkle_", "count": 10, "spread": 4.0, "size": [0.05, 0.09], "period": [1, 1], "span": 0.3,
				"colors": [Color("#e0f0ff")], "glow": true, "energy": 1.6},
		],
		"burst": {"kinds": [0, 2, 0], "colors": [Color("#ffffff"), Color("#9ad0ff"), Color("#ffc870"), Color("#8affc0")],
				"spread": 0.2, "sky": Color("#8affc0")},
	},
	{   # 5 Thorn Tower: a stormy dusk, an ember of sunset under the clouds, rain, lightning
		"name": "Thorn Tower", "blocks": "stone", "tint": Color("#a49ab4"), "night": true,
		"sky_top": Color("#0c0a14"), "sky_mid": Color("#2a1e30"), "sky_horizon": Color("#a8443a"), "below": Color("#1a1420"),
		"ground_horizon": Color("#3a2830"), "ground_bottom": Color("#0e0a12"),
		"sun_dir": Vector3(0.75, 0.03, -0.66), "sun_disc": 0.0, "sun_glow": 0.6, "sky_sun": Color("#ff6a3a"),
		"storm": 1.0, "storm_col": Color("#2a2234"), "storm_lit": Color("#9a4a42"),
		"eye": 0.45, "eye_dir": Vector3(0.16, 0.22, -0.96), "eye_col": Color("#a03a6a"), "eye_size": 0.2,
		"sun_color": Color("#ff9a78"), "sun_rotation": Vector3(-18, 42, 0), "sun_energy": 0.55,
		"ambient_color": Color("#4a3e62"), "ambient_energy": 0.8,
		"fog_color": Color("#3e2e48"), "fog_density": 0.005, "fog_sun_scatter": 0.1,
		"exposure": 1.05, "glow_intensity": 0.9, "glow_threshold": 0.95, "saturation": 1.02, "contrast": 1.1,
		"water": {}, "mist": [0.4, 0.9], "lightning": [5.0, 10.0],
		"motes": [
			{"kind": 2, "box": [-10, 30, 2, 24, -2, -16], "count": 260, "size": [0.6, 0.9], "period": [0.7, 1.0], "span": 22.0,
				"wind": Vector3(-4.0, 0, 0), "colors": [Color("#9a98b8")], "energy": 0.55},
			{"kind": 2, "box": [-30, 50, 4, 40, -16, -70], "count": 420, "size": [1.2, 1.8], "period": [0.9, 1.2], "span": 34.0,
				"wind": Vector3(-6.0, 0, 0), "colors": [Color("#7a7898")], "energy": 0.45},
			{"kind": 7, "at": "wisp_", "count": 40, "spread": 5.0, "size": [0.25, 0.45], "period": [5, 9], "span": 8.0,
				"wind": Vector3(-2.0, 0, 0), "colors": [Color("#c87aff"), Color("#ff6ab0")], "glow": true, "energy": 2.0},
			{"kind": 5, "box": [10, 28, 20, 30, -70, -85], "count": 7, "size": [0.9, 1.3], "period": [14, 22], "span": 16.0,
				"colors": [Color("#141018")], "energy": 1.0},
		],
		"burst": {"kinds": [1, 0, 1], "colors": [Color("#ff3a5a"), Color("#ff7a9a"), Color("#c87aff"), Color("#ffd0e0")],
				"spread": 0.15, "sky": Color("#ff6a8a")},
	},
]

var theme := 0
var _t := 0.0
var _d: Dictionary = {}
var _mats := {}
var _clocked: Array = []     ## ShaderMaterials that read `clock`
var _sky: ShaderMaterial
var _float: Array = []       ## [node, rest transform, height, rate, phase]
var _drift: Array = []       ## [node, rest transform, amplitude, rate, phase]
var _swing: Array = []       ## [node, rest transform, angle, rate, phase]
var _lights: Array = []      ## [OmniLight3D, base energy, mode (0 steady, 1 flame, 2 pulse), phase]
var _rng := RandomNumberGenerator.new()
var _mm: MultiMesh
var _slot := 0
var _pop_light: OmniLight3D
var _pop_t := -10.0
var _bolt_light: OmniLight3D
var _next_bolt := 4.0
var _bolt_t := -10.0
var _sheet_t := -10.0
var _glow_t := -10.0


## The environment the view applies for a theme. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color,
## for a ProceduralSkyMaterial: ambient and reflections; the dome covers the background), sun_color, sun_rotation
## (Vector3, degrees, for the DirectionalLight3D: a key light from the front, so the blocks read), sun_energy,
## ambient_color, ambient_energy, fog_color, fog_density (exponential fog), fog_sun_scatter, exposure,
## glow_intensity, glow_threshold, saturation, contrast, night (bool: keep the level's own lights on), name, blocks
## ("stone", "wood" or "crystal": the block style that suits the theme) and tint (Color: tint the blocks with it).
func environment_for(t: int) -> Dictionary:
	var d: Dictionary = THEMES[clampi(t, 0, THEMES.size() - 1)]
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_rotation", "sun_energy",
			"ambient_color", "ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure",
			"glow_intensity", "glow_threshold", "saturation", "contrast", "night", "name", "blocks", "tint"]:
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
	env.set_glow_level(1, 0.6)
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.85)
	env.set_glow_level(4, 0.6)
	env.set_glow_level(5, 0.3)
	env.adjustment_enabled = true
	env.adjustment_saturation = d["saturation"]
	env.adjustment_contrast = d["contrast"]
	return env


## The key light (sunlight, moonlight, the glow of the storm's sunset).
static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 60.0


## A level cleared: bursts across the scene in the theme's colours (sparkles, petals or fireworks), a glow in the sky.
func celebrate() -> void:
	if _mm == null:
		return
	var b: Dictionary = _d["burst"]
	var kinds: Array = b["kinds"]
	var cols: Array = b["colors"]
	for i in 9:
		var xs := lerpf(1.0, 19.0, (i + 0.5) / 9.0) + _rng.randf_range(-0.8, 0.8)
		var ys := _rng.randf_range(8.0, 14.0)
		var z := _rng.randf_range(-3.0, -12.0)
		var k: int = kinds[i % kinds.size()]
		var r := _rng.randf_range(2.2, 3.4) * (CAMERA.z - z) / CAMERA.z
		_burst(_level_to_world(xs, ys, z), k, cols[i % cols.size()], b["spread"], r, _t + 0.15 + i * 0.18 + _rng.randf() * 0.1)
	for i in 4:
		var z := -40.0
		_burst(_level_to_world(2.0 + i * 5.3, 15.0, z), kinds[0], cols[(i + 1) % cols.size()], b["spread"],
				4.0 * (CAMERA.z - z) / CAMERA.z, _t + 1.9 + i * 0.15)
	_glow_t = _t


## A quick pop of light at pos (play space): a little ring of sparks and a brief light.
func flash(pos: Vector3) -> void:
	if _mm == null:
		return
	var b: Dictionary = _d["burst"]
	var cols: Array = b["colors"]
	_burst(pos + Vector3(0, 0, 0.6), 3, cols[_rng.randi() % cols.size()], 0.2, 1.0, _t)
	if _pop_light:
		_pop_light.position = pos + Vector3(0, 0.3, 1.4)
		_pop_light.light_color = (cols[0] as Color).lerp(Color.WHITE, 0.4)
		_pop_t = _t


func build(t: int) -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	theme = clampi(t, 0, THEMES.size() - 1)
	_d = THEMES[theme]
	_t = 0.0
	_mats.clear()
	_clocked.clear()
	_float.clear()
	_drift.clear()
	_swing.clear()
	_lights.clear()
	_slot = 0
	_rng.seed = 330000 + theme * 977
	_next_bolt = 3.5
	_bolt_t = -10.0
	_sheet_t = -10.0
	_glow_t = -10.0
	_add_sky()
	var packed := load(GLB % theme) as PackedScene
	if packed == null:
		push_error("BloomBackdrop: missing %s" % (GLB % theme))
		return
	var root := packed.instantiate() as Node3D
	root.name = "diorama"
	add_child(root)
	_dress(root)
	_collect(root)
	_add_motes()
	_add_bursts()


func _add_sky() -> void:
	var dome := MeshInstance3D.new()
	dome.name = "sky"
	var m := SphereMesh.new()
	m.radius = DOME_RADIUS
	m.height = DOME_RADIUS * 2.0
	m.radial_segments = 48
	m.rings = 24
	dome.mesh = m
	dome.position = CAMERA
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dome.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	dome.custom_aabb = AABB(Vector3(-1, -1, -1) * DOME_RADIUS, Vector3(2, 2, 2) * DOME_RADIUS)
	_sky = _shader("bloom_sky")
	var d := _d
	for k in ["sky_top:top_col", "sky_mid:mid_col", "sky_horizon:horizon_col", "below:below_col", "sky_sun:sun_col",
			"sun_disc:sun_disc", "sun_glow:sun_glow"]:
		var kv: PackedStringArray = k.split(":")
		_sky.set_shader_parameter(kv[1], d[kv[0]])
	_sky.set_shader_parameter("sun_dir", (d["sun_dir"] as Vector3).normalized())
	for k in ["sun_size", "moon", "moon_size", "stars", "clouds", "cloud_col", "cloud_lit", "cloud_scale", "storm",
			"storm_col", "storm_lit", "aurora", "aurora_low", "aurora_high", "rainbow", "rainbow_radius", "eye", "eye_col",
			"eye_size"]:
		if d.has(k):
			_sky.set_shader_parameter(k, d[k])
	if d.has("eye_dir"):
		_sky.set_shader_parameter("eye_dir", (d["eye_dir"] as Vector3).normalized())
	if d.has("rainbow_dir"):
		_sky.set_shader_parameter("rainbow_dir", (d["rainbow_dir"] as Vector3).normalized())
	if d.has("moon_from"):
		_sky.set_shader_parameter("moon_dir", (d["moon_from"] as Vector3).normalized())
	if d.has("burst"):
		_sky.set_shader_parameter("glow_col", d["burst"]["sky"])
	dome.material_override = _sky
	add_child(dome)


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	_clocked.append(m)
	return m


## Swaps the named materials for the backdrop shaders; only the framing in front (fg_*) casts shadows.
func _dress(root: Node3D) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if nm.begins_with("fg") else \
				GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			mi.set_surface_override_material(i, _material_for(mn, src))


func _glow(col: Color, energy: float) -> ShaderMaterial:
	var g := _shader("bloom_glow")
	g.set_shader_parameter("color", col)
	g.set_shader_parameter("energy", energy)
	return g


func _material_for(mn: String, src: Material) -> Material:
	if _mats.has(mn):
		return _mats[mn]
	var m: Material = null
	var night: bool = _d["night"]
	match mn:
		"water", "ice", "pool":
			var w := _shader("bloom_water")
			var wd: Dictionary = _d["water"]
			w.set_shader_parameter("deep_col", wd.get("deep", Color("#103030")))
			w.set_shader_parameter("shallow_col", wd.get("shallow", Color("#304030")))
			w.set_shader_parameter("sky_col", wd.get("sky", Color("#a0c0d0")))
			if mn == "ice":
				w.set_shader_parameter("ice", 1.0)
				w.set_shader_parameter("frost_col", Color("#c8d8f8"))
			elif mn == "pool":
				w.set_shader_parameter("glow", 1.6)
				w.set_shader_parameter("glow_col", wd.get("glow", Color("#3ae8ff")))
				w.set_shader_parameter("ripple", 0.5)
				w.set_shader_parameter("glints", 0.3)
				w.set_shader_parameter("flow", Vector2(0.1, 0.05))
			m = w
		"falls":
			m = _shader("bloom_falls")
		"beam":
			var b := _shader("bloom_beam")
			var bd: Array = _d.get("beam", [Color.WHITE, 0.2])
			b.set_shader_parameter("color", bd[0])
			b.set_shader_parameter("strength", bd[1])
			m = b
		"mist":
			var s := _shader("bloom_mist")
			var md: Array = _d.get("mist", [0.4, 1.0])
			s.set_shader_parameter("density", md[0])
			s.set_shader_parameter("brightness", md[1])
			m = s
		"cloud":
			var c := _shader("bloom_cloud")
			c.set_shader_parameter("rim_col", _d.get("cloud_rim", Color("#fff0e0")))
			m = c
		"crystal":
			m = _shader("bloom_crystal")
		"lantern_glow":
			var g := _glow(Color(1.0, 0.72, 0.38), 3.0)
			g.set_shader_parameter("flicker", 0.18)
			g.set_shader_parameter("cell", 0.5)
			m = g
		"window_glow":
			var g := _glow(Color(1.0, 0.7, 0.38), 2.2)
			g.set_shader_parameter("variety", 0.4)
			g.set_shader_parameter("flicker", 0.05)
			m = g
		"door_glow", "lamp_glow":
			var g := _glow(Color(1.0, 0.75, 0.42), 3.0)
			g.set_shader_parameter("flicker", 0.1)
			m = g
		"glowcap_glow":
			var g := _glow(Color.WHITE, 1.5)
			g.set_shader_parameter("pulse", 0.25)
			g.set_shader_parameter("rim", 0.35)
			g.set_shader_parameter("cell", 0.7)
			m = g
		"dot_glow":
			var g := _glow(Color.WHITE, 3.5)
			g.set_shader_parameter("pulse", 0.3)
			g.set_shader_parameter("cell", 0.3)
			m = g
		"glowworm_glow":
			var g := _glow(Color.WHITE, 4.0)
			g.set_shader_parameter("twinkle", 0.9)
			g.set_shader_parameter("cell", 0.25)
			m = g
		"magic_glow":
			var g := _glow(Color(0.85, 0.45, 1.0), 4.5)
			g.set_shader_parameter("pulse", 0.4)
			g.set_shader_parameter("pulse_speed", 1.3)
			m = g
		"reflect_glow":
			var r := _shader("bloom_reflect")
			r.set_shader_parameter("color", Color(1.0, 0.8, 0.5))
			r.set_shader_parameter("ripple", 0.25 if _d["water"].get("ice", false) else 1.0)
			m = r
		_:
			if mn.contains("sway"):
				var s := _shader("bloom_sway")
				if mn.begins_with("flower") or mn.begins_with("blossom"):
					s.set_shader_parameter("amp", 0.012)
					s.set_shader_parameter("rough", 0.6)
					s.set_shader_parameter("self_light", 0.12 if night else 0.04)
				else:
					s.set_shader_parameter("snow_glow", _d.get("snow_glow", 0.0))
				if mn.begins_with("grass"):
					s.set_shader_parameter("amp", 0.12)
					s.set_shader_parameter("speed", 1.6)
				m = s
			elif src is BaseMaterial3D:
				# the colour lives in the vertex colours (the importer does not always flag it)
				var sm := (src as BaseMaterial3D).duplicate() as BaseMaterial3D
				sm.vertex_color_use_as_albedo = true
				sm.vertex_color_is_srgb = false
				if mn == "cap":
					sm.roughness = 0.35
					sm.metallic_specular = 0.6
				elif mn == "snow":
					sm.roughness = 0.75
					sm.metallic_specular = 0.4
					sm.rim_enabled = true
					sm.rim = 0.4
					sm.rim_tint = 0.6
				elif mn == "roof":
					sm.roughness = 0.45
					sm.metallic_specular = 0.6
				m = sm
			else:
				m = src
	_mats[mn] = m
	return m


## The animated nodes and the light empties the Blender script names.
func _collect(root: Node3D) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 33100 + theme
	var glow_col: Color = _d.get("glow_light", Color("#5af0d0"))
	for n in root.find_children("*", "Node3D", true, false):
		var node := n as Node3D
		var nm := String(node.name)
		if nm.begins_with("float_"):
			_float.append([node, node.transform, 0.25 + 0.2 * rng.randf(), 0.35 + 0.2 * rng.randf(), rng.randf() * TAU])
		elif nm.begins_with("drift_"):
			_drift.append([node, node.transform, 3.0 + 3.0 * rng.randf(), 0.02 + 0.015 * rng.randf(), rng.randf() * TAU])
		elif nm.begins_with("swing_"):
			_swing.append([node, node.transform, 0.06 + 0.04 * rng.randf(), 1.1 + 0.4 * rng.randf(), rng.randf() * TAU])
		elif nm.begins_with("light_"):
			var l := OmniLight3D.new()
			l.shadow_enabled = false
			var mode := 0
			if nm.begins_with("light_warm"):
				l.light_color = Color(1.0, 0.66, 0.34)
				l.light_energy = 2.2
				l.omni_range = 7.0
				mode = 1
			elif nm.begins_with("light_cool"):
				l.light_color = Color(0.45, 0.85, 1.0)
				l.light_energy = 2.6
				l.omni_range = 12.0
				mode = 2
			elif nm.begins_with("light_magic"):
				l.light_color = Color(0.75, 0.4, 1.0)
				l.light_energy = 3.0
				l.omni_range = 14.0
				mode = 2
			else:
				l.light_color = glow_col
				l.light_energy = 2.0
				l.omni_range = 9.0
				mode = 2
			l.omni_attenuation = 1.3
			node.add_child(l)
			_lights.append([l, l.light_energy, mode, rng.randf() * TAU])
	_pop_light = OmniLight3D.new()
	_pop_light.name = "pop_light"
	_pop_light.shadow_enabled = false
	_pop_light.omni_range = 5.0
	_pop_light.light_energy = 0.0
	_pop_light.visible = false
	add_child(_pop_light)
	if _d.has("lightning"):
		_bolt_light = OmniLight3D.new()
		_bolt_light.name = "lightning"
		_bolt_light.shadow_enabled = false
		_bolt_light.omni_range = 260.0
		_bolt_light.omni_attenuation = 0.5
		_bolt_light.light_color = Color(0.78, 0.8, 1.0)
		_bolt_light.light_energy = 0.0
		_bolt_light.visible = false
		add_child(_bolt_light)


## The motes: one MultiMesh per group, worked out on the GPU (bloom_mote.gdshaderinc).
func _add_motes() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 33200 + theme
	var anchors := {}
	for n in find_children("*", "Node3D", true, false):
		var nm := String(n.name)
		for prefix in ["butterfly_", "firefly_", "petal_", "sparkle_", "wisp_"]:
			if nm.begins_with(prefix):
				var list: Array = anchors.get(prefix, [])
				list.append(_local_pos(n as Node3D))
				anchors[prefix] = list
	var gi := 0
	for g in _d["motes"]:
		var homes: Array = []
		var count: int = g["count"]
		if g.has("box"):
			var b: Array = g["box"]
			for i in count:
				homes.append(Vector3(rng.randf_range(b[0], b[1]), rng.randf_range(b[2], b[3]), rng.randf_range(b[5], b[4])))
		else:
			var spread: float = g["spread"]
			for a in anchors.get(g["at"], []):
				for i in count:
					homes.append((a as Vector3) + Vector3(rng.randf_range(-spread, spread), rng.randf_range(-spread, spread) * 0.5,
							rng.randf_range(-spread, spread) * 0.6))
		if homes.is_empty():
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.use_custom_data = true
		var q := QuadMesh.new()
		q.size = Vector2(2, 2)
		mm.mesh = q
		mm.instance_count = homes.size()
		var sz: Array = g["size"]
		var pr: Array = g["period"]
		var cols: Array = g["colors"]
		for i in homes.size():
			mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * rng.randf_range(sz[0], sz[1])), homes[i]))
			mm.set_instance_color(i, cols[rng.randi() % cols.size()])
			mm.set_instance_custom_data(i, Color(rng.randf(), rng.randf_range(pr[0], pr[1]), rng.randf(), 0.0))
		var mi := MultiMeshInstance3D.new()
		mi.name = "motes_%d" % gi
		mi.multimesh = mm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		mi.custom_aabb = AABB(Vector3(-120, -30, -220), Vector3(260, 160, 240))
		var m := _shader("bloom_mote_glow" if g.get("glow", false) else "bloom_mote")
		m.set_shader_parameter("kind", g["kind"])
		m.set_shader_parameter("span", g["span"])
		m.set_shader_parameter("wind", g.get("wind", Vector3.ZERO))
		m.set_shader_parameter("energy", g.get("energy", 1.0))
		mi.material_override = m
		add_child(mi)
		gi += 1


func _add_bursts() -> void:
	_mm = MultiMesh.new()
	_mm.transform_format = MultiMesh.TRANSFORM_3D
	_mm.use_colors = true
	_mm.use_custom_data = true
	_mm.mesh = _spark_mesh()
	_mm.instance_count = POOL
	for i in POOL:
		_mm.set_instance_transform(i, Transform3D(Basis(), Vector3(10, -50, -10)))
		_mm.set_instance_color(i, Color.WHITE)
		_mm.set_instance_custom_data(i, Color(-1000.0, 0.0, 0.0, 0.0))
	var mi := MultiMeshInstance3D.new()
	mi.name = "bursts"
	mi.multimesh = _mm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	mi.custom_aabb = AABB(Vector3(-60, -30, -80), Vector3(140, 100, 120))
	mi.material_override = _shader("bloom_burst")
	add_child(mi)


## SPARKS quads, each carrying its direction on the unit sphere (spread evenly, in a shuffled order) and a random
## number in UV2.
func _spark_mesh() -> ArrayMesh:
	var rng := RandomNumberGenerator.new()
	rng.seed = 3333
	var dirs: Array[Vector3] = []
	var golden := PI * (3.0 - sqrt(5.0))
	for k in SPARKS:
		var y := 1.0 - 2.0 * (k + 0.5) / SPARKS
		var r := sqrt(1.0 - y * y)
		dirs.append(Vector3(cos(golden * k) * r, y, sin(golden * k) * r))
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var uv2s := PackedVector2Array()
	var idx := PackedInt32Array()
	var corners := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
	for k in SPARKS:
		var base := verts.size()
		var dv := dirs[k] * (0.9 + 0.2 * rng.randf())
		var u2 := Vector2(rng.randf(), float(k) / SPARKS)
		for c in corners:
			verts.append(dv)
			uvs.append(c)
			uv2s.append(u2)
		idx.append_array([base, base + 1, base + 2, base, base + 2, base + 3])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_TEX_UV2] = uv2s
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	mesh.custom_aabb = AABB(Vector3(-60, -60, -60), Vector3(120, 120, 120))
	return mesh


func _burst(at: Vector3, kind: int, col: Color, spread: float, radius: float, when: float) -> void:
	var b := Basis.from_euler(Vector3(_rng.randf() * TAU, _rng.randf() * TAU, _rng.randf() * TAU))
	_mm.set_instance_transform(_slot, Transform3D(b.scaled(Vector3.ONE * radius), at))
	_mm.set_instance_color(_slot, col)
	_mm.set_instance_custom_data(_slot, Color(when, float(kind), spread, _rng.randf()))
	_slot = (_slot + 1) % POOL


func _level_to_world(xs: float, ys: float, z: float) -> Vector3:
	var k := (CAMERA.z - z) / CAMERA.z
	return Vector3(10.0 + (xs - 10.0) * k, 7.5 + (ys - 7.5) * k, z)


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
	for m in _clocked:
		(m as ShaderMaterial).set_shader_parameter("clock", _t)
	for f in _float:
		var tr: Transform3D = f[1]
		var ph: float = _t * f[3] + f[4]
		tr.origin.y += sin(ph) * f[2]
		tr.basis = tr.basis * Basis(Vector3.BACK, sin(ph * 0.7) * 0.01)
		(f[0] as Node3D).transform = tr
	for f in _drift:
		var tr: Transform3D = f[1]
		tr.origin.x += sin(_t * f[3] + f[4]) * f[2]
		(f[0] as Node3D).transform = tr
	for s in _swing:
		var rest: Transform3D = s[1]
		var a: float = sin(_t * s[3] + s[4]) * s[2]
		(s[0] as Node3D).transform = rest * Transform3D(Basis(Vector3.BACK, a), Vector3.ZERO)
	for l in _lights:
		var e: float = l[1]
		match int(l[2]):
			1:
				e *= 0.86 + 0.08 * sin(_t * 11.0 + l[3]) + 0.06 * sin(_t * 23.7 + l[3] * 2.0)
			2:
				e *= 0.85 + 0.15 * sin(_t * 0.8 + l[3])
		(l[0] as OmniLight3D).light_energy = e
	if _d.has("moon_from") and _d.has("moon_rise"):
		var k := smoothstep(0.0, _d["moon_rise"], _t)
		_sky.set_shader_parameter("moon_dir", (_d["moon_from"] as Vector3).lerp(_d["moon_to"], k).normalized())
	_update_storm()
	var ga := _t - _glow_t
	var gw := 0.25 * exp(-ga * 0.9) * smoothstep(0.0, 0.3, ga) if ga >= 0.0 else 0.0
	_sky.set_shader_parameter("glow", Vector4(0.0, 0.35, -0.94, gw))
	if _pop_light:
		var age := _t - _pop_t
		var e := 3.0 * exp(-age * 7.0) if age >= 0.0 else 0.0
		_pop_light.light_energy = e
		_pop_light.visible = e > 0.03


## Thorn Tower: a bolt now and then (the sky draws it), the scene lit by its flash; sheet lightning between.
func _update_storm() -> void:
	if not _d.has("lightning"):
		return
	var every: Array = _d["lightning"]
	if _t >= _next_bolt:
		_bolt_t = _next_bolt
		var az := _rng.randf_range(-0.45, 0.45)
		var dir := Vector3(sin(az), _rng.randf_range(0.32, 0.45), -cos(az))
		_sky.set_shader_parameter("bolt", Vector4(dir.x, dir.y, dir.z, _bolt_t))
		_sky.set_shader_parameter("bolt_seed", _rng.randf() * 10.0)
		if _bolt_light:
			_bolt_light.position = CAMERA + Vector3(dir.x, 0.0, dir.z).normalized() * 120.0 + Vector3(0, 60, 0)
		_next_bolt += _rng.randf_range(every[0], every[1])
		_sheet_t = _t + _rng.randf_range(1.5, 3.0)
	var age := _t - _bolt_t
	var env := 0.0
	if age >= 0.0 and age < 0.8:
		env = exp(-age * 14.0) + 0.8 * (exp(-(age - 0.13) * 10.0) if age >= 0.13 else 0.0) + \
				0.5 * (exp(-(age - 0.32) * 12.0) if age >= 0.32 else 0.0)
	var sa := _t - _sheet_t
	var sheet := 0.35 * exp(-sa * 9.0) if sa >= 0.0 and sa < 0.6 else 0.0
	_sky.set_shader_parameter("flash", clampf(env * 0.6 + sheet, 0.0, 1.0))
	if _bolt_light:
		_bolt_light.light_energy = env * 3.5 + sheet * 1.5
		_bolt_light.visible = _bolt_light.light_energy > 0.02
