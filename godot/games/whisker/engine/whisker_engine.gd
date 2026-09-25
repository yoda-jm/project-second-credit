class_name WhiskerEngine
extends RefCounted
## Rules of Whisker Alley (inspired by Alley Cat, 1984). Pure logic, fixed ticks, seeded random generator.
##
## The alley: a cat walks the ground, bounces off trash-can lids onto the fence, rides the moving clotheslines and
## jumps into open windows of the building. A bulldog patrols the ground; residents throw shoes from open windows.
## Each window leads to a room with a short challenge (WhiskerRoom subclasses); clearing rooms scores and raises
## the level. Our own tuning throughout; the original's layout and timings are still to be checked.
##
## Units are metres, x to the right, y up. The alley is W x H.

signal event(kind: String, data: Dictionary)  ## "jump", "bounce", "land", "window_open", "window_close",
## "enter_room", "leave_room", "room_won", "room_failed", "shoe", "shoe_hit", "dog_bark", "death", "phase",
## "game_over", and room-specific events (see the rooms)

enum Phase { READY, ALLEY, ROOM, DYING, GAME_OVER }
enum RoomKind { FISHBOWL, MICE, BIRDCAGE, DOGBOWLS, HEARTS }

const TICK := 1.0 / 60.0
const W := 24.0
const H := 14.0
const READY_SECONDS := 1.5
const DYING_SECONDS := 2.0
const LIVES := 9
const WALK := 5.0
const AIR_CONTROL := 4.6
const JUMP := 11.6  ## about 2.2 m high
const BOUNCE := 14.2  ## off a trash-can lid: about 3.4 m high
const CAN_X: Array[float] = [3.0, 7.5, 12.0, 16.5, 21.0]
const CAN_TOP := 1.3
const CAN_W := 1.3
const FENCE_TOP := 3.2
const LINE_Y: Array[float] = [5.2, 7.3, 9.4]  ## a jump (2.2 m) reaches the next line up
const LINE_SPEED: Array[float] = [1.2, -1.6, 2.0]
const WINDOW_X: Array[float] = [4.0, 9.0, 14.0, 19.0]
const WINDOW_Y: Array[float] = [6.3, 8.4, 10.5]  ## bottom of each row of window openings (reached from the line below)
const WINDOW_SIZE := Vector2(1.6, 1.5)
const MAX_OPEN := 4
const DOG_SPEED := 2.4
const DOG_CHASE := 4.6  ## a little slower than the cat at first; +8 % per level
const DOG_ALERT := 0.45  ## the dog barks and braces before it runs
const DOG_SIGHT := 8.0
const SHOE_EVERY := Vector2(2.5, 5.0)
const SHOE_FLIGHT := 1.0
const SHOE_GRAVITY := 15.0
const STUN := 0.7
const SCORE_ENTER := 50
const SCORE_ROOM := 500
const SCORE_SERENADE := 2000
const ROOMS_PER_SERENADE := 3

var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_left := READY_SECONDS
var time := 0.0
var score := 0
var lives := LIVES
var level := 1
var rooms_won := 0
var serenades := 0
var cat := PlatformBody.new()
var facing := 1
var stunned := 0.0
var input_x := 0  ## -1, 0, 1: set by the game every tick
var input_y := 0  ## -1 down, 1 up
var windows: Array[Dictionary] = []  ## {col, row, rect: Rect2, open: bool, t: float, room: RoomKind}
var dog := {"x": 18.0, "dir": -1, "chasing": false, "alert": 0.0}
var shoes: Array[Dictionary] = []  ## {pos, vel, spin}
var room: WhiskerRoom = null
var room_window := -1
var _jump := false
var _shoe_in := 4.0
var _alley_platforms: Array = []


func _init(seed: int = 1) -> void:
	rng.seed = seed
	cat.gravity = 30.0
	_build_alley()
	_respawn()
	_set_phase(Phase.READY, READY_SECONDS)


func _build_alley() -> void:
	_alley_platforms.clear()
	_alley_platforms.append({"rect": Rect2(0, -1, W, 1), "solid": true, "kind": "ground"})
	for x in CAN_X:
		_alley_platforms.append({"rect": Rect2(x - CAN_W * 0.5, 0, CAN_W, CAN_TOP), "kind": "can", "x": x})
	_alley_platforms.append({"rect": Rect2(0, 0, W, FENCE_TOP), "kind": "fence"})
	for i in LINE_Y.size():
		_alley_platforms.append({"rect": Rect2(0, LINE_Y[i] - 0.05, W, 0.05), "kind": "line", "line": i,
			"vel": Vector2(LINE_SPEED[i], 0)})
	windows.clear()
	var kinds := [RoomKind.FISHBOWL, RoomKind.MICE, RoomKind.BIRDCAGE, RoomKind.DOGBOWLS]
	var i := 0
	for row in WINDOW_Y.size():
		for col in WINDOW_X.size():
			var r := Rect2(WINDOW_X[col] - WINDOW_SIZE.x * 0.5, WINDOW_Y[row], WINDOW_SIZE.x, WINDOW_SIZE.y)
			windows.append({"col": col, "row": row, "rect": r, "open": false, "t": rng.randf_range(0.5, 6.0),
				"room": kinds[(i * 7 + row) % kinds.size()]})
			i += 1


func _respawn() -> void:
	cat.pos = Vector2(1.5, 0)
	cat.vel = Vector2.ZERO
	cat.on_ground = true
	facing = 1
	stunned = 0.0
	shoes.clear()
	dog = {"x": 18.0, "dir": -1, "chasing": false, "alert": 0.0}


func _set_phase(p: Phase, secs: float) -> void:
	phase = p
	phase_left = secs
	event.emit("phase", {"phase": p})


func jump() -> void:
	_jump = true


func platforms() -> Array:
	return room.platforms if room else _alley_platforms


func bounds() -> Rect2:
	return room.bounds if room else Rect2(0, 0, W, H)


func open_windows() -> int:
	var n := 0
	for w in windows:
		if w["open"]:
			n += 1
	return n


# ------------------------------------------------------------------ tick

func tick() -> void:
	time += TICK
	var jump_now := _jump
	_jump = false
	match phase:
		Phase.READY:
			phase_left -= TICK
			if phase_left <= 0.0:
				_set_phase(Phase.ALLEY, 0.0)
		Phase.DYING:
			phase_left -= TICK
			_tick_windows(TICK)
			if phase_left <= 0.0:
				if lives <= 0:
					_set_phase(Phase.GAME_OVER, 0.0)
					event.emit("game_over", {"score": score})
				else:
					if room:
						_leave_room(false)
					_respawn()
					_set_phase(Phase.READY, READY_SECONDS)
		Phase.ALLEY:
			_control(TICK, jump_now)
			_tick_windows(TICK)
			_tick_dog(TICK)
			_tick_shoes(TICK)
			_try_windows()
		Phase.ROOM:
			if room.swimming(self):
				room.swim(self, TICK, jump_now)
			else:
				_control(TICK, jump_now)
				room.resolve_walls(self)
			room.tick(self, TICK)
			if room.status != 0:
				_leave_room(room.status > 0)


func _control(dt: float, jump_now: bool) -> void:
	stunned = maxf(0.0, stunned - dt)
	var dir := input_x if stunned <= 0.0 else 0
	if dir != 0:
		facing = dir
	var was_ground := cat.on_ground
	if cat.on_ground:
		cat.vel.x = dir * WALK
		if jump_now and stunned <= 0.0:
			var g: Dictionary = cat.ground
			if input_y < 0 and not g.is_empty() and not g.get("solid", false):
				cat.drop_until = time + 0.25  # down + jump: drop through the platform
				event.emit("drop", {})
			elif g.get("kind", "") == "can":
				cat.vel.y = BOUNCE
				event.emit("bounce", {"x": g["x"]})
			else:
				cat.vel.y = JUMP
				event.emit("jump", {"pos": cat.pos})
	else:
		cat.vel.x = move_toward(cat.vel.x, dir * AIR_CONTROL, 30.0 * dt)
	cat.step(dt, platforms(), bounds(), time)
	if cat.on_ground and not was_ground:
		event.emit("land", {"pos": cat.pos, "kind": cat.ground.get("kind", "")})


func _tick_windows(dt: float) -> void:
	for i in windows.size():
		var w := windows[i]
		w["t"] -= dt
		if w["t"] > 0.0:
			continue
		if w["open"]:
			w["open"] = false
			w["t"] = rng.randf_range(2.0, 8.0)
			event.emit("window_close", {"i": i})
		elif open_windows() < MAX_OPEN:
			w["open"] = true
			w["t"] = rng.randf_range(3.0, 6.5) / (1.0 + 0.1 * (level - 1))
			event.emit("window_open", {"i": i})
		else:
			w["t"] = rng.randf_range(0.5, 2.0)


func _tick_dog(dt: float) -> void:
	var on_street := cat.pos.y < 0.05
	var dx: float = cat.pos.x - dog["x"]
	var chasing: bool = on_street and absf(dx) < DOG_SIGHT
	if chasing and not dog["chasing"]:
		event.emit("dog_bark", {"x": dog["x"]})
		dog["alert"] = DOG_ALERT
	dog["chasing"] = chasing
	dog["alert"] = maxf(0.0, dog["alert"] - dt)
	if chasing and dog["alert"] > 0.0:
		dog["dir"] = 1 if dx > 0.0 else -1  # turns to face the cat, barking
	elif chasing:
		dog["dir"] = 1 if dx > 0.0 else -1
		dog["x"] += dog["dir"] * DOG_CHASE * (1.0 + 0.08 * (level - 1)) * dt
	else:
		dog["x"] += dog["dir"] * DOG_SPEED * dt
		if dog["x"] < 1.0 or dog["x"] > W - 1.0:
			dog["dir"] = -dog["dir"]
	dog["x"] = clampf(dog["x"], 0.8, W - 0.8)
	if on_street and absf(cat.pos.x - dog["x"]) < 0.9:
		_die("dog")


func _tick_shoes(dt: float) -> void:
	_shoe_in -= dt
	if _shoe_in <= 0.0:
		_shoe_in = rng.randf_range(SHOE_EVERY.x, SHOE_EVERY.y) / (1.0 + 0.12 * (level - 1))
		var open: Array[int] = []
		for i in windows.size():
			if windows[i]["open"]:
				open.append(i)
		if not open.is_empty():
			var w := windows[open[rng.randi_range(0, open.size() - 1)]]
			var from: Vector2 = w["rect"].get_center()
			var target := cat.pos + Vector2(cat.vel.x * SHOE_FLIGHT * 0.5, 0.3)
			var vel := Vector2((target.x - from.x) / SHOE_FLIGHT, (target.y - from.y) / SHOE_FLIGHT + 0.5 * SHOE_GRAVITY * SHOE_FLIGHT)
			shoes.append({"pos": from, "vel": vel, "spin": rng.randf_range(-12.0, 12.0)})
			event.emit("shoe", {"from": from})
	var i := 0
	while i < shoes.size():
		var s := shoes[i]
		s["vel"].y -= SHOE_GRAVITY * dt
		s["pos"] += s["vel"] * dt
		if s["pos"].distance_to(cat.pos + Vector2(0, 0.3)) < 0.55 and stunned <= 0.0:
			stunned = STUN
			cat.vel = Vector2(signf(s["vel"].x) * 3.0, minf(cat.vel.y, 0.0) - 2.0)
			cat.on_ground = false
			cat.drop_until = time + 0.4  # knocked off whatever it stood on
			event.emit("shoe_hit", {"pos": s["pos"]})
			shoes.remove_at(i)
			continue
		if s["pos"].y < -1.0:
			event.emit("shoe_land", {"pos": s["pos"]})
			shoes.remove_at(i)
			continue
		i += 1


func _try_windows() -> void:
	var c := cat.rect().get_center()
	for i in windows.size():
		var w := windows[i]
		if w["open"] and (w["rect"] as Rect2).grow(0.1).has_point(c):
			_enter_room(i)
			return


# ------------------------------------------------------------------ rooms

func _enter_room(i: int, serenade := false) -> void:
	room_window = i
	var kind: RoomKind = RoomKind.HEARTS if serenade else windows[i]["room"]
	match kind:
		RoomKind.FISHBOWL: room = FishbowlRoom.new()
		RoomKind.MICE: room = MiceRoom.new()
		RoomKind.DOGBOWLS: room = DogbowlsRoom.new()
		RoomKind.HEARTS: room = HeartsRoom.new()
		_: room = BirdcageRoom.new()
	room.kind = kind
	room.setup(self)
	cat.pos = room.entry
	cat.vel = Vector2.ZERO
	stunned = 0.0
	shoes.clear()
	if not serenade:
		score += SCORE_ENTER
	_set_phase(Phase.ROOM, 0.0)
	event.emit("enter_room", {"window": i, "kind": kind})


func _leave_room(won: bool) -> void:
	var w := windows[room_window]
	var was := room.kind
	room.cleanup(self)
	if won and was == RoomKind.HEARTS:
		serenades += 1
		level = 1 + serenades
		var bonus := SCORE_SERENADE + int(room.time_left * 20.0)
		score += bonus
		event.emit("room_won", {"kind": was, "bonus": bonus})
	elif won:
		rooms_won += 1
		var bonus := SCORE_ROOM + int(room.time_left * 10.0)
		score += bonus
		event.emit("room_won", {"kind": was, "bonus": bonus})
	else:
		event.emit("room_failed", {"kind": was})
	room = null
	if won and was != RoomKind.HEARTS and rooms_won % ROOMS_PER_SERENADE == 0 and phase == Phase.ROOM:
		event.emit("leave_room", {"window": room_window, "won": true})
		_enter_room(room_window, true)  # straight on to the serenade
		return
	w["open"] = false
	w["t"] = rng.randf_range(3.0, 6.0)
	cat.pos = Vector2((w["rect"] as Rect2).get_center().x, (w["rect"] as Rect2).position.y)
	cat.vel = Vector2(0, 2.0)
	cat.drop_until = time + 0.3
	if phase == Phase.ROOM:
		_set_phase(Phase.ALLEY, 0.0)
	event.emit("leave_room", {"window": room_window, "won": won})


## Captures and tests: go straight into a room of this kind (the serenade for HEARTS).
func enter_room_kind(kind: RoomKind) -> void:
	for i in windows.size():
		if kind == RoomKind.HEARTS or windows[i]["room"] == kind:
			_enter_room(i, kind == RoomKind.HEARTS)
			return


func die(why: String) -> void:
	_die(why)


func _die(why: String) -> void:
	if phase != Phase.ALLEY and phase != Phase.ROOM:
		return
	lives -= 1
	event.emit("death", {"pos": cat.pos, "why": why, "lives": lives})
	_set_phase(Phase.DYING, DYING_SECONDS)
