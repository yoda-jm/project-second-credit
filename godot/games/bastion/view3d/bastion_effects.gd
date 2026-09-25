class_name BastionEffects
extends Node3D
## Pooled particle bursts and light flashes for Bastion Coast: muzzle smoke, splashes, dirt, fire, dust.

var _pool: Array[CPUParticles3D] = []
var _next := 0
var _lights: Array[OmniLight3D] = []
var _next_light := 0


func _ready() -> void:
	for i in 40:
		var p := CPUParticles3D.new()
		p.one_shot = true
		p.emitting = false
		p.explosiveness = 0.85
		p.local_coords = false
		var q := QuadMesh.new()
		q.size = Vector2(0.4, 0.4)
		p.mesh = q
		add_child(p)
		_pool.append(p)
	for i in 6:
		var l := OmniLight3D.new()
		l.light_energy = 0.0
		l.omni_range = 7.0
		l.omni_attenuation = 2.0
		l.light_specular = 0.0  # light the scene, but no glare on the glossy sea
		add_child(l)
		_lights.append(l)


func _process(delta: float) -> void:
	for l in _lights:
		l.light_energy = maxf(0.0, l.light_energy - delta * 12.0)


func burst(pos: Vector3, color: Color, amount: int, speed: float, life: float, size: float, glow: float, gravity: float,
		up: float = 1.0, kind: String = "") -> void:
	var p := _pool[_next]
	_next = (_next + 1) % _pool.size()
	p.position = pos
	p.amount = amount
	p.lifetime = life
	p.direction = Vector3(0, up, 0)
	p.spread = 70.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector3(0, gravity, 0)
	p.scale_amount_min = size * 0.5
	p.scale_amount_max = size
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 1))
	fade.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = fade
	p.material_override = Fx.material(kind if kind != "" else ("glow" if glow > 0.0 else "soft"), color)
	p.scale_amount_curve = Fx.size_curve(kind == "smoke")
	p.restart()
	p.emitting = true


func flash(pos: Vector3, color: Color, energy: float) -> void:
	var l := _lights[_next_light]
	_next_light = (_next_light + 1) % _lights.size()
	l.position = pos + Vector3(0, 2.5, 0)  # high and wide: a soft glow, not a bright disc on the sea
	l.light_color = color
	l.light_energy = energy


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
