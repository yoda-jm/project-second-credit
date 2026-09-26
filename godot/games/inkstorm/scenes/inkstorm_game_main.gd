extends Node
## Game 14 main scene: the map table in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets the
## autopilot play, which is what the captures record; any key takes over. "--stage=N" starts at a later stage.

@onready var game: InkGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	for a in args:
		if a.begins_with("--stage="):
			game.stage = int(a.substr(8))
	var first := game.stage
	game.start(4 if game.demo else -1)
	if first > 0:
		game.stage = first
		game._new_stage(3, 0)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
