extends Node
## Game 24 main scene: the beach in 3D, the HUD, sound and the pause menu. "--demo" (user argument) lets two CPU blobs
## play, which is what the captures record; any key takes over. "--versus" starts with two players.

@onready var game: SpikeGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	game.versus = args.has("--versus")
	game.start()
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
