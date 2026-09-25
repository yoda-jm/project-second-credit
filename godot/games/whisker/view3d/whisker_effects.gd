class_name WhiskerEffects
extends Bursts
## Whisker Alley effects: dust puffs, cartoon stars, splashes, sparkles, the eel's zap, confetti.


func dust(pos: Vector3, amount: int) -> void:
	burst(pos, Color(0.6, 0.58, 0.62, 0.55), amount, 1.2, 0.8, 1.0, 0.0, -0.5, 1.0, "smoke")


func stars(pos: Vector3) -> void:
	burst(pos + Vector3(0, 0.5, 0), Color(1.0, 0.9, 0.35), 16, 3.0, 0.7, 0.35, 1.0, -1.0, 1.0, "glow")
	flash(pos, Color(1.0, 0.85, 0.4), 1.2)


func splash(pos: Vector3) -> void:
	burst(pos, Color(0.75, 0.9, 1.0, 0.85), 40, 4.5, 0.8, 0.28, 0.0, -10.0, 1.0, "soft")


func sparkle(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.95, 0.6), 22, 3.0, 0.5, 0.35, 1.0, -1.5, 1.0, "glow")
	flash(pos, Color(1.0, 0.9, 0.6), 1.0)


func zap(pos: Vector3) -> void:
	burst(pos, Color(0.7, 0.9, 1.0), 40, 6.0, 0.3, 0.25, 1.0, 0.0, 1.0, "glow")
	flash(pos, Color(0.6, 0.8, 1.0), 4.0)


func confetti(pos: Vector3) -> void:
	for c in [Color(1, 0.3, 0.3), Color(1, 0.85, 0.2), Color(0.4, 1, 0.5), Color(0.4, 0.7, 1), Color(1, 0.5, 0.9)]:
		burst(pos, c, 22, 7.0, 2.0, 0.3, 0.6, -5.0, 1.0, "glow")
