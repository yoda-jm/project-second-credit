class_name CfImport
extends RefCounted
## Reads a mission of the original Cannon Fodder (1 or 2) from the player's own data files, locally: the .map
## (tiles), the .spt (sprites: soldiers, enemies, buildings, hostages...) and the tileset's .hit tables (the
## terrain of each tile). Nothing of the original is shipped or copied; the result is a BootsMap in memory.
##
## The format, as documented by Open Fodder (GPL-3.0, github.com/OpenFodder/openfodder, Map/Original.cpp and
## Map/MapRuntime.cpp):
##   .map  header of 0x60 bytes: the base tileset file name at 0x00 (e.g. "junbase.blk"), the sub tileset at 0x10,
##         width and height as big-endian words at 0x54 and 0x56; then width x height big-endian tile words
##         (tile id = word & 0x1FF).
##   .hit  one big-endian word per tile: 240 for the base set, then the sub set from index 240. The low nibble is
##         the terrain feature; a negative value mixes two features in one tile (we keep the low one).
##   .spt  records of five big-endian words: two unused here, x and y in pixels (16 per tile), sprite type.

const T = BootsMap.T
## terrain feature (low nibble of the hit value) -> our terrain
const FEATURES := {0: T.LAND, 1: T.ROUGH, 2: T.ROUGH, 3: T.ROCK, 4: T.QUICKSAND, 5: T.SHALLOW, 6: T.WATER,
	7: T.SNOW, 8: T.ROUGH, 9: T.CLIFF, 10: T.CLIFF, 11: T.QUICKSAND}
## sprite type -> our things (the rest is decoration or not supported yet)
const SPRITES := {0: "start", 5: "enemy", 106: "enemy", 20: "hut", 100: "hut", 72: "hostage", 73: "tent",
	37: "grenades", 38: "rockets", 54: "mine", 56: "mine", 14: "tree"}


static func be16(b: PackedByteArray, at: int) -> int:
	return (b[at] << 8) | b[at + 1] if at + 1 < b.size() else 0


static func be16s(b: PackedByteArray, at: int) -> int:
	var v := be16(b, at)
	return v - 0x10000 if v >= 0x8000 else v


## hit: the base .hit followed by the sub .hit (as the game loads them), or empty (everything is land).
static func from_bytes(map_bytes: PackedByteArray, spt_bytes: PackedByteArray, base_hit: PackedByteArray,
		sub_hit: PackedByteArray, mission_name := "") -> BootsMap:
	var m := BootsMap.new()
	m.source = "original"
	m.name = mission_name
	m.goals.assign(["kill"])
	m.w = be16(map_bytes, 0x54)
	m.h = be16(map_bytes, 0x56)
	m.terrain.resize(m.w * m.h)
	var hit := PackedInt32Array()
	hit.resize(512)
	for i in mini(240, base_hit.size() / 2):
		hit[i] = be16s(base_hit, i * 2)
	for i in mini(272, sub_hit.size() / 2):
		hit[240 + i] = be16s(sub_hit, i * 2)
	for y in m.h:
		for x in m.w:
			var tile := be16(map_bytes, 0x60 + (y * m.w + x) * 2) & 0x1FF
			var feature := hit[tile] & 0x0F
			m.terrain[y * m.w + x] = FEATURES.get(feature, T.LAND)
	var i := 0
	while i + 9 < spt_bytes.size():
		var px := be16(spt_bytes, i + 4)
		var py := be16(spt_bytes, i + 6)
		var kind: int = be16(spt_bytes, i + 8)
		i += 10
		if not SPRITES.has(kind):
			continue
		var cell := Vector2i((px + 0x10) / 16, py / 16)
		if not m.inside(cell):
			continue
		if SPRITES[kind] == "tree":
			m.terrain[cell.y * m.w + cell.x] = T.TREE
		else:
			m.things.append({"kind": SPRITES[kind], "cell": cell})
	if m.count("hut") > 0:
		m.goals.append("destroy")
	if m.count("hostage") > 0 and m.count("tent") > 0:
		m.goals.append("rescue")
	return m


## Reads a mission from files: `map_path` (…/MAPM1.MAP), its .spt next to it, and the .hit files named in the
## map header, looked up in the same folder (any case).
static func load_mission(map_path: String) -> BootsMap:
	var map_bytes := FileAccess.get_file_as_bytes(map_path)
	if map_bytes.size() < 0x60:
		return null
	var dir := map_path.get_base_dir()
	var spt := FileAccess.get_file_as_bytes(_sibling(dir, map_path.get_file().get_basename() + ".spt"))
	var base_name := map_bytes.slice(0, 11).get_string_from_ascii().get_basename() + ".hit"
	var sub_name := map_bytes.slice(16, 27).get_string_from_ascii().get_basename() + ".hit"
	var base_hit := FileAccess.get_file_as_bytes(_sibling(dir, base_name))
	var sub_hit := FileAccess.get_file_as_bytes(_sibling(dir, sub_name))
	return from_bytes(map_bytes, spt, base_hit, sub_hit, map_path.get_file().get_basename())


static func _sibling(dir: String, file: String) -> String:
	for f in DirAccess.get_files_at(dir):
		if f.to_lower() == file.to_lower():
			return dir.path_join(f)
	return dir.path_join(file)
