extends GdUnitTestSuite
## The library's rules (LibraryCatalog): what each game's card says from what is on this computer and what the
## update channel offers; nothing here touches the network.

const SHA := "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


func _game(id: String, scene := "res://games/x/x.tscn") -> Dictionary:
	return {"id": id, "title": id.capitalize(), "scene": scene}


func _manifest(games: Dictionary, launcher_core := 5) -> Dictionary:
	var g := {}
	for id in games:
		g[id] = {"version": games[id][0], "file": "%s-%s.pck" % [id, games[id][0]], "sha256": SHA, "size": 1_500_000,
			"min_core": games[id][1], "web": games[id].size() > 2 and games[id][2]}
	return {"format": 1, "launcher": {"core": launcher_core, "files": {"linux": {"file": "SecondCredit-linux-x86_64.AppImage", "size": 9}}}, "games": g}


func test_a_game_on_this_computer_and_up_to_date_is_ready() -> void:
	var ctx := {"manifest": _manifest({"a": ["v1", 3]}), "local": {"a": "v1"}, "core": 5}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.READY)


func test_a_newer_version_is_offered_as_an_update() -> void:
	var ctx := {"manifest": _manifest({"a": ["v2", 3]}), "local": {"a": "v1"}, "core": 5}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.UPDATE)
	assert_array(LibraryCatalog.updates([_game("a"), _game("b")], ctx)).contains_exactly(["a"])


func test_an_update_that_needs_a_newer_launcher_keeps_the_game_playable() -> void:
	var ctx := {"manifest": _manifest({"a": ["v2", 9]}), "local": {"a": "v1"}, "core": 5}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.READY)


func test_a_game_not_here_can_be_downloaded() -> void:
	var ctx := {"manifest": _manifest({"a": ["v1", 3]}), "local": {}, "core": 5}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.MISSING)
	assert_array(LibraryCatalog.missing([_game("a")], ctx)).contains_exactly(["a"])
	assert_int(LibraryCatalog.total_size(["a"], ctx["manifest"])).is_equal(1_500_000)


func test_a_game_built_for_a_newer_launcher_asks_for_it() -> void:
	var ctx := {"manifest": _manifest({"a": ["v1", 7]}), "local": {}, "core": 5}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.NEEDS_LAUNCHER)


func test_without_a_manifest_a_missing_game_waits_for_a_connection() -> void:
	assert_str(LibraryCatalog.state(_game("a"), {"manifest": {}, "local": {}, "core": 5})).is_equal(LibraryCatalog.OFFLINE)
	# and the games that are here still play
	assert_str(LibraryCatalog.state(_game("b"), {"manifest": {}, "local": {"b": "bundled"}, "core": 5})).is_equal(LibraryCatalog.READY)


func test_the_browser_lists_only_the_games_checked_there() -> void:
	var m := _manifest({"a": ["v1", 3, true], "b": ["v1", 3, false]})
	var ctx := {"manifest": m, "local": {}, "core": 5, "web": true}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.MISSING)
	assert_str(LibraryCatalog.state(_game("b"), ctx)).is_equal(LibraryCatalog.UNAVAILABLE)


func test_downloading_and_in_development() -> void:
	var ctx := {"manifest": _manifest({"a": ["v1", 3]}), "local": {}, "core": 5, "downloading": ["a"]}
	assert_str(LibraryCatalog.state(_game("a"), ctx)).is_equal(LibraryCatalog.DOWNLOADING)
	assert_str(LibraryCatalog.state(_game("c", ""), ctx)).is_equal(LibraryCatalog.IN_DEVELOPMENT)


func test_the_launcher_update() -> void:
	var m := _manifest({}, 6)
	assert_bool(LibraryCatalog.launcher_newer(m, 5)).is_true()
	assert_bool(LibraryCatalog.launcher_newer(m, 6)).is_false()
	assert_str(LibraryCatalog.launcher_file(m, "linux").get("file", "")).is_equal("SecondCredit-linux-x86_64.AppImage")
	assert_dict(LibraryCatalog.launcher_file(m, "windows")).is_empty()


func test_manifests_are_checked_before_use() -> void:
	assert_bool(LibraryCatalog.valid_manifest(_manifest({"a": ["v1", 3]}))).is_true()
	assert_bool(LibraryCatalog.valid_manifest("nope")).is_false()
	assert_bool(LibraryCatalog.valid_manifest({"format": 2, "games": {}, "launcher": {}})).is_false()
	var bad := _manifest({"a": ["v1", 3]})
	bad["games"]["a"]["file"] = "../../evil.pck"
	assert_bool(LibraryCatalog.valid_manifest(bad)).is_false()
	bad = _manifest({"a": ["v1", 3]})
	bad["games"]["a"]["sha256"] = "short"
	assert_bool(LibraryCatalog.valid_manifest(bad)).is_false()


func test_files_are_found_beside_the_manifest() -> void:
	assert_str(LibraryCatalog.url_beside("https://github.com/o/r/releases/download/latest/manifest.json", "a-v1.pck")) \
		.is_equal("https://github.com/o/r/releases/download/latest/a-v1.pck")
	assert_str(LibraryCatalog.size_text(14_200_000)).is_equal("14.2 MB")
	assert_str(LibraryCatalog.size_text(820_000)).is_equal("820 KB")


func test_a_download_is_checked_against_the_manifest() -> void:
	var path := "user://test_library_file.bin"
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string("second credit")
	f.close()
	var entry := {"size": 13, "sha256": "second credit".sha256_text()}
	assert_bool(Library._file_ok(path, entry)).is_true()
	entry["sha256"] = SHA
	assert_bool(Library._file_ok(path, entry)).is_false()
	entry = {"size": 12, "sha256": "second credit".sha256_text()}
	assert_bool(Library._file_ok(path, entry)).is_false()
	DirAccess.remove_absolute(path)


func test_development_runs_have_every_game_ready_and_stay_offline() -> void:
	assert_bool(Library.dev).is_true()
	assert_str(Library.state(GameRegistry.GAMES[0])).is_equal(LibraryCatalog.READY)
	assert_array(Library.updates()).is_empty()
	assert_bool(Library.checking).is_false()
