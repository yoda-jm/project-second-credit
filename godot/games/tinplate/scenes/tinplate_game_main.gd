extends Node
## Game 31 main scene: the tabletop tracks in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets
## CPU cars race, which is what the captures record; any key takes over. "--track=N" starts at a track,
## "--players=2" seats a second player.

@onready var game: TinGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var at := 0
	for a in args:
		if a.begins_with("--track="):
			at = int(a.substr(8)) - 1
		elif a.begins_with("--players="):
			game.humans = clampi(int(a.substr(10)), 1, 2)
	game.start(at)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start(0))
