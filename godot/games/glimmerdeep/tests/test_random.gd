extends GdUnitTestSuite
## Random generators against reference values produced by GLib (C) and by hand-checked C64 arithmetic.


func _draws(seed: int) -> Array:
	var r := GlibRand.new(seed)
	var out := []
	for i in 3: out.append(r.rand_int())
	for i in 3: out.append(r.rand_int_range(0, 256))
	for i in 3: out.append(r.rand_int_range(0, 1000000))
	for i in 3: out.append(1 if r.rand_boolean() else 0)
	out.append(r.rand_int_range(0, 100))
	out.append(r.rand_int_range(0, 3))
	out.append(r.rand_int_range(-5, 5))
	return out


func test_glib_rand_matches_glib() -> void:
	assert_array(_draws(0)).is_equal([2357136044, 2546248239, 3071714933, 192, 67, 251, 255427, 918503, 583497, 1, 0, 1, 56, 0, 3])
	assert_array(_draws(1)).is_equal([1791095845, 4282876139, 3093770124, 72, 255, 137, 508491, 846341, 311759, 0, 1, 0, 16, 2, -2])
	assert_array(_draws(669174884)).is_equal([2152606936, 1167469419, 1748314074, 67, 170, 5, 344436, 664877, 122818, 1, 1, 0, 96, 0, 1])
	assert_array(_draws(4294967295)).is_equal([419326371, 479346978, 3918654476, 71, 180, 64, 89942, 765114, 50329, 0, 1, 0, 22, 2, 0])


func test_glib_rand_regenerates_state() -> void:
	var r := GlibRand.new(12345)
	for i in 700:
		r.rand_int()
	assert_int(r.rand_int()).is_equal(926638379)


func test_c64_rand_sequence() -> void:
	var r := C64Rand.new()
	r.set_seed(10)
	var seq := []
	for i in 6:
		seq.append(r.random())
	# seed 10 -> s1=0, s2=10: s2'=10+0+0x13=29; s1'=0+0+0 + (10>>1)=5 ...
	assert_int(seq[0]).is_equal(5)
	assert_int(seq.size()).is_equal(6)
