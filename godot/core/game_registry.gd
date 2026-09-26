class_name GameRegistry
extends RefCounted
## Every game of the collection, in build order. The launcher lists them; `scene` is empty until playable.

const GAMES: Array[Dictionary] = [
	{
		"id": "glimmerdeep",
		"style": "Puzzle",
		"title": "Glimmerdeep",
		"tagline": "Dig deep, grab the gems, mind the boulders.",
		"inspired_by": "Boulder Dash (1984)",
		"scene": "res://games/glimmerdeep/scenes/glimmerdeep_game.tscn",
		"card": "res://core/ui/cards/glimmerdeep.png",
		"accent": Color(0.35, 0.9, 1.0),
		## objects floating behind the launcher when this game is selected: [mesh, material, share]
		"props": [["res://games/glimmerdeep/art/models/diamond.obj", "gem", 0.6],
			["res://games/glimmerdeep/art/models/boulder.obj", "rock", 0.4]],
	},
	{
		"id": "bastion",
		"style": "Strategy",
		"title": "Bastion Coast",
		"tagline": "Build walls, aim cannons, hold the coast.",
		"inspired_by": "Rampart (1990)",
		"scene": "res://games/bastion/scenes/bastion_game.tscn",
		"card": "res://core/ui/cards/bastion.png",
		"accent": Color(1.0, 0.55, 0.25),
		"props": [["res://games/bastion/art/models/ship_small.glb", "model", 0.35],
			["res://games/bastion/art/models/cannon.glb", "model", 0.3],
			["res://games/bastion/art/models/wall.obj", "stone", 0.35]],
	},
	{
		"id": "fruitburrow",
		"style": "Arcade",
		"title": "Fruitburrow",
		"tagline": "Dig the garden, pick the fruit, drop the apples.",
		"inspired_by": "Fruity Frank (1984)",
		"scene": "res://games/fruitburrow/scenes/fruitburrow_game.tscn",
		"card": "res://core/ui/cards/fruitburrow.png",
		"accent": Color(0.55, 1.0, 0.4),
		"props": [["res://games/fruitburrow/art/models/apple.glb", "model", 0.3],
			["res://games/fruitburrow/art/models/cherries.glb", "model", 0.25],
			["res://games/fruitburrow/art/models/strawberry.glb", "model", 0.2],
			["res://games/fruitburrow/art/models/plum.glb", "model", 0.25]],
	},
	{
		"id": "whisker",
		"style": "Platform",
		"title": "Whisker Alley",
		"tagline": "Moonlit fences, open windows and a cat with nine lives.",
		"inspired_by": "Alley Cat (1984)",
		"scene": "res://games/whisker/scenes/whisker_game.tscn",
		"card": "res://core/ui/cards/whisker.png",
		"accent": Color(0.75, 0.55, 1.0),
		"props": [["res://games/whisker/art/models/trash_can.glb", "model", 0.3],
			["res://games/whisker/art/models/goldfish.glb", "model", 0.25],
			["res://games/whisker/art/models/boot.glb", "model", 0.25],
			["res://games/whisker/art/models/canary.glb", "model", 0.2]],
	},
	{
		"id": "frostpeak",
		"style": "Sports",
		"title": "Frostpeak Games",
		"tagline": "Ice, snow and a medal ceremony. Up to four players.",
		"inspired_by": "Winter Games (1985)",
		"scene": "res://games/frostpeak/scenes/frostpeak_game.tscn",
		"card": "res://core/ui/cards/frostpeak.png",
		"accent": Color(0.6, 0.85, 1.0),
		"props": [["res://games/frostpeak/art/models/snowy_pine.glb", "model", 0.3],
			["res://games/frostpeak/art/models/podium.glb", "model", 0.2],
			["res://games/frostpeak/art/models/cauldron.glb", "model", 0.2],
			["res://games/frostpeak/art/models/flagpole.glb", "model", 0.3]],
	},
	{
		"id": "boots",
		"style": "Action",
		"title": "Muddy Boots",
		"tagline": "A squad, a jungle and a long way home.",
		"inspired_by": "Cannon Fodder (1993)",
		"scene": "res://games/boots/scenes/boots_game.tscn",
		"card": "res://core/ui/cards/boots.png",
		"accent": Color(0.5, 0.8, 0.35),
		"props": [["res://games/boots/art/models/palm.glb", "model", 0.3],
			["res://games/boots/art/models/grenade_crate.glb", "model", 0.25],
			["res://games/boots/art/models/hut.glb", "model", 0.2],
			["res://games/boots/art/models/mine.glb", "model", 0.25]],
	},
	{
		"id": "knuckles",
		"style": "Fighting",
		"title": "Neon Knuckles",
		"tagline": "Two brothers, one neon street, fists first.",
		"inspired_by": "Double Dragon (1987)",
		"scene": "res://games/knuckles/scenes/knuckles_game.tscn",
		"card": "res://core/ui/cards/knuckles.png",
		"accent": Color(1.0, 0.4, 0.65),
		"props": [["res://games/knuckles/art/models/bat.glb", "model", 0.3],
			["res://games/knuckles/art/models/barrel.glb", "model", 0.25],
			["res://games/knuckles/art/models/crate.glb", "model", 0.25],
			["res://games/knuckles/art/models/knife.glb", "model", 0.2]],
	},
	{
		"id": "flags",
		"style": "Strategy",
		"title": "Iron Flags",
		"tagline": "Robots, flags and a very short fuse.",
		"inspired_by": "Z (1996)",
		"scene": "res://games/flags/scenes/flags_game.tscn",
		"card": "res://core/ui/cards/flags.png",
		"accent": Color(0.95, 0.6, 0.2),
		"props": [["res://games/flags/art/models/robot_grunt.glb", "model", 0.5],
			["res://games/flags/art/models/tank_medium.glb", "model", 0.35],
			["res://games/flags/art/models/flag_pole.glb", "model", 0.3],
			["res://games/flags/art/models/cannon_gun.glb", "model", 0.3]],
	},
	{
		"id": "blastyard",
		"style": "Party",
		"title": "Blastyard",
		"tagline": "Four bombers, one yard, no hard feelings.",
		"inspired_by": "Bomberman (1983)",
		"scene": "res://games/blastyard/scenes/blastyard_game.tscn",
		"card": "res://core/ui/cards/blastyard.png",
		"accent": Color(1.0, 0.55, 0.2),
		"props": [["res://games/blastyard/art/models/bomb.glb", "model", 0.4],
			["res://games/blastyard/art/models/crate.glb", "model", 0.3],
			["res://games/blastyard/art/models/pu_fire.glb", "model", 0.3]],
	},
]


## The styles in collection order (for the launcher's filter).
static func styles() -> Array[String]:
	var out: Array[String] = []
	for g in GAMES:
		if not out.has(g.get("style", "")):
			out.append(g.get("style", ""))
	return out


static func find(id: String) -> Dictionary:
	for g in GAMES:
		if g["id"] == id:
			return g
	return {}
