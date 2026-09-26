extends Node
## Game 2 main scene: the coast in 3D, the HUD and the pause menu. "--demo" (user argument) starts the
## autopilot, which is what the captures record; any key takes over. Both play The Coastline, the island campaign;
## "--endless" plays the first island until it falls instead.

@onready var game: BastionGame = $Game


func _ready() -> void:
	game.demo = OS.get_cmdline_user_args().has("--demo") and not OS.get_cmdline_user_args().has("--play")  # --play: captures of the player HUD
	game.demo_locked = game.demo and OS.get_cmdline_user_args().has("--locked")
	var pack := Pack.find("bastion", "the-coastline")
	if pack and not OS.get_cmdline_user_args().has("--endless"):
		game.start_campaign(pack, 7 if game.demo else -1)
	else:
		game.start(7 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
