class_name FrostpeakGame
extends Node
## Runs Frostpeak Games: the players' setup (1 to 4 in hot seat, each with a nation), then event after event:
## a title card, each player's attempt and result, the CPU rivals, the standings and a medal podium; at the end
## the medal table. In demo mode a CPU-played athlete competes, so captures show real play.

signal stage_changed(stage: int)
signal attempt_started(ev: WinterEvent)

enum Stage { SETUP, INTRO, ATTEMPT, RESULT, STANDINGS, PODIUM, FINAL }

const STAGE_SECONDS := {Stage.INTRO: 3.5, Stage.RESULT: 3.2, Stage.STANDINGS: 4.5, Stage.PODIUM: 6.0}

var comp: Competition
var ev: WinterEvent
var stage := Stage.SETUP
var stage_t := 0.0
var athlete := 0  ## the human athlete whose turn it is
var demo := false
var demo_locked := false
var setup_players: Array[Dictionary] = [{"name": "PLAYER 1", "nation": 0}]
var setup_cursor := 0
var _acc := 0.0
var _seed := 1


func start_setup() -> void:
	_set_stage(Stage.SETUP)


func start(seed: int = -1) -> void:
	_seed = seed if seed >= 0 else randi()
	var players: Array = setup_players if not demo else [{"name": "DEMO", "nation": 0}]
	comp = Competition.new(players, 5 - players.size(), _seed)
	athlete = 0
	_set_stage(Stage.INTRO)


func _set_stage(s: Stage) -> void:
	stage = s
	stage_t = 0.0
	stage_changed.emit(s)


func humans() -> Array[int]:
	var out: Array[int] = []
	for i in comp.athletes.size():
		if not comp.athletes[i]["cpu"]:
			out.append(i)
	return out


func _new_attempt() -> void:
	match comp.event_name():
		"speed_skating":
			ev = SpeedSkating.new(_seed * 31 + comp.current * 7 + athlete)
			(ev as SpeedSkating).rival_skill = 0.6 + 0.1 * comp.current
		_:
			ev = SkiJump.new(_seed * 31 + comp.current * 7 + athlete)
	ev.auto = demo
	ev.skill = 0.85
	attempt_started.emit(ev)


func _process(delta: float) -> void:
	if stage == Stage.SETUP or stage == Stage.FINAL:
		stage_t += delta
		if demo and stage == Stage.FINAL and stage_t > 8.0:
			start(_seed + 1)
		return
	if stage == Stage.ATTEMPT:
		_acc = minf(_acc + delta, 0.25)
		while _acc >= WinterEvent.TICK:
			_acc -= WinterEvent.TICK
			if not demo:
				ev.hold_up = Input.is_action_pressed("ui_up")
				ev.hold_down = Input.is_action_pressed("ui_down")
			ev.tick()
		if ev.phase == WinterEvent.Phase.DONE:
			comp.record(humans()[athlete], ev.result)
			_set_stage(Stage.RESULT)
		return
	stage_t += delta
	if stage_t < STAGE_SECONDS.get(stage, 3.0):
		return
	match stage:
		Stage.INTRO:
			athlete = 0
			_new_attempt()
			_set_stage(Stage.ATTEMPT)
		Stage.RESULT:
			athlete += 1
			if athlete < humans().size():
				_new_attempt()
				_set_stage(Stage.ATTEMPT)
			else:
				comp.play_cpus()
				_set_stage(Stage.STANDINGS)
		Stage.STANDINGS:
			_set_stage(Stage.PODIUM)
		Stage.PODIUM:
			comp.next_event()
			_set_stage(Stage.FINAL if comp.finished() else Stage.INTRO)


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	if demo:
		if not demo_locked and (event is InputEventKey or event is InputEventJoypadButton) and not event.is_action("ui_cancel"):
			demo = false
			start_setup()
		return
	match stage:
		Stage.SETUP: _setup_input(event)
		Stage.ATTEMPT:
			if event.is_action("ui_left"):
				ev.press("left")
			elif event.is_action("ui_right"):
				ev.press("right")
			elif event.is_action("ui_accept") or (event is InputEventKey and event.keycode == KEY_SPACE):
				ev.press("action")
		Stage.INTRO, Stage.RESULT, Stage.STANDINGS, Stage.PODIUM:
			if event.is_action("ui_accept"):
				stage_t = 99.0  # skip ahead
		Stage.FINAL:
			if event.is_action("ui_accept") and stage_t > 1.0:
				start_setup()


func _setup_input(event: InputEvent) -> void:
	var p := setup_players[setup_cursor]
	if event.is_action("ui_left"):
		p["nation"] = posmod(p["nation"] - 1, Competition.NATIONS.size())
	elif event.is_action("ui_right"):
		p["nation"] = posmod(p["nation"] + 1, Competition.NATIONS.size())
	elif event.is_action("ui_up"):
		setup_cursor = maxi(0, setup_cursor - 1)
	elif event.is_action("ui_down"):
		setup_cursor = mini(setup_players.size() - 1, setup_cursor + 1)
	elif event is InputEventKey and event.keycode in [KEY_PLUS, KEY_KP_ADD, KEY_EQUAL] and setup_players.size() < 4:
		setup_players.append({"name": "PLAYER %d" % (setup_players.size() + 1), "nation": setup_players.size()})
	elif event is InputEventKey and event.keycode in [KEY_MINUS, KEY_KP_SUBTRACT] and setup_players.size() > 1:
		setup_players.pop_back()
		setup_cursor = mini(setup_cursor, setup_players.size() - 1)
	elif event.is_action("ui_accept"):
		start()
