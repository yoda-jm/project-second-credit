extends Node
## Game 6 main scene: the jungle in 3D, the HUD, sound and the pause menu. "--demo" (user argument) plays the
## campaign with the autopilot, which is what the captures record; any key takes over.

@onready var game: BootsGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	game.start(3 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
