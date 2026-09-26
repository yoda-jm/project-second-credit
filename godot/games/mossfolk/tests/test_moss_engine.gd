extends GdUnitTestSuite
## Mossfolk: levels parse, walkers turn at walls and step over bumps, long falls splat, each tool cuts or builds,
## steel stops them, and every level's recorded solution saves enough.

const E = preload("res://games/mossfolk/engine/moss_engine.gd")
const FILE := "res://games/mossfolk/levels/first-steps.moss"


func _levels() -> Array[MossLevel]:
	return MossLevel.parse_file(FileAccess.get_file_as_string(FILE))


func _flat(extra := "") -> MossLevel:
	return MossLevel.parse_file("[level]\nsize=200x100\nfolk=1 save=1 rate=50 minutes=2\nentrance=50,60\nexit=190,69\nrect 0 70 200 30\n" + extra)[0]


func _one(lv: MossLevel) -> MossEngine:
	var e := MossEngine.new(lv)
	for i in 60:
		e.tick()
		if not e.folk.is_empty() and e.folk[0]["state"] == "walk":
			break
	return e


func test_levels_parse() -> void:
	var ls := _levels()
	assert_int(ls.size()).is_equal(5)
	assert_str(ls[0].name).is_equal("Just Dig Down")
	assert_int(ls[0].terrain[100 * ls[0].w + 10]).is_equal(E.EARTH)
	assert_int(ls[0].terrain[50 * ls[0].w + 2]).is_equal(E.STEEL)
	assert_int(ls[2].water.size()).is_equal(1)


func test_walkers_turn_at_walls_and_step_over_bumps() -> void:
	var e := _one(_flat("rect 60 66 4 4\nrect 80 40 5 30\n"))
	var c: Dictionary = e.folk[0]
	for i in 40:
		e.tick()
	assert_int(c["dir"]).is_equal(-1)
	assert_int(c["x"]).is_less(80)


func test_a_long_fall_splats_and_a_glider_lands() -> void:
	var lv := MossLevel.parse_file("[level]\nsize=100x200\nfolk=2 save=1 rate=99 minutes=2\nskills=glide:1\nentrance=50,10\nexit=0,0\nrect 0 190 100 10\nsteel 0 150 4 40\nsteel 96 150 4 40\n")[0]
	var e := MossEngine.new(lv)
	for i in 200:
		e.tick()
		if e.folk.size() == 2 and not e.folk[1]["glider"]:
			e.assign(1, "glide")
	assert_int(e.dead).is_equal(1)
	assert_str(e.folk[1]["state"]).is_equal("walk")


func test_tools_cut_and_steel_stops_them() -> void:
	var lv := _flat("steel 0 90 200 10\n")
	lv.skills = {"dig": 1}
	var e := _one(lv)
	assert_bool(e.assign(0, "dig")).is_true()
	for i in 300:
		e.tick()
	var c: Dictionary = e.folk[0]
	# dug down to the steel and stopped
	assert_int(c["y"]).is_equal(89)
	assert_str(c["state"]).is_equal("walk")


func test_builders_lay_twelve_bricks() -> void:
	var lv := _flat()
	lv.skills = {"build": 1}
	var e := _one(lv)
	var y0: int = e.folk[0]["y"]
	e.assign(0, "build")
	var bricks := []
	e.event.connect(func(k, _d): if k == "brick": bricks.append(1))
	for i in 16 * 13:
		e.tick()
	assert_int(bricks.size()).is_equal(12)
	assert_int(e.folk[0]["y"]).is_less(y0 - 8)


func test_every_solution_saves_enough() -> void:
	for lv in _levels():
		var e := MossEngine.new(lv)
		var d := MossDemo.new()
		while not e.over:
			d.drive(e)
			e.tick()
		prints(lv.name, "saved", e.saved, "of", lv.count, "needed", lv.save, "in", e.frame / 17, "s")
		assert_int(e.saved).is_greater_equal(lv.save)
