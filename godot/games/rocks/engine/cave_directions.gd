class_name CaveDirections
extends RefCounted
## Movement directions, in GDash order (GdDirectionEnum). The *_2 values move two cells.

const STILL := 0
const UP := 1
const UP_RIGHT := 2
const RIGHT := 3
const DOWN_RIGHT := 4
const DOWN := 5
const DOWN_LEFT := 6
const LEFT := 7
const UP_LEFT := 8
const UP_2 := 9
const UP_RIGHT_2 := 10
const RIGHT_2 := 11
const DOWN_RIGHT_2 := 12
const DOWN_2 := 13
const DOWN_LEFT_2 := 14
const LEFT_2 := 15
const UP_LEFT_2 := 16

const DX: Array[int] = [0, 0, 1, 1, 1, 0, -1, -1, -1, 0, 2, 2, 2, 0, -2, -2, -2]
const DY: Array[int] = [0, -1, -1, 0, 1, 1, 1, 0, -1, -2, -2, 0, 2, 2, 2, 0, -2]

## Names used in BDCFF files (Gravitation=down).
const FILE_NAME: Array[String] = ["none", "up", "upright", "right", "downright", "down", "downleft", "left", "upleft"]


static func from_keypress(up: bool, down: bool, left: bool, right: bool) -> int:
	if up and right: return UP_RIGHT
	if down and right: return DOWN_RIGHT
	if down and left: return DOWN_LEFT
	if up and left: return UP_LEFT
	if up: return UP
	if down: return DOWN
	if left: return LEFT
	if right: return RIGHT
	return STILL
