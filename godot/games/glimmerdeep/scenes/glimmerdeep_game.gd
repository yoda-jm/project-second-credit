extends Node
## Game 1 main scene: one cave in the 3D diorama view with its HUD. Pass "--demo" (user argument) to run the
## cave's demo replay instead of waiting for the player (the capture script does this), or "--demo=N" for the
## N-th replay (1: the hero gets crushed, for the death effect). Without --demo the campaign starts (the pack's
## caves in order, with its story), or the single cave with "--cave". "--descent=N" shows the campaign's cave N
## played by the demo bot (for captures). F2 opens the two-player race.

@export_file("*.bd") var cave_file := "res://games/glimmerdeep/packs/second-credit/first-light.bd"
@export var cave_index := 0

@onready var game: CaveGame = $Game


func _ready() -> void:
	var demo := false
	var demo_index := 0
	for arg in OS.get_cmdline_user_args():
		if arg == "--demo":
			demo = true
		elif arg.begins_with("--demo="):
			demo = true
			demo_index = int(arg.substr(7))
	var pack := Pack.find("glimmerdeep", "second-credit")
	var descent := -1
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--descent="):
			descent = int(arg.get_slice("=", 1))
	if descent >= 0 and pack:  # captures: the campaign's cave N, played by the demo bot
		game.autopilot = true
		game.start_campaign(pack, descent)
	elif demo or pack == null or OS.get_cmdline_user_args().has("--cave"):
		game.load_cave(cave_file, cave_index, demo, demo_index)
	else:  # the player: the campaign, from the first cave
		game.start_campaign(pack)
	game.demo_locked = demo and OS.get_cmdline_user_args().has("--locked")
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(game.restart)


## F2: the two-player race, split screen.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F2:
		get_tree().change_scene_to_file("res://games/glimmerdeep/scenes/glimmerdeep_race.tscn")
