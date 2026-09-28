extends GdUnitTestSuite
## Frostpeak Games: the events' rules and the competition's results and medals.

const W = preload("res://games/frostpeak/engine/events/winter_event.gd")


func _play(ev: WinterEvent, max_seconds := 120.0) -> void:
	var n := 0
	while ev.phase != W.Phase.DONE and n < int(max_seconds * 60.0):
		ev.tick()
		n += 1


func test_skating_in_rhythm_beats_forty_seconds() -> void:
	var s := SpeedSkating.new(1)
	s.auto = true
	s.skill = 1.0
	_play(s)
	assert_float(s.result).is_less(40.0)


func test_skating_off_the_beat_is_slow() -> void:
	var s := SpeedSkating.new(1)
	s.auto = true
	s.skill = 0.1
	_play(s)
	assert_float(s.result).is_greater(50.0)


func test_wrong_foot_costs_speed() -> void:
	var s := SpeedSkating.new(1)
	s.phase = W.Phase.RUN
	s.speed = 10.0
	s.next_foot = "left"
	s.press("right")
	s.tick()
	assert_float(s.speed).is_less(9.6)


func test_two_false_starts_disqualify() -> void:
	var s := SpeedSkating.new(1)
	s.press("left")
	s.tick()
	assert_int(s.false_starts).is_equal(1)
	assert_int(s.phase).is_equal(W.Phase.READY)
	s.press("right")
	s.tick()
	assert_int(s.phase).is_equal(W.Phase.DONE)
	assert_str(s.result_text).is_equal("DISQUALIFIED")


func test_good_jump_reaches_the_k_point() -> void:
	var j := SkiJump.new(2)
	j.auto = true
	j.skill = 0.95
	_play(j)
	assert_float(j.distance).is_greater(SkiJump.K - 3.0)
	assert_bool(j.telemark).is_true()
	assert_bool(j.fell).is_false()


func test_no_takeoff_is_a_short_jump() -> void:
	var j := SkiJump.new(2)
	j.phase = W.Phase.RUN
	j.hold_down = true
	_play(j)
	assert_float(j.distance).is_less(SkiJump.K - 10.0)


func test_no_telemark_costs_style() -> void:
	var j := SkiJump.new(3)
	j.auto = true
	j.skill = 0.9
	var n := 0
	while j.phase != W.Phase.DONE and n < 60 * 60:
		if j.stage == SkiJump.Stage.FLIGHT:
			j.auto = false  # nobody presses for the landing
			j.hold_up = j.angle > 0.08
			j.hold_down = j.angle < -0.08
		j.tick()
		n += 1
	assert_bool(j.telemark).is_false()
	assert_float(j.style).is_less(52.0)  # telemark landings score about 55


func test_hill_has_a_large_hill_profile() -> void:
	# the K point sits about 0.55-0.62 as far down as it is out (FIS large hills), on a 35.5 degree slope
	var k := SkiHill.land_point(SkiHill.K)
	assert_float(-k.y / k.x).is_between(0.55, 0.62)
	assert_float(rad_to_deg(SkiHill.land_angle(SkiHill.K))).is_equal_approx(35.5, 0.1)
	assert_float(rad_to_deg(SkiHill.land_angle(SkiHill.HS))).is_equal_approx(32.1, 0.1)
	# the in-run: 35 degrees at the gate, 11 on the table, the gate some 40-50 m above the lip
	assert_float(rad_to_deg(SkiHill.inrun_angle(0.0))).is_equal_approx(35.0, 0.01)
	assert_float(rad_to_deg(SkiHill.inrun_angle(SkiHill.INRUN - 1.0))).is_equal_approx(11.0, 0.01)
	assert_float(SkiHill.inrun_point(0.0).y).is_between(40.0, 50.0)
	assert_vector(SkiHill.inrun_point(SkiHill.INRUN)).is_equal_approx(Vector2.ZERO, Vector2(0.01, 0.01))
	# the outrun is level, 80-90 m below the lip
	assert_float(SkiHill.land_angle(220.0)).is_equal(0.0)
	assert_float(SkiHill.outrun_y()).is_between(-90.0, -80.0)


func test_distance_is_measured_along_the_hill() -> void:
	for s in [10.0, 60.0, SkiHill.K, SkiHill.HS]:
		var p := SkiHill.land_point(s)
		assert_float(SkiHill.distance_at(p.x)).is_equal_approx(s, 0.05)
		assert_float(SkiHill.ground_y(p.x)).is_equal_approx(p.y, 0.05)
	# the profile only falls, then levels out
	var last := 0.0
	for x in range(1, 170):
		var y := SkiHill.ground_y(x)
		assert_float(y).is_less_equal(last)
		last = y


func test_poor_flight_falls_short_of_a_good_one() -> void:
	var good := SkiJump.new(4)
	good.auto = true
	good.skill = 0.95
	_play(good)
	var poor := SkiJump.new(4)
	poor.auto = true
	poor.skill = 0.3
	_play(poor)
	assert_float(poor.distance).is_less(good.distance - 5.0)
	assert_float(good.distance).is_less(SkiHill.HS + 8.0)


func test_competition_ranks_and_awards_medals() -> void:
	var c := Competition.new([{"name": "You", "nation": 0}], 3, 7)
	assert_int(c.athletes.size()).is_equal(4)
	c.record(0, 37.5)
	c.play_cpus()
	var rk := c.ranking("speed_skating")
	assert_int(rk[0]).is_equal(0)  # 37.5 s beats every CPU rival
	c.next_event()
	c.record(0, 50.0)
	c.play_cpus()
	var m := c.medals()
	assert_int(m[0][0]).is_equal(1)
	assert_bool(c.finished()).is_false()
	c.next_event()
	assert_bool(c.finished()).is_true()


func test_cpu_results_are_deterministic() -> void:
	var a := Competition.new([], 4, 11)
	var b := Competition.new([], 4, 11)
	a.play_cpus()
	b.play_cpus()
	assert_dict(a.results).is_equal(b.results)
