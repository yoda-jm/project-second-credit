class_name CaveEngine
extends CaveRendered
## The rules engine: one call to iterate() is one cave frame. Port of GDash's caverenderedengine.cpp and the
## game-related parts of caverendered.cpp (MIT, Copyright (c) 2007-2013 Czirkos Zoltan; see GDASH_LICENSE.txt).
##
## The port keeps GDash's structure and names so it can be checked line by line against the original.
## Sounds and particles do not change the game state; they are reported as events for the presentation layer:
## [kind, a, b, c] with kind "effect" (element, x, y, dir), "eat" (element, x, y), "sound" (name, x, y),
## "particles" (element, x, y) and "explosion" (element, x, y).

const D = preload("res://games/rocks/engine/cave_directions.gd")

const CREATURE_DIR: Array[int] = [D.LEFT, D.UP, D.RIGHT, D.DOWN]
const CREATURE_CHDIR: Array[int] = [D.RIGHT, D.DOWN, D.LEFT, D.UP]
const CCW_EIGHTH: Array[int] = [D.STILL, D.UP_LEFT, D.UP, D.UP_RIGHT, D.RIGHT, D.DOWN_RIGHT, D.DOWN, D.DOWN_LEFT, D.LEFT]
const CCW_FOURTH: Array[int] = [D.STILL, D.LEFT, D.UP_LEFT, D.UP, D.UP_RIGHT, D.RIGHT, D.DOWN_RIGHT, D.DOWN, D.DOWN_LEFT, D.LEFT]
const CW_EIGHTH: Array[int] = [D.STILL, D.UP_RIGHT, D.RIGHT, D.DOWN_RIGHT, D.DOWN, D.DOWN_LEFT, D.LEFT, D.UP_LEFT, D.UP]
const CW_FOURTH: Array[int] = [D.STILL, D.RIGHT, D.DOWN_RIGHT, D.DOWN, D.DOWN_LEFT, D.LEFT, D.UP_LEFT, D.UP, D.UP_RIGHT]
const OPPOSITE: Array[int] = [D.STILL, D.DOWN, D.DOWN_LEFT, D.LEFT, D.UP_LEFT, D.UP, D.UP_RIGHT, D.RIGHT, D.DOWN_RIGHT]
const TWICE: Array[int] = [D.STILL, D.UP_2, D.UP_RIGHT_2, D.RIGHT_2, D.DOWN_RIGHT_2, D.DOWN_2, D.DOWN_LEFT_2, D.LEFT_2, D.UP_LEFT_2]
const BITER_MOVE: Array[int] = [D.UP, D.RIGHT, D.DOWN, D.LEFT]
const GHOST_DIRS: Array[int] = [D.UP, D.DOWN, D.LEFT, D.RIGHT]
const PLAYER_MEM_SIZE := 16

var ghost_explode_to: Array[int] = [E.SPACE, E.SPACE, E.DIRT, E.DIRT, E.CLOCK, E.CLOCK, E.PRE_OUTBOX,
	E.BOMB, E.BOMB, E.PLAYER, E.GHOST, E.BLADDER, E.DIAMOND, E.SWEET, E.WAITING_STONE, E.BITER_1]

var hammered_reappear := PackedInt32Array()
var hatched := false
var gate_open := false
var time_elapsed: int = 0
var diamonds_collected: int = 0
var skeletons_collected: int = 0
var gate_open_flash: int = 0
var convert_amoeba_this_frame := false
var player_seen_ago: int = 0
var kill_player := false
var sweet_eaten := false
var player_x_mem := PackedInt32Array()
var player_y_mem := PackedInt32Array()
var key1: int = 0
var key2: int = 0
var key3: int = 0
var diamond_key_collected := false
var inbox_flash_toggle := false
var biters_wait_frame: int = 0
var replicators_wait_frame: int = 0
var creatures_direction_will_change: int = 0
var gravity_will_change: int = 0
var gravity_disabled := false
var gravity_next_direction: int = D.STILL
var got_pneumatic_hammer := false
var pneumatic_hammer_active_delay: int = 0
var voodoo_touched := false
var score: int = 0  ## score collected in the last frame
var cave_hatching_frames: int = 0  ## initial hatching delay, for countdown displays
var cave_hatching_ms: int = 0
var events: Array = []  ## sounds and visual effects of the last frame (see the class comment)
var moves: Array[Vector3i] = []  ## objects that moved one cell in the last frame: (from x, from y, direction)

## Elements that do something when scanned (the rest are skipped quickly).
static var _active := PackedByteArray()
var _flags := PackedInt32Array(E.FLAGS)
var _pair := PackedInt32Array(E.PAIR)
var _ckdelay := PackedInt32Array(E.CKDELAY)

# per-iteration scan state (locals in GDash's iterate)
var _amoeba_found_enclosed := true
var _amoeba_2_found_enclosed := true
var _amoeba_count: int = 0
var _amoeba_2_count: int = 0
var _inbox_toggle := false
var _time_decrement_sec: int = 0


func _init(data: CaveStored = null, level: int = 0, seed: int = 0) -> void:
	if _active.is_empty():
		_build_active_table()
	super(data, level, seed)
	player_x_mem.resize(PLAYER_MEM_SIZE)
	player_y_mem.resize(PLAYER_MEM_SIZE)
	if data != null:
		setup_for_game()


## GDash's CaveRendered::setup_for_game.
func setup_for_game() -> void:
	if active_is_first_found:
		for y in range(h - 1, -1, -1):
			for x in range(w - 1, -1, -1):
				if map[y * w + x] == E.INBOX:
					player_x = x
					player_y = y
	else:
		for y in h:
			for x in w:
				if map[y * w + x] == E.INBOX:
					player_x = x
					player_y = y
	for i in PLAYER_MEM_SIZE:
		player_x_mem[i] = player_x
		player_y_mem[i] = player_y
	timing_factor = 1200 if pal_timing else 1000
	time *= timing_factor
	magic_wall_time *= timing_factor
	amoeba_time *= timing_factor
	amoeba_2_time *= timing_factor
	hatching_delay_time *= timing_factor
	cave_hatching_frames = hatching_delay_frame
	cave_hatching_ms = hatching_delay_time
	if hammered_walls_reappear:
		hammered_reappear.resize(w * h)
		hammered_reappear.fill(0)
	set_ckdelay_extra_for_animation()
	update_scheduling()


func set_ckdelay_extra_for_animation() -> void:
	var has_amoeba := false
	var has_firefly := false
	var has_butterfly := false
	ckdelay_current = 0
	for i in map.size():
		var e: int = map[i]
		ckdelay_current += E.CKDELAY[e]
		if e >= E.FIREFLY_1 and e <= E.FIREFLY_4:
			has_firefly = true
		elif e >= E.BUTTER_1 and e <= E.BUTTER_4:
			has_butterfly = true
		elif e == E.AMOEBA:
			has_amoeba = true
	ckdelay_extra_for_animation = 0
	if has_amoeba: ckdelay_extra_for_animation += 2600
	if has_firefly: ckdelay_extra_for_animation += 2600
	if has_butterfly: ckdelay_extra_for_animation += 2600
	if has_amoeba: ckdelay_extra_for_animation += 2600


func update_scheduling() -> void:
	match scheduling:
		CaveScheduling.MILLISECONDS:
			pass
		CaveScheduling.BD1:
			if not intermission:
				speed = int(88 + 3.66 * ckdelay + (ckdelay_current + ckdelay_extra_for_animation) / 1000)
			else:
				speed = int(60 + 3.66 * ckdelay + (ckdelay_current + ckdelay_extra_for_animation) / 1000)
		CaveScheduling.BD1_ATARI:
			if not intermission:
				speed = int(74 + 3.2 * ckdelay + ckdelay_current / 1000)
			else:
				speed = int(65 + 2.88 * ckdelay + ckdelay_current / 1000)
		CaveScheduling.BD2:
			speed = maxi(60 + (ckdelay_current + ckdelay_extra_for_animation) / 1000, ckdelay * 20)
		CaveScheduling.PLCK:
			speed = maxi(65 + ckdelay_current / 1000, ckdelay * 20)
		CaveScheduling.BD2_PLCK_ATARI:
			speed = maxi(40 + ckdelay_current / 1000, ckdelay * 20)
		CaveScheduling.CRDR:
			if hammered_walls_reappear:
				ckdelay_current += 60000
			speed = maxi(130 + ckdelay_current / 1000, ckdelay * 20)


func count_diamonds() -> void:
	if diamonds_needed <= 0:
		for e in map:
			match e:
				E.DIAMOND, E.DIAMOND_F, E.FLYING_DIAMOND, E.FLYING_DIAMOND_F:
					diamonds_needed += 1
				E.SKELETON:
					diamonds_needed += skeletons_worth_diamonds
		if diamonds_needed < 0:
			diamonds_needed = 0


## Seconds shown to the player (rounded up).
func time_visible(internal_time: int = -1) -> int:
	var t := time if internal_time < 0 else internal_time
	return (t + timing_factor - 1) / timing_factor


# --- events (no effect on the game state) ---

func _effect(element: int, x: int, y: int, dir: int = D.STILL, particles: bool = true) -> void:
	events.append(["effect", element, x + D.DX[dir], y + D.DY[dir], particles])


func _eat(element: int, x: int, y: int) -> void:
	events.append(["eat", element, x, y])


func _sound(name: String, x: int, y: int) -> void:
	events.append(["sound", name, x, y])


func _particles(x: int, y: int, element: int) -> void:
	events.append(["particles", element, x, y])


# --- map access, as in GDash (all coordinates wrap around the cave borders) ---

func _at(x: int, y: int) -> int:
	return get_cell(x, y)


func _get_dir(x: int, y: int, dir: int) -> int:
	return get_cell(x + D.DX[dir], y + D.DY[dir])


func _flag(x: int, y: int, dir: int, flag: int) -> bool:
	return (_flags[get_cell(x + D.DX[dir], y + D.DY[dir])] & flag) != 0


func _explodes_by_hit(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_EXPLODES_BY_HIT)
func _non_explodable(x: int, y: int) -> bool: return _flag(x, y, D.STILL, E.P_NON_EXPLODABLE)
func _amoeba_eats(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_AMOEBA_CONSUMES)
func _sloped_for_bladder(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_BLADDER_SLOPED)
func _blows_up_flies(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_BLOWS_UP_FLIES)
func _rotates_ccw(x: int, y: int) -> bool: return _flag(x, y, D.STILL, E.P_CCW)
func is_player(x: int, y: int, dir: int = D.STILL) -> bool: return _flag(x, y, dir, E.P_PLAYER)
func _can_be_hammered(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_CAN_BE_HAMMERED)
func can_be_pushed(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_CAN_BE_PUSHED)
func _is_first_stage_of_explosion(x: int, y: int) -> bool: return _flag(x, y, D.STILL, E.P_EXPLOSION_FIRST_STAGE)
func _moved_by_conveyor_top(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_MOVED_BY_CONVEYOR_TOP)
func _moved_by_conveyor_bottom(x: int, y: int, dir: int) -> bool: return _flag(x, y, dir, E.P_MOVED_BY_CONVEYOR_BOTTOM)
func _is_scanned(x: int, y: int, dir: int = D.STILL) -> bool: return _flag(x, y, dir, E.P_SCANNED)
func _is_like_dirt(x: int, y: int, dir: int = D.STILL) -> bool: return _flag(x, y, dir, E.P_DIRT)


func _sloped(x: int, y: int, dir: int, slop: int) -> bool:
	match slop:
		D.LEFT: return _flag(x, y, dir, E.P_SLOPED_LEFT)
		D.RIGHT: return _flag(x, y, dir, E.P_SLOPED_RIGHT)
		D.UP: return _flag(x, y, dir, E.P_SLOPED_UP)
		D.DOWN: return _flag(x, y, dir, E.P_SLOPED_DOWN)
	return false


func _is_like_element(x: int, y: int, dir: int, e: int) -> bool:
	var examined := _get_dir(x, y, dir)
	if (E.FLAGS[examined] & E.P_DIRT) != 0:
		examined = E.DIRT
	if (E.FLAGS[e] & E.P_DIRT) != 0:
		e = E.DIRT
	if examined == E.LAVA:
		examined = E.SPACE
	return e == examined


func _is_like_space(x: int, y: int, dir: int = D.STILL) -> bool:
	var e := _get_dir(x, y, dir)
	return e == E.SPACE or e == E.LAVA


## Stores an element (as its "scanned" pair); lava swallows everything.
func _store(x: int, y: int, element: int) -> void:
	if get_cell(x, y) == E.LAVA:
		_effect(E.LAVA, x, y)
		return
	set_cell(x, y, E.scanned_pair(element))


func _store_dir(x: int, y: int, dir: int, element: int) -> void:
	_store(x + D.DX[dir], y + D.DY[dir], element)


func _move(x: int, y: int, dir: int, element: int) -> void:
	_store_dir(x, y, dir, element)
	_store(x, y, E.SPACE)
	moves.append(Vector3i(x, y, dir))


func _next(x: int, y: int) -> void:
	set_cell(x, y, get_cell(x, y) + 1)


func _unscan(x: int, y: int) -> void:
	var e := get_cell(x, y)
	if (E.FLAGS[e] & E.P_SCANNED) != 0:
		set_cell(x, y, E.PAIR[e])


# --- explosions ---

func _cell_explode(x: int, y: int, explode_to: int) -> void:
	if _non_explodable(x, y):
		return
	if voodoo_any_hurt_kills_player and _at(x, y) == E.VOODOO:
		voodoo_touched = true
	if _at(x, y) == E.VOODOO and not voodoo_disappear_in_explosion:
		_store(x, y, E.TIME_PENALTY)
	elif _at(x, y) == E.NITRO_PACK or _at(x, y) == E.NITRO_PACK_F:
		_store(x, y, E.NITRO_PACK_EXPLODE)
	else:
		_store(x, y, explode_to)


func _creature_explode(x: int, y: int, explode_to: int) -> void:
	ckdelay_current += 1200
	_sound("explosion", x, y)
	for yy in range(y - 1, y + 2):
		for xx in range(x - 1, x + 2):
			_cell_explode(xx, yy, explode_to)


func _nitro_explode(x: int, y: int) -> void:
	ckdelay_current += 1200
	_sound("nitro_explosion", x, y)
	for yy in range(y - 1, y + 2):
		for xx in range(x - 1, x + 2):
			_cell_explode(xx, yy, E.NITRO_EXPL_1)
	_store(x, y, E.NITRO_EXPL_1)


func _voodoo_explode(x: int, y: int) -> void:
	if voodoo_any_hurt_kills_player:
		voodoo_touched = true
	ckdelay_current += 1000
	_sound("voodoo_explosion", x, y)
	for yy in range(y - 1, y + 2):
		for xx in range(x - 1, x + 2):
			_store(xx, yy, E.PRE_STEEL_1)
	_store(x, y, E.TIME_PENALTY)


func _cell_explode_skip_voodoo(x: int, y: int, expl: int) -> void:
	if _non_explodable(x, y):
		return
	if not voodoo_disappear_in_explosion and _at(x, y) == E.VOODOO:
		return
	if voodoo_any_hurt_kills_player and _at(x, y) == E.VOODOO:
		voodoo_touched = true
	_store(x, y, expl)


func _ghost_explode(x: int, y: int) -> void:
	ckdelay_current += 650
	_sound("ghost_explosion", x, y)
	_cell_explode_skip_voodoo(x, y, E.GHOST_EXPL_1)
	_cell_explode_skip_voodoo(x - 1, y - 1, E.GHOST_EXPL_1)
	_cell_explode_skip_voodoo(x + 1, y + 1, E.GHOST_EXPL_1)
	_cell_explode_skip_voodoo(x - 1, y + 1, E.GHOST_EXPL_1)
	_cell_explode_skip_voodoo(x + 1, y - 1, E.GHOST_EXPL_1)


func _bomb_explode(x: int, y: int) -> void:
	ckdelay_current += 650
	_sound("bomb_explosion", x, y)
	_cell_explode_skip_voodoo(x, y, E.BOMB_EXPL_1)
	_cell_explode_skip_voodoo(x - 1, y, E.BOMB_EXPL_1)
	_cell_explode_skip_voodoo(x + 1, y, E.BOMB_EXPL_1)
	_cell_explode_skip_voodoo(x, y + 1, E.BOMB_EXPL_1)
	_cell_explode_skip_voodoo(x, y - 1, E.BOMB_EXPL_1)


func _explode(x: int, y: int) -> void:
	var e := _at(x, y)
	events.append(["explosion", e, x, y])
	match e:
		E.GHOST:
			_ghost_explode(x, y)
		E.BOMB_TICK_7:
			_bomb_explode(x, y)
		E.VOODOO:
			_voodoo_explode(x, y)
		E.NITRO_PACK, E.NITRO_PACK_F, E.NITRO_PACK_EXPLODE:
			_nitro_explode(x, y)
		E.AMOEBA_2:
			_creature_explode(x, y, E.AMOEBA_2_EXPL_1)
		E.FALLING_WALL_F:
			_creature_explode(x, y, E.EXPLODE_1)
		E.ROCKET_1, E.ROCKET_2, E.ROCKET_3, E.ROCKET_4:
			_creature_explode(x, y, E.EXPLODE_1)
		E.BUTTER_1, E.BUTTER_2, E.BUTTER_3, E.BUTTER_4:
			_creature_explode(x, y, butterfly_explode_to)
		E.ALT_BUTTER_1, E.ALT_BUTTER_2, E.ALT_BUTTER_3, E.ALT_BUTTER_4:
			_creature_explode(x, y, alt_butterfly_explode_to)
		E.FIREFLY_1, E.FIREFLY_2, E.FIREFLY_3, E.FIREFLY_4:
			_creature_explode(x, y, firefly_explode_to)
		E.ALT_FIREFLY_1, E.ALT_FIREFLY_2, E.ALT_FIREFLY_3, E.ALT_FIREFLY_4:
			_creature_explode(x, y, alt_firefly_explode_to)
		E.PLAYER, E.PLAYER_BOMB, E.PLAYER_GLUED, E.PLAYER_STIRRING, E.PLAYER_ROCKET_LAUNCHER, \
				E.PLAYER_PNEUMATIC_LEFT, E.PLAYER_PNEUMATIC_RIGHT:
			_creature_explode(x, y, E.EXPLODE_1)
		E.STONEFLY_1, E.STONEFLY_2, E.STONEFLY_3, E.STONEFLY_4:
			_creature_explode(x, y, stonefly_explode_to)
		E.DRAGONFLY_1, E.DRAGONFLY_2, E.DRAGONFLY_3, E.DRAGONFLY_4:
			_creature_explode(x, y, dragonfly_explode_to)
		_:
			push_error("explode: unexpected element %d" % e)


func _explode_dir(x: int, y: int, dir: int) -> void:
	_explode(x + D.DX[dir], y + D.DY[dir])


static func get_hammered(elem: int) -> int:
	match elem:
		E.WALLED_KEY_1: return E.KEY_1
		E.WALLED_KEY_2: return E.KEY_2
		E.WALLED_KEY_3: return E.KEY_3
		E.WALLED_DIAMOND: return E.DIAMOND
		E.BRICK, E.BRICK_SLOPED_UP_RIGHT, E.BRICK_SLOPED_UP_LEFT, E.BRICK_SLOPED_DOWN_RIGHT, \
				E.BRICK_SLOPED_DOWN_LEFT, E.BRICK_NON_SLOPED, E.MAGIC_WALL, E.STEEL_EXPLODABLE, \
				E.EXPANDING_WALL, E.V_EXPANDING_WALL, E.H_EXPANDING_WALL, E.FALLING_WALL, E.FALLING_WALL_F:
			return E.SPACE
	return E.NONE


# --- player ---

## What remains after the player eats or activates an element (NONE: not eatable).
func _player_eat_element(element: int, x: int, y: int, dir: int) -> int:
	var was_element := element
	x += D.DX[dir]
	y += D.DY[dir]
	match element:
		E.DIAMOND_KEY:
			diamond_key_collected = true
			element = E.SPACE
		E.KEY_1:
			key1 += 1
			element = E.SPACE
		E.KEY_2:
			key2 += 1
			element = E.SPACE
		E.KEY_3:
			key3 += 1
			element = E.SPACE
		E.DOOR_1:
			if key1 == 0:
				element = E.NONE
			else:
				key1 -= 1
				element = E.SPACE
		E.DOOR_2:
			if key2 == 0:
				element = E.NONE
			else:
				key2 -= 1
				element = E.SPACE
		E.DOOR_3:
			if key3 == 0:
				element = E.NONE
			else:
				key3 -= 1
				element = E.SPACE
		E.CREATURE_SWITCH:
			creatures_backwards = not creatures_backwards
		E.EXPANDING_WALL_SWITCH:
			expanding_wall_changed = not expanding_wall_changed
		E.BITER_SWITCH:
			biter_delay_frame += 1
			if biter_delay_frame == 4:
				biter_delay_frame = 0
		E.REPLICATOR_SWITCH:
			replicators_active = not replicators_active
		E.CONVEYOR_SWITCH:
			conveyor_belts_active = not conveyor_belts_active
		E.CONVEYOR_DIR_SWITCH:
			conveyor_belts_direction_changed = not conveyor_belts_direction_changed
		E.GRAVITY_SWITCH:
			if gravity_switch_active and (dir == D.LEFT or dir == D.RIGHT or dir == D.UP or dir == D.DOWN):
				_sound("switch_gravity", x, y)
				gravity_will_change = gravity_change_time * timing_factor
				gravity_next_direction = dir
				gravity_switch_active = false
			else:
				element = E.NONE
		E.DIRT, E.DIRT2, E.DIRT_SLOPED_UP_RIGHT, E.DIRT_SLOPED_UP_LEFT, E.DIRT_SLOPED_DOWN_LEFT, \
				E.DIRT_SLOPED_DOWN_RIGHT, E.DIRT_BALL, E.DIRT_LOOSE, E.STEEL_EATABLE, E.BRICK_EATABLE:
			element = E.SPACE
		E.SPACE, E.LAVA:
			element = E.SPACE
		E.SWEET:
			sweet_eaten = true
			element = E.SPACE
		E.PNEUMATIC_HAMMER:
			got_pneumatic_hammer = true
			element = E.SPACE
		E.CLOCK:
			time += time_bonus * timing_factor
			if time > max_time * timing_factor:
				time -= max_time * timing_factor
			element = E.DIRT
		E.DIAMOND, E.FLYING_DIAMOND:
			score += diamond_value
			diamonds_collected += 1
			if diamonds_needed == diamonds_collected:
				gate_open = true
				diamond_value = extra_diamond_value
				gate_open_flash = 1
				_sound("crack", x, y)
			element = E.SPACE
		E.SKELETON:
			skeletons_collected += 1
			for i in skeletons_worth_diamonds:
				_player_eat_element(E.DIAMOND, x, y, D.STILL)
			element = E.SPACE
		E.OUTBOX, E.INVIS_OUTBOX:
			player_state = PlayerState.EXITED
			element = E.SPACE
		_:
			element = E.NONE
	if element != E.NONE:
		_eat(was_element, x, y)
	return element


func _do_teleporter(px: int, py: int, player_move: int) -> bool:
	var tx := px
	var ty := py
	var teleported := false
	while true:
		tx += 1
		if tx >= w:
			tx = 0
			ty += 1
			if ty >= h:
				ty = 0
		if _at(tx, ty) == E.TELEPORTER and _is_like_space(tx, ty, player_move):
			_store_dir(tx, ty, player_move, _at(px, py))
			_store(px, py, E.SPACE)
			_sound("teleporter", tx, ty)
			teleported = true
		if teleported or (tx == px and ty == py):
			break
	return teleported


func _do_push(x: int, y: int, player_move: int, player_fire: bool) -> bool:
	var what := _get_dir(x, y, player_move)
	var grav_compat: int = gravity if gravity_affects_all else D.DOWN
	var result := false
	match what:
		E.WAITING_STONE, E.STONE, E.NITRO_PACK, E.CHASING_STONE, E.MEGA_STONE, E.FLYING_STONE, E.NUT:
			if player_move == CCW_FOURTH[gravity] or player_move == CW_FOURTH[gravity]:
				var prob := 0
				match what:
					E.WAITING_STONE:
						prob = 1000000
					E.CHASING_STONE:
						if sweet_eaten:
							prob = 1000000
					E.MEGA_STONE:
						if mega_stones_pushable_with_sweet and sweet_eaten:
							prob = 1000000
					E.STONE, E.NUT, E.FLYING_STONE, E.NITRO_PACK:
						prob = pushing_stone_prob_sweet if sweet_eaten else pushing_stone_prob
				if _is_like_space(x, y, TWICE[player_move]) and random.rand_int_range(0, 1000000) < prob:
					_effect(what, x + D.DX[player_move], y + D.DY[player_move])
					if what == E.STONE:
						_store_dir(x, y, TWICE[player_move], stone_bouncing_effect)
					else:
						_store_dir(x, y, TWICE[player_move], what)
					result = true
		E.BLADDER, E.BLADDER_1, E.BLADDER_2, E.BLADDER_3, E.BLADDER_4, E.BLADDER_5, E.BLADDER_6, \
				E.BLADDER_7, E.BLADDER_8:
			if player_move != OPPOSITE[grav_compat]:
				if player_move == grav_compat:
					if _is_like_space(x, y, TWICE[player_move]):
						_store_dir(x, y, TWICE[player_move], E.BLADDER); result = true
					elif _is_like_space(x, y, CW_EIGHTH[grav_compat]):
						_store_dir(x, y, CW_EIGHTH[grav_compat], E.BLADDER); result = true
					elif _is_like_space(x, y, CCW_EIGHTH[grav_compat]):
						_store_dir(x, y, CCW_EIGHTH[grav_compat], E.BLADDER); result = true
				elif player_move == CW_FOURTH[grav_compat]:
					if _is_like_space(x, y, TWICE[CW_FOURTH[grav_compat]]):
						_store_dir(x, y, TWICE[CW_FOURTH[grav_compat]], E.BLADDER); result = true
					elif _is_like_space(x, y, CW_EIGHTH[grav_compat]):
						_store_dir(x, y, CW_EIGHTH[grav_compat], E.BLADDER); result = true
					elif _is_like_space(x, y, CW_EIGHTH[player_move]):
						_store_dir(x, y, CW_EIGHTH[player_move], E.BLADDER); result = true
				elif player_move == CCW_FOURTH[grav_compat]:
					if _is_like_space(x, y, TWICE[player_move]):
						_store_dir(x, y, TWICE[player_move], E.BLADDER); result = true
					elif _is_like_space(x, y, CCW_EIGHTH[grav_compat]):
						_store_dir(x, y, CCW_EIGHTH[grav_compat], E.BLADDER); result = true
					elif _is_like_space(x, y, CCW_EIGHTH[player_move]):
						_store_dir(x, y, CCW_EIGHTH[player_move], E.BLADDER); result = true
				if result:
					_effect(E.BLADDER, x, y)
		E.BOX:
			if player_fire:
				if player_move == D.LEFT or player_move == D.RIGHT or player_move == D.UP or player_move == D.DOWN:
					if _is_like_space(x, y, TWICE[player_move]):
						_store_dir(x, y, TWICE[player_move], E.BOX)
						result = true
						_sound("box_push", x, y)
	return result


# --- falling ---

func _do_start_fall(x: int, y: int, falling_direction: int, falling_element: int) -> void:
	if gravity_disabled:
		return
	if _is_like_space(x, y, falling_direction):
		_effect(_at(x, y), x, y, D.STILL, false)
		_move(x, y, falling_direction, falling_element)
	elif _sloped(x, y, falling_direction, OPPOSITE[falling_direction]):
		if _sloped(x, y, falling_direction, CW_FOURTH[falling_direction]) \
				and _is_like_space(x, y, CW_FOURTH[falling_direction]) \
				and _is_like_space(x, y, CW_EIGHTH[falling_direction]):
			_effect(_at(x, y), x, y, D.STILL, false)
			_move(x, y, CW_FOURTH[falling_direction], falling_element)
		elif _sloped(x, y, falling_direction, CCW_FOURTH[falling_direction]) \
				and _is_like_space(x, y, CCW_FOURTH[falling_direction]) \
				and _is_like_space(x, y, CCW_EIGHTH[falling_direction]):
			_effect(_at(x, y), x, y, D.STILL, false)
			_move(x, y, CCW_FOURTH[falling_direction], falling_element)


func _do_fall_try_crush_voodoo(x: int, y: int, fall_dir: int) -> bool:
	if _get_dir(x, y, fall_dir) == E.VOODOO and voodoo_dies_by_stone:
		_explode_dir(x, y, fall_dir)
		return true
	return false


func _do_fall_try_eat_voodoo(x: int, y: int, fall_dir: int) -> bool:
	if _get_dir(x, y, fall_dir) == E.VOODOO and voodoo_collects_diamonds:
		_player_eat_element(E.DIAMOND, x, y, fall_dir)
		_store(x, y, E.SPACE)
		return true
	return false


func _do_fall_try_crack_nut(x: int, y: int, fall_dir: int, bouncing: int) -> bool:
	var e := _get_dir(x, y, fall_dir)
	if e == E.NUT or e == E.NUT_F:
		_store(x, y, bouncing)
		_store_dir(x, y, fall_dir, nut_turns_to_when_crushed)
		_sound("nut_crack", x, y)
		return true
	return false


func _do_fall_try_magic(x: int, y: int, fall_dir: int, magic: int) -> bool:
	if _get_dir(x, y, fall_dir) == E.MAGIC_WALL:
		_effect(E.DIAMOND, x, y, D.STILL, false)
		if magic_wall_state == MagicWallState.DORMANT:
			magic_wall_state = MagicWallState.ACTIVE
		if magic_wall_state == MagicWallState.ACTIVE and _is_like_space(x, y, TWICE[fall_dir]):
			_store_dir(x, y, TWICE[fall_dir], magic)
		_store(x, y, E.SPACE)
		if magic_wall_breakscan and amoeba_state == AmoebaState.AWAKE:
			convert_amoeba_this_frame = true
		return true
	return false


func _do_fall_try_crush(x: int, y: int, fall_dir: int) -> bool:
	if _explodes_by_hit(x, y, fall_dir):
		_explode_dir(x, y, fall_dir)
		return true
	return false


func _do_fall_roll_or_stop(x: int, y: int, fall_dir: int, bouncing: int) -> void:
	if _is_like_space(x, y, fall_dir):
		_move(x, y, fall_dir, _at(x, y))
		return
	if _sloped(x, y, fall_dir, OPPOSITE[fall_dir]):
		if _sloped(x, y, fall_dir, CW_FOURTH[fall_dir]) and _is_like_space(x, y, CW_EIGHTH[fall_dir]) \
				and _is_like_space(x, y, CW_FOURTH[fall_dir]):
			_effect(_at(x, y), x, y)
			_move(x, y, CW_FOURTH[fall_dir], _at(x, y))
		elif _sloped(x, y, fall_dir, CCW_FOURTH[fall_dir]) and _is_like_space(x, y, CCW_EIGHTH[fall_dir]) \
				and _is_like_space(x, y, CCW_FOURTH[fall_dir]):
			_effect(_at(x, y), x, y)
			_move(x, y, CCW_FOURTH[fall_dir], _at(x, y))
		else:
			_effect(_at(x, y), x, y)
			_store(x, y, bouncing)
		return
	_effect(_at(x, y), x, y)
	_store(x, y, bouncing)


# --- the frame ---

## One cave frame. Returns the player move actually used (diagonals removed when not allowed).
func iterate(player_move: int, player_fire: bool, suicide: bool) -> int:
	events.clear()
	moves.clear()
	var grav_compat: int = gravity if gravity_affects_all else D.DOWN

	if not diagonal_movements:
		match player_move:
			D.UP_RIGHT, D.DOWN_RIGHT:
				player_move = D.RIGHT
			D.UP_LEFT, D.DOWN_LEFT:
				player_move = D.LEFT

	if player_seen_ago < 100:
		player_seen_ago += 1
	if pneumatic_hammer_active_delay > 0:
		pneumatic_hammer_active_delay -= 1
	inbox_flash_toggle = not inbox_flash_toggle
	_inbox_toggle = inbox_flash_toggle
	if gate_open_flash > 0:
		gate_open_flash -= 1
	score = 0
	convert_amoeba_this_frame = false

	if suicide and player_state == PlayerState.LIVING and is_player(player_x, player_y):
		_store(player_x, player_y, E.EXPLODE_1)

	if hammered_walls_reappear:
		for y in h:
			for x in w:
				var i := y * w + x
				if hammered_reappear[i] > 0:
					hammered_reappear[i] -= 1
					if hammered_reappear[i] == 0:
						_store(x, y, E.BRICK)
						_sound("wall_reappear", x, y)

	_amoeba_found_enclosed = true
	_amoeba_2_found_enclosed = true
	_amoeba_count = 0
	_amoeba_2_count = 0
	ckdelay_current = 0
	_time_decrement_sec = 0

	var ymin := 0 if border_scan_first_and_last else 1
	var ymax := h - 1 if border_scan_first_and_last else h - 2
	for y in range(ymin, ymax + 1):
		var row := y * w
		for x in w:
			var e: int = map[row + x]
			if (_flags[e] & E.P_SCANNED) != 0:
				map[row + x] = _pair[e]
				continue
			ckdelay_current += _ckdelay[e]
			if _active[e] == 0:
				continue
			_process_cell(x, y, player_move, player_fire, grav_compat)
			e = map[row + x]
			if (_flags[e] & E.P_SCANNED) != 0:
				map[row + x] = _pair[e]

	# postprocessing
	for i in map.size():
		var e: int = map[i]
		if (_flags[e] & E.P_SCANNED) != 0:
			e = _pair[e]
			map[i] = e
		if e == E.TIME_PENALTY:
			map[i] = E.scanned_pair(E.GRAVESTONE)
			_time_decrement_sec += time_penalty
	if short_explosions:
		for i in map.size():
			if (_flags[map[i]] & E.P_EXPLOSION_FIRST_STAGE) != 0:
				var e: int = map[i] + 1
				map[i] = _pair[e] if (_flags[e] & E.P_SCANNED) != 0 else e

	if player_state == PlayerState.LIVING:
		# GDash scans the whole map and keeps the last match: the first one from the top (1stB) or from the bottom.
		if active_is_first_found:
			for i in map.size():
				if (_flags[map[i]] & E.P_PLAYER) != 0:
					player_x = i % w
					player_y = i / w
					break
		else:
			for i in range(map.size() - 1, -1, -1):
				if (_flags[map[i]] & E.P_PLAYER) != 0:
					player_x = i % w
					player_y = i / w
					break
	for i in PLAYER_MEM_SIZE - 1:
		player_x_mem[i] = player_x_mem[i + 1]
		player_y_mem[i] = player_y_mem[i + 1]
	player_x_mem[PLAYER_MEM_SIZE - 1] = player_x
	player_y_mem[PLAYER_MEM_SIZE - 1] = player_y

	update_scheduling()

	if (player_state == PlayerState.LIVING and player_seen_ago > 15) or kill_player:
		player_state = PlayerState.DIED
	if voodoo_touched:
		kill_player = true

	if amoeba_state == AmoebaState.AWAKE:
		if _amoeba_count >= amoeba_max_count:
			amoeba_state = AmoebaState.TOO_BIG
		if _amoeba_found_enclosed:
			amoeba_state = AmoebaState.ENCLOSED
	if magic_wall_stops_amoeba and magic_wall_state == MagicWallState.ACTIVE:
		amoeba_state = AmoebaState.ENCLOSED
	if amoeba_2_state == AmoebaState.AWAKE:
		if _amoeba_2_count >= amoeba_2_max_count:
			amoeba_2_state = AmoebaState.TOO_BIG
		if _amoeba_2_found_enclosed:
			amoeba_2_state = AmoebaState.ENCLOSED
	if magic_wall_stops_amoeba and magic_wall_state == MagicWallState.ACTIVE:
		amoeba_2_state = AmoebaState.ENCLOSED

	time -= _time_decrement_sec * timing_factor
	if time < 0:
		time = 0
	if hatched:
		var seconds_before := time / timing_factor
		time -= speed
		if time <= 0:
			time = 0
		if seconds_before != time / timing_factor:
			events.append(["seconds", time_visible()])
		time_elapsed += speed

	if gravity_will_change > 0:
		gravity_will_change -= speed
		if gravity_will_change < 0:
			gravity_will_change = 0
		if gravity_will_change == 0:
			gravity = gravity_next_direction
			if gravity_change_sound:
				_sound("gravity_change", player_x, player_y)

	if creatures_direction_will_change > 0:
		creatures_direction_will_change -= speed
		if creatures_direction_will_change < 0:
			creatures_direction_will_change = 0
		if creatures_direction_will_change == 0:
			if creature_direction_auto_change_sound:
				_sound("switch_creatures", player_x, player_y)
			creatures_backwards = not creatures_backwards
			creatures_direction_will_change = creatures_direction_auto_change_time * timing_factor

	if magic_wall_state == MagicWallState.ACTIVE and (hatched or not magic_timer_wait_for_hatching):
		magic_wall_time -= speed
		if magic_wall_time < 0:
			magic_wall_time = 0
		if magic_wall_time == 0:
			magic_wall_state = MagicWallState.EXPIRED

	if amoeba_timer_started_immediately or (amoeba_state == AmoebaState.AWAKE \
			and (hatched or not amoeba_timer_wait_for_hatching)):
		amoeba_time -= speed
		if amoeba_time < 0:
			amoeba_time = 0
		if amoeba_time == 0:
			amoeba_growth_prob = amoeba_fast_growth_prob
	if amoeba_timer_started_immediately or (amoeba_2_state == AmoebaState.AWAKE \
			and (hatched or not amoeba_timer_wait_for_hatching)):
		amoeba_2_time -= speed
		if amoeba_2_time < 0:
			amoeba_2_time = 0
		if amoeba_2_time == 0:
			amoeba_2_growth_prob = amoeba_2_fast_growth_prob

	var start_signal := false
	if scheduling == CaveScheduling.MILLISECONDS:
		if hatching_delay_frame > 0:
			hatching_delay_frame -= 1
			if hatching_delay_frame == 0:
				start_signal = true
	else:
		if hatching_delay_time > 0:
			hatching_delay_time -= speed
			if hatching_delay_time <= 0:
				hatching_delay_time = 0
				start_signal = true
	if start_signal:
		hatched = true
		count_diamonds()
		if creatures_direction_auto_change_time != 0:
			creatures_direction_will_change = creatures_direction_auto_change_time * timing_factor
			if creatures_direction_auto_change_on_start:
				creatures_backwards = not creatures_backwards
		if player_state == PlayerState.NOT_YET:
			player_state = PlayerState.LIVING
		_sound("crack", player_x, player_y)

	if biters_wait_frame == 0:
		biters_wait_frame = biter_delay_frame
	else:
		biters_wait_frame -= 1
	if replicators_wait_frame == 0:
		replicators_wait_frame = replicator_delay_frame
	else:
		replicators_wait_frame -= 1

	if player_state != PlayerState.TIMEOUT and time == 0:
		player_state = PlayerState.TIMEOUT
		_sound("timeout", player_x, player_y)

	last_direction = player_move
	if player_move == D.LEFT or player_move == D.UP_LEFT or player_move == D.DOWN_LEFT:
		last_horizontal_direction = D.LEFT
	if player_move == D.RIGHT or player_move == D.UP_RIGHT or player_move == D.DOWN_RIGHT:
		last_horizontal_direction = D.RIGHT
	return player_move


func _process_cell(x: int, y: int, player_move: int, player_fire: bool, grav_compat: int) -> void:
	var e := _at(x, y)
	match e:
		E.PLAYER:
			_process_player(x, y, player_move, player_fire)
		E.PLAYER_BOMB:
			_process_player_bomb(x, y, player_move, player_fire)
		E.PLAYER_ROCKET_LAUNCHER:
			_process_player_rocket_launcher(x, y, player_move, player_fire)
		E.PLAYER_STIRRING:
			if kill_player:
				_explode(x, y)
				return
			_sound("stirring", x, y)
			player_seen_ago = 0
			if player_state != PlayerState.EXITED:
				player_state = PlayerState.LIVING
			if player_fire:
				gravity_disabled = false
				_store(x, y, E.PLAYER)
				gravity_switch_active = true
		E.PLAYER_PNEUMATIC_LEFT, E.PLAYER_PNEUMATIC_RIGHT:
			if kill_player:
				_explode(x, y)
				return
			player_seen_ago = 0
			if player_state != PlayerState.EXITED:
				player_state = PlayerState.LIVING
			if pneumatic_hammer_active_delay == 0:
				_store(x, y, E.PLAYER)
		E.PNEUMATIC_ACTIVE_RIGHT, E.PNEUMATIC_ACTIVE_LEFT:
			if pneumatic_hammer_active_delay > 0:
				_sound("pneumatic_hammer", x, y)
			if pneumatic_hammer_active_delay == 0:
				_store(x, y, E.SPACE)
				var new_elem := get_hammered(_get_dir(x, y, D.DOWN))
				if new_elem != E.NONE:
					_store_dir(x, y, D.DOWN, new_elem)
					if hammered_walls_reappear:
						var yy := (y + 1) % h
						hammered_reappear[yy * w + ((x + w) % w)] = hammered_wall_reappear_frame

		# stones, diamonds
		E.STONE:
			_do_start_fall(x, y, gravity, stone_falling_effect)
		E.MEGA_STONE:
			_do_start_fall(x, y, gravity, E.MEGA_STONE_F)
		E.DIAMOND:
			_do_start_fall(x, y, gravity, diamond_falling_effect)
		E.NUT:
			_do_start_fall(x, y, gravity, E.NUT_F)
		E.DIRT_BALL:
			_do_start_fall(x, y, gravity, E.DIRT_BALL_F)
		E.DIRT_LOOSE:
			_do_start_fall(x, y, gravity, E.DIRT_LOOSE_F)
		E.FLYING_STONE:
			_do_start_fall(x, y, OPPOSITE[gravity], E.FLYING_STONE_F)
		E.FLYING_DIAMOND:
			_do_start_fall(x, y, OPPOSITE[gravity], E.FLYING_DIAMOND_F)

		# falling elements
		E.DIRT_BALL_F:
			if not gravity_disabled:
				_do_fall_roll_or_stop(x, y, gravity, E.DIRT_BALL)
		E.DIRT_LOOSE_F:
			if not gravity_disabled:
				_do_fall_roll_or_stop(x, y, gravity, E.DIRT_LOOSE)
		E.STONE_F:
			if not gravity_disabled:
				if _do_fall_try_crush_voodoo(x, y, gravity): return
				if _do_fall_try_crack_nut(x, y, gravity, stone_bouncing_effect): return
				if _do_fall_try_magic(x, y, gravity, magic_stone_to): return
				if _do_fall_try_crush(x, y, gravity): return
				_do_fall_roll_or_stop(x, y, gravity, stone_bouncing_effect)
		E.MEGA_STONE_F:
			if not gravity_disabled:
				if _do_fall_try_crush_voodoo(x, y, gravity): return
				if _do_fall_try_crack_nut(x, y, gravity, E.MEGA_STONE): return
				if _do_fall_try_magic(x, y, gravity, magic_mega_stone_to): return
				if _do_fall_try_crush(x, y, gravity): return
				_do_fall_roll_or_stop(x, y, gravity, E.MEGA_STONE)
		E.DIAMOND_F:
			if not gravity_disabled:
				if _do_fall_try_eat_voodoo(x, y, gravity): return
				if _do_fall_try_magic(x, y, gravity, magic_diamond_to): return
				if _do_fall_try_crush(x, y, gravity): return
				_do_fall_roll_or_stop(x, y, gravity, diamond_bouncing_effect)
		E.NUT_F:
			if not gravity_disabled:
				if _do_fall_try_magic(x, y, gravity, magic_nut_to): return
				if _do_fall_try_crush(x, y, gravity): return
				_do_fall_roll_or_stop(x, y, gravity, E.NUT)
		E.FLYING_STONE_F:
			if not gravity_disabled:
				var fall_dir := OPPOSITE[gravity]
				if _do_fall_try_crush_voodoo(x, y, fall_dir): return
				if _do_fall_try_crack_nut(x, y, fall_dir, E.FLYING_STONE): return
				if _do_fall_try_magic(x, y, fall_dir, magic_flying_stone_to): return
				if _do_fall_try_crush(x, y, fall_dir): return
				_do_fall_roll_or_stop(x, y, fall_dir, E.FLYING_STONE)
		E.FLYING_DIAMOND_F:
			if not gravity_disabled:
				var fall_dir := OPPOSITE[gravity]
				if _do_fall_try_eat_voodoo(x, y, fall_dir): return
				if _do_fall_try_magic(x, y, fall_dir, magic_flying_diamond_to): return
				if _do_fall_try_crush(x, y, fall_dir): return
				_do_fall_roll_or_stop(x, y, fall_dir, E.FLYING_DIAMOND)

		# nitro pack
		E.NITRO_PACK:
			_do_start_fall(x, y, gravity, E.NITRO_PACK_F)
		E.NITRO_PACK_F:
			if not gravity_disabled:
				if _is_like_space(x, y, gravity):
					_move(x, y, gravity, E.NITRO_PACK_F)
				elif _do_fall_try_magic(x, y, gravity, magic_nitro_pack_to):
					pass
				elif _is_like_dirt(x, y, gravity):
					_store(x, y, E.NITRO_PACK)
					_effect(E.NITRO_PACK, x, y)
				else:
					_explode(x, y)
		E.NITRO_PACK_EXPLODE:
			_explode(x, y)

		# creatures
		E.COW_1, E.COW_2, E.COW_3, E.COW_4:
			if not _is_like_space(x, y, D.UP) and not _is_like_space(x, y, D.DOWN) \
					and not _is_like_space(x, y, D.LEFT) and not _is_like_space(x, y, D.RIGHT):
				_store(x, y, E.COW_ENCLOSED_1)
			else:
				_move_creature(x, y, E.COW_1)
		E.COW_ENCLOSED_1, E.COW_ENCLOSED_2, E.COW_ENCLOSED_3, E.COW_ENCLOSED_4, E.COW_ENCLOSED_5, E.COW_ENCLOSED_6:
			if _is_like_space(x, y, D.UP) or _is_like_space(x, y, D.LEFT) or _is_like_space(x, y, D.RIGHT) \
					or _is_like_space(x, y, D.DOWN):
				_store(x, y, E.COW_1)
			else:
				_next(x, y)
		E.COW_ENCLOSED_7:
			if _is_like_space(x, y, D.UP) or _is_like_space(x, y, D.LEFT) or _is_like_space(x, y, D.RIGHT) \
					or _is_like_space(x, y, D.DOWN):
				_store(x, y, E.COW_1)
			else:
				_store(x, y, E.SKELETON)
		E.FIREFLY_1, E.FIREFLY_2, E.FIREFLY_3, E.FIREFLY_4, E.ALT_FIREFLY_1, E.ALT_FIREFLY_2, E.ALT_FIREFLY_3, \
				E.ALT_FIREFLY_4, E.BUTTER_1, E.BUTTER_2, E.BUTTER_3, E.BUTTER_4, E.ALT_BUTTER_1, E.ALT_BUTTER_2, \
				E.ALT_BUTTER_3, E.ALT_BUTTER_4, E.STONEFLY_1, E.STONEFLY_2, E.STONEFLY_3, E.STONEFLY_4:
			if _get_dir(x, y, D.LEFT) == E.VOODOO or _get_dir(x, y, D.RIGHT) == E.VOODOO \
					or _get_dir(x, y, D.UP) == E.VOODOO or _get_dir(x, y, D.DOWN) == E.VOODOO:
				voodoo_touched = true
			if _blows_up_flies(x, y, D.DOWN) or _blows_up_flies(x, y, D.UP) \
					or _blows_up_flies(x, y, D.LEFT) or _blows_up_flies(x, y, D.RIGHT):
				_explode(x, y)
			else:
				var base: int
				if e >= E.FIREFLY_1 and e <= E.FIREFLY_4:
					base = E.FIREFLY_1
				elif e >= E.BUTTER_1 and e <= E.BUTTER_4:
					base = E.BUTTER_1
				elif e >= E.STONEFLY_1 and e <= E.STONEFLY_4:
					base = E.STONEFLY_1
				elif e >= E.ALT_FIREFLY_1 and e <= E.ALT_FIREFLY_4:
					base = E.ALT_FIREFLY_1
				else:
					base = E.ALT_BUTTER_1
				_move_creature(x, y, base)
		E.WAITING_STONE:
			if _is_like_space(x, y, grav_compat):
				_move(x, y, grav_compat, E.CHASING_STONE)
			elif _sloped(x, y, grav_compat, OPPOSITE[grav_compat]):
				if _sloped(x, y, grav_compat, CW_FOURTH[grav_compat]) and _is_like_space(x, y, CW_FOURTH[grav_compat]) \
						and _is_like_space(x, y, CW_EIGHTH[grav_compat]):
					_move(x, y, CW_FOURTH[grav_compat], E.WAITING_STONE)
				elif _sloped(x, y, grav_compat, CCW_FOURTH[grav_compat]) \
						and _is_like_space(x, y, CCW_FOURTH[grav_compat]) \
						and _is_like_space(x, y, CCW_EIGHTH[grav_compat]):
					_move(x, y, CCW_FOURTH[grav_compat], E.WAITING_STONE)
		E.CHASING_STONE:
			_process_chasing_stone(x, y)
		E.REPLICATOR:
			if replicators_wait_frame == 0 and replicators_active and not gravity_disabled:
				if _is_like_space(x, y, gravity) and not is_player(x, y, OPPOSITE[gravity]) \
						and not _is_scanned(x, y, OPPOSITE[gravity]):
					_store_dir(x, y, gravity, _get_dir(x, y, OPPOSITE[gravity]))
					_sound("replicator", x, y)
		E.BITER_1, E.BITER_2, E.BITER_3, E.BITER_4:
			if biters_wait_frame == 0:
				_process_biter(x, y)
		E.DRAGONFLY_1, E.DRAGONFLY_2, E.DRAGONFLY_3, E.DRAGONFLY_4:
			if _get_dir(x, y, D.LEFT) == E.VOODOO or _get_dir(x, y, D.RIGHT) == E.VOODOO \
					or _get_dir(x, y, D.UP) == E.VOODOO or _get_dir(x, y, D.DOWN) == E.VOODOO:
				voodoo_touched = true
			if _blows_up_flies(x, y, D.DOWN) or _blows_up_flies(x, y, D.UP) \
					or _blows_up_flies(x, y, D.LEFT) or _blows_up_flies(x, y, D.RIGHT):
				_explode(x, y)
			else:
				var ccw := _rotates_ccw(x, y)
				var base := E.DRAGONFLY_1
				var dir := e - base
				var creature_move := CREATURE_CHDIR if creatures_backwards else CREATURE_DIR
				if creatures_backwards:
					ccw = not ccw
				var dirn := (dir + 3) & 3 if ccw else (dir + 1) & 3
				if _is_like_space(x, y, creature_move[dir]):
					_move(x, y, creature_move[dir], base + dir)
				else:
					_store(x, y, base + dirn)
		E.BLADDER:
			_store(x, y, E.BLADDER_1)
		E.BLADDER_1, E.BLADDER_2, E.BLADDER_3, E.BLADDER_4, E.BLADDER_5, E.BLADDER_6, E.BLADDER_7, E.BLADDER_8:
			_process_bladder(x, y, grav_compat)
		E.GHOST:
			if _blows_up_flies(x, y, D.DOWN) or _blows_up_flies(x, y, D.UP) \
					or _blows_up_flies(x, y, D.LEFT) or _blows_up_flies(x, y, D.RIGHT):
				_explode(x, y)
			else:
				for i in 4:
					var random_dir := GHOST_DIRS[random.rand_int_range(0, GHOST_DIRS.size())]
					if _is_like_space(x, y, random_dir):
						_move(x, y, random_dir, E.GHOST)
						break

		# active elements
		E.AMOEBA:
			_process_amoeba(x, y)
		E.AMOEBA_2:
			_process_amoeba_2(x, y)
		E.ACID:
			if random.rand_int_range(0, 1000000) <= acid_spread_ratio:
				_store(x, y, acid_turns_to)
				for dir in [D.UP, D.DOWN, D.LEFT, D.RIGHT]:
					if _is_like_element(x, y, dir, acid_eats_this):
						_store_dir(x, y, dir, E.ACID)
						_effect(E.ACID, x, y)
		E.WATER:
			if not water_does_not_flow_down and _is_like_space(x, y, D.DOWN):
				_store_dir(x, y, D.DOWN, E.WATER_1)
			if _is_like_space(x, y, D.UP):
				_store_dir(x, y, D.UP, E.WATER_1)
			if _is_like_space(x, y, D.LEFT):
				_store_dir(x, y, D.LEFT, E.WATER_1)
			if _is_like_space(x, y, D.RIGHT):
				_store_dir(x, y, D.RIGHT, E.WATER_1)
		E.WATER_16:
			_store(x, y, E.WATER)
		E.H_EXPANDING_WALL, E.V_EXPANDING_WALL, E.H_EXPANDING_STEEL_WALL, E.V_EXPANDING_STEEL_WALL:
			var horizontal: bool = ((e == E.H_EXPANDING_WALL or e == E.H_EXPANDING_STEEL_WALL) and not expanding_wall_changed) \
					or ((e == E.V_EXPANDING_WALL or e == E.V_EXPANDING_STEEL_WALL) and expanding_wall_changed)
			if horizontal:
				if _is_like_space(x, y, D.LEFT):
					_store_dir(x, y, D.LEFT, e)
					_effect(e, x, y, D.LEFT)
				elif _is_like_space(x, y, D.RIGHT):
					_store_dir(x, y, D.RIGHT, e)
					_effect(e, x, y, D.RIGHT)
			else:
				if _is_like_space(x, y, D.UP):
					_store_dir(x, y, D.UP, e)
					_effect(e, x, y, D.UP)
				elif _is_like_space(x, y, D.DOWN):
					_store_dir(x, y, D.DOWN, e)
					_effect(e, x, y, D.DOWN)
		E.EXPANDING_WALL, E.EXPANDING_STEEL_WALL:
			for dir in [D.LEFT, D.RIGHT, D.UP, D.DOWN]:
				if _is_like_space(x, y, dir):
					_store_dir(x, y, dir, _at(x, y))
					_effect(_at(x, y), x, y, dir)
		E.SLIME:
			_process_slime(x, y)
		E.FALLING_WALL:
			if _is_like_space(x, y, grav_compat):
				var yy := y + 1
				while yy < y + h:
					if not _is_like_space(x, yy):
						break
					yy += 1
				var below := _at(x, yy)
				if below == E.PLAYER or below == E.PLAYER_GLUED or below == E.PLAYER_BOMB:
					_move(x, y, grav_compat, E.FALLING_WALL_F)
		E.FALLING_WALL_F:
			if is_player(x, y, grav_compat):
				_explode(x, y)
			elif _is_like_space(x, y, grav_compat):
				_move(x, y, grav_compat, E.FALLING_WALL_F)
			else:
				_effect(E.FALLING_WALL_F, x, y)
				_store(x, y, E.FALLING_WALL)

		# conveyor belts
		E.CONVEYOR_RIGHT, E.CONVEYOR_LEFT:
			if not gravity_disabled and conveyor_belts_active:
				var left := e != E.CONVEYOR_RIGHT
				if conveyor_belts_direction_changed:
					left = not left
				var dir := CCW_EIGHTH if left else CW_EIGHTH
				if (gravity == D.DOWN and _moved_by_conveyor_top(x, y, D.UP)) \
						or (gravity == D.UP and _moved_by_conveyor_bottom(x, y, D.UP)):
					if _is_like_space(x, y, dir[D.UP]):
						_store_dir(x, y, dir[D.UP], _get_dir(x, y, D.UP))
						_store_dir(x, y, D.UP, E.SPACE)
				if (gravity == D.UP and _moved_by_conveyor_top(x, y, D.DOWN)) \
						or (gravity == D.DOWN and _moved_by_conveyor_bottom(x, y, D.DOWN)):
					if _is_like_space(x, y, dir[D.DOWN]):
						_store_dir(x, y, dir[D.DOWN], _get_dir(x, y, D.DOWN))
						_store_dir(x, y, D.DOWN, E.SPACE)

		# rockets
		E.ROCKET_1:
			_rocket(x, y, D.RIGHT, e)
		E.ROCKET_2:
			_rocket(x, y, D.UP, e)
		E.ROCKET_3:
			_rocket(x, y, D.LEFT, e)
		E.ROCKET_4:
			_rocket(x, y, D.DOWN, e)

		# simple changes, explosions
		E.EXPLODE_3:
			_store(x, y, explosion_3_effect)
		E.EXPLODE_5:
			_store(x, y, explosion_effect)
		E.NUT_CRACK_4:
			_store(x, y, E.DIAMOND)
		E.PRE_DIA_5:
			_store(x, y, diamond_birth_effect)
		E.PRE_STONE_4:
			_store(x, y, E.STONE)
		E.NITRO_EXPL_4:
			_store(x, y, nitro_explosion_effect)
		E.BOMB_EXPL_4:
			_store(x, y, bomb_explosion_effect)
		E.AMOEBA_2_EXPL_4:
			_store(x, y, amoeba_2_explosion_effect)
		E.GHOST_EXPL_4:
			_store(x, y, ghost_explode_to[random.rand_int_range(0, ghost_explode_to.size())])
		E.PRE_STEEL_4:
			_store(x, y, E.STEEL)
		E.PRE_CLOCK_4:
			_store(x, y, E.CLOCK)
		E.BOMB_TICK_7:
			_explode(x, y)
		E.TRAPPED_DIAMOND:
			if diamond_key_collected:
				_store(x, y, E.DIAMOND)
		E.PRE_OUTBOX:
			if gate_open:
				_store(x, y, E.OUTBOX)
		E.PRE_INVIS_OUTBOX:
			if gate_open:
				_store(x, y, E.INVIS_OUTBOX)
		E.INBOX:
			player_seen_ago = 0
			if hatched and not _inbox_toggle:
				_store(x, y, E.PRE_PL_1)
			_inbox_toggle = not _inbox_toggle
		E.PRE_PL_1:
			player_seen_ago = 0
			_store(x, y, E.PRE_PL_2)
		E.PRE_PL_2:
			player_seen_ago = 0
			_store(x, y, E.PRE_PL_3)
		E.PRE_PL_3:
			player_seen_ago = 0
			_store(x, y, E.PLAYER)
		E.PRE_DIA_1, E.PRE_DIA_2, E.PRE_DIA_3, E.PRE_DIA_4, E.PRE_STONE_1, E.PRE_STONE_2, E.PRE_STONE_3, \
				E.BOMB_TICK_1, E.BOMB_TICK_2, E.BOMB_TICK_3, E.BOMB_TICK_4, E.BOMB_TICK_5, E.BOMB_TICK_6, \
				E.PRE_STEEL_1, E.PRE_STEEL_2, E.PRE_STEEL_3, E.BOMB_EXPL_1, E.BOMB_EXPL_2, E.BOMB_EXPL_3, \
				E.NUT_CRACK_1, E.NUT_CRACK_2, E.NUT_CRACK_3, E.GHOST_EXPL_1, E.GHOST_EXPL_2, E.GHOST_EXPL_3, \
				E.EXPLODE_1, E.EXPLODE_2, E.EXPLODE_4, E.PRE_CLOCK_1, E.PRE_CLOCK_2, E.PRE_CLOCK_3, \
				E.NITRO_EXPL_1, E.NITRO_EXPL_2, E.NITRO_EXPL_3, E.AMOEBA_2_EXPL_1, E.AMOEBA_2_EXPL_2, \
				E.AMOEBA_2_EXPL_3:
			_next(x, y)
		E.WATER_1, E.WATER_2, E.WATER_3, E.WATER_4, E.WATER_5, E.WATER_6, E.WATER_7, E.WATER_8, E.WATER_9, \
				E.WATER_10, E.WATER_11, E.WATER_12, E.WATER_13, E.WATER_14, E.WATER_15:
			_sound("water", x, y)
			_next(x, y)
		E.BLADDER_SPENDER:
			if _is_like_space(x, y, OPPOSITE[grav_compat]):
				_store_dir(x, y, OPPOSITE[grav_compat], E.BLADDER)
				_store(x, y, E.PRE_STEEL_1)
				_effect(E.BLADDER_SPENDER, x, y)
		E.MAGIC_WALL:
			if magic_wall_state == MagicWallState.ACTIVE:
				_effect(E.MAGIC_WALL, x, y)
		E.LAVA:
			_particles(x, y, E.LAVA)


static func _build_active_table() -> void:
	_active.resize(E.COUNT)
	var inert: Array[int] = [E.SPACE, E.DIRT, E.DIRT2, E.DIRT_SLOPED_UP_RIGHT, E.DIRT_SLOPED_UP_LEFT,
		E.DIRT_SLOPED_DOWN_LEFT, E.DIRT_SLOPED_DOWN_RIGHT, E.BRICK, E.BRICK_SLOPED_UP_RIGHT, E.BRICK_SLOPED_UP_LEFT,
		E.BRICK_SLOPED_DOWN_LEFT, E.BRICK_SLOPED_DOWN_RIGHT, E.BRICK_NON_SLOPED, E.STEEL, E.STEEL_SLOPED_UP_RIGHT,
		E.STEEL_SLOPED_UP_LEFT, E.STEEL_SLOPED_DOWN_LEFT, E.STEEL_SLOPED_DOWN_RIGHT, E.STEEL_EXPLODABLE,
		E.STEEL_EATABLE, E.BRICK_EATABLE, E.OUTBOX, E.INVIS_OUTBOX]
	_active.fill(1)
	for e in inert:
		_active[e] = 0


func _move_creature(x: int, y: int, base: int) -> void:
	var ccw := _rotates_ccw(x, y)
	var dir := _at(x, y) - base
	var creature_move := CREATURE_CHDIR if creatures_backwards else CREATURE_DIR
	if creatures_backwards:
		ccw = not ccw
	var dirn: int
	var dirp: int
	if ccw:
		dirn = (dir + 3) & 3
		dirp = (dir + 1) & 3
	else:
		dirn = (dir + 1) & 3
		dirp = (dir + 3) & 3
	if _is_like_space(x, y, creature_move[dirn]):
		_move(x, y, creature_move[dirn], base + dirn)
	elif _is_like_space(x, y, creature_move[dir]):
		_move(x, y, creature_move[dir], base + dir)
	else:
		_store(x, y, base + dirp)


func _rocket(x: int, y: int, dir: int, element: int) -> void:
	if _is_like_space(x, y, dir):
		_move(x, y, dir, element)
		_particles(x, y, element)
	else:
		_explode(x, y)


func _player_alive_check(x: int, y: int) -> bool:
	if kill_player:
		_explode(x, y)
		return false
	player_seen_ago = 0
	if player_state != PlayerState.EXITED:
		player_state = PlayerState.LIVING
	return true


func _process_player(x: int, y: int, player_move: int, player_fire: bool) -> void:
	if not _player_alive_check(x, y):
		return
	if player_fire and got_pneumatic_hammer and _is_like_space(x, y, player_move) \
			and not _is_like_space(x, y, D.DOWN):
		if player_move == D.LEFT and _can_be_hammered(x, y, D.DOWN_LEFT):
			pneumatic_hammer_active_delay = pneumatic_hammer_frame
			_store_dir(x, y, D.LEFT, E.PNEUMATIC_ACTIVE_LEFT)
			_store(x, y, E.PLAYER_PNEUMATIC_LEFT)
			return
		if player_move == D.RIGHT and _can_be_hammered(x, y, D.DOWN_RIGHT):
			pneumatic_hammer_active_delay = pneumatic_hammer_frame
			_store_dir(x, y, D.RIGHT, E.PNEUMATIC_ACTIVE_RIGHT)
			_store(x, y, E.PLAYER_PNEUMATIC_RIGHT)
			return
	if player_move == D.STILL:
		return
	var what := _get_dir(x, y, player_move)
	var remains := E.NONE
	if what == E.TELEPORTER and _do_teleporter(x, y, player_move):
		return
	var push := _do_push(x, y, player_move, player_fire)
	if push:
		remains = E.SPACE
	else:
		match what:
			E.BOMB:
				_sound("bomb_collect", x, y)
				_store_dir(x, y, player_move, E.SPACE)
				if player_fire:
					_store(x, y, E.PLAYER_BOMB)
				else:
					_move(x, y, player_move, E.PLAYER_BOMB)
			E.ROCKET_LAUNCHER:
				_sound("bomb_collect", x, y)
				_store_dir(x, y, player_move, E.SPACE)
				if player_fire:
					_store(x, y, E.PLAYER_ROCKET_LAUNCHER)
				else:
					_move(x, y, player_move, E.PLAYER_ROCKET_LAUNCHER)
			E.POT:
				if not player_fire and not gravity_switch_active and skeletons_collected >= skeletons_needed_for_pot:
					skeletons_collected -= skeletons_needed_for_pot
					_move(x, y, player_move, E.PLAYER_STIRRING)
					gravity_disabled = true
			_:
				remains = _player_eat_element(what, x, y, player_move)
	if remains != E.NONE:
		if remains == E.SPACE and player_fire and not push:
			remains = snap_element
		if remains != E.SPACE or player_fire:
			_store_dir(x, y, player_move, remains)
		else:
			_move(x, y, player_move, E.PLAYER)


func _process_player_bomb(x: int, y: int, player_move: int, player_fire: bool) -> void:
	if not _player_alive_check(x, y):
		return
	if player_move == D.STILL:
		return
	var what := _get_dir(x, y, player_move)
	var remains := E.NONE
	if player_fire:
		if _is_like_space(x, y, player_move) or _is_like_dirt(x, y, player_move):
			_store_dir(x, y, player_move, E.BOMB_TICK_1)
			_store(x, y, E.PLAYER)
			_sound("bomb_place", x, y)
		return
	if what == E.TELEPORTER and _do_teleporter(x, y, player_move):
		return
	if _do_push(x, y, player_move, false):
		remains = E.SPACE
	else:
		remains = _player_eat_element(what, x, y, player_move)
	if remains != E.NONE:
		_move(x, y, player_move, E.PLAYER_BOMB)


func _process_player_rocket_launcher(x: int, y: int, player_move: int, player_fire: bool) -> void:
	if not _player_alive_check(x, y):
		return
	if player_move == D.STILL:
		return
	var what := _get_dir(x, y, player_move)
	var remains := E.NONE
	if player_fire:
		if _is_like_space(x, y, player_move):
			var rocket := E.NONE
			match player_move:
				D.RIGHT: rocket = E.ROCKET_1
				D.UP: rocket = E.ROCKET_2
				D.LEFT: rocket = E.ROCKET_3
				D.DOWN: rocket = E.ROCKET_4
			if rocket != E.NONE:
				_store_dir(x, y, player_move, rocket)
				if not infinite_rockets:
					_store(x, y, E.PLAYER)
			_sound("bomb_place", x, y)
		return
	if what == E.TELEPORTER and _do_teleporter(x, y, player_move):
		return
	if _do_push(x, y, player_move, false):
		remains = E.SPACE
	else:
		remains = _player_eat_element(what, x, y, player_move)
	if remains != E.NONE:
		_move(x, y, player_move, E.PLAYER_ROCKET_LAUNCHER)


func _process_chasing_stone(x: int, y: int) -> void:
	var px: int = player_x_mem[0]
	var py: int = player_y_mem[0]
	var horizontal := random.rand_boolean()
	var dont_move := false
	var i := 3
	while true:
		if horizontal:
			if px == x:
				i -= 1
				horizontal = not horizontal
				if i == 2:
					continue
			else:
				if px > x and _is_like_space(x, y, D.RIGHT):
					_move(x, y, D.RIGHT, E.CHASING_STONE)
					dont_move = true
					break
				elif px < x and _is_like_space(x, y, D.LEFT):
					_move(x, y, D.LEFT, E.CHASING_STONE)
					dont_move = true
					break
				else:
					i -= 2
					if i == 1:
						horizontal = not horizontal
						continue
		else:
			if py == y:
				i -= 1
				horizontal = not horizontal
				if i == 2:
					continue
			else:
				if py > y and _is_like_space(x, y, D.DOWN):
					_move(x, y, D.DOWN, E.CHASING_STONE)
					dont_move = true
					break
				elif py < y and _is_like_space(x, y, D.UP):
					_move(x, y, D.UP, E.CHASING_STONE)
					dont_move = true
					break
				else:
					i -= 2
					if i == 1:
						horizontal = not horizontal
						continue
		if i != 0:
			dont_move = true
		break
	if dont_move:
		return
	if horizontal:
		if x >= px:
			if _is_like_space(x, y, D.UP) and _is_like_space(x, y, D.UP_LEFT):
				_move(x, y, D.UP, E.CHASING_STONE)
			elif _is_like_space(x, y, D.DOWN) and _is_like_space(x, y, D.DOWN_LEFT):
				_move(x, y, D.DOWN, E.CHASING_STONE)
		else:
			if _is_like_space(x, y, D.UP) and _is_like_space(x, y, D.UP_RIGHT):
				_move(x, y, D.UP, E.CHASING_STONE)
			elif _is_like_space(x, y, D.DOWN) and _is_like_space(x, y, D.DOWN_RIGHT):
				_move(x, y, D.DOWN, E.CHASING_STONE)
	else:
		if y >= py:
			if _is_like_space(x, y, D.LEFT) and _is_like_space(x, y, D.UP_LEFT):
				_move(x, y, D.LEFT, E.CHASING_STONE)
			elif _is_like_space(x, y, D.RIGHT) and _is_like_space(x, y, D.UP_RIGHT):
				_move(x, y, D.RIGHT, E.CHASING_STONE)
		else:
			if _is_like_space(x, y, D.LEFT) and _is_like_space(x, y, D.DOWN_LEFT):
				_move(x, y, D.LEFT, E.CHASING_STONE)
			elif _is_like_space(x, y, D.RIGHT) and _is_like_space(x, y, D.DOWN_RIGHT):
				_move(x, y, D.RIGHT, E.CHASING_STONE)


func _process_biter(x: int, y: int) -> void:
	var biter_try: Array[int] = [E.DIRT, biter_eat, E.SPACE, E.STONE]
	var dir := _at(x, y) - E.BITER_1
	var dirn := (dir + 3) & 3
	var dirp := (dir + 1) & 3
	var made_sound_of := E.NONE
	var i := 0
	while i < biter_try.size():
		var moved := -1
		if _is_like_element(x, y, BITER_MOVE[dir], biter_try[i]):
			moved = dir
		elif _is_like_element(x, y, BITER_MOVE[dirn], biter_try[i]):
			moved = dirn
		elif _is_like_element(x, y, BITER_MOVE[dirp], biter_try[i]):
			moved = dirp
		if moved >= 0:
			var mdir := BITER_MOVE[moved]
			_eat(_get_dir(x, y, mdir), x + D.DX[mdir], y + D.DY[mdir])
			_move(x, y, mdir, E.BITER_1 + moved)
			if biter_try[i] != E.SPACE:
				made_sound_of = E.BITER_1
			break
		i += 1
	if i == biter_try.size():
		_store(x, y, E.BITER_1 + dirp)
	elif biter_try[i] == E.STONE:
		_store(x, y, E.STONE)
		made_sound_of = E.STONE
	if made_sound_of != E.NONE:
		_effect(made_sound_of, x, y)


func _process_bladder(x: int, y: int, grav_compat: int) -> void:
	var up := OPPOSITE[grav_compat]
	if _is_like_element(x, y, up, bladder_converts_by) \
			or _is_like_element(x, y, CW_FOURTH[grav_compat], bladder_converts_by) \
			or _is_like_element(x, y, CCW_FOURTH[grav_compat], bladder_converts_by):
		_store(x, y, E.PRE_CLOCK_1)
		_effect(E.PRE_CLOCK_1, x, y)
	elif _is_like_space(x, y, up):
		if _at(x, y) == E.BLADDER_8:
			_move(x, y, up, E.BLADDER_1)
			_effect(E.BLADDER, x, y)
		else:
			_next(x, y)
	elif _sloped_for_bladder(x, y, up) and _sloped(x, y, up, up):
		if _sloped(x, y, up, CCW_FOURTH[up]) and _is_like_space(x, y, CCW_FOURTH[up]) \
				and _is_like_space(x, y, CCW_EIGHTH[up]):
			if _at(x, y) == E.BLADDER_8:
				_move(x, y, CCW_FOURTH[up], E.BLADDER_8)
				_effect(E.BLADDER, x, y)
			else:
				_next(x, y)
		elif _sloped(x, y, up, CW_FOURTH[up]) and _is_like_space(x, y, CW_FOURTH[up]) \
				and _is_like_space(x, y, CW_EIGHTH[up]):
			if _at(x, y) == E.BLADDER_8:
				_move(x, y, CW_FOURTH[up], E.BLADDER_8)
				_effect(E.BLADDER, x, y)
			else:
				_next(x, y)
	else:
		_store(x, y, E.BLADDER_1)


func _amoeba_grow(x: int, y: int, element: int) -> void:
	match random.rand_int_range(0, 4):
		0:
			if _amoeba_eats(x, y, D.UP): _store_dir(x, y, D.UP, element)
		1:
			if _amoeba_eats(x, y, D.DOWN): _store_dir(x, y, D.DOWN, element)
		2:
			if _amoeba_eats(x, y, D.LEFT): _store_dir(x, y, D.LEFT, element)
		3:
			if _amoeba_eats(x, y, D.RIGHT): _store_dir(x, y, D.RIGHT, element)


func _process_amoeba(x: int, y: int) -> void:
	if hatched and amoeba_state == AmoebaState.AWAKE:
		_effect(E.AMOEBA, x, y)
	if convert_amoeba_this_frame and _amoeba_found_enclosed:
		_store(x, y, amoeba_enclosed_effect)
		return
	_amoeba_count += 1
	match amoeba_state:
		AmoebaState.TOO_BIG:
			_store(x, y, amoeba_too_big_effect)
		AmoebaState.ENCLOSED:
			_store(x, y, amoeba_enclosed_effect)
		AmoebaState.SLEEPING, AmoebaState.AWAKE:
			if _amoeba_found_enclosed:
				if _amoeba_eats(x, y, D.UP) or _amoeba_eats(x, y, D.DOWN) or _amoeba_eats(x, y, D.LEFT) \
						or _amoeba_eats(x, y, D.RIGHT):
					_amoeba_found_enclosed = false
					amoeba_state = AmoebaState.AWAKE
			if amoeba_state == AmoebaState.AWAKE:
				if random.rand_int_range(0, 1000000) < amoeba_growth_prob:
					_amoeba_grow(x, y, E.AMOEBA)


func _process_amoeba_2(x: int, y: int) -> void:
	if hatched and amoeba_2_state == AmoebaState.AWAKE:
		_effect(E.AMOEBA, x, y)
	_amoeba_2_count += 1
	if amoeba_2_explodes_by_amoeba and (_is_like_element(x, y, D.DOWN, E.AMOEBA) \
			or _is_like_element(x, y, D.UP, E.AMOEBA) or _is_like_element(x, y, D.LEFT, E.AMOEBA) \
			or _is_like_element(x, y, D.RIGHT, E.AMOEBA)):
		_explode(x, y)
		return
	match amoeba_2_state:
		AmoebaState.TOO_BIG:
			_store(x, y, amoeba_2_too_big_effect)
		AmoebaState.ENCLOSED:
			_store(x, y, amoeba_2_enclosed_effect)
		AmoebaState.SLEEPING, AmoebaState.AWAKE:
			if _amoeba_2_found_enclosed:
				if _amoeba_eats(x, y, D.UP) or _amoeba_eats(x, y, D.DOWN) or _amoeba_eats(x, y, D.LEFT) \
						or _amoeba_eats(x, y, D.RIGHT):
					_amoeba_2_found_enclosed = false
					amoeba_2_state = AmoebaState.AWAKE
			if amoeba_2_state == AmoebaState.AWAKE:
				if random.rand_int_range(0, 1000000) < amoeba_2_growth_prob:
					_amoeba_grow(x, y, E.AMOEBA_2)


func _process_slime(x: int, y: int) -> void:
	var passes: bool
	if slime_predictable:
		passes = (c64_rand.random() & slime_permeability_c64) == 0
	else:
		passes = random.rand_int_range(0, 1000000) < slime_permeability
	if not passes:
		return
	var grav := gravity
	var oppos := OPPOSITE[gravity]
	if _is_like_space(x, y, grav):
		var above := _get_dir(x, y, oppos)
		var converted := -1
		if above == slime_eats_1:
			converted = slime_converts_1
		elif above == slime_eats_2:
			converted = slime_converts_2
		elif above == slime_eats_3:
			converted = slime_converts_3
		elif above == E.WAITING_STONE:
			converted = E.WAITING_STONE
		elif above == E.CHASING_STONE:
			converted = E.CHASING_STONE
		if converted >= 0:
			_store_dir(x, y, grav, converted)
			_store_dir(x, y, oppos, E.SPACE)
			_effect(E.SLIME, x, y)
	elif _is_like_space(x, y, oppos):
		var below := _get_dir(x, y, grav)
		var converted := -1
		if below == E.BLADDER:
			converted = E.BLADDER_1
		elif below == E.FLYING_STONE:
			converted = E.FLYING_STONE_F
		elif below == E.FLYING_DIAMOND:
			converted = E.FLYING_DIAMOND_F
		if converted >= 0:
			_store_dir(x, y, grav, E.SPACE)
			_store_dir(x, y, oppos, converted)
			_effect(E.SLIME, x, y)
