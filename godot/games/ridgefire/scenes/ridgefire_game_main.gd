extends Node
## Game 30 main scene: the battlefield in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets
## CPU tanks play, which is what the captures record; any key takes over (to the seats). "--players=N", "--humans=N",
## "--rounds=N" skip the seats.

@onready var game: RidgeGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var quick := false
	var humans := 1
	for a in args:
		if a.begins_with("--players="):
			game.seats = clampi(int(a.substr(10)), 2, 4)
			quick = true
		elif a.begins_with("--humans="):
			humans = clampi(int(a.substr(9)), 0, 4)
			quick = true
		elif a.begins_with("--land="):
			game.land = clampi(int(a.substr(7)) - 1, 0, 4)
		elif a.begins_with("--rounds="):
			game.rounds = clampi(int(a.substr(9)), 1, 10)
	for i in 4:
		game.cpu[i] = i >= humans
	if quick and not game.demo:
		game._begin()
	else:
		game.start()
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func():
		game._wait()
		game.mode = RidgeGame.Mode.SEATS)
