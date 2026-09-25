class_name CaveNames
extends RefCounted
## Element name and map-character lookup for BDCFF files (case-insensitive names, like GDash).

const E = preload("res://games/rocks/engine/cave_elements.gd")

## Aliases GDash accepts for compatibility with older converters.
const ALIASES := {
	"HEXPANDING_WALL": E.H_EXPANDING_WALL, "FALLING_DIAMOND": E.DIAMOND_F, "FALLING_BOULDER": E.STONE_F,
	"EXPLOSION1S": E.EXPLODE_1, "EXPLOSION2S": E.EXPLODE_2, "EXPLOSION3S": E.EXPLODE_3,
	"EXPLOSION4S": E.EXPLODE_4, "EXPLOSION5S": E.EXPLODE_5,
	"EXPLOSION1D": E.PRE_DIA_1, "EXPLOSION2D": E.PRE_DIA_2, "EXPLOSION3D": E.PRE_DIA_3,
	"EXPLOSION4D": E.PRE_DIA_4, "EXPLOSION5D": E.PRE_DIA_5,
	"WALL2": E.STEEL_EXPLODABLE, "BLADDERD9": E.BLADDER_8,
}

static var _by_name := {}
static var _by_char := {}


static func _build() -> void:
	for i in E.COUNT:
		_by_name[E.FILE_NAME[i].to_upper()] = i
		var c: String = E.MAP_CHAR[i]
		if c != "":
			_by_char[c] = i
	for k in ALIASES:
		_by_name[k] = ALIASES[k]


## Element by BDCFF name, or -1.
static func element(name: String) -> int:
	if _by_name.is_empty():
		_build()
	return _by_name.get(name.to_upper(), -1)


## Default map character table (a fresh copy; [mapcodes] may add to it).
static func default_char_table() -> Dictionary:
	if _by_name.is_empty():
		_build()
	return _by_char.duplicate()
