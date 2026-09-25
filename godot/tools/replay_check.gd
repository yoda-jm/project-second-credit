extends SceneTree
## Plays the replays of one BDCFF file and compares them with their recorded outcome.
## Run: godot --headless --path godot -s res://tools/replay_check.gd -- /path/file.bd [cave-index]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var cs := BdcffLoader.load_file(args[0])
	var only := int(args[1]) if args.size() > 1 else -1
	var ok := 0
	var bad := 0
	for ci in cs.caves.size():
		if only >= 0 and ci != only:
			continue
		var cave := cs.caves[ci]
		for replay in cave.replays:
			var t0 := Time.get_ticks_msec()
			var r := ReplayRunner.play(cave, replay)
			var match_: bool = r["success"] == replay.success and r["score"] == replay.score
			if match_: ok += 1
			else: bad += 1
			print("%s %-24s L%d  got %-5s %5d  expected %-5s %5d  %5d frames %5d ms" % ["OK " if match_ else "BAD",
				cave.name.left(24), replay.level, r["success"], r["score"], replay.success, replay.score, r["frames"],
				Time.get_ticks_msec() - t0])
	print("%d ok, %d bad" % [ok, bad])
	quit(0 if bad == 0 else 1)
