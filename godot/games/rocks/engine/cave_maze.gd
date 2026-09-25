class_name CaveMaze
extends RefCounted
## The BDCFF Maze object (perfect, braid and unicursal mazes). Port of GDash's caveobjectmaze.cpp
## (MIT, Copyright (c) 2007-2013 Czirkos Zoltan; see GDASH_LICENSE.txt). The recursive generator is made
## iterative, keeping the exact order of random draws.


static func draw(o: Dictionary, cave: CaveRendered) -> void:
	var x1: int = mini(o["p1"].x, o["p2"].x)
	var y1: int = mini(o["p1"].y, o["p2"].y)
	var x2: int = maxi(o["p1"].x, o["p2"].x)
	var y2: int = maxi(o["p1"].y, o["p2"].y)
	var wall: int = maxi(1, o["wall_width"])
	var path: int = maxi(1, o["path_width"])
	var w: int = (x2 - x1 + 1 + wall) / (path + wall)
	var h: int = (y2 - y1 + 1 + wall) / (path + wall)
	var maze_type: String = o["maze_type"]
	if maze_type == "unicursal":
		w = w / 2 * 2
		h = h / 2 * 2
	else:
		w = 2 * (w - 1) + 1
		h = 2 * (h - 1) + 1
	var rand := GlibRand.new()
	var s: int = o["seed"][cave.rendered_on]
	rand.set_seed(cave.random.rand_int() if s == -1 else s)
	var m := Grid.new(maxi(w, 0), maxi(h, 0))
	if w >= 1 and h >= 1:
		_mazegen(m, rand, o["horiz"])
	if maze_type == "braid":
		_braid(m, rand)
	if w >= 1 and h >= 1 and maze_type == "unicursal":
		m = _unicursal(m)
		w = m.draw_w
		h = m.draw_h
	var yk := y1
	for y in h:
		for i in (path if y % 2 == 0 else wall):
			var xk := x1
			for x in w:
				for j in (path if x % 2 == 0 else wall):
					cave.store_rc(xk, yk, o["path"] if m.at(x, y) else o["wall"], o["id"])
					xk += 1
			for x in range(xk, x2 + 1):
				cave.store_rc(x, yk, o["wall"], o["id"])
			yk += 1
	for y in range(yk, y2 + 1):
		for x in range(x1, x2 + 1):
			cave.store_rc(x, y, o["wall"], o["id"])


static func _mazegen(m: Grid, rand: GlibRand, horiz: int) -> void:
	var stack: Array[Vector3i] = [Vector3i(0, 0, 15)]  # x, y, dirmask
	m.put(0, 0, true)
	while not stack.is_empty():
		var top: Vector3i = stack.back()
		var x := top.x
		var y := top.y
		var dirmask := top.z
		if dirmask == 0:
			stack.pop_back()
			continue
		var dir: int = 2 if rand.rand_int_range(0, 100) < horiz else 0
		if dir == 2 and (dirmask & 12) == 0:
			dir = 0
		elif dir == 0 and (dirmask & 3) == 0:
			dir = 2
		dir += rand.rand_int_range(0, 2)
		if (dirmask & (1 << dir)) == 0:
			continue
		dirmask &= ~(1 << dir)
		stack[stack.size() - 1] = Vector3i(x, y, dirmask)
		var nx := x
		var ny := y
		match dir:
			0:
				if not (y >= 2 and not m.at(x, y - 2)): continue
				m.put(x, y - 1, true); ny = y - 2
			1:
				if not (y < m.h - 2 and not m.at(x, y + 2)): continue
				m.put(x, y + 1, true); ny = y + 2
			2:
				if not (x >= 2 and not m.at(x - 2, y)): continue
				m.put(x - 1, y, true); nx = x - 2
			3:
				if not (x < m.w - 2 and not m.at(x + 2, y)): continue
				m.put(x + 1, y, true); nx = x + 2
		m.put(nx, ny, true)
		stack.append(Vector3i(nx, ny, 15))


static func _braid(m: Grid, rand: GlibRand) -> void:
	var y := 0
	while y < m.h:
		var x := 0
		while x < m.w:
			var closed := 0
			var dirs: Array[int] = []
			if x < 1 or not m.at(x - 1, y):
				closed += 1
				if x > 0: dirs.append(CaveDirections.LEFT)
			if y < 1 or not m.at(x, y - 1):
				closed += 1
				if y > 0: dirs.append(CaveDirections.UP)
			if x >= m.w - 1 or not m.at(x + 1, y):
				closed += 1
				if x < m.w - 1: dirs.append(CaveDirections.RIGHT)
			if y >= m.h - 1 or not m.at(x, y + 1):
				closed += 1
				if y < m.h - 1: dirs.append(CaveDirections.DOWN)
			if closed == 3 and not dirs.is_empty():
				var dir: int = dirs[rand.rand_int_range(0, dirs.size())]
				m.put(x + CaveDirections.DX[dir], y + CaveDirections.DY[dir], true)
			x += 2
		y += 2


static func _unicursal(m: Grid) -> Grid:
	var u := Grid.new(m.w * 2 + 1, m.h * 2 + 1)
	for y in m.h:
		for x in m.w:
			if m.at(x, y):
				u.put(x * 2, y * 2, true)
				u.put(x * 2 + 2, y * 2, true)
				u.put(x * 2, y * 2 + 2, true)
				u.put(x * 2 + 2, y * 2 + 2, true)
				if x < 1 or not m.at(x - 1, y): u.put(x * 2, y * 2 + 1, true)
				if y < 1 or not m.at(x, y - 1): u.put(x * 2 + 1, y * 2, true)
				if x >= m.w - 1 or not m.at(x + 1, y): u.put(x * 2 + 2, y * 2 + 1, true)
				if y >= m.h - 1 or not m.at(x, y + 1): u.put(x * 2 + 1, y * 2 + 2, true)
	# GDash keeps the (2w+1)x(2h+1) buffer but draws only (2w-1)x(2h-1) of it.
	u.draw_w = m.w * 2 - 1
	u.draw_h = m.h * 2 - 1
	return u


class Grid:
	var w: int
	var h: int
	var draw_w: int
	var draw_h: int
	var cells := PackedByteArray()

	func _init(width: int, height: int) -> void:
		w = width
		h = height
		draw_w = width
		draw_h = height
		cells.resize(width * height)

	func at(x: int, y: int) -> bool:
		return cells[y * w + x] != 0

	func put(x: int, y: int, v: bool) -> void:
		cells[y * w + x] = 1 if v else 0
