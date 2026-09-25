class_name CaveStored
extends CaveProperties
## A cave as described in a BDCFF file: properties, an optional map, drawing objects and replays.

var map := PackedInt32Array()  ## w*h elements, or empty when the cave is drawn from objects and random fill
var objects: Array[Dictionary] = []  ## see CaveObjects
var replays: Array[CaveReplay] = []
var highscore: Array = []  ## [score, name] pairs


func has_map() -> bool:
	return not map.is_empty()
