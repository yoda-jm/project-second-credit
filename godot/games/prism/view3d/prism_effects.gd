class_name PrismEffects
extends Bursts
## Prism Breaker effects: crystal shards when a brick breaks, sparks off steel, a pop for drones and capsules.


func shatter(pos: Vector3, col: Color) -> void:
	burst(pos, col, 22, 4.0, 0.7, 0.12, 1.0, -9.0, 0.6, "glow")
	flash(pos + Vector3(0, -2.5, 1.2), col, 1.2)  # the flash sits 2.5 above: bring it level, in front


func spark(pos: Vector3, col: Color) -> void:
	burst(pos, col, 8, 3.0, 0.3, 0.07, 1.0, -4.0, -1.0, "glow")


func pop(pos: Vector3, col: Color) -> void:
	burst(pos, col, 30, 5.0, 0.6, 0.15, 1.0, 0.0, 1.0, "glow")
	flash(pos + Vector3(0, -2.5, 1.2), col, 2.0)  # the flash sits 2.5 above: bring it level, in front
