class_name BastionGame
extends Node
## Runs a Bastion Coast game in real time: fixed 60 Hz ticks of the engine, player input (keys with repeat,
## mouse aiming via the view), the demo autopilot, restarts. The view and HUD read `engine` and its events.
## Campaign mode plays a pack's islands in order (core/packs/pack.gd): hold each for its rounds to sail on to the
## next, with the pack's story cards between; a lost island is tried again (Enter), the score carries on.

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


func start(seed: int = -1) -> void:
	_seed = seed if seed >= 0 else randi()
	if pack:
		_start_island()
		return
	engine = BastionEngine.new(CoastMap.load_file(map_file), _seed)
	game_over_time = 0.0
	_bot_plan = {}
	started.emit(engine)


func start_campaign(p: Pack, seed: int = -1) -> void:
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


func total_score() -> int:
	return banked + (engine.score if engine else 0)


func _process(delta: float) -> void:
	if engine == null or story_open:
		return
	if engine.phase == P.GAME_OVER:
		game_over_time += delta
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
	if demo:
		_bot(delta)
	else:
		_held_keys(delta)
	_acc += delta
	while _acc >= BastionEngine.TICK:
		_acc -= BastionEngine.TICK
		engine.tick()


# ------------------------------------------------------------------ player input

func _unhandled_input(event: InputEvent) -> void:
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


func _step_cursor(d: Vector2) -> void:
	if engine.phase == P.CHOOSE:
		# jump between castles in the pressed direction
		var best := -1
		var best_d := INF
		for i in engine.map.castles.size():
			var v := Vector2(engine.map.castles[i]) - engine.cursor
			if v.dot(d) > 0.5 and v.length() < best_d:
				best_d = v.length()
				best = i
		if best >= 0:
			engine.cursor = Vector2(engine.map.castles[best])
		return
	engine.move_cursor(d)


func _piece_center() -> Vector2:
	if engine.phase == P.BUILD:
		return Vector2(WallPieces.size_of(engine.piece) - Vector2i.ONE) * 0.5
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


func _bot_cannon_spot() -> Vector2i:
	var home := engine.map.castles[maxi(0, engine.home_castle)] + Vector2i.ONE
	var best := Vector2i(-1, -1)
	var best_d := INF
	for y in engine.map.h:
		for x in engine.map.w:
			if engine.can_place_cannon(Vector2i(x, y)):
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
func _bot_piece_spot() -> Dictionary:
	var home := engine.map.castles[maxi(0, engine.home_castle)]
	var ring := {}
	for r in [BastionEngine.HOME_RING, BastionEngine.HOME_RING + 1]:
		for y in range(home.y - r, home.y + 2 + r):
			for x in range(home.x - r, home.x + 2 + r):
				var edge: bool = y == home.y - r or y == home.y + 1 + r or x == home.x - r or x == home.x + 1 + r
				if edge and engine.map.is_land(x, y) and engine.cell(x, y) != BastionEngine.Cell.WALL:
					ring[Vector2i(x, y)] = 2.0 if r == BastionEngine.HOME_RING else 1.0
	if ring.is_empty():
		return {}
	var best := {}
	var best_score := 0.5
	var saved := engine.piece_turns
	for turns in 4:
		var cells := WallPieces.rotated(WallPieces.SHAPES[engine._piece_shape], turns)
		for y in range(home.y - 6, home.y + 8):
			for x in range(home.x - 6, home.x + 8):
				var ok := true
				var score := 0.0
				for c in cells:
					var p := Vector2i(x, y) + c
					if not engine.buildable(p.x, p.y):
						ok = false
						break
					score += ring.get(p, -0.4)
				if ok and score > best_score:
					best_score = score
					best = {"at": Vector2i(x, y), "turns": turns}
	engine.piece_turns = saved
	return best
