class_name BrawlEngine
extends RefCounted
## Rules of Neon Knuckles (inspired by Double Dragon, 1987): a side-scrolling street brawl in 2.5D. Fighters move
## along the street (x) and in depth (z), jump (y), punch, kick, grab and throw. Waves of enemies lock the screen
## until they are down, then the street opens ("GO"). One or two players. Pure logic, fixed ticks, seeded.
## Our own tuning throughout; the original's moves and timings are still to be checked.

signal event(kind: String, data: Dictionary)  ## "swing", "hit", "block", "knockdown", "grab", "throw", "pickup",
## "weapon_break", "ko", "spawn", "wave", "go", "player_down", "stage_clear", "game_over"

enum S { IDLE, WALK, JUMP, ATTACK, HITSTUN, DOWN, GETUP, GRABBED, GRABBING, THROWN, DEAD }
enum Phase { PLAY, CLEAR, GAME_OVER }

const TICK := 1.0 / 60.0
const DEPTH := Vector2(-2.2, 2.2)  ## the street's depth band (z)
const WALK := 3.2
const DEPTH_WALK := 2.2
const JUMP_V := 6.5
const GRAVITY := 18.0
const HIT_DEPTH := 0.45  ## attacks connect only within this depth difference
const INVULN := 1.2  ## after getting up
const LIVES := 3
const HP := 100

## attack data: startup (s), active window (s), recovery (s), reach (m, from the body), damage, knockback (m/s),
## knockdown (bool), hitstun (s)
const ATTACKS := {
	"jab": [0.06, 0.08, 0.12, 0.9, 6, 0.6, false, 0.3],
	"punch": [0.08, 0.08, 0.16, 1.0, 8, 0.8, false, 0.35],
	"hook": [0.12, 0.1, 0.3, 1.1, 14, 4.0, true, 0.6],
	"kick": [0.12, 0.1, 0.25, 1.3, 11, 3.0, false, 0.45],
	"jump_kick": [0.05, 0.3, 0.1, 1.2, 16, 5.0, true, 0.6],
	"knee": [0.08, 0.06, 0.18, 0.7, 9, 0.0, false, 0.4],
	"elbow": [0.1, 0.1, 0.25, 1.0, 12, 3.5, true, 0.5],
	"bat": [0.15, 0.12, 0.3, 1.6, 20, 5.0, true, 0.6],
	"knife": [0.08, 0.08, 0.15, 1.1, 14, 1.0, false, 0.4],
	"charge": [0.3, 0.5, 0.4, 1.3, 18, 6.0, true, 0.7],
	"crate": [0.2, 0.12, 0.35, 1.4, 22, 6.0, true, 0.6],
}
const ENEMY_KINDS := {
	"thug": {"hp": 40, "speed": 2.4, "attacks": ["punch", "kick"], "think": 0.9},
	"knifer": {"hp": 35, "speed": 2.8, "attacks": ["knife"], "think": 0.7, "weapon": "knife"},
	"bruiser": {"hp": 110, "speed": 1.8, "attacks": ["hook", "charge"], "think": 1.3},
	"boss": {"hp": 220, "speed": 2.2, "attacks": ["hook", "kick", "charge"], "think": 0.8},
}

var level: BrawlLevel
var rng := RandomNumberGenerator.new()
var phase := Phase.PLAY
var time := 0.0
var fighters: Array[Dictionary] = []
var items: Array[Dictionary] = []  ## weapons on the ground: {kind, pos: Vector3, id}
var scroll := 0.0  ## left edge of the view (m)
var lock_right := 0.0  ## the view can't scroll past this until the wave is down
var wave := 0
var score := 0
var view_width := 16.0
var _next_id := 1
var _input := {}  ## player index -> {dir: Vector2, attack: bool, jump: bool, pick: bool}


func _init(lv: BrawlLevel = null, players := 1, seed := 1) -> void:
	rng.seed = seed
	if lv == null:
		return
	level = lv
	for i in players:
		fighters.append(_fighter("player", Vector3(2.0 + i * 1.2, 0, -0.6 + i * 1.2), i))
	for it in lv.items:
		items.append({"kind": it["kind"], "pos": Vector3(it["x"], 0, it["z"]), "id": _id()})
	lock_right = lv.waves[0]["at"] if not lv.waves.is_empty() else lv.length


func _id() -> int:
	_next_id += 1
	return _next_id


func _fighter(kind: String, pos: Vector3, player := -1) -> Dictionary:
	var k: Dictionary = ENEMY_KINDS.get(kind, {"hp": HP, "speed": WALK})
	return {"id": _id(), "kind": kind, "player": player, "pos": pos, "vel": Vector3.ZERO, "facing": 1,
		"hp": k.get("hp", HP), "max_hp": k.get("hp", HP), "state": S.IDLE, "t": 0.0, "attack": "", "hit_done": false,
		"combo": 0, "combo_t": 0.0, "lives": LIVES if player >= 0 else 0, "invuln": 0.0, "weapon": k.get("weapon", ""),
		"think": rng.randf_range(0.2, 1.0), "grab": -1, "knees": 0, "alive": true}


func players() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for f in fighters:
		if f["player"] >= 0:
			out.append(f)
	return out


func enemies() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for f in fighters:
		if f["player"] < 0 and f["alive"]:
			out.append(f)
	return out


func by_id(id: int) -> Dictionary:
	for f in fighters:
		if f["id"] == id:
			return f
	return {}


## The game sets each player's input every tick: dir (x along the street, y in depth), and presses.
func set_input(player: int, dir: Vector2, attack: bool, jump: bool, pick := false) -> void:
	_input[player] = {"dir": dir, "attack": attack, "jump": jump, "pick": pick}


# ------------------------------------------------------------------ tick

func tick() -> void:
	if phase == Phase.GAME_OVER:
		return
	time += TICK
	for f in fighters:
		if f["alive"]:
			if f["player"] >= 0:
				_player_control(f)
			else:
				_ai(f)
			_physics(f)
	_hits()
	_waves()
	_scroll()
	_input.clear()


func _can_act(f: Dictionary) -> bool:
	return f["state"] in [S.IDLE, S.WALK]


func _player_control(f: Dictionary) -> void:
	var inp: Dictionary = _input.get(f["player"], {"dir": Vector2.ZERO, "attack": false, "jump": false, "pick": false})
	f["combo_t"] -= TICK
	if f["state"] == S.GRABBING:
		var g := by_id(f["grab"])
		if g.is_empty() or g["state"] != S.GRABBED:
			f["state"] = S.IDLE
		elif inp["attack"]:
			if inp["dir"].x * f["facing"] < -0.5:  # pull back and throw
				_throw(f, g)
			else:
				_start_attack(f, "knee")
				f["knees"] += 1
		return
	if not _can_act(f):
		return
	var d: Vector2 = inp["dir"]
	if inp["pick"] or (inp["attack"] and f["weapon"] == "" and _item_near(f) >= 0 and d == Vector2.ZERO):
		var i := _item_near(f)
		if i >= 0:
			f["weapon"] = items[i]["kind"]
			event.emit("pickup", {"id": f["id"], "kind": items[i]["kind"]})
			items.remove_at(i)
			return
	if inp["jump"]:
		f["state"] = S.JUMP
		f["vel"] = Vector3(d.x * WALK, JUMP_V, d.y * DEPTH_WALK)
		return
	if inp["attack"]:
		# a grab when walking into a staggered enemy, else the combo: jab, punch, hook (or the weapon)
		var near := _enemy_in_reach(f, 0.8)
		if not near.is_empty() and near["state"] == S.HITSTUN and f["weapon"] == "" and d.x * f["facing"] > 0.5:
			f["state"] = S.GRABBING
			f["grab"] = near["id"]
			f["knees"] = 0
			near["state"] = S.GRABBED
			near["t"] = 2.0
			event.emit("grab", {"id": f["id"], "target": near["id"]})
			return
		if d.x * f["facing"] < -0.5 and f["weapon"] == "":
			_start_attack(f, "elbow")  # a back elbow at whoever is behind
			return
		if f["weapon"] != "":
			_start_attack(f, f["weapon"])
			return
		var chain := ["jab", "punch", "hook"]
		var k: int = f["combo"] if f["combo_t"] > 0.0 else 0
		_start_attack(f, chain[mini(k, 2)])
		f["combo"] = (k + 1) % 3
		f["combo_t"] = 0.5
		return
	if d != Vector2.ZERO:
		f["state"] = S.WALK
		if d.x != 0.0:
			f["facing"] = 1 if d.x > 0.0 else -1
		f["vel"] = Vector3(d.x * WALK, 0, d.y * DEPTH_WALK)
	else:
		f["state"] = S.IDLE
		f["vel"] = Vector3.ZERO


func _item_near(f: Dictionary) -> int:
	for i in items.size():
		var p: Vector3 = items[i]["pos"]
		if absf(p.x - f["pos"].x) < 0.7 and absf(p.z - f["pos"].z) < 0.5:
			return i
	return -1


func _enemy_in_reach(f: Dictionary, reach: float) -> Dictionary:
	for o in fighters:
		if o["alive"] and o["player"] < 0 != (f["player"] < 0) and o["state"] != S.DOWN:
			var dx: float = (o["pos"].x - f["pos"].x) * f["facing"]
			if dx > 0.0 and dx < reach and absf(o["pos"].z - f["pos"].z) < HIT_DEPTH:
				return o
	return {}


func _start_attack(f: Dictionary, name: String) -> void:
	f["state"] = S.ATTACK
	f["attack"] = name
	f["t"] = 0.0
	f["hit_done"] = false
	f["vel"] = Vector3.ZERO if name != "charge" else Vector3(f["facing"] * 6.0, 0, 0)
	event.emit("swing", {"id": f["id"], "attack": name})


func _throw(f: Dictionary, g: Dictionary) -> void:
	f["state"] = S.ATTACK
	f["attack"] = "knee"
	f["t"] = 0.1
	f["hit_done"] = true
	f["facing"] = -f["facing"]
	g["state"] = S.THROWN
	g["vel"] = Vector3(f["facing"] * 7.0, 4.5, 0)
	g["pos"] = f["pos"] + Vector3(f["facing"] * 0.6, 0.6, 0)
	g["thrown_by"] = f["id"]
	_damage(g, 18, f)
	event.emit("throw", {"id": f["id"], "target": g["id"]})


func _physics(f: Dictionary) -> void:
	f["invuln"] = maxf(0.0, f["invuln"] - TICK)
	match f["state"]:
		S.JUMP, S.THROWN:
			f["vel"].y -= GRAVITY * TICK
			f["pos"] += f["vel"] * TICK
			if f["pos"].y <= 0.0:
				f["pos"].y = 0.0
				if f["state"] == S.THROWN:
					_knock_down(f)
					event.emit("slam", {"pos": f["pos"], "id": f["id"]})
				else:
					f["state"] = S.IDLE
					f["vel"] = Vector3.ZERO
			if f["state"] == S.JUMP and _input.get(f["player"], {}).get("attack", false) and f["attack"] != "jump_kick":
				var v: Vector3 = f["vel"]
				_start_attack(f, "jump_kick")
				f["state"] = S.JUMP  # the kick happens in the air, keeping the jump's flight
				f["vel"] = v
		S.WALK:
			f["pos"] += f["vel"] * TICK
		S.ATTACK:
			f["t"] += TICK
			var a: Array = ATTACKS[f["attack"]]
			f["pos"] += f["vel"] * TICK
			if f["t"] >= a[0] + a[1] + a[2]:
				f["state"] = S.GRABBING if f["grab"] >= 0 and not by_id(f["grab"]).is_empty() and by_id(f["grab"])["state"] == S.GRABBED else S.IDLE
				f["vel"] = Vector3.ZERO
				if f["attack"] == "knee" and f["knees"] >= 3:
					var g := by_id(f["grab"])
					if not g.is_empty() and g["state"] == S.GRABBED:
						_throw(f, g)
		S.HITSTUN:
			f["t"] -= TICK
			f["pos"] += f["vel"] * TICK
			f["vel"] *= 0.85
			if f["t"] <= 0.0:
				f["state"] = S.IDLE
		S.DOWN:
			f["t"] -= TICK
			f["pos"] += f["vel"] * TICK
			f["vel"] *= 0.9
			if f["t"] <= 0.0:
				if f["hp"] <= 0:
					_ko(f)
				else:
					f["state"] = S.GETUP
					f["t"] = 0.5
		S.GETUP:
			f["t"] -= TICK
			if f["t"] <= 0.0:
				f["state"] = S.IDLE
				f["invuln"] = INVULN
		S.GRABBED:
			f["t"] -= TICK
			if f["t"] <= 0.0:
				f["state"] = S.IDLE  # wriggles free
	# the jump kick lands with the fighter
	if f["state"] == S.JUMP and f["attack"] == "jump_kick":
		f["t"] += TICK
	if f["state"] == S.IDLE and f["attack"] == "jump_kick":
		f["attack"] = ""
	f["pos"].z = clampf(f["pos"].z, DEPTH.x, DEPTH.y)
	f["pos"].x = clampf(f["pos"].x, scroll + 0.4, maxf(scroll + view_width - 0.4, scroll + 0.5)) if f["player"] >= 0 else f["pos"].x


func _hits() -> void:
	for f in fighters:
		if not f["alive"] or f["attack"] == "" or f["hit_done"]:
			continue
		var active := false
		var a: Array = ATTACKS[f["attack"]]
		if f["state"] == S.ATTACK:
			active = f["t"] >= a[0] and f["t"] <= a[0] + a[1]
		elif f["state"] == S.JUMP and f["attack"] == "jump_kick":
			active = f["t"] >= a[0] and f["t"] <= a[0] + a[1]
		if not active:
			continue
		for o in fighters:
			if not o["alive"] or o == f or (o["player"] >= 0) == (f["player"] >= 0):
				continue
			if o["state"] in [S.DOWN, S.GETUP, S.THROWN, S.DEAD] or o["invuln"] > 0.0:
				continue
			if o["state"] == S.GRABBED and f["attack"] != "knee":
				continue
			var dx: float = (o["pos"].x - f["pos"].x) * f["facing"]
			var reach: float = a[3]
			if f["attack"] == "elbow":
				dx = -dx  # the elbow strikes behind
			if dx > -0.2 and dx < reach and absf(o["pos"].z - f["pos"].z) < HIT_DEPTH and absf(o["pos"].y - f["pos"].y) < 1.2:
				f["hit_done"] = true
				_damage(o, a[4], f)
				var dir: float = f["facing"] * (-1.0 if f["attack"] == "elbow" else 1.0)
				if a[6] or o["hp"] <= 0:
					o["vel"] = Vector3(dir * a[5], 0, 0)
					_knock_down(o)
				elif o["state"] != S.GRABBED:
					o["state"] = S.HITSTUN
					o["t"] = a[7]
					o["vel"] = Vector3(dir * a[5], 0, 0)
				event.emit("hit", {"id": f["id"], "target": o["id"], "attack": f["attack"], "pos": o["pos"] + Vector3(0, 1.3, 0),
					"damage": a[4]})
				if (f["weapon"] == "bat" and rng.randf() < 0.15) or f["weapon"] == "crate":
					event.emit("weapon_break", {"id": f["id"], "kind": f["weapon"]})
					f["weapon"] = ""
				break


func _damage(o: Dictionary, amount: int, by: Dictionary) -> void:
	o["hp"] -= amount
	if by["player"] >= 0:
		score += amount * 10


func _knock_down(f: Dictionary) -> void:
	f["state"] = S.DOWN
	f["t"] = 1.0 if f["hp"] > 0 else 1.4
	if f["grab"] >= 0:
		f["grab"] = -1
	if f["weapon"] != "":  # the weapon clatters to the ground
		items.append({"kind": f["weapon"], "pos": f["pos"] + Vector3(f["facing"] * -0.5, 0, 0), "id": _id()})
		f["weapon"] = ""
	event.emit("knockdown", {"id": f["id"], "pos": f["pos"]})


func _ko(f: Dictionary) -> void:
	if f["player"] >= 0:
		f["lives"] -= 1
		event.emit("player_down", {"id": f["id"], "lives": f["lives"]})
		if f["lives"] > 0:
			f["hp"] = f["max_hp"]
			f["state"] = S.GETUP
			f["t"] = 0.8
			return
		f["alive"] = false
		f["state"] = S.DEAD
		if players().filter(func(p): return p["alive"]).is_empty():
			phase = Phase.GAME_OVER
			event.emit("game_over", {"score": score})
		return
	f["alive"] = false
	f["state"] = S.DEAD
	score += 500 if f["kind"] == "boss" else 100
	event.emit("ko", {"id": f["id"], "kind": f["kind"], "pos": f["pos"]})


# ------------------------------------------------------------------ enemies

func _ai(f: Dictionary) -> void:
	if not _can_act(f):
		return
	var k: Dictionary = ENEMY_KINDS[f["kind"]]
	var target := {}
	var best := INF
	for p in players():
		if p["alive"]:
			var d: float = Vector2(p["pos"].x, p["pos"].z).distance_to(Vector2(f["pos"].x, f["pos"].z))
			if d < best:
				best = d
				target = p
	if target.is_empty():
		f["state"] = S.IDLE
		f["vel"] = Vector3.ZERO
		return
	var dx: float = target["pos"].x - f["pos"].x
	var dz: float = target["pos"].z - f["pos"].z
	f["facing"] = 1 if dx > 0.0 else -1
	f["think"] -= TICK
	var in_reach := absf(dx) < 1.1 and absf(dz) < HIT_DEPTH * 0.8
	if in_reach and f["think"] <= 0.0:
		f["think"] = k["think"] * rng.randf_range(0.7, 1.4)
		var atk: Array = k["attacks"]
		_start_attack(f, atk[rng.randi_range(0, atk.size() - 1)])
		return
	if f["kind"] in ["bruiser", "boss"] and absf(dx) > 3.0 and absf(dz) < 0.3 and f["think"] <= 0.0 and rng.randf() < 0.02:
		f["think"] = k["think"] * 2.0
		_start_attack(f, "charge")
		return
	# approach to a spot beside the target, lined up in depth; hang back a little when others are closer
	var want := Vector3(target["pos"].x - signf(dx) * 0.9, 0, target["pos"].z)
	var crowd := 0
	for o in enemies():
		if o != f and Vector2(o["pos"].x, o["pos"].z).distance_to(Vector2(target["pos"].x, target["pos"].z)) < best:
			crowd += 1
	if crowd >= 2:
		want.x = target["pos"].x - signf(dx) * 3.0
	var mv := Vector3(want.x - f["pos"].x, 0, want.z - f["pos"].z)
	if mv.length() > 0.15:
		f["state"] = S.WALK
		f["vel"] = Vector3(signf(mv.x) * minf(absf(mv.x) * 3.0, k["speed"]), 0, signf(mv.z) * minf(absf(mv.z) * 3.0, k["speed"] * 0.7))
	else:
		f["state"] = S.IDLE
		f["vel"] = Vector3.ZERO


# ------------------------------------------------------------------ waves and scrolling

func _waves() -> void:
	if phase != Phase.PLAY:
		return
	var alive := enemies().size()
	if wave < level.waves.size():
		var w: Dictionary = level.waves[wave]
		var lead := _lead_x()
		if not w.get("spawned", false) and lead + view_width * 0.5 >= w["at"]:
			w["spawned"] = true
			for e in w["enemies"]:
				var side: float = 1.0 if e.get("side", "right") == "right" else -1.0
				var x: float = scroll + (view_width + 1.0 if side > 0.0 else -1.0)
				var f := _fighter(e["kind"], Vector3(x, 0, rng.randf_range(DEPTH.x, DEPTH.y)))
				fighters.append(f)
				event.emit("spawn", {"id": f["id"], "kind": e["kind"]})
			lock_right = w["at"] + view_width * 0.5
			event.emit("wave", {"wave": wave})
		elif w.get("spawned", false) and alive == 0:
			wave += 1
			lock_right = level.waves[wave]["at"] + view_width * 0.5 if wave < level.waves.size() else level.length
			event.emit("go", {"wave": wave})
	elif alive == 0:
		phase = Phase.CLEAR
		event.emit("stage_clear", {"score": score})


func _lead_x() -> float:
	var x := -INF
	for p in players():
		if p["alive"]:
			x = maxf(x, p["pos"].x)
	return x


func _scroll() -> void:
	var lead := _lead_x()
	if lead == -INF:
		return
	var target := lead - view_width * 0.45
	scroll = clampf(maxf(scroll, target), 0.0, maxf(0.0, lock_right - view_width))
