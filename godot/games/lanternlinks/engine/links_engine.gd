class_name LinksEngine
extends RefCounted
## A round of Lantern Links: the holes in order, one to four players in hot seat (honours: the best score on the
## last hole tees off first), strokes, the stroke limit, water penalties, the scorecard. Ticks at 60 Hz; the hole
## clock runs all the time, so the gadgets keep turning while a player aims. Emits `event(kind, data)` for the view,
## the HUD and the sound.

signal event(kind: String, d: Dictionary)

const B = preload("res://games/lanternlinks/engine/links_ball.gd")
const P = preload("res://games/lanternlinks/engine/links_physics.gd")

enum Phase { INTRO, TEE, AIM, ROLL, SUNK, LOST, PICKUP, CARD, FINAL }

const TICK := P.TICK
const MAX_STROKES := 8
const INTRO_T := 3.2
const TEE_T := 0.7
const SUNK_T := 2.2
const LOST_T := 1.5
const PICKUP_T := 1.6
const CARD_T := 5.0
const COLORS: Array[Color] = [Color(1.0, 0.95, 0.85), Color(1.0, 0.45, 0.35), Color(0.35, 0.75, 1.0), Color(1.0, 0.85, 0.25)]
const NAMES := {-3: "ALBATROSS", -2: "EAGLE", -1: "BIRDIE", 0: "PAR", 1: "BOGEY", 2: "DOUBLE BOGEY", 3: "TRIPLE BOGEY"}

var holes: Array[LinksHole] = []
var hole_i := 0
var hole: LinksHole
var players: Array[Dictionary] = []   ## {name, cpu, color, scores: Array[int] (-1 unplayed)}
var order: Array[int] = []            ## the tee order on this hole
var turn := 0                         ## index in `order`
var ball := LinksBall.new()
var strokes := 0                      ## the current player's strokes on this hole
var clock := 0.0                      ## the hole clock (gadgets)
var phase := Phase.INTRO
var phase_t := 0.0
var shot_from := Vector2.ZERO
var last_power := 0.0
var rng := RandomNumberGenerator.new()
var _ev: Array = []


func _init(course: Array[LinksHole], who: Array[Dictionary], first := 0, seed_value := 1) -> void:
	holes = course
	rng.seed = seed_value
	for i in who.size():
		var p: Dictionary = who[i].duplicate()
		p["color"] = COLORS[i % COLORS.size()]
		var sc: Array[int] = []
		sc.resize(holes.size())
		sc.fill(-1)
		p["scores"] = sc
		players.append(p)
	_start_hole(clampi(first, 0, holes.size() - 1))


func player() -> Dictionary:
	return players[order[turn]]


func player_index() -> int:
	return order[turn]


func total(p: int) -> int:
	var t := 0
	for s in players[p]["scores"]:
		if s > 0:
			t += s
	return t


## Strokes against par over the holes played.
func to_par(p: int) -> int:
	var t := 0
	for i in holes.size():
		var s: int = players[p]["scores"][i]
		if s > 0:
			t += s - holes[i].par
	return t


func par_total() -> int:
	var t := 0
	for h in holes:
		t += h.par
	return t


static func result_name(strokes_: int, par_: int) -> String:
	if strokes_ == 1:
		return "HOLE IN ONE"
	return NAMES.get(strokes_ - par_, "+%d" % (strokes_ - par_))


func _start_hole(i: int) -> void:
	hole_i = i
	hole = holes[i]
	clock = 0.0
	# honours: the best score on the last hole goes first (a stable sort keeps the seating order on ties)
	order.clear()
	for k in players.size():
		order.append(k)
	if i > 0:
		order.sort_custom(func(a, b):
			var sa: int = players[a]["scores"][i - 1]
			var sb: int = players[b]["scores"][i - 1]
			return sa < sb or (sa == sb and a < b))
	turn = 0
	ball.place(hole.tee, hole.height(hole.tee))
	_go(Phase.INTRO)
	_emit("hole", {"index": i})


func _go(p: Phase) -> void:
	phase = p
	phase_t = 0.0


func _emit(kind: String, d: Dictionary) -> void:
	event.emit(kind, d)


## Skips the hole's fly-over or the scorecard.
func skip() -> void:
	if phase == Phase.INTRO and phase_t > 0.3:
		_tee_up()
	elif phase == Phase.CARD and phase_t > 0.5:
		_next_hole()


func can_shoot() -> bool:
	return phase == Phase.AIM


## Strikes the ball: `angle` on the plan (0 east, PI/2 south), `power` 0..1 of a full stroke.
func shoot(angle: float, power: float) -> void:
	if phase != Phase.AIM:
		return
	power = clampf(power, 0.0, 1.0)
	strokes += 1
	last_power = power
	shot_from = ball.pos
	ball.vel = Vector2.from_angle(angle) * power * P.MAX_SPEED
	ball.at_rest = false
	ball.hits = 0
	_go(Phase.ROLL)
	_emit("shot", {"pos": ball.pos, "power": power, "angle": angle, "player": player_index(), "strokes": strokes})


func tick() -> void:
	phase_t += TICK
	match phase:
		Phase.INTRO:
			if phase_t >= INTRO_T:
				_tee_up()
		Phase.TEE:
			if phase_t >= TEE_T:
				_go(Phase.AIM)
				_emit("aim", {"player": player_index()})
		Phase.ROLL:
			_ev.clear()
			P.tick(hole, ball, clock, _ev)
			for e in _ev:
				_emit(e[0], e[1])
			if ball.mode == B.Mode.SUNK:
				_go(Phase.SUNK)
				_record(strokes)
				_emit("holed", {"player": player_index(), "strokes": strokes, "par": hole.par,
					"name": result_name(strokes, hole.par)})
			elif ball.mode == B.Mode.LOST:
				strokes += 1
				_go(Phase.LOST)
				_emit("penalty", {"player": player_index(), "strokes": strokes})
			elif ball.at_rest:
				_after_rest()
		Phase.SUNK:
			P.tick(hole, ball, clock, null)
			if phase_t >= SUNK_T:
				_next_turn()
		Phase.LOST:
			if phase_t >= LOST_T:
				if strokes >= MAX_STROKES:
					_pick_up()
				else:
					ball.place(shot_from, hole.height(shot_from))
					_go(Phase.AIM)
					_emit("replace", {"pos": shot_from})
		Phase.PICKUP:
			if phase_t >= PICKUP_T:
				_next_turn()
		Phase.CARD:
			if phase_t >= CARD_T:
				_next_hole()
	clock += TICK


func _after_rest() -> void:
	if strokes >= MAX_STROKES:
		_pick_up()
	else:
		_go(Phase.AIM)
		_emit("aim", {"player": player_index()})


func _pick_up() -> void:
	_record(MAX_STROKES + 1)
	_go(Phase.PICKUP)
	_emit("pickup", {"player": player_index(), "strokes": MAX_STROKES + 1})


func _record(s: int) -> void:
	players[player_index()]["scores"][hole_i] = s


func _tee_up() -> void:
	strokes = 0
	ball.place(hole.tee, hole.height(hole.tee))
	_go(Phase.TEE)
	_emit("tee", {"player": player_index()})


func _next_turn() -> void:
	turn += 1
	if turn >= order.size():
		turn = 0
		_go(Phase.CARD)
		_emit("card", {"index": hole_i})
		return
	_tee_up()


func _next_hole() -> void:
	if hole_i + 1 >= holes.size():
		_go(Phase.FINAL)
		_emit("final", {"winners": winners()})
		return
	_start_hole(hole_i + 1)


## The players with the lowest total (ties share the win).
func winners() -> Array[int]:
	var best := 1 << 30
	var out: Array[int] = []
	for p in players.size():
		var t := total(p)
		if t < best:
			best = t
			out = [p]
		elif t == best:
			out.append(p)
	return out
