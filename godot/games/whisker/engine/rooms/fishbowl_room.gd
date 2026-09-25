class_name FishbowlRoom
extends WhiskerRoom
## The fishbowl: climb the dresser, dive into the bowl and catch the fish before your air runs out. The eel's
## touch is a shock (a life lost).

const BOWL := Rect2(4.6, 1.0, 6.0, 4.2)  ## the water inside the glass
const AIR_SECONDS := 6.0
const SWIM := 3.6
const FISH_SPEED := 2.2

var fish: Array[Dictionary] = []  ## {pos, vel}
var eels: Array[Dictionary] = []  ## {pos, phase, dir}
var air := AIR_SECONDS
var _in_water := false


func setup(e: WhiskerEngine) -> void:
	super.setup(e)
	add(Rect2(4.0, 0, 7.2, 1.0), "table")       # the table under the bowl
	add(Rect2(0.3, 0, 1.4, 1.8), "chair")       # chair, then cabinet, then a leap into the bowl
	add(Rect2(2.0, 0, 1.6, 3.4), "cabinet")
	add(Rect2(13.0, 0, 2.4, 2.4), "dresser")
	walls.append(BOWL.grow_individual(0.1, 0, 0.1, 0))  # the glass
	entry = Vector2(1.0, 6.0)
	goal = 3 + (1 if e.rng.randf() < 0.4 else 0)
	for i in goal:
		fish.append({"pos": BOWL.position + Vector2(0.8 + i * 1.4 + e.rng.randf_range(-0.3, 0.3), 1.0 + (i % 2) * 1.6 + e.rng.randf_range(-0.3, 0.3)),
			"vel": Vector2(FISH_SPEED * (1 if i % 2 == 0 else -1), e.rng.randf_range(-0.6, 0.6))})
	for i in mini(1 + (e.level - 1) / 2, 2):
		eels.append({"pos": BOWL.position + Vector2(3.0, 0.8 + i * 2.2), "phase": e.rng.randf() * TAU, "dir": 1 if i == 0 else -1})


## The glass lets the cat in over the rim only.
func wall_blocks(e: WhiskerEngine, _w: Rect2) -> bool:
	return e.cat.pos.y < BOWL.end.y - 0.4


func swimming(e: WhiskerEngine) -> bool:
	var c := e.cat.rect().get_center()
	return BOWL.has_point(c) or (_in_water and BOWL.grow_individual(0, 0, 0, 0.3).has_point(c))


func swim(e: WhiskerEngine, dt: float, jump: bool) -> void:
	var cat := e.cat
	if not _in_water:
		_in_water = true
		e.event.emit("splash", {"pos": cat.pos})
	if e.input_x != 0:
		e.facing = e.input_x
	cat.vel.x = move_toward(cat.vel.x, e.input_x * SWIM, 12.0 * dt)
	var up := e.input_y
	if jump:
		up = 1
	cat.vel.y = move_toward(cat.vel.y, up * SWIM - 0.6, 10.0 * dt)
	cat.pos += cat.vel * dt
	cat.on_ground = false
	var surface := BOWL.end.y
	# the glass keeps the cat in, except over the top
	cat.pos.x = clampf(cat.pos.x, BOWL.position.x + cat.size.x * 0.5, BOWL.end.x - cat.size.x * 0.5)
	cat.pos.y = maxf(cat.pos.y, BOWL.position.y)
	if cat.pos.y + cat.size.y > surface + 0.2 and jump:  # leap out at the surface
		cat.vel.y = WhiskerEngine.JUMP
		cat.pos.y = surface
		_in_water = false
		e.event.emit("splash", {"pos": cat.pos})
		return
	cat.pos.y = minf(cat.pos.y, surface - cat.size.y * 0.3)


func tick(e: WhiskerEngine, dt: float) -> void:
	super.tick(e, dt)
	if not swimming(e):
		_in_water = false
	var head_under := _in_water and e.cat.pos.y + e.cat.size.y < BOWL.end.y - 0.05
	if head_under:
		air -= dt
		if air <= 0.0:
			e.die("air")
			return
	else:
		air = minf(AIR_SECONDS, air + dt * 3.0)
	var inner := BOWL.grow(-0.3)
	for f in fish:
		f["pos"] += f["vel"] * dt
		if f["pos"].x < inner.position.x or f["pos"].x > inner.end.x:
			f["vel"].x = -f["vel"].x
		if f["pos"].y < inner.position.y or f["pos"].y > inner.end.y - 0.3:
			f["vel"].y = -f["vel"].y
		f["pos"] = f["pos"].clamp(inner.position, inner.end)
		if e.rng.randf() < dt * 0.8:
			f["vel"] = f["vel"].rotated(e.rng.randf_range(-0.8, 0.8))
			f["vel"] = f["vel"].normalized() * FISH_SPEED * (1.0 + 0.1 * (e.level - 1))
	var c := e.cat.rect().get_center()
	var i := 0
	while i < fish.size():
		if _in_water and fish[i]["pos"].distance_to(c) < 0.55:
			var p: Vector2 = fish[i]["pos"]
			fish.remove_at(i)
			catch_one(e, "fish", p, 150)
			continue
		i += 1
	for eel in eels:
		eel["phase"] += dt * 1.3
		eel["pos"].x = BOWL.get_center().x + sin(eel["phase"]) * (BOWL.size.x * 0.4) * eel["dir"]
		eel["pos"].y = clampf(eel["pos"].y + sin(eel["phase"] * 2.3) * dt * 0.8, inner.position.y, inner.end.y - 0.4)
		if _in_water and eel["pos"].distance_to(c) < 0.6:
			e.event.emit("zap", {"pos": eel["pos"]})
			e.die("eel")
			return
