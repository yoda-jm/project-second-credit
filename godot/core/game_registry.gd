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
	},
	{
		"id": "rampart",
		"title": "Game 2",
		"tagline": "Build walls, aim cannons, hold the coast.",
		"inspired_by": "Rampart (1990)",
		"scene": "",
		"card": "",
		"accent": Color(1.0, 0.55, 0.25),
	},
	{
		"id": "fruityfrank",
		"title": "Game 3",
		"tagline": "A garden of tunnels and falling apples.",
		"inspired_by": "Fruity Frank (1984)",
		"scene": "",
		"card": "",
		"accent": Color(0.55, 1.0, 0.4),
	},
]


static func find(id: String) -> Dictionary:
	for g in GAMES:
		if g["id"] == id:
			return g
	return {}
