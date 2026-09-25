extends Node
## Game 7 main scene: the night street in 3D, the HUD, sound and the pause menu. "--demo" (user argument) plays two
## autopilot brothers, which is what the captures record; any key takes over.

@onready var game: KnucklesGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var first := 0
	for a in args:
		if a.begins_with("--stage="):
			first = int(a.get_slice("=", 1))
	game.start(7 if game.demo else -1, 2 if game.demo else 1)
	if first > 0:
		game.stage = first
		game._start_stage()
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
