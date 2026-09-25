class_name DogbowlsRoom
extends WhiskerRoom
## The dogs' dinner: three bowls of milk, each next to a sleeping bulldog. Stand still at a bowl to drink it.
## A landing close to a dog wakes it; an awake dog chases the cat for a few seconds before dozing off again.

const BOWL_X: Array[float] = [3.5, 8.0, 12.5]
const DOG_OFFSET := 1.4  ## each dog sleeps this far right of its bowl
const DRINK_SECONDS := 1.2
const WAKE_RADIUS := 2.5
const AWAKE_SECONDS := 3.5
const DOG_SPEED := 3.8

var bowls: Array[float] = []  ## milk left in each bowl, 1 full .. 0 empty
var dogs: Array[Dictionary] = []  ## {x, home, awake: float (seconds left), dir}


func setup(e: WhiskerEngine) -> void:
	super.setup(e)
	add(Rect2(0.2, 0, 1.2, 2.0), "cabinet")
	add(Rect2(14.3, 0, 1.4, 1.4), "stool")
	add(Rect2(5.3, 3.4, 2.2, 0.25), "shelf")
	add(Rect2(9.9, 3.4, 2.2, 0.25), "shelf")
	entry = Vector2(1.0, 6.0)
	goal = BOWL_X.size()
	for x in BOWL_X:
		bowls.append(1.0)
		dogs.append({"x": x + DOG_OFFSET, "home": x + DOG_OFFSET, "awake": 0.0, "dir": -1})
	e.event.connect(_on_engine_event.bind(e))


func cleanup(e: WhiskerEngine) -> void:
	if e.event.is_connected(_on_engine_event):
		e.event.disconnect(_on_engine_event)


func _on_engine_event(kind: String, d: Dictionary, e: WhiskerEngine) -> void:
	if kind != "land" or e.room != self:
		return
	for dog in dogs:
		if absf(dog["x"] - d["pos"].x) < WAKE_RADIUS and dog["awake"] <= 0.0:
			dog["awake"] = AWAKE_SECONDS
			e.event.emit("dog_bark", {"x": dog["x"]})


func tick(e: WhiskerEngine, dt: float) -> void:
	super.tick(e, dt)
	var c := e.cat
	for dog in dogs:
		if dog["awake"] > 0.0:
			dog["awake"] -= dt
			var dx: float = c.pos.x - dog["x"]
			dog["dir"] = 1 if dx > 0.0 else -1
			if c.pos.y < 0.3:
				dog["x"] += dog["dir"] * DOG_SPEED * dt
			if absf(dx) < 0.8 and c.pos.y < 0.8:
				e.die("dog")
				return
		else:  # back to its bowl and asleep
			dog["x"] = move_toward(dog["x"], dog["home"], DOG_SPEED * 0.5 * dt)
	for i in bowls.size():
		if bowls[i] <= 0.0:
			continue
		if c.on_ground and c.pos.y < 0.1 and absf(c.pos.x - BOWL_X[i]) < 0.6 and absf(c.vel.x) < 0.1:
			bowls[i] -= dt / DRINK_SECONDS
			if bowls[i] <= 0.0:
				bowls[i] = 0.0
				catch_one(e, "milk", Vector2(BOWL_X[i], 0.2), 150)


func drinking(e: WhiskerEngine) -> bool:
	for i in bowls.size():
		if bowls[i] > 0.0 and e.cat.on_ground and absf(e.cat.pos.x - BOWL_X[i]) < 0.6 and absf(e.cat.vel.x) < 0.1:
			return true
	return false
