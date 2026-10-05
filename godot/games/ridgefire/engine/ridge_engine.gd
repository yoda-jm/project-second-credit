class_name RidgeEngine
extends RefCounted
## Ridgefire rules (turn-based artillery in the Scorched Earth tradition; our own tuning), 60 Hz ticks. A side-view
## arena 96 m wide: the ground is a height per column (0.25 m apart), so earth never overhangs: a blast carves a hole
## and whatever was above it falls in. Two to four tanks take turns: aim (an angle, 0 right to 180 left), a power, a
## weapon; the shell flies under gravity and the wind and bursts on the ground or a tank. Blasts hurt tanks by distance;
## a tank whose ground drops falls, and a long fall hurts. A wrecked tank blows up too. The last tank standing wins the
## round (and money); between rounds the money buys weapons. Weapons: shell (endless), heavy, mirv (splits in five at
## the top of its flight), roller (rolls down the slopes to the lowest point before bursting), dirt (heaps earth up),
## digger (bores a tunnel down along its path), nuke; a shield soaks up the next 60 points of harm.
## Events: "turn" {player}, "fire" {player, weapon, pos}, "split" {pos}, "blast" {pos, radius, weapon},
## "dirt" {pos, radius}, "dig" {from, to}, "roll" {pos}, "hit" {player, damage}, "fall" {player, drop}, "die" {player},
## "round_end" {winner}, "wind" {wind}, "shield" {player, left}.

signal event(kind: String, data: Dictionary)

enum Phase { AIM, FLIGHT, SETTLE, ROUND_END, OVER }
const TICK := 1.0 / 60.0
const W := 96.0
const COL := 0.25
const N := 385                  ## columns at x = i * COL
const G := 20.0
const MAX_SPEED := 48.0
const TANK_R := 1.4             ## a tank's hit radius (around its body centre, 0.7 m above its tracks)
const FALL_SAFE := 2.0
const COLOURS := [Color(0.9, 0.25, 0.2), Color(0.25, 0.5, 0.95), Color(0.35, 0.8, 0.3), Color(0.95, 0.75, 0.2)]
const NAMES := ["RED", "BLUE", "GREEN", "GOLD"]
## weapon: blast radius, damage at the centre, shop price for a pack, pack size, name
const WEAPONS := {
	"shell": {"r": 3.0, "dmg": 45, "price": 0, "pack": 0, "name": "SHELL"},
	"heavy": {"r": 5.0, "dmg": 65, "price": 400, "pack": 3, "name": "HEAVY SHELL"},
	"mirv": {"r": 3.0, "dmg": 40, "price": 1200, "pack": 2, "name": "MIRV"},
	"roller": {"r": 4.0, "dmg": 55, "price": 600, "pack": 3, "name": "ROLLER"},
	"dirt": {"r": 5.0, "dmg": 0, "price": 300, "pack": 3, "name": "DIRT BALL"},
	"digger": {"r": 1.6, "dmg": 10, "price": 500, "pack": 3, "name": "DIGGER"},
	"nuke": {"r": 13.0, "dmg": 110, "price": 3000, "pack": 1, "name": "NUKE"},
}
const ORDER := ["shell", "heavy", "mirv", "roller", "dirt", "digger", "nuke"]
const SHIELD_PRICE := 800
const SHIELD := 60.0
const ROUND_WIN := 1500
const KILL := 1000

var heights := PackedFloat32Array()
var players: Array[Dictionary] = []
var turn := 0                   ## the player aiming
var phase := Phase.AIM
var phase_t := 0.0
var round_i := 0
var rounds := 5
var wind := 0.0                 ## m/s² along x
var theme := 0
var shots: Array[Dictionary] = []   ## {pos, vel, weapon, owner, apex (mirv), t, rolling}
var settle_t := 0.0
var time := 0.0
var first_land := 0             ## the land of the first round (the next rounds follow on)
var rng := RandomNumberGenerator.new()
var dirty := true               ## the ground changed (the view rebuilds it)
var winner := -1
var _last_shooter := -1


func _init(count := 3, cpu: Array = [], seed_ := 1, rounds_ := 5) -> void:
	rng.seed = seed_
	rounds = rounds_
	for i in count:
		players.append({"i": i, "name": NAMES[i], "colour": COLOURS[i], "cpu": cpu[i] if i < cpu.size() else true,
			"x": 0.0, "y": 0.0, "angle": 45.0, "power": 60.0, "hp": 100.0, "alive": true, "money": 0, "score": 0,
			"weapon": "shell", "ammo": {"shell": -1}, "fall_v": 0.0, "falling": false, "wins": 0, "shield": 0.0})
	new_round()


# ------------------------------------------------------------------ rounds

func new_round() -> void:
	theme = (round_i + first_land) % 5
	_terrain()
	var n := players.size()
	var slots: Array = []
	for i in n:
		slots.append(W * (0.12 + 0.76 * (i + rng.randf_range(0.15, 0.85)) / n))
	slots.shuffle()
	for i in n:
		var p := players[i]
		p["x"] = clampf(slots[i], 4.0, W - 4.0)
		_flatten(p["x"], 1.8)
		p["y"] = ground(p["x"])
		p["hp"] = 100.0
		p["alive"] = true
		p["falling"] = false
		p["angle"] = 45.0 if p["x"] < W * 0.5 else 135.0
		p["power"] = 60.0
		if not p["ammo"].has(p["weapon"]):
			p["weapon"] = "shell"
	shots.clear()
	winner = -1
	turn = rng.randi() % n
	_new_wind(true)
	phase = Phase.AIM
	phase_t = 0.0
	dirty = true
	event.emit("turn", {"player": turn})


## Rolling hills from a few octaves of waves, a theme's character on top (mesas are terraced, the moon is cratered).
func _terrain() -> void:
	heights.resize(N)
	var waves: Array = []
	for k in 5:
		waves.append([rng.randf_range(0.5, 1.0) * 9.0 / (k + 1), rng.randf_range(1.0, 2.2) * (k + 1), rng.randf() * TAU])
	var base := rng.randf_range(10.0, 16.0)
	for i in N:
		var x := i * COL / W
		var h := base
		for wv in waves:
			h += wv[0] * sin(x * TAU * wv[1] * 0.5 + wv[2])
		match theme:
			0:
				h = lerpf(h, floorf(h / 4.0) * 4.0 + 1.5, 0.75)   # terraces: mesas and buttes
			3:
				h += 6.0 * exp(-pow((x - 0.5) * 6.0, 2.0))         # a volcanic hump in the middle
		heights[i] = clampf(h, 3.0, 34.0)
	if theme == 2:
		for c in 6:
			var cx := rng.randf_range(6.0, W - 6.0)
			_carve(Vector2(cx, ground(cx) + 1.5), rng.randf_range(2.5, 5.0))
	# a little smoothing for the terraces' edges
	var s := heights.duplicate()
	for i in range(1, N - 1):
		heights[i] = (s[i - 1] + s[i] * 2.0 + s[i + 1]) * 0.25


func _flatten(x: float, half: float) -> void:
	var h := ground(x)
	for i in range(_col(x - half), _col(x + half) + 1):
		if i >= 0 and i < N:
			heights[i] = h


func _new_wind(fresh := false) -> void:
	if fresh:
		wind = rng.randf_range(-6.0, 6.0)
	else:
		wind = clampf(wind + rng.randf_range(-1.5, 1.5), -8.0, 8.0)
	event.emit("wind", {"wind": wind})


# ------------------------------------------------------------------ the ground

static func _col(x: float) -> int:
	return int(roundf(x / COL))


## The ground's height at x (between columns, linear).
func ground(x: float) -> float:
	var f := clampf(x / COL, 0.0, N - 1.0)
	var i := int(floorf(f))
	var j := mini(i + 1, N - 1)
	return lerpf(heights[i], heights[j], f - i)


## A blast removes a disc of earth; earth above the disc falls into it (no overhangs).
func _carve(c: Vector2, r: float) -> void:
	for i in range(_col(c.x - r) - 1, _col(c.x + r) + 2):
		if i < 0 or i >= N:
			continue
		var dx := i * COL - c.x
		if absf(dx) >= r:
			continue
		var dy := sqrt(r * r - dx * dx)
		var lo := c.y - dy
		var hi := c.y + dy
		var h := heights[i]
		if h <= lo:
			continue
		heights[i] = maxf(0.0, lo + maxf(0.0, h - hi))
	dirty = true


## A dirt ball heaps a disc of earth, which settles onto the ground below it.
func _heap(c: Vector2, r: float) -> void:
	for i in range(_col(c.x - r) - 1, _col(c.x + r) + 2):
		if i < 0 or i >= N:
			continue
		var dx := i * COL - c.x
		if absf(dx) >= r:
			continue
		var dy := sqrt(r * r - dx * dx)
		var lo := c.y - dy
		var hi := c.y + dy
		var h := heights[i]
		var add := 2.0 * dy if h <= lo else maxf(0.0, hi - h)
		heights[i] = minf(h + add, 45.0)
	dirty = true


# ------------------------------------------------------------------ the turn

func current() -> Dictionary:
	return players[turn]


## The muzzle: from the gun's trunnion (0.6 m forward on the side it aims, 1.15 m up), 1.62 m along the aim.
static func muzzle_at(x: float, y: float, angle: float) -> Vector2:
	var a := deg_to_rad(angle)
	var fwd := 0.6 if angle <= 90.0 else -0.6
	return Vector2(x + fwd, y + 1.15) + Vector2(cos(a), sin(a)) * 1.62


func muzzle(p: Dictionary) -> Vector2:
	return muzzle_at(p["x"], p["y"], p["angle"])


func fire() -> void:
	if phase != Phase.AIM:
		return
	var p := current()
	var wpn: String = p["weapon"]
	var ammo: Dictionary = p["ammo"]
	if int(ammo.get(wpn, 0)) == 0:
		wpn = "shell"
	if int(ammo.get(wpn, 0)) > 0:
		ammo[wpn] = int(ammo[wpn]) - 1
		if int(ammo[wpn]) == 0:
			ammo.erase(wpn)
	if not ammo.has(p["weapon"]):
		p["weapon"] = "shell"
	var a := deg_to_rad(float(p["angle"]))
	var v := Vector2(cos(a), sin(a)) * float(p["power"]) / 100.0 * MAX_SPEED
	shots.append({"pos": muzzle(p), "vel": v, "weapon": wpn, "owner": turn, "t": 0.0, "rolling": false, "split": false})
	_last_shooter = turn
	phase = Phase.FLIGHT
	phase_t = 0.0
	event.emit("fire", {"player": turn, "weapon": wpn, "pos": muzzle(p)})


## Steps one shot through the air (shared with the CPU's aiming). Returns "" while flying, else what stopped it:
## "ground", "tank", "out".
func step_shot(s: Dictionary, collide_tanks := true) -> String:
	var v: Vector2 = s["vel"]
	v.y -= G * TICK
	v.x += wind * TICK
	s["vel"] = v
	var p: Vector2 = s["pos"] + v * TICK
	s["pos"] = p
	s["t"] += TICK
	if p.x < -2.0 or p.x > W + 2.0 or p.y < -5.0:
		return "out"
	if p.y <= ground(p.x):
		return "ground"
	if collide_tanks and s["t"] > 0.15:
		for q in players:
			if q["alive"] and Vector2(q["x"], q["y"] + 0.7).distance_to(p) < TANK_R:
				return "tank"
	return ""


func tick() -> void:
	time += TICK
	phase_t += TICK
	match phase:
		Phase.FLIGHT:
			_fly()
		Phase.SETTLE:
			_settle()
		Phase.ROUND_END:
			pass


func _fly() -> void:
	var done: Array[Dictionary] = []
	for s in shots.duplicate():
		if s["rolling"]:
			_roll(s)
			if s.get("stop", false):
				done.append(s)
			continue
		var was_up: bool = s["vel"].y > 0.0
		var hit := step_shot(s)
		if s["weapon"] == "mirv" and not s["split"] and was_up and s["vel"].y <= 0.0:
			# the top of its flight: five warheads fan out
			s["split"] = true
			event.emit("split", {"pos": s["pos"]})
			for k in [-2, -1, 1, 2]:
				shots.append({"pos": s["pos"], "vel": s["vel"] + Vector2(k * 3.2, 0.0), "weapon": "mirv", "owner": s["owner"],
					"t": s["t"], "rolling": false, "split": true})
		if hit == "":
			continue
		if hit == "out":
			done.append(s)
			continue
		if s["weapon"] == "roller" and hit == "ground":
			s["rolling"] = true
			s["vel"] = Vector2(signf(s["vel"].x) * 2.0, 0.0)
			s["pos"] = Vector2(s["pos"].x, ground(s["pos"].x))
			event.emit("roll", {"pos": s["pos"]})
			continue
		_burst(s)
		done.append(s)
	for s in done:
		shots.erase(s)
		if s["rolling"]:
			_burst(s)
	if shots.is_empty():
		phase = Phase.SETTLE
		phase_t = 0.0
		settle_t = 0.0


## A roller runs down the slope, gathering speed, and stops in a hollow (or against a tank).
func _roll(s: Dictionary) -> void:
	var p: Vector2 = s["pos"]
	var slope := (ground(p.x + 0.3) - ground(p.x - 0.3)) / 0.6
	var v: float = s["vel"].x
	v += -slope * G * 0.6 * TICK
	v *= 1.0 - 0.6 * TICK
	p.x += v * TICK
	p.y = ground(p.x)
	s["pos"] = p
	s["vel"] = Vector2(v, 0)
	s["t"] += TICK
	var stuck: bool = absf(v) < 0.25 and s["t"] > 0.6
	for q in players:
		if q["alive"] and absf(q["x"] - p.x) < 1.6 and absf(q["y"] - p.y) < 1.5:
			stuck = true
	if stuck or p.x < 0.5 or p.x > W - 0.5 or s["t"] > 12.0:
		s["stop"] = true


func _burst(s: Dictionary) -> void:
	var w: Dictionary = WEAPONS[s["weapon"]]
	var c: Vector2 = s["pos"]
	var r: float = w["r"]
	match s["weapon"]:
		"dirt":
			_heap(c, r)
			event.emit("dirt", {"pos": c, "radius": r})
			return
		"digger":
			# bores on down along its path for 9 m, a tunnel of small bites
			var d: Vector2 = (s["vel"] as Vector2).normalized()
			if d.y > -0.3:
				d = (d + Vector2(0, -1)).normalized()
			var from := c
			for k in 12:
				_carve(c + d * k * 0.8, r)
			event.emit("dig", {"from": from, "to": c + d * 9.0})
			_hurt(c + d * 4.0, 2.5, w["dmg"], s["owner"])
			return
	_carve(c, r)
	event.emit("blast", {"pos": c, "radius": r, "weapon": s["weapon"]})
	_hurt(c, r + 1.5, w["dmg"], s["owner"])


func _hurt(c: Vector2, reach: float, dmg: float, owner: int) -> void:
	for q in players:
		if not q["alive"]:
			continue
		var d := Vector2(q["x"], q["y"] + 0.7).distance_to(c)
		if d >= reach:
			continue
		var hurt := dmg * clampf(1.15 - d / reach, 0.0, 1.0)
		if hurt <= 0.5:
			continue
		var soak := minf(float(q["shield"]), hurt)
		q["shield"] = float(q["shield"]) - soak
		hurt -= soak
		if soak > 0.0:
			event.emit("shield", {"player": q["i"], "left": q["shield"]})
		if hurt <= 0.0:
			continue
		q["hp"] = maxf(0.0, q["hp"] - hurt)
		if owner >= 0 and owner != q["i"]:
			players[owner]["money"] += int(hurt * 5.0)
			players[owner]["score"] += int(hurt)
		event.emit("hit", {"player": q["i"], "damage": hurt})


## After the shots: tanks fall onto the ground that is left, wrecks blow up (which may start it all again), then the
## next turn.
func _settle() -> void:
	var busy := false
	for q in players:
		if not q["alive"]:
			continue
		var g := ground(q["x"])
		if q["y"] > g + 0.02:
			if not q["falling"]:
				q["falling"] = true
				q["fall_from"] = q["y"]
				q["fall_v"] = 0.0
			q["fall_v"] += G * TICK
			q["y"] = maxf(g, q["y"] - q["fall_v"] * TICK)
			busy = true
		else:
			q["y"] = g
			if q["falling"]:
				q["falling"] = false
				var drop: float = q["fall_from"] - g
				event.emit("fall", {"player": q["i"], "drop": drop})
				if drop > FALL_SAFE:
					var hurt := (drop - FALL_SAFE) * 4.0
					q["hp"] = maxf(0.0, q["hp"] - hurt)
					event.emit("hit", {"player": q["i"], "damage": hurt})
	if busy:
		return
	for q in players:
		if q["alive"] and q["hp"] <= 0.0:
			q["alive"] = false
			if _last_shooter >= 0 and _last_shooter != q["i"]:
				players[_last_shooter]["money"] += KILL
				players[_last_shooter]["score"] += 100
			event.emit("die", {"player": q["i"]})
			var c := Vector2(q["x"], q["y"] + 0.7)
			_carve(c, 3.5)
			event.emit("blast", {"pos": c, "radius": 3.5, "weapon": "wreck"})
			_hurt(c, 5.0, 30.0, -1)
			return   # settle again after the wreck's blast
	if phase_t < 0.6:
		return   # a beat to see the result
	var alive := players.filter(func(q): return q["alive"])
	if alive.size() <= 1:
		winner = alive[0]["i"] if alive.size() == 1 else -1
		if winner >= 0:
			players[winner]["money"] += ROUND_WIN
			players[winner]["wins"] += 1
			players[winner]["score"] += 300
		phase = Phase.ROUND_END
		phase_t = 0.0
		event.emit("round_end", {"winner": winner})
		return
	_next_turn()


func _next_turn() -> void:
	for k in range(1, players.size() + 1):
		var j := (turn + k) % players.size()
		if players[j]["alive"]:
			turn = j
			break
	_new_wind()
	phase = Phase.AIM
	phase_t = 0.0
	event.emit("turn", {"player": turn})


## The game moves on after a round (the shop is the game's business): the next round, or the end.
func next_round() -> void:
	round_i += 1
	if round_i >= rounds:
		phase = Phase.OVER
		phase_t = 0.0
		return
	new_round()


# ------------------------------------------------------------------ the shop

func buy(i: int, item: String) -> bool:
	var p := players[i]
	if item == "shield":
		if p["money"] < SHIELD_PRICE or float(p["shield"]) >= SHIELD:
			return false
		p["money"] -= SHIELD_PRICE
		p["shield"] = SHIELD
		return true
	var w: Dictionary = WEAPONS[item]
	if int(w["price"]) <= 0 or p["money"] < int(w["price"]):
		return false
	p["money"] -= int(w["price"])
	p["ammo"][item] = int(p["ammo"].get(item, 0)) + int(w["pack"])
	return true


## The weapons a player has, in shop order.
func owned(i: int) -> Array[String]:
	var out: Array[String] = []
	for w in ORDER:
		if players[i]["ammo"].has(w):
			out.append(w)
	return out


func cycle_weapon(step: int) -> void:
	var p := current()
	var o := owned(turn)
	var k := o.find(p["weapon"])
	p["weapon"] = o[posmod(k + step, o.size())]


## Standings: by rounds won, then score.
func standings() -> Array:
	var s := players.duplicate()
	s.sort_custom(func(a, b): return a["wins"] > b["wins"] or (a["wins"] == b["wins"] and a["score"] > b["score"]))
	return s
