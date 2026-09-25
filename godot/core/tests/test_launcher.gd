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
