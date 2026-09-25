class_name WhiskerRoom
extends RefCounted
## A room behind one of the alley's windows: its own floor and furniture (platforms), a challenge and a time
## limit. When the time runs out the broom sweeps the cat back out (no life lost, no bonus).
## Subclasses fill `platforms`, `entry` and their own things in setup(), and play in tick().

const ROOM_SECONDS := 30.0

var kind := 0
var bounds := Rect2(0, 0, 16, 9)
var platforms: Array = []
var walls: Array[Rect2] = []  ## solid boxes the cat can't walk through (it is pushed out sideways)
var entry := Vector2(1.5, 5.0)
var time_left := ROOM_SECONDS
var status := 0  ## 0 playing, 1 won, -1 swept out
var goal := 1  ## things to catch
var caught := 0


func setup(_e: WhiskerEngine) -> void:
	platforms = [{"rect": Rect2(-1, -1, bounds.size.x + 2, 1), "solid": true, "kind": "floor"}]


func tick(e: WhiskerEngine, dt: float) -> void:
	time_left -= dt
	if time_left <= 0.0 and status == 0:
		status = -1
		e.event.emit("broom", {})


## Called when the cat leaves the room.
func cleanup(_e: WhiskerEngine) -> void:
	pass


## Rooms with water override these (the fishbowl).
func swimming(_e: WhiskerEngine) -> bool:
	return false


func swim(_e: WhiskerEngine, _dt: float, _jump: bool) -> void:
	pass


## Pushes the cat out of the walls sideways (called after each step, not while swimming).
func resolve_walls(e: WhiskerEngine) -> void:
	for w in walls:
		if not wall_blocks(e, w):
			continue
		var r := e.cat.rect()
		if r.intersects(w):
			var left := r.end.x - w.position.x
			var right := w.end.x - r.position.x
			e.cat.pos.x += -left if left < right else right
			e.cat.vel.x = 0.0


## Rooms can let the cat through a wall (the fishbowl lets it in over the rim).
func wall_blocks(_e: WhiskerEngine, _w: Rect2) -> bool:
	return true


func add(rect: Rect2, what: String) -> void:
	platforms.append({"rect": rect, "kind": what})


func catch_one(e: WhiskerEngine, what: String, pos: Vector2, points: int) -> void:
	caught += 1
	e.score += points
	e.event.emit("catch", {"what": what, "pos": pos, "points": points, "left": goal - caught})
	if caught >= goal and status == 0:
		status = 1
