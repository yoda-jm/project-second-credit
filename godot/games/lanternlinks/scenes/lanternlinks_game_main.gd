extends Node
## Game 26 main scene: the lantern-garden course in 3D, the HUD, sound and the pause menu. "--demo" (user argument)
## lets the CPU play two seats (what the captures record); any key takes over. "--hole=N" starts at a hole,
## "--players=N" seats N people (and skips the seats screen).

@onready var game: LinksGame = $Game


func _ready() -> void:
	var args := Array(OS.get_cmdline_user_args())
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	for a in args:
		if a.begins_with("--hole="):
			game.first_hole = clampi(int(a.substr(7)) - 1, 0, game.holes.size() - 1)
		elif a.begins_with("--players="):
			game.seats.clear()
			for i in clampi(int(a.substr(10)), 1, 4):
				game.seats.append({"name": "PLAYER %d" % (i + 1), "cpu": false})
	if game.demo:
		game.demo_seats()
	if game.demo or args.any(func(a): return a.begins_with("--players=")):
		game.begin()
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func():
		game.setup = false
		game.begin())
