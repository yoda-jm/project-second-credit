extends SceneTree
## Records a DemoBot run on a cave and prints it as a BDCFF [replay] section.
## Run: godot --headless --path godot -s res://tools/record_demo.gd -- res://path/file.bd [cave-index] [level]


func _init() -> void:
	var a := OS.get_cmdline_user_args()
	var cs := BdcffLoader.load_file(a[0])
	var cave := cs.caves[int(a[1]) if a.size() > 1 else 0]
	var level := int(a[2]) if a.size() > 2 else 0
	var r := DemoBot.record(cave, level, 0)
	print("result: success=%s score=%d frames=%d state=%d" % [r["success"], r["score"], r["frames"], r["state"]])
	print("[replay]\nLevel=%d\nRandomSeed=0\nPlayer=DemoBot\nScore=%d\nSuccess=%s\nMovements=%s\n[/replay]" % [
		level + 1, r["score"], str(r["success"]).to_lower(), r["movements"]])
	quit()
