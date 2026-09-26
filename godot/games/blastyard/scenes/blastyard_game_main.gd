extends Node
## Game 9 main scene: the arena in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets four bots
## battle, which is what the captures record; a key opens the setup screen. "--solo" makes the demo play the solo
## stages with one bot.

@onready var game: BlastGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var demo := args.has("--demo") and not args.has("--play")
	game.demo_locked = demo and args.has("--locked")
	if demo:
		game.start_demo(5)
		if args.has("--solo"):
			game.mode = "solo"
			game.humans = 0
			game._new_match()
	else:
		game.start_demo(5)  # the arena plays behind the setup screen
		game.start_setup()
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start_setup())
