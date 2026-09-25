extends GdUnitTestSuite
## Rules of Whisker Alley: platforming in the alley, the dog, the shoes, windows and rooms.

const E = preload("res://games/whisker/engine/whisker_engine.gd")


func _engine() -> WhiskerEngine:
	var e := WhiskerEngine.new(5)
	_run(e, E.READY_SECONDS + 0.05)
	assert_int(e.phase).is_equal(E.Phase.ALLEY)
	return e


func _run(e: WhiskerEngine, seconds: float, x := 0, y := 0) -> void:
	for i in int(seconds / E.TICK):
		e.input_x = x
		e.input_y = y
		e.tick()


func _quiet(e: WhiskerEngine) -> void:
	e.dog["x"] = 23.0  # far away and walking off
	e.dog["dir"] = 1
	for w in e.windows:  # no open windows: no shoes
		w["open"] = false
		w["t"] = 100.0


func test_cat_walks_and_jumps() -> void:
	var e := _engine()
	_quiet(e)
	_run(e, 0.5, 1)
	assert_float(e.cat.pos.x).is_greater(3.0)
	e.jump()
	_run(e, 0.2)
	assert_float(e.cat.pos.y).is_greater(1.2)
	_run(e, 1.5)
	assert_bool(e.cat.on_ground).is_true()


func test_can_lid_bounces_the_cat_onto_the_fence() -> void:
	var e := _engine()
	_quiet(e)
	e.cat.pos = Vector2(E.CAN_X[0], E.CAN_TOP)
	e.cat.on_ground = true
	_run(e, 0.05)
	assert_str(e.cat.ground.get("kind", "")).is_equal("can")
	e.jump()
	_run(e, 1.5, 1)  # bounce and drift right: lands on the fence
	assert_bool(e.cat.on_ground).is_true()
	assert_float(e.cat.pos.y).is_equal_approx(E.FENCE_TOP, 0.01)


func test_clothesline_carries_the_cat() -> void:
	var e := _engine()
	_quiet(e)
	e.cat.pos = Vector2(10.0, E.LINE_Y[0])
	e.cat.vel = Vector2.ZERO
	_run(e, 1.0)
	assert_float(e.cat.pos.x).is_equal_approx(10.0 + E.LINE_SPEED[0], 0.1)


func test_down_and_jump_drops_through() -> void:
	var e := _engine()
	_quiet(e)
	e.cat.pos = Vector2(10.0, E.FENCE_TOP)
	_run(e, 0.1)
	e.jump()
	_run(e, 1.0, 0, -1)
	assert_float(e.cat.pos.y).is_less(0.1)


func test_dog_catches_a_cat_on_the_ground() -> void:
	var e := _engine()
	_quiet(e)
	e.dog["x"] = 6.0
	e.cat.pos = Vector2(2.0, 0.0)
	_run(e, 2.0)
	assert_int(e.lives).is_equal(E.LIVES - 1)
	assert_int(e.phase).is_equal(E.Phase.DYING)


func test_dog_cannot_reach_the_fence() -> void:
	var e := _engine()
	_quiet(e)
	e.dog["x"] = 6.0
	e.cat.pos = Vector2(5.0, E.FENCE_TOP)
	_run(e, 3.0)
	assert_int(e.lives).is_equal(E.LIVES)


func test_a_shoe_knocks_the_cat_off() -> void:
	var e := _engine()
	_quiet(e)
	e.cat.pos = Vector2(9.0, E.FENCE_TOP)
	_run(e, 0.1)
	e.shoes.append({"pos": e.cat.pos + Vector2(-1.0, 0.3), "vel": Vector2(10, 0), "spin": 0.0})
	_run(e, 0.2)
	assert_float(e.stunned).is_greater(0.0)
	_run(e, 1.0)
	assert_float(e.cat.pos.y).is_less(E.FENCE_TOP)


func test_open_window_leads_into_a_room_and_the_broom_sweeps_out() -> void:
	var e := _engine()
	_quiet(e)
	var w := e.windows[0]
	w["open"] = true
	w["t"] = 100.0
	e.cat.pos = (w["rect"] as Rect2).get_center() - Vector2(0, 0.3)
	_run(e, 0.05)
	assert_int(e.phase).is_equal(E.Phase.ROOM)
	assert_object(e.room).is_not_null()
	_run(e, WhiskerRoom.ROOM_SECONDS + 0.5)
	assert_int(e.phase).is_equal(E.Phase.ALLEY)
	assert_int(e.lives).is_equal(E.LIVES)
	assert_int(e.rooms_won).is_equal(0)


func _room(kind: int) -> WhiskerEngine:
	var e := _engine()
	_quiet(e)
	for w in e.windows:
		if w["room"] == kind:
			w["open"] = true
			e.cat.pos = (w["rect"] as Rect2).get_center() - Vector2(0, 0.3)
			break
	_run(e, 0.05)
	assert_int(e.room.kind).is_equal(kind)
	return e


func test_fishbowl_catching_all_fish_wins_the_room() -> void:
	var e := _room(E.RoomKind.FISHBOWL)
	var r := e.room as FishbowlRoom
	r.eels.clear()
	var before := e.score
	for i in 3:
		e.cat.pos = r.fish[0]["pos"] - Vector2(0, 0.3)
		_run(e, E.TICK * 2)
	assert_int(e.rooms_won).is_equal(1)
	assert_int(e.phase).is_equal(E.Phase.ALLEY)
	assert_int(e.score).is_greater(before + 3 * 150)


func test_fishbowl_running_out_of_air_costs_a_life() -> void:
	var e := _room(E.RoomKind.FISHBOWL)
	var r := e.room as FishbowlRoom
	r.eels.clear()
	r.fish.clear()
	r.goal = 99
	e.cat.pos = FishbowlRoom.BOWL.position + Vector2(3.0, 0.2)
	_run(e, FishbowlRoom.AIR_SECONDS + 0.5, 0, -1)
	assert_int(e.lives).is_equal(E.LIVES - 1)


func test_mice_room_catching_five_mice_wins() -> void:
	var e := _room(E.RoomKind.MICE)
	var r := e.room as MiceRoom
	var guard := 0
	while e.rooms_won == 0 and guard < 3000:
		guard += 1
		if not r.mice.is_empty():  # teleport onto the first mouse: we test the rules, not the aim
			e.cat.pos = r.mouse_pos(r.mice[0])
			e.cat.vel = Vector2.ZERO
		e.tick()
	assert_int(e.rooms_won).is_equal(1)


func test_birdcage_knock_the_cage_then_catch_the_bird() -> void:
	var e := _room(E.RoomKind.BIRDCAGE)
	var r := e.room as BirdcageRoom
	e.cat.pos = BirdcageRoom.CAGE.position + Vector2(0.5, 0.2)
	_run(e, E.TICK)
	assert_bool(r.cage_down).is_true()
	e.cat.pos = Vector2(1.0, 0.0)
	_run(e, 1.0)
	assert_bool(r.bird["free"]).is_true()
	e.cat.pos = (r.bird["pos"] as Vector2) - Vector2(0, 0.3)
	_run(e, E.TICK)
	assert_int(e.rooms_won).is_equal(1)


func test_nine_lives_then_game_over() -> void:
	var e := _engine()
	for i in E.LIVES:
		_quiet(e)
		e.dog["x"] = e.cat.pos.x
		_run(e, E.DYING_SECONDS + E.READY_SECONDS + 0.2)
	assert_int(e.phase).is_equal(E.Phase.GAME_OVER)


func test_same_seed_and_inputs_replay_identically() -> void:
	var out := []
	for run in 2:
		var e := WhiskerEngine.new(9)
		for i in 2400:
			e.input_x = [1, 1, 0, -1][(i / 70) % 4]
			if i % 53 == 0:
				e.jump()
			e.tick()
		out.append([e.score, e.lives, e.cat.pos, e.dog["x"], e.shoes.size()])
	assert_array(out[0]).is_equal(out[1])
