extends Node
## Game 6 main scene: the jungle in 3D, the HUD, sound and the pause menu. "--demo" (user argument) plays the
## campaign with the autopilot, which is what the captures record; any key takes over. With more than one campaign
## pack, the player picks one first.

@onready var game: BootsGame = $Game


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	game.demo = args.has("--demo") and not args.has("--play")
	game.demo_locked = game.demo and args.has("--locked")
	var packs := Pack.scan("boots")
	if game.demo or packs.size() < 2:
		game.start(3 if game.demo else -1)
	else:  # more than one campaign: the player picks one first, over the demo playing behind like a title screen
		game.demo = true
		game.demo_locked = true
		game.show_story = false
		game.start(3)
		$HudLayer.visible = false
		var ch := PackChooser.new()
		ch.packs = packs
		ch.accent = Color(0.6, 0.8, 0.4)
		ch.count_label = "MISSIONS"
		ch.level_count = func(p: Pack) -> int: return BootsMap.parse_campaign(p.levels_text()).size()
		ch.chosen.connect(func(p: Pack):
			game.demo = false
			game.demo_locked = false
			game.show_story = true
			$HudLayer.visible = true
			game.pack_id = p.id
			game.start())
		add_child(ch)
	var pause := PauseMenu.new()
	add_child(pause)
	pause.restart_requested.connect(func(): game.start())
