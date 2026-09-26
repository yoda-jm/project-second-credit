class_name PrismLevel
extends RefCounted
## A Prism Breaker wall, 13 bricks wide, in our own text format (a file holds several, each after [level]):
##
##   [level]
##   name=First Light
##   .............        .  empty   a-f  crystal bricks in six colours (one hit)   H  hard (several hits)
##   .aabbccddeef.        S  steel (never breaks)   G  gold (never breaks)
##
## Level sets written for LBreakout2 can be read too (their "Bricks:" grid: '.' empty, '#' or '*' unbreakable, any
## other character a breakable brick, coloured by its letter); only the layout is used.

const W := 13

var name := ""
var rows: Array[String] = []  ## normalised: . a-f H S G


static func parse_file(text: String) -> Array[PrismLevel]:
	if text.contains("Bricks:"):
		return _parse_lbreakout(text)
	var out: Array[PrismLevel] = []
	var cur: PrismLevel = null
	for raw in text.split("\n"):
		var line := raw.rstrip("\r")
		if line.begins_with(";"):
			continue
		if line.strip_edges() == "[level]":
			if cur and not cur.rows.is_empty():
				out.append(cur)
			cur = PrismLevel.new()
			continue
		if cur == null:
			continue
		if line.begins_with("name="):
			cur.name = line.substr(5).strip_edges()
		elif line.strip_edges() != "":
			cur.rows.append(_norm(line))
	if cur and not cur.rows.is_empty():
		out.append(cur)
	return out


static func _norm(line: String) -> String:
	var s := ""
	for i in W:
		var ch := line[i] if i < line.length() else "."
		s += ch if ch in ".abcdefHSG" else "."
	return s


static func _parse_lbreakout(text: String) -> Array[PrismLevel]:
	var out: Array[PrismLevel] = []
	var lines := text.split("\n")
	var i := 0
	var title := ""
	while i < lines.size():
		var l := lines[i].strip_edges()
		if l.begins_with("Title:"):
			title = l.substr(6).strip_edges()
		if l == "Bricks:":
			var lv := PrismLevel.new()
			lv.name = title if title != "" else "Wall %d" % (out.size() + 1)
			i += 1
			while i < lines.size() and lines[i].strip_edges() != "" and not lines[i].contains(":"):
				var src := lines[i].rstrip("\r")
				var row := ""
				# 14 columns there, 13 here: drop the last column
				for x in W:
					var ch := src[x] if x < src.length() else "."
					if ch == "." or ch == " ":
						row += "."
					elif ch == "#" or ch == "*":
						row += "S"
					else:
						row += "abcdef"[ch.unicode_at(0) % 6]
				lv.rows.append(row)
				i += 1
			out.append(lv)
			title = ""
		i += 1
	return out
