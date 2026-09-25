extends GdUnitTestSuite
## Our own first cave: it loads, its demo replay finishes the cave, and the scene plays it.

const FILE := "res://games/glimmerdeep/packs/second-credit/first-light.bd"


func test_demo_replay_finishes_the_cave() -> void:
	var cave := BdcffLoader.load_file(FILE).caves[0]
	var replay := cave.replays[0]
	var r := ReplayRunner.play(cave, replay)
	assert_bool(r["success"]).is_true()
	assert_int(r["score"]).is_equal(replay.score)


func test_demo_bot_still_solves_it() -> void:
	var cave := BdcffLoader.load_file(FILE).caves[0]
	assert_bool(DemoBot.record(cave)["success"]).is_true()


func test_game_scene_plays_the_demo() -> void:
	var runner := scene_runner("res://games/glimmerdeep/scenes/glimmerdeep_game.tscn")
	var game: CaveGame = runner.find_child("Game")
	game.load_cave(FILE, 0, true)
	await runner.simulate_frames(130, 100)  # 3 s countdown, then 10 s of demo
	assert_bool(game.playing_demo).is_true()
	assert_int(game.engine.diamonds_collected).is_greater(0)


func test_3d_game_scene_runs() -> void:
	var runner := scene_runner("res://games/glimmerdeep/scenes/glimmerdeep_game.tscn")
	await runner.simulate_frames(60, 100)  # 3 s countdown, then the cave hatches
	var game: CaveGame = runner.find_child("Game")
	assert_object(game.engine).is_not_null()
	assert_bool(game.engine.hatched).is_true()


func test_death_demo_crushes_the_hero() -> void:
	var cave := BdcffLoader.load_file(FILE).caves[0]
	var r := ReplayRunner.play(cave, cave.replays[1])
	assert_bool(r["success"]).is_false()
	assert_int(r["engine"].player_state).is_equal(CaveRendered.PlayerState.DIED)
