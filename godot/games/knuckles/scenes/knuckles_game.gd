class_name KnucklesGame
extends Node
## Runs Neon Knuckles: fixed 60 Hz ticks, two players' controls (player 1: arrows, Space or Z to attack, X or Up to
## jump, C to pick up; player 2: WASD, F to attack, G to jump; gamepads 1 and 2), a short hit-stop on every blow,
## stages in a row, the demo autopilot.

signal stage_started(engine: BrawlEngine)
signal run_over(won: bool)

const B = preload("res://games/knuckles/engine/brawl_engine.gd")

@export_file("*.brawl") var stages_file := "res://games/knuckles/stages/downtown.brawl"

var engine: BrawlEngine
var stages: Array[BrawlLevel] = []
var stage := 0
var players := 1
var demo := false
var demo_locked := false
var end_time := 0.0
var over := false
var _acc := 0.0
var _freeze := 0  ## hit-stop ticks left
var _bots := [BrawlBot.new(1), BrawlBot.new(2)]
var _seed := 1
var _press := [{}, {}]
var _carry_score := 0


func start(seed := -1, n_players := -1) -> void:
	_seed = seed if seed >= 0 else randi()
	if n_players > 0:
		players = n_players
	stages = BrawlLevel.parse_file(FileAccess.get_file_as_string(stages_file))
	stage = 0
	over = false
	_carry_score = 0
	_start_stage()


func _start_stage() -> void:
	var lv: BrawlLevel = BrawlLevel.parse_file(FileAccess.get_file_as_string(stages_file))[stage]
	engine = BrawlEngine.new(lv, players, _seed + stage * 37)
	engine.score = _carry_score
	engine.event.connect(_on_event)
	end_time = 0.0
	stage_started.emit(engine)


func _on_event(kind: String, d: Dictionary) -> void:
	if kind == "hit":
		_freeze = 4 if d["damage"] >= 14 else 2


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase != B.Phase.PLAY:
		end_time += delta
		if end_time > 4.0:
			if engine.phase == B.Phase.CLEAR and stage + 1 < stages.size():
				_carry_score = engine.score
				stage += 1
				_start_stage()
			else:
				over = true
				run_over.emit(engine.phase == B.Phase.CLEAR)
				if demo:
					get_tree().create_timer(6.0).timeout.connect(func(): start(_seed + 1))
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= B.TICK:
		_acc -= B.TICK
		if _freeze > 0:
			_freeze -= 1
			continue
		if demo:
			for i in players:
				_bots[i].drive(engine, i)
		else:
			_read_input()
		engine.tick()


func _read_input() -> void:
	var keys := [
		{"l": KEY_LEFT, "r": KEY_RIGHT, "u": KEY_UP, "d": KEY_DOWN},
		{"l": KEY_A, "r": KEY_D, "u": KEY_W, "d": KEY_S},
	]
	for i in players:
		var k: Dictionary = keys[i]
		var dir := Vector2(float(Input.is_key_pressed(k["r"])) - float(Input.is_key_pressed(k["l"])),
			float(Input.is_key_pressed(k["d"])) - float(Input.is_key_pressed(k["u"])))
		var pad := Vector2(Input.get_joy_axis(i, JOY_AXIS_LEFT_X), Input.get_joy_axis(i, JOY_AXIS_LEFT_Y))
		if pad.length() > 0.35:
			dir = pad.normalized()
		if Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_LEFT): dir.x = -1
		if Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_RIGHT): dir.x = 1
		if Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_UP): dir.y = -1
		if Input.is_joy_button_pressed(i, JOY_BUTTON_DPAD_DOWN): dir.y = 1
		var p: Dictionary = _press[i]
		engine.set_input(i, dir, p.get("attack", false), p.get("jump", false), p.get("pick", false))
		_press[i] = {}


func _unhandled_input(event: InputEvent) -> void:
	if engine == null or not event.is_pressed() or event.is_echo():
		return
	if demo:
		if not demo_locked and (event is InputEventKey or event is InputEventJoypadButton) and not event.is_action("ui_cancel"):
			demo = false
			start(-1, 1)
		return
	if over and event.is_action("ui_accept"):
		start()
		return
	if event is InputEventKey:
		match event.keycode:
			KEY_SPACE, KEY_Z: _press[0]["attack"] = true
			KEY_X: _press[0]["jump"] = true
			KEY_C: _press[0]["pick"] = true
			KEY_F: _join_or(1, "attack")
			KEY_G: _join_or(1, "jump")
	elif event is InputEventJoypadButton:
		var i: int = event.device
		if i > 1:
			return
		match event.button_index:
			JOY_BUTTON_X: _join_or(i, "attack")
			JOY_BUTTON_A: _join_or(i, "jump")
			JOY_BUTTON_B: _join_or(i, "pick")


## Player 2 joins by pressing a button (the next stage starts with two).
func _join_or(i: int, what: String) -> void:
	if i >= players:
		players = 2
		return
	_press[i][what] = true
