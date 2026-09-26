class_name CratesGame
extends Node
## Runs Crate Keeper: the puzzles of a set in order (solved ones remembered, each with stars for beating or matching
## par), keys to walk and push (arrows or W A S D, held keys repeat), Z or Backspace to undo, Y to redo, R to start
## over, N / P for the next and previous puzzle, a click to walk to a cell. The demo plays the stored solutions.

signal puzzle_started(engine: CratesEngine)
signal stepped()

const SET := "res://games/crates/levels/harbour.xsb"
const STEP_TIME := 0.16      ## seconds per step when a key is held
const DEMO_STEP := 0.22
const SAVE := "user://crates.cfg"

var engine: CratesEngine
var puzzles: Array[CratesLevel] = []
var index := 0
var best := {}             ## puzzle name -> best moves
var demo := false
var demo_locked := false
var view: Node             ## provides screen_to_cell(Vector2) -> Variant
var _held := Vector2i.ZERO
var _repeat := 0.0
var _queue: Array[Vector2i] = []  ## steps still to walk (click to move, demo)
var _t := 0.0
var _solved_t := -1.0


func _ready() -> void:
	puzzles = CratesLevel.parse_file(FileAccess.get_file_as_string(SET))
	var cf := ConfigFile.new()
	if cf.load(SAVE) == OK:
		best = cf.get_value("progress", "best", {})


func start(i := 0) -> void:
	index = clampi(i, 0, puzzles.size() - 1)
	engine = CratesEngine.new(CratesLevel.parse_file(FileAccess.get_file_as_string(SET))[index])
	engine.event.connect(_on_event)
	_queue.clear()
	_solved_t = -1.0
	if demo:
		for ch in engine.level.solution.to_lower():
			if CratesEngine.DIRS.has(ch):
				_queue.append(CratesEngine.DIRS[ch])
	puzzle_started.emit(engine)


## Stars: 3 for par or better, 2 within half again, 1 for solving.
func stars(p: CratesLevel, moves: int) -> int:
	if moves <= 0:
		return 0
	if p.par <= 0 or moves <= p.par:
		return 3
	return 2 if moves <= int(p.par * 1.5) else 1


func _on_event(kind: String, d: Dictionary) -> void:
	if kind == "solved":
		_solved_t = 0.0
		if not demo:
			var name := engine.level.name
			if not best.has(name) or d["moves"] < best[name]:
				best[name] = d["moves"]
				var cf := ConfigFile.new()
				cf.set_value("progress", "best", best)
				cf.save(SAVE)


func _process(delta: float) -> void:
	if engine == null:
		return
	_t -= delta
	if _solved_t >= 0.0:
		_solved_t += delta
		if _solved_t > (3.0 if demo else 99.0):
			start((index + 1) % puzzles.size())
		return
	if not _queue.is_empty():
		if _t <= 0.0:
			_t = DEMO_STEP if demo else STEP_TIME * 0.7
			var d: Vector2i = _queue.pop_front()
			if not engine.step(d):
				_queue.clear()
			stepped.emit()
		return
	if _held != Vector2i.ZERO:
		_repeat -= delta
		if _repeat <= 0.0:
			_repeat = STEP_TIME
			engine.step(_held)
			stepped.emit()


func _dir_of(event: InputEvent) -> Vector2i:
	if event.is_action("ui_up") or (event is InputEventKey and event.physical_keycode == KEY_W): return Vector2i(0, -1)
	if event.is_action("ui_down") or (event is InputEventKey and event.physical_keycode == KEY_S): return Vector2i(0, 1)
	if event.is_action("ui_left") or (event is InputEventKey and event.physical_keycode == KEY_A): return Vector2i(-1, 0)
	if event.is_action("ui_right") or (event is InputEventKey and event.physical_keycode == KEY_D): return Vector2i(1, 0)
	return Vector2i.ZERO


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start(0)
			get_viewport().set_input_as_handled()
		return
	var d := _dir_of(event)
	if d != Vector2i.ZERO:
		if event.is_pressed() and not event.is_echo():
			_queue.clear()
			if _solved_t < 0.0:
				engine.step(d)
				stepped.emit()
			_held = d
			_repeat = STEP_TIME * 1.8
		elif not event.is_pressed() and _held == d:
			_held = Vector2i.ZERO
		return
	if not event.is_pressed() or event.is_echo():
		return
	if event is InputEventKey:
		match event.physical_keycode:
			KEY_Z, KEY_BACKSPACE, KEY_U:
				_queue.clear()
				if engine.undo():
					_solved_t = -1.0
			KEY_Y:
				engine.redo()
			KEY_R:
				_queue.clear()
				_solved_t = -1.0
				engine.restart()
			KEY_N, KEY_PAGEDOWN:
				start((index + 1) % puzzles.size())
			KEY_P, KEY_PAGEUP:
				start((index + puzzles.size() - 1) % puzzles.size())
			KEY_ENTER, KEY_SPACE:
				if _solved_t >= 0.0:
					start((index + 1) % puzzles.size())
	elif event is InputEventJoypadButton:
		match event.button_index:
			JOY_BUTTON_B: engine.undo(); _solved_t = -1.0
			JOY_BUTTON_Y: engine.restart(); _solved_t = -1.0
			JOY_BUTTON_A:
				if _solved_t >= 0.0:
					start((index + 1) % puzzles.size())
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and view and _solved_t < 0.0:
		var c = view.screen_to_cell(event.position)
		if c != null:
			var path := engine.walk_to(c)
			if path.is_empty():
				# a click on a crate next to the keeper pushes it
				var dd: Vector2i = c - engine.keeper
				if absi(dd.x) + absi(dd.y) == 1:
					path = [dd]
			_queue = path
			_t = 0.0


func solved_time() -> float:
	return _solved_t
