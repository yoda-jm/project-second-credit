class_name BioWorld
extends Node3D
## The living cavern of a Biosurge level, one look per theme (0 Spawning Grounds, 1 Coral Abyss, 2 Crystal Hive,
## 3 Furnace Gut, 4 The Heart). build() turns the engine's wall profile into continuous organic walls (a lit,
## glowing rim exactly on the deadly edge at the play plane, crowns rising to y 3-6, an undercut falling into the
## abyss), the islands as organic masses on stalks, the abyss floor at y -18 (glowing pools, veins, relief), two
## drifting veils of haze, drifting spores (embers in the furnace), a few pool lights, and dressing from the
## Blender kit (art/world/*.glb, tools/blender/biosurge_world.py) as MultiMeshes: on the crowns, under the lip and
## on the abyss floor. Everything is cut in chunks of CHUNK metres; update() shows those near the camera and drives
## the shaders' clock (fixed-step safe: the world runs on its own clock, advanced by update()'s delta).
##
## Space: the play plane is y = 0, the level runs from z = 0 to z = -length (index i of the profile is z = -i);
## the walls are solid where x < left[i] or x > right[i]. The visual edge of each wall at y = 0 is exactly the
## profile; the dressing keeps clear of the channel. The view owns the camera, the WorldEnvironment and the sun:
## it reads environment_for(theme) and may use make_environment() and setup_sun().

const KIT := "res://games/biosurge/art/world/%s.glb"
const SH := "res://games/biosurge/shaders/"
const CHUNK := 32
const PRE := 14               ## rows of wall before the level's start (z > 0)
const POST := 40              ## rows after its end
const FLOOR_Y := -18.0
const OUTER_LEFT := -22.0     ## the walls' crowns reach out to here (beyond the widest view)
const OUTER_RIGHT := 38.0
const SHOW_AHEAD := 52.0      ## chunks are shown from scroll_z - SHOW_AHEAD ...
const SHOW_BEHIND := 14.0     ## ... to scroll_z + SHOW_BEHIND
const FLASHES := 6
const KIT_SCALE := {"crown": 1.8, "under": 1.6, "floor": 1.3, "island": 1.5}

## The wall's cross-section, outward distance d from the edge and height y, from the abyss up to the edge
## (BELOW), then the shoulder (scaled by the row's height), then the crown (TOP: fractions of the way out to
## OUTER_*, base heights; lumpy).
const BELOW := [[5.5, -23.0], [3.4, -15.0], [1.9, -9.5], [0.95, -5.5], [0.38, -2.6], [0.09, -0.95], [0.0, 0.0]]
const SHOULDER := [[0.08, 0.6], [0.3, 1.25], [0.72, 1.85], [1.3, 2.4], [2.1, 2.85], [3.1, 3.2]]
const TOP := [[0.03, 3.4], [0.07, 3.55], [0.11, 3.65], [0.16, 3.75], [0.22, 3.8], [0.29, 3.85], [0.37, 3.9],
		[0.46, 3.9], [0.56, 3.95], [0.67, 3.95], [0.79, 4.0], [0.9, 4.0], [1.0, 4.0]]
## An island's rings: scale of its outline and height (the top's height is scaled by the island's size).
const ISLAND := [[0.4, -23.0], [0.55, -13.0], [0.78, -6.0], [0.94, -2.2], [0.99, -0.7], [1.0, 0.0], [0.98, 0.5],
		[0.93, 1.1], [0.84, 1.8], [0.7, 2.5], [0.5, 3.1], [0.28, 3.5], [0.0, 3.65]]

## Kit footprints (half-width at scale 1, metres): keeps the dressing off the channel.
const KIT_RADIUS := {"polyp": 0.4, "tube_coral": 0.5, "egg_cluster": 0.45, "crystal": 0.45, "tendril": 0.45,
		"rib": 1.25, "pipe": 0.65, "glow_plant": 0.55, "spore_pod": 0.4, "vent": 0.55, "anemone": 0.55,
		"fan_coral": 0.75, "spine": 0.5, "pustule": 0.4}

## Per theme: the environment (PopVoyage's keys), the wall shader, floor, haze, spores, pool lights and the kit.
## Kit entries: [name, where (crown/under/floor/island), count per chunk (per side for crown and under),
## scale min, scale max, sway].
const THEMES := [
	{   # 0 Spawning Grounds: green-teal living tissue, eggs and polyps, a lime edge
		"name": "Spawning Grounds",
		"sky_top": Color("#0a2a24"), "sky_horizon": Color("#1a5a48"), "ground_horizon": Color("#0a2a22"),
		"ground_bottom": Color("#020a08"), "background": Color("#020e0b"),
		"sun_color": Color("#e0fff0"), "sun_rotation": Vector3(-36, 170, 0), "sun_energy": 1.00,
		"ambient_color": Color("#3a7a68"), "ambient_energy": 0.30,
		"fog_color": Color("#031612"), "fog_density": 0.006, "fog_sun_scatter": 0.0,
		"fog_height": -3.0, "fog_height_density": 0.11,
		"exposure": 1.0, "glow_intensity": 0.8, "glow_threshold": 1.0, "saturation": 1.1, "contrast": 1.06,
		"wall": {"pattern": 0, "scale": 1.0, "deep_color": Color("#03140f"), "base_color": Color("#185444"),
				"top_color": Color("#4a9476"), "seam_color": Color("#0a2c22"), "vein_color": Color("#3cff96"),
				"rim_color": Color("#b4ff5a"), "vein_energy": 1.1, "rim_energy": 3.2, "roughness_v": 0.35,
				"pulse_rate": 0.45, "heart": 0.0, "breathe": 0.12, "flow": 0.0},
		"floor": {"ground_color": Color("#03110d"), "ridge_color": Color("#0c3a2e"), "pool_color": Color("#38ffb4"),
				"vein_color": Color("#3acf8a"), "pool_energy": 1.4, "vein_energy": 0.6, "pool_share": 0.3},
		"mist": [Color("#1a6a52"), 0.12, Vector2(0.4, 0.15)],
		"spores": {"count": 150, "color_a": Color("#c8ff8a"), "color_b": Color("#6affd0"), "energy": 1.6,
				"size": 0.26, "rise": 0.25, "wander": 0.6},
		"lights": [Color("#4affb0"), 1.1],
		"roles": {"flesh": [Color("#3d8a6c"), Color("#5a9a5a")], "dark": [Color("#0e2e26"), Color("#1a3a2a")],
				"shell": [Color("#c8dab0"), Color("#a8c890")], "metal": [Color("#4a6060"), Color("#3a5050")],
				"crystal": [Color("#b0ffd8"), Color("#d0ffb0")], "egg": [Color("#d8f0a0"), Color("#b0f0c0")],
				"glow": [Color("#9affb0"), Color("#d8ff6a")]},
		"glow_energy": 1.8,
		"kit": [["polyp", "crown", 7, 0.6, 1.3, 0.05], ["egg_cluster", "crown", 6, 0.7, 1.5, 0.0],
				["pustule", "crown", 6, 0.8, 1.8, 0.0], ["spore_pod", "crown", 3, 0.7, 1.2, 0.0],
				["tendril", "crown", 3, 0.5, 0.9, 0.06], ["glow_plant", "under", 4, 1.0, 1.8, 0.03],
				["tendril", "under", 3, 1.0, 1.6, 0.04], ["glow_plant", "floor", 8, 2.0, 4.0, 0.02],
				["tendril", "floor", 6, 3.0, 5.0, 0.012], ["egg_cluster", "floor", 5, 2.5, 4.0, 0.0],
				["spore_pod", "floor", 3, 2.5, 4.0, 0.0], ["polyp", "island", 2, 0.5, 0.8, 0.05]],
	},
	{   # 1 Coral Abyss: a blue-violet reef in a water haze, coral pores lit cyan, magenta tips
		"name": "Coral Abyss",
		"sky_top": Color("#0a1040"), "sky_horizon": Color("#2a3a8a"), "ground_horizon": Color("#10184a"),
		"ground_bottom": Color("#04061a"), "background": Color("#040820"),
		"sun_color": Color("#c8d8ff"), "sun_rotation": Vector3(-36, 195, 0), "sun_energy": 0.92,
		"ambient_color": Color("#4a4ea0"), "ambient_energy": 0.33,
		"fog_color": Color("#070f2c"), "fog_density": 0.009, "fog_sun_scatter": 0.0,
		"fog_height": -2.0, "fog_height_density": 0.15,
		"exposure": 1.0, "glow_intensity": 0.85, "glow_threshold": 1.0, "saturation": 1.12, "contrast": 1.05,
		"wall": {"pattern": 1, "scale": 1.0, "deep_color": Color("#060a26"), "base_color": Color("#3c3a92"),
				"top_color": Color("#8a78d0"), "seam_color": Color("#120c34"), "vein_color": Color("#40e0ff"),
				"rim_color": Color("#70f4ff"), "vein_energy": 2.2, "rim_energy": 3.0, "roughness_v": 0.55,
				"pulse_rate": 0.3, "heart": 0.0, "breathe": 0.06, "flow": 0.0},
		"floor": {"ground_color": Color("#050826"), "ridge_color": Color("#1a1a5a"), "pool_color": Color("#8a5aff"),
				"vein_color": Color("#3ab8ff"), "pool_energy": 1.8, "vein_energy": 0.8, "pool_share": 0.3},
		"mist": [Color("#2a4aa0"), 0.15, Vector2(0.25, 0.3)],
		"spores": {"count": 190, "color_a": Color("#9af0ff"), "color_b": Color("#e090ff"), "energy": 1.3,
				"size": 0.20, "rise": 0.12, "wander": 1.0},
		"lights": [Color("#8a6aff"), 1.2],
		"roles": {"flesh": [Color("#6a4ab8"), Color("#4a5ac8")], "dark": [Color("#140c38"), Color("#0c1440")],
				"shell": [Color("#f0d8ff"), Color("#ffc0e0")], "metal": [Color("#5a6080"), Color("#4a5070")],
				"crystal": [Color("#c0e8ff"), Color("#e0c8ff")], "egg": [Color("#c0d8ff"), Color("#f0c0ff")],
				"glow": [Color("#ff6ad8"), Color("#50e8ff")]},
		"glow_energy": 2.0,
		"kit": [["tube_coral", "crown", 7, 0.7, 1.5, 0.0], ["fan_coral", "crown", 4, 0.7, 1.3, 0.025],
				["anemone", "crown", 6, 0.8, 1.5, 0.12], ["polyp", "crown", 3, 0.6, 1.1, 0.05],
				["anemone", "under", 3, 1.0, 1.6, 0.1], ["fan_coral", "under", 3, 1.0, 1.8, 0.02],
				["glow_plant", "floor", 6, 2.0, 3.5, 0.02], ["fan_coral", "floor", 6, 2.5, 4.5, 0.01],
				["tube_coral", "floor", 6, 2.5, 4.0, 0.0], ["tendril", "floor", 4, 3.0, 4.5, 0.012],
				["anemone", "island", 2, 0.6, 0.9, 0.1]],
	},
	{   # 2 Crystal Hive: amber chitin plates, white and amber crystals, a honeyed glow below
		"name": "Crystal Hive",
		"sky_top": Color("#2a1a08"), "sky_horizon": Color("#8a5a20"), "ground_horizon": Color("#3a2408"),
		"ground_bottom": Color("#0c0602"), "background": Color("#100802"),
		"sun_color": Color("#fff0d8"), "sun_rotation": Vector3(-36, 160, 0), "sun_energy": 1.04,
		"ambient_color": Color("#7a5a38"), "ambient_energy": 0.28,
		"fog_color": Color("#190e03"), "fog_density": 0.006, "fog_sun_scatter": 0.0,
		"fog_height": -3.0, "fog_height_density": 0.11,
		"exposure": 1.0, "glow_intensity": 0.8, "glow_threshold": 1.0, "saturation": 1.08, "contrast": 1.08,
		"wall": {"pattern": 2, "scale": 1.0, "deep_color": Color("#120a03"), "base_color": Color("#94520e"),
				"top_color": Color("#e0a040"), "seam_color": Color("#241204"), "vein_color": Color("#ffb040"),
				"rim_color": Color("#fff0c0"), "vein_energy": 2.0, "rim_energy": 3.0, "roughness_v": 0.5,
				"pulse_rate": 0.35, "heart": 0.0, "breathe": 0.03, "flow": 0.0},
		"floor": {"ground_color": Color("#0e0702"), "ridge_color": Color("#3a2208"), "pool_color": Color("#ffa830"),
				"vein_color": Color("#ff8a20"), "pool_energy": 1.9, "vein_energy": 0.8, "pool_share": 0.3},
		"mist": [Color("#6a4210"), 0.11, Vector2(0.2, 0.1)],
		"spores": {"count": 150, "color_a": Color("#ffe0a0"), "color_b": Color("#fffaf0"), "energy": 1.5,
				"size": 0.18, "rise": 0.15, "wander": 0.5},
		"lights": [Color("#ffb040"), 1.1],
		"roles": {"flesh": [Color("#7a4a18"), Color("#9a6020")], "dark": [Color("#2a1406"), Color("#1a0c04")],
				"shell": [Color("#e8c888"), Color("#d0a050")], "metal": [Color("#6a5a40"), Color("#5a4a30")],
				"crystal": [Color("#fff6e8"), Color("#ffd890")], "egg": [Color("#ffe0a0"), Color("#ffd080")],
				"glow": [Color("#ffc050"), Color("#fff0c0")]},
		"glow_energy": 1.8,
		"kit": [["crystal", "crown", 9, 0.6, 1.6, 0.0], ["spine", "crown", 5, 0.6, 1.2, 0.0],
				["egg_cluster", "crown", 3, 0.7, 1.2, 0.0], ["pustule", "crown", 3, 0.7, 1.4, 0.0],
				["crystal", "under", 5, 1.0, 2.0, 0.0], ["spine", "under", 2, 1.0, 1.6, 0.0],
				["crystal", "floor", 10, 2.5, 5.0, 0.0], ["spine", "floor", 4, 2.5, 4.0, 0.0],
				["egg_cluster", "floor", 3, 2.5, 3.5, 0.0], ["crystal", "island", 2, 0.5, 0.9, 0.0]],
	},
	{   # 3 Furnace Gut: charred crust over molten veins, pipes and vents, embers rising
		"name": "Furnace Gut",
		"sky_top": Color("#2a0804"), "sky_horizon": Color("#8a2a0a"), "ground_horizon": Color("#3a0c04"),
		"ground_bottom": Color("#0c0201"), "background": Color("#100302"),
		"sun_color": Color("#ffd8b0"), "sun_rotation": Vector3(-36, 185, 0), "sun_energy": 0.72,
		"ambient_color": Color("#7a3a28"), "ambient_energy": 0.28,
		"fog_color": Color("#190602"), "fog_density": 0.006, "fog_sun_scatter": 0.0,
		"fog_height": -3.0, "fog_height_density": 0.08,
		"exposure": 1.0, "glow_intensity": 0.9, "glow_threshold": 1.0, "saturation": 1.1, "contrast": 1.08,
		"wall": {"pattern": 3, "scale": 1.0, "deep_color": Color("#140402"), "base_color": Color("#4a2418"),
				"top_color": Color("#6a3a26"), "seam_color": Color("#0a0201"), "vein_color": Color("#ff5a12"),
				"rim_color": Color("#ffb04a"), "vein_energy": 2.6, "rim_energy": 3.2, "roughness_v": 0.7,
				"pulse_rate": 0.6, "heart": 0.0, "breathe": 0.05, "flow": 0.12},
		"floor": {"ground_color": Color("#0c0201"), "ridge_color": Color("#2a0a04"), "pool_color": Color("#ff4a0c"),
				"vein_color": Color("#ff6a1a"), "pool_energy": 2.4, "vein_energy": 1.2, "pool_share": 0.45},
		"mist": [Color("#5a1a08"), 0.11, Vector2(0.1, 0.5)],
		"spores": {"count": 170, "color_a": Color("#ffb040"), "color_b": Color("#ff4a10"), "energy": 2.2,
				"size": 0.18, "rise": 1.6, "wander": 0.4},
		"lights": [Color("#ff5a1a"), 1.4],
		"roles": {"flesh": [Color("#5a2a1a"), Color("#4a2014")], "dark": [Color("#140604"), Color("#1a0804")],
				"shell": [Color("#c8a890"), Color("#a88870")], "metal": [Color("#6a5a50"), Color("#5a4a44")],
				"crystal": [Color("#ffd0a0"), Color("#ffb080")], "egg": [Color("#ffb080"), Color("#ff9060")],
				"glow": [Color("#ff7a20"), Color("#ffc050")]},
		"glow_energy": 2.2,
		"kit": [["pipe", "crown", 4, 0.8, 1.4, 0.0], ["vent", "crown", 5, 0.7, 1.4, 0.0],
				["rib", "crown", 2, 0.8, 1.3, 0.0], ["spine", "crown", 4, 0.6, 1.1, 0.0],
				["pustule", "crown", 5, 0.8, 1.6, 0.0], ["pipe", "under", 3, 1.2, 2.0, 0.0],
				["spine", "under", 3, 1.0, 1.8, 0.0], ["vent", "floor", 8, 2.5, 4.5, 0.0],
				["rib", "floor", 4, 2.5, 4.0, 0.0], ["pipe", "floor", 4, 2.5, 4.0, 0.0],
				["vent", "island", 1, 0.5, 0.8, 0.0]],
	},
	{   # 4 The Heart: the hive's living core, crimson membranes over purple veins, beating
		"name": "The Heart",
		"sky_top": Color("#2a0418"), "sky_horizon": Color("#7a1a48"), "ground_horizon": Color("#3a0820"),
		"ground_bottom": Color("#0c0106"), "background": Color("#0e0208"),
		"sun_color": Color("#ffd8e8"), "sun_rotation": Vector3(-36, 200, 0), "sun_energy": 0.88,
		"ambient_color": Color("#7a2a58"), "ambient_energy": 0.28,
		"fog_color": Color("#16020c"), "fog_density": 0.007, "fog_sun_scatter": 0.0,
		"fog_height": -3.0, "fog_height_density": 0.11,
		"exposure": 1.0, "glow_intensity": 0.85, "glow_threshold": 1.0, "saturation": 1.12, "contrast": 1.08,
		"wall": {"pattern": 4, "scale": 1.0, "deep_color": Color("#12020a"), "base_color": Color("#7a1232"),
				"top_color": Color("#b03458"), "seam_color": Color("#2a0216"), "vein_color": Color("#c050ff"),
				"rim_color": Color("#ff7ac0"), "vein_energy": 1.8, "rim_energy": 3.2, "roughness_v": 0.32,
				"pulse_rate": 1.1, "heart": 1.0, "breathe": 0.14, "flow": 0.0},
		"floor": {"ground_color": Color("#0e0108"), "ridge_color": Color("#3a0624"), "pool_color": Color("#ff2a7a"),
				"vein_color": Color("#a040ff"), "pool_energy": 2.1, "vein_energy": 1.0, "pool_share": 0.35},
		"mist": [Color("#6a1048"), 0.12, Vector2(0.3, 0.2)],
		"spores": {"count": 150, "color_a": Color("#ff8ac8"), "color_b": Color("#c070ff"), "energy": 1.5,
				"size": 0.22, "rise": 0.2, "wander": 0.7},
		"lights": [Color("#ff3a8a"), 1.2],
		"roles": {"flesh": [Color("#8a1a3a"), Color("#6a1448")], "dark": [Color("#24020e"), Color("#1a0418")],
				"shell": [Color("#f0d0c8"), Color("#e0b8c0")], "metal": [Color("#6a4a58"), Color("#5a3a48")],
				"crystal": [Color("#ffc8e0"), Color("#e0b0ff")], "egg": [Color("#ffb0c8"), Color("#e0a0ff")],
				"glow": [Color("#ff5aa8"), Color("#c060ff")]},
		"glow_energy": 1.8,
		"kit": [["rib", "crown", 3, 0.8, 1.3, 0.0], ["pustule", "crown", 7, 0.8, 1.8, 0.0],
				["tendril", "crown", 4, 0.5, 0.9, 0.06], ["polyp", "crown", 3, 0.6, 1.1, 0.05],
				["egg_cluster", "crown", 3, 0.7, 1.2, 0.0], ["tendril", "under", 5, 1.0, 1.8, 0.04],
				["rib", "under", 2, 1.0, 1.5, 0.0], ["rib", "floor", 2, 3.0, 4.0, 0.0],
				["tendril", "floor", 8, 3.0, 5.0, 0.012], ["pustule", "floor", 6, 3.0, 5.0, 0.0],
				["pustule", "island", 2, 0.5, 0.9, 0.0]],
	},
]

var theme := 0
var _t := 0.0
var _clocked: Array[ShaderMaterial] = []
var _chunks: Array[Node3D] = []
var _chunk_z: Array[Vector2] = []    ## per chunk: (z of its far end, z of its near end)
var _flash: Array = []               ## [OmniLight3D, start time, peak energy]
var _flash_slot := 0
var _rng := RandomNumberGenerator.new()
var _noise := FastNoiseLite.new()
var _kit_mesh := {}                  ## kit name -> ArrayMesh with the theme's materials
var _role_mats := {}
var _wall_mat: ShaderMaterial
var _rows := 0
var _cols := 0


## The environment the view applies for a theme. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color,
## for a ProceduralSkyMaterial: ambient and reflections), sun_color, sun_rotation (Vector3, degrees), sun_energy,
## ambient_color, ambient_energy, fog_color, fog_density (exponential), fog_sun_scatter, exposure, glow_intensity,
## glow_threshold, saturation, contrast, night (false: no lamps needed), name; and for Biosurge: background (the
## clear colour), fog_height and fog_height_density (the abyss haze), accent (the rim's colour: the deadly edge)
## and glow (the theme's glow colour, for the HUD or effects).
func environment_for(t: int) -> Dictionary:
	var d: Dictionary = THEMES[clampi(t, 0, THEMES.size() - 1)]
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_rotation", "sun_energy",
			"ambient_color", "ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure",
			"glow_intensity", "glow_threshold", "saturation", "contrast", "name", "background", "fog_height",
			"fog_height_density"]:
		out[k] = d[k]
	out["night"] = false
	out["accent"] = d["wall"]["rim_color"]
	out["glow"] = d["roles"]["glow"][0]
	return out


## A ready Environment from environment_for()'s dictionary.
static func make_environment(d: Dictionary) -> Environment:
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = d["sky_top"]
	sm.sky_horizon_color = d["sky_horizon"]
	sm.ground_horizon_color = d["ground_horizon"]
	sm.ground_bottom_color = d["ground_bottom"]
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_COLOR
	env.background_color = d.get("background", d["ground_bottom"])
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
	env.fog_height = d.get("fog_height", 0.0)
	env.fog_height_density = d.get("fog_height_density", 0.0)
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


## The cavern's key light (from above, a little ahead), with shadows reaching the abyss floor.
static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 75.0
	sun.directional_shadow_split_1 = 0.45
	sun.shadow_bias = 0.1
	sun.shadow_normal_bias = 2.0
	sun.shadow_blur = 1.5


## Builds the level's world. left/right: the walls' inner x every metre (index i at z = -i); islands: Rect2s in
## (x, distance along the level), i.e. x from position.x to end.x and z from -position.y to -end.y; length: the
## level's length in metres (the profile's size is used when it is longer).
func build(theme_index: int, left: PackedFloat32Array, right: PackedFloat32Array, islands: Array,
		length: float) -> void:
	var t0 := Time.get_ticks_msec()
	for c in get_children():
		c.queue_free()
	_chunks.clear()
	_chunk_z.clear()
	_clocked.clear()
	_flash.clear()
	_kit_mesh.clear()
	_role_mats.clear()
	theme = clampi(theme_index, 0, THEMES.size() - 1)
	var th: Dictionary = THEMES[theme]
	_rng.seed = 7919 + theme * 131
	_noise.seed = 4242 + theme
	_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	_noise.frequency = 0.09
	_noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	_noise.fractal_octaves = 3
	var n := maxi(left.size(), 1)
	if left.is_empty():
		left = PackedFloat32Array([0.0])
		right = PackedFloat32Array([16.0])
	_rows = PRE + maxi(n, int(length) + 1) + POST
	_make_materials(th)
	var nchunks := int(ceil(float(_rows - 1) / CHUNK))
	for k in nchunks:
		var c := Node3D.new()
		c.name = "Chunk%d" % k
		add_child(c)
		_chunks.append(c)
		var r0 := k * CHUNK
		var r1 := mini(r0 + CHUNK, _rows - 1)
		_chunk_z.append(Vector2(PRE - r1, PRE - r0))
	for side in [-1, 1]:
		var g := _wall_grid(side, left, right)
		_wall_meshes(g)
		_dress_wall(g, side, left, right, th)
	for r in islands:
		_island(r as Rect2, th)
	for k in nchunks:
		_abyss(k, left, right, th)
	for i in FLASHES:
		var l := OmniLight3D.new()
		l.visible = false
		l.omni_range = 9.0
		l.shadow_enabled = false
		add_child(l)
		_flash.append([l, -10.0, 0.0])
	update(0.0, 0.0)
	print("BioWorld: theme %d built in %d ms (%d chunks)" % [theme, Time.get_ticks_msec() - t0, nchunks])


## Called each frame with the camera's z: shows the chunks near it, animates the shaders, fades the flashes.
func update(scroll_z: float, delta: float) -> void:
	_t += delta
	for m in _clocked:
		m.set_shader_parameter("clock", _t)
	for k in _chunks.size():
		var zr: Vector2 = _chunk_z[k]
		_chunks[k].visible = zr.y > scroll_z - SHOW_AHEAD and zr.x < scroll_z + SHOW_BEHIND
	for f in _flash:
		var l: OmniLight3D = f[0]
		if not l.visible:
			continue
		var a: float = (_t - f[1]) / 0.45
		if a >= 1.0:
			l.visible = false
		else:
			l.light_energy = f[2] * (1.0 - a) * (1.0 - a)


## A brief light at pos (an explosion against the walls).
func flash(pos: Vector3, color: Color) -> void:
	if _flash.is_empty():
		return
	var f: Array = _flash[_flash_slot]
	_flash_slot = (_flash_slot + 1) % _flash.size()
	var l: OmniLight3D = f[0]
	l.position = pos + Vector3(0, 1.2, 0)
	l.light_color = color
	l.visible = true
	f[1] = _t
	f[2] = 7.0
	l.light_energy = 7.0


## True when (x, distance along the level) lies inside the island's visible outline at the play plane: a
## superellipse (exponent 8/3) touching the middle of each side of the Rect2, its corners rounded off. The engine may
## use it for a collision that matches the look exactly (the rectangle's corners stick out up to 23% beyond it).
static func island_contains(rect: Rect2, x: float, d: float) -> bool:
	var c := rect.get_center()
	var hx := maxf(rect.size.x * 0.5, 0.3)
	var hz := maxf(rect.size.y * 0.5, 0.3)
	return pow(absf(x - c.x) / hx, 8.0 / 3.0) + pow(absf(d - c.y) / hz, 8.0 / 3.0) <= 1.0


# ------------------------------------------------------------------ materials

func _shader_mat(file: String, params: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + file)
	for k in params:
		var v = params[k]
		if v is Color:
			v = Vector3(v.r, v.g, v.b)
		m.set_shader_parameter(k, v)
	_clocked.append(m)
	return m


func _make_materials(th: Dictionary) -> void:
	var w: Dictionary = th["wall"]
	_wall_mat = _shader_mat("bio_wall.gdshader", w)
	var roles: Dictionary = th["roles"]
	var glow: Array = roles["glow"]
	var pulse: float = w["pulse_rate"]
	var spec := {"flesh": [0.0, 0.4, 0.0], "dark": [0.0, 0.6, 0.0], "shell": [0.0, 0.5, 0.0],
			"metal": [0.0, 0.35, 0.75], "glow": [1.0, 0.4, 0.0], "egg": [2.0, 0.2, 0.0], "crystal": [3.0, 0.08, 0.2]}
	for role in spec:
		var cols: Array = roles[role]
		var s: Array = spec[role]
		_role_mats[role] = _shader_mat("bio_kit.gdshader", {"albedo": cols[0], "albedo_b": cols[1],
				"glow_color": glow[0] if role != "egg" else glow[1], "glow_energy": th["glow_energy"],
				"roughness_v": s[1], "metallic_v": s[2], "kind": s[0], "pulse_rate": pulse})
	if theme == 2:   # the hive's crystals shine
		(_role_mats["crystal"] as ShaderMaterial).set_shader_parameter("glow_energy", 6.0)


func _kit(name: String) -> ArrayMesh:
	if _kit_mesh.has(name):
		return _kit_mesh[name]
	var ps: PackedScene = load(KIT % name)
	var inst := ps.instantiate()
	var src: ArrayMesh = null
	for mi in inst.find_children("*", "MeshInstance3D", true, false):
		src = (mi as MeshInstance3D).mesh
		break
	inst.free()
	var mesh: ArrayMesh = src.duplicate()
	for i in mesh.get_surface_count():
		var mat := mesh.surface_get_material(i)
		var role := mat.resource_name if mat else "flesh"
		for r in _role_mats:
			if role.begins_with(r):
				role = r
				break
		mesh.surface_set_material(i, _role_mats.get(role, _role_mats["flesh"]))
	_kit_mesh[name] = mesh
	return mesh


# ------------------------------------------------------------------ walls

## The wall's vertex grid for one side: rows along the level, columns across the cross-section.
## Returns {pos, nrm, uv, tan (PackedVector3Array/PackedVector2Array, row-major), lip (column of the edge)}.
func _wall_grid(side: int, left: PackedFloat32Array, right: PackedFloat32Array) -> Dictionary:
	var ncol := BELOW.size() + SHOULDER.size() + TOP.size()
	_cols = ncol
	var lip_col := BELOW.size() - 1
	var outer := OUTER_LEFT if side < 0 else OUTER_RIGHT
	var pos := PackedVector3Array()
	pos.resize(_rows * ncol)
	var ao := PackedColorArray()
	ao.resize(_rows * ncol)
	ao.fill(Color.WHITE)
	var n := left.size()
	for r in _rows:
		var z := float(PRE - r)
		var i := clampi(r - PRE, 0, n - 1)
		var edge: float = left[i] if side < 0 else right[i]
		var hs := 1.0 + 0.32 * _noise.get_noise_2d(37.0 * side, z * 0.35) + 0.12 * sin(z * 0.05 + side)
		var c := 0
		for p in BELOW:
			var d: float = p[0]
			var y: float = p[1]
			if y < -1.5:
				d += absf(_noise.get_noise_2d(z * 1.3, y * 2.0 + side * 50.0)) * 1.4 * smoothstep(-1.5, -5.0, y)
			pos[r * ncol + c] = Vector3(edge + side * d, y, z)
			c += 1
		for p in SHOULDER:
			var d: float = p[0]
			var y: float = p[1] * hs
			var k := float(c - lip_col) / SHOULDER.size()
			y += _noise.get_noise_2d(edge * 0.7 + 90.0 * side, z * 0.8) * 0.5 * k * k
			pos[r * ncol + c] = Vector3(edge + side * d, y, z)
			c += 1
		var start := edge + side * float(SHOULDER[-1][0])
		for p in TOP:
			var f: float = p[0]
			var x := lerpf(start, outer, f)
			if side * (x - start) < 0.5:   # a channel reaching out past the crown's end: keep going outward
				x = start + side * (0.6 + f * 4.0)
			x += _noise.get_noise_2d(z * 0.6, f * 30.0 + side * 70.0) * 0.6 * (1.0 if f < 0.99 else 0.0)
			var w := smoothstep(0.0, 0.12, f)
			var bil := absf(_noise.get_noise_2d(x * 1.5 + 17.0, z * 1.5))        # billowy lobes, creased between
			var roll := _noise.get_noise_2d(x * 0.45, z * 0.45)
			var y: float = p[1] * hs + (bil * 3.2 + roll * 1.4) * w + 0.6 * f
			pos[r * ncol + c] = Vector3(x, y, z)
			var occ := clampf(0.5 + bil * 1.4 + roll * 0.25, 0.45, 1.0)
			ao[r * ncol + c] = Color(lerpf(1.0, occ, smoothstep(0.0, 0.15, f)), 1.0, 1.0)
			c += 1
	# normals, tangents (along the wall) and UVs (along: the edge's path length; across: arc from the edge)
	var nrm := PackedVector3Array()
	var tan := PackedFloat32Array()
	var uv := PackedVector2Array()
	nrm.resize(pos.size())
	tan.resize(pos.size() * 4)
	uv.resize(pos.size())
	var s := 0.0
	for r in _rows:
		if r > 0:
			s += pos[r * ncol + lip_col].distance_to(pos[(r - 1) * ncol + lip_col])
		var arc := 0.0
		for c in range(lip_col, ncol):
			if c > lip_col:
				arc += pos[r * ncol + c].distance_to(pos[r * ncol + c - 1])
			uv[r * ncol + c] = Vector2(s, arc)
		arc = 0.0
		for c in range(lip_col - 1, -1, -1):
			arc -= pos[r * ncol + c].distance_to(pos[r * ncol + c + 1])
			uv[r * ncol + c] = Vector2(s, arc)
		for c in ncol:
			var tc := pos[r * ncol + mini(c + 1, ncol - 1)] - pos[r * ncol + maxi(c - 1, 0)]
			var tr := pos[mini(r + 1, _rows - 1) * ncol + c] - pos[maxi(r - 1, 0) * ncol + c]
			if tr.length_squared() < 1e-6:
				tr = Vector3(0, 0, -1)
			var nn := tr.cross(tc) if side < 0 else tc.cross(tr)
			nrm[r * ncol + c] = nn.normalized()
			var tt := tr.normalized()
			var o := (r * ncol + c) * 4
			tan[o] = tt.x
			tan[o + 1] = tt.y
			tan[o + 2] = tt.z
			tan[o + 3] = 1.0
	return {"pos": pos, "nrm": nrm, "uv": uv, "tan": tan, "ao": ao, "lip": lip_col, "side": side}


func _wall_meshes(g: Dictionary) -> void:
	var ncol := _cols
	var pos: PackedVector3Array = g["pos"]
	var nrm: PackedVector3Array = g["nrm"]
	var uv: PackedVector2Array = g["uv"]
	var tan: PackedFloat32Array = g["tan"]
	for k in _chunks.size():
		var r0 := k * CHUNK
		var r1 := mini(r0 + CHUNK, _rows - 1)
		var a := r0 * ncol
		var b := (r1 + 1) * ncol
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = pos.slice(a, b)
		arr[Mesh.ARRAY_NORMAL] = nrm.slice(a, b)
		arr[Mesh.ARRAY_TANGENT] = tan.slice(a * 4, b * 4)
		arr[Mesh.ARRAY_TEX_UV] = uv.slice(a, b)
		arr[Mesh.ARRAY_COLOR] = (g["ao"] as PackedColorArray).slice(a, b)
		var idx := PackedInt32Array()
		for r in r1 - r0:
			for c in ncol - 1:
				var i0 := r * ncol + c
				var i1 := i0 + 1
				var i2 := i0 + ncol
				var i3 := i2 + 1
				idx.append_array([i0, i2, i1, i1, i2, i3])
		arr[Mesh.ARRAY_INDEX] = idx
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		mesh.surface_set_material(0, _wall_mat)
		var mi := MeshInstance3D.new()
		mi.name = "Wall%s" % ("L" if g["side"] < 0 else "R")
		mi.mesh = mesh
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_chunks[k].add_child(mi)


func _grid_point(g: Dictionary, r: int, c: float) -> Array:
	var pos: PackedVector3Array = g["pos"]
	var nrm: PackedVector3Array = g["nrm"]
	var c0 := int(c)
	var f := c - c0
	var c1 := mini(c0 + 1, _cols - 1)
	var p := pos[r * _cols + c0].lerp(pos[r * _cols + c1], f)
	var nn := nrm[r * _cols + c0].lerp(nrm[r * _cols + c1], f).normalized()
	return [p, nn]


## A random placement on the crown (or under the lip) of one side, clear of the channel by the item's footprint.
func _dress_wall(g: Dictionary, side: int, left: PackedFloat32Array, right: PackedFloat32Array,
		th: Dictionary) -> void:
	var lip: int = g["lip"]
	var n := left.size()
	for entry in th["kit"]:
		var where: String = entry[1]
		if where != "crown" and where != "under":
			continue
		for k in _chunks.size():
			var xf: Array[Transform3D] = []
			for j in entry[2]:
				var r := mini(k * CHUNK + _rng.randi_range(0, CHUNK - 1), _rows - 1)
				var sc: float = _rng.randf_range(entry[3], entry[4]) * KIT_SCALE[where]
				var rad: float = KIT_RADIUS[entry[0]] * sc
				var i := clampi(r - PRE, 0, n - 1)
				var edge: float = left[i] if side < 0 else right[i]
				var p: Vector3
				var up: Vector3
				if where == "crown":
					# biased towards the shoulder: the part of the crown in view
					var c := lip + 2.0 + pow(_rng.randf(), 1.6) * (SHOULDER.size() + 2.5)
					var q := _grid_point(g, r, c)
					p = q[0]
					up = (q[1] as Vector3).lerp(Vector3.UP, 0.55).normalized()
					var clear := side * (p.x - edge)   # outward distance from the edge
					# the nearest edge along a few metres either way (the profile may jut out nearby)
					for di in [-3, -2, -1, 1, 2, 3]:
						var e2: float = left[clampi(i + di, 0, n - 1)] if side < 0 else right[clampi(i + di, 0, n - 1)]
						clear = minf(clear, side * (p.x - e2) + absf(di) * 0.6)
					if clear < rad + 0.5:
						continue
				else:
					var c := _rng.randf_range(0.6, 2.6)   # the undercut, y about -8 .. -19
					var q := _grid_point(g, r, c)
					p = q[0]
					up = ((q[1] as Vector3) + Vector3.UP * 0.7).normalized()
				p.y -= 0.12 * sc
				xf.append(_place(p, up, sc, entry[0] == "rib" or entry[0] == "fan_coral"))
			_add_multimesh(k, entry, xf)


func _place(p: Vector3, up: Vector3, sc: float, along: bool) -> Transform3D:
	var yaw := _rng.randf() * TAU
	if along:   # ribs and fans stand along the wall (arching over the crown, not into the channel)
		yaw = PI * 0.5 + _rng.randf_range(-0.25, 0.25) + (PI if _rng.randf() < 0.5 else 0.0)
	var b := Basis(Vector3.UP, yaw)
	var q := Quaternion(Vector3.UP, up.normalized())
	b = Basis(q) * b
	return Transform3D(b.scaled(Vector3.ONE * sc), p)


func _add_multimesh(k: int, entry: Array, xf: Array[Transform3D]) -> void:
	if xf.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = _kit(entry[0])
	mm.instance_count = xf.size()
	for i in xf.size():
		mm.set_instance_transform(i, xf[i])
		mm.set_instance_custom_data(i, Color(_rng.randf(), entry[5], _rng.randf_range(0.7, 1.3), _rng.randf()))
	var mmi := MultiMeshInstance3D.new()
	mmi.name = "Kit_%s_%s" % [entry[0], entry[1]]
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_chunks[k].add_child(mmi)


# ------------------------------------------------------------------ islands

func _island(rect: Rect2, th: Dictionary) -> void:
	var cx := rect.get_center().x
	var cz := -rect.get_center().y
	var hx := maxf(rect.size.x * 0.5, 0.3)
	var hz := maxf(rect.size.y * 0.5, 0.3)
	var k := clampi(int(floor((PRE - cz) / CHUNK)), 0, _chunks.size() - 1)
	var seg := 28
	var top := clampf(minf(hx, hz) * 1.5, 2.0, 5.0) / 3.65
	var rings := ISLAND.size()
	var pos := PackedVector3Array()
	var outline := PackedVector2Array()
	for j in seg:
		var a := TAU * j / seg
		var ca := cos(a)
		var sa := sin(a)
		# a superellipse (exponent 2.7): nearly fills the rectangle, rounded corners
		var ex := signf(ca) * pow(absf(ca), 0.75)
		var ez := signf(sa) * pow(absf(sa), 0.75)
		outline.append(Vector2(ex * hx, ez * hz))
	for ri in rings:
		var sc: float = ISLAND[ri][0]
		var y: float = ISLAND[ri][1]
		if y > 0.0:
			y *= top
		for j in seg:
			var o := outline[j] * sc
			var wob := 0.0
			if y < -1.0 or y > 0.6:
				wob = _noise.get_noise_2d(j * 3.1 + cx, y * 0.7 + cz) * 0.35 * (1.0 if y < 0.0 else sc)
			o *= 1.0 + wob
			pos.append(Vector3(cx + o.x, y, cz + o.y))
	# grid normals (wrapping round), tangents, UVs
	var nrm := PackedVector3Array()
	var tan := PackedFloat32Array()
	var uv := PackedVector2Array()
	nrm.resize(pos.size())
	tan.resize(pos.size() * 4)
	uv.resize(pos.size())
	var lip_ring := 5
	var per := PackedFloat32Array([0.0])
	for j in range(1, seg + 1):
		per.append(per[j - 1] + outline[j % seg].distance_to(outline[j - 1]))
	for ri in rings:
		for j in seg:
			var tr := pos[ri * seg + (j + 1) % seg] - pos[ri * seg + (j - 1 + seg) % seg]
			var tc := pos[mini(ri + 1, rings - 1) * seg + j] - pos[maxi(ri - 1, 0) * seg + j]
			var nn := tc.cross(tr)
			if ri == rings - 1:
				nn = Vector3.UP
			nrm[ri * seg + j] = nn.normalized()
			var tt := tr.normalized()
			tan[(ri * seg + j) * 4] = tt.x
			tan[(ri * seg + j) * 4 + 1] = tt.y
			tan[(ri * seg + j) * 4 + 2] = tt.z
			tan[(ri * seg + j) * 4 + 3] = 1.0
	for j in seg:
		var arc := 0.0
		uv[lip_ring * seg + j] = Vector2(per[j], 0.0)
		for ri in range(lip_ring + 1, rings):
			arc += pos[ri * seg + j].distance_to(pos[(ri - 1) * seg + j])
			uv[ri * seg + j] = Vector2(per[j], arc)
		arc = 0.0
		for ri in range(lip_ring - 1, -1, -1):
			arc -= pos[ri * seg + j].distance_to(pos[(ri + 1) * seg + j])
			uv[ri * seg + j] = Vector2(per[j], arc)
	# the outward normal check: flip if the lip ring's normal points inward
	var test := nrm[lip_ring * seg]
	var outw := pos[lip_ring * seg] - Vector3(cx, 0.0, cz)
	if test.dot(outw) < 0.0:
		for i in nrm.size():
			nrm[i] = -nrm[i]
	var idx := PackedInt32Array()
	for ri in rings - 1:
		for j in seg:
			var j1 := (j + 1) % seg
			idx.append_array([ri * seg + j, (ri + 1) * seg + j, ri * seg + j1,
					ri * seg + j1, (ri + 1) * seg + j, (ri + 1) * seg + j1])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = pos
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_TANGENT] = tan
	arr[Mesh.ARRAY_TEX_UV] = uv
	var col := PackedColorArray()   # r: occlusion, g: how much of the rim's soft band shows (little on an island)
	for i in pos.size():
		col.append(Color(0.8 + 0.2 * _noise.get_noise_2d(pos[i].x * 2.0, pos[i].z * 2.0), 0.2, 1.0))
	arr[Mesh.ARRAY_COLOR] = col
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	mesh.surface_set_material(0, _wall_mat)
	var mi := MeshInstance3D.new()
	mi.name = "Island"
	mi.mesh = mesh
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_chunks[k].add_child(mi)
	# a little life on its crown
	for entry in th["kit"]:
		if entry[1] != "island":
			continue
		var xf: Array[Transform3D] = []
		for j in entry[2]:
			var sc: float = _rng.randf_range(entry[3], entry[4]) * KIT_SCALE["island"] * clampf(minf(hx, hz) / 1.5, 0.5, 1.2)
			var o := Vector2(_rng.randf_range(-0.35, 0.35) * hx, _rng.randf_range(-0.35, 0.35) * hz)
			xf.append(_place(Vector3(cx + o.x * 0.6, 3.65 * top * 0.9, cz + o.y * 0.6), Vector3.UP, sc, false))
		_add_multimesh(k, entry, xf)


# ------------------------------------------------------------------ the abyss

func _abyss(k: int, left: PackedFloat32Array, right: PackedFloat32Array, th: Dictionary) -> void:
	var chunk := _chunks[k]
	var zr: Vector2 = _chunk_z[k]
	var zc := (zr.x + zr.y) * 0.5
	var zl := zr.y - zr.x
	if k == 0:
		_floor_mat(th)
	# the floor
	var pm := PlaneMesh.new()
	pm.size = Vector2(110.0, zl)
	pm.subdivide_width = 22
	pm.subdivide_depth = 8
	var fl := MeshInstance3D.new()
	fl.name = "Floor"
	fl.mesh = pm
	fl.material_override = _floor
	fl.position = Vector3(8.0, FLOOR_Y, zc)
	fl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	chunk.add_child(fl)
	# two veils of haze
	for layer in 2:
		var mp := PlaneMesh.new()
		mp.size = Vector2(90.0, zl)
		var mm := MeshInstance3D.new()
		mm.name = "Mist%d" % layer
		mm.mesh = mp
		mm.material_override = _mist[layer]
		mm.position = Vector3(8.0, -6.5 if layer == 0 else -12.5, zc)
		mm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		chunk.add_child(mm)
	# spores
	var sp: Dictionary = th["spores"]
	var smm := MultiMesh.new()
	smm.transform_format = MultiMesh.TRANSFORM_3D
	smm.use_custom_data = true
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	smm.mesh = q
	smm.instance_count = sp["count"]
	var n := left.size()
	for i in smm.instance_count:
		var z := _rng.randf_range(zr.x, zr.y)
		var li := clampi(int(-z), 0, n - 1)
		var x := _rng.randf_range(left[li] - 3.0, right[li] + 3.0)
		smm.set_instance_transform(i, Transform3D(Basis(), Vector3(x, _rng.randf_range(-16.0, -1.5), z)))
		smm.set_instance_custom_data(i, Color(_rng.randf(), _rng.randf_range(0.6, 1.4), _rng.randf(), _rng.randf()))
	var smi := MultiMeshInstance3D.new()
	smi.name = "Spores"
	smi.multimesh = smm
	smi.material_override = _spores
	smi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	smi.custom_aabb = AABB(Vector3(-20, -20, zr.x - 4), Vector3(60, 24, zl + 8))
	chunk.add_child(smi)
	# pool lights under the channel
	var lc: Array = th["lights"]
	for j in 2:
		var z := lerpf(zr.x, zr.y, (j + _rng.randf_range(0.2, 0.8)) / 2.0)
		var li := clampi(int(-z), 0, n - 1)
		var l := OmniLight3D.new()
		l.light_color = lc[0]
		l.light_energy = lc[1]
		l.omni_range = 17.0
		l.omni_attenuation = 1.2
		l.shadow_enabled = false
		l.position = Vector3((left[li] + right[li]) * 0.5 + _rng.randf_range(-3.0, 3.0), FLOOR_Y + 5.0, z)
		chunk.add_child(l)
	# the floor's life
	for entry in th["kit"]:
		if entry[1] != "floor":
			continue
		var xf: Array[Transform3D] = []
		for j in entry[2]:
			var z := _rng.randf_range(zr.x, zr.y)
			var x := _rng.randf_range(-16.0, 32.0)
			var sc: float = _rng.randf_range(entry[3], entry[4]) * KIT_SCALE["floor"]
			var up := Vector3(_rng.randf_range(-0.25, 0.25), 1.0, _rng.randf_range(-0.25, 0.25))
			xf.append(_place(Vector3(x, FLOOR_Y - 1.0, z), up, sc, false))
		_add_multimesh(k, entry, xf)


var _floor: ShaderMaterial
var _mist: Array[ShaderMaterial] = []
var _spores: ShaderMaterial


func _floor_mat(th: Dictionary) -> void:
	var fp: Dictionary = th["floor"].duplicate()
	var w: Dictionary = th["wall"]
	fp["pulse_rate"] = w["pulse_rate"]
	fp["heart"] = w["heart"]
	fp["flow"] = w["flow"] * 0.3
	_floor = _shader_mat("bio_floor.gdshader", fp)
	_mist.clear()
	var mc: Array = th["mist"]
	_mist.append(_shader_mat("bio_mist.gdshader", {"mist_color": mc[0], "strength": mc[1], "drift": mc[2],
			"scale": 0.045}))
	_mist.append(_shader_mat("bio_mist.gdshader", {"mist_color": (mc[0] as Color).darkened(0.3),
			"strength": mc[1] * 0.9, "drift": -(mc[2] as Vector2) * 0.6, "scale": 0.07}))
	var sp: Dictionary = th["spores"]
	_spores = _shader_mat("bio_spores.gdshader", {"color_a": sp["color_a"], "color_b": sp["color_b"],
			"energy": sp["energy"], "size": sp["size"], "rise": sp["rise"], "wander": sp["wander"],
			"box_bottom": -16.5, "box_height": 15.5})
