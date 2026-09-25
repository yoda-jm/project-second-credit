class_name CaveGame
extends Node
## Runs one cave in real time: engine timing, player input (with a tap buffer), demo replays, score, time
## bonus and restarts. Views (flat debug view, 3D diorama) listen to its signals and read `engine`.

signal cave_started(engine: CaveEngine)
## Emitted after each engine frame; `frame_ms` is how long this frame lasts on screen.
signal frame_done(engine: CaveEngine, frame_ms: float)
signal cave_finished(engine: CaveEngine, success: bool)

const D = preload("res://games/rocks/engine/cave_directions.gd")
const PS = CaveRendered.PlayerState

var cave_set: CaveSet
var cave: CaveStored
var engine: CaveEngine
var level := 0
var demo: CaveReplay
var playing_demo := false
var score := 0
var bonus_pending := false
var finished := false
## Fraction (0..1) of the current engine frame that has elapsed: views use it to interpolate movement.
var frame_progress := 0.0

var _elapsed_ms := 0.0
var _finished_ms := 0.0
var _tapped_dir := D.STILL
var _tapped_fire := false
var _suicide := false


func load_cave(path: String, index: int = 0, with_demo: bool = false) -> void:
	cave_set = BdcffLoader.load_file(path)
	cave = cave_set.caves[index]
	demo = cave.replays[0] if with_demo and not cave.replays.is_empty() else null
	restart()


func restart() -> void:
	playing_demo = demo != null
	if demo:
		demo.rewind()
	engine = CaveEngine.new(cave, level, demo.seed if demo else randi() & 0x7fffffff)
	score = 0
	finished = false
	bonus_pending = false
	_elapsed_ms = 0.0
	_finished_ms = 0.0
	frame_progress = 0.0
	cave_started.emit(engine)


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	var dir := D.STILL
	if event.is_action("ui_up"): dir = D.UP
	elif event.is_action("ui_down"): dir = D.DOWN
	elif event.is_action("ui_left"): dir = D.LEFT
	elif event.is_action("ui_right"): dir = D.RIGHT
	if dir != D.STILL:
		if playing_demo:
			demo = null
			restart()
		_tapped_dir = dir
		_tapped_fire = _fire_held()
	elif event is InputEventKey and event.keycode == KEY_ESCAPE and not playing_demo:
		_suicide = true


func _fire_held() -> bool:
	return Input.is_key_pressed(KEY_SHIFT) or Input.is_key_pressed(KEY_CTRL) or Input.is_key_pressed(KEY_SPACE)


func _process(delta: float) -> void:
	if engine == null:
		return
	if finished:
		_finished_ms += delta * 1000.0
		if _finished_ms > 3500.0:
			restart()
		return
	_elapsed_ms += delta * 1000.0
	while _elapsed_ms >= engine.speed and not finished:
		_elapsed_ms -= engine.speed
		_step()
	frame_progress = clampf(_elapsed_ms / maxf(engine.speed, 1.0), 0.0, 1.0)


func _step() -> void:
	var move := D.STILL
	var fire := false
	if playing_demo:
		var m := demo.next_movement()
		if not m.is_empty():
			move = m[0]
			fire = m[1]
	else:
		# held keys win; otherwise a tap made since the last frame still counts (no lost key presses)
		move = D.from_keypress(Input.is_action_pressed("ui_up"), Input.is_action_pressed("ui_down"),
			Input.is_action_pressed("ui_left"), Input.is_action_pressed("ui_right"))
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
