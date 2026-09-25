class_name BirdcageRoom
extends WhiskerRoom
## The bird cage: jump up and knock the hanging cage down; the door springs open and the bird flutters around the
## room. Catch it.

const CAGE := Rect2(11.2, 4.4, 1.4, 1.6)
const BIRD_SPEED := 3.2

var cage_down := false
var cage_y := CAGE.position.y  ## falls when knocked
var bird := {"pos": CAGE.get_center(), "t": 0.0, "free": false}
var _path := Vector4(0.9, 2.3, 1.4, 3.1)  ## the bird's flight pattern (varies from visit to visit)


func setup(e: WhiskerEngine) -> void:
	super.setup(e)
	add(Rect2(2.5, 0, 2.6, 1.5), "table")
	add(Rect2(6.4, 0, 1.4, 3.0), "bookcase")
	add(Rect2(8.6, 2.9, 2.0, 0.25), "shelf")
	add(Rect2(13.0, 0, 1.0, 1.2), "chair")      # chair, dresser, then a leap at the cage
	add(Rect2(14.2, 0, 1.6, 2.4), "dresser")
	entry = Vector2(1.0, 6.0)
	goal = 1
	_path = Vector4(e.rng.randf_range(0.7, 1.1), e.rng.randf_range(1.8, 2.8), e.rng.randf_range(1.1, 1.7), e.rng.randf_range(2.5, 3.5))
	bird["t"] = e.rng.randf_range(0.0, 10.0)


func tick(e: WhiskerEngine, dt: float) -> void:
	super.tick(e, dt)
	var c := e.cat.rect()
	if not cage_down and c.intersects(Rect2(CAGE.position.x, cage_y, CAGE.size.x, CAGE.size.y)):
		cage_down = true
		e.event.emit("cage_knocked", {"pos": CAGE.get_center()})
	if cage_down and cage_y > 0.0:
		cage_y = maxf(0.0, cage_y - dt * 9.0)
		if cage_y == 0.0:
			bird["free"] = true
			e.event.emit("cage_crash", {"pos": Vector2(CAGE.get_center().x, 0.3)})
	if bird["free"]:
		bird["t"] += dt * (1.0 + 0.1 * (e.level - 1))
		var t: float = bird["t"]
		var target := Vector2(8.0 + sin(t * _path.x) * 6.5 + sin(t * _path.y) * 0.8, 4.2 + sin(t * _path.z) * 2.8 + cos(t * _path.w) * 0.5)
		bird["pos"] = (bird["pos"] as Vector2).move_toward(target, BIRD_SPEED * 2.0 * dt)
		if c.grow(0.2).has_point(bird["pos"]) and status == 0:
			catch_one(e, "bird", bird["pos"], 400)
	else:
		bird["pos"] = Vector2(CAGE.get_center().x, cage_y + CAGE.size.y * 0.4)
