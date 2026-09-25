class_name WallPieces
extends RefCounted
## The wall pieces handed out during the build phase: polyominoes of 1 to 5 blocks, like the arcade
## original's set (to be checked against it). Shapes are lists of cells; rotation is 90 degrees clockwise.

const SHAPES: Array = [
	[Vector2i(0, 0)],                                                           # single block
	[Vector2i(0, 0), Vector2i(1, 0)],                                           # domino
	[Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0)],                           # I3
	[Vector2i(0, 0), Vector2i(0, 1), Vector2i(1, 1)],                           # small L
	[Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0), Vector2i(3, 0)],           # I4
	[Vector2i(0, 0), Vector2i(0, 1), Vector2i(0, 2), Vector2i(1, 2)],           # L
	[Vector2i(1, 0), Vector2i(1, 1), Vector2i(1, 2), Vector2i(0, 2)],           # J
	[Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0), Vector2i(1, 1)],           # T
	[Vector2i(1, 0), Vector2i(2, 0), Vector2i(0, 1), Vector2i(1, 1)],           # S
	[Vector2i(0, 0), Vector2i(1, 0), Vector2i(1, 1), Vector2i(2, 1)],           # Z
	[Vector2i(0, 0), Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1)],           # square
	[Vector2i(0, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(2, 1), Vector2i(2, 0)],  # U
	[Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0), Vector2i(0, 1), Vector2i(0, 2)],  # big L (corner)
	[Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(2, 1), Vector2i(1, 2)],  # plus
]


static func rotated(cells: Array, turns: int) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for c in cells:
		out.append(c)
	for t in (turns % 4 + 4) % 4:
		var next: Array[Vector2i] = []
		for c in out:
			next.append(Vector2i(-c.y, c.x))
		out = next
	# normalise so the top-left of the bounding box is (0, 0)
	var min_x := 1 << 20
	var min_y := 1 << 20
	for c in out:
		min_x = mini(min_x, c.x)
		min_y = mini(min_y, c.y)
	for i in out.size():
		out[i] -= Vector2i(min_x, min_y)
	return out


static func size_of(cells: Array[Vector2i]) -> Vector2i:
	var s := Vector2i.ZERO
	for c in cells:
		s = Vector2i(maxi(s.x, c.x + 1), maxi(s.y, c.y + 1))
	return s
