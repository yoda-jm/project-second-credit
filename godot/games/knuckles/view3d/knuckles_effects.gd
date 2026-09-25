class_name KnucklesEffects
extends Bursts
## Neon Knuckles effects: hit sparks (bigger for heavy blows), dust when someone hits the ground, stars on a KO,
## splinters from a broken bat.


func hit(pos: Vector3, heavy: bool) -> void:
	burst(pos, Color(1.0, 0.95, 0.7), 18 if heavy else 9, 5.0 if heavy else 3.0, 0.18, 0.3 if heavy else 0.2, 1.0, 0.0, 1.0, "glow")
	burst(pos, Color(1.0, 1.0, 1.0), 1, 0.0, 0.08, 1.4 if heavy else 0.8, 1.0, 0.0, 1.0, "glow")  # the white flash
	if heavy:
		flash(pos, Color(1.0, 0.8, 0.6), 2.0)


func dust(pos: Vector3) -> void:
	burst(pos, Color(0.55, 0.52, 0.6, 0.6), 16, 2.0, 0.7, 0.9, 0.0, -0.5, 0.4, "smoke")


func ko(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.85, 0.3), 14, 1.2, 1.0, 0.25, 1.0, 1.5, 1.0, "glow")


func splinters(pos: Vector3) -> void:
	burst(pos, Color(0.7, 0.5, 0.3), 22, 5.0, 0.8, 0.12, 0.0, -9.0, 1.0, "soft")
