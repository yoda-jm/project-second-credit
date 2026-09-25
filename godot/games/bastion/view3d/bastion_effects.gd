class_name BastionEffects
extends Bursts
## Bastion Coast effects: muzzle smoke, splashes, dirt, fire, dust.


func dust(pos: Vector3, amount: int) -> void:
	burst(pos, Color(0.78, 0.7, 0.58, 0.7), amount, 1.6, 0.8, 1.6, 0.0, -1.5, 1.0, "smoke")


func muzzle(pos: Vector3, ours: bool) -> void:
	burst(pos, Color(0.9, 0.9, 0.88, 0.8), 14, 1.6, 1.6, 2.4, 0.0, 0.6, 1.0, "smoke")
	burst(pos, Color(1.0, 0.65, 0.25), 12, 4.0, 0.2, 1.4, 1.0, 0.0, 1.0, "glow")
	if ours:  # our cannons stand on land: a brief warm glow around them (never on the sea)
		flash(pos, Color(1.0, 0.7, 0.4), 1.6)


func impact(pos: Vector3, water: bool) -> void:
	if water:  # a column of spray: soft droplets thrown up, then a low mist
		burst(pos, Color(0.9, 0.95, 1.0, 0.9), 70, 6.0, 1.0, 0.5, 0.0, -11.0, 1.0, "soft")
		burst(pos, Color(0.92, 0.96, 1.0, 0.45), 16, 1.0, 1.6, 2.2, 0.0, -0.5, 1.0, "smoke")
	else:
		burst(pos, Color(0.45, 0.36, 0.28), 30, 4.5, 0.9, 0.9, 0.0, -9.0, 1.0, "soft")
		burst(pos, Color(0.6, 0.52, 0.42, 0.7), 10, 1.2, 1.5, 2.4, 0.0, 0.3, 1.0, "smoke")


func explosion(pos: Vector3, scale: float) -> void:
	burst(pos, Color(1.0, 0.6, 0.2), int(24 * scale), 2.5 * scale, 0.5, 3.0 * scale, 1.0, 0.5, 1.0, "glow")   # fireball
	burst(pos, Color(1.0, 0.8, 0.4), int(40 * scale), 8.0 * scale, 0.7, 0.5, 1.0, -6.0, 1.0, "glow")         # sparks
	burst(pos, Color(0.22, 0.2, 0.19, 0.85), int(22 * scale), 1.8, 2.6, 3.8 * scale, 0.0, 1.0, 1.0, "smoke") # smoke
	flash(pos, Color(1.0, 0.55, 0.2), 3.0 * scale)
