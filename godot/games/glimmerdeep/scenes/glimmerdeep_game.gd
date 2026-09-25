extends Node
## Game 1 main scene: one cave in the 3D diorama view with its HUD. Pass "--demo" (user argument) to run the
## cave's demo replay instead of waiting for the player; the capture script does this.

@export_file("*.bd") var cave_file := "res://games/glimmerdeep/packs/second-credit/first-light.bd"
@export var cave_index := 0

@onready var game: CaveGame = $Game


func _ready() -> void:
	var demo := OS.get_cmdline_user_args().has("--demo")
	game.load_cave(cave_file, cave_index, demo)
