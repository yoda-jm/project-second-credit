class_name FlagsGame
extends Node
## Runs an Iron Flags campaign: fixed 60 Hz ticks, the computer general for blue (and for red too in the demo), the
## player's mouse orders, and the campaign: win a map to move on, lose it to try again.
## Mouse: left click selects a squad (drag a box for several; click a factory to choose what it builds), right click
## moves the selection there or attacks what is under the cursor. Keys: 1-6 choose the selected factory's product,
## A selects the whole army, Space centres on the fort.

signal map_started(engine: FlagsEngine)
signal selection_changed()
signal campaign_over(won: bool)

const E = preload("res://games/flags/engine/flags_engine.gd")
const Team = FlagsMap.Team

@export_file("*.flags") var campaign_file := "res://games/flags/maps/campaign.flags"

var engine: FlagsEngine
var maps: Array[FlagsMap] = []
var level := 0
var demo := false
var demo_locked := false
var view: Node  ## provides screen_to_map(Vector2) -> Variant, pick(Vector2) -> int, select_box(Rect2) -> Array
var selected: Array[int] = []
var factory := -1  ## the selected building
var end_time := 0.0
var over := false
var _acc := 0.0
var _ais: Array[FlagsAI] = []
var _seed := 1
var _drag_from := Vector2(-1, -1)
var drag_rect := Rect2()  ## the selection box on screen, for the HUD


func start(seed := -1, first_level := 0) -> void:
	_seed = seed if seed >= 0 else randi()
	maps = FlagsMap.parse_campaign(FileAccess.get_file_as_string(campaign_file))
	level = clampi(first_level, 0, maps.size() - 1)
	over = false
	_start_map()


## Plays a map read from elsewhere (an imported Zod Engine map).
func start_map(m: FlagsMap, seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	maps = [m]
	level = 0
	over = false
	_start_map()


func _start_map() -> void:
	var m: FlagsMap = maps[level]
	if m.source == "text":  # a fresh copy: the engine blasts rocks in its map
		m = FlagsMap.parse_campaign(FileAccess.get_file_as_string(campaign_file))[level]
	engine = FlagsEngine.new(m, _seed + level * 101)
	_ais.clear()
	_ais.append(FlagsAI.new(Team.BLUE, _seed + level, 0.8 + 0.15 * level))
	if demo:
		_ais.append(FlagsAI.new(Team.RED, _seed + level + 7, 1.0))
	selected.clear()
	factory = -1
	end_time = 0.0
	map_started.emit(engine)
	selection_changed.emit()


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase != E.Phase.PLAY:
		end_time += delta
		if end_time > 5.0:
			if engine.phase == E.Phase.WON:
				level += 1
				if level >= maps.size():
					over = true
					campaign_over.emit(true)
					if demo:
						get_tree().create_timer(8.0).timeout.connect(func(): start(_seed + 1))
					return
			elif demo:
				level = (level + 1) % maps.size()
			_start_map()
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		for ai in _ais:
			ai.drive(engine)
		engine.tick()
	var before := selected.size()
	selected = selected.filter(func(id): return engine.alive(id) and engine.by_id(id)["team"] == Team.RED)
	if selected.size() != before:
		selection_changed.emit()
	if factory >= 0 and engine.by_id(factory)["team"] != Team.RED:
		factory = -1
		selection_changed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventMouseButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start()
		return
	if over and event.is_action_pressed("ui_accept"):
		start()
		return
	if view == null:
		return
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				_drag_from = event.position
				drag_rect = Rect2(event.position, Vector2.ZERO)
			else:
				_select(event.position)
				_drag_from = Vector2(-1, -1)
				drag_rect = Rect2()
		elif event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
			_order(event.position)
	elif event is InputEventMouseMotion and _drag_from.x >= 0:
		drag_rect = Rect2(_drag_from, event.position - _drag_from).abs()
	elif event is InputEventKey and event.pressed and not event.echo:
		if event.keycode >= KEY_1 and event.keycode <= KEY_6 and factory >= 0:
			var b := engine.by_id(factory)
			var list: Array = E.VEHICLE_BUILDS if b["kind"] == "vehicle_factory" else E.ROBOT_BUILDS
			engine.set_build(factory, list[event.keycode - KEY_1])
			selection_changed.emit()
		elif event.keycode == KEY_A:
			selected.assign(engine.team_units(Team.RED).filter(func(u): return u["cls"] != "cannon").map(func(u): return u["id"]))
			factory = -1
			selection_changed.emit()


func _select(pos: Vector2) -> void:
	var ids: Array[int] = []
	if drag_rect.size.length() > 8.0:
		for id in view.select_box(drag_rect):
			var u := engine.by_id(id)
			if u["team"] == Team.RED and u["cls"] != "cannon":
				ids.append(id)
		factory = -1
	else:
		var id: int = view.pick(pos)
		var t := engine.by_id(id) if id >= 0 else {}
		factory = -1
		if not t.is_empty() and t["team"] == Team.RED:
			if t.has("size"):
				if t["kind"] in E.FACTORIES:
					factory = id
			elif t["cls"] != "cannon":
				for u in engine.team_units(Team.RED):
					if u["group"] == t["group"]:
						ids.append(u["id"])
	selected = ids
	selection_changed.emit()
	if not ids.is_empty():
		engine.event.emit("select", {"ids": ids})


func _order(pos: Vector2) -> void:
	if selected.is_empty():
		return
	var id: int = view.pick(pos)
	var t := engine.by_id(id) if id >= 0 else {}
	if not t.is_empty() and t["team"] != Team.RED and t["team"] != Team.NEUTRAL:
		engine.order_attack(selected, id)
		engine.event.emit("order", {"attack": true, "pos": engine._center(t)})
		return
	var p = view.screen_to_map(pos)
	if p == null:
		return
	engine.order_move(selected, Vector2i(p.floor()))
	engine.event.emit("order", {"attack": false, "pos": p})
