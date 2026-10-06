class_name TorchGame
extends Node
## Runs Four Torches: level after level down the dungeon, the heroes' health, score, keys and potions carried down.
## The party: one to four heroes, each a player or a CPU companion. Player 1: the arrows (eight directions), space or
## enter to attack, P or right shift a potion; player 2: W A S D, F to attack, G a potion; players 3 and 4 on pads
## (the stick, A to attack, B a potion); the first pad drives player 1 too when nobody else uses it. F2, F3, F4 bring a
## hero in or hand them to the CPU. "--demo" lets CPUs play; "--players=N" (heroes), "--humans=N"; "--level=N".

signal level_started(engine: TorchEngine)
signal game_over()

const T = preload("res://games/fourtorches/engine/torch_engine.gd")

var engine: TorchEngine
var level := 0
var demo := false
var demo_locked := false
var over := false
var heroes := 4
var humans := 1
var _acc := 0.0
var _bots: Array[TorchBot] = []
var _games := 0
var high := 0


func start(at := 0) -> void:
	_games += 1
	level = maxi(0, at)
	over = false
	var party := []
	for i in heroes:
		party.append({"cls": T.ORDER[i], "cpu": demo or i >= humans, "health": 800})
	_load(party)


func _load(party: Array) -> void:
	# fallen heroes come back with a little health at a new level
	for p in party:
		if p.get("dead", false) or p.get("health", 800) <= 0:
			p["health"] = 300
			p["dead"] = false
	engine = TorchEngine.new(level, party, _games * 17 + 5)
	_bots.clear()
	for i in party.size():
		_bots.append(TorchBot.new(i))
	level_started.emit(engine)


func _process(delta: float) -> void:
	if engine == null or over:
		return
	if engine.phase == T.Phase.OVER and engine.phase_t <= 0.0:
		over = true
		for h in engine.heroes:
			high = maxi(high, h["score"])
		game_over.emit()
		if demo:
			get_tree().create_timer(6.0).timeout.connect(func(): start(0))
		return
	if engine.phase == T.Phase.EXIT and engine.phase_t <= 0.0:
		level += engine.jump
		_load(engine.party())
		return
	_acc = minf(_acc + delta, 0.25)
	while _acc >= T.TICK:
		_acc -= T.TICK
		for i in engine.heroes.size():
			var h := engine.heroes[i]
			if h["cpu"]:
				_bots[i].drive(engine)
			else:
				_steer(i, h)
		engine.tick()


func _steer(i: int, h: Dictionary) -> void:
	var v := Vector2.ZERO
	var fire := false
	var potion := false
	match i:
		0:
			if Input.is_physical_key_pressed(KEY_LEFT): v.x -= 1
			if Input.is_physical_key_pressed(KEY_RIGHT): v.x += 1
			if Input.is_physical_key_pressed(KEY_UP): v.y -= 1
			if Input.is_physical_key_pressed(KEY_DOWN): v.y += 1
			fire = Input.is_physical_key_pressed(KEY_SPACE) or Input.is_physical_key_pressed(KEY_ENTER)
			potion = Input.is_physical_key_pressed(KEY_P) or Input.is_physical_key_pressed(KEY_SHIFT)
			if humans == 1:
				if Input.is_physical_key_pressed(KEY_A): v.x -= 1
				if Input.is_physical_key_pressed(KEY_D): v.x += 1
				if Input.is_physical_key_pressed(KEY_W): v.y -= 1
				if Input.is_physical_key_pressed(KEY_S): v.y += 1
		1:
			if Input.is_physical_key_pressed(KEY_A): v.x -= 1
			if Input.is_physical_key_pressed(KEY_D): v.x += 1
			if Input.is_physical_key_pressed(KEY_W): v.y -= 1
			if Input.is_physical_key_pressed(KEY_S): v.y += 1
			fire = Input.is_physical_key_pressed(KEY_F)
			potion = Input.is_physical_key_pressed(KEY_G)
	var pad := i
	var stick := Vector2(Input.get_joy_axis(pad, JOY_AXIS_LEFT_X), Input.get_joy_axis(pad, JOY_AXIS_LEFT_Y))
	if stick.length() > 0.35:
		v = stick
	fire = fire or Input.is_joy_button_pressed(pad, JOY_BUTTON_A)
	potion = potion or Input.is_joy_button_pressed(pad, JOY_BUTTON_B)
	# eight directions, as on the old sticks
	if v.length() > 0.1:
		var a := snappedf(v.angle(), PI / 4.0)
		v = Vector2.from_angle(a)
		if fire:
			h["face"] = v
	h["move"] = v if not fire else Vector2.ZERO   # standing to shoot, as in the classic
	h["fire"] = fire
	h["potion_pressed"] = potion and not h.get("potion_was", false)
	h["potion_was"] = potion


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
	# F2..F4: a seat taken by a player, or given back to the CPU
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_F2, KEY_F3, KEY_F4]:
		var i: int = event.physical_keycode - KEY_F1
		if i < engine.heroes.size():
			engine.heroes[i]["cpu"] = not engine.heroes[i]["cpu"]
			humans = engine.heroes.filter(func(h): return not h["cpu"]).size()
