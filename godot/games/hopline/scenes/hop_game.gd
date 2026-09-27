class_name HopGame
extends Node
## Runs Hopline: stage after stage (faster lanes, more diving turtles, the crocodile), four frogs, fixed 60 Hz
## ticks. Arrows, W A S D or a gamepad hop (one hop per press). The demo lets the autopilot play.

signal stage_started(engine: HopEngine)
signal game_over()
## Presentation-only happenings the view decides (a honk, a near miss), for the HUD and the sound.
signal fx(kind: String, data: Dictionary)

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
var first_stage := 0         ## "--stage=N": start later (captures of the sunset and night stages)
var streak := 0              ## quick crossings in a row (presentation only: no points)
var best_streak := 0
var last_crossing := 0.0     ## seconds the last frog home took
const QUICK := 11.0          ## a crossing under this many seconds keeps the streak going


func start(seed := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	stage = first_stage
	over = false
	streak = 0
	_new_stage(4, 0)


func _new_stage(lives: int, score: int) -> void:
	engine = HopEngine.new(stage, _seed + stage * 13, lives, score)
	_bot = HopBot.new(_seed + stage)
	engine.event.connect(_on_event)
	stage_started.emit(engine)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"home":
			last_crossing = HopEngine.LIFE_TIME - engine.life_t
			streak = streak + 1 if last_crossing < QUICK else 0
			best_streak = maxi(best_streak, streak)
		"die":
			streak = 0


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
			first_stage = 0
			start()
			get_viewport().set_input_as_handled()
		return
	if over:
		if event.is_action_pressed("ui_accept"):
			first_stage = 0
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
