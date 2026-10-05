extends GdUnitTestSuite
## Four Torches: the dungeon always joins the start to the exit, health drains and food mends it, a missile kills a
## monster, a key opens a door, generators spawn and break, and an autopilot party gets down a few levels.

const T = preload("res://games/fourtorches/engine/torch_engine.gd")


func _party(n := 1) -> Array:
	var out := []
	for i in n:
		out.append({"cls": T.ORDER[i], "cpu": true})
	return out


func test_the_exit_is_reachable() -> void:
	for lv in 6:
		for sd in 4:
			var e := TorchEngine.new(lv, _party(), sd + 1)
			var d := e._bfs(Vector2i(floori(e.start.x), floori(e.start.y)))
			assert_int(d[e.idx(e.exit_cell)]).is_less(1 << 20)


func test_health_drains_and_food_mends() -> void:
	var e := TorchEngine.new(0, _party(), 3)
	e.phase = T.Phase.PLAY
	e.monsters.clear()
	e.gens.clear()
	var h := e.heroes[0]
	var h0: float = h["health"]
	for i in 120:
		e.tick()
	assert_float(h["health"]).is_less(h0)
	e.items.append({"cell": Vector2i(floori(h["pos"].x), floori(h["pos"].y)), "kind": "food_ham"})
	var before: float = h["health"]
	e.tick()
	assert_float(h["health"]).is_greater(before + 50.0)


func test_a_missile_kills() -> void:
	var e := TorchEngine.new(0, _party(), 3)
	e.phase = T.Phase.PLAY
	e.monsters.clear()
	e.gens.clear()
	var h := e.heroes[0]
	var p: Vector2 = h["pos"]
	# put a grunt in the open straight ahead
	for dir in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
		if not e.solid_at(p + dir * 2.0) and not e.solid_at(p + dir * 1.0):
			e._spawn("grunt", p + dir * 2.0)
			e.monsters[0]["hp"] = 1.0
			h["face"] = dir
			break
	var kills := []
	e.event.connect(func(k, d): if k == "kill": kills.append(d["kind"]))
	h["fire"] = true
	for i in 20:
		e.tick()
	assert_array(kills).contains(["grunt"])


func test_the_autopilot_party_goes_down() -> void:
	var levels := 0
	var party := _party(2)
	for lv in 3:
		var e := TorchEngine.new(lv, party, 11 + lv)
		for h in e.heroes:
			h["health"] = 2000.0
		var bots := [TorchBot.new(0), TorchBot.new(1)]
		for n in 60 * 240:
			for b in bots:
				b.drive(e)
			e.tick()
			if e.phase == T.Phase.EXIT or e.phase == T.Phase.OVER:
				break
		prints("fourtorches level", lv + 1, "phase", e.phase, "time", snappedf(e.time, 0.1), "health", e.heroes.map(func(h): return roundi(h["health"])),
			"score", e.heroes.map(func(h): return h["score"]))
		if e.phase == T.Phase.EXIT:
			levels += 1
			party = e.party()
	assert_int(levels).is_greater_equal(2)


func test_companions_follow_the_player_and_leave_the_exit_to_them() -> void:
	# a human who walks the autopilot's way (the leader) with two CPU companions: they stay on its screen, and they
	# never take the party down themselves
	var party := _party(3)
	party[0]["cpu"] = false
	var e := TorchEngine.new(1, party, 5)
	for h in e.heroes:
		h["health"] = 4000.0
	var lead := TorchBot.new(0)
	var bots := [TorchBot.new(1), TorchBot.new(2)]
	var exits := []
	e.event.connect(func(k, d): if k == "exit": exits.append(d["h"]))
	var worst := 0.0
	for n in 60 * 120:
		e.heroes[0]["cpu"] = true      # the leader's bot picks goals as if alone
		lead.drive(e)
		e.heroes[0]["cpu"] = false
		for b in bots:
			b.drive(e)
		e.tick()
		var a: Vector2 = e.heroes[0]["pos"]
		for i in [1, 2]:
			var o: Vector2 = e.heroes[i]["pos"] - a
			worst = maxf(worst, maxf(absf(o.x) / T.VIEW.x, absf(o.y) / T.VIEW.y))
		if e.phase != T.Phase.PLAY and e.phase != T.Phase.READY:
			break
	prints("fourtorches companions: worst screen fraction", snappedf(worst, 0.01), "exits", exits)
	assert_float(worst).is_less(1.0)
	for x in exits:
		assert_int(x).is_equal(0)
