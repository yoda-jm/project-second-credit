class_name C64Rand
extends RefCounted
## The predictable random generator of the C64 original, as reimplemented by GDash (MIT). Classic caves are
## generated from a seed with it, so our caves match the originals cell for cell.

var seed_1: int = 0
var seed_2: int = 0


func set_seed(seed: int) -> void:
	seed_1 = (seed / 256) % 256
	seed_2 = seed % 256


func set_seed_2(s1: int, s2: int) -> void:
	seed_1 = s1 % 256
	seed_2 = s2 % 256


## Next number, 0..255.
func random() -> int:
	var temp_rand_1: int = (seed_1 & 0x0001) << 7
	var temp_rand_2: int = (seed_2 >> 1) & 0x007F
	var result: int = seed_2 + ((seed_2 & 0x0001) << 7)
	var carry: int = result >> 8
	result = result & 0x00FF
	result = result + carry + 0x13
	carry = result >> 8
	seed_2 = result & 0x00FF
	result = seed_1 + carry + temp_rand_1
	carry = result >> 8
	result = result & 0x00FF
	result = result + carry + temp_rand_2
	seed_1 = result & 0x00FF
	return seed_1
