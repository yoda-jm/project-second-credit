class_name GameRegistry
extends RefCounted
## Every game of the collection, in build order. The launcher lists them; `scene` is empty until playable.

const GAMES: Array[Dictionary] = [
	{
		"id": "glimmerdeep",
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
		"title": "Fruitburrow",
		"tagline": "Dig the garden, pick the fruit, drop the apples.",
		"inspired_by": "Fruity Frank (1984)",
		"scene": "res://games/fruitburrow/scenes/fruitburrow_game.tscn",
		"card": "",
		"accent": Color(0.55, 1.0, 0.4),
		"props": [["res://core/art/props/cone.obj", "cone", 0.55], ["res://core/art/props/gear.obj", "steel", 0.45]],
	},
]


static func find(id: String) -> Dictionary:
	for g in GAMES:
		if g["id"] == id:
			return g
	return {}
