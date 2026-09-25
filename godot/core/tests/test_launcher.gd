extends GdUnitTestSuite
## The launcher opens with every registered game, and settings round-trip through the config file.


func test_launcher_lists_the_games() -> void:
	var runner := scene_runner("res://core/ui/launcher.tscn")
	await runner.simulate_frames(10, 50)
	var launcher = runner.scene()
	assert_int(launcher._cards.size()).is_equal(GameRegistry.GAMES.size())
	assert_int(launcher._selected).is_equal(0)


func test_every_playable_game_scene_exists() -> void:
	for g in GameRegistry.GAMES:
		if g["scene"] != "":
			assert_bool(ResourceLoader.exists(g["scene"])).is_true()


func test_settings_save_and_load() -> void:
	var before: float = Settings.volume["Music"]
	Settings.volume["Music"] = 0.35
	Settings.save_settings()
	Settings.volume["Music"] = 1.0
	Settings.load_settings()
	assert_float(Settings.volume["Music"]).is_equal_approx(0.35, 0.001)
	Settings.volume["Music"] = before
	Settings.save_settings()


func test_pause_menu_is_on_screen() -> void:
	var host := Node.new()
	add_child(host)
	var pause := PauseMenu.new()
	host.add_child(pause)
	await get_tree().process_frame
	pause._open()
	await get_tree().process_frame
	await get_tree().process_frame
	var panel: Control = pause._buttons[0].get_parent().get_parent()
	var screen := Rect2(Vector2.ZERO, pause.get_viewport().get_visible_rect().size)
	assert_bool(screen.encloses(panel.get_global_rect())).is_true()
	pause._resume()
	host.queue_free()


func test_in_game_credits_match_credits_md() -> void:
	var root := ProjectSettings.globalize_path("res://").path_join("../CREDITS.md").simplify_path()
	if not FileAccess.file_exists(root):
		return
	assert_str(FileAccess.get_file_as_string("res://core/ui/credits.md")).is_equal(FileAccess.get_file_as_string(root))
