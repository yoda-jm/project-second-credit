class_name CaveReplay
extends RefCounted
## A recorded game: the random seed and one movement per cave iteration (GDash / BDCFF [replay] section).

const MOVE_MASK := 0x0f
const FIRE_MASK := 0x10
const SUICIDE_MASK := 0x20

const DESCRIPTORS := [
	["Level", "INT", "level"],
	["RandomSeed", "INT", "seed"],
	["Player", "STRING", "player_name"],
	["Date", "STRING", "date"],
	["Comment", "STRING", "comment"],
	["RecordedWith", "STRING", "recorded_with"],
	["Score", "INT", "score"],
	["Duration", "INT", "duration"],
	["Success", "BOOLEAN", "success"],
	["CheckSum", "INT", "checksum"],
]

var level: int = 1
var seed: int = 0
var player_name: String = ""
var date: String = ""
var comment: String = ""
var recorded_with: String = ""
var score: int = 0
var duration: int = 0
var success: bool = false
var checksum: int = 0
var movements := PackedByteArray()
var _pos: int = 0


func store_movement(move: int, fire: bool, suicide: bool) -> void:
	movements.append((move & MOVE_MASK) | (FIRE_MASK if fire else 0) | (SUICIDE_MASK if suicide else 0))


## Returns [move, fire, suicide], or an empty array when the replay is over.
func next_movement() -> Array:
	if _pos >= movements.size():
		return []
	var data: int = movements[_pos]
	_pos += 1
	return [data & MOVE_MASK, (data & FIRE_MASK) != 0, (data & SUICIDE_MASK) != 0]


func rewind() -> void:
	_pos = 0


## Parses the BDCFF movement string, e.g. ".22 u r7 D2" (uppercase = with fire, digits = repeat count).
func load_movements(text: String) -> void:
	for word in text.split(" ", false):
		_load_one(word)


func _load_one(word: String) -> void:
	var up := false
	var down := false
	var left := false
	var right := false
	var fire := false
	var suicide := false
	var num := -1
	for i in word.length():
		var c := word[i]
		match c:
			"U": fire = true; up = true
			"u": up = true
			"D": fire = true; down = true
			"d": down = true
			"L": fire = true; left = true
			"l": left = true
			"R": fire = true; right = true
			"r": right = true
			"F": fire = true
			"k": suicide = true
			_:
				if num == -1 and c >= "0" and c <= "9":
					var j := i
					while j < word.length() and word[j] >= "0" and word[j] <= "9":
						j += 1
					num = word.substr(i, j - i).to_int()
	var dir := CaveDirections.from_keypress(up, down, left, right)
	var count := 1 if num == -1 else num
	for n in count:
		store_movement(dir, fire, suicide)
