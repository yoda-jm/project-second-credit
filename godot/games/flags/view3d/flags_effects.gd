class_name FlagsEffects
extends Bursts
## Iron Flags effects: muzzle flashes, bullet sparks on armour, flame bursts, laser glints, explosions big and small,
## rock dust, and the confetti of a captured flag.


func muzzle(pos: Vector3, heavy := false) -> void:
	burst(pos, Color(1.0, 0.8, 0.4), 8 if heavy else 4, 2.5 if heavy else 1.5, 0.08, 0.35 if heavy else 0.18, 1.0, 0.0, 1.0, "glow")
	if heavy:
		burst(pos, Color(0.6, 0.58, 0.55, 0.6), 6, 0.8, 1.2, 0.6, 0.0, 0.6, 1.0, "smoke")


func spark(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.85, 0.5), 6, 3.0, 0.25, 0.08, 1.0, -9.0, 1.0, "glow")


func flame(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.55, 0.15), 14, 1.2, 0.45, 0.45, 1.0, 1.5, 1.0, "glow")
	burst(pos, Color(0.3, 0.25, 0.22, 0.5), 5, 0.6, 1.0, 0.5, 0.0, 1.0, 1.0, "smoke")


func laser_hit(pos: Vector3) -> void:
	burst(pos, Color(0.4, 1.0, 0.9), 12, 2.5, 0.3, 0.12, 1.0, -2.0, 1.0, "glow")
	flash(pos, Color(0.4, 1.0, 0.9), 1.2)


func explosion(pos: Vector3, scale: float) -> void:
	burst(pos, Color(1.0, 0.55, 0.18), int(20 * scale), 2.0 * scale, 0.45, 0.9 * scale, 1.0, 0.8, 1.0, "glow")
	burst(pos, Color(1.0, 0.85, 0.4), int(24 * scale), 5.0 * scale, 0.55, 0.12, 1.0, -9.0, 1.0, "glow")
	burst(pos, Color(0.3, 0.27, 0.24), int(14 * scale), 3.5 * scale, 0.9, 0.16, 0.0, -9.0, 0.8, "soft")  # debris
	burst(pos, Color(0.22, 0.2, 0.2, 0.75), int(10 * scale), 1.2, 2.4, 1.2 * scale, 0.0, 0.7, 1.0, "smoke")
	flash(pos, Color(1.0, 0.6, 0.25), 2.5 * scale)


func dust(pos: Vector3, color: Color) -> void:
	burst(pos, color, 16, 2.0, 1.2, 0.5, 0.0, -2.0, 1.0, "smoke")
	burst(pos, color.darkened(0.3), 12, 3.5, 0.8, 0.15, 0.0, -9.0, 1.0, "soft")


func confetti(pos: Vector3, color: Color) -> void:
	burst(pos, color, 40, 4.0, 1.2, 0.12, 1.0, -5.0, 1.0, "glow")
	burst(pos, Color(1.0, 0.95, 0.7), 20, 3.0, 0.9, 0.1, 1.0, -4.0, 1.0, "glow")
	flash(pos, color, 2.0)
