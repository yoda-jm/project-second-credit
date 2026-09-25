extends SceneTree
## Plays every replay of the local GDash checkout and prints one line per replay (OK/BAD) plus a summary.
## Run: godot --headless --path godot -s res://tools/replay_corpus.gd


func _init() -> void:
	var ok := 0
	var bad := 0
	var t0 := Time.get_ticks_msec()
	for path in GdashReference.bdcff_files():
		var cs := BdcffLoader.load_file(path)
		for cave in cs.caves:
			for replay in cave.replays:
				var r := ReplayRunner.play(cave, replay)
				var good: bool = r["success"] == replay.success and r["score"] == replay.score
				if good: ok += 1
				else: bad += 1
				print("%s %s / %s L%d: got %s %d, expected %s %d (%d frames)" % ["OK " if good else "BAD",
					path.get_file(), cave.name, replay.level, r["success"], r["score"], replay.success, replay.score,
					r["frames"]])
	print("SUMMARY %d ok, %d bad, %d s" % [ok, bad, (Time.get_ticks_msec() - t0) / 1000])
	quit()
