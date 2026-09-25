class_name FruitburrowEffects
extends Bursts
## Fruitburrow effects: soil crumbs, fruit sparkles, apple splats, monster pops, confetti.


func crumbs(pos: Vector3, big: bool) -> void:
	burst(pos, Color(0.45, 0.32, 0.22), 18 if big else 10, 2.4, 0.7, 0.45, 0.0, -9.0, 0.6, "soft")
	burst(pos, Color(0.55, 0.45, 0.35, 0.5), 5, 0.6, 1.0, 1.4, 0.0, 0.2, 1.0, "smoke")


func dust(pos: Vector3, amount: int) -> void:
	burst(pos, Color(0.7, 0.6, 0.48, 0.6), amount, 1.2, 0.9, 1.3, 0.0, -0.5, 1.0, "smoke")


func sparkle(pos: Vector3, color: Color) -> void:
	burst(pos, color.lightened(0.3), 20, 3.0, 0.5, 0.4, 1.0, -2.0, 1.0, "glow")
	burst(pos, Color(1.0, 1.0, 0.9), 8, 1.2, 0.35, 0.8, 1.0, 0.0, 1.0, "glow")
	flash(pos, color, 1.2)


func splat(pos: Vector3, color: Color) -> void:
	burst(pos, color, 40, 5.0, 0.8, 0.45, 0.0, -12.0, 0.8, "soft")
	burst(pos, Color(color, 0.6), 10, 1.0, 1.2, 1.8, 0.0, 0.0, 1.0, "smoke")


func pop(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.95, 0.6), 26, 4.5, 0.45, 0.4, 1.0, -4.0, 1.0, "glow")
	burst(pos, Color(0.9, 0.9, 1.0, 0.7), 12, 1.5, 0.9, 1.5, 0.0, 0.5, 1.0, "smoke")
	flash(pos, Color(1.0, 0.9, 0.6), 2.0)


func confetti(pos: Vector3) -> void:
	for c in [Color(1, 0.3, 0.3), Color(1, 0.85, 0.2), Color(0.4, 1, 0.5), Color(0.4, 0.7, 1), Color(1, 0.5, 0.9)]:
		burst(pos, c, 24, 7.0, 2.2, 0.35, 0.6, -5.0, 1.0, "glow")
