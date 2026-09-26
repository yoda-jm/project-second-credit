class_name BastionGame
extends Node
## Runs a Bastion Coast game in real time: fixed 60 Hz ticks of the engine, player input (keys with repeat,
## mouse aiming via the view), the demo autopilot, restarts. The view and HUD read `engine` and its events.
## Campaign mode plays a pack's islands in order (core/packs/pack.gd): hold each for its rounds to sail on to the
## next, with the pack's story cards between; a lost island is tried again (Enter), the score carries on.
## Versus mode (F2, then 2 or 3 players) plays a map of the versus pack: player 1 on the arrows, Space/Enter, Ctrl/R
## and the mouse; player 2 on W A S D (by key position, so Z Q S D on AZERTY), F and G; gamepads move (d-pad or
## stick), act (A) and rotate (B). The demo autopilot plays every player.

signal started(engine: BastionEngine)

const P = BastionEngine.Phase

@export_file("*.map") var map_file := "res://games/bastion/packs/the-coastline/first-shore.map"

var engine: BastionEngine
var demo := false
var demo_locked := false  ## captures: the demo cannot be taken over by input
var view: Node  ## set by the view: provides screen_to_cell(Vector2) -> Vector2 (or null)
var game_over_time := 0.0
var _acc := 0.0
var _repeat_dir := Vector2.ZERO
var _repeat_t := 0.0
var _bot_t := 0.0
var _bot_plan := {}
var _seed := 1
# campaign
var pack: Pack
var island := 0
var banked := 0  ## score of the islands already held
var story_open := false
var campaign_done := false
var _cards_seen := {}
# versus
var versus := 0  ## players in a versus match (0: the solo game)
var versus_map := ""
var choosing := false  ## the versus chooser is open (2 or 3 players)
var choose_count := 2
var _vs_next := 0  ## rotates through the versus maps from one match to the next
var _pads := {}  ## gamepad device -> player
var _rep_dir: Array[Vector2] = [Vector2.ZERO, Vector2.ZERO, Vector2.ZERO]
var _rep_t: Array[float] = [0.0, 0.0, 0.0]
var _bot_ts: Array[float] = [0.0, 0.0, 0.0]
var _bot_rng := RandomNumberGenerator.new()
var _bot_focus: Array[Vector2] = [Vector2(-1, -1), Vector2(-1, -1), Vector2(-1, -1)]

const VERSUS_PACK := "versus"
const P2_KEYS := [KEY_W, KEY_S, KEY_A, KEY_D]  ## physical: up, down, left, right
const P2_ACT := KEY_F
const P2_ROTATE := KEY_G
const PLAYER_COLORS: Array[Color] = [Color(0.3, 0.62, 1.0), Color(1.0, 0.32, 0.25), Color(1.0, 0.8, 0.2)]
const PLAYER_NAMES: Array[String] = ["BLUE", "RED", "GOLD"]


func start(seed: int = -1) -> void:
	_seed = seed if seed >= 0 else randi()
	if versus > 1:
		_start_versus()
		return
	if pack:
		_start_island()
		return
	engine = BastionEngine.new(CoastMap.load_file(map_file), _seed)
	game_over_time = 0.0
	_bot_plan = {}
	started.emit(engine)


func start_campaign(p: Pack, seed: int = -1) -> void:
	versus = 0
	pack = p
	island = 0
	banked = 0
	campaign_done = false
	_cards_seen.clear()
	start(seed)


func _start_island() -> void:
	for c in get_children():
		if c is StoryCard:
			c.queue_free()
	story_open = false
	engine = BastionEngine.new(CoastMap.load_file(pack.levels[island]), _seed + island * 17)
	game_over_time = 0.0
	_bot_plan = {}
	started.emit(engine)
	var card := pack.card_before(island)
	if not card.is_empty() and not _cards_seen.has(island):
		_cards_seen[island] = true
		story_open = true
		var c := StoryCard.show_card(self, card, Color(0.4, 0.7, 1.0), 7.0 if demo else 0.0)
		c.closed.connect(func(): story_open = false)


## A versus match for `players` (2 or 3) on the next map of the versus pack made for that many.
func start_versus(players: int, seed: int = -1) -> void:
	versus = clampi(players, 2, 3)
	pack = null
	campaign_done = false
	choosing = false
	var maps := versus_maps(versus)
	versus_map = maps[_vs_next % maps.size()] if not maps.is_empty() else map_file
	_vs_next += 1
	start(seed)


## The versus maps with room for `players`, the ones made for exactly that many first.
static func versus_maps(players: int) -> Array[String]:
	var out: Array[String] = []
	var p := Pack.find("bastion", VERSUS_PACK)
	if p == null:
		return out
	for exact in [true, false]:
		for f in p.levels:
			var n := CoastMap.load_file(f).players
			if (n == players) if exact else (n > players):
				out.append(f)
	return out


func _start_versus() -> void:
	for c in get_children():
		if c is StoryCard:
			c.queue_free()
	story_open = false
	engine = BastionEngine.new(CoastMap.load_file(versus_map), _seed, versus)
	game_over_time = 0.0
	_bot_plan = {}
	_bot_rng.seed = _seed
	for i in 3:
		_rep_dir[i] = Vector2.ZERO
		_bot_ts[i] = 0.3 * i
		_bot_focus[i] = Vector2(-1, -1)
	_assign_pads()
	started.emit(engine)


## Restart what is being played (the pause menu's Restart).
func restart() -> void:
	if versus > 1:
		start_versus(versus)
		_vs_next -= 1  # the same map again
		return
	start()


func total_score() -> int:
	return banked + (engine.score if engine else 0)


func _process(delta: float) -> void:
	if engine == null or story_open:
		return
	if engine.phase == P.GAME_OVER:
		game_over_time += delta
		if versus > 1:
			if demo and game_over_time > 8.0:
				start_versus(versus, _seed + 1)  # the next versus coast
			return
		if pack and engine.won and game_over_time > 4.0 and not campaign_done:
			banked += engine.score
			island += 1
			if island >= pack.levels.size():
				campaign_done = true
				if not pack.outro.is_empty():
					StoryCard.show_card(self, pack.outro, Color(0.4, 0.7, 1.0), 9.0 if demo else 0.0)
				if demo:
					get_tree().create_timer(12.0).timeout.connect(func(): start_campaign(pack, _seed + 1))
			else:
				_start_island()
			return
		if game_over_time > (6.0 if demo else 1e9) and not campaign_done:
			start(_seed + 1)
		return
	if demo and versus > 1:
		for pl in engine.players:
			if pl.alive:
				_bot_versus(pl.index, delta)
	elif demo:
		_bot(delta)
	elif versus > 1:
		for p in versus:
			_held_player(p, delta)
	else:
		_held_keys(delta)
	_acc += delta
	while _acc >= BastionEngine.TICK:
		_acc -= BastionEngine.TICK
		engine.tick()


# ------------------------------------------------------------------ player input

## Versus input and the chooser are read here, before the pause menu, so a gamepad's B (rotate) does not pause.
func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F2:
		choosing = not choosing
		get_viewport().set_input_as_handled()
		return
	if choosing:
		_chooser_input(event)
		return
	if engine == null or versus <= 1:
		return
	if engine.phase == P.GAME_OVER:
		if not demo and _is_confirm(event):
			start_versus(versus)  # a rematch on the next coast
			get_viewport().set_input_as_handled()
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and not event.is_action("ui_cancel") \
				and (event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton):
			demo = false  # a key press takes over: the same match for real players
			start_versus(versus)
			get_viewport().set_input_as_handled()
		return
	if _versus_event(event):
		get_viewport().set_input_as_handled()


func _chooser_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	get_viewport().set_input_as_handled()
	if event is InputEventKey:
		match event.physical_keycode:
			KEY_2, KEY_KP_2:
				choose_count = 2
				_choose()
				return
			KEY_3, KEY_KP_3:
				choose_count = 3
				_choose()
				return
			KEY_ESCAPE:
				choosing = false
				return
	if event.is_action("ui_left") or event.is_action("ui_right") or event.is_action("ui_up") or event.is_action("ui_down"):
		choose_count = 5 - choose_count
	elif event.is_action("ui_accept"):
		_choose()
	elif event.is_action("ui_cancel"):
		choosing = false


func _choose() -> void:
	choosing = false
	demo = false
	start_versus(choose_count)


func _is_confirm(event: InputEvent) -> bool:
	if not event.is_pressed() or event.is_echo():
		return false
	if event is InputEventKey:
		return event.keycode in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE]
	return event is InputEventJoypadButton and event.button_index == JOY_BUTTON_A


## One versus input event: returns true when it was a player's.
func _versus_event(event: InputEvent) -> bool:
	if event is InputEventMouseMotion and view != null:
		var c = view.screen_to_cell(event.position)
		if c != null:
			_aim_player(0, c)
		return true
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			engine.act(0)
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			engine.rotate_piece(0)
		return true
	if not event.is_pressed() or event.is_echo():
		return false
	if event is InputEventKey:
		if event.keycode in [KEY_SPACE, KEY_ENTER, KEY_KP_ENTER]:
			engine.act(0)
			return true
		if event.keycode in [KEY_CTRL, KEY_R, KEY_X]:
			engine.rotate_piece(0)
			return true
		if event.physical_keycode == P2_ACT and versus >= 2:
			engine.act(1)
			return true
		if event.physical_keycode == P2_ROTATE and versus >= 2:
			engine.rotate_piece(1)
			return true
		return event.keycode in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT] or event.physical_keycode in P2_KEYS
	if event is InputEventJoypadButton:
		var p: int = _pads.get(event.device, -1)
		if p < 0:
			return false
		if event.button_index == JOY_BUTTON_A:
			engine.act(p)
			return true
		if event.button_index == JOY_BUTTON_B:
			engine.rotate_piece(p)
			return true
		return event.button_index in [JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT]
	return false


## Gamepads to players: with a pad for everyone, pad 1 is player 1 and so on; with fewer, they go to the last
## players (the keyboard can only hold two), so a third player always has one.
func _assign_pads() -> void:
	_pads.clear()
	var pads := Input.get_connected_joypads()
	var first := 0 if pads.size() >= versus else versus - pads.size()
	for i in pads.size():
		if first + i < versus:
			_pads[pads[i]] = first + i


## The direction player `p` holds now (keys, d-pad or stick).
func _held_dir(p: int) -> Vector2:
	var d := Vector2.ZERO
	if p == 0:
		d = Vector2(float(Input.is_key_pressed(KEY_RIGHT)) - float(Input.is_key_pressed(KEY_LEFT)),
			float(Input.is_key_pressed(KEY_DOWN)) - float(Input.is_key_pressed(KEY_UP)))
	elif p == 1:
		d = Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)),
			float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
	for dev in _pads:
		if _pads[dev] != p:
			continue
		var pad := Vector2(float(Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_RIGHT)) - float(Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_LEFT)),
			float(Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_DOWN)) - float(Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_UP)))
		var stick := Vector2(Input.get_joy_axis(dev, JOY_AXIS_LEFT_X), Input.get_joy_axis(dev, JOY_AXIS_LEFT_Y))
		if stick.length() > 0.5:
			pad += Vector2(signf(stick.x) if absf(stick.x) > 0.4 else 0.0, signf(stick.y) if absf(stick.y) > 0.4 else 0.0)
		d += pad
	return d.clamp(-Vector2.ONE, Vector2.ONE)


## Versus movement: smooth aiming in battle, else a step on press and a repeat while held.
func _held_player(p: int, delta: float) -> void:
	if not engine.players[p].alive:
		return
	var d := _held_dir(p)
	if engine.phase == P.BATTLE:
		if d != Vector2.ZERO:
			engine.move_cursor(d.normalized() * 16.0 * delta, p)
		_rep_dir[p] = Vector2.ZERO
		return
	if d == Vector2.ZERO:
		_rep_dir[p] = Vector2.ZERO
		return
	if d != _rep_dir[p]:
		_rep_dir[p] = d
		_rep_t[p] = 0.28
		_step_cursor(d, p)
		return
	_rep_t[p] -= delta
	if _rep_t[p] <= 0.0:
		_step_cursor(d, p)
		_rep_t[p] = 0.07


## Puts player `p`'s cursor under a map point (the mouse): the piece or cannon centred on it, the aim point in battle.
func _aim_player(p: int, c: Vector2) -> void:
	var pl := engine.players[p]
	pl.cursor = c if engine.phase == P.BATTLE else Vector2(roundf(c.x - _piece_center(p).x), roundf(c.y - _piece_center(p).y))


func _unhandled_input(event: InputEvent) -> void:
	if versus > 1:
		return
	if pack and engine and engine.phase == P.GAME_OVER and not demo and event.is_action_pressed("ui_accept"):
		if campaign_done:
			start_campaign(pack)  # the whole coastline again
		elif not engine.won:
			start(_seed + 1)  # the fallen island, again
		return
	if engine == null or demo:
		if demo and not demo_locked and event.is_pressed() and not event.is_echo() \
				and (event is InputEventKey or event is InputEventMouseButton):
			if not event.is_action("ui_cancel"):
				demo = false  # a key press takes over
				if pack:
					start_campaign(pack)
				else:
					start()
		return
	if event is InputEventMouseMotion and view != null:
		var c = view.screen_to_cell(event.position)
		if c != null:
			engine.cursor = c if engine.phase == P.BATTLE else Vector2(roundf(c.x - _piece_center().x), roundf(c.y - _piece_center().y))
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			engine.act()
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			engine.rotate_piece()
	elif event.is_pressed() and not event.is_echo():
		if event.is_action("ui_accept") or (event is InputEventKey and event.keycode == KEY_SPACE):
			engine.act()
		elif event is InputEventKey and (event.keycode == KEY_R or event.keycode == KEY_X or event.keycode == KEY_CTRL):
			engine.rotate_piece()
		else:
			var d := _dir_of(event)
			if d != Vector2.ZERO:
				_step_cursor(d)
				_repeat_dir = d
				_repeat_t = 0.28


func _dir_of(event: InputEvent) -> Vector2:
	if event.is_action("ui_left"): return Vector2.LEFT
	if event.is_action("ui_right"): return Vector2.RIGHT
	if event.is_action("ui_up"): return Vector2.UP
	if event.is_action("ui_down"): return Vector2.DOWN
	return Vector2.ZERO


func _held_keys(delta: float) -> void:
	var d := Vector2(Input.get_axis("ui_left", "ui_right"), Input.get_axis("ui_up", "ui_down"))
	if engine.phase == P.BATTLE:
		if d != Vector2.ZERO:
			engine.move_cursor(d.normalized() * 16.0 * delta)  # smooth aiming in battle
		return
	if d == Vector2.ZERO:
		_repeat_dir = Vector2.ZERO
		return
	_repeat_t -= delta
	if _repeat_t <= 0.0 and _repeat_dir != Vector2.ZERO:
		_step_cursor(_repeat_dir)
		_repeat_t = 0.07


func _step_cursor(d: Vector2, p: int = 0) -> void:
	var pl := engine.players[p]
	if engine.phase == P.CHOOSE:
		# jump between castles in the pressed direction (in versus, the player's own)
		var best := -1
		var best_d := INF
		for i in engine.map.castles.size():
			if engine.versus and engine.map.region_of(engine.map.castles[i].x, engine.map.castles[i].y) != p:
				continue
			var v := Vector2(engine.map.castles[i]) - pl.cursor
			if v.dot(d) > 0.5 and v.length() < best_d:
				best_d = v.length()
				best = i
		if best >= 0:
			pl.cursor = Vector2(engine.map.castles[best])
		return
	engine.move_cursor(d, p)


func _piece_center(p: int = 0) -> Vector2:
	if engine.phase == P.BUILD:
		return Vector2(WallPieces.size_of(engine.players[p].piece) - Vector2i.ONE) * 0.5
	if engine.phase == P.CANNONS:
		return Vector2(0.5, 0.5)
	return Vector2.ZERO


# ------------------------------------------------------------------ demo autopilot

func _bot(delta: float) -> void:
	_bot_t -= delta
	if _bot_t > 0.0:
		return
	match engine.phase:
		P.CHOOSE:
			engine.cursor = Vector2(engine.map.castles[1 % engine.map.castles.size()])
			_bot_t = 1.2
			if engine.phase_left < BastionEngine.CHOOSE_SECONDS - 1.0:
				engine.act()
		P.CANNONS:
			_bot_t = 0.6
			var spot := _bot_cannon_spot()
			if spot.x >= 0:
				engine.cursor = Vector2(spot)
				engine.act()
		P.BATTLE:
			_bot_t = 0.25
			var target := _bot_target()
			if target.x >= 0.0:
				engine.cursor = engine.cursor.lerp(target, 0.7)
				engine.fire_at(target)
		P.BUILD:
			_bot_t = 0.55
			var best := _bot_piece_spot()
			if best.is_empty():
				return
			while engine.piece_turns != best["turns"]:
				engine.rotate_piece()
			engine.cursor = Vector2(best["at"])
			engine.act()


func _bot_cannon_spot(p: int = 0) -> Vector2i:
	var home := engine.map.castles[maxi(0, engine.players[p].home_castle)] + Vector2i.ONE
	var best := Vector2i(-1, -1)
	var best_d := INF
	for y in engine.map.h:
		for x in engine.map.w:
			if engine.can_place_cannon(Vector2i(x, y), p):
				var d := Vector2(x, y).distance_to(Vector2(home)) + (0.0 if (x + y) % 2 == 0 else 0.5)
				if d < best_d:
					best_d = d
					best = Vector2i(x, y)
	return best


func _bot_target() -> Vector2:
	var best := Vector2(-1, -1)
	var best_d := INF
	var home := Vector2(engine.map.castles[maxi(0, engine.home_castle)])
	for s in engine.ships:
		var d: float = s["pos"].distance_to(home)
		if d < best_d:
			best_d = d
			var lead: Vector2 = (s["target"] - s["pos"]).limit_length(1.0) * BastionEngine.SHIP_SPEED * (d / BastionEngine.BALL_SPEED)
			best = s["pos"] + lead
	return best


## Greedy repair: choose the placement of the current piece (any rotation) that covers the most gaps in the
## ring the walls should form around the home castle, wasting as few blocks as possible.
func _bot_piece_spot(p: int = 0) -> Dictionary:
	var pl := engine.players[p]
	var home := engine.map.castles[maxi(0, pl.home_castle)]
	var ring := {}
	for r in [BastionEngine.HOME_RING, BastionEngine.HOME_RING + 1]:
		for y in range(home.y - r, home.y + 2 + r):
			for x in range(home.x - r, home.x + 2 + r):
				var edge: bool = y == home.y - r or y == home.y + 1 + r or x == home.x - r or x == home.x + 1 + r
				if edge and engine.map.is_land(x, y) and engine.cell(x, y) != BastionEngine.Cell.WALL:
					ring[Vector2i(x, y)] = 2.0 if r == BastionEngine.HOME_RING else 1.0
	var reach := 6
	if engine.versus:  # versus: the gaps the hole finder sees come first (craters push the ring outwards)
		if pl.enclosed_castles.has(pl.home_castle):
			return {}  # sealed: keep the pieces for the next breach (and the land clear for cannons)
		reach = 9
		var holes: Array = pl.castle_holes.get(pl.home_castle, [])
		if holes.size() <= BastionEngine.HOLE_LIMIT:
			for h in holes:
				ring[h] = 4.0
	if ring.is_empty():
		return {}
	var best := {}
	var best_score := 0.5
	# versus, while the home castle is open: where a piece that helps nowhere does least harm (so the next piece
	# comes), against our own walls rather than out on open ground
	var spare := {}
	var spare_score := -INF
	var want_spare := engine.versus and not pl.enclosed_castles.has(pl.home_castle)
	var saved := pl.piece_turns
	for turns in 4:
		var cells := WallPieces.rotated(WallPieces.SHAPES[pl.piece_shape], turns)
		for y in range(home.y - reach, home.y + reach + 2):
			for x in range(home.x - reach, home.x + reach + 2):
				var ok := true
				var score := 0.0
				var harm := 0.0
				var hug := 0.0
				for c in cells:
					var q := Vector2i(x, y) + c
					if not engine.buildable(q.x, q.y, p):
						ok = false
						break
					score += ring.get(q, -0.4)
					if engine.versus and engine.is_ours(q.x, q.y, p):
						harm += 1.0  # it would eat room for cannons
					if want_spare:
						for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
							if engine.owner_at(q.x + d.x, q.y + d.y) == p:
								hug += 0.3
						hug -= 0.12 * Vector2(q).distance_to(Vector2(home) + Vector2(0.5, 0.5))  # a compact fort
				score -= harm * 1.2
				if ok and score > best_score:
					best_score = score
					best = {"at": Vector2i(x, y), "turns": turns}
				if ok and want_spare and score + hug > spare_score:
					spare_score = score + hug
					spare = {"at": Vector2i(x, y), "turns": turns}
	pl.piece_turns = saved
	return best if not best.is_empty() else spare


## The versus autopilot for player `p`: picks a castle in its own region, places cannons near home, shells the
## walls around an enemy's home castle (now and then a cannon), and repairs the gaps in its own ring.
func _bot_versus(p: int, delta: float) -> void:
	_bot_ts[p] -= delta
	if _bot_ts[p] > 0.0:
		return
	var pl := engine.players[p]
	match engine.phase:
		P.CHOOSE:
			_bot_ts[p] = 1.0
			if pl.home_castle >= 0:
				return
			var mine := engine.map.castles_of(p)
			if not mine.is_empty():
				pl.cursor = Vector2(engine.map.castles[mine[mine.size() / 2]])
			if engine.phase_left < BastionEngine.CHOOSE_SECONDS - 1.5:
				engine.act(p)
		P.CANNONS:
			_bot_ts[p] = 0.6
			var spot := _bot_cannon_spot(p)
			if spot.x >= 0 and pl.cannons_to_place > 0:
				pl.cursor = Vector2(spot)
				engine.act(p)
		P.BATTLE:
			_bot_ts[p] = 0.45
			if _bot_focus[p].x < 0.0 or not _still_a_target(_bot_focus[p], p):
				_bot_focus[p] = _bot_enemy_target(p)
			var target := _bot_focus[p]
			if target.x >= 0.0:
				pl.cursor = pl.cursor.lerp(target, 0.7)
				if engine.fire_at(target, p):
					_bot_focus[p] = Vector2(-1, -1)  # the next shot picks again, near the same breach
		P.BUILD:
			_bot_ts[p] = 0.55
			var best := _bot_piece_spot(p)
			if best.is_empty():
				return
			while pl.piece_turns != best["turns"]:
				engine.rotate_piece(p)
			pl.cursor = Vector2(best["at"])
			engine.act(p)


func _still_a_target(t: Vector2, p: int) -> bool:
	var o := engine.owner_at(roundi(t.x), roundi(t.y))
	return o >= 0 and o != p


## An enemy wall on the ring around their home castle (so shots open a breach), or one of their cannons.
func _bot_enemy_target(p: int) -> Vector2:
	var enemies: Array[int] = []
	for q in engine.alive_players():
		if q != p:
			enemies.append(q)
	if enemies.is_empty():
		return Vector2(-1, -1)
	var e: int = enemies[(p + engine.round_number) % enemies.size()]
	if _bot_rng.randf() < 0.25:
		var guns: Array[Vector2] = []
		for c in engine.cannons:
			if c["player"] == e and c["active"]:
				guns.append(Vector2(c["pos"]) + Vector2(0.5, 0.5))
		if not guns.is_empty():
			return guns[_bot_rng.randi_range(0, guns.size() - 1)]
	var home := Vector2(engine.map.castles[maxi(0, engine.players[e].home_castle)]) + Vector2(0.5, 0.5)
	var walls := engine._our_walls(e)
	if walls.is_empty():
		return Vector2(-1, -1)
	var near: Array[Vector2i] = []
	for w in walls:
		if Vector2(w).distance_to(home) < BastionEngine.HOME_RING + 3.0:
			near.append(w)
	var pool := near if not near.is_empty() else walls
	return Vector2(pool[_bot_rng.randi_range(0, pool.size() - 1)])
