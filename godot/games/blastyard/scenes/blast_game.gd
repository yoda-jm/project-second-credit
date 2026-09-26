class_name BlastGame
extends Node
## Runs Blastyard: the setup screen (battle or solo, how many people play, which arena), then matches of rounds
## (first to WINS rounds; bots fill the empty seats) or the solo stages (three lives, the stages in order), at
## fixed 60 Hz ticks with a countdown before each round. The demo lets four bots battle.
## Controls: player 1 arrows + Space, Enter or right Ctrl; player 2 W A S D + left Shift or Tab; player 3 I J K L
## + U; player 4 the number pad 8 4 5 6 + 0 (keys by position, so AZERTY works); gamepad N plays player N.

signal round_started(engine: BlastEngine)
signal setup_changed()

const E = preload("res://games/blastyard/engine/blast_engine.gd")
const WINS := 3
const COUNTDOWN := 2.5
const KEYS := [[KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT], [KEY_W, KEY_S, KEY_A, KEY_D], [KEY_I, KEY_K, KEY_J, KEY_L],
	[KEY_KP_8, KEY_KP_5, KEY_KP_4, KEY_KP_6]]
const BOMB_KEYS := [[KEY_SPACE, KEY_ENTER, KEY_CTRL], [KEY_SHIFT, KEY_TAB], [KEY_U], [KEY_KP_0, KEY_KP_ENTER]]
const ARENA_FILE := "res://games/blastyard/maps/arenas.blast"
const SOLO_FILE := "res://games/blastyard/maps/solo.blast"

var engine: BlastEngine
var demo := false
var demo_locked := false
var in_setup := true
var mode := "battle"      ## battle or solo
var humans := 1
var arena_choice := 0     ## index into the arenas, or -1 for a different one each round
var arena_names: Array[String] = []
var wins := [0, 0, 0, 0]
var round_no := 0
var stage := 0
var lives := 3
var countdown := 0.0
var over_t := -1.0
var match_winner := -1
var _acc := 0.0
var _bots: Array[BlastBot] = []
var _seed := 1
var _setup_row := 0
var _pressed := [false, false, false, false]


func _ready() -> void:
	for m in ArenaMap.parse_file(FileAccess.get_file_as_string(ARENA_FILE)):
		arena_names.append(m.name)


func start_demo(seed := 5) -> void:
	demo = true
	in_setup = false
	mode = "battle"
	humans = 0
	arena_choice = -1
	_seed = seed
	_new_match()


func start_setup() -> void:
	demo = false
	in_setup = true
	setup_changed.emit()


func _new_match() -> void:
	wins = [0, 0, 0, 0]
	round_no = 0
	stage = 0
	lives = 3
	match_winner = -1
	_new_round()


func _new_round() -> void:
	var m: ArenaMap
	var slots := 4
	if mode == "solo":
		var stages := ArenaMap.parse_file(FileAccess.get_file_as_string(SOLO_FILE), _seed + stage * 7 + round_no)
		m = stages[stage % stages.size()]
		slots = clampi(humans, 1, 2)
	else:
		var arenas := ArenaMap.parse_file(FileAccess.get_file_as_string(ARENA_FILE), _seed + round_no * 13)
		m = arenas[arena_choice if arena_choice >= 0 else (round_no % arenas.size())]
	engine = BlastEngine.new(m, slots, _seed + round_no)
	_bots.clear()
	for i in slots:
		if i >= humans or demo:
			_bots.append(BlastBot.new(i, _seed + round_no * 3 + i, 0.8 + 0.1 * i))
	round_no += 1
	countdown = COUNTDOWN
	over_t = -1.0
	engine.event.connect(_on_event)
	round_started.emit(engine)


func _on_event(kind: String, d: Dictionary) -> void:
	if kind == "round_over" or kind == "stage_clear":
		over_t = 0.0
		if mode == "battle" and d.get("winner", -1) >= 0:
			wins[d["winner"]] += 1
			if wins[d["winner"]] >= WINS:
				match_winner = d["winner"]


func is_bot(slot: int) -> bool:
	return demo or slot >= humans


func _process(delta: float) -> void:
	if in_setup or engine == null:
		return
	if countdown > 0.0:
		countdown -= delta
		return
	if over_t >= 0.0:
		over_t += delta
		if over_t > (4.5 if match_winner >= 0 else 3.0):
			_after_round()
		# the arena keeps ticking a moment so the last flames and the victory dance play out
	_acc = minf(_acc + delta, 0.25)
	while _acc >= E.TICK:
		_acc -= E.TICK
		for b in _bots:
			b.drive(engine)
		if not demo:
			for s in mini(humans, engine.players.size()):
				engine.set_input(s, _dir(s), _bomb(s))
		engine.tick()


func _after_round() -> void:
	over_t = -1.0
	if mode == "solo":
		if engine.winner >= 0:
			stage += 1
		else:
			lives -= 1
			if lives <= 0:
				match_winner = -1
				start_setup()
				return
		_new_round()
		return
	if match_winner >= 0:
		if demo:
			_seed += 1
			_new_match()
		else:
			start_setup()
		return
	_new_round()


func _dir(slot: int) -> Vector2i:
	var k: Array = KEYS[slot]
	var up := Input.is_physical_key_pressed(k[0]) or Input.is_joy_button_pressed(slot, JOY_BUTTON_DPAD_UP) or Input.get_joy_axis(slot, JOY_AXIS_LEFT_Y) < -0.5
	var down := Input.is_physical_key_pressed(k[1]) or Input.is_joy_button_pressed(slot, JOY_BUTTON_DPAD_DOWN) or Input.get_joy_axis(slot, JOY_AXIS_LEFT_Y) > 0.5
	var left := Input.is_physical_key_pressed(k[2]) or Input.is_joy_button_pressed(slot, JOY_BUTTON_DPAD_LEFT) or Input.get_joy_axis(slot, JOY_AXIS_LEFT_X) < -0.5
	var right := Input.is_physical_key_pressed(k[3]) or Input.is_joy_button_pressed(slot, JOY_BUTTON_DPAD_RIGHT) or Input.get_joy_axis(slot, JOY_AXIS_LEFT_X) > 0.5
	if up != down:
		return Vector2i(0, -1 if up else 1)
	if left != right:
		return Vector2i(-1 if left else 1, 0)
	return Vector2i.ZERO


## True once per press (the bomb key has to be released between two bombs).
func _bomb(slot: int) -> bool:
	var held := Input.is_joy_button_pressed(slot, JOY_BUTTON_A)
	for key in BOMB_KEYS[slot]:
		held = held or Input.is_physical_key_pressed(key)
	var fire: bool = held and not _pressed[slot]
	_pressed[slot] = held
	return fire


# ------------------------------------------------------------------ setup screen

const SETUP_ROWS := ["mode", "humans", "arena", "start"]


func _unhandled_input(event: InputEvent) -> void:
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			start_setup()
			get_viewport().set_input_as_handled()
		return
	if not in_setup or not event.is_pressed() or event.is_echo():
		return
	if event.is_action("ui_up"):
		_setup_row = (_setup_row + SETUP_ROWS.size() - 1) % SETUP_ROWS.size()
	elif event.is_action("ui_down"):
		_setup_row = (_setup_row + 1) % SETUP_ROWS.size()
	elif event.is_action("ui_left") or event.is_action("ui_right"):
		var s := -1 if event.is_action("ui_left") else 1
		match SETUP_ROWS[_setup_row]:
			"mode": mode = "solo" if mode == "battle" else "battle"
			"humans": humans = clampi(humans + s, 1, 2 if mode == "solo" else 4)
			"arena": arena_choice = wrapi(arena_choice + s + 1, 0, arena_names.size() + 1) - 1
	elif event.is_action("ui_accept"):
		in_setup = false
		humans = clampi(humans, 1, 2 if mode == "solo" else 4)
		_seed = randi() % 100000
		_new_match()
	else:
		return
	get_viewport().set_input_as_handled()
	setup_changed.emit()


func setup_row() -> String:
	return SETUP_ROWS[_setup_row]
