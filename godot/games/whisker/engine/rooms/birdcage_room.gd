class_name BirdcageRoom
extends WhiskerRoom
## The bird cage: jump up and knock the hanging cage down; the door springs open and the bird flutters around the
## room. Catch it.

const CAGE := Rect2(11.2, 4.4, 1.4, 1.6)
const BIRD_SPEED := 3.2

var cage_down := false
var cage_y := CAGE.position.y  ## falls when knocked
var bird := {"pos": CAGE.get_center(), "t": 0.0, "free": false, "vel": Vector2.ZERO, "target": CAGE.get_center(),
	"perch": 0.0, "retarget": 0.0}


func setup(e: WhiskerEngine) -> void:
	super.setup(e)
	add(Rect2(2.5, 0, 2.6, 1.5), "table")
	add(Rect2(6.4, 0, 1.4, 3.0), "bookcase")
	add(Rect2(8.6, 2.9, 2.0, 0.25), "shelf")
	add(Rect2(13.0, 0, 1.0, 1.2), "chair")      # chair, dresser, then a leap at the cage
	add(Rect2(14.2, 0, 1.6, 2.4), "dresser")
	entry = Vector2(1.0, 6.0)
	goal = 1
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
		_fly(e, dt)
		if c.grow(0.2).has_point(bird["pos"]) and status == 0:
			catch_one(e, "bird", bird["pos"], 400)
	else:
		bird["pos"] = Vector2(CAGE.get_center().x, cage_y + CAGE.size.y * 0.4)


## The bird's flight: it darts from one random spot to the next, now and then lands on a piece of furniture for a
## breather, and bolts away when the cat comes close. Never the same route twice.
func _fly(e: WhiskerEngine, dt: float) -> void:
	var p: Vector2 = bird["pos"]
	var cat := e.cat.rect().get_center()
	var near := p.distance_to(cat) < 2.4
	bird["t"] += dt
	var pace := 1.0 + 0.1 * (e.level - 1)
	if bird["perch"] > 0.0:
		bird["perch"] -= dt
		if near:
			bird["perch"] = 0.0  # startled off its perch
			bird["retarget"] = 0.0
		else:
			return
	bird["retarget"] -= dt
	if near or bird["retarget"] <= 0.0 or p.distance_to(bird["target"]) < 0.3:
		var t: Vector2
		if near:
			# bolt away from the cat, with a jink up or down
			var away := (p - cat).normalized()
			t = p + away.rotated(e.rng.randf_range(-0.7, 0.7)) * e.rng.randf_range(3.0, 5.0)
			bird["retarget"] = e.rng.randf_range(0.4, 0.8)
		elif e.rng.randf() < 0.3:
			# a breather on top of a piece of furniture
			var tops := platforms.filter(func(pl): return pl["kind"] in ["table", "bookcase", "shelf", "chair", "dresser"])
			var pick: Rect2 = tops[e.rng.randi_range(0, tops.size() - 1)]["rect"]
			t = Vector2(pick.position.x + e.rng.randf_range(0.2, pick.size.x - 0.2), pick.end.y + 0.15)
			bird["retarget"] = 3.0
			bird["landing"] = true
		else:
			t = Vector2(e.rng.randf_range(1.0, 15.0), e.rng.randf_range(2.4, 7.2))
			bird["retarget"] = e.rng.randf_range(0.8, 2.0)
			bird["landing"] = false
		t.x = clampf(t.x, bounds.position.x + 0.6, bounds.end.x - 0.6)
		t.y = clampf(t.y, 0.3, bounds.end.y - 0.8)
		bird["target"] = t
	var to: Vector2 = bird["target"] - p
	var speed := BIRD_SPEED * (2.4 if near else 1.6) * pace
	var desired := to.normalized() * minf(speed, to.length() * 4.0)
	bird["vel"] = (bird["vel"] as Vector2).lerp(desired, minf(1.0, dt * 4.0))
	# a flutter on top of the flight
	p += (bird["vel"] + Vector2(0, sin(bird["t"] * 17.0) * 0.8)) * dt
	bird["pos"] = p
	if bird.get("landing", false) and to.length() < 0.15:
		bird["perch"] = e.rng.randf_range(0.6, 1.6)
		bird["landing"] = false
		bird["vel"] = Vector2.ZERO
