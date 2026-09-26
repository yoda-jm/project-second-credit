class_name FlagsAI
extends RefCounted
## The computer general (and the demo's two generals): it thinks twice a second. Idle squads go for the nearest flag
## they don't hold (neutral ones first), squads close to a threatened flag of their own come back to defend it,
## and once the army is big enough the tanks and a few squads push on the enemy fort. Factories build a mix.

const Team = FlagsMap.Team

var team: int
var aggression := 1.0  ## lower waits longer before the push on the fort
var _rng := RandomNumberGenerator.new()
var _claims := {}  ## zone -> group sent to it
var _last_progress := {}  ## building -> progress seen last time (a drop means a unit came out)


func _init(team_: int, seed_: int, aggression_ := 1.0) -> void:
	team = team_
	aggression = aggression_
	_rng.seed = seed_ * 31 + team_


func drive(e: FlagsEngine) -> void:
	if e.ticks % 30 != team * 7 or e.phase != FlagsEngine.Phase.PLAY:
		return
	_factories(e)
	var groups := {}
	for u in e.team_units(team):
		if u["cls"] == "cannon":
			continue
		if not groups.has(u["group"]):
			groups[u["group"]] = []
		groups[u["group"]].append(u)
	# forget claims whose squads are gone or whose flag is ours
	for z in _claims.keys():
		if e.zones[z]["owner"] == team or not groups.has(_claims[z]):
			_claims.erase(z)
	var enemy_fort := e.fort_of(Team.RED if team == Team.BLUE else Team.BLUE)
	var army := 0
	for g in groups:
		army += groups[g].size()
	var push := army >= int(20.0 / aggression) and e.time > 150.0 / aggression
	# the fort under attack: the three nearest squads come home, whatever they were doing
	var home := e.fort_of(team)
	var defenders := {}
	if not home.is_empty():
		var hc := e._center(home)
		var raider := _threat(e, hc, 11.0)
		if raider >= 0:
			var order := groups.keys()
			order.sort_custom(func(a, b): return groups[a][0]["pos"].distance_to(hc) < groups[b][0]["pos"].distance_to(hc))
			for g in order.slice(0, 3):
				var gm: Array = groups[g]
				if gm[0]["order"] == "attack" and gm[0]["forced"] >= 0 and e.by_id(gm[0]["forced"]).get("pos", Vector2(-99, -99)).distance_to(hc) < 12.0:
					defenders[g] = true
					continue
				e.order_attack(gm.map(func(u): return u["id"]), raider)
				defenders[g] = true
	for g in groups:
		var members: Array = groups[g]
		var lead: Dictionary = members[0]
		if defenders.has(g) or _busy(members):
			continue
		var ids: Array = members.map(func(u): return u["id"])
		var is_robot: bool = lead["cls"] == "robot"
		var threat := _threat(e, lead["pos"])
		if threat >= 0 and _rng.randf() < 0.7:
			e.order_attack(ids, threat)
			continue
		if is_robot:
			var z := _pick_zone(e, lead["pos"], g)
			if z >= 0 and not (push and _rng.randf() < 0.35):
				_claims[z] = g
				e.order_move(ids, e.zones[z]["flag"], false)
				continue
		# vehicles, and squads with nothing left to take: the fort when the army is big, else the front line
		if (push or not is_robot and army > 8) and not enemy_fort.is_empty():
			e.order_attack(ids, enemy_fort["id"])
		else:
			var front := _front(e, lead["pos"])
			if front.x >= 0:
				e.order_move(ids, front, false)


func _busy(members: Array) -> bool:
	for u in members:
		if u["moving"] or u["order"] == "attack" or u["target"] >= 0:
			return true
	return false


## An enemy close to one of our flags or to this squad.
func _threat(e: FlagsEngine, pos: Vector2, reach := 9.0) -> int:
	var best := -1
	var bd := reach
	for o in e.units:
		if o["dead"] or o["team"] == team or o["team"] == Team.NEUTRAL or o["cls"] == "cannon":
			continue
		var d: float = o["pos"].distance_to(pos)
		if d < bd:
			bd = d
			best = o["id"]
	return best


func _pick_zone(e: FlagsEngine, pos: Vector2, group: int) -> int:
	var best := -1
	var bs := INF
	for i in e.zones.size():
		var z: Dictionary = e.zones[i]
		if z["owner"] == team or z["flag"].x < 0:
			continue
		if _claims.has(i) and _claims[i] != group:
			continue
		var s := pos.distance_to(Vector2(z["flag"])) - (6.0 if z["owner"] == Team.NEUTRAL else 0.0) + _rng.randf_range(0.0, 4.0)
		if s < bs:
			bs = s
			best = i
	return best


## The nearest flag of ours that borders enemy ground: where idle vehicles wait.
func _front(e: FlagsEngine, pos: Vector2) -> Vector2i:
	var enemy := Team.RED if team == Team.BLUE else Team.BLUE
	var best := Vector2i(-1, -1)
	var bd := INF
	for z in e.zones:
		if z["owner"] != team or z["flag"].x < 0:
			continue
		var near_enemy := INF
		for o in e.zones:
			if o["owner"] == enemy and o["flag"].x >= 0:
				near_enemy = minf(near_enemy, Vector2(o["flag"]).distance_to(Vector2(z["flag"])))
		var d := near_enemy + pos.distance_to(Vector2(z["flag"])) * 0.3
		if d < bd:
			bd = d
			best = z["flag"] + Vector2i(_rng.randi_range(-2, 2), _rng.randi_range(1, 3))
	return best


func _factories(e: FlagsEngine) -> void:
	var zones := e.zones_owned(team)
	for b in e.buildings:
		if b["team"] != team:
			continue
		var fresh: bool = b["progress"] < _last_progress.get(b["id"], 2.0)
		_last_progress[b["id"]] = b["progress"]
		if not fresh:
			continue
		match b["kind"]:
			"robot_factory", "fort":
				var pick := ["grunt", "grunt", "psycho", "psycho", "tough", "sniper"]
				if zones >= 4:
					pick.append_array(["pyro", "laser", "tough"])
				e.set_build(b["id"], pick[_rng.randi_range(0, pick.size() - 1)])
			"vehicle_factory":
				var pick := ["jeep", "tank_light", "tank_light"]
				if zones >= 4:
					pick.append_array(["tank_medium", "tank_medium", "apc"])
				if zones >= 6:
					pick.append_array(["tank_heavy", "missile_launcher"])
				e.set_build(b["id"], pick[_rng.randi_range(0, pick.size() - 1)])
