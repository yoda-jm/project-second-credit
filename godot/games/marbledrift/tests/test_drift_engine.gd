extends GdUnitTestSuite
## Marble Drift: the height field, rolling down a slope, pushing, walls, falls that shatter, acid, the goal, the
## clock, and the autopilot clearing every course.

const D = preload("res://games/marbledrift/engine/drift_engine.gd")
const FILE := "res://games/marbledrift/courses/courses.drift"


func _courses() -> Array[DriftCourse]:
	return DriftCourse.parse_file(FileAccess.get_file_as_string(FILE))


func _engine(i := 0) -> DriftEngine:
	var e := DriftEngine.new(_courses()[i])
	e.phase = D.Phase.PLAY
	return e


func test_courses_parse() -> void:
	var cs := _courses()
	assert_int(cs.size()).is_greater_equal(2)
	var c: DriftCourse = cs[0]
	assert_float(c.height_at(c.start)).is_equal_approx(12.0, 0.01)
	assert_float(c.height_at(Vector2(0.5, 0.5))).is_equal(-INF)


func test_the_marble_rolls_down_a_ramp() -> void:
	var e := _engine()
	e.ball["pos"] = Vector3(7.5, e.course.height_at(Vector2(7.5, 8.0)), 8.0)
	for i in 30:
		e.tick()
	assert_float(e.ball["vel"].z).is_greater(1.0)


func test_pushing_moves_it_on_the_flat() -> void:
	var e := _engine()
	e.input = Vector2(1, 0)
	for i in 30:
		e.tick()
	assert_float(e.ball["pos"].x).is_greater(8.0)


func test_a_wall_bounces_it_back() -> void:
	var e := _engine()
	e.ball["pos"] = Vector3(10.5, 12.0, 2.5)
	e.ball["vel"] = Vector3(8.0, 0.0, 0.0)
	for i in 30:
		e.tick()
	assert_float(e.ball["pos"].x).is_less(12.0)


func test_off_the_edge_into_the_void_breaks_it() -> void:
	var e := _engine()
	var deaths := []
	e.event.connect(func(k, d): if k in ["fall", "shatter", "acid"]: deaths.append(k))
	e.ball["pos"] = Vector3(3.0, 8.0, 18.5)   # near the open left edge of the second platform
	e.ball["vel"] = Vector3(-9.0, 0.0, 0.0)
	for i in 300:
		e.tick()
		if not deaths.is_empty():
			break
	assert_array(deaths).contains(["fall"])


func test_acid_dissolves_it() -> void:
	var e := _engine(1)
	var deaths := []
	e.event.connect(func(k, d): if k == "acid": deaths.append(k))
	e.ball["pos"] = Vector3(10.0, e.course.height_at(Vector2(10.0, 19.0)), 19.0)
	e.tick()
	assert_int(deaths.size()).is_equal(1)


func test_the_clock_running_out_ends_it() -> void:
	var e := _engine()
	e.clock = 0.05
	for i in 10:
		e.tick()
	assert_int(e.phase).is_equal(D.Phase.OVER)


func test_autopilot_clears_every_course() -> void:
	var cs := _courses()
	for i in cs.size():
		var e := DriftEngine.new(cs[i])
		var bot := DriftBot.new()
		var deaths := []
		e.event.connect(func(k, d): if k in ["fall", "shatter", "acid"]: deaths.append([k, Vector2(d["pos"].x, d["pos"].z).snapped(Vector2(0.1, 0.1))]))
		for n in int(150.0 / D.TICK):
			bot.drive(e)
			e.tick()
			if e.phase == D.Phase.FINISHED or e.phase == D.Phase.OVER:
				break
		prints("autopilot", cs[i].name, "phase", e.phase, "clock left", snappedf(e.clock, 0.1), "deaths", deaths, "checkpoint", e.checkpoint, "at", e.ball_xz().snapped(Vector2(0.1, 0.1)))
		assert_int(e.phase).is_equal(D.Phase.FINISHED)
		assert_int(deaths.size()).is_less_equal(1)
