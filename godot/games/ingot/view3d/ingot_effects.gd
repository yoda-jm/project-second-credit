class_name IngotEffects
extends Bursts
## Ingot Run effects: the zap and crumble of a dug brick, dust when a hole closes, gold sparkles.


func dig(pos: Vector3) -> void:
	burst(pos, Color(0.4, 0.85, 1.0), 14, 2.5, 0.35, 0.12, 1.0, -2.0, 1.0, "glow")
	burst(pos, Color(0.7, 0.55, 0.4), 16, 2.5, 0.7, 0.12, 0.0, -10.0, 1.0, "soft")
	flash(pos, Color(0.4, 0.8, 1.0), 1.2)


func dust(pos: Vector3) -> void:
	burst(pos, Color(0.6, 0.5, 0.42, 0.7), 12, 1.5, 0.9, 0.4, 0.0, 0.5, 1.0, "smoke")


func sparkle(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.85, 0.35), 22, 2.2, 0.6, 0.12, 1.0, -1.5, 1.0, "glow")
	flash(pos, Color(1.0, 0.8, 0.3), 1.4)
