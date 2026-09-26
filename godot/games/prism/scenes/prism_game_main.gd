extends Node
## Game 13 main scene: the crystal wall in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets the
## autopilot play, which is what the captures record; any key takes over.

@onready var game: PrismGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	game.pick_x = $View.field_x_at
	game.start(4 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
