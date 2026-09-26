extends GdUnitTestSuite
## The Descent: our campaign pack of eight caves, each one cleared by the autopilot, and the campaign flow.


func _pack() -> Pack:
	return Pack.find("glimmerdeep", "second-credit")


func test_pack_holds_eight_caves_with_a_story() -> void:
	var p := _pack()
	assert_object(p).is_not_null()
	var n := 0
	for f in p.levels:
		n += BdcffLoader.load_file(f).caves.size()
	assert_int(n).is_equal(8)
	assert_bool(p.card_before(0).is_empty()).is_false()
	for i in range(1, 8):
		assert_bool(p.card_before(i).is_empty()).override_failure_message("no story before cave %d" % (i + 1)).is_false()


func test_every_cave_can_be_cleared() -> void:
	for c in BdcffLoader.load_file("res://games/glimmerdeep/packs/second-credit/the-descent.bd").caves:
		assert_bool(DemoBot.record(c)["success"]).override_failure_message("%s is not cleared by the bot" % c.name).is_true()


func test_campaign_moves_on_and_counts_lives() -> void:
	var g := CaveGame.new()
	g.countdown_seconds = 0.0
	add_child(g)
	g.start_campaign(_pack())
	for c in g.get_children():  # close the intro card
		if c is StoryCard:
			c._close()
	assert_int(g.caves.size()).is_equal(8)
	assert_int(g.cave_no).is_equal(0)
	# a cleared cave: the next one, the score kept
	g.engine.player_state = CaveRendered.PlayerState.EXITED
	g.score = 500
	g._after_cave()
	assert_int(g.cave_no).is_equal(1)
	assert_int(g.score).is_equal(500)
	# a lost cave: one life less, same cave, the score back to what it was when the cave began
	g.story_open = false
	g.score = 900
	g.engine.player_state = CaveRendered.PlayerState.DIED
	g._after_cave()
	assert_int(g.lives).is_equal(CaveGame.LIVES - 1)
	assert_int(g.cave_no).is_equal(1)
	assert_int(g.score).is_equal(500)
	g.queue_free()
