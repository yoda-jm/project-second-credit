extends Node
## Game 35 main scene: the dungeon in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets the CPU
## heroes play, which is what the captures record; any key takes over. "--players=N" (heroes), "--humans=N",
## "--level=N".

@onready var game: TorchGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var at := 0
	for a in args:
		if a.begins_with("--level="):
			at = int(a.substr(8)) - 1
		elif a.begins_with("--players="):
			game.heroes = clampi(int(a.substr(10)), 1, 4)
		elif a.begins_with("--humans="):
			game.humans = clampi(int(a.substr(9)), 0, 4)
	game.start(at)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start(0))
