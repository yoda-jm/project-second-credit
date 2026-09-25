class_name FruitburrowEngine
extends RefCounted
## Rules of Fruitburrow (inspired by Fruity Frank, 1984). Pure logic, advanced in fixed ticks with a seeded
## random generator, so a game can be replayed from its inputs and tested without a view.
##
## The gardener digs tunnels through a slice of soil and picks the fruit. Monsters come out of the nest and chase
## him through the tunnels; a monster that cannot reach him for a while starts digging. Undermined apples wobble,
## fall and squash whatever is below (and break if they fall two cells or more). The gardener's ball runs along
## the tunnels, bouncing at walls, and knocks out the first monster it meets; it grows back after a while.
## A garden is cleared when all its fruit is picked or all its monsters are out.
## Speeds, timings and scores are our own tuning; the original's are still to be checked in an emulator.
##
## Entities move from cell centre to cell centre: {cell: Vector2i, to: Vector2i, t: 0..1}.

signal event(kind: String, data: Dictionary)  ## for the view and audio: "dig", "fruit", "apple_wobble",
## "apple_fall", "apple_land", "apple_break", "squash", "monster_spawn", "monster_dig", "monster_hit",
## "transform", "throw", "ball_bounce", "ball_lost", "ball_back", "death", "phase", "clear", "game_over"

enum Phase { READY, PLAY, DYING, CLEAR, GAME_OVER }
enum Apple { REST, WOBBLE, FALL }
enum Kind { PLUM, DIGGER }
const T = GardenMap.Terrain
const DIRS: Array[Vector2i] = [Vector2i.UP, Vector2i.LEFT, Vector2i.DOWN, Vector2i.RIGHT]

const TICK := 1.0 / 60.0
const READY_SECONDS := 2.0
const DYING_SECONDS := 2.2
const CLEAR_SECONDS := 3.0
const PLAYER_SPEED := 4.2  ## cells per second in tunnels
const DIG_SPEED := 2.8  ## cells per second through soil
const MONSTER_SPEED := 3.0
const DIGGER_SPEED := 1.8
const SPEEDUP_PER_LEVEL := 0.06
const BALL_SPEED := 11.0
const BALL_LIFE := 3.0
const BALL_REGROW := 2.0  ## seconds for the first throw of a garden; each further throw adds BALL_REGROW_STEP
const BALL_REGROW_STEP := 1.0
const BALL_MAX_REGROW := 8.0
const APPLE_WOBBLE := 0.7
const APPLE_FALL_SPEED := 7.5
const SPAWN_FIRST := 1.5
const SPAWN_EVERY := 3.5
const MAX_ALIVE := 4
const STUCK_TO_DIGGER := 8.0  ## seconds a monster tries to reach the gardener before it starts digging
const WANDER := 0.12  ## chance that a monster takes a random turn at a junction
const LIVES := 3
const HIT_RADIUS := 0.6
const SCORE_FRUIT: Array[int] = [50, 80, 100, 120, 150]
const SCORE_BALL := 200
const SCORE_SQUASH := 500  ## doubled for every further monster under the same apple
const SCORE_CLEAR := 1000
const INF := 1 << 28

var map: GardenMap
var level := 1
var rng := RandomNumberGenerator.new()
var terrain := PackedByteArray()
var fruit := {}  ## Vector2i -> fruit index
var apples: Array[Dictionary] = []  ## {cell, state, t, y (row, float), fell, id, kills}
var monsters: Array[Dictionary] = []  ## {kind, cell, to, t, id, stuck}
var player := {}  ## {cell, to, t, face, dig}
var ball := {}  ## empty unless flying: {cell, to, t, dir, life, flip}
var has_ball := true
var ball_regrow := 0.0
var throws := 0  ## this garden
var phase := Phase.READY
var phase_left := READY_SECONDS
var score := 0
var lives := LIVES
var spawned := 0
var killed := 0
var fruit_total := 0
var time := 0.0
var input_dir := Vector2i.ZERO  ## held direction, set by the game every tick
var _fire := false
var _spawn_in := SPAWN_FIRST
var _next_id := 1
var _dist := PackedInt32Array()  ## tunnel steps to the gardener
var _dig_dist := PackedInt32Array()  ## weighted steps to the gardener through soil (diggers)
var _dist_target := Vector2i(-1, -1)
var _dist_dirty := true


func _init(m: GardenMap = null, seed: int = 1) -> void:
	rng.seed = seed
	if m != null:
		load_garden(m, 1)


## Starts a garden (keeps score and lives: call it for the next level too).
func load_garden(m: GardenMap, lvl: int) -> void:
	map = m
	level = lvl
	terrain = m.terrain.duplicate()
	fruit = m.fruit.duplicate()
	fruit_total = fruit.size()
	apples.clear()
	for c in m.apples:
		apples.append({"cell": c, "state": Apple.REST, "t": 0.0, "y": float(c.y), "fell": 0, "id": _new_id(), "kills": 0})
	spawned = 0
	killed = 0
	throws = 0
	_reset_actors()
	_set_phase(Phase.READY, READY_SECONDS)


func _reset_actors() -> void:
	monsters.clear()
	player = {"cell": map.start, "to": map.start, "t": 0.0, "face": Vector2i.RIGHT, "dig": false}
	ball = {}
	has_ball = true
	ball_regrow = 0.0
	_spawn_in = SPAWN_FIRST
	_dist_dirty = true


func _new_id() -> int:
	_next_id += 1
	return _next_id


func _set_phase(p: Phase, secs: float) -> void:
	phase = p
	phase_left = secs
	event.emit("phase", {"phase": p, "level": level})


# ------------------------------------------------------------------ queries

func at(c: Vector2i) -> int:
	return terrain[c.y * map.w + c.x] if map.inside(c) else T.STONE


func pos_of(e: Dictionary) -> Vector2:
	return Vector2(e["cell"]).lerp(Vector2(e["to"]), e["t"])


## The cell whose centre the entity is closest to.
func near_cell(e: Dictionary) -> Vector2i:
	return e["cell"] if e["t"] < 0.5 else e["to"]


func apple_at(c: Vector2i) -> int:
	for i in apples.size():
		var a := apples[i]
		if a["state"] != Apple.FALL:
			if a["cell"] == c:
				return i
		elif c.x == a["cell"].x and (c.y == floori(a["y"]) or c.y == ceili(a["y"])):
			return i
	return -1


## Open tunnel with no apple in it (apples fall into it, monsters walk it).
func hollow(c: Vector2i) -> bool:
	return map.inside(c) and at(c) == T.TUNNEL and apple_at(c) < 0


func player_can_enter(c: Vector2i) -> bool:
	return map.inside(c) and at(c) != T.STONE and apple_at(c) < 0


func level_speed() -> float:
	return 1.0 + SPEEDUP_PER_LEVEL * float(mini(level - 1, 10))


func fire() -> void:
	_fire = true


# ------------------------------------------------------------------ tick

func tick() -> void:
	time += TICK
	var fire_now := _fire
	_fire = false
	match phase:
		Phase.READY:
			phase_left -= TICK
			if phase_left <= 0.0:
				_set_phase(Phase.PLAY, 0.0)
		Phase.DYING:
			_apples(TICK)
			phase_left -= TICK
			if phase_left <= 0.0:
				if lives <= 0:
					_set_phase(Phase.GAME_OVER, 0.0)
					event.emit("game_over", {"score": score})
				else:
					spawned -= monsters.size()
					_reset_actors()
					_set_phase(Phase.READY, READY_SECONDS)
		Phase.CLEAR:
			_apples(TICK)
			phase_left -= TICK
		Phase.PLAY:
			_move_player(TICK)
			if fire_now:
				_throw()
			_apples(TICK)
			_spawn(TICK)
			_move_monsters(TICK)
			_move_ball(TICK)
			_touch()
			if phase == Phase.PLAY and (fruit.is_empty() or (map.monsters > 0 and killed >= map.monsters)):
				score += SCORE_CLEAR
				_set_phase(Phase.CLEAR, CLEAR_SECONDS)
				event.emit("clear", {"level": level, "by_fruit": fruit.is_empty()})


## True once the clear celebration is over: the game loads the next garden.
func level_done() -> bool:
	return phase == Phase.CLEAR and phase_left <= 0.0


# ------------------------------------------------------------------ gardener

func _move_player(dt: float) -> void:
	var p := player
	var want := input_dir
	if want != Vector2i.ZERO:
		p["face"] = want
	var moving: bool = p["to"] != p["cell"]
	if moving:
		var dir: Vector2i = p["to"] - p["cell"]
		if want == -dir:  # turn back at once
			var c: Vector2i = p["cell"]
			p["cell"] = p["to"]
			p["to"] = c
			p["t"] = 1.0 - p["t"]
			p["dig"] = false
			dir = -dir
		p["t"] += (DIG_SPEED if p["dig"] else PLAYER_SPEED) * dt
		if p["t"] < 1.0:
			return
		var left: float = (p["t"] - 1.0) / (DIG_SPEED if p["dig"] else PLAYER_SPEED)
		p["cell"] = p["to"]
		p["t"] = 0.0
		_arrive(p["cell"])
		# keep going: the held direction, or straight on for no key at all? No: stop when nothing is held
		if want != Vector2i.ZERO:
			_player_start(want)
			if p["to"] != p["cell"]:
				p["t"] += (DIG_SPEED if p["dig"] else PLAYER_SPEED) * left
	elif want != Vector2i.ZERO:
		_player_start(want)
		if p["to"] != p["cell"]:
			p["t"] += (DIG_SPEED if p["dig"] else PLAYER_SPEED) * dt


func _player_start(dir: Vector2i) -> void:
	var p := player
	var nxt: Vector2i = p["cell"] + dir
	if not player_can_enter(nxt):
		return
	p["to"] = nxt
	p["dig"] = at(nxt) == T.SOIL
	if p["dig"]:
		terrain[nxt.y * map.w + nxt.x] = T.TUNNEL
		_dist_dirty = true
		event.emit("dig", {"cell": nxt, "by": "player", "dir": dir})
	elif _dist_target != nxt:
		_dist_dirty = true


func _arrive(c: Vector2i) -> void:
	if fruit.has(c):
		var f: int = fruit[c]
		fruit.erase(c)
		score += SCORE_FRUIT[f]
		event.emit("fruit", {"cell": c, "fruit": f, "left": fruit.size(), "points": SCORE_FRUIT[f]})


# ------------------------------------------------------------------ ball

func _throw() -> void:
	if not has_ball or not ball.is_empty():
		return
	var c := near_cell(player)
	var dir: Vector2i = player["face"]
	ball = {"cell": c, "to": c, "t": 0.0, "dir": dir, "life": BALL_LIFE, "flip": false}
	if not _ball_route(ball):
		ball = {}
		return
	has_ball = false
	throws += 1
	event.emit("throw", {"cell": c, "dir": dir})


## Picks the ball's next cell from its centre: straight on, else a turn (alternating sides), else back.
func _ball_route(b: Dictionary) -> bool:
	var d: Vector2i = b["dir"]
	var right := Vector2i(-d.y, d.x)
	var turns := [right, -right] if not b["flip"] else [-right, right]
	var bounced := false
	for cand in [d] + turns + [-d]:
		if hollow(b["cell"] + cand):
			if cand != d:
				bounced = true
				b["flip"] = not b["flip"]
			b["dir"] = cand
			b["to"] = b["cell"] + cand
			if bounced:
				event.emit("ball_bounce", {"cell": b["cell"]})
			return true
	return false


func _move_ball(dt: float) -> void:
	if ball.is_empty():
		if not has_ball:
			ball_regrow -= dt
			if ball_regrow <= 0.0:
				has_ball = true
				event.emit("ball_back", {})
		return
	ball["life"] -= dt
	if ball["life"] <= 0.0:
		_lose_ball("lost")
		return
	ball["t"] += BALL_SPEED * dt
	while ball["t"] >= 1.0:
		ball["t"] -= 1.0
		ball["cell"] = ball["to"]
		if not _ball_route(ball):
			_lose_ball("lost")
			return
	var bp := pos_of(ball)
	for i in monsters.size():
		if pos_of(monsters[i]).distance_to(bp) < HIT_RADIUS:
			var m := monsters[i]
			score += SCORE_BALL
			killed += 1
			event.emit("monster_hit", {"pos": pos_of(m), "id": m["id"], "kind": m["kind"], "points": SCORE_BALL})
			monsters.remove_at(i)
			_lose_ball("hit")
			return


func _lose_ball(why: String) -> void:
	event.emit("ball_lost", {"pos": pos_of(ball), "why": why})
	ball = {}
	ball_regrow = regrow_time()


## How long the ball takes to grow back after the current throw.
func regrow_time() -> float:
	return minf(BALL_MAX_REGROW, BALL_REGROW + BALL_REGROW_STEP * float(maxi(0, throws - 1)))


# ------------------------------------------------------------------ apples

func _apples(dt: float) -> void:
	var i := 0
	while i < apples.size():
		var a := apples[i]
		var below: Vector2i = a["cell"] + Vector2i.DOWN
		match a["state"]:
			Apple.REST:
				if hollow(below):
					a["state"] = Apple.WOBBLE
					a["t"] = APPLE_WOBBLE
					event.emit("apple_wobble", {"id": a["id"], "cell": a["cell"]})
			Apple.WOBBLE:
				if not hollow(below):
					a["state"] = Apple.REST
				else:
					a["t"] -= dt
					if a["t"] <= 0.0:
						a["state"] = Apple.FALL
						a["fell"] = 0
						a["kills"] = 0
						var c: Vector2i = a["cell"]
						terrain[c.y * map.w + c.x] = T.TUNNEL  # the apple leaves a hole behind
						_dist_dirty = true
						event.emit("apple_fall", {"id": a["id"], "cell": c})
			Apple.FALL:
				a["y"] += APPLE_FALL_SPEED * dt
				while a["y"] >= a["cell"].y + 1 and hollow_for_fall(a, a["cell"] + Vector2i.DOWN):
					a["cell"] = a["cell"] + Vector2i.DOWN
					a["fell"] += 1
				_crush(a)
				if a["y"] >= a["cell"].y and not hollow_for_fall(a, a["cell"] + Vector2i.DOWN):
					a["y"] = float(a["cell"].y)
					if a["fell"] >= 2:
						event.emit("apple_break", {"id": a["id"], "cell": a["cell"], "kills": a["kills"]})
						apples.remove_at(i)
						_dist_dirty = true
						continue
					a["state"] = Apple.REST
					_dist_dirty = true
					event.emit("apple_land", {"id": a["id"], "cell": a["cell"], "kills": a["kills"]})
		i += 1


## A falling apple ignores itself when testing the cell below.
func hollow_for_fall(a: Dictionary, c: Vector2i) -> bool:
	if not map.inside(c) or at(c) != T.TUNNEL:
		return false
	var j := apple_at(c)
	return j < 0 or apples[j] == a


func _crush(a: Dictionary) -> void:
	var ax: float = a["cell"].x
	var ay: float = a["y"]
	var i := 0
	while i < monsters.size():
		var mp := pos_of(monsters[i])
		if absf(mp.x - ax) < 0.5 and mp.y - ay > -0.2 and mp.y - ay < 0.8:
			var pts := SCORE_SQUASH << mini(a["kills"], 4)
			a["kills"] += 1
			score += pts
			killed += 1
			event.emit("squash", {"pos": mp, "id": monsters[i]["id"], "points": pts})
			monsters.remove_at(i)
			continue
		i += 1
	if phase == Phase.PLAY:
		var pp := pos_of(player)
		if absf(pp.x - ax) < 0.5 and pp.y - ay > -0.2 and pp.y - ay < 0.8:
			_die("apple")


# ------------------------------------------------------------------ monsters

func _spawn(dt: float) -> void:
	if spawned >= map.monsters or monsters.size() >= MAX_ALIVE:
		return
	_spawn_in -= dt
	if _spawn_in > 0.0:
		return
	_spawn_in = SPAWN_EVERY
	var kind := Kind.DIGGER if spawned >= map.monsters - map.diggers else Kind.PLUM
	var m := {"kind": kind, "cell": map.nest, "to": map.nest, "t": 0.0, "id": _new_id(), "stuck": 0.0, "last": Vector2i.ZERO}
	monsters.append(m)
	spawned += 1
	event.emit("monster_spawn", {"id": m["id"], "kind": kind, "cell": map.nest})


func _move_monsters(dt: float) -> void:
	var target := near_cell(player)
	if _dist_dirty or target != _dist_target:
		_distances(target)
	for m in monsters:
		var speed := (MONSTER_SPEED if m["kind"] == Kind.PLUM else DIGGER_SPEED) * level_speed()
		if m["to"] != m["cell"] and apple_at(m["to"]) >= 0 and apple_at(m["cell"]) < 0:
			var c: Vector2i = m["cell"]  # an apple landed in the way: back off
			m["cell"] = m["to"]
			m["to"] = c
			m["t"] = 1.0 - m["t"]
		if m["to"] != m["cell"]:
			m["t"] += speed * dt
			if m["t"] < 1.0:
				continue
			m["cell"] = m["to"]
			m["t"] = 0.0
		_monster_choose(m, dt)


func _monster_choose(m: Dictionary, dt: float) -> void:
	var c: Vector2i = m["cell"]
	var back: Vector2i = -m["last"]
	var opts: Array[Vector2i] = []
	var digger: bool = m["kind"] == Kind.DIGGER
	for d in DIRS:
		var n := c + d
		if not map.inside(n) or apple_at(n) >= 0:
			continue
		if at(n) == T.TUNNEL or (digger and at(n) == T.SOIL):
			opts.append(d)
	if opts.is_empty():  # boxed in (a fresh nest in solid soil): wait, then dig out
		if not digger:
			m["stuck"] += dt
			if m["stuck"] >= STUCK_TO_DIGGER:
				m["kind"] = Kind.DIGGER
				m["stuck"] = 0.0
				event.emit("transform", {"id": m["id"], "cell": c})
		return
	var field := _dig_dist if digger else _dist
	var here: int = field[c.y * map.w + c.x]
	var pick := Vector2i.ZERO
	if here < INF:
		m["stuck"] = 0.0
		var best := INF
		for d in opts:
			var n := c + d
			var v: int = field[n.y * map.w + n.x] + (1 if d == back else 0)
			if v < best:
				best = v
				pick = d
		if opts.size() >= 3 and rng.randf() < WANDER:
			pick = opts[rng.randi_range(0, opts.size() - 1)]
	else:
		m["stuck"] += 1.0 / maxf(0.001, (MONSTER_SPEED if not digger else DIGGER_SPEED) * level_speed())
		var fwd := opts.filter(func(d): return d != back)
		var pool: Array = fwd if not fwd.is_empty() else opts
		pick = pool[rng.randi_range(0, pool.size() - 1)]
		if not digger and m["stuck"] >= STUCK_TO_DIGGER:
			m["kind"] = Kind.DIGGER
			m["stuck"] = 0.0
			event.emit("transform", {"id": m["id"], "cell": c})
	var n := c + pick
	m["last"] = pick
	m["to"] = n
	if at(n) == T.SOIL:
		terrain[n.y * map.w + n.x] = T.TUNNEL
		_dist_dirty = true
		event.emit("dig", {"cell": n, "by": "monster", "dir": pick})


## Distance fields to the gardener: plain steps through tunnels, and weighted steps (soil costs 3) for diggers.
func _distances(target: Vector2i) -> void:
	_dist_target = target
	_dist_dirty = false
	var n := map.w * map.h
	_dist.resize(n)
	_dig_dist.resize(n)
	_dist.fill(INF)
	_dig_dist.fill(INF)
	if not map.inside(target):
		return
	# BFS through tunnels
	var q: Array[Vector2i] = [target]
	_dist[target.y * map.w + target.x] = 0
	var head := 0
	while head < q.size():
		var c := q[head]
		head += 1
		var dc: int = _dist[c.y * map.w + c.x]
		for d in DIRS:
			var nb := c + d
			if map.inside(nb) and at(nb) == T.TUNNEL and apple_at(nb) < 0 and _dist[nb.y * map.w + nb.x] == INF:
				_dist[nb.y * map.w + nb.x] = dc + 1
				q.append(nb)
	# Dijkstra through soil and tunnels (small grids: a simple scan for the minimum is enough)
	var done := PackedByteArray()
	done.resize(n)
	_dig_dist[target.y * map.w + target.x] = 0
	var frontier: Array[Vector2i] = [target]
	while not frontier.is_empty():
		var bi := 0
		for i in frontier.size():
			var f := frontier[i]
			if _dig_dist[f.y * map.w + f.x] < _dig_dist[frontier[bi].y * map.w + frontier[bi].x]:
				bi = i
		var c := frontier[bi]
		frontier.remove_at(bi)
		var ci := c.y * map.w + c.x
		if done[ci]:
			continue
		done[ci] = 1
		for d in DIRS:
			var nb := c + d
			if not map.inside(nb) or at(nb) == T.STONE or apple_at(nb) >= 0:
				continue
			var ni := nb.y * map.w + nb.x
			var cost := 1 if at(nb) == T.TUNNEL else 3
			if _dig_dist[ci] + cost < _dig_dist[ni]:
				_dig_dist[ni] = _dig_dist[ci] + cost
				frontier.append(nb)


# ------------------------------------------------------------------ contact and death

func _touch() -> void:
	if phase != Phase.PLAY:
		return
	var pp := pos_of(player)
	for m in monsters:
		if pos_of(m).distance_to(pp) < HIT_RADIUS:
			_die("monster")
			return


func _die(why: String) -> void:
	if phase != Phase.PLAY:
		return
	lives -= 1
	ball = {}
	event.emit("death", {"pos": pos_of(player), "why": why, "lives": lives})
	_set_phase(Phase.DYING, DYING_SECONDS)
