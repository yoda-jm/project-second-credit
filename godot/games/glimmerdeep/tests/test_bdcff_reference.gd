extends GdUnitTestSuite
## Loader exactness against GDash: every replay stores the checksum of the cave GDash rendered for it.
## Needs the local GDash checkout (see tools/gdash_port); skipped otherwise.


func test_replay_checksums_match_gdash() -> void:
	if not GdashReference.available():
		print("GDash checkout not found, skipping")
		return
	var checked := 0
	var failures := PackedStringArray()
	for path in GdashReference.bdcff_files():
		var cs := BdcffLoader.load_file(path)
		for cave in cs.caves:
			for replay in cave.replays:
				if replay.checksum == 0:
					continue
				var rendered := CaveRendered.new(cave, replay.level - 1, replay.seed)
				checked += 1
				if rendered.adler_checksum() != (replay.checksum & 0xffffffff):
					failures.append("%s / %s (level %d)" % [path.get_file(), cave.name, replay.level])
	print("checked %d replay checksums, %d mismatches" % [checked, failures.size()])
	for f in failures.slice(0, 20):
		print("  mismatch: ", f)
	assert_int(checked).is_greater(0)
	assert_array(failures).is_empty()


func test_all_reference_files_load() -> void:
	if not GdashReference.available():
		return
	var caves := 0
	for path in GdashReference.bdcff_files():
		var cs := BdcffLoader.load_file(path)
		caves += cs.caves.size()
		for w in cs.warnings:
			if not w.contains("unknown tag"):
				print(path.get_file(), ": ", w)
	print("loaded %d caves" % caves)
	assert_int(caves).is_greater(100)
