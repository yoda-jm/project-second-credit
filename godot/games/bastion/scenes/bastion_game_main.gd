extends Node
## Game 2 main scene: the coast in 3D, the HUD and the pause menu. "--demo" (user argument) starts the
## autopilot, which is what the captures record; any key takes over. Both play The Coastline, the island campaign;
## "--endless" plays the first island until it falls instead. "--versus" (or "--versus=3") starts a versus match
## instead, played by the autopilot for every player with "--demo"; F2 in the game opens the versus chooser.

@onready var game: BastionGame = $Game


func _ready() -> void:
	game.demo = OS.get_cmdline_user_args().has("--demo") and not OS.get_cmdline_user_args().has("--play")  # --play: captures of the player HUD
	game.demo_locked = game.demo and OS.get_cmdline_user_args().has("--locked")
	var pack := Pack.find("bastion", "the-coastline")
	var vs := 0
	for arg in OS.get_cmdline_user_args():
		if arg == "--versus":
			vs = 2
		elif arg.begins_with("--versus="):
			vs = arg.get_slice("=", 1).to_int()
	if vs > 1:
		game.start_versus(vs, 7 if game.demo else -1)
	elif pack and not OS.get_cmdline_user_args().has("--endless"):
		game.start_campaign(pack, 7 if game.demo else -1)
	else:
		game.start(7 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(game.restart)
