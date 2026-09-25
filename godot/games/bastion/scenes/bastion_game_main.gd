extends Node
## Game 2 main scene: the coast in 3D, the HUD and the pause menu. "--demo" (user argument) starts the
## autopilot, which is what the captures record; any key takes over.

@onready var game: BastionGame = $Game


func _ready() -> void:
	game.demo = OS.get_cmdline_user_args().has("--demo")
	game.start(7 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
