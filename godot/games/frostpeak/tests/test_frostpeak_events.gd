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
	# a clean race beats the typical CPU skater (form 0.72)
	assert_float(s.result).is_less(SpeedSkating.cpu_time(0.72))


func test_skating_off_the_beat_is_slow() -> void:
	var s := SpeedSkating.new(1)
	s.auto = true
	s.skill = 0.1
	_play(s)
	# a sloppy race loses to every CPU skater
	assert_float(s.result).is_greater(SpeedSkating.cpu_time(0.0))


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
	assert_str(c.event_name()).is_equal("biathlon")
	c.record(0, 100.0)  # a clean, quick race wins it
	c.play_cpus()
	assert_int(c.ranking("biathlon")[0]).is_equal(0)
	assert_int(c.medals()[0][0]).is_equal(2)
	c.next_event()
	assert_bool(c.finished()).is_true()


func test_cpu_results_are_deterministic() -> void:
	var a := Competition.new([], 4, 11)
	var b := Competition.new([], 4, 11)
	a.play_cpus()
	b.play_cpus()
	assert_dict(a.results).is_equal(b.results)


# ------------------------------------------------------------------ biathlon

func test_biathlon_course_is_a_closed_loop_with_a_range() -> void:
	var lap := BiathlonCourse.lap()
	assert_float(lap).is_between(400.0, 470.0)
	assert_vector(BiathlonCourse.point(0.0)).is_equal_approx(BiathlonCourse.point(lap), Vector3(0.01, 0.01, 0.01))
	# climbs and descents a skater can manage, the stadium level
	var s := 0.0
	while s < lap:
		assert_float(absf(BiathlonCourse.slope(s))).is_less(0.16)
		s += 2.0
	assert_float(BiathlonCourse.point(BiathlonCourse.RANGE_S).y).is_equal_approx(0.0, 0.05)
	# the mat beside the straight, the targets fifty metres off
	var m := BiathlonCourse.mat()
	assert_float(m.distance_to(BiathlonCourse.point(BiathlonCourse.RANGE_S))).is_equal_approx(BiathlonCourse.MAT_OFF, 0.01)
	assert_float(Vector2(m.x, m.z).distance_to(Vector2(BiathlonCourse.targets().x, BiathlonCourse.targets().z))).is_equal_approx(50.0, 0.01)
	# the penalty loop leaves the straight and comes back to it
	assert_float(BiathlonCourse.pen_loop()).is_between(45.0, 70.0)
	var p0 := BiathlonCourse.pen_point(0.0)
	assert_vector(Vector3(p0.x, 0, p0.z)).is_equal_approx(Vector3(BiathlonCourse.xz(BiathlonCourse.PEN_S).x, 0, BiathlonCourse.xz(BiathlonCourse.PEN_S).y), Vector3(0.05, 0.05, 0.05))


func test_biathlon_clean_race_takes_about_two_minutes() -> void:
	var b := Biathlon.new(3)
	b.auto = true
	b.skill = 1.0
	_play(b, 400.0)
	assert_int(b.phase).is_equal(W.Phase.DONE)
	assert_int(b.misses).is_equal(0)
	assert_int(b.shot).is_equal(Biathlon.SHOTS)
	assert_float(b.result).is_between(105.0, 135.0)
	# a CPU in top form is on the same scale
	assert_float(Biathlon.cpu_time(1.0)).is_equal_approx(b.result, 8.0)


func test_biathlon_rhythm_beats_rushing() -> void:
	var good := Biathlon.new(5)
	good.auto = true
	good.skill = 1.0
	_play(good, 400.0)
	var poor := Biathlon.new(5)
	poor.auto = true
	poor.skill = 0.3
	_play(poor, 400.0)
	assert_float(poor.result).is_greater(good.result + 15.0)


func test_biathlon_misses_are_penalty_loops() -> void:
	var b := Biathlon.new(9)
	b.auto = true
	b.skill = 0.25
	var saw_penalty := false
	var n := 0
	while b.phase != W.Phase.DONE and n < 60 * 400:
		b.tick()
		saw_penalty = saw_penalty or b.stage == Biathlon.Stage.PENALTY
		n += 1
	assert_int(b.misses).is_greater(0)
	assert_bool(saw_penalty).is_true()
	assert_float(b.pen_total).is_equal_approx(b.misses * BiathlonCourse.pen_loop(), 0.01)
	assert_float(b.pen_done).is_greater_equal(b.pen_total)


func test_biathlon_heart_races_then_settles_at_the_range() -> void:
	var b := Biathlon.new(4)
	b.auto = true
	b.skill = 0.9
	var hr_in := 0.0
	var n := 0
	while n < 60 * 400 and not (b.stage == Biathlon.Stage.RANGE and b.range_t > Biathlon.SETTLE):
		b.tick()
		if b.stage == Biathlon.Stage.RANGE and hr_in == 0.0:
			hr_in = b.hr
		n += 1
	assert_float(hr_in).is_greater(135.0)  # skied hard
	assert_float(b.hr).is_less(hr_in - 12.0)  # lying still, it comes down
	# the calmer the pulse, the steadier the sight
	var calm := b.sway()
	b.hr = 180.0
	assert_float(b.sway()).is_greater(calm * 1.5)


func test_biathlon_hits_close_the_targets_only_on_target() -> void:
	var b := Biathlon.new(6)
	b.phase = W.Phase.RUN
	b.stage = Biathlon.Stage.RANGE
	b.range_t = Biathlon.SETTLE + 0.1
	b.hr = 72.0
	b._base_to = Biathlon.target(0)
	b.base = Biathlon.target(0)
	b.press("action")
	b.tick()
	assert_int(b.shot).is_equal(1)
	# the aim was on the first target (the sway at rest is smaller than the target)
	assert_bool(b.hits[0]).is_true()
	# far off the plate: a miss
	for i in 40:
		b.tick()
	b._base_to = Vector2(0.5, 0.5)
	b.base = Vector2(0.5, 0.5)
	b.press("action")
	b.tick()
	assert_bool(b.hits[1]).is_false()
	assert_int(b.misses).is_equal(1)


func test_biathlon_is_deterministic() -> void:
	var a := Biathlon.new(12)
	a.auto = true
	a.skill = 0.7
	_play(a, 400.0)
	var b := Biathlon.new(12)
	b.auto = true
	b.skill = 0.7
	_play(b, 400.0)
	assert_float(a.result).is_equal(b.result)
	assert_int(a.misses).is_equal(b.misses)


# ------------------------------------------------------------------ the games: menu, practice, replay

func _run_game(g: FrostpeakGame, seconds: float) -> Array:
	var seen := []
	g.stage_changed.connect(func(st: int) -> void: seen.append(st))
	for i in int(seconds * 60.0):
		g._process(1.0 / 60.0)
	return seen


func test_menu_offers_competition_and_practice_at_every_event() -> void:
	var g := FrostpeakGame.new()
	assert_int(g.menu_items().size()).is_equal(Competition.EVENTS.size() + 1)
	g.free()


func test_practice_repeats_one_event_with_a_replay_and_no_medals() -> void:
	var g := FrostpeakGame.new()
	g.demo = true
	g.practice = "ski_jump"
	g.start(3)
	assert_array(g.comp.programme).is_equal(["ski_jump"])
	assert_int(g.comp.athletes.size()).is_equal(1)
	var seen := _run_game(g, 110.0)
	var S := FrostpeakGame.Stage
	assert_array(seen).contains([S.ATTEMPT, S.RESULT, S.REPLAY, S.NEXT])
	assert_array(seen).not_contains([S.STANDINGS, S.PODIUM, S.FINAL])
	assert_bool(g.best.has(0)).is_true()
	g.free()


func test_competition_flows_through_replay_to_the_standings() -> void:
	var g := FrostpeakGame.new()
	g.demo = true
	g.start(4, 1)
	var seen := _run_game(g, 100.0)
	var S := FrostpeakGame.Stage
	var i := seen.find(S.REPLAY)
	assert_int(i).is_greater(0)
	assert_int(seen[i - 1]).is_equal(S.RESULT)
	assert_int(seen[i + 1]).is_equal(S.STANDINGS)
	g.free()


func test_demo_competition_runs_every_event_to_the_medal_table() -> void:
	var g := FrostpeakGame.new()
	g.demo = true
	g.start(8)
	var S := FrostpeakGame.Stage
	var seen := []
	g.stage_changed.connect(func(st: int) -> void: seen.append(st))
	var n := 0
	while g.stage != S.FINAL and n < 60 * 600:
		g._process(1.0 / 60.0)
		n += 1
	assert_array(seen).contains([S.FINAL])
	assert_int(seen.count(S.PODIUM)).is_equal(Competition.EVENTS.size())
	for ev in Competition.EVENTS:
		assert_int(g.comp.results[ev].size()).is_equal(g.comp.athletes.size())
	g.free()
