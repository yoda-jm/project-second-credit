class_name CratesEffects
extends Bursts
## Crate Keeper effects: sawdust scuffed up by a push, the green glow of a crate settling on its goal.


func scuff(pos: Vector3) -> void:
	burst(pos, Color(0.75, 0.62, 0.45, 0.7), 6, 0.8, 0.5, 0.18, 0.0, -2.0, 0.3, "soft")


func glow(pos: Vector3) -> void:
	burst(pos, Color(0.5, 1.0, 0.6), 18, 1.8, 0.6, 0.12, 1.0, -1.0, 1.0, "glow")
	flash(pos, Color(0.5, 1.0, 0.6), 1.2)
