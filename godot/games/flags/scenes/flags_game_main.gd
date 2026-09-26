extends Node
## Game 8 main scene: the battlefield in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets two
## computer generals fight it out, which is what the captures record; any key takes over. "--map=N" starts on
## campaign map N; "--zod=/path/to/map.map" plays a Zod Engine map from the player's own files (the planet's
## .tileinfo is looked for in ../assets/planets next to the maps folder).

@onready var game: FlagsGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var first := 0
	var zod := ""
	for a in args:
		if a.begins_with("--map="):
			first = int(a.get_slice("=", 1))
		elif a.begins_with("--zod="):
			zod = a.get_slice("=", 1)
	if zod != "":
		var bytes := FileAccess.get_file_as_bytes(zod)
		var info := zod.get_base_dir().path_join("../assets/planets/%s.tileinfo" % ZodImport.planet_of(bytes))
		var m := ZodImport.from_files(zod, info)
		if m.w > 0:
			game.start_map(m, 5 if game.demo else -1)
		else:
			game.start(5 if game.demo else -1, first)
	else:
		game.start(5 if game.demo else -1, first)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start(-1, game.level))
