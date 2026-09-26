class_name CratesLevel
extends RefCounted
## A Crate Keeper puzzle in the standard Sokoban text format (.xsb/.sok), so the community's level collections
## load as they are:
##
##   #  wall   (space), - or _  floor   .  goal   $  crate   *  crate on a goal   @  keeper   +  keeper on a goal
##
## A file holds many levels, separated by blank lines or comment lines; a line "Title: ..." or a ";" comment
## right before or after a level names it. Our own sets also give "par=N" (the moves of a good solution) in a
## ";" line: "; par=42".

var name := ""
var par := 0
var solution := ""  ## a known solution in LURD notation (our sets carry one; the demo plays it)
var w := 0
var h := 0
var walls := PackedByteArray()
var floor_ := PackedByteArray()  ## 1 inside the reachable room (for drawing)
var goals: Array[Vector2i] = []
var crates: Array[Vector2i] = []
var keeper := Vector2i(-1, -1)


static func is_row(line: String) -> bool:
	if line.strip_edges() == "" or not line.contains("#"):
		return false
	for ch in line:
		if not ch in " #.$*@+-_\t":
			return false
	return true


static func parse_file(text: String) -> Array[CratesLevel]:
	var out: Array[CratesLevel] = []
	var rows: Array[String] = []
	var comment := ""  ## the last plain comment: names the puzzle that follows, unless a Title says otherwise
	var last: CratesLevel = null  ## Title, par and solution lines after a puzzle belong to it
	for raw in text.split("\n") + PackedStringArray([""]):
		var line := raw.rstrip("\r").replace("\t", "    ")
		if is_row(line):
			rows.append(line)
			continue
		if not rows.is_empty():
			var lv := parse_rows(rows)
			rows.clear()
			last = null
			if lv.keeper.x >= 0 and lv.crates.size() > 0:
				lv.name = comment if comment != "" else "Puzzle %d" % (out.size() + 1)
				out.append(lv)
				last = lv
			comment = ""
		var t := line.strip_edges().trim_prefix(";").strip_edges()
		if t == "":
			continue
		if t.to_lower().begins_with("title:"):
			if last:
				last.name = t.substr(6).strip_edges()
			else:
				comment = t.substr(6).strip_edges()
		elif t.begins_with("par="):
			if last:
				last.par = t.substr(4).to_int()
		elif t.begins_with("solution="):
			if last:
				last.solution = t.substr(9).strip_edges()
		elif line.strip_edges().begins_with(";"):
			comment = t
			last = null
	return out


static func parse_rows(rows: Array[String]) -> CratesLevel:
	var lv := CratesLevel.new()
	lv.h = rows.size()
	for r in rows:
		lv.w = maxi(lv.w, r.length())
	lv.walls.resize(lv.w * lv.h)
	lv.floor_.resize(lv.w * lv.h)
	for y in lv.h:
		for x in lv.w:
			var ch := rows[y][x] if x < rows[y].length() else " "
			var c := Vector2i(x, y)
			match ch:
				"#": lv.walls[y * lv.w + x] = 1
				".": lv.goals.append(c)
				"$": lv.crates.append(c)
				"*": lv.goals.append(c); lv.crates.append(c)
				"@": lv.keeper = c
				"+": lv.goals.append(c); lv.keeper = c
	# the room: floor reachable from the keeper without crossing walls (the outside stays dark)
	if lv.keeper.x >= 0:
		var q: Array[Vector2i] = [lv.keeper]
		lv.floor_[lv.keeper.y * lv.w + lv.keeper.x] = 1
		while not q.is_empty():
			var c: Vector2i = q.pop_back()
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var n: Vector2i = c + d
				if n.x >= 0 and n.y >= 0 and n.x < lv.w and n.y < lv.h and lv.walls[n.y * lv.w + n.x] == 0 and lv.floor_[n.y * lv.w + n.x] == 0:
					lv.floor_[n.y * lv.w + n.x] = 1
					q.append(n)
	return lv


func wall(c: Vector2i) -> bool:
	return c.x < 0 or c.y < 0 or c.x >= w or c.y >= h or walls[c.y * w + c.x] == 1


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < w and c.y < h and floor_[c.y * w + c.x] == 1
