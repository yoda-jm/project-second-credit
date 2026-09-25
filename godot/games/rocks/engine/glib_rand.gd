class_name GlibRand
extends RefCounted
## Bit-exact port of GLib's GRand (Mersenne Twister MT19937, seeding and range functions of GLib >= 2.2).
## GDash uses it for everything random in the engine, so replays only reproduce with this exact generator.

const N := 624
const M := 397
const MATRIX_A := 0x9908b0df
const UPPER_MASK := 0x80000000
const LOWER_MASK := 0x7fffffff
const MASK32 := 0xffffffff

var _mt := PackedInt64Array()
var _mti: int = N + 1


func _init(seed: int = 0) -> void:
	_mt.resize(N)
	set_seed(seed)


func set_seed(seed: int) -> void:
	_mt[0] = seed & MASK32
	for i in range(1, N):
		var prev: int = _mt[i - 1]
		_mt[i] = (1812433253 * (prev ^ (prev >> 30)) + i) & MASK32
	_mti = N


func duplicate_state() -> GlibRand:
	var r := GlibRand.new()
	r._mt = _mt.duplicate()
	r._mti = _mti
	return r


## Uniform 32-bit unsigned integer (g_rand_int).
func rand_int() -> int:
	var y: int
	if _mti >= N:
		var kk := 0
		while kk < N - M:
			y = (_mt[kk] & UPPER_MASK) | (_mt[kk + 1] & LOWER_MASK)
			_mt[kk] = _mt[kk + M] ^ (y >> 1) ^ (MATRIX_A if (y & 1) != 0 else 0)
			kk += 1
		while kk < N - 1:
			y = (_mt[kk] & UPPER_MASK) | (_mt[kk + 1] & LOWER_MASK)
			_mt[kk] = _mt[kk + (M - N)] ^ (y >> 1) ^ (MATRIX_A if (y & 1) != 0 else 0)
			kk += 1
		y = (_mt[N - 1] & UPPER_MASK) | (_mt[0] & LOWER_MASK)
		_mt[N - 1] = _mt[M - 1] ^ (y >> 1) ^ (MATRIX_A if (y & 1) != 0 else 0)
		_mti = 0
	y = _mt[_mti]
	_mti += 1
	y ^= y >> 11
	y ^= (y << 7) & 0x9d2c5680
	y ^= (y << 15) & 0xefc60000
	y ^= y >> 18
	return y & MASK32


## Integer in [begin, end) (g_rand_int_range).
func rand_int_range(begin: int, end: int) -> int:
	var dist: int = (end - begin) & MASK32
	var random := 0
	if dist != 0:
		var maxvalue: int
		if dist <= 0x80000000:
			var leftover: int = (0x80000000 % dist) * 2
			if leftover >= dist:
				leftover -= dist
			maxvalue = 0xffffffff - leftover
		else:
			maxvalue = dist - 1
		random = rand_int()
		while random > maxvalue:
			random = rand_int()
		random %= dist
	return begin + random


## g_rand_boolean
func rand_boolean() -> bool:
	return (rand_int() & (1 << 15)) != 0
