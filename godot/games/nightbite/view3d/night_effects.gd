class_name NightEffects
extends Bursts
## Nightbite effects: bursts of light when an orb, a spirit or a gem is eaten, and the hero's pop.


func burst_at(pos: Vector3, col: Color) -> void:
	burst(pos, col, 26, 3.5, 0.6, 0.14, 1.0, -1.0, 1.0, "glow")
	flash(pos, col, 2.0)
