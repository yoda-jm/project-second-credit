class_name DriftGame
extends Node
## Runs Marble Drift: course after course, the time left on one carried over to the next, until the clock runs out
## or the last course is done. 60 Hz ticks. The controls are screen-relative, like the arcade's: up pushes the marble
## up the screen. Arrows, W A S D or a gamepad's stick (proportional) push it; the mouse works as a trackball (move it
## and the marble rolls that way, faster for a quicker flick). "--level=N" (user argument) starts at a course.

signal course_started(engine: DriftEngine)
signal game_over()

const D = preload("res://games/marbledrift/engine/drift_engine.gd")
const FILE := "res://games/marbledrift/courses/courses.drift"
## the camera looks down the course from the +x +z side, turned 45 degrees: screen axes in course directions
const SCREEN_RIGHT := Vector2(0.70710678, -0.70710678)
const SCREEN_UP := Vector2(-0.70710678, -0.70710678)

var engine: DriftEngine
var courses: Array[DriftCourse] = []
var index := 0
var demo := false
var demo_locked := false
var over := false
var won := false
var high := 0
var _acc := 0.0
var _bot: DriftBot
var _ball := Vector2.ZERO   ## the trackball: mouse motion, fading


func start(at := 0) -> void:
	courses = DriftCourse.parse_file(FileAccess.get_file_as_string(FILE))
	index = clampi(at, 0, courses.size() - 1)
	over = false
	won = false
	_load(0.0, 0)


func _load(carried: float, score: int) -> void:
	var c: DriftCourse = DriftCourse.parse_file(FileAccess.get_file_as_string(FILE))[index]
	engine = DriftEngine.new(c, carried, score)
	engine.event.connect(_on_event)
	_bot = DriftBot.new()
	course_started.emit(engine)


func _on_event(kind: String, _d: Dictionary) -> void:
	if kind == "time_up":
		high = maxi(high, engine.score)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == D.Phase.OVER and engine.phase_t <= 0.0:
		_end()
		return
	if engine.phase == D.Phase.FINISHED and engine.phase_t <= 0.0:
		if index + 1 >= courses.size():
			won = true
			_end()
			return
		index += 1
		_load(engine.clock, engine.score)
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= D.TICK:
		_acc -= D.TICK
		if demo:
			_bot.drive(engine)
		else:
			engine.input = _steer()
		engine.tick()
	_ball = _ball.lerp(Vector2.ZERO, 1.0 - exp(-delta * 10.0))


func _end() -> void:
	over = true
	high = maxi(high, engine.score)
	game_over.emit()
	if demo:
		get_tree().create_timer(5.0).timeout.connect(func(): start(0))


## The push, in course directions, from screen directions.
func _steer() -> Vector2:
	var s := Vector2.ZERO
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D): s.x += 1.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A): s.x -= 1.0
	if Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W): s.y += 1.0
	if Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S): s.y -= 1.0
	var stick := Vector2(Input.get_joy_axis(0, JOY_AXIS_LEFT_X), -Input.get_joy_axis(0, JOY_AXIS_LEFT_Y))
	if stick.length() > 0.15:
		s += stick
	s += _ball
	s = s.limit_length(1.0)
	return SCREEN_RIGHT * s.x + SCREEN_UP * s.y


func _unhandled_input(event: InputEvent) -> void:
	if engine == null:
		return
	if demo:
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start(0)
			get_viewport().set_input_as_handled()
		return
	if over and event.is_action_pressed("ui_accept"):
		start(0)
		return
	# the trackball: mouse motion rolls the marble (screen y grows downwards)
	if event is InputEventMouseMotion:
		var m: Vector2 = event.relative
		_ball = (_ball + Vector2(m.x, -m.y) * 0.02).limit_length(1.0)
