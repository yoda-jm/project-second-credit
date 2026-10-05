extends GdUnitTestSuite
## Each game ships as its own download (a .pck with only res://games/<id>/, see docs/updater.md), so a game may use
## core/ and its own folder, never another game's; and core/ (in the launcher download) never needs a game.

const TEXT := ["gd", "tscn", "tres", "gdshader", "gdshaderinc", "json", "cfg"]
## core files allowed to name game paths: they list the games or look inside a game's own folder
const CORE_ALLOWED := ["res://core/game_registry.gd", "res://core/packs/pack.gd"]


func test_games_use_only_core_and_their_own_folder() -> void:
	var re := RegEx.create_from_string("res://games/([a-z0-9_]+)")
	for id in DirAccess.get_directories_at("res://games"):
		for path in _text_files("res://games/" + id):
			for m in re.search_all(FileAccess.get_file_as_string(path)):
				assert_str(m.get_string(1)).override_failure_message(
					"%s uses another game's file (%s): copy it into the game or move it to core/" % [path, m.get_string()]) \
					.is_equal(id)


func test_core_needs_no_game() -> void:
	for path in _text_files("res://core"):
		if path in CORE_ALLOWED:
			continue
		assert_bool(FileAccess.get_file_as_string(path).contains("res://games/")) \
			.override_failure_message("%s names a game's file: the launcher download has no games" % path).is_false()


func test_card_art_is_in_core() -> void:
	for g in GameRegistry.GAMES:
		var card := String(g.get("card", ""))
		if card == "":
			continue  # not made yet: the launcher draws a placeholder
		assert_str(card).override_failure_message("%s's card is not in core/" % g["id"]).starts_with("res://core/")
		assert_bool(ResourceLoader.exists(card)).is_true()


func _text_files(dir: String) -> Array[String]:
	var out: Array[String] = []
	for d in DirAccess.get_directories_at(dir):
		if d not in ["tests", "tools"]:
			out.append_array(_text_files(dir.path_join(d)))
	for f in DirAccess.get_files_at(dir):
		if f.get_extension() in TEXT:
			out.append(dir.path_join(f))
	return out
