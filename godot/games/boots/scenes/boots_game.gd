class_name BootsGame
extends Node
## Runs a Muddy Boots campaign: fixed 60 Hz ticks, mouse orders (left: move, right held: fire, middle or G:
## grenade, R: rocket), the demo autopilot, and the campaign: survivors carry over to the next mission and new
## recruits fill the squad up to four; a lost mission is tried again while recruits remain.

signal mission_started(engine: BootsEngine)
signal campaign_over(won: bool)

const E = preload("res://games/boots/engine/boots_engine.gd")
const RECRUITS := 30

@export var pack_id := "first-tour"  ## the campaign pack (core/packs/pack.gd): its missions and story cards

var pack: Pack
var story_open := false  ## a story card is up: the mission waits
var show_story := true  ## false while the demo plays behind the campaign chooser
var _cards_seen := {}

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
	for c in get_children():  # a story card left from the demo
		if c is StoryCard:
			c.queue_free()
	story_open = false
	pack = Pack.find("boots", pack_id)
	missions = BootsMap.parse_campaign(pack.levels_text())
	_cards_seen.clear()
	mission = 0
	recruits = RECRUITS
	squad_size = 4
	over = false
	_start_mission()


func _start_mission() -> void:
	var m: BootsMap = BootsMap.parse_campaign(pack.levels_text())[mission]  # a fresh copy: the engine changes nothing in it, but huts etc. are rebuilt
	var n := mini(4, squad_size + recruits)
	recruits -= maxi(0, n - squad_size)
	squad_size = n
	engine = BootsEngine.new(m, _seed + mission * 101, n)
	engine.event.connect(_on_event)
	_bot = BootsBot.new()
	end_time = 0.0
	mission_started.emit(engine)
	_story(pack.card_before(mission), mission)


## Shows a story card once (not again when a lost mission is retried); the mission waits until it closes.
func _story(card: Dictionary, key) -> void:
	if card.is_empty() or _cards_seen.has(key) or not show_story:
		return
	_cards_seen[key] = true
	story_open = true
	var c := StoryCard.show_card(self, card, Color(0.6, 0.8, 0.4), 7.0 if demo else 0.0)
	c.closed.connect(func(): story_open = false)


func _on_event(kind: String, _d: Dictionary) -> void:
	if kind == "death" and _d.get("who", "") == "soldier":
		squad_size -= 1


func _process(delta: float) -> void:
	if engine == null or over or story_open:
		return
	if engine.phase != E.Phase.PLAY:
		end_time += delta
		if end_time > 3.5:
			if engine.phase == E.Phase.WON:
				mission += 1
				if mission >= missions.size():
					over = true
					campaign_over.emit(true)
					_story(pack.outro, "outro")
					if demo:
						get_tree().create_timer(10.0).timeout.connect(func(): start(_seed + 1))
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
