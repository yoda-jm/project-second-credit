class_name BootsEffects
extends Bursts
## Muddy Boots effects: muzzle flashes, dirt kicked up by bullets, splashes, explosions, hits, sparkles.


func muzzle(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.8, 0.4), 5, 2.0, 0.08, 0.25, 1.0, 0.0, 1.0, "glow")


func dirt(pos: Vector3) -> void:
	burst(pos, Color(0.4, 0.33, 0.25), 8, 2.0, 0.5, 0.18, 0.0, -8.0, 1.0, "soft")


func splash(pos: Vector3) -> void:
	burst(pos, Color(0.8, 0.9, 1.0, 0.85), 50, 5.5, 0.9, 0.22, 0.0, -10.0, 1.0, "soft")
	burst(pos, Color(0.9, 0.95, 1.0, 0.4), 12, 1.0, 1.4, 1.2, 0.0, -0.5, 1.0, "smoke")


func explosion(pos: Vector3, scale: float) -> void:
	burst(pos, Color(1.0, 0.6, 0.2), int(22 * scale), 2.2 * scale, 0.45, 1.3 * scale, 1.0, 0.5, 1.0, "glow")
	burst(pos, Color(1.0, 0.85, 0.4), int(30 * scale), 6.0 * scale, 0.6, 0.18, 1.0, -8.0, 1.0, "glow")
	burst(pos, Color(0.35, 0.28, 0.2), int(20 * scale), 4.0 * scale, 1.0, 0.25, 0.0, -9.0, 0.8, "soft")  # clods of earth
	burst(pos, Color(0.25, 0.23, 0.22, 0.8), int(14 * scale), 1.5, 2.2, 1.8 * scale, 0.0, 0.8, 1.0, "smoke")
	flash(pos, Color(1.0, 0.6, 0.25), 3.0 * scale)


func hit(pos: Vector3) -> void:
	burst(pos, Color(0.75, 0.1, 0.08), 10, 1.8, 0.4, 0.12, 0.0, -6.0, 1.0, "soft")


func sparkle(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.95, 0.6), 18, 2.5, 0.5, 0.2, 1.0, -1.0, 1.0, "glow")
