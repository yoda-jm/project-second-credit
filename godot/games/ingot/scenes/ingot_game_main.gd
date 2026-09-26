extends Node
## Game 10 main scene: the temple mine in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets the
## autopilot play, which is what the captures record; any key takes over. "--level=N" starts at level N.

@onready var game: IngotGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var first := 0
	for a in args:
		if a.begins_with("--level="):
			first = int(a.get_slice("=", 1))
	game.start(3 if game.demo else -1, first)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
