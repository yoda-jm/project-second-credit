extends SceneTree
## Prints a BDCFF [replay] where the demo bot gets crushed by a boulder (see DemoBot.record_death).
## Run: godot --headless --path godot -s res://tools/record_death_demo.gd -- res://path/file.bd


func _init() -> void:
	var cave := BdcffLoader.load_file(OS.get_cmdline_user_args()[0]).caves[0]
	var r := DemoBot.record_death(cave)
	print("result: died=%s frames=%d" % [r["died"], r["frames"]])
	print("[replay]\nLevel=1\nRandomSeed=0\nPlayer=DemoBot (crushed on purpose)\nScore=0\nSuccess=false\nMovements=%s\n[/replay]" % r["movements"])
	quit()
