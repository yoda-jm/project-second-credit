class_name FuseBackdrop
extends Node3D
## The festival nights behind the Fuseflight arena, one per stage theme (0-4, see stages/festival.fuse): Lantern
## Harbour, Pagoda Steps, Lighthouse Rocks, Windmill Fair, Comet Square. build(theme) loads
## art/backdrops/backdrop_<theme>.glb (tools/blender/fuseflight_backdrops.py), swaps the materials the Blender script
## marks by name for the game's shaders (water, lanterns, windows, string bulbs, flames, the lighthouse beam, the
## light streaks on the water, foliage in the breeze), adds the sky dome (stars, moon, the comet, the haze round each
## firework), the omni lights the script marks with empties, the risers (sky lanterns, bonfire sparks, petals) and
## the fireworks: rockets climbing and bursting as peonies, willows, rings, chrysanthemums, glitter and palms, with
## now and then a big shell, mirrored on the water where there is water, each burst briefly lighting the scene.
## Everything runs on the node's own clock in _process (fixed-step safe, deterministic: the shows are seeded per
## theme), and the sparks are worked out on the GPU from each burst's start time.
##
## The game reacts through celebrate() (the finale: a volley of big shells, for a stage clear) and flash(pos) (a
## small crackling pop at pos in the play space, with a brief light: a firework collected).
## The view owns the WorldEnvironment and the moonlight: it reads environment_for(theme) (PopBackdrop's keys) and
## may call make_environment() and setup_sun() with that dictionary.
##
## Space: the arena is x 0..16, y 0..12 on z = 0, the camera near (8, 6, 21), fov 38 (Camera3D.far must reach the sky
## dome: 260 or more). The foreground strip's top is exactly y = 0 for z -2..+3 (it runs on to z = +6); the scenery
## fills z -2 .. -200. What lies behind the arena's middle is kept dark; the bright landmarks are at the sides and the
## fireworks burst high (above the arena's upper rows or beyond its ends).

const GLB := "res://games/fuseflight/art/backdrops/backdrop_%d.glb"
const SH := "res://games/fuseflight/shaders/"
const CAMERA := Vector3(8.0, 6.0, 21.0)
const DOME_RADIUS := 230.0
const POOL := 56               ## burst and rocket slots (a ring: the oldest is reused)
const SPARKS := 160            ## spark quads per burst (the fireworks shader counts on it)
const WHEEL_SPEED := 0.075     ## rad/s
const CAROUSEL_SPEED := 0.42
const SAILS_SPEED := 0.35
const BEAM_SPEED := 0.5
const FW_COLORS := [Color(1.0, 0.22, 0.16), Color(1.0, 0.72, 0.28), Color(0.3, 1.0, 0.42), Color(0.3, 0.5, 1.0),
		Color(0.78, 0.36, 1.0), Color(1.0, 0.4, 0.68), Color(0.88, 0.92, 1.0), Color(1.0, 0.48, 0.12),
		Color(0.3, 0.92, 1.0)]

## Per theme: the sky (the dome is also where the fog ends), the environment the view applies, the water (level
## and colours; none where there is no water), and the fireworks: a launch every `every` seconds on average, bursting
## in a zone given in arena units (x0, x1, y0, y1: where the burst shows on the arena plane) at depths z, rockets
## rising from launch_y; kinds: weights of peony, willow, ring, chrysanthemum, glitter, crackle, palm; palette:
## indices into FW_COLORS; big: the share of big shells.
const THEMES := [
	{   # 0 Lantern Harbour: dusk turning to night, the last light low on the left over the sea
		"name": "Lantern Harbour",
		"sky_top": Color("#060a22"), "sky_mid": Color("#1c1c4a"), "sky_horizon": Color("#5a3a5e"),
		"below": Color("#0c0c1e"), "sea": 1.0,
		"dusk_dir": Vector3(-0.85, 0.0, -0.5), "dusk_col": Color("#e0704a"), "dusk": 0.8,
		"stars": 0.45, "moon": 0.0, "moon_dir": Vector3(0.5, 0.4, -0.75), "comet": 0.0,
		"clouds": 0.28, "cloud_col": Color("#151430"), "cloud_lit": Color("#5a2c40"),
		"ground_horizon": Color("#1c1a34"), "ground_bottom": Color("#0a0a16"),
		"sun_color": Color("#b8b0ff"), "sun_rotation": Vector3(-30, -50, 0), "sun_energy": 0.35,
		"ambient_color": Color("#40385e"), "ambient_energy": 0.55,
		"fog_color": Color("#1c1838"), "fog_density": 0.0045, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.9, "glow_threshold": 0.95, "saturation": 1.1, "contrast": 1.05,
		"water": {"level": -1.1, "deep": Color("#05060e"), "far": Color("#141330"), "sky": Color("#3a2a50"),
				"shallow": Color("#0a0e18")},
		"fw": {"every": 1.7, "zone": [-4.0, 20.0, 8.6, 13.4], "z": [-75.0, -140.0], "launch_y": -1.1,
				"kinds": [4, 2, 2, 3, 1, 1, 1], "palette": [0, 1, 2, 3, 4, 5, 6], "big": 0.12, "energy": 3.2},
	},
	{   # 1 Pagoda Steps: deep blue night, a high moon on the left
		"name": "Pagoda Steps",
		"sky_top": Color("#040820"), "sky_mid": Color("#0c1840"), "sky_horizon": Color("#26305e"),
		"below": Color("#0a0e1a"), "sea": 0.0,
		"dusk_dir": Vector3(0.6, 0.0, -0.8), "dusk_col": Color("#6a4a8a"), "dusk": 0.3,
		"stars": 0.8, "moon": 1.0, "moon_dir": Vector3(-0.42, 0.5, -0.76), "comet": 0.0,
		"clouds": 0.18, "cloud_col": Color("#0e1430"), "cloud_lit": Color("#3a2a3a"),
		"ground_horizon": Color("#141c38"), "ground_bottom": Color("#080a16"),
		"sun_color": Color("#b0c0ff"), "sun_rotation": Vector3(-40, -35, 0), "sun_energy": 0.45,
		"ambient_color": Color("#33406e"), "ambient_energy": 0.55,
		"fog_color": Color("#121a38"), "fog_density": 0.006, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.9, "glow_threshold": 0.95, "saturation": 1.1, "contrast": 1.05,
		"water": {},
		"fw": {"every": 1.9, "zone": [-3.0, 19.0, 9.0, 13.4], "z": [-110.0, -160.0], "launch_y": 14.0,
				"kinds": [4, 3, 2, 3, 1, 1, 1], "palette": [0, 1, 5, 6, 7, 4], "big": 0.1, "energy": 3.0},
	},
	{   # 2 Lighthouse Rocks: clear starry night, the moon low on the right over the sea
		"name": "Lighthouse Rocks",
		"sky_top": Color("#02040e"), "sky_mid": Color("#0a1430"), "sky_horizon": Color("#1e2a50"),
		"below": Color("#060a16"), "sea": 1.0,
		"dusk_dir": Vector3(-0.7, 0.0, -0.7), "dusk_col": Color("#3a3060"), "dusk": 0.25,
		"stars": 1.0, "moon": 1.0, "moon_dir": Vector3(0.4, 0.2, -0.9), "comet": 0.0,
		"clouds": 0.1, "cloud_col": Color("#0a1024"), "cloud_lit": Color("#2a2030"),
		"ground_horizon": Color("#141c36"), "ground_bottom": Color("#060812"),
		"sun_color": Color("#b4c4ff"), "sun_rotation": Vector3(-22, 25, 0), "sun_energy": 0.5,
		"ambient_color": Color("#2e3c66"), "ambient_energy": 0.55,
		"fog_color": Color("#101830"), "fog_density": 0.004, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.9, "glow_threshold": 0.95, "saturation": 1.08, "contrast": 1.05,
		"water": {"level": -1.0, "deep": Color("#03060e"), "far": Color("#0e1630"), "sky": Color("#2a3460"),
				"shallow": Color("#0c1820")},
		"fw": {"every": 1.9, "zone": [-4.0, 11.0, 8.8, 13.4], "z": [-70.0, -130.0], "launch_y": 6.0,
				"kinds": [4, 2, 3, 2, 2, 1, 2], "palette": [0, 2, 3, 6, 8, 1], "big": 0.12, "energy": 3.0},
	},
	{   # 3 Windmill Fair: a warm summer night, a haze of light over the fair
		"name": "Windmill Fair",
		"sky_top": Color("#060a1e"), "sky_mid": Color("#141a40"), "sky_horizon": Color("#3a3058"),
		"below": Color("#0c0e18"), "sea": 0.0,
		"dusk_dir": Vector3(0.2, 0.0, -1.0), "dusk_col": Color("#7a4a5a"), "dusk": 0.45,
		"stars": 0.6, "moon": 1.0, "moon_dir": Vector3(0.55, 0.45, -0.7), "comet": 0.0,
		"clouds": 0.22, "cloud_col": Color("#12142c"), "cloud_lit": Color("#4a2e3a"),
		"ground_horizon": Color("#1c1a34"), "ground_bottom": Color("#0a0a14"),
		"sun_color": Color("#b8b8ff"), "sun_rotation": Vector3(-35, 30, 0), "sun_energy": 0.4,
		"ambient_color": Color("#3a3a62"), "ambient_energy": 0.55,
		"fog_color": Color("#1a1834"), "fog_density": 0.005, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.9, "glow_threshold": 0.95, "saturation": 1.12, "contrast": 1.05,
		"water": {},
		"fw": {"every": 1.6, "zone": [-3.0, 19.0, 9.0, 13.4], "z": [-90.0, -150.0], "launch_y": 4.0,
				"kinds": [4, 2, 3, 2, 2, 1, 2], "palette": [0, 1, 2, 3, 4, 5, 8], "big": 0.14, "energy": 3.1},
	},
	{   # 4 Comet Square: the comet over the old town, the grand finale
		"name": "Comet Square",
		"sky_top": Color("#03051a"), "sky_mid": Color("#0c1238"), "sky_horizon": Color("#2a2a54"),
		"below": Color("#0a0a14"), "sea": 0.0,
		"dusk_dir": Vector3(0.8, 0.0, -0.6), "dusk_col": Color("#4a3a70"), "dusk": 0.3,
		"stars": 0.9, "moon": 0.0, "moon_dir": Vector3(0.5, 0.4, -0.75),
		"comet": 1.0, "comet_dir": Vector3(0.25, 0.2, -0.95), "comet_tail": Vector3(-0.95, 0.3, 0.05),
		"clouds": 0.12, "cloud_col": Color("#0c1028"), "cloud_lit": Color("#3a2c40"),
		"ground_horizon": Color("#161a36"), "ground_bottom": Color("#080a14"),
		"sun_color": Color("#c0c8ff"), "sun_rotation": Vector3(-40, -20, 0), "sun_energy": 0.4,
		"ambient_color": Color("#363e6a"), "ambient_energy": 0.55,
		"fog_color": Color("#141a36"), "fog_density": 0.0055, "fog_sun_scatter": 0.0,
		"exposure": 1.05, "glow_intensity": 0.95, "glow_threshold": 0.95, "saturation": 1.1, "contrast": 1.06,
		"water": {},
		"fw": {"every": 1.15, "zone": [-3.0, 19.0, 9.2, 13.4], "z": [-90.0, -150.0], "launch_y": 10.0,
				"kinds": [4, 3, 2, 3, 2, 1, 2], "palette": [0, 1, 2, 3, 4, 5, 6, 7, 8], "big": 0.2, "energy": 3.3},
	},
]

var theme := 0
var _t := 0.0
var _mats := {}
var _sky: ShaderMaterial
var _bob: Array = []        ## [node, rest transform, height, rate, phase, roll]
var _spin: Array = []       ## [node, rest transform, local axis, rad/s]
var _wheel: Node3D
var _wheel_rest: Transform3D
var _gondolas: Array = []   ## [node, pin position]
var _lights: Array = []     ## [OmniLight3D, base energy, flicker]
# fireworks
var _fw: Dictionary = {}
var _rng := RandomNumberGenerator.new()
var _mm: MultiMesh
var _fw_mats: Array = []    ## the fireworks' materials (direct, mirrored): both read `clock`
var _slot := 0
var _next_launch := 0.5
var _pending: Array = []    ## bursts waiting for their rocket: [time, position, kind, colour, hue2, radius, seed, big]
var _recent: Array = []     ## [time, position, colour, radius, strength]: the sky's haze and the flash lights
var _flash_lights: Array = []  ## [OmniLight3D, start time, peak energy]
var _flash_slot := 0
var _near_light: OmniLight3D
var _near_t := -10.0
var _risers: Array = []     ## the risers' materials (they read `clock`)


## The environment the view applies for a theme. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color,
## for a ProceduralSkyMaterial: ambient and reflections; the dome covers the background), sun_color (Color: the
## moonlight), sun_rotation (Vector3, degrees, for the DirectionalLight3D), sun_energy, ambient_color,
## ambient_energy, fog_color, fog_density (exponential fog), fog_sun_scatter, exposure, glow_intensity,
## glow_threshold, saturation, contrast, night (always true: keep the arena's own lights on), name, water_level
## (the water's height, or NAN where there is none).
func environment_for(t: int) -> Dictionary:
	var d: Dictionary = THEMES[clampi(t, 0, THEMES.size() - 1)]
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_rotation", "sun_energy",
			"ambient_color", "ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure",
			"glow_intensity", "glow_threshold", "saturation", "contrast", "name"]:
		out[k] = d[k]
	out["night"] = true
	var w: Dictionary = d["water"]
	out["water_level"] = w["level"] if w.has("level") else NAN
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
	env.fog_enabled = true
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


## The moonlight.
static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 50.0


## The finale for a stage clear: a volley of rockets, then big shells all across the sky and a glittering curtain.
func celebrate() -> void:
	if _mm == null:
		return
	var p: Array = _fw["palette"]
	for i in 6:
		_launch(_t + i * 0.12, true)
	for i in 9:
		var xs := lerpf(-2.0, 18.0, (i + 0.5) / 9.0) + _rng.randf_range(-0.8, 0.8)
		var ys := _rng.randf_range(9.6, 12.8)
		var z := _rng.randf_range(-80.0, -120.0)
		var kind: int = [0, 3, 2, 0, 1, 3, 0, 2, 3][i]
		var col: Color = FW_COLORS[p[_rng.randi() % p.size()]]
		_pending.append([_t + 0.35 + i * 0.16 + _rng.randf() * 0.1, _arena_to_world(xs, ys, z), kind, col, _rng.randf(),
				_rng.randf_range(3.0, 4.2) * (CAMERA.z - z) / CAMERA.z, _rng.randf(), true])
	for i in 4:
		var z := -95.0
		_pending.append([_t + 1.9 + i * 0.12, _arena_to_world(1.0 + i * 4.7, 12.6, z), 4, Color(1.0, 0.85, 0.55), 0.12,
				3.6 * (CAMERA.z - z) / CAMERA.z, _rng.randf(), true])
	_pending.append([_t + 2.4, _arena_to_world(8.0, 12.0, -110.0), 1, Color(1.0, 0.75, 0.35), 0.1,
			5.5 * (CAMERA.z + 110.0) / CAMERA.z, 0.5, true])


## A small crackling pop at pos (play space, e.g. where a firework was collected) and a brief warm light there.
func flash(pos: Vector3) -> void:
	if _mm == null:
		return
	var p := pos + Vector3(0, 0, -0.4)
	_burst(p, 5, Color(1.0, 0.8, 0.4), _rng.randf(), 1.1, _rng.randf(), false)
	if _near_light:
		_near_light.position = pos + Vector3(0, 0.3, 1.2)
		_near_t = _t


func build(t: int) -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	theme = clampi(t, 0, THEMES.size() - 1)
	_t = 0.0
	_mats.clear()
	_bob.clear()
	_spin.clear()
	_gondolas.clear()
	_lights.clear()
	_wheel = null
	_pending.clear()
	_recent.clear()
	_flash_lights.clear()
	_risers.clear()
	_fw_mats.clear()
	_slot = 0
	_next_launch = 0.4
	var d: Dictionary = THEMES[theme]
	_fw = d["fw"]
	_rng.seed = 280000 + theme * 977
	_add_sky(d)
	var packed := load(GLB % theme) as PackedScene
	if packed == null:
		push_error("FuseBackdrop: missing %s" % (GLB % theme))
		return
	var root := packed.instantiate() as Node3D
	root.name = "diorama"
	add_child(root)
	_dress(root, d)
	_collect(root)
	_add_fireworks(d)
	_add_risers()
	# a show already under way: a few bursts in the sky at the start
	for i in 3:
		_launch(-1.6 + i * 0.5, false)


func _add_sky(d: Dictionary) -> void:
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
	_sky = _shader("fuse_sky")
	for k in ["sky_top:top_col", "sky_mid:mid_col", "sky_horizon:horizon_col", "below:below_col", "sea:sea",
			"dusk_col:dusk_col", "dusk:dusk", "stars:stars", "moon:moon", "comet:comet", "clouds:clouds",
			"cloud_col:cloud_col", "cloud_lit:cloud_lit"]:
		var kv: PackedStringArray = k.split(":")
		_sky.set_shader_parameter(kv[1], d[kv[0]])
	_sky.set_shader_parameter("dusk_dir", (d["dusk_dir"] as Vector3).normalized())
	_sky.set_shader_parameter("moon_dir", (d["moon_dir"] as Vector3).normalized())
	if d.has("comet_dir"):
		_sky.set_shader_parameter("comet_dir", (d["comet_dir"] as Vector3).normalized())
		_sky.set_shader_parameter("comet_tail", d["comet_tail"])
	dome.material_override = _sky
	add_child(dome)


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	return m


## Swaps the named materials for the backdrop shaders; only the foreground strip casts shadows.
func _dress(root: Node3D, d: Dictionary) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if nm.begins_with("fg") else \
				GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			mi.set_surface_override_material(i, _material_for(mn, src, d))


func _glow(col: Color, energy: float) -> ShaderMaterial:
	var g := _shader("fuse_glow")
	g.set_shader_parameter("color", col)
	g.set_shader_parameter("energy", energy)
	return g


func _material_for(mn: String, src: Material, d: Dictionary) -> Material:
	if _mats.has(mn):
		return _mats[mn]
	var m: Material = null
	match mn:
		"water":
			var w := _shader("fuse_water")
			var wd: Dictionary = d["water"]
			if wd.is_empty():   # the fountain in the square
				wd = {"deep": Color("#060810"), "far": Color("#101428"), "sky": Color("#2a2a50"), "shallow": Color("#0c1018")}
				w.set_shader_parameter("wave_height", 0.0)
				w.set_shader_parameter("ripple", 1.6)
			w.set_shader_parameter("deep_col", wd["deep"])
			w.set_shader_parameter("far_col", wd["far"])
			w.set_shader_parameter("sky_col", wd["sky"])
			w.set_shader_parameter("shallow_col", wd["shallow"])
			m = w
		"lantern_glow":
			var g := _glow(Color.WHITE, 2.4)
			g.set_shader_parameter("paper", 1.0)
			g.set_shader_parameter("flicker", 0.12)
			g.set_shader_parameter("variety", 0.3)
			g.set_shader_parameter("cell", 0.6)
			m = g
		"window_glow":
			var g := _glow(Color(1.0, 0.68, 0.36), 1.9)
			g.set_shader_parameter("twinkle", 0.25)
			g.set_shader_parameter("variety", 0.6)
			g.set_shader_parameter("cell", 0.8)
			m = g
		"stall_glow":
			var g := _glow(Color(1.0, 0.7, 0.4), 1.25)
			g.set_shader_parameter("variety", 0.4)
			g.set_shader_parameter("flicker", 0.05)
			g.set_shader_parameter("cell", 2.0)
			m = g
		"lamp_glow":
			var g := _glow(Color(1.0, 0.8, 0.52), 3.2)
			g.set_shader_parameter("flicker", 0.04)
			g.set_shader_parameter("cell", 2.0)
			m = g
		"bulb_glow":
			var g := _glow(Color.WHITE, 3.4)
			g.set_shader_parameter("hues", 1.0)
			g.set_shader_parameter("chase", 0.6)
			g.set_shader_parameter("cell", 0.3)
			m = g
		"warmbulb_glow":
			var g := _glow(Color(1.0, 0.8, 0.5), 3.2)
			g.set_shader_parameter("chase", 0.35)
			g.set_shader_parameter("variety", 0.2)
			g.set_shader_parameter("cell", 0.3)
			m = g
		"fire_glow":
			var g := _glow(Color(1.0, 0.42, 0.1), 3.0)
			g.set_shader_parameter("flicker", 0.9)
			g.set_shader_parameter("cell", 0.5)
			m = g
		"flame_glow":
			m = _shader("fuse_flame")
			(m as ShaderMaterial).set_shader_parameter("energy", 1.15)
		"beam_glow":
			m = _shader("fuse_beam")
		"beacon_glow":
			var g := _glow(Color(1.0, 0.2, 0.12), 5.0)
			g.set_shader_parameter("blink", 1.0)
			g.set_shader_parameter("cell", 4.0)
			m = g
		"clock_glow":
			m = _glow(Color(1.0, 0.9, 0.7), 1.3)
		"lens_glow":
			var g := _glow(Color(1.0, 0.95, 0.82), 7.0)
			m = g
		"reflect_glow":
			var r := _shader("fuse_reflect")
			r.set_shader_parameter("strength", 1.0)
			m = r
		_:
			if mn.contains("sway"):
				var s := _shader("fuse_sway")
				if mn.begins_with("blossom"):
					s.set_shader_parameter("amp", 0.012)
					s.set_shader_parameter("self_light", 0.03)
				m = s
			elif src is BaseMaterial3D:
				# the colour lives in the vertex colours (the importer does not always flag it)
				var sm := (src as BaseMaterial3D).duplicate() as BaseMaterial3D
				sm.vertex_color_use_as_albedo = true
				if mn == "roof":
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
	rng.seed = 28100 + theme
	for n in root.find_children("*", "Node3D", true, false):
		var node := n as Node3D
		var nm := String(node.name)
		if nm.begins_with("boat_"):
			_bob.append([node, node.transform, 0.07, 0.8 + 0.4 * rng.randf(), rng.randf() * TAU, 0.03])
		elif nm == "beam":
			_spin.append([node, node.transform, Vector3.UP, BEAM_SPEED])
		elif nm == "carousel":
			_spin.append([node, node.transform, Vector3.UP, CAROUSEL_SPEED])
		elif nm.begins_with("sails_"):
			_spin.append([node, node.transform, Vector3.BACK, -SAILS_SPEED * (0.8 + 0.4 * rng.randf())])
		elif nm == "wheel":
			_wheel = node
			_wheel_rest = node.transform
		elif nm.begins_with("gondola_"):
			_gondolas.append([node, node.position])
		elif nm.begins_with("light_"):
			var l := OmniLight3D.new()
			l.shadow_enabled = false
			var flick := 0.0
			if nm.begins_with("light_fire"):
				l.light_color = Color(1.0, 0.5, 0.2)
				l.light_energy = 5.0
				l.omni_range = 18.0
				flick = 1.0
			elif nm.begins_with("light_cool"):
				l.light_color = Color(0.8, 0.88, 1.0)
				l.light_energy = 2.0
				l.omni_range = 10.0
			else:
				l.light_color = Color(1.0, 0.6, 0.3)
				l.light_energy = 2.2
				l.omni_range = 10.0
			l.omni_attenuation = 1.2
			node.add_child(l)
			_lights.append([l, l.light_energy, flick])


func _add_fireworks(d: Dictionary) -> void:
	_mm = MultiMesh.new()
	_mm.transform_format = MultiMesh.TRANSFORM_3D
	_mm.use_colors = true
	_mm.use_custom_data = true
	_mm.mesh = _spark_mesh()
	_mm.instance_count = POOL
	for i in POOL:
		_mm.set_instance_transform(i, Transform3D(Basis(), Vector3(8, 40, -100)))
		_mm.set_instance_color(i, Color.WHITE)
		_mm.set_instance_custom_data(i, Color(-1000.0, 0.0, 0.0, 0.0))
	var w: Dictionary = d["water"]
	for mirror in ([false, true] if w.has("level") else [false]):
		var mi := MultiMeshInstance3D.new()
		mi.name = "fireworks_reflection" if mirror else "fireworks"
		mi.multimesh = _mm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		mi.custom_aabb = AABB(Vector3(-400, -50, -400), Vector3(800, 400, 800))
		var m := _shader("fuse_firework")
		m.set_shader_parameter("energy", _fw["energy"])
		if mirror:
			m.set_shader_parameter("mirror", 1.0)
			m.set_shader_parameter("water_y", w["level"])
		mi.material_override = m
		_fw_mats.append(m)
		add_child(mi)
	for i in 2:
		var l := OmniLight3D.new()
		l.name = "burst_light_%d" % i
		l.shadow_enabled = false
		l.omni_range = 160.0
		l.omni_attenuation = 0.7
		l.light_energy = 0.0
		l.visible = false
		add_child(l)
		_flash_lights.append([l, -100.0, 0.0])
	_near_light = OmniLight3D.new()
	_near_light.name = "pop_light"
	_near_light.shadow_enabled = false
	_near_light.omni_range = 5.0
	_near_light.light_color = Color(1.0, 0.75, 0.4)
	_near_light.light_energy = 0.0
	_near_light.visible = false
	add_child(_near_light)


## SPARKS quads, each carrying its direction on the unit sphere (spread evenly, in a shuffled order so any run of
## indices points every way), a random number and its index; plus the flash quad.
func _spark_mesh() -> ArrayMesh:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2828
	var dirs: Array[Vector3] = []
	var golden := PI * (3.0 - sqrt(5.0))
	for k in SPARKS:
		var y := 1.0 - 2.0 * (k + 0.5) / SPARKS
		var r := sqrt(1.0 - y * y)
		var a := golden * k
		dirs.append(Vector3(cos(a) * r, y, sin(a) * r))
	for k in range(SPARKS - 1, 0, -1):
		var j := rng.randi_range(0, k)
		var tmp := dirs[k]
		dirs[k] = dirs[j]
		dirs[j] = tmp
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var uv2s := PackedVector2Array()
	var idx := PackedInt32Array()
	var corners := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
	for k in SPARKS + 1:
		var base := verts.size()
		var flash_quad := k == SPARKS
		var dv := Vector3.ZERO if flash_quad else dirs[k] * (0.97 + 0.06 * rng.randf())
		var u2 := Vector2(-1.0, 0.0) if flash_quad else Vector2(rng.randf(), float(k) / SPARKS)
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
	mesh.custom_aabb = AABB(Vector3(-300, -60, -300), Vector3(600, 400, 600))
	return mesh


func _arena_to_world(xs: float, ys: float, z: float) -> Vector3:
	var k := (CAMERA.z - z) / CAMERA.z
	return Vector3(8.0 + (xs - 8.0) * k, 6.0 + (ys - 6.0) * k, z)


func _pick_kind() -> int:
	var w: Array = _fw["kinds"]
	var total := 0.0
	for v in w:
		total += v
	var r := _rng.randf() * total
	for i in w.size():
		r -= w[i]
		if r <= 0.0:
			return i
	return 0


## A rocket now (at time `when`, which may lie in the past for a show already under way) and its burst after it.
func _launch(when: float, big: bool) -> void:
	var zone: Array = _fw["zone"]
	var zr: Array = _fw["z"]
	var z := _rng.randf_range(zr[1], zr[0])
	var xs := _rng.randf_range(zone[0], zone[1])
	var ys := _rng.randf_range(zone[2], zone[3])
	# keep the middle of the arena's upper rows a little quieter: push bursts there higher
	if xs > 4.0 and xs < 12.0:
		ys = maxf(ys, lerpf(zone[2], zone[3], 0.45))
	big = big or _rng.randf() < _fw["big"]
	var kind := _pick_kind()
	if big and kind == 5:
		kind = 0
	var pal: Array = _fw["palette"]
	var col: Color = FW_COLORS[pal[_rng.randi() % pal.size()]]
	var k := (CAMERA.z - z) / CAMERA.z
	var radius := (_rng.randf_range(2.6, 3.4) if big else _rng.randf_range(1.1, 2.0)) * k
	if xs > 3.0 and xs < 13.0:
		radius *= 0.85
	if kind == 5:
		radius *= 0.6
	var at := _arena_to_world(xs, ys, z)
	var from := Vector3(at.x + _rng.randf_range(-0.08, 0.08) * (at.y - _fw["launch_y"]), _fw["launch_y"], z)
	var rise_t := _rng.randf_range(1.0, 1.5) * (1.15 if big else 1.0)
	var seed := _rng.randf()
	_spawn(Transform3D(Basis(Vector3(1, 0, 0), at - from, Vector3(0, 0, 1)), from), Color(1, 0.8, 0.5),
			Color(when, 7.0, rise_t, seed))
	_pending.append([when + rise_t, at, kind, col, _rng.randf(), radius, seed, big])


func _spawn(tr: Transform3D, col: Color, custom: Color) -> void:
	_mm.set_instance_transform(_slot, tr)
	_mm.set_instance_color(_slot, col)
	_mm.set_instance_custom_data(_slot, custom)
	_slot = (_slot + 1) % POOL


func _burst(at: Vector3, kind: int, col: Color, hue2: float, radius: float, seed: float, big: bool,
		when: float = NAN) -> void:
	var t0 := _t if is_nan(when) else when
	var b := Basis.from_euler(Vector3(_rng.randf() * TAU, _rng.randf() * TAU, _rng.randf() * TAU))
	if kind == 2:   # rings face the camera more or less
		b = Basis.looking_at(CAMERA - at, Vector3.UP) * Basis.from_euler(Vector3(_rng.randf_range(-0.9, 0.9),
				_rng.randf_range(-0.9, 0.9), _rng.randf() * TAU))
	_spawn(Transform3D(b.scaled(Vector3.ONE * radius), at), col, Color(t0, float(kind), hue2, seed))
	var strength := 1.0 if big else 0.45
	if kind == 5:
		strength = 0.2 if radius < 3.0 else 0.4
	_recent.push_front([t0, at, col, radius, strength])
	if _recent.size() > 6:
		_recent.resize(6)
	if kind != 5 or big:
		var fl: Array = _flash_lights[_flash_slot]
		_flash_slot = (_flash_slot + 1) % _flash_lights.size()
		var l: OmniLight3D = fl[0]
		l.position = at
		l.light_color = col.lerp(Color.WHITE, 0.3)
		fl[1] = t0
		fl[2] = (8.0 if big else 5.0)


func _add_risers() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 28200 + theme
	var groups := {}   # kind -> [instances]
	for n in find_children("*", "Node3D", true, false):
		var nm := String(n.name)
		var kind := -1
		if nm.begins_with("spark_"):
			kind = 1
		elif nm.begins_with("rise_"):
			kind = 0
		elif nm.begins_with("petal_"):
			kind = 2
		if kind < 0:
			continue
		var p := _local_pos(n as Node3D)
		var list: Array = groups.get(kind, [])
		match kind:
			0:
				for i in 7:
					var o := Vector3(rng.randf_range(-8, 8), rng.randf_range(0, 2), rng.randf_range(-8, 8))
					list.append([p + o, rng.randf_range(0.55, 0.8), rng.randf(), rng.randf_range(45.0, 70.0),
							rng.randf_range(55.0, 80.0), Color(1.0, 0.5, 0.22).lerp(Color(1.0, 0.75, 0.35), rng.randf())])
			1:
				for i in 90:
					var o := Vector3(rng.randf_range(-0.9, 0.9), 0, rng.randf_range(-0.9, 0.9))
					list.append([p + o, rng.randf_range(0.1, 0.2), rng.randf(), rng.randf_range(2.0, 3.6),
							rng.randf_range(7.0, 13.0), Color.WHITE])
			2:
				for i in 26:
					var o := Vector3(rng.randf_range(-3.5, 3.5), rng.randf_range(-1, 2), rng.randf_range(-3, 2.5))
					list.append([p + o, rng.randf_range(0.07, 0.11), rng.randf(), rng.randf_range(7.0, 11.0),
							-rng.randf_range(5.0, 7.0), Color(1.0, 0.55, 0.7)])
		groups[kind] = list
	for kind in groups:
		var list: Array = groups[kind]
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
			mm.set_instance_color(i, e[5])
			mm.set_instance_custom_data(i, Color(e[2], e[3], e[4], float(kind)))
		var mi := MultiMeshInstance3D.new()
		mi.name = ["sky_lanterns", "sparks", "petals"][kind]
		mi.multimesh = mm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.custom_aabb = AABB(Vector3(-200, -20, -220), Vector3(400, 200, 260))
		var m := _shader("fuse_rise")
		m.set_shader_parameter("energy", [2.2, 3.0, 0.35][kind])
		m.set_shader_parameter("wind", [Vector3(5.0, 0, -4.0), Vector3(0.6, 0, 0), Vector3(1.5, 0, 0.5)][kind])
		mi.material_override = m
		_risers.append(m)
		add_child(mi)


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
	for b in _bob:
		var node: Node3D = b[0]
		var rest: Transform3D = b[1]
		var ph: float = _t * b[3] + b[4]
		var tr := rest
		tr.origin.y += sin(ph) * b[2]
		tr.basis = rest.basis * Basis(Vector3.BACK, sin(ph * 0.8 + 1.0) * b[5]) * Basis(Vector3.RIGHT, sin(ph * 0.6) * b[5] * 0.6)
		node.transform = tr
	for s in _spin:
		var rest: Transform3D = s[1]
		(s[0] as Node3D).transform = rest * Transform3D(Basis(s[2], _t * s[3]), Vector3.ZERO)
	if _wheel:
		var a := _t * WHEEL_SPEED
		_wheel.transform = _wheel_rest * Transform3D(Basis(Vector3.BACK, a), Vector3.ZERO)
		var hub := _wheel_rest.origin
		for g in _gondolas:
			(g[0] as Node3D).position = hub + ((g[1] as Vector3) - hub).rotated(Vector3.BACK, a)
	for l in _lights:
		if l[2] > 0.0:
			var f := 0.82 + 0.1 * sin(_t * 11.0) + 0.06 * sin(_t * 23.7 + 1.3) + 0.05 * sin(_t * 5.1)
			(l[0] as OmniLight3D).light_energy = l[1] * f
	_update_fireworks()


func _update_fireworks() -> void:
	if _mm == null:
		return
	while _t >= _next_launch:
		_launch(_next_launch, false)
		var every: float = _fw["every"]
		_next_launch += every * _rng.randf_range(0.45, 1.55)
		if _rng.randf() < 0.18:   # a quick pair now and then
			_launch(_next_launch - every * 0.3, false)
	var i := 0
	while i < _pending.size():
		var p: Array = _pending[i]
		if _t >= p[0]:
			_burst(p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[0])
			_pending.remove_at(i)
		else:
			i += 1
	for m in _fw_mats:
		(m as ShaderMaterial).set_shader_parameter("clock", _t)
	for m in _risers:
		(m as ShaderMaterial).set_shader_parameter("clock", _t)
	# the haze each recent burst lights in the sky, and the lights they throw on the scene
	var dirs := PackedVector4Array()
	var cols := PackedVector4Array()
	for r in _recent:
		var age: float = _t - r[0]
		var at: Vector3 = r[1]
		var to := at - CAMERA
		var dd := to.length()
		var dn := to / dd
		var c: Color = r[2]
		var k: float = r[4] * exp(-age * 1.8) * 0.05 if age >= 0.0 else 0.0
		dirs.append(Vector4(dn.x, dn.y, dn.z, atan(float(r[3]) * 1.4 / dd)))
		cols.append(Vector4(c.r * k, c.g * k, c.b * k, 0.0))
	while dirs.size() < 6:
		dirs.append(Vector4(0, 1, 0, 0))
		cols.append(Vector4())
	_sky.set_shader_parameter("clock", _t)
	_sky.set_shader_parameter("glow_dir", dirs)
	_sky.set_shader_parameter("glow_col", cols)
	for fl in _flash_lights:
		var l: OmniLight3D = fl[0]
		var age: float = _t - fl[1]
		var e: float = fl[2] * exp(-age * 2.6) if age >= 0.0 else 0.0
		l.light_energy = e
		l.visible = e > 0.05
	if _near_light:
		var age := _t - _near_t
		var e := 3.0 * exp(-age * 7.0) if age >= 0.0 else 0.0
		_near_light.light_energy = e
		_near_light.visible = e > 0.03
