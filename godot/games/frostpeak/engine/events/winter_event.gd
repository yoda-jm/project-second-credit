class_name WinterEvent
extends RefCounted
## One attempt at a Frostpeak event by one athlete: fixed ticks, a countdown, the run, then a result.
## Input is set by the game each tick (held up/down, and presses of left, right and action). With `auto` the
## event plays itself (CPU athletes in demo mode), with a little human error.

signal event(kind: String, data: Dictionary)

enum Phase { READY, RUN, DONE }

const TICK := 1.0 / 60.0

var phase := Phase.READY
var phase_left := 3.0
var time := 0.0  ## since the start of the run
var auto := false
var skill := 0.8  ## for auto play
var rng := RandomNumberGenerator.new()
var result := 0.0
var result_text := ""
var hold_up := false
var hold_down := false
var _left := false
var _right := false
var _action := false


func _init(seed: int = 1) -> void:
	rng.seed = seed


func press(what: String) -> void:
	match what:
		"left": _left = true
		"right": _right = true
		"action": _action = true


func tick() -> void:
	if auto:
		autoplay()
	var l := _left
	var r := _right
	var a := _action
	_left = false
	_right = false
	_action = false
	match phase:
		Phase.READY:
			phase_left -= TICK
			if a or l or r:
				early(l, r, a)
			if phase_left <= 0.0:
				phase = Phase.RUN
				event.emit("go", {})
		Phase.RUN:
			time += TICK
			run(l, r, a)
		Phase.DONE:
			pass


func finish(value: float, text: String) -> void:
	result = value
	result_text = text
	phase = Phase.DONE
	event.emit("finish", {"result": value, "text": text})


## Overridden by the events.
func early(_l: bool, _r: bool, _a: bool) -> void:
	pass


func run(_l: bool, _r: bool, _a: bool) -> void:
	pass


func autoplay() -> void:
	pass
