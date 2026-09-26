extends Node
## Game 11 main scene: the harbour warehouse in 3D, the HUD, sound and the pause menu. "--demo" (user argument)
## plays the stored solutions, which is what the captures record; any key takes over. "--puzzle=N" starts at N.

@onready var game: CratesGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var first := 0
	for a in args:
		if a.begins_with("--puzzle="):
			first = int(a.get_slice("=", 1))
	game.start(first)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.engine.restart())
