extends GdUnitTestSuite
## Engine exactness against GDash: every replay in GDash's cave sets must give the same outcome (success and
## score) as GDash's own engine, run by tools/gdash_port/reference.sh (results in .tools/ref/gdash-results.txt).
## The scores stored in the files are not used: some were recorded by older GDash versions.
## Needs the local GDash checkout and the results file, and takes about 20 minutes, so it only runs with
## GLIMMERDEEP_REFERENCE=1 (tools/test.sh passes the environment through).


func test_replays_match_gdash_engine() -> void:
	if OS.get_environment("GLIMMERDEEP_REFERENCE") != "1":
		print("set GLIMMERDEEP_REFERENCE=1 to compare the engine with GDash on the whole corpus")
		return
	var results_path := GdashReference.root().path_join("../gdash-results.txt").simplify_path()
	if not GdashReference.available() or not FileAccess.file_exists(results_path):
		print("GDash reference results not found, skipping (run tools/gdash_port/reference.sh)")
		return
	var expected := {}  # file name -> Array of "success score"
	for line in FileAccess.get_file_as_string(results_path).split("\n", false):
		var m := RegEx.create_from_string("^(\\S+) (?:OK |BAD) \\| .*: got (\\w+) (-?\\d+),").search(line)
		if m:
			if not expected.has(m.get_string(1)):
				expected[m.get_string(1)] = []
			expected[m.get_string(1)].append("%s %s" % [m.get_string(2), m.get_string(3)])
	var checked := 0
	var failures := PackedStringArray()
	for path in GdashReference.bdcff_files():
		var cs := BdcffLoader.load_file(path)
		var i := 0
		for cave in cs.caves:
			for replay in cave.replays:
				var r := ReplayRunner.play(cave, replay)
				var got := "%s %d" % [str(r["success"]).to_lower(), r["score"]]
				var want: String = expected.get(path.get_file(), [])[i] if i < expected.get(path.get_file(), []).size() else "?"
				checked += 1
				i += 1
				if got != want:
					failures.append("%s / %s L%d: got %s, GDash %s" % [path.get_file(), cave.name, replay.level, got, want])
	print("played %d replays, %d differ from GDash" % [checked, failures.size()])
	for f in failures.slice(0, 40):
		print("  ", f)
	assert_int(checked).is_greater(0)
	assert_array(failures).is_empty()
