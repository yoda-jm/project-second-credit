extends Node
## Game 4 main scene: the alley in 3D, the HUD, sound and the pause menu. "--demo" (user argument) starts the
## autopilot, which is what the captures record; any key takes over.

@onready var game: WhiskerGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	game.start(21 if game.demo else -1)
	for a in args:
		if a.begins_with("--room="):  # captures: start inside a room
			game.engine.phase = WhiskerEngine.Phase.ALLEY
			game.engine.enter_room_kind(int(a.get_slice("=", 1)))
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
