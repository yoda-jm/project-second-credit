class_name CaveGame
extends Node
## Runs one cave in real time: engine timing, player input (with a tap buffer), demo replays, score, time
## bonus and restarts. Views (flat debug view, 3D diorama) listen to its signals and read `engine`.
## Campaign mode plays a pack's caves in order (core/packs/pack.gd): three lives, the score carries on, and the
## pack's story cards show between caves.

signal cave_started(engine: CaveEngine)
## Emitted after each engine frame; `frame_ms` is how long this frame lasts on screen.
signal frame_done(engine: CaveEngine, frame_ms: float)
signal cave_finished(engine: CaveEngine, success: bool)
## Emitted when the pre-start countdown shows a new number (3, 2, 1, then 0 for GO).
signal countdown_tick(number: int)
## Campaign: the run is over (won: every cave cleared; else out of lives).
signal campaign_over(won: bool)

const LIVES := 3

## Seconds of 3-2-1 countdown before the cave starts (the engine does not run meanwhile).
@export var countdown_seconds := 3.0

const D = preload("res://games/glimmerdeep/engine/cave_directions.gd")
const PS = CaveRendered.PlayerState

var cave_set: CaveSet
var cave: CaveStored
var engine: CaveEngine
var level := 0
var demo: CaveReplay
var playing_demo := false
var demo_locked := false  ## captures: the demo cannot be taken over by input
var score := 0
var bonus_pending := false
var finished := false
## Fraction (0..1) of the current engine frame that has elapsed: views use it to interpolate movement.
var frame_progress := 0.0

var countdown_left := 0.0  ## seconds of countdown remaining (0 when the cave runs)
var _elapsed_ms := 0.0
var _finished_ms := 0.0
var _tapped_dir := D.STILL
var _tapped_fire := false
var _suicide := false
# campaign
var pack: Pack
var caves: Array[CaveStored] = []
var cave_no := 0
var lives := LIVES
var campaign_done := false
var story_open := false
var autopilot := false
## Two-player race: 0 = the only player (arrows, WASD... through the ui actions), 1 = arrow keys and the first
## gamepad, 2 = W A S D (by key position, so ZQSD on AZERTY) and the second gamepad.
var player := 0
var race_seed := -1  ## the engine's random seed (a race gives both players the same cave, rocks and creatures)
var auto_restart := true  ## a finished cave starts again by itself (not in a race: the race decides)
const P_KEYS := {1: [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT], 2: [KEY_W, KEY_S, KEY_A, KEY_D]}
const P_FIRE := {1: [KEY_CTRL, KEY_ENTER, KEY_KP_0], 2: [KEY_SHIFT, KEY_SPACE, KEY_TAB]}  ## captures: the demo bot plays the campaign (and story cards are skipped)
var _score_at_start := 0
var _cards_seen := {}


func load_cave(path: String, index: int = 0, with_demo: bool = false, demo_index: int = 0) -> void:
	_clear_cards()
	pack = null
	campaign_done = false
	_score_at_start = 0
	cave_set = BdcffLoader.load_file(path)
	cave = cave_set.caves[index]
	demo = cave.replays[mini(demo_index, cave.replays.size() - 1)] if with_demo and not cave.replays.is_empty() else null
	restart()


## Plays a pack's caves one after the other (every cave of every level file, in order).
func start_campaign(p: Pack, first := 0) -> void:
	_clear_cards()
	pack = p
	caves.clear()
	for f in p.levels:
		caves.append_array(BdcffLoader.load_file(f).caves)
	cave_no = clampi(first, 0, 999)
	lives = LIVES
	score = 0
	campaign_done = false
	_cards_seen.clear()
	demo = null
	cave_no = mini(cave_no, caves.size() - 1)
	_begin_cave()


func _clear_cards() -> void:
	for c in get_children():
		if c is StoryCard:
			c.queue_free()
	story_open = false


func _begin_cave() -> void:
	cave = caves[cave_no]
	_score_at_start = score
	restart()
	var card := pack.card_before(cave_no)
	if not card.is_empty() and not _cards_seen.has(cave_no) and not autopilot:
		_cards_seen[cave_no] = true
		story_open = true
		var c := StoryCard.show_card(self, card, Color(1.0, 0.8, 0.35))
		c.closed.connect(func(): story_open = false)


func restart() -> void:
	playing_demo = demo != null
	if demo:
		demo.rewind()
	engine = CaveEngine.new(cave, level, demo.seed if demo else (race_seed if race_seed >= 0 else randi() & 0x7fffffff))
	score = _score_at_start if pack else 0
	finished = false
	bonus_pending = false
	_elapsed_ms = 0.0
	_finished_ms = 0.0
	frame_progress = 0.0
	countdown_left = countdown_seconds
	cave_started.emit(engine)
	if countdown_left > 0.0:
		countdown_tick.emit(ceili(countdown_left))


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	var dir := _event_dir(event)
	if dir != D.STILL:
		if playing_demo and not demo_locked:
			demo = null
			var p := Pack.find("glimmerdeep", "second-credit")
			if p:  # the player takes over: the campaign starts
				start_campaign(p)
			else:
				restart()
			return
		elif playing_demo:
			return
		_tapped_dir = dir
		_tapped_fire = _fire_held()


func _event_dir(event: InputEvent) -> int:
	if player == 0:
		if event.is_action("ui_up"): return D.UP
		if event.is_action("ui_down"): return D.DOWN
		if event.is_action("ui_left"): return D.LEFT
		if event.is_action("ui_right"): return D.RIGHT
		return D.STILL
	if event is InputEventKey:
		var k: Array = P_KEYS[player]
		var i := k.find(event.physical_keycode)
		return [D.UP, D.DOWN, D.LEFT, D.RIGHT][i] if i >= 0 else D.STILL
	if event is InputEventJoypadButton and event.device == player - 1:
		match event.button_index:
			JOY_BUTTON_DPAD_UP: return D.UP
			JOY_BUTTON_DPAD_DOWN: return D.DOWN
			JOY_BUTTON_DPAD_LEFT: return D.LEFT
			JOY_BUTTON_DPAD_RIGHT: return D.RIGHT
	return D.STILL


## The directions held now: up, down, left, right.
func _held() -> Array:
	if player == 0:
		return [Input.is_action_pressed("ui_up"), Input.is_action_pressed("ui_down"),
			Input.is_action_pressed("ui_left"), Input.is_action_pressed("ui_right")]
	var k: Array = P_KEYS[player]
	var dev := player - 1
	var ax := Input.get_joy_axis(dev, JOY_AXIS_LEFT_X)
	var ay := Input.get_joy_axis(dev, JOY_AXIS_LEFT_Y)
	return [Input.is_physical_key_pressed(k[0]) or Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_UP) or ay < -0.5,
		Input.is_physical_key_pressed(k[1]) or Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_DOWN) or ay > 0.5,
		Input.is_physical_key_pressed(k[2]) or Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_LEFT) or ax < -0.5,
		Input.is_physical_key_pressed(k[3]) or Input.is_joy_button_pressed(dev, JOY_BUTTON_DPAD_RIGHT) or ax > 0.5]


func _fire_held() -> bool:
	if player == 0:
		return Input.is_key_pressed(KEY_SHIFT) or Input.is_key_pressed(KEY_CTRL) or Input.is_key_pressed(KEY_SPACE)
	for key in P_FIRE[player]:
		if Input.is_physical_key_pressed(key):
			return true
	return Input.is_joy_button_pressed(player - 1, JOY_BUTTON_A)


func _process(delta: float) -> void:
	if engine == null or story_open or campaign_done:
		return
	if countdown_left > 0.0:
		var before := ceili(countdown_left)
		countdown_left = maxf(0.0, countdown_left - delta)
		var after := ceili(countdown_left)
		if after != before:
			countdown_tick.emit(after)
		return
	if finished:
		_finished_ms += delta * 1000.0
		if _finished_ms > 3500.0 and auto_restart:
			_after_cave()
		return
	_elapsed_ms += delta * 1000.0
	while _elapsed_ms >= engine.speed and not finished:
		_elapsed_ms -= engine.speed
		_step()
	frame_progress = clampf(_elapsed_ms / maxf(engine.speed, 1.0), 0.0, 1.0)


func _after_cave() -> void:
	if pack == null:  # single cave (the demo): play it again
		restart()
		return
	if engine.player_state == PS.EXITED:
		cave_no += 1
		if cave_no >= caves.size():
			campaign_done = true
			campaign_over.emit(true)
			if not pack.outro.is_empty():
				StoryCard.show_card(self, pack.outro, Color(1.0, 0.8, 0.35))
			return
		_begin_cave()
		return
	lives -= 1
	if lives <= 0:
		campaign_done = true
		campaign_over.emit(false)
		return
	restart()


## After a finished campaign: Enter plays it again from the first cave.
func _input(event: InputEvent) -> void:
	if campaign_done and pack and event.is_action_pressed("ui_accept"):
		start_campaign(pack)
		get_viewport().set_input_as_handled()


func _step() -> void:
	var move := D.STILL
	var fire := false
	if playing_demo:
		var m := demo.next_movement()
		if not m.is_empty():
			move = m[0]
			fire = m[1]
	elif autopilot:
		move = DemoBot.next_move(engine)
	else:
		# held keys win; otherwise a tap made since the last frame still counts (no lost key presses)
		var held := _held()
		move = D.from_keypress(held[0], held[1], held[2], held[3])
		fire = _fire_held()
		if move == D.STILL and _tapped_dir != D.STILL:
			move = _tapped_dir
			fire = _tapped_fire
		_tapped_dir = D.STILL
	engine.iterate(move, fire, _suicide)
	_suicide = false
	score += engine.score
	frame_done.emit(engine, float(engine.speed))
	var st := engine.player_state
	if st == PS.EXITED:
		score += ReplayRunner.time_bonus(engine)
		finished = true
		cave_finished.emit(engine, true)
	elif st == PS.TIMEOUT or st == PS.DIED:
		finished = true
		cave_finished.emit(engine, false)
