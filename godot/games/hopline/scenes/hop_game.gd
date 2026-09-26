class_name HopGame
extends Node
## Runs Hopline: stage after stage (faster lanes, more diving turtles, the crocodile), four frogs, fixed 60 Hz
## ticks. Arrows, W A S D or a gamepad hop (one hop per press). The demo lets the autopilot play.

signal stage_started(engine: HopEngine)
signal game_over()

const E = preload("res://games/hopline/engine/hop_engine.gd")

var engine: HopEngine
var stage := 0
var demo := false
var demo_locked := false
var over := false
var high := 0
var _acc := 0.0
var _bot: HopBot
var _seed := 1


func start(seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	stage = 0
	over = false
	_new_stage(4, 0)


func _new_stage(lives: int, score: int) -> void:
	engine = HopEngine.new(stage, _seed + stage * 13, lives, score)
	_bot = HopBot.new(_seed + stage)
	stage_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == E.Phase.OVER:
		over = true
		high = maxi(high, engine.score)
		game_over.emit()
		if demo:
			get_tree().create_timer(5.0).timeout.connect(func(): start(_seed + 1))
		return
	if engine.phase == E.Phase.CLEARED and engine.phase_t <= 0.0:
		stage += 1
		_new_stage(engine.lives, engine.score)
		return
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
		if not demo_locked and event.is_pressed() and not event.is_echo() and (event is InputEventKey or event is InputEventJoypadButton) \
				and not event.is_action("ui_cancel"):
			demo = false
			start()
			get_viewport().set_input_as_handled()
		return
	if over:
		if event.is_action_pressed("ui_accept"):
			start()
		return
	if event.is_echo() or not event.is_pressed():
		return
	var dir := ""
	if event.is_action("ui_up") or (event is InputEventKey and event.physical_keycode == KEY_W): dir = "up"
	elif event.is_action("ui_down") or (event is InputEventKey and event.physical_keycode == KEY_S): dir = "down"
	elif event.is_action("ui_left") or (event is InputEventKey and event.physical_keycode == KEY_A): dir = "left"
	elif event.is_action("ui_right") or (event is InputEventKey and event.physical_keycode == KEY_D): dir = "right"
	if dir != "":
		engine.want = dir
