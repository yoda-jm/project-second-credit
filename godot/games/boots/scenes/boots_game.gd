class_name BootsGame
extends Node
## Runs a Muddy Boots campaign: fixed 60 Hz ticks, mouse orders (left: move, right held: fire, middle or G:
## grenade, R: rocket), the demo autopilot, and the campaign: survivors carry over to the next mission and new
## recruits fill the squad up to four; a lost mission is tried again while recruits remain.

signal mission_started(engine: BootsEngine)
signal campaign_over(won: bool)

const E = preload("res://games/boots/engine/boots_engine.gd")
const RECRUITS := 30

@export_file("*.boots") var campaign_file := "res://games/boots/maps/first-tour.boots"

var engine: BootsEngine
var missions: Array[BootsMap] = []
var mission := 0
var recruits := RECRUITS
var squad_size := 4
var demo := false
var demo_locked := false
var view: Node  ## provides screen_to_map(Vector2) -> Vector2 (or null)
var end_time := 0.0
var over := false
var _acc := 0.0
var _bot := BootsBot.new()
var _seed := 1
var _cursor := Vector2.ZERO


func start(seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	missions = BootsMap.parse_campaign(FileAccess.get_file_as_string(campaign_file))
	mission = 0
	recruits = RECRUITS
	squad_size = 4
	over = false
	_start_mission()


func _start_mission() -> void:
	var text := FileAccess.get_file_as_string(campaign_file)
	var m: BootsMap = BootsMap.parse_campaign(text)[mission]  # a fresh copy: the engine changes nothing in it, but huts etc. are rebuilt
	var n := mini(4, squad_size + recruits)
	recruits -= maxi(0, n - squad_size)
	squad_size = n
	engine = BootsEngine.new(m, _seed + mission * 101, n)
	engine.event.connect(_on_event)
	_bot = BootsBot.new()
	end_time = 0.0
	mission_started.emit(engine)


func _on_event(kind: String, _d: Dictionary) -> void:
	if kind == "death" and _d.get("who", "") == "soldier":
		squad_size -= 1


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase != E.Phase.PLAY:
		end_time += delta
		if end_time > 3.5:
			if engine.phase == E.Phase.WON:
				mission += 1
				if mission >= missions.size():
					over = true
					campaign_over.emit(true)
					if demo:
						get_tree().create_timer(6.0).timeout.connect(func(): start(_seed + 1))
					return
			elif recruits <= 0:
				over = true
				campaign_over.emit(false)
				if demo:
					get_tree().create_timer(6.0).timeout.connect(func(): start(_seed + 1))
				return
			_start_mission()
		return
	if not demo and view:
		var p = view.screen_to_map(get_viewport().get_mouse_position())
		if p != null:
			_cursor = p
			engine.aim = p
		engine.firing = Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		if demo:
			_bot.drive(engine)
		engine.tick()


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
	if event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT: engine.move_to(_cursor)
			MOUSE_BUTTON_MIDDLE: engine.throw_grenade(_cursor)
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_G: engine.throw_grenade(_cursor)
			KEY_R: engine.fire_rocket(_cursor)
