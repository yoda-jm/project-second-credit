class_name CaveRendered
extends CaveProperties
## A cave ready to play: the map drawn from a CaveStored at one difficulty level, plus the game state.
## Port of GDash's CaveRendered (MIT, Copyright (c) 2007-2013 Czirkos Zoltan; see GDASH_LICENSE.txt).
## The engine itself (iterate) is in CaveEngine, which extends this class.

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")

enum AmoebaState { SLEEPING, AWAKE, TOO_BIG, ENCLOSED }
enum MagicWallState { DORMANT, ACTIVE, EXPIRED }
enum PlayerState { NOT_YET, LIVING, TIMEOUT, DIED, EXITED }

var map := PackedInt32Array()
var objects_order := PackedInt32Array()  ## which object drew each cell (object id), for BoundaryFill
var rendered_on: int = 0
var render_seed: int = 0
var random := GlibRand.new()  ## the cave's own random generator (seeded by render_seed)
var c64_rand := C64Rand.new()  ## predictable slime and cave generation

var time: int = 0
var timevalue: int = 0
var diamonds_needed: int = 0
var magic_wall_time: int = 0
var slime_permeability: int = 0
var slime_permeability_c64: int = 0
var time_bonus: int = 0
var time_penalty: int = 0
var amoeba_time: int = 0
var amoeba_max_count: int = 0
var amoeba_2_time: int = 0
var amoeba_2_max_count: int = 0
var hatching_delay_time: int = 0
var hatching_delay_frame: int = 0
var speed: int = 0
var ckdelay: int = 0
var ckdelay_current: int = 0
var ckdelay_extra_for_animation: int = 0
var timing_factor: int = 1000

var amoeba_state: int = AmoebaState.SLEEPING
var amoeba_2_state: int = AmoebaState.SLEEPING
var magic_wall_state: int = MagicWallState.DORMANT
var player_state: int = PlayerState.NOT_YET
var player_x: int = 0
var player_y: int = 0
var last_direction: int = CaveDirections.STILL
var last_horizontal_direction: int = CaveDirections.STILL


## Renders the stored cave for a level (0..4) with a random seed, like GDash's CaveRendered constructor.
func _init(data: CaveStored = null, level: int = 0, seed: int = 0) -> void:
	if data == null:
		return
	copy_properties_from(data)
	rendered_on = level
	render_seed = seed
	time = data.level_time[level]
	timevalue = data.level_timevalue[level]
	diamonds_needed = data.level_diamonds[level]
	magic_wall_time = data.level_magic_wall_time[level]
	slime_permeability = data.level_slime_permeability[level]
	slime_permeability_c64 = data.level_slime_permeability_c64[level]
	time_bonus = data.level_bonus_time[level]
	time_penalty = data.level_penalty_time[level]
	amoeba_time = data.level_amoeba_time[level]
	amoeba_max_count = data.level_amoeba_threshold[level]
	amoeba_2_time = data.level_amoeba_2_time[level]
	amoeba_2_max_count = data.level_amoeba_2_threshold[level]
	hatching_delay_time = data.level_hatching_delay_time[level]
	hatching_delay_frame = data.level_hatching_delay_frame[level]
	speed = data.level_speed[level]
	ckdelay = data.level_ckdelay[level]
	random.set_seed(render_seed)
	objects_order.resize(w * h)
	create_map(data, level)
	var slime_seed: int = data.level_slime_seed_c64[level]
	if slime_seed != -1:
		c64_rand.set_seed_2(slime_seed / 256, slime_seed % 256)
	if scheduling != CaveScheduling.MILLISECONDS:
		speed = 120
	_correct_visible_size()


func create_map(data: CaveStored, level: int) -> void:
	rendered_on = level
	if not data.has_map():
		map.resize(w * h)
		if data.level_rand[level] < 0:
			c64_rand.set_seed_2(random.rand_int_range(0, 256), random.rand_int_range(0, 256))
		else:
			c64_rand.set_seed(data.level_rand[level])
		for y in range(1, h - 1):
			for x in w:
				var randm: int
				if data.level_rand[level] < 0:
					randm = random.rand_int_range(0, 256)
				else:
					randm = c64_rand.random()
				var element: int = data.initial_fill
				if randm < data.random_fill_probability_1: element = data.random_fill_1
				if randm < data.random_fill_probability_2: element = data.random_fill_2
				if randm < data.random_fill_probability_3: element = data.random_fill_3
				if randm < data.random_fill_probability_4: element = data.random_fill_4
				map[y * w + x] = element
		for y in h:
			map[y * w] = data.initial_border
			map[y * w + w - 1] = data.initial_border
		for x in w:
			map[x] = data.initial_border
			map[(h - 1) * w + x] = data.initial_border
	else:
		map = data.map.duplicate()
		c64_rand.set_seed_2(0, 0x1e)
	objects_order.fill(0)
	for i in data.objects.size():
		var o: Dictionary = data.objects[i]
		o["id"] = i + 1
		if o["seen_on"][rendered_on]:
			CaveObjects.draw(o, self)


## Puts an element while drawing objects, with GDash's wraparound rules (store_rc).
func store_rc(x: int, y: int, element: int, object_id: int = 0) -> void:
	if element == E.NONE:
		return
	if wraparound_objects:
		if lineshift:
			if x < 0:
				x += 5 * w
				y -= 5
			y += x / w
			x %= w
		else:
			y = (y + h) % h
			x = (x + w) % w
	if x >= 0 and x < w and y >= 0 and y < h:
		map[y * w + x] = element
		objects_order[y * w + x] = object_id


## Element at (x, y), with the cave's border wrapping (perfect or line-shifting), like GDash's map(x, y).
func get_cell(x: int, y: int) -> int:
	if x >= 0 and x < w and y >= 0 and y < h:
		return map[y * w + x]
	if lineshift:
		if x < 0:
			x += 5 * w
			y -= 5
		y += x / w
		x %= w
		y = (y + h) % h
	else:
		y = (y + h) % h
		x = (x + w) % w
	return map[y * w + x]


func set_cell(x: int, y: int, element: int) -> void:
	if x >= 0 and x < w and y >= 0 and y < h:
		map[y * w + x] = element
		return
	if lineshift:
		if x < 0:
			x += 5 * w
			y -= 5
		y += x / w
		x %= w
		y = (y + h) % h
	else:
		y = (y + h) % h
		x = (x + w) % w
	map[y * w + x] = element


## GDash's Adler checksum of the rendered map (over the BDCFF map characters). Replays store it.
func adler_checksum() -> int:
	var a := 1
	var b := 0
	for y in h:
		for x in w:
			var c: String = E.MAP_CHAR[map[y * w + x]]
			a += c.unicode_at(0) if c != "" else 0
			b += a
			a %= 65521
			b %= 65521
	return ((b << 16) + a) & 0xffffffff


func _correct_visible_size() -> void:
	if x2 < x1:
		var t := x2; x2 = x1; x1 = t
	if y2 < y1:
		var t := y2; y2 = y1; y1 = t
	x1 = maxi(x1, 0)
	y1 = maxi(y1, 0)
	x2 = mini(x2, w - 1)
	y2 = mini(y2, h - 1)
