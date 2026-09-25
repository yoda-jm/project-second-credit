class_name WhiskerBot
extends RefCounted
## Demo autopilot for Whisker Alley: picks an open window, climbs to the clothesline below it (can, fence, lines),
## lines up and jumps in; in the rooms it goes for the fish, the mice or the cage and the bird.

const E = preload("res://games/whisker/engine/whisker_engine.gd")

var _target := -1
var _cool := 0
var _air_x := NAN  ## in the air: where the last jump meant to land (NAN: free)


func drive(e: WhiskerEngine) -> void:
	e.input_x = 0
	e.input_y = 0
	_cool -= 1
	match e.phase:
		E.Phase.ALLEY: _alley(e)
		E.Phase.ROOM:
			match e.room.kind:
				E.RoomKind.FISHBOWL: _fishbowl(e, e.room as FishbowlRoom)
				E.RoomKind.MICE: _mice(e, e.room as MiceRoom)
				E.RoomKind.DOGBOWLS: _dogbowls(e, e.room as DogbowlsRoom)
				E.RoomKind.HEARTS: _hearts(e, e.room as HeartsRoom)
				_: _birdcage(e, e.room as BirdcageRoom)


func _jump(e: WhiskerEngine, land_x := NAN) -> void:
	if _cool <= 0 and e.cat.on_ground:
		e.jump()
		_cool = 12
		_air_x = land_x


## In the air: steer toward the planned landing spot. Returns false when there is none.
func _steer(e: WhiskerEngine) -> bool:
	if e.cat.on_ground or is_nan(_air_x):
		return false
	_toward(e, _air_x, 0.1)
	return true


func _toward(e: WhiskerEngine, x: float, dead := 0.2) -> float:
	var dx := x - e.cat.pos.x
	if absf(dx) > dead:
		e.input_x = 1 if dx > 0.0 else -1
	return absf(dx)


# ------------------------------------------------------------------ alley

## 0 ground, 1 can, 2 fence, 3 + k clothesline k
func _tier(e: WhiskerEngine) -> int:
	if not e.cat.on_ground:
		return -1
	var g: Dictionary = e.cat.ground
	match g.get("kind", "ground"):
		"can": return 1
		"fence": return 2
		"line": return 3 + int(g["line"])
	return 0


func _alley(e: WhiskerEngine) -> void:
	if _target < 0 or not e.windows[_target]["open"]:
		_target = _pick_window(e)
	var tier := _tier(e)
	if tier < 0:  # in the air: to the planned landing, else toward the target window
		if _steer(e):
			return
		if _target >= 0:
			_toward(e, (e.windows[_target]["rect"] as Rect2).get_center().x, 0.3)
		return
	if tier == 0:  # the street: the dog is here, get onto the nearest can
		var best: float = E.CAN_X[0]
		var best_cost := INF
		for x in E.CAN_X:  # the nearest can that is not past the dog
			var cost := absf(x - e.cat.pos.x)
			if signf(x - e.cat.pos.x) == signf(e.dog["x"] - e.cat.pos.x) and absf(e.dog["x"] - e.cat.pos.x) < absf(x - e.cat.pos.x) + 1.5:
				cost += 100.0
			if cost < best_cost:
				best_cost = cost
				best = x
		if _toward(e, best, 0.25) < 0.5:
			_jump(e, best)
		return
	if tier == 1 or tier == 2:
		_jump(e)
		return
	if _target < 0:
		return
	var w := e.windows[_target]
	var line := tier - 3
	var row: int = w["row"]
	var cx := (w["rect"] as Rect2).get_center().x
	if line < row:
		_jump(e)  # climb to the next line
	elif line > row:
		e.input_y = -1  # drop down one line
		_jump(e)
	else:
		# the line moves: aim a little ahead of the drift
		var drift := E.LINE_SPEED[line] * 0.25
		if _toward(e, cx - drift, 0.3) < 0.45:
			_jump(e)


func _pick_window(e: WhiskerEngine) -> int:
	var best := -1
	var best_score := INF
	for i in e.windows.size():
		var w := e.windows[i]
		if not w["open"] or w["t"] < 1.5:
			continue
		var s: float = w["row"] * 4.0 + absf((w["rect"] as Rect2).get_center().x - e.cat.pos.x) * 0.3
		if s < best_score:
			best_score = s
			best = i
	return best


# ------------------------------------------------------------------ rooms

func _fishbowl(e: WhiskerEngine, r: FishbowlRoom) -> void:
	if r.swimming(e):
		var c := e.cat.rect().get_center()
		if r.air < 2.0 or r.fish.is_empty():
			e.input_y = 1
			return
		var target: Vector2 = r.fish[0]["pos"]
		for f in r.fish:
			if (f["pos"] as Vector2).distance_to(c) < target.distance_to(c):
				target = f["pos"]
		for eel in r.eels:
			if (eel["pos"] as Vector2).distance_to(c) < 1.6:  # keep away from the eel
				target = c + (c - (eel["pos"] as Vector2)).normalized() * 2.0
		_toward(e, target.x, 0.15)
		if target.y > c.y + 0.2:
			e.input_y = 1
		elif target.y < c.y - 0.2:
			e.input_y = -1
		return
	# out of the water: chair, cabinet, then a leap right into the bowl
	if _steer(e):
		return
	match e.cat.ground.get("kind", "") if e.cat.on_ground else "air":
		"chair": _jump(e, 2.8)
		"cabinet":
			if _toward(e, 3.2, 0.15) < 0.2:
				_jump(e, FishbowlRoom.BOWL.get_center().x)
		"air": pass
		_:
			if _toward(e, 1.0, 0.15) < 0.2:
				_jump(e, 1.0)


func _mice(e: WhiskerEngine, r: MiceRoom) -> void:
	if r.mice.is_empty():
		_toward(e, 8.0, 0.5)
		return
	var best: Dictionary = r.mice[0]
	for m in r.mice:
		if absf(r.mouse_pos(m).x - e.cat.pos.x) + absf(r.mouse_pos(m).y - e.cat.pos.y) * 2.0 < \
				absf(r.mouse_pos(best).x - e.cat.pos.x) + absf(r.mouse_pos(best).y - e.cat.pos.y) * 2.0:
			best = m
	var p := r.mouse_pos(best)
	# meet the mouse where it will be
	_toward(e, p.x + best["dir"] * 0.6, 0.1)
	if p.y > e.cat.pos.y + 0.5 and absf(p.x - e.cat.pos.x) < 2.5:
		_jump(e)
	elif p.y < e.cat.pos.y - 0.5:
		e.input_y = -1
		_jump(e)


func _birdcage(e: WhiskerEngine, r: BirdcageRoom) -> void:
	if not r.cage_down:
		# chair, dresser, then a leap left into the cage
		if _steer(e):
			return
		match e.cat.ground.get("kind", "") if e.cat.on_ground else "air":
			"chair": _jump(e, 15.0)
			"dresser":
				if _toward(e, 14.7, 0.15) < 0.2:
					_jump(e, BirdcageRoom.CAGE.get_center().x)
			"air": pass
			_:
				if _toward(e, 13.5, 0.15) < 0.2:
					_jump(e, 13.5)
		return
	var b: Vector2 = r.bird["pos"]
	_toward(e, b.x, 0.2)
	if b.y > e.cat.pos.y + 0.8 and absf(b.x - e.cat.pos.x) < 1.5:
		_jump(e)


func _dogbowls(e: WhiskerEngine, r: DogbowlsRoom) -> void:
	# never jump near the dogs: walk along the floor from bowl to bowl and stand still to drink
	if not e.cat.on_ground:
		return
	for i in r.bowls.size():
		if r.bowls[i] > 0.0:
			var awake := false
			for dog in r.dogs:
				if dog["awake"] > 0.0 and absf(dog["x"] - e.cat.pos.x) < 3.0:
					awake = true
			if awake:  # a dog is up: wait on the cabinet, far from it
				if _toward(e, 1.0, 0.2) < 0.3 and e.cat.pos.y < 0.1:
					_jump(e, 1.0)
				return
			if e.cat.pos.y > 0.1:  # down from furniture, away from the dogs
				e.input_x = 1 if e.cat.pos.x < DogbowlsRoom.BOWL_X[i] else -1
				return
			_toward(e, DogbowlsRoom.BOWL_X[i], 0.12)
			return


func _hearts(e: WhiskerEngine, r: HeartsRoom) -> void:
	if _steer(e):
		return
	if not e.cat.on_ground:
		return
	if e.cat.pos.y > HeartsRoom.TOP_Y - 0.6:
		_toward(e, r.lady.x, 0.1)
		return
	# the next heart up: wait until it drifts close, then jump for where it will be
	var best: Dictionary = {}
	for h in r.hearts:
		var top: float = (h["rect"] as Rect2).end.y
		if top > e.cat.pos.y + 0.5 and top < e.cat.pos.y + 2.3 and (best.is_empty() or top < (best["rect"] as Rect2).end.y):
			best = h
	if best.is_empty():
		_toward(e, r.lady.x, 0.3)  # the last hop: the lady's ledge
		if absf(e.cat.pos.x - r.lady.x) < 1.2:
			_jump(e, r.lady.x)
		return
	var rect: Rect2 = best["rect"]
	var lead: float = rect.get_center().x + best["vel"].x * 0.45
	if absf(lead - e.cat.pos.x) < 2.2:
		_jump(e, lead)
	else:
		# ride the current heart: walk toward the next one, but never off our own platform
		var here: Rect2 = e.cat.ground.get("rect", Rect2(-100, 0, 300, 1))
		_toward(e, clampf(lead, here.position.x + 0.4, here.end.x - 0.4), 0.2)
