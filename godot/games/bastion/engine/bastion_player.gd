class_name BastionPlayer
extends RefCounted
## One player's side of a Bastion Coast game: cursor, current wall piece, home castle, enclosed castles, score.
## The solo game has one; a versus match has two or three. Walls, cannons and territory carry the player's index.

var index := 0
var alive := true  ## false once the player ends a repair phase with no enclosed castle (versus)
var cursor := Vector2.ZERO  ## in cells; during battle it is a free aim point
var piece: Array[Vector2i] = []
var piece_turns := 0
var piece_shape := 0
var cannons_to_place := 0
var home_castle := -1
var enclosed_castles: Array[int] = []
## For the home castle and every castle being walled in: castle index -> holes (cells to wall to seal it).
var castle_holes := {}
var score := 0
var walls_broken := 0  ## enemy walls knocked down (versus)
var cannons_broken := 0  ## enemy cannons destroyed (versus)
var out_round := 0  ## the round the player fell in (versus)


func _init(i: int = 0) -> void:
	index = i
