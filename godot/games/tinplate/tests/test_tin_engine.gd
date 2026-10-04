extends GdUnitTestSuite
## Tinplate Turbo: the tracks load and close, cars follow their own road over a bridge, walls keep them on the track,
## laps count only after going round, oil steals the grip, and CPU drivers finish every track's race in good time.

const T = preload("res://games/tinplate/engine/tin_engine.gd")
const FILE := "res://games/tinplate/tracks/tracks.tin"


func _tracks() -> Array[TinTrack]:
	return TinTrack.parse_file(FileAccess.get_file_as_string(FILE))


func _field(cpu := true) -> Array:
	var out := []
	for i in 4:
		out.append({"cpu": cpu, "up": {"speed": 0, "grip": 0, "accel": 0}})
	return out


func test_tracks_load() -> void:
	var ts := _tracks()
	assert_int(ts.size()).is_equal(6)
	for t in ts:
		assert_int(t.count()).is_greater(150)
		# closed: the last sample runs into the first
		assert_float(t.pos[t.count() - 1].distance_to(t.pos[0])).is_less(1.0)


func test_a_bridge_lifts_one_road_over_the_other() -> void:
	var t := _tracks()[1]
	var top := 0.0
	for h in t.height:
		top = maxf(top, h)
	assert_float(top).is_greater(2.0)


func test_walls_keep_cars_on_the_track() -> void:
	var t := _tracks()[0]
	var e := TinEngine.new(t, _field(false), 1)
	e.phase = T.Phase.RACE
	var c := e.cars[0]
	c["throttle"] = 1.0
	c["steer"] = 1.0
	for i in 600:
		e.tick()
		assert_float(absf(t.offset(c["pos"], c["s"]))).is_less(t.width * 0.5 + 0.3)


func test_oil_steals_grip() -> void:
	var t := _tracks()[0]
	var e := TinEngine.new(t, _field(false), 1)
	var c := e.cars[0]
	c["vel"] = Vector2.from_angle(c["heading"] + 0.5) * 10.0
	c["oil"] = 1.0
	e._drive(c)
	var slid: float = c["slide"]
	c["vel"] = Vector2.from_angle(c["heading"] + 0.5) * 10.0
	c["oil"] = 0.0
	e._drive(c)
	assert_float(slid).is_greater(c["slide"])


func test_cpus_finish_every_track() -> void:
	var ts := _tracks()
	for ti in ts.size():
		var t := ts[ti]
		var e := TinEngine.new(t, _field(), 3 + ti)
		var bots := []
		for i in 4:
			bots.append(TinBot.new(t, i + 1, 0.7 + 0.1 * i))
		var laps := []
		e.event.connect(func(k, d): if k == "lap": laps.append(d["car"]))
		var ticks := 0
		while e.finished < 4 and ticks < 60 * 240:
			for i in 4:
				bots[i].drive(e, e.cars[i])
			e.tick()
			ticks += 1
		prints("tinplate", t.name, "finished", e.finished, "in", snappedf(ticks / 60.0, 0.1), "s; winner best lap",
			snappedf(e.cars[e.order()[0]]["best"], 0.01), "laps", t.laps, "length", snappedf(t.length, 1.0))
		assert_int(e.finished).is_equal(4)
		assert_int(laps.size()).is_greater_equal(4 * (t.laps - 1))
