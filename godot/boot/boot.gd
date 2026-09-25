extends Node2D
## Placeholder boot scene: proves the project runs and gives the capture script something to see.

@onready var _title: Label = $Title

var _time: float = 0.0


func _process(delta: float) -> void:
	_time += delta
	_title.modulate = Color.from_hsv(fmod(_time * 0.1, 1.0), 0.6, 1.0)
