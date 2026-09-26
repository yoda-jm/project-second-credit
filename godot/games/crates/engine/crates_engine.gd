class_name CratesEngine
extends RefCounted
## Crate Keeper rules: the keeper walks the grid and pushes one crate at a time (never pulls, never two); the
## puzzle is solved when every goal holds a crate. Every move is recorded, so undo and redo work all the way back.
## Events: "move" {from, to, dir, pushed (crate index or -1)}, "bump" {dir}, "on_goal" / "off_goal" {crate},
## "solved", "undo", "redo", "restart".

signal event(kind: String, data: Dictionary)

const DIRS := {"u": Vector2i(0, -1), "d": Vector2i(0, 1), "l": Vector2i(-1, 0), "r": Vector2i(1, 0)}

var level: CratesLevel
var keeper := Vector2i.ZERO
var crates: Array[Vector2i] = []
var goals := {}
var moves := 0
var pushes := 0
var solved := false
var history: Array[Dictionary] = []   ## {dir, pushed}
var future: Array[Dictionary] = []    ## undone moves, for redo
var face := Vector2i(0, 1)


func _init(lv: CratesLevel) -> void:
	level = lv
	reset()


func reset() -> void:
	keeper = level.keeper
	crates = level.crates.duplicate()
	goals.clear()
	for g in level.goals:
		goals[g] = true
	moves = 0
	pushes = 0
	solved = false
	history.clear()
	future.clear()


func crate_at(c: Vector2i) -> int:
	return crates.find(c)


func on_goal_count() -> int:
	var n := 0
	for c in crates:
		if goals.has(c):
			n += 1
	return n


## Tries one step; returns true if the keeper moved.
func step(d: Vector2i, record := true) -> bool:
	if solved and record:
		return false
	face = d
	var n := keeper + d
	if level.wall(n):
		event.emit("bump", {"dir": d})
		return false
	var ci := crate_at(n)
	if ci >= 0:
		var beyond := n + d
		if level.wall(beyond) or crate_at(beyond) >= 0:
			event.emit("bump", {"dir": d})
			return false
		var was_goal := goals.has(n)
		crates[ci] = beyond
		pushes += 1
		if goals.has(beyond) and not was_goal:
			event.emit("on_goal", {"crate": ci})
		elif was_goal and not goals.has(beyond):
			event.emit("off_goal", {"crate": ci})
	var from := keeper
	keeper = n
	moves += 1
	if record:
		history.append({"dir": d, "pushed": ci})
		future.clear()
	event.emit("move", {"from": from, "to": n, "dir": d, "pushed": ci})
	if on_goal_count() == goals.size() and not solved:
		solved = true
		event.emit("solved", {"moves": moves, "pushes": pushes})
	return true


func undo() -> bool:
	if history.is_empty():
		return false
	var h: Dictionary = history.pop_back()
	var d: Vector2i = h["dir"]
	var ci: int = h["pushed"]
	if ci >= 0:
		var was_goal := goals.has(crates[ci])
		crates[ci] -= d
		pushes -= 1
		if goals.has(crates[ci]) and not was_goal:
			event.emit("on_goal", {"crate": ci})
		elif was_goal and not goals.has(crates[ci]):
			event.emit("off_goal", {"crate": ci})
	var from := keeper
	keeper -= d
	moves -= 1
	face = d
	solved = false
	future.append(h)
	event.emit("undo", {"from": from, "to": keeper, "dir": -d, "pushed": ci})
	return true


func redo() -> bool:
	if future.is_empty():
		return false
	var h: Dictionary = future.pop_back()
	var keep := future.duplicate()
	var ok := step(h["dir"], false)
	if ok:
		history.append(h)
	future = keep
	event.emit("redo", {})
	return ok


func restart() -> void:
	reset()
	event.emit("restart", {})


## Plays a solution in LURD notation (lowercase moves, uppercase pushes; case is not checked).
func play(lurd: String) -> void:
	for ch in lurd.to_lower():
		if DIRS.has(ch):
			step(DIRS[ch])


## The shortest keeper walk to a cell (for click-to-move), or [] if none.
func walk_to(target: Vector2i) -> Array[Vector2i]:
	var first := {keeper: Vector2i.ZERO}
	var q: Array[Vector2i] = [keeper]
	var head := 0
	while head < q.size():
		var c := q[head]
		head += 1
		if c == target:
			var path: Array[Vector2i] = []
			var p := c
			while p != keeper:
				var d: Vector2i = first[p]
				path.push_front(d)
				p -= d
			return path
		for d in DIRS.values():
			var n: Vector2i = c + d
			if not first.has(n) and not level.wall(n) and crate_at(n) < 0:
				first[n] = d
				q.append(n)
	return []
