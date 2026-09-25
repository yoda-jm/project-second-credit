class_name BdcffLoader
extends RefCounted
## Reads BDCFF cave sets (the Boulder Dash Common File Format, versions 0.32 to 0.5 with GDash extensions).
## Port of GDash's fileops/bdcffload.cpp (MIT, Copyright (c) 2007-2013 Czirkos Zoltan; see GDASH_LICENSE.txt),
## including its compatibility quirks, so community cave sets load exactly as in GDash.

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")

var _warnings := PackedStringArray()
var _context := ""


static func load_file(path: String) -> CaveSet:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		var cs := CaveSet.new()
		cs.warnings.append("cannot open %s" % path)
		return cs
	var bytes := f.get_buffer(f.get_length())
	var text := bytes.get_string_from_utf8()
	if text.is_empty() and not bytes.is_empty():
		text = bytes.get_string_from_ascii()
	return load_string(text)


static func load_string(text: String) -> CaveSet:
	return BdcffLoader.new()._load(text)


func _warn(msg: String) -> void:
	_warnings.append(("%s: %s" % [_context, msg]) if _context != "" else msg)


func _load(text: String) -> CaveSet:
	var file := _parse_sections(text)
	var default_cave := CaveStored.new()
	var ctet := CaveNames.default_char_table()
	var version := "0.32"
	for line in file["bdcff"]:
		var ap := _attrib_param(line)
		if ap.is_empty():
			continue
		if ap[0].to_lower() == "version":
			version = ap[1]
		elif ap[0].to_lower() == "engine":
			_cave_process_tag(default_cave, ap[0], ap[1])
		else:
			_warn("invalid attribute: %s" % ap[0])
	var cs := CaveSet.new()
	# [game]: GDash reads it twice, first with the special cave tags, then as plain properties.
	for pass_no in 2:
		for line in file["game"]:
			var ap := _attrib_param(line)
			if ap.is_empty():
				continue
			var a: String = ap[0].to_lower()
			if a == "caves" or a == "levels":
				continue
			if _set_property(cs, CaveSet.DESCRIPTORS, ap[0], ap[1], 0):
				continue
			var ok: bool
			if pass_no == 0:
				ok = _cave_process_tag(default_cave, ap[0], ap[1])
			else:
				ok = _set_property(default_cave, CaveProperties.DESCRIPTORS, ap[0], ap[1], default_cave.w * default_cave.h)
			if not ok:
				_warn("invalid attribute: %s" % ap[0])
	for line in file["game_highscore"]:
		var parts := (line as String).split(" ", true, 1)
		if parts.size() == 2 and parts[0].is_valid_int():
			cs.highscore.append([parts[0].to_int(), parts[1]])
	for line in file["mapcodes"]:
		var ap := _attrib_param(line)
		if ap.is_empty():
			continue
		if ap[0].to_lower() == "length":
			if ap[1] != "1":
				_warn("only one-character map codes are supported")
		else:
			var el := CaveNames.element(ap[1])
			if el >= 0:
				ctet[ap[0].substr(0, 1)] = el
			else:
				_warn("unknown element name for map char: %s" % ap[1])

	for info in file["caves"]:
		var cave := CaveStored.new()
		cave.copy_properties_from(default_cave)
		cs.caves.append(cave)
		_cave_process_all_tags(cave, info["properties"])
		for line in info["highscore"]:
			var parts := (line as String).split(" ", true, 1)
			if parts.size() == 2 and parts[0].is_valid_int():
				cave.highscore.append([parts[0].to_int(), parts[1]])
		var map_lines: Array = info["map"]
		if not map_lines.is_empty():
			cave.map.resize(cave.w * cave.h)
			cave.map.fill(cave.initial_border)
			if map_lines.size() != cave.h:
				_warn("map error: cave height=%d, map height=%d" % [cave.h, map_lines.size()])
			for y in mini(cave.h, map_lines.size()):
				var row: String = map_lines[y]
				for x in mini(row.length(), cave.w):
					var ch := row[x]
					if ctet.has(ch):
						cave.map[y * cave.w + x] = ctet[ch]
					else:
						_warn("invalid character representing element: %s" % ch)
						cave.map[y * cave.w + x] = E.UNKNOWN
		var levels := [true, true, true, true, true]
		for line in info["objects"]:
			var l: String = line
			if l.to_lower() == "[/level]":
				levels = [true, true, true, true, true]
			elif l.to_lower().begins_with("[level="):
				levels = [false, false, false, false, false]
				var ok := true
				for part in l.substr(l.find("=") + 1).replace("]", "").split(",", false):
					var i := part.strip_edges().to_int() - 1
					if i >= 0 and i < 5:
						levels[i] = true
					else:
						ok = false
				if not ok:
					_warn("invalid [Level=xxx] specification")
					levels = [true, true, true, true, true]
			else:
				var o := CaveObjects.parse(l)
				if o.is_empty():
					_warn("invalid object specification: %s" % l)
				else:
					o["seen_on"] = levels.duplicate()
					cave.objects.append(o)
		for section in info["replays"]:
			var replay := CaveReplay.new()
			for rl in section:
				var line: String = rl
				if line.find("=") >= 0:
					var ap := _attrib_param(line)
					if ap[0].to_lower() == "movements":
						replay.load_movements(ap[1])
					else:
						_set_property(replay, CaveReplay.DESCRIPTORS, ap[0], ap[1], 0)
				else:
					replay.load_movements(line)
			cave.replays.append(replay)
		for demo in info["demo"]:
			var replay := CaveReplay.new()
			replay.player_name = "???"
			replay.load_movements(demo)
			cave.replays.append(replay)
		_context = ""

	# Old files: intermissions without a size are 40x22 with the 20x12 upper-left corner visible.
	if version == "0.32":
		for cave in cs.caves:
			if cave.intermission and not cave.has_map():
				cave.w = 40
				cave.h = 22
				cave.x1 = 0
				cave.y1 = 0
				cave.x2 = 19
				cave.y2 = 11
				var b := cave.initial_border
				cave.objects.append({"type": "fillrect", "p1": Vector2i(0, 11), "p2": Vector2i(39, 21),
					"element": b, "fill": b, "seen_on": [true, true, true, true, true]})
				cave.objects.append({"type": "fillrect", "p1": Vector2i(19, 0), "p2": Vector2i(39, 21),
					"element": b, "fill": b, "seen_on": [true, true, true, true, true]})
	cs.warnings = _warnings
	return cs


func _parse_sections(text: String) -> Dictionary:
	var file := {"bdcff": [], "game": [], "game_highscore": [], "mapcodes": [], "caves": []}
	var state := "start"
	var caves: Array = file["caves"]
	var lineno := 0
	for raw in text.split("\n"):
		lineno += 1
		var line: String = raw.replace("\r", "")
		if line.is_empty():
			continue
		if state != "map" and line[0] == ";":
			continue
		if line[0] == "[":
			var tag := line.strip_edges().to_lower()
			match tag:
				"[bdcff]": state = "bdcff"
				"[/bdcff]": state = "start"
				"[game]": state = "game"
				"[/game]": pass
				"[mapcodes]": state = "game_mapcodes" if state == "game" else "bdcff_mapcodes"
				"[/mapcodes]": state = "bdcff" if state == "bdcff_mapcodes" else "game"
				"[cave]":
					state = "cave"
					caves.append({"properties": [], "map": [], "objects": [], "replays": [], "demo": [], "highscore": []})
				"[/cave]": state = "game"
				"[map]":
					if state == "cave": state = "map"
				"[/map]": state = "cave"
				"[highscore]": state = "game_highscore" if state == "game" else "cave_highscore"
				"[/highscore]": state = "game" if state == "game_highscore" else "cave"
				"[objects]":
					if caves.is_empty(): caves.append({"properties": [], "map": [], "objects": [], "replays": [], "demo": [], "highscore": []})
					state = "objects"
				"[/objects]": state = "cave"
				"[demo]":
					state = "demo"
					caves.back()["demo"].append("")
				"[/demo]": state = "cave"
				"[replay]":
					state = "replay"
					caves.back()["replays"].append([])
				"[/replay]": state = "cave"
				_:
					if tag.begins_with("[level=") or tag == "[/level]":
						if state == "objects":
							caves.back()["objects"].append(line.strip_edges())
					else:
						_warn("line %d: unknown section %s" % [lineno, line])
			continue
		if state == "map":
			caves.back()["map"].append(line)
			continue
		line = line.strip_edges(false, true)
		match state:
			"bdcff": file["bdcff"].append(line)
			"game": file["game"].append(line)
			"game_highscore": file["game_highscore"].append(line)
			"game_mapcodes", "bdcff_mapcodes": file["mapcodes"].append(line)
			"cave": caves.back()["properties"].append(line)
			"replay": caves.back()["replays"].back().append(line)
			"demo":
				var d: Array = caves.back()["demo"]
				d[d.size() - 1] = d.back() + line + " "
			"cave_highscore": caves.back()["highscore"].append(line)
			"objects": caves.back()["objects"].append(line)
			"start": _warn("line %d: nothing allowed outside [BDCFF]" % lineno)
	return file


func _attrib_param(line: String) -> Array:
	var eq := line.find("=")
	if eq < 0:
		return []
	return [line.substr(0, eq), line.substr(eq + 1)]


func _cave_process_all_tags(cave: CaveStored, lines: Array) -> void:
	var rest := lines.duplicate()
	_process_specific(cave, rest, "Name")
	_context = "cave '%s'" % cave.name if cave.name != "" else "<unnamed cave>"
	_process_specific(cave, rest, "Engine")
	_process_specific(cave, rest, "Intermission")
	_process_specific(cave, rest, "Size")
	if _process_specific(cave, rest, "SlimePermeability"):
		cave.slime_predictable = false
	if _process_specific(cave, rest, "SlimePermeabilityC64"):
		cave.slime_predictable = true
	if _process_specific(cave, rest, "CaveDelay"):
		if cave.scheduling == CaveScheduling.MILLISECONDS:
			cave.scheduling = CaveScheduling.PLCK
	if _process_specific(cave, rest, "FrameTime"):
		cave.scheduling = CaveScheduling.MILLISECONDS
	for line in rest:
		var ap := _attrib_param(line)
		if ap.is_empty():
			_warn("cannot parse line: %s" % line)
		elif not _cave_process_tag(cave, ap[0], ap[1]):
			_warn("unknown tag '%s'" % ap[0])
			cave.unknown_tags += line + "\n"


func _process_specific(cave: CaveStored, lines: Array, name: String) -> bool:
	var prefix := name.to_lower() + "="
	for i in lines.size():
		if (lines[i] as String).to_lower().begins_with(prefix):
			var ap := _attrib_param(lines[i])
			_cave_process_tag(cave, ap[0], ap[1])
			lines.remove_at(i)
			return true
	return false


## Special cave tags first (GDash's cave_process_tags_func), then the generic property table.
func _cave_process_tag(cave: CaveProperties, attrib: String, param: String) -> bool:
	var a := attrib.to_lower()
	var params := param.split(" ", false)
	match a:
		"snapexplosions":
			var b = _read_bool(param)
			if b == null:
				_warn("invalid param for '%s': '%s'" % [attrib, param])
			else:
				cave.snap_element = E.EXPLODE_1 if b else E.SPACE
			return true
		"bd1scheduling":
			var b = _read_bool(param)
			if b == null:
				_warn("invalid param for '%s': '%s'" % [attrib, param])
			elif b and cave.scheduling == CaveScheduling.PLCK:
				cave.scheduling = CaveScheduling.BD1
			return true
		"engine":
			if not CaveEngineDefaults.apply(cave, param.strip_edges()):
				_warn("invalid param for '%s': '%s'" % [attrib, param])
			return true
		"amoebaproperties":
			var e1 := CaveNames.element(params[0]) if params.size() > 0 else -1
			var e2 := CaveNames.element(params[1]) if params.size() > 1 else -1
			if e1 >= 0 and e2 >= 0:
				cave.amoeba_too_big_effect = e1
				cave.amoeba_enclosed_effect = e2
			else:
				_warn("invalid param for '%s': '%s'" % [attrib, param])
			return true
		"colors":
			var c := Array(params)
			var names := ["colorb", "color0", "color1", "color2", "color3", "color4", "color5"]
			var vals: Array
			if c.size() == 3:
				vals = ["C64:0", "C64:0", c[0], c[1], c[2], c[2], c[0]]
			elif c.size() == 5:
				vals = [c[0], c[1], c[2], c[3], c[4], c[4], c[2]]
			elif c.size() == 7:
				vals = c
			else:
				_warn("invalid param for '%s': '%s'" % [attrib, param])
				return true
			for i in 7:
				cave.set(names[i], vals[i])
			return true
		"effect":
			if params.size() != 2:
				_warn("invalid effect specification '%s'" % param)
				return true
			for d in CaveProperties.DESCRIPTORS:
				if d[1] == "EFFECT" and (d[0] as String).to_lower() == params[0].to_lower():
					var el := CaveNames.element(params[1])
					if el >= 0:
						cave.set(d[2], E.nonscanned_pair(el))
					else:
						_warn("cannot read element name '%s'" % params[1])
					return true
			var p0 := params[0].to_lower()
			var el := CaveNames.element(params[1])
			if p0 == "bouncing_boulder" and el >= 0:
				cave.stone_bouncing_effect = E.nonscanned_pair(el)
			elif p0 == "explosion3s" and el >= 0:
				cave.explosion_3_effect = E.nonscanned_pair(el)
			elif p0 == "starting_faling_diamond" and el >= 0:
				cave.diamond_falling_effect = E.nonscanned_pair(el)
			elif p0 == "dirt" and el >= 0:
				cave.dirt_looks_like = el
			elif p0 == "hexpanding_wall" and params[1].to_lower() == "steel_hexpanding_wall":
				cave.expanding_wall_looks_like = el
			else:
				_warn("invalid effect name '%s'" % params[0])
			return true
	return _set_property(cave, CaveProperties.DESCRIPTORS, attrib, param, cave.w * cave.h)


## GDash's struct_set_property: fills every descriptor row with this identifier, word by word.
func _set_property(obj: Object, descriptors: Array, attrib: String, param: String, ratio: int) -> bool:
	var params := param.split(" ", false)
	var index := 0
	var found := false
	var was_string := false
	var a := attrib.to_lower()
	for d in descriptors:
		if (d[0] as String).to_lower() != a:
			continue
		found = true
		var typ: String = d[1]
		var member: String = d[2]
		var flags: String = d[3] if d.size() > 3 else ""
		if typ == "STRING":
			obj.set(member, param)
			was_string = true
			continue
		if typ == "LONGSTRING":
			obj.set(member, param.c_unescape())
			was_string = true
			continue
		var count := 5 if typ.ends_with("_LEVELS") else 1
		var j := 0
		while j < count and index < params.size():
			var s: String = params[index]
			var value = null
			match typ:
				"BOOLEAN":
					value = _read_bool(s)
				"INT", "INT_LEVELS":
					value = _read_ratio(s, ratio) if flags.contains("RATIO_TO_CAVE_SIZE") else _read_int(s)
				"PROBABILITY", "PROBABILITY_LEVELS":
					value = _read_ratio(s, 1000000)
				"ELEMENT", "EFFECT":
					var el := CaveNames.element(s)
					value = el if el >= 0 else null
				"DIRECTION":
					var di := CaveDirections.FILE_NAME.find(s.to_lower())
					value = di if di >= 0 else null
				"SCHEDULING":
					var sc := CaveScheduling.FILE_NAME.find(s.to_lower())
					value = sc if sc >= 0 else null
			if value == null:
				_warn("invalid parameter '%s' for attribute %s" % [s, attrib])
			else:
				if count == 5:
					var arr: Array = obj.get(member)
					for k in range(j, 5):
						arr[k] = value
				else:
					obj.set(member, value)
				index += 1
			j += 1
	if found and not was_string and index < params.size():
		_warn("excess parameters for attribute '%s': '%s'" % [attrib, params[index]])
	return found


static func _read_bool(s: String):
	var l := s.to_lower()
	if s == "1" or l == "true" or l == "on" or l == "yes":
		return true
	if s == "0" or l == "false" or l == "off" or l == "no":
		return false
	return null


## Like C++ "is >> int": reads a leading integer.
static func _read_int(s: String):
	var m := RegEx.create_from_string("^\\s*[+-]?\\d+").search(s)
	return m.get_string().strip_edges().to_int() if m != null else null


## A number between 0 and 1 multiplied by ratio (probabilities, ratios of the cave size).
static func _read_ratio(s: String, ratio: int):
	var m := RegEx.create_from_string("^\\s*[+-]?(\\d+\\.?\\d*|\\.\\d+)([eE][+-]?\\d+)?").search(s)
	if m == null:
		return null
	var v := m.get_string().strip_edges().to_float()
	if v < 0.0 or v > 1.0:
		return null
	return int(v * ratio + 0.5)
