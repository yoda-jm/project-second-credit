extends GdUnitTestSuite
## Our own first cave: it loads, its demo replay finishes the cave, and the scene plays it.

const FILE := "res://games/rocks/packs/second-credit/first-light.bd"


func test_demo_replay_finishes_the_cave() -> void:
	var cave := BdcffLoader.load_file(FILE).caves[0]
	var replay := cave.replays[0]
	var r := ReplayRunner.play(cave, replay)
	assert_bool(r["success"]).is_true()
	assert_int(r["score"]).is_equal(replay.score)


func test_demo_bot_still_solves_it() -> void:
	var cave := BdcffLoader.load_file(FILE).caves[0]
	assert_bool(DemoBot.record(cave)["success"]).is_true()


func test_scene_plays_the_demo() -> void:
	var runner := scene_runner("res://games/rocks/scenes/cave_player.tscn")
	await runner.simulate_frames(150, 66)  # ~10 s of game time
	var engine: CaveEngine = runner.scene().engine
	assert_int(engine.diamonds_collected).is_greater(0)


func test_3d_game_scene_runs() -> void:
	var runner := scene_runner("res://games/rocks/scenes/rocks_game.tscn")
	await runner.simulate_frames(20, 100)
	var game: CaveGame = runner.find_child("Game")
	assert_object(game.engine).is_not_null()
	assert_bool(game.engine.hatched).is_true()
