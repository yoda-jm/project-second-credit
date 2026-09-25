extends Node
## Game 1 main scene: one cave in the 3D diorama view with its HUD. Pass "--demo" (user argument) to run the
## cave's demo replay instead of waiting for the player (the capture script does this), or "--demo=N" for the
## N-th replay (1: the hero gets crushed, for the death effect).

@export_file("*.bd") var cave_file := "res://games/glimmerdeep/packs/second-credit/first-light.bd"
@export var cave_index := 0

@onready var game: CaveGame = $Game


func _ready() -> void:
	var demo := false
	var demo_index := 0
	for arg in OS.get_cmdline_user_args():
		if arg == "--demo":
			demo = true
		elif arg.begins_with("--demo="):
			demo = true
			demo_index = int(arg.substr(7))
	game.load_cave(cave_file, cave_index, demo, demo_index)
	game.demo_locked = demo and OS.get_cmdline_user_args().has("--locked")
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(game.restart)
