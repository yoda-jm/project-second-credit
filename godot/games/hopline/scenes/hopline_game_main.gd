extends Node
## Game 16 main scene: the canal town in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets the
## autopilot play, which is what the captures record; any key takes over. "--stage=N" starts at stage N (0: the golden
## afternoon, 1: sunset, 2: night).

@onready var game: HopGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	for a in args:
		if a.begins_with("--stage="):
			game.first_stage = maxi(0, int(a.get_slice("=", 1)))
	game.start(4 if game.demo else -1)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func():
		game.first_stage = 0
		game.start())
