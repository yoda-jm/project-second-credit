extends Node
## Game 5 main scene: the valley in 3D, the HUD, sound and the pause menu. "--demo" (user argument) plays the
## games with a CPU athlete, which is what the captures record; any key goes to the players' setup.

@onready var game: FrostpeakGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var first := 0
	for a in args:
		if a.begins_with("--event="):
			first = int(a.get_slice("=", 1))
	if game.demo:
		game.start(5, first)
	else:
		game.start_setup()
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start_setup())
