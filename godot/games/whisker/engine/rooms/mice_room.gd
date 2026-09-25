class_name MiceRoom
extends WhiskerRoom
## The cheese: a giant wedge with holes at the ends of its tiers. Mice pop out of one hole and dash along the tier
## to the other; catch five.

const TIERS: Array[float] = [0.0, 2.0, 4.0]  ## heights of the cheese tiers (0 is the floor)
const CHEESE_X := Vector2(3.5, 12.5)  ## the holes at both ends of each tier
const MOUSE_SPEED := 3.6

var mice: Array[Dictionary] = []  ## {x, tier, dir, id}
var _next_in := 1.0
var _id := 0


func setup(e: WhiskerEngine) -> void:
	super.setup(e)
	for k in range(1, TIERS.size()):
		var inset := k * 1.2
		add(Rect2(CHEESE_X.x + inset, 0, CHEESE_X.y - CHEESE_X.x - inset * 2.0, TIERS[k]), "cheese")
	add(Rect2(0.3, 0, 1.6, 1.4), "stool")
	add(Rect2(14.2, 0, 1.5, 2.8), "shelf")
	entry = Vector2(1.0, 6.0)
	goal = 5


func tick(e: WhiskerEngine, dt: float) -> void:
	super.tick(e, dt)
	_next_in -= dt
	if _next_in <= 0.0 and mice.size() < 3:
		_next_in = e.rng.randf_range(0.8, 2.0) / (1.0 + 0.1 * (e.level - 1))
		var tier := e.rng.randi_range(0, TIERS.size() - 1)
		var inset := tier * 1.2
		var dir := 1 if e.rng.randf() < 0.5 else -1
		_id += 1
		mice.append({"x": (CHEESE_X.x + inset) if dir > 0 else (CHEESE_X.y - inset), "tier": tier, "dir": dir, "id": _id})
		e.event.emit("squeak", {"tier": tier})
	var c := e.cat.rect()
	var i := 0
	while i < mice.size():
		var m := mice[i]
		var inset: float = m["tier"] * 1.2
		m["x"] += m["dir"] * MOUSE_SPEED * (1.0 + 0.1 * (e.level - 1)) * dt
		var pos := Vector2(m["x"], TIERS[m["tier"]])
		if c.grow(0.15).has_point(pos + Vector2(0, 0.15)):
			mice.remove_at(i)
			catch_one(e, "mouse", pos, 100)
			continue
		if m["x"] < CHEESE_X.x + inset - 0.01 or m["x"] > CHEESE_X.y - inset + 0.01:
			mice.remove_at(i)  # safely into the other hole
			continue
		i += 1


func mouse_pos(m: Dictionary) -> Vector2:
	return Vector2(m["x"], TIERS[m["tier"]])
