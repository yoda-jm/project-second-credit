class_name BlastEffects
extends Bursts
## Blastyard effects: the fireball of a blast, flames licking along each arm of the cross, crate splinters, the dust
## of a block slamming down, a bomber's poof, power-up sparkles.


func blast(pos: Vector3, scale: float) -> void:
	burst(pos, Color(1.0, 0.6, 0.2), int(26 * scale), 3.0 * scale, 0.45, 0.9 * scale, 1.0, 1.5, 1.0, "glow")
	burst(pos, Color(1.0, 0.9, 0.5), int(18 * scale), 6.0 * scale, 0.4, 0.12, 1.0, -8.0, 1.0, "glow")
	burst(pos, Color(0.25, 0.22, 0.22, 0.7), int(10 * scale), 1.2, 1.8, 1.1 * scale, 0.0, 1.2, 1.0, "smoke")
	flash(pos, Color(1.0, 0.6, 0.25), 3.0 * scale)


func fire(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.5, 0.12), 6, 1.2, 0.35, 0.45, 1.0, 2.5, 1.0, "glow")


func splinters(pos: Vector3) -> void:
	burst(pos, Color(0.7, 0.5, 0.3), 16, 4.0, 0.8, 0.12, 0.0, -12.0, 1.0, "soft")
	burst(pos, Color(0.55, 0.5, 0.45, 0.6), 6, 1.0, 1.0, 0.6, 0.0, 0.5, 1.0, "smoke")


func dust(pos: Vector3) -> void:
	burst(pos, Color(0.7, 0.68, 0.65, 0.7), 14, 2.5, 0.9, 0.5, 0.0, 0.3, 0.2, "smoke")


func poof(pos: Vector3, col: Color) -> void:
	burst(pos, col, 24, 3.0, 0.8, 0.2, 1.0, -3.0, 1.0, "glow")
	burst(pos, Color(0.9, 0.9, 0.9, 0.7), 10, 1.5, 1.2, 0.7, 0.0, 1.0, 1.0, "smoke")


func sparkle(pos: Vector3, col: Color) -> void:
	burst(pos, col, 20, 2.5, 0.6, 0.15, 1.0, -1.5, 1.0, "glow")
	flash(pos, col, 1.2)
