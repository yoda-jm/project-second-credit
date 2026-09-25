class_name DemoBot
extends RefCounted
## A simple autopilot for attract mode and demo recordings: each frame it walks toward the nearest reachable
## diamond (or the open exit), avoiding fireflies and stones overhead. Deterministic, so its runs are replays.

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")
const D = preload("res://games/glimmerdeep/engine/cave_directions.gd")
const DIRS: Array[int] = [D.UP, D.RIGHT, D.DOWN, D.LEFT]


static func next_move(c: CaveEngine) -> int:
	if c.player_state != CaveRendered.PlayerState.LIVING:
		return D.STILL
	var start := Vector2i(c.player_x, c.player_y)
	var first_step := {start: D.STILL}
	var queue: Array[Vector2i] = [start]
	var head := 0
	while head < queue.size():
		var p: Vector2i = queue[head]
		head += 1
		var here := c.get_cell(p.x, p.y)
		if p != start and (here == E.DIAMOND or here == E.OUTBOX):
			return first_step[p]
		for dir in DIRS:
			var n := Vector2i(p.x + D.DX[dir], p.y + D.DY[dir])
			if first_step.has(n) or not _safe(c, p, n, dir):
				continue
			first_step[n] = dir if p == start else first_step[p]
			queue.append(n)
	return D.STILL


static func _safe(c: CaveEngine, from: Vector2i, to: Vector2i, dir: int) -> bool:
	if to.x < 1 or to.y < 1 or to.x >= c.w - 1 or to.y >= c.h - 1:
		return false
	var e := c.get_cell(to.x, to.y)
	if not (e == E.SPACE or e == E.DIRT or e == E.DIAMOND or e == E.OUTBOX):
		return false
	# never stand under an open shaft topped by a stone or diamond (it falls as soon as it can)
	var y := to.y - 1
	while y > 0:
		var a := c.get_cell(to.x, y)
		if a == E.STONE or a == E.DIAMOND or a == E.STONE_F or a == E.DIAMOND_F:
			if y < to.y - 1 or a == E.STONE_F or a == E.DIAMOND_F:
				return false
			break
		if not (a == E.SPACE or (to.x == from.x and y == from.y)):
			break
		y -= 1
	if dir == D.DOWN:
		var over := c.get_cell(from.x, from.y - 1)
		if over == E.STONE or over == E.DIAMOND or over == E.STONE_F or over == E.DIAMOND_F:
			return false
	for d in DIRS:
		var f := c.get_cell(to.x + D.DX[d], to.y + D.DY[d])
		if (f >= E.FIREFLY_1 and f <= E.FIREFLY_4) or (f >= E.BUTTER_1 and f <= E.BUTTER_4):
			return false
	return true


## Runs the bot on a cave and returns {success, movements (BDCFF string), frames, score}.
static func record(cave: CaveStored, level: int = 0, seed: int = 0, max_frames: int = 3000) -> Dictionary:
	var c := CaveEngine.new(cave, level, seed)
	var moves := PackedByteArray()
	var score := 0
	while moves.size() < max_frames and c.player_state != CaveRendered.PlayerState.TIMEOUT \
			and c.player_state != CaveRendered.PlayerState.DIED:
		var m := next_move(c)
		moves.append(m)
		c.iterate(m, false, false)
		score += c.score
		if c.player_state == CaveRendered.PlayerState.EXITED:
			score += ReplayRunner.time_bonus(c)
			break
	return {"success": c.player_state == CaveRendered.PlayerState.EXITED, "movements": to_bdcff(moves),
		"frames": moves.size(), "score": score, "state": c.player_state}


static func to_bdcff(moves: PackedByteArray) -> String:
	const NAMES := [".", "u", "ur", "r", "dr", "d", "dl", "l", "ul"]
	var out := PackedStringArray()
	var i := 0
	while i < moves.size():
		var j := i
		while j < moves.size() and moves[j] == moves[i]:
			j += 1
		out.append(NAMES[moves[i]] + (str(j - i) if j - i > 1 else ""))
		i = j
	return " ".join(out)
