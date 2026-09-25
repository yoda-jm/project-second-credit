extends GdUnitTestSuite
## BDCFF loader on small caves written for these tests (CC BY-SA 4.0, like all our levels).

const SAMPLE := """[BDCFF]
Version=0.5
[game]
Name=Test set
Author=Second Credit
Lives=4 9
[cave]
Name=Objects
Size=20 12 0 0 19 11
DiamondsRequired=5 6 7 8 9
CaveTime=100 90
RandSeed=1 2 3 4 5
RandomFill=BOULDER 40 DIAMOND 10
InitialFill=DIRT
AmoebaGrowthProb=0.25
Effect=DIAMONDBIRTHEffect STEELWALL
[objects]
Point=2 2 INBOX
Line=1 5 18 5 WALL
FillRect=4 7 8 10 STEELWALL SPACE
[Level=2,3]
Point=17 9 OUTBOX
[/Level]
[/objects]
[/cave]
[cave]
Name=Map
Size=5 3
[map]
WWWWW
WP.dW
WWWWW
[/map]
[replay]
Level=2
RandomSeed=77
Movements=.3 r2 D k
[/replay]
[/cave]
[/game]
[/BDCFF]
"""

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")


func test_game_and_cave_properties() -> void:
	var cs := BdcffLoader.load_string(SAMPLE)
	assert_str(cs.name).is_equal("Test set")
	assert_int(cs.initial_lives).is_equal(4)
	assert_int(cs.maximum_lives).is_equal(9)
	assert_int(cs.caves.size()).is_equal(2)
	var c := cs.caves[0]
	assert_str(c.name).is_equal("Objects")
	assert_int(c.w).is_equal(20)
	assert_array(c.level_diamonds).is_equal([5, 6, 7, 8, 9])
	assert_array(c.level_time).is_equal([100, 90, 90, 90, 90])  # later levels copy the last value
	assert_int(c.random_fill_1).is_equal(E.STONE)
	assert_int(c.random_fill_probability_2).is_equal(10)
	assert_int(c.amoeba_growth_prob).is_equal(250000)
	assert_int(c.diamond_birth_effect).is_equal(E.STEEL)
	assert_int(c.objects.size()).is_equal(4)
	assert_array(c.objects[3]["seen_on"]).is_equal([false, true, true, false, false])
	assert_array(cs.warnings).is_empty()


func test_render_objects_and_levels() -> void:
	var c := BdcffLoader.load_string(SAMPLE).caves[0]
	var r1 := CaveRendered.new(c, 0, 0)
	assert_int(r1.get_cell(2, 2)).is_equal(E.INBOX)
	assert_int(r1.get_cell(10, 5)).is_equal(E.BRICK)
	assert_int(r1.get_cell(4, 7)).is_equal(E.STEEL)
	assert_int(r1.get_cell(6, 8)).is_equal(E.SPACE)
	assert_int(r1.get_cell(0, 0)).is_equal(E.STEEL)  # initial border
	assert_int(r1.get_cell(17, 9)).is_not_equal(E.PRE_OUTBOX)  # outbox only on levels 2 and 3
	var r2 := CaveRendered.new(c, 1, 0)
	assert_int(r2.get_cell(17, 9)).is_equal(E.PRE_OUTBOX)


func test_random_fill_is_predictable() -> void:
	var c := BdcffLoader.load_string(SAMPLE).caves[0]
	var a := CaveRendered.new(c, 0, 1)
	var b := CaveRendered.new(c, 0, 999)
	assert_int(a.adler_checksum()).is_equal(b.adler_checksum())  # C64 seed decides, not the game seed
	var other := CaveRendered.new(c, 1, 1)
	assert_int(a.adler_checksum()).is_not_equal(other.adler_checksum())


func test_map_and_replay() -> void:
	var c := BdcffLoader.load_string(SAMPLE).caves[1]
	assert_bool(c.has_map()).is_true()
	var r := CaveRendered.new(c, 0, 0)
	assert_int(r.get_cell(1, 1)).is_equal(E.INBOX)
	assert_int(r.get_cell(3, 1)).is_equal(E.DIAMOND)
	var replay := c.replays[0]
	assert_int(replay.level).is_equal(2)
	assert_int(replay.seed).is_equal(77)
	assert_int(replay.movements.size()).is_equal(7)
	assert_array(replay.next_movement()).is_equal([CaveDirections.STILL, false, false])
	for i in 3:
		replay.next_movement()
	assert_array(replay.next_movement()).is_equal([CaveDirections.RIGHT, false, false])
	assert_array(replay.next_movement()).is_equal([CaveDirections.DOWN, true, false])
	assert_array(replay.next_movement()).is_equal([CaveDirections.STILL, false, true])
	assert_array(replay.next_movement()).is_empty()
