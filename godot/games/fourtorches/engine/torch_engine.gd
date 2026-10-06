class_name TorchEngine
extends RefCounted
## Four Torches rules (a co-op dungeon crawl in the Gauntlet tradition; our own tuning), 60 Hz ticks. A dungeon of
## tiles (x right, y down: walls, floor, doors, exits, walls that crumble when shot): the first levels are our own mazes
## (`levels/crypts.torch`), the deeper ones generated (rooms joined by corridors, side rooms behind doors, generators).
## Monsters and generators have a rank, 1 to 3, as in the classic: each hit takes a rank off, and a generator knocked
## down a rank makes weaker monsters, and slower. They come in hordes. Shots also smash food and set off potions. One to four heroes (knight, shieldmaiden, mage,
## ranger: different speed, armour, missile and magic), each moving in eight directions and throwing one missile at a
## time; walking into monsters fights them hand to hand. Health drains slowly all the time; food mends it; touches and
## shots hurt (armour softens). Generators keep making monsters while heroes are near: ghosts (they hurt and vanish),
## grunts, imps throwing fire, skeleton archers, sorcerers who blink out, and the deathshade, who drains a lot and
## shrugs off missiles (a potion is the answer). A potion blasts every monster round the hero. Keys open doors.
## Treasure scores. Any hero on the exit takes everyone down to the next level. The heroes stay together on one screen.
## Events: "shoot" {h}, "melee" {h}, "hit" {pos, kind}, "kill" {pos, kind, points}, "gen_hit" {pos, state}, "gen_break"
## {pos}, "hurt" {h, damage}, "die" {h}, "food" {h}, "key" {h}, "door" {cells}, "treasure" {h, points}, "potion"
## {h} (picked up), "blast" {h, pos}, "exit" {h, jump}, "food_shot" {h, pos}, "potion_shot" {h, pos}, "crumble" {cell}, "rejoin" {h, pos}, "low" {h}, "spawn" {pos, kind}, "monster_shot" {pos, kind}.

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, EXIT, OVER }
const TICK := 1.0 / 60.0
const W := 44
const H := 30
const R := 0.34
const VIEW := Vector2(8.0, 4.6)          ## the screen's half-size in tiles round anchor() (every hero stays on it)
const STRAY := 2.0                       ## seconds a CPU companion may spend off the screen before it rejoins
const CLASSES := {
	"knight": {"speed": 3.1, "armor": 0.45, "shot": 2.0, "shot_speed": 9.0, "melee": 3.0, "magic": 1.0, "name": "KNIGHT"},
	"shieldmaiden": {"speed": 3.5, "armor": 0.35, "shot": 1.6, "shot_speed": 10.5, "melee": 2.0, "magic": 1.4, "name": "SHIELDMAIDEN"},
	"mage": {"speed": 3.3, "armor": 0.1, "shot": 2.2, "shot_speed": 10.0, "melee": 1.0, "magic": 2.5, "name": "MAGE"},
	"ranger": {"speed": 4.1, "armor": 0.2, "shot": 1.3, "shot_speed": 13.5, "melee": 1.3, "magic": 1.6, "name": "RANGER"},
}
const ORDER := ["knight", "shieldmaiden", "mage", "ranger"]
const MONSTER := {
	"ghost": {"hp": 1.0, "speed": 2.4, "touch": 18.0, "points": 10},
	"grunt": {"hp": 3.0, "speed": 2.0, "touch": 9.0, "points": 20},
	"imp": {"hp": 2.0, "speed": 1.8, "touch": 8.0, "points": 30},
	"skeleton": {"hp": 2.0, "speed": 1.9, "touch": 6.0, "points": 30},
	"sorcerer": {"hp": 2.0, "speed": 2.2, "touch": 10.0, "points": 40},
	"deathshade": {"hp": 8.0, "speed": 1.6, "touch": 60.0, "points": 100},
}
const GEN_KIND := {"bones": "ghost", "hut": "grunt", "brazier": "imp"}
const LEVELS := "res://games/fourtorches/levels/crypts.torch"
const HORDE := 80                        ## monsters at most
const WAKE := 16.0                       ## monsters further than this from every hero wait
const GEN_REACH := 12.0                  ## generators make monsters while a hero is this near
const CRACK_HP := 3.0                    ## hits a crumbling wall takes

static var _authored: Array = []

var level := 0
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var tiles := PackedByteArray()     ## 0 wall, 1 floor, 2 door, 3 exit, 4 crumbling wall
var title := ""                    ## the level's name
var rank := 1                      ## how strong the level's generators begin
var exits := {}                    ## exit cell -> levels it goes down (1, or 2 for a skip)
var jump := 1                      ## the exit taken
var cracks := {}                   ## crumbling wall cell index -> hits left
var heroes: Array[Dictionary] = []
var monsters: Array[Dictionary] = []
var gens: Array[Dictionary] = []
var items: Array[Dictionary] = []  ## {cell, kind}
var missiles: Array[Dictionary] = []   ## {pos, vel, h (hero, or -1), kind, dmg}
var exit_cell := Vector2i.ZERO
var start := Vector2.ZERO
var rng := RandomNumberGenerator.new()
var _field := PackedInt32Array()    ## walking distance to the nearest hero
var _field_t := 0.0
var _next_id := 0
var _ticks := 0


## `party`: an array of {cls, cpu, health, score, keys, potions} (carried over between levels).
func _init(level_: int, party: Array, seed_ := 1) -> void:
	level = level_
	rng.seed = seed_ * 7919 + level_ * 131
	var lv := authored()
	if level < lv.size():
		_load_level(lv[level])
	else:
		rank = mini(3, 1 + level / 3)
		title = "THE DEEP %d" % (level - lv.size() + 1)
		_dungeon()
	# each hero on a free floor cell of their own, nearest the start first
	var d0 := _bfs(Vector2i(floori(start.x), floori(start.y)), [], 3)
	var spots: Array[Vector2] = [start]
	for dd in [Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(-1, 0), Vector2i(0, -1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(2, 0), Vector2i(0, 2)]:
		var c: Vector2i = Vector2i(floori(start.x), floori(start.y)) + dd
		if walkable(c) and d0[idx(c)] <= 3:
			spots.append(Vector2(c) + Vector2(0.5, 0.5))
	for i in party.size():
		var p: Dictionary = party[i]
		var cls: String = p.get("cls", ORDER[i])
		heroes.append({"i": i, "cls": cls, "cpu": p.get("cpu", true), "pos": spots[mini(i, spots.size() - 1)],
			"face": Vector2(0, 1), "move": Vector2.ZERO, "fire": false, "potion_pressed": false, "health": float(p.get("health", 800)),
			"score": p.get("score", 0), "keys": p.get("keys", 0), "potions": p.get("potions", 0), "dead": false, "melee_t": 0.0,
			"hurt": 0.0, "shot": false, "low": false})


# ------------------------------------------------------------------ the dungeon

## Our levels, read once: [{name, rank, rows}].
static func authored() -> Array:
	if not _authored.is_empty():
		return _authored
	var f := FileAccess.open(LEVELS, FileAccess.READ)
	if f == null:
		return _authored
	var cur := {}
	for line in f.get_as_text().split("\n"):
		var l := line.strip_edges(false, true)
		if l.begins_with("== "):
			cur = {"name": l.substr(3), "rank": 1, "rows": []}
			_authored.append(cur)
		elif cur.is_empty():
			continue
		elif l.begins_with("rank "):
			cur["rank"] = int(l.substr(5))
		elif l != "":
			(cur["rows"] as Array).append(l)
	return _authored


func _load_level(lv: Dictionary) -> void:
	title = lv["name"]
	rank = lv["rank"]
	tiles.resize(W * H)
	tiles.fill(0)
	var rows: Array = lv["rows"]
	for y in mini(H, rows.size()):
		var row: String = rows[y]
		for x in mini(W, row.length()):
			var ch := row[x]
			var c := Vector2i(x, y)
			if ch == "#":
				continue
			tiles[idx(c)] = 1
			match ch:
				"%":
					tiles[idx(c)] = 4
					cracks[idx(c)] = CRACK_HP
				"D": tiles[idx(c)] = 2
				"@": start = Vector2(x + 0.5, y + 0.5)
				"E", "X":
					tiles[idx(c)] = 3
					exits[c] = 2 if ch == "X" else 1
					if ch == "E":
						exit_cell = c
				"1", "2", "3":
					tiles[idx(c)] = 0   # a generator is solid
					_gen(c, ["bones", "hut", "brazier"][int(ch) - 1], rank)
				"g", "r", "i", "s", "z", "d":
					var kind: String = {"g": "ghost", "r": "grunt", "i": "imp", "s": "skeleton", "z": "sorcerer", "d": "deathshade"}[ch]
					_spawn(kind, Vector2(x + 0.5, y + 0.5), rank)
				"f", "b", "c", "k", "p", "$", "*":
					var kind: String = {"f": "food_ham", "b": "food_bowl", "c": "food_cider", "k": "key", "p": "potion", "$": "chest", "*": "gold_pile"}[ch]
					items.append({"cell": c, "kind": kind})


## A generator of rank `r` (1-3): its hit points come in ranks, its look (state 0 whole .. 2 nearly gone) shows the rank.
func _gen(c: Vector2i, kind: String, r: int) -> void:
	var per := gen_rank_hp()
	gens.append({"cell": c, "kind": kind, "rank": r, "state": 3 - r, "hp": per * r, "t": rng.randf_range(0.5, 2.0), "solid": true})


func gen_rank_hp() -> float:
	return 1.6 + level * 0.15


func monster_rank_hp(kind: String) -> float:
	return MONSTER[kind]["hp"] * 0.5 * (1.0 + level * 0.06)


func idx(c: Vector2i) -> int:
	return c.y * W + c.x


func tile(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= W or c.y >= H:
		return 0
	return tiles[idx(c)]


func walkable(c: Vector2i) -> bool:
	var t := tile(c)
	return t == 1 or t == 3


func _carve(r: Rect2i) -> void:
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			if x > 0 and y > 0 and x < W - 1 and y < H - 1:
				tiles[idx(Vector2i(x, y))] = 1


## Rooms placed at random without overlapping, each joined to the one before by a two-wide L-shaped corridor; the exit
## in the room farthest from the start; a few side rooms behind a door, their keys out in the open; generators, food,
## treasure and potions in the rooms.
func _dungeon() -> void:
	tiles.resize(W * H)
	tiles.fill(0)
	var rooms: Array[Rect2i] = []
	var tries := 0
	while rooms.size() < 11 and tries < 400:
		tries += 1
		var r := Rect2i(rng.randi_range(1, W - 10), rng.randi_range(1, H - 9), rng.randi_range(5, 9), rng.randi_range(4, 7))
		var ok := true
		for o in rooms:
			if o.grow(2).intersects(r):
				ok = false
		if ok:
			rooms.append(r)
	rooms.sort_custom(func(a, b): return a.position.x + a.position.y * 0.6 < b.position.x + b.position.y * 0.6)
	for r in rooms:
		_carve(r)
	for i in range(1, rooms.size()):
		var a := rooms[i - 1].get_center()
		var b := rooms[i].get_center()
		if rng.randf() < 0.5:
			_carve(Rect2i(mini(a.x, b.x), a.y, absi(b.x - a.x) + 2, 2))
			_carve(Rect2i(b.x, mini(a.y, b.y), 2, absi(b.y - a.y) + 2))
		else:
			_carve(Rect2i(a.x, mini(a.y, b.y), 2, absi(b.y - a.y) + 2))
			_carve(Rect2i(mini(a.x, b.x), b.y, absi(b.x - a.x) + 2, 2))
	# a few loops so it isn't just a chain
	for k in 2:
		var a := rooms[rng.randi() % rooms.size()].get_center()
		var b := rooms[rng.randi() % rooms.size()].get_center()
		_carve(Rect2i(mini(a.x, b.x), a.y, absi(b.x - a.x) + 1, 2))
	var s := rooms[0].get_center()
	start = Vector2(s.x + 0.5, s.y + 0.5)
	# the exit: the farthest room's middle
	var dist := _bfs(Vector2i(s))
	var far := 0
	var fd := -1
	for i in rooms.size():
		var d: int = dist[idx(rooms[i].get_center())]
		if d > fd:
			fd = d
			far = i
	exit_cell = rooms[far].get_center()
	tiles[idx(exit_cell)] = 3
	exits[exit_cell] = 1
	# side rooms behind doors
	for k in 2:
		_side_room(rooms, dist)
	# the contents of the rooms
	for i in rooms.size():
		var r := rooms[i]
		if i == 0:
			continue
		var n_gen := 1 + (1 if rng.randf() < 0.3 + level * 0.08 else 0)
		for g in n_gen:
			var c := _free_cell(r)
			if c != Vector2i(-1, -1):
				var kinds := ["bones", "hut", "brazier"]
				var kind: String = kinds[rng.randi() % mini(kinds.size(), 2 + level / 2)]
				_gen(c, kind, rank)
				tiles[idx(c)] = 0   # a generator is solid
		var stuff := ["food_ham", "food_bowl", "food_cider", "chest", "gold_pile", "potion"]
		for k in rng.randi_range(1, 3):
			var c := _free_cell(r)
			if c != Vector2i(-1, -1):
				items.append({"cell": c, "kind": stuff[rng.randi() % stuff.size()]})
	# a monster or two waiting in some rooms, and the rare deathshade from level 3
	for i in range(1, rooms.size()):
		for k in rng.randi_range(0, 2 + level / 2):
			var c := _free_cell(rooms[i])
			if c != Vector2i(-1, -1):
				var kind: String = ["grunt", "ghost", "imp", "skeleton", "sorcerer"][rng.randi() % mini(5, 2 + level)]
				_spawn(kind, Vector2(c) + Vector2(0.5, 0.5), rank)
		if level >= 2 and rng.randf() < 0.12:
			var c := _free_cell(rooms[i])
			if c != Vector2i(-1, -1):
				_spawn("deathshade", Vector2(c) + Vector2(0.5, 0.5))


func _free_cell(r: Rect2i) -> Vector2i:
	for k in 30:
		var c := Vector2i(rng.randi_range(r.position.x + 1, r.end.x - 2), rng.randi_range(r.position.y + 1, r.end.y - 2))
		if tile(c) != 1 or c == exit_cell:
			continue
		var busy := false
		for it in items:
			if it["cell"] == c:
				busy = true
		for g in gens:
			if (g["cell"] as Vector2i).distance_to(c) < 2.0:
				busy = true
		if Vector2(c).distance_to(start) < 4.0:
			busy = true
		if not busy:
			return c
	return Vector2i(-1, -1)


## A small treasure room off a corridor, closed by a door; its key somewhere already reachable.
func _side_room(rooms: Array[Rect2i], dist: PackedInt32Array) -> void:
	for tries in 60:
		var base := rooms[rng.randi() % rooms.size()]
		var side := rng.randi() % 4
		var r: Rect2i
		var door: Rect2i
		match side:
			0: r = Rect2i(base.position.x + 1, base.position.y - 6, 4, 4); door = Rect2i(r.position.x + 1, r.end.y, 2, 2)
			1: r = Rect2i(base.position.x + 1, base.end.y + 2, 4, 4); door = Rect2i(r.position.x + 1, base.end.y, 2, 2)
			2: r = Rect2i(base.position.x - 6, base.position.y + 1, 4, 4); door = Rect2i(r.end.x, r.position.y + 1, 2, 2)
			_: r = Rect2i(base.end.x + 2, base.position.y + 1, 4, 4); door = Rect2i(base.end.x, r.position.y + 1, 2, 2)
		if r.position.x < 1 or r.position.y < 1 or r.end.x > W - 1 or r.end.y > H - 1:
			continue
		var clear := true
		for y in range(r.position.y - 1, r.end.y + 1):
			for x in range(r.position.x - 1, r.end.x + 1):
				if tile(Vector2i(x, y)) != 0:
					clear = false
		if not clear:
			continue
		_carve(r)
		for y in range(door.position.y, door.end.y):
			for x in range(door.position.x, door.end.x):
				tiles[idx(Vector2i(x, y))] = 2
		for k in 3:
			var c := Vector2i(rng.randi_range(r.position.x, r.end.x - 1), rng.randi_range(r.position.y, r.end.y - 1))
			items.append({"cell": c, "kind": ["chest", "gold_pile", "potion", "chest"][k % 4]})
		# the key: on the reachable side, not too near
		for k in 40:
			var c := Vector2i(rng.randi_range(1, W - 2), rng.randi_range(1, H - 2))
			if tile(c) == 1 and dist[idx(c)] > 6 and dist[idx(c)] < 1 << 20:
				items.append({"cell": c, "kind": "key"})
				break
		return


## Walking distances (in tiles) from one or more cells, over the floor (a queue run by index: quick).
func _bfs(from: Vector2i, extra: Array[Vector2i] = [], limit := 1 << 20) -> PackedInt32Array:
	var d := PackedInt32Array()
	d.resize(W * H)
	d.fill(1 << 20)
	var q := PackedInt32Array()
	for c in [from] + extra:
		if c.x >= 0 and walkable(c):
			d[idx(c)] = 0
			q.append(idx(c))
	var head := 0
	while head < q.size():
		var i: int = q[head]
		head += 1
		var dist: int = d[i] + 1
		if dist > limit:
			continue
		var x := i % W
		var y := i / W
		for n in [i + 1, i - 1, i + W, i - W]:
			if n < 0 or n >= W * H or (absi(n % W - x) > 1):
				continue
			var t: int = tiles[n]
			if (t == 1 or t == 3) and d[n] > dist:
				d[n] = dist
				q.append(n)
	return d


func _spawn(kind: String, p: Vector2, r := 2) -> void:
	r = clampi(r, 1, 3) if kind != "deathshade" else 3
	monsters.append({"id": _next_id, "kind": kind, "pos": p, "rank": r, "top": r, "hp": monster_rank_hp(kind) * r, "dead": false, "t": rng.randf() * 2.0,
		"shoot_t": rng.randf_range(1.5, 3.0), "fade": 0.0, "hit_t": 0.0, "face": Vector2(0, 1)})
	_next_id += 1


# ------------------------------------------------------------------ helpers

func alive() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for h in heroes:
		if not h["dead"]:
			out.append(h)
	return out


## Who leads: the living human heroes, or with no player (the demo) the first hero still standing.
func leaders() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for h in alive():
		if not h["cpu"]:
			out.append(h)
	if out.is_empty() and not alive().is_empty():
		out.append(alive()[0])
	return out


## Where the screen is: the middle of the leaders (the CPU companions follow them).
func anchor() -> Vector2:
	var ls := leaders()
	if ls.is_empty():
		return start
	var c := Vector2.ZERO
	for h in ls:
		c += h["pos"]
	return c / ls.size()


func centre() -> Vector2:
	var al := alive()
	if al.is_empty():
		return start
	var c := Vector2.ZERO
	for h in al:
		c += h["pos"]
	return c / al.size()


func solid_at(p: Vector2) -> bool:
	var c := Vector2i(floori(p.x), floori(p.y))
	return not walkable(c)


## Moves a circle by v, sliding along walls.
func _slide(p: Vector2, v: Vector2, r: float) -> Vector2:
	var nx := p + Vector2(v.x, 0)
	if _blocked(nx, r):
		nx = p
	var ny := nx + Vector2(0, v.y)
	if _blocked(ny, r):
		ny = nx
	return ny


func _blocked(p: Vector2, r: float) -> bool:
	for dx in [-r, r]:
		for dy in [-r, r]:
			if solid_at(p + Vector2(dx, dy)):
				return true
	return false


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	_ticks += 1
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			return
		Phase.EXIT, Phase.OVER:
			phase_t -= TICK
			return
	_field_t -= TICK
	if _field_t <= 0.0:
		_field_t = 0.25
		_make_field()
	var c := centre()
	for h in heroes:
		_hero(h, c)
	_missiles()
	_monsters()
	_generators()
	if alive().is_empty():
		phase = Phase.OVER
		phase_t = 3.0
		event.emit("game_over", {})


func _make_field() -> void:
	var cells: Array[Vector2i] = []
	for h in alive():
		cells.append(Vector2i(floori(h["pos"].x), floori(h["pos"].y)))
	if cells.is_empty():
		return
	var first: Vector2i = cells.pop_front()
	_field = _bfs(first, cells, 32)


func _hero(h: Dictionary, c: Vector2) -> void:
	if h["dead"]:
		return
	var cls: Dictionary = CLASSES[h["cls"]]
	# health drains, a little each second
	h["health"] -= TICK * 1.0
	h["hurt"] = maxf(0.0, h["hurt"] - TICK)
	if h["health"] < 200.0 and not h["low"]:
		h["low"] = true
		event.emit("low", {"h": h["i"]})
	elif h["health"] >= 250.0:
		h["low"] = false
	if h["health"] <= 0.0:
		h["dead"] = true
		event.emit("die", {"h": h["i"]})
		return
	var mv: Vector2 = h["move"]
	if mv.length() > 0.1:
		h["face"] = Vector2(signf(roundf(mv.x * 1.3)), signf(roundf(mv.y * 1.3))).normalized() if mv.length() > 0.1 else h["face"]
	var p: Vector2 = h["pos"]
	var np := _slide(p, mv.limit_length(1.0) * cls["speed"] * TICK, R)
	# stay on the screen: a human may not push past the edge the other humans hold; a CPU companion keeps to the
	# screen round them, and one left off it (stuck behind a wall) rejoins beside the leader after a moment
	var humans := leaders()
	var leads := humans.has(h)
	if leads and humans.size() > 1:
		var oc := Vector2.ZERO
		for o in humans:
			if o != h:
				oc += o["pos"]
		oc /= humans.size() - 1
		var k := float(humans.size()) / (humans.size() - 1)
		np = _keep(p, np, oc, VIEW * k)
	elif not leads and not humans.is_empty():
		var a := anchor()
		np = _keep(p, np, a, VIEW * 0.92)
		var off := absf(np.x - a.x) > VIEW.x or absf(np.y - a.y) > VIEW.y
		h["stray"] = h.get("stray", 0.0) + TICK if off else 0.0
		if h["stray"] > STRAY:
			h["stray"] = 0.0
			np = _beside(humans[0]["pos"])
			event.emit("rejoin", {"h": h["i"], "pos": np})
	# doors: a key opens the whole door it touches
	var cc := Vector2i(floori(np.x + (h["face"] as Vector2).x * 0.5), floori(np.y + (h["face"] as Vector2).y * 0.5))
	if tile(cc) == 2 and h["keys"] > 0:
		h["keys"] -= 1
		_open_door(cc)
	h["pos"] = np
	# a missile, one at a time
	if h["fire"] and not h["shot"]:
		h["shot"] = true
		missiles.append({"pos": np + (h["face"] as Vector2) * 0.4, "vel": (h["face"] as Vector2) * cls["shot_speed"], "h": h["i"], "kind": h["cls"], "dmg": cls["shot"]})
		event.emit("shoot", {"h": h["i"]})
	# a potion
	if h["potion_pressed"] and h["potions"] > 0:
		h["potions"] -= 1
		_blast(h, cls["magic"])
	h["potion_pressed"] = false
	# items underfoot
	var here := Vector2i(floori(np.x), floori(np.y))
	for it in items.duplicate():
		if (Vector2(it["cell"]) + Vector2(0.5, 0.5)).distance_to(np) < 0.75:
			items.erase(it)
			match it["kind"]:
				"food_ham", "food_bowl", "food_cider":
					h["health"] = minf(h["health"] + 100.0, 2000.0)
					event.emit("food", {"h": h["i"], "kind": it["kind"]})
				"key":
					h["keys"] += 1
					event.emit("key", {"h": h["i"]})
				"potion":
					h["potions"] += 1
					event.emit("potion", {"h": h["i"]})
				"chest", "gold_pile":
					var pts := 100 if it["kind"] == "chest" else 50
					h["score"] += pts
					event.emit("treasure", {"h": h["i"], "points": pts})
	# the exit is the players' choice: a CPU companion on it waits (unless everyone is CPU, as in the demo)
	if tile(here) == 3 and leaders().has(h):
		jump = exits.get(here, 1)
		phase = Phase.EXIT
		phase_t = 2.5
		for o in heroes:
			o["score"] += 200 if not o["dead"] else 0
		event.emit("exit", {"h": h["i"], "jump": jump})


## The move from `p` to `np`, kept inside the box of half-size `half` round `at`: a step that would leave it (or go
## farther out) is held on that axis, so nobody is ever pushed through a wall.
func _keep(p: Vector2, np: Vector2, at: Vector2, half: Vector2) -> Vector2:
	if absf(np.x - at.x) > half.x and absf(np.x - at.x) > absf(p.x - at.x):
		np.x = p.x
	if absf(np.y - at.y) > half.y and absf(np.y - at.y) > absf(p.y - at.y):
		np.y = p.y
	return np


## A free floor spot next to `p` (for a companion rejoining), or `p` itself.
func _beside(p: Vector2) -> Vector2:
	for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1), Vector2(1, 1), Vector2(-1, 1), Vector2(1, -1), Vector2(-1, -1)]:
		var q: Vector2 = p + d * 0.9
		if not solid_at(q):
			return q
	return p


func _open_door(c: Vector2i) -> void:
	var cells: Array[Vector2i] = []
	var q: Array[Vector2i] = [c]
	while not q.is_empty():
		var d: Vector2i = q.pop_front()
		if tile(d) != 2 or cells.has(d):
			continue
		cells.append(d)
		tiles[idx(d)] = 1
		for dd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			q.append(d + dd)
	event.emit("door", {"cells": cells})


func _blast(h: Dictionary, magic: float) -> void:
	event.emit("blast", {"h": h["i"], "pos": h["pos"]})
	_blast_at(h, h["pos"], magic, 11.0)


func _blast_at(h: Dictionary, p: Vector2, magic: float, reach: float) -> void:
	for m in monsters:
		if not m["dead"] and (m["pos"] as Vector2).distance_to(p) < reach:
			_hurt_monster(m, 3.0 * magic * monster_rank_hp(m["kind"]), h)
	for g in gens:
		if g["hp"] > 0.0 and (Vector2(g["cell"]) + Vector2(0.5, 0.5)).distance_to(p) < reach:
			_hurt_gen(g, 1.5 * magic, h)


func _missiles() -> void:
	var keep: Array[Dictionary] = []
	for s in missiles:
		var p: Vector2 = s["pos"] + s["vel"] * TICK
		s["pos"] = p
		var gone := false
		var pc := Vector2i(floori(p.x), floori(p.y))
		if solid_at(p):
			# a generator in the way?
			for g in gens:
				if g["hp"] > 0.0 and pc == g["cell"] and s["h"] >= 0:
					_hurt_gen(g, s["dmg"], heroes[s["h"]])
			# a crumbling wall
			if tile(pc) == 4 and s["h"] >= 0:
				cracks[idx(pc)] = cracks.get(idx(pc), CRACK_HP) - 1.0
				if cracks[idx(pc)] <= 0.0:
					tiles[idx(pc)] = 1
					cracks.erase(idx(pc))
					event.emit("crumble", {"cell": pc})
			gone = true
			event.emit("hit", {"pos": p, "kind": "wall"})
		elif s["h"] >= 0 and _shot_item(pc, s["h"]):
			gone = true
		elif s["h"] >= 0:
			for m in monsters:
				if not m["dead"] and (m["pos"] as Vector2).distance_to(p) < 0.55:
					var dmg: float = s["dmg"] * (0.25 if m["kind"] == "deathshade" else 1.0)
					_hurt_monster(m, dmg, heroes[s["h"]])
					gone = true
					break
		else:
			for h in heroes:
				if not h["dead"] and (h["pos"] as Vector2).distance_to(p) < 0.5:
					_hurt_hero(h, 10.0)
					gone = true
					break
		if (s["pos"] as Vector2).distance_to(centre()) > 30.0:
			gone = true
		if gone:
			if s["h"] >= 0:
				heroes[s["h"]]["shot"] = false
		else:
			keep.append(s)
	missiles = keep


## A hero's missile on an item: food is smashed (the cider jug is stone), a potion goes off as a smaller blast.
func _shot_item(c: Vector2i, hi: int) -> bool:
	for k in items.size():
		var it: Dictionary = items[k]
		if it["cell"] != c:
			continue
		var pos := Vector2(c) + Vector2(0.5, 0.5)
		match it["kind"]:
			"food_ham", "food_bowl":
				items.remove_at(k)
				event.emit("food_shot", {"h": hi, "pos": pos})
				return true
			"potion":
				items.remove_at(k)
				event.emit("potion_shot", {"h": hi, "pos": pos})
				_blast_at(heroes[hi], pos, 0.5 * CLASSES[heroes[hi]["cls"]]["magic"], 6.0)
				return true
	return false


func _hurt_monster(m: Dictionary, dmg: float, by: Dictionary) -> void:
	m["hp"] -= dmg
	m["hit_t"] = 0.15
	m["rank"] = clampi(ceili(m["hp"] / monster_rank_hp(m["kind"]) - 0.001), 1, 3)
	event.emit("hit", {"pos": m["pos"], "kind": m["kind"]})
	if m["hp"] <= 0.0 and not m["dead"]:
		m["dead"] = true
		var pts: int = MONSTER[m["kind"]]["points"] * int(m.get("top", m["rank"]))
		by["score"] += pts
		event.emit("kill", {"pos": m["pos"], "kind": m["kind"], "points": pts})


func _hurt_gen(g: Dictionary, dmg: float, by: Dictionary) -> void:
	if g["hp"] <= 0.0:
		return
	g["hp"] -= dmg
	g["rank"] = clampi(ceili(g["hp"] / gen_rank_hp() - 0.001), 1, 3)
	g["state"] = 3 - g["rank"]
	event.emit("gen_hit", {"pos": Vector2(g["cell"]) + Vector2(0.5, 0.5), "state": g["state"]})
	if g["hp"] <= 0.0:
		tiles[idx(g["cell"])] = 1
		by["score"] += 100
		event.emit("gen_break", {"pos": Vector2(g["cell"]) + Vector2(0.5, 0.5)})


func _hurt_hero(h: Dictionary, dmg: float) -> void:
	var armor: float = CLASSES[h["cls"]]["armor"]
	var d := dmg * (1.0 - armor)
	h["health"] -= d
	h["hurt"] = 0.25
	event.emit("hurt", {"h": h["i"], "damage": d})


func _monsters() -> void:
	var keep: Array[Dictionary] = []
	var c := centre()
	for m in monsters:
		if m["dead"]:
			continue
		m["t"] += TICK
		m["hit_t"] = maxf(0.0, m["hit_t"] - TICK)
		var p: Vector2 = m["pos"]
		# asleep when far from everyone
		var nh := _nearest_hero(p)
		if nh.is_empty() or p.distance_to(nh["pos"]) > WAKE:
			keep.append(m)
			continue
		var spec: Dictionary = MONSTER[m["kind"]]
		# step down the distance field towards the heroes (each monster rethinks every fourth tick)
		if (_ticks + int(m["id"])) % 4 != 0 and m.has("dir"):
			m["pos"] = _slide(p, (m["dir"] as Vector2) * spec["speed"] * (1.0 + level * 0.04) * TICK, 0.3)
			_touch(m, spec)
			if not m["dead"]:
				keep.append(m)
			continue
		var near := _nearest_hero(p)
		var cell := Vector2i(floori(p.x), floori(p.y))
		var best := cell
		var bd: int = _field[idx(cell)] if walkable(cell) else 1 << 20
		for dd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1)]:
			var n: Vector2i = cell + dd
			if walkable(n) and _field[idx(n)] < bd and (dd.x == 0 or dd.y == 0 or (walkable(cell + Vector2i(dd.x, 0)) and walkable(cell + Vector2i(0, dd.y)))):
				bd = _field[idx(n)]
				best = n
		var target := Vector2(best) + Vector2(0.5, 0.5)
		if not near.is_empty() and bd <= 1:
			target = near["pos"]
		var keep_away: bool = m["kind"] in ["imp", "skeleton"] and not near.is_empty() and p.distance_to(near["pos"]) < 4.0
		var dir := (target - p).normalized() * (-0.6 if keep_away else 1.0)
		m["dir"] = dir
		if dir.length() > 0.01:
			m["face"] = dir.normalized()
		m["pos"] = _slide(p, dir * spec["speed"] * (1.0 + level * 0.04) * TICK, 0.3)
		# sorcerers blink out now and then
		if m["kind"] == "sorcerer":
			m["fade"] = 1.0 if fmod(m["t"], 4.0) > 2.6 else 0.0
		# imps and skeletons shoot when in line
		if m["kind"] in ["imp", "skeleton"] and not near.is_empty():
			m["shoot_t"] -= TICK
			var to: Vector2 = near["pos"] - p
			if m["shoot_t"] <= 0.0 and to.length() < 9.0:
				m["shoot_t"] = rng.randf_range(1.6, 3.0)
				missiles.append({"pos": p, "vel": to.normalized() * 6.5, "h": -1, "kind": "imp_fire" if m["kind"] == "imp" else "arrow", "dmg": 1.0})
				event.emit("monster_shot", {"pos": p, "kind": m["kind"]})
		_touch(m, spec)
		if not m["dead"]:
			keep.append(m)
	monsters = keep


## Touching a hero: it hurts, and the hero hits back.
func _touch(m: Dictionary, spec: Dictionary) -> void:
	for h in heroes:
		if h["dead"]:
			continue
		if (h["pos"] as Vector2).distance_to(m["pos"]) < 0.65:
			if m["kind"] == "ghost":
				_hurt_hero(h, spec["touch"])
				m["dead"] = true
				event.emit("kill", {"pos": m["pos"], "kind": "ghost", "points": 0})
				break
			h["melee_t"] -= TICK
			if h["melee_t"] <= 0.0:
				h["melee_t"] = 0.45
				_hurt_hero(h, spec["touch"] if m["kind"] != "sorcerer" or m["fade"] == 0.0 else 0.0)
				_hurt_monster(m, CLASSES[h["cls"]]["melee"] * (0.3 if m["kind"] == "deathshade" else 1.0), h)
				event.emit("melee", {"h": h["i"]})
				if m["kind"] == "deathshade":
					m["dead"] = true   # it drains, then fades
			break


func _nearest_hero(p: Vector2) -> Dictionary:
	var best := {}
	var bd := INF
	for h in heroes:
		if not h["dead"] and (h["pos"] as Vector2).distance_to(p) < bd:
			bd = (h["pos"] as Vector2).distance_to(p)
			best = h
	return best


func _generators() -> void:
	var c := centre()
	for g in gens:
		if g["hp"] <= 0.0:
			continue
		var p := Vector2(g["cell"]) + Vector2(0.5, 0.5)
		var nh := _nearest_hero(p)
		if nh.is_empty() or p.distance_to(nh["pos"]) > GEN_REACH or monsters.size() >= HORDE:
			continue
		g["t"] -= TICK
		if g["t"] <= 0.0:
			# a horde: one every second or two from a whole generator, slower as it is knocked down
			g["t"] = rng.randf_range(0.6, 1.3) / (1.0 + level * 0.05) * (1.0 + g["state"] * 0.5)
			# out of a free side
			for dd in [Vector2i(0, 1), Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, -1)]:
				var n: Vector2i = g["cell"] + dd
				if walkable(n):
					var kind: String = GEN_KIND[g["kind"]]
					if level >= 3 and rng.randf() < 0.2:
						kind = ["skeleton", "sorcerer"][rng.randi() % 2]
					_spawn(kind, Vector2(n) + Vector2(0.5, 0.5), g["rank"])
					event.emit("spawn", {"pos": Vector2(n) + Vector2(0.5, 0.5), "kind": kind})
					break


func party() -> Array:
	var out := []
	for h in heroes:
		out.append({"cls": h["cls"], "cpu": h["cpu"], "health": maxf(h["health"], 0.0) if not h["dead"] else 0.0, "score": h["score"],
			"keys": h["keys"], "potions": h["potions"], "dead": h["dead"]})
	return out
