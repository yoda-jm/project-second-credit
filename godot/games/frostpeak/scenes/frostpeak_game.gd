class_name FrostpeakGame
extends Node
## Runs Frostpeak Games: a menu (the full competition, or practice at any one event), the players' setup (1 to 4
## in hot seat, each with a nation), then event after event: a title card, each player's attempt, its result and
## (on the hill) a TV replay, the CPU rivals, the standings and a medal podium; at the end the medal table. Practice
## repeats one event, attempt after attempt, keeping each player's best. In demo mode a CPU-played athlete competes,
## so captures show real play.

signal stage_changed(stage: int)
signal attempt_started(ev: WinterEvent)

enum Stage { SETUP, INTRO, ATTEMPT, RESULT, STANDINGS, PODIUM, FINAL, MENU, REPLAY, NEXT }

const STAGE_SECONDS := {Stage.INTRO: 9.0, Stage.RESULT: 3.2, Stage.STANDINGS: 14.0, Stage.PODIUM: 6.0, Stage.REPLAY: 10.5,
	Stage.NEXT: 6.0}
## How long each event's intro flies (the camera glides from wherever it is to the venue), and when its title card shows.
const INTRO_SECONDS := {"ski_jump": 24.0, "speed_skating": 12.0, "biathlon": 17.0, "bobsled": 20.0}
const INTRO_CARD := {"ski_jump": Vector2(5.0, 11.0)}
## Events with a TV replay after each attempt.
const REPLAYS := ["ski_jump"]

var comp: Competition
var ev: WinterEvent
var stage := Stage.SETUP
var stage_t := 0.0
var athlete := 0  ## the human athlete whose turn it is
var demo := false
var demo_locked := false
var setup_players: Array[Dictionary] = [{"name": "PLAYER 1", "nation": 0}]
var setup_cursor := 0
var menu_cursor := 0
var practice := ""  ## the event being practised ("" for the full competition)
var best := {}  ## practice: athlete index -> best result so far
var replay_seconds := 10.0  ## set by the view when it cuts the replay together
var _acc := 0.0
var ticks := 0  ## event ticks run so far (the view draws between the last two)
var _seed := 1


## The menu's entries: the full competition, then practice at each event.
func menu_items() -> Array[String]:
	var out: Array[String] = ["COMPETITION"]
	for ev_name in Competition.EVENTS:
		out.append("PRACTICE  " + Competition.EVENT_TITLES[ev_name])
	return out


func start_menu() -> void:
	_set_stage(Stage.MENU)


func start_setup() -> void:
	_set_stage(Stage.SETUP)


## Starts the games (or, with `practice` set, practice at that one event).
func start(seed: int = -1, first_event := 0) -> void:
	_seed = seed if seed >= 0 else randi()
	var players: Array = setup_players if not demo else [{"name": "DEMO", "nation": 0}]
	if practice != "":
		comp = Competition.new(players, 0, _seed, [practice])
	else:
		comp = Competition.new(players, 5 - players.size(), _seed)
		comp.current = first_event  # captures can start at a later event
	best = {}
	athlete = 0
	_set_stage(Stage.INTRO)


func _set_stage(s: Stage) -> void:
	stage = s
	stage_t = 0.0
	stage_changed.emit(s)


## How long a stage lasts. The ski jump takes longer: the camera glides across the valley to the hill and up it to
## the start gate, the jumper slides out and waves in the arena, the replay, and the flight back up to the gate.
func stage_seconds(s: Stage) -> float:
	var ev_name := comp.event_name() if comp != null else ""
	var jump := ev_name == "ski_jump"
	var bob := ev_name == "bobsled"
	match s:
		Stage.INTRO:
			return INTRO_SECONDS.get(ev_name, STAGE_SECONDS[Stage.INTRO])
		Stage.RESULT:
			return 7.0 if bob else (4.5 if jump else 3.2)  # (the bob brakes to a stop, and the crew celebrates)
		Stage.NEXT:
			return 12.0 if jump or bob else STAGE_SECONDS[Stage.NEXT]  # (the bob's start is a kilometre up the run)
		Stage.STANDINGS:
			return 18.0 if jump else (16.0 if bob else STAGE_SECONDS[Stage.STANDINGS])  # the hill is furthest from the plaza
		Stage.REPLAY:
			return replay_seconds
	return STAGE_SECONDS.get(s, 3.0)


## When the intro's title card shows (seconds into the intro).
func intro_card() -> Vector2:
	var dur := stage_seconds(Stage.INTRO)
	return INTRO_CARD.get(comp.event_name(), Vector2(dur - 5.5, dur - 0.6))


## How far the clock is between the last event tick and the next (0..1): the view draws the athletes that far on
## from the previous tick, so they move evenly whatever the frame rate.
func tick_alpha() -> float:
	return clampf(_acc / WinterEvent.TICK, 0.0, 1.0)


func has_replay() -> bool:
	return comp != null and comp.event_name() in REPLAYS


## Which player is up (an index into the athletes).
func current_athlete() -> int:
	var hs := humans()
	return hs[mini(athlete, hs.size() - 1)]


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
		"biathlon":
			ev = Biathlon.new(_seed * 31 + comp.current * 7 + athlete)
		"bobsled":
			ev = Bobsled.new(_seed * 31 + comp.current * 7 + athlete)
		_:
			ev = SkiJump.new(_seed * 31 + comp.current * 7 + athlete)
	ev.auto = demo
	ev.skill = 0.85
	attempt_started.emit(ev)


func _process(delta: float) -> void:
	if stage == Stage.SETUP or stage == Stage.FINAL or stage == Stage.MENU:
		stage_t += delta
		if demo and stage == Stage.FINAL and stage_t > 8.0:
			start(_seed + 1)
		return
	if stage == Stage.ATTEMPT:
		_acc = minf(_acc + delta, 0.25)
		while _acc >= WinterEvent.TICK - 0.000001:
			_acc -= WinterEvent.TICK
			ticks += 1
			if not demo:
				ev.hold_up = Input.is_action_pressed("ui_up")
				ev.hold_down = Input.is_action_pressed("ui_down")
				if ev is Biathlon:
					(ev as Biathlon).hold_left = Input.is_action_pressed("ui_left")
					(ev as Biathlon).hold_right = Input.is_action_pressed("ui_right")
				elif ev is Bobsled:
					(ev as Bobsled).hold_left = Input.is_action_pressed("ui_left")
					(ev as Bobsled).hold_right = Input.is_action_pressed("ui_right")
			ev.tick()
		if ev.phase == WinterEvent.Phase.DONE:
			var who := humans()[athlete]
			comp.record(who, ev.result)
			if practice != "":
				var lower: bool = Competition.LOWER_IS_BETTER[practice]
				if not best.has(who) or (ev.result < best[who] if lower else ev.result > best[who]):
					best[who] = ev.result
			_set_stage(Stage.RESULT)
		return
	stage_t += delta
	if stage_t < stage_seconds(stage):
		return
	match stage:
		Stage.INTRO, Stage.NEXT:
			_new_attempt()
			_set_stage(Stage.ATTEMPT)
		Stage.RESULT, Stage.REPLAY:
			if stage == Stage.RESULT and has_replay():
				_set_stage(Stage.REPLAY)
				return
			athlete += 1
			if practice != "":
				athlete %= humans().size()  # practice goes round the players until they leave
				_set_stage(Stage.NEXT)
			elif athlete < humans().size():
				_set_stage(Stage.NEXT)
			else:
				comp.play_cpus()
				_set_stage(Stage.STANDINGS)
		Stage.STANDINGS:
			_set_stage(Stage.PODIUM)
		Stage.PODIUM:
			comp.next_event()
			athlete = 0
			_set_stage(Stage.FINAL if comp.finished() else Stage.INTRO)


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	if demo:
		if not demo_locked and (event is InputEventKey or event is InputEventJoypadButton) and not event.is_action("ui_cancel"):
			demo = false
			start_menu()
		return
	match stage:
		Stage.MENU: _menu_input(event)
		Stage.SETUP: _setup_input(event)
		Stage.ATTEMPT:
			if event.is_action("ui_left"):
				ev.press("left")
			elif event.is_action("ui_right"):
				ev.press("right")
			elif event.is_action("ui_accept") or (event is InputEventKey and event.keycode == KEY_SPACE):
				ev.press("action")
		Stage.INTRO, Stage.RESULT, Stage.STANDINGS, Stage.PODIUM, Stage.REPLAY, Stage.NEXT:
			if event.is_action("ui_accept") or (event is InputEventKey and event.keycode == KEY_SPACE):
				stage_t = maxf(stage_t, stage_seconds(stage) - 0.01)  # skip ahead
		Stage.FINAL:
			if event.is_action("ui_accept") and stage_t > 1.0:
				start_menu()


func _menu_input(event: InputEvent) -> void:
	var n := menu_items().size()
	if event.is_action("ui_up"):
		menu_cursor = posmod(menu_cursor - 1, n)
	elif event.is_action("ui_down"):
		menu_cursor = posmod(menu_cursor + 1, n)
	elif event.is_action("ui_accept") or (event is InputEventKey and event.keycode == KEY_SPACE):
		practice = "" if menu_cursor == 0 else Competition.EVENTS[menu_cursor - 1]
		start_setup()


func _setup_input(event: InputEvent) -> void:
	if event is InputEventKey and event.keycode == KEY_BACKSPACE:
		start_menu()
		return
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
