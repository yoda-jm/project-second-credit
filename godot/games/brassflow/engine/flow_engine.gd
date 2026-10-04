class_name FlowEngine
extends RefCounted
## Brassflow rules (a pipe-laying race in the Pipe Mania tradition; our own tuning), 60 Hz ticks. The board is a grid
## (10 x 7); a source sits on it, its outlet facing one way; some cells are blocked. A dispenser holds the next five
## pieces (straights, corners, crosses), drawn at random. The player puts the front piece on the cursor's cell (on an
## empty cell, or over a piece the flow has not reached yet: that one is scrapped, for a small cost and a pause).
## After a countdown the glow starts to flow from the source, filling one piece every so often: it must enter each
## piece by one of its openings and leave by the matching one. When it runs out (an empty cell, a blocked one, a piece
## that does not take it, the board's edge), the level ends: passed if it filled at least the level's length, else a
## chance is lost. A cross filled both ways scores a loop bonus. Fast flow (a key) sends it on quickly once you're done.
## Events: "place" {cell, piece}, "replace" {cell}, "flow_start", "fill" {cell, n, cross_twice}, "spill" {cell, why},
## "passed" {length, bonus}, "failed", "game_over", "fast".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DONE, OVER }
const TICK := 1.0 / 60.0
const COLS := 10
const ROWS := 7
const QUEUE := 5
## directions: 0 up (-row), 1 right, 2 down, 3 left
const DIRS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
## pieces and their openings (as direction sets)
const PIECES := {"h": [1, 3], "v": [0, 2], "ne": [0, 1], "nw": [0, 3], "se": [2, 1], "sw": [2, 3], "x": [0, 1, 2, 3]}
const DRAW := ["h", "v", "ne", "nw", "se", "sw", "h", "v", "x"]   ## the dispenser's odds (straights a little likelier)

var level := 0
var phase := Phase.READY
var phase_t := 1.0
var time := 0.0
var score := 0
var chances := 3
var length := 12              ## pieces the flow must fill to pass
var countdown := 18.0         ## seconds before the flow starts
var step_time := 2.0          ## seconds the flow takes through one piece
var grid := {}                ## cell -> {piece, filled: [dirs entered], }
var blocked := {}             ## cell -> true
var source := Vector2i(1, 3)
var source_dir := 1
var queue: Array[String] = []
var cursor := Vector2i(4, 3)
var place_pressed := false
var fast_pressed := false
var cool := 0.0               ## the pause after scrapping a piece
var flowing := false
var fast := false
var head := Vector2i.ZERO     ## the cell the flow is filling
var head_from := 0            ## the side it entered by (a direction from the cell)
var progress := 0.0           ## 0..1 through the head piece
var filled := 0
var rng := RandomNumberGenerator.new()


func _init(level_ := 0, score_ := 0, chances_ := 3, seed_ := 1) -> void:
	level = level_
	score = score_
	chances = chances_
	rng.seed = seed_ * 7919 + level_ * 31
	length = 10 + level * 2
	countdown = maxf(8.0, 18.0 - level * 1.2)
	step_time = maxf(0.7, 2.0 - level * 0.15)
	_layout()
	for i in QUEUE:
		queue.append(_draw())


func _draw() -> String:
	return DRAW[rng.randi() % DRAW.size()]


## The source somewhere along the left half, facing into the board, and a few blocked cells from level 2 on.
func _layout() -> void:
	source = Vector2i(rng.randi_range(1, 3), rng.randi_range(1, ROWS - 2))
	source_dir = [1, 2, 0][rng.randi() % 3]
	if source.y <= 1 and source_dir == 0:
		source_dir = 1
	if source.y >= ROWS - 2 and source_dir == 2:
		source_dir = 1
	var n := 0 if level < 1 else mini(2 + level, 7)
	var tries := 0
	while blocked.size() < n and tries < 100:
		tries += 1
		var c := Vector2i(rng.randi_range(0, COLS - 1), rng.randi_range(0, ROWS - 1))
		if c == source or c == source + DIRS[source_dir] or (c - source).length() < 2.0:
			continue
		blocked[c] = true
	cursor = source + (DIRS[source_dir] as Vector2i)


static func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < COLS and c.y < ROWS


static func opposite(d: int) -> int:
	return (d + 2) % 4


## Whether a piece takes the flow coming in from side d (d is the side of the cell it enters by).
static func accepts(piece: String, d: int) -> bool:
	return PIECES[piece].has(d)


## Where the flow goes out of a piece it entered by side d.
static func exit_of(piece: String, d: int) -> int:
	if piece == "x":
		return opposite(d)
	for o in PIECES[piece]:
		if o != d:
			return o
	return -1


func can_place(c: Vector2i) -> bool:
	if not inside(c) or blocked.has(c) or c == source:
		return false
	var g: Dictionary = grid.get(c, {})
	return g.is_empty() or g["filled"].is_empty()


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			place_pressed = false
			return
		Phase.DONE, Phase.OVER:
			phase_t -= TICK
			return
	cool = maxf(0.0, cool - TICK)
	if place_pressed and cool <= 0.0:
		_place()
	place_pressed = false
	if fast_pressed and not fast:
		fast = true
		countdown = minf(countdown, 0.5)
		event.emit("fast", {})
	fast_pressed = false
	if not flowing:
		countdown -= TICK
		if countdown <= 0.0:
			flowing = true
			head = source
			head_from = -1
			progress = 0.0
			event.emit("flow_start", {})
		return
	progress += TICK / (step_time * (0.08 if fast else 1.0)) * (1.0 if head != source else 1.5)
	if progress >= 1.0:
		progress = 0.0
		_advance()


func _place() -> void:
	var c := cursor
	if not can_place(c):
		return
	var piece: String = queue.pop_front()
	queue.append(_draw())
	if grid.has(c):
		score = maxi(0, score - 50)
		cool = 0.6
		event.emit("replace", {"cell": c})
	grid[c] = {"piece": piece, "filled": []}
	event.emit("place", {"cell": c, "piece": piece})


## The flow leaves the head piece and enters the next one, or spills.
func _advance() -> void:
	var out: int
	if head == source:
		out = source_dir
	else:
		out = exit_of(grid[head]["piece"], head_from)
	var nxt: Vector2i = head + DIRS[out]
	var enter := opposite(out)
	var why := ""
	if not inside(nxt):
		why = "edge"
	elif blocked.has(nxt):
		why = "blocked"
	elif not grid.has(nxt):
		why = "empty"
	elif not accepts(grid[nxt]["piece"], enter):
		why = "wrong"
	elif (grid[nxt]["filled"] as Array).has(enter) or (grid[nxt]["piece"] != "x" and not (grid[nxt]["filled"] as Array).is_empty()):
		why = "full"
	if why != "":
		event.emit("spill", {"cell": nxt, "why": why})
		_end()
		return
	var g: Dictionary = grid[nxt]
	var twice: bool = g["piece"] == "x" and not (g["filled"] as Array).is_empty()
	g["filled"].append(enter)
	head = nxt
	head_from = enter
	filled += 1
	var pts := 50 if not fast else 100
	if twice:
		pts += 500
	score += pts
	event.emit("fill", {"cell": nxt, "n": filled, "cross_twice": twice})


func _end() -> void:
	if filled >= length:
		var bonus := (filled - length) * 100
		score += bonus
		phase = Phase.DONE
		phase_t = 3.0
		event.emit("passed", {"length": filled, "bonus": bonus})
	else:
		chances -= 1
		phase = Phase.DONE if chances > 0 else Phase.OVER
		phase_t = 3.0
		event.emit("failed", {})
		if chances <= 0:
			event.emit("game_over", {})


## Whether the level was passed (once it is done).
func passed() -> bool:
	return phase == Phase.DONE and filled >= length
