extends Node
## Game 27 main scene: the floating courses in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets
## the autopilot roll, which is what the captures record; any key takes over. "--level=N" starts at a course.

@onready var game: DriftGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var at := 0
	for a in args:
		if a.begins_with("--level="):
			at = int(a.substr(8)) - 1
	game.start(at)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start(0))
