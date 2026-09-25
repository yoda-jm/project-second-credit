extends Node
## Game 3 main scene: the garden in 3D, the HUD, sound and the pause menu. "--demo" (user argument) starts the
## autopilot, which is what the captures record; any key takes over.

@onready var game: FruitburrowGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")  # --play: captures of the player HUD
	game.demo_locked = game.demo and args.has("--locked")
	game.start(11 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
