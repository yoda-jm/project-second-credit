class_name MossGame
extends Node
## Runs Mossfolk: the levels in turn (a level is passed by saving enough; otherwise it is played again), 17 logic
## steps a second. Keys 1-8 (or the skill bar) pick a skill, a click gives it to the mossling under the cursor;
## - and + change the release rate, P pauses, N twice pops them all, the arrows (or the screen edges) scroll.
## The demo plays each level's recorded solution. "--level=N" (user argument) starts at a level.

signal level_started(engine: MossEngine)
signal level_done(engine: MossEngine, passed: bool)

const E = preload("res://games/mossfolk/engine/moss_engine.gd")
const FILE := "res://games/mossfolk/levels/first-steps.moss"

var engine: MossEngine
var levels: Array[MossLevel] = []
var index := 0
var demo := false
var demo_locked := false
var skill := "dig"          ## the skill picked on the bar
var hover := -1             ## the mossling under the cursor
var result := false         ## the result card is showing
var speed := 1.0            ## fast forward (F)
var _acc := 0.0
var _demo: MossDemo
var _nuke_armed := 0.0


func start(at := 0) -> void:
	levels = MossLevel.parse_file(FileAccess.get_file_as_string(FILE))
	index = clampi(at, 0, levels.size() - 1)
	load_level()


func load_level() -> void:
	# a fresh copy: the terrain is eaten as they play
	var lv: MossLevel = MossLevel.parse_file(FileAccess.get_file_as_string(FILE))[index]
	engine = MossEngine.new(lv)
	_demo = MossDemo.new()
	result = false
	skill = _first_skill()
	level_started.emit(engine)


func _first_skill() -> String:
	for s in E.SKILLS:
		if engine.skills[s] > 0:
			return s
	return "dig"


func _process(delta: float) -> void:
	if engine == null:
		return
	_nuke_armed = maxf(0.0, _nuke_armed - delta)
	if engine.over:
		if not result:
			result = true
			var passed := engine.saved >= engine.level.save
			level_done.emit(engine, passed)
			if demo:
				get_tree().create_timer(4.0).timeout.connect(func(): _next(true))
		return
	_acc = minf(_acc + delta * speed, 0.5)
	while _acc >= E.TICK:
		_acc -= E.TICK
		if demo:
			_demo.drive(engine)
		engine.tick()


func _next(passed: bool) -> void:
	if passed:
		index = (index + 1) % levels.size()
	load_level()


func give(id: int) -> bool:
	if id < 0 or demo:
		return false
	return engine.assign(id, skill)


func pick_skill(s: String) -> void:
	skill = s


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
	if result:
		if event.is_action_pressed("ui_accept"):
			_next(engine.saved >= engine.level.save)
		return
	if event is InputEventKey and event.pressed and not event.echo:
		var k: int = event.physical_keycode
		if k >= KEY_1 and k <= KEY_8:
			skill = E.SKILLS[k - KEY_1]
		match k:
			KEY_MINUS, KEY_KP_SUBTRACT: engine.rate = maxi(engine.level.rate, engine.rate - 5)
			KEY_EQUAL, KEY_PLUS, KEY_KP_ADD: engine.rate = mini(99, engine.rate + 5)
			KEY_P: engine.paused = not engine.paused
			KEY_F: speed = 3.0 if speed == 1.0 else 1.0
			KEY_R: load_level()
			KEY_N:
				if _nuke_armed > 0.0:
					engine.nuke()
				_nuke_armed = 0.6
