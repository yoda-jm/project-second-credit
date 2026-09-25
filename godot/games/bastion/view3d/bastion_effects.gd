class_name BastionEffects
extends Node3D
## Pooled particle bursts and light flashes for Bastion Coast: muzzle smoke, splashes, dirt, fire, dust.

var _pool: Array[CPUParticles3D] = []
var _next := 0
var _lights: Array[OmniLight3D] = []
var _next_light := 0
var _mats := {}


func _ready() -> void:
	for i in 40:
		var p := CPUParticles3D.new()
		p.one_shot = true
		p.emitting = false
		p.explosiveness = 0.85
		p.local_coords = false
		var q := QuadMesh.new()
		q.size = Vector2(0.25, 0.25)
		p.mesh = q
		add_child(p)
		_pool.append(p)
	for i in 6:
		var l := OmniLight3D.new()
		l.light_energy = 0.0
		l.omni_range = 6.0
		add_child(l)
		_lights.append(l)


func _process(delta: float) -> void:
	for l in _lights:
		l.light_energy = maxf(0.0, l.light_energy - delta * 12.0)


func _mat(color: Color, glow: float) -> StandardMaterial3D:
	var key := str(color) + str(glow)
	if not _mats.has(key):
		var m := StandardMaterial3D.new()
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if glow > 0.0 else BaseMaterial3D.SHADING_MODE_PER_PIXEL
		m.vertex_color_use_as_albedo = true
		m.albedo_color = color * (1.0 + glow)
		_mats[key] = m
	return _mats[key]


func burst(pos: Vector3, color: Color, amount: int, speed: float, life: float, size: float, glow: float, gravity: float,
		up: float = 1.0) -> void:
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
	p.material_override = _mat(color, glow)
	p.restart()
	p.emitting = true


func flash(pos: Vector3, color: Color, energy: float) -> void:
	var l := _lights[_next_light]
	_next_light = (_next_light + 1) % _lights.size()
	l.position = pos + Vector3(0, 1.0, 0)
	l.light_color = color
	l.light_energy = energy


func dust(pos: Vector3, amount: int) -> void:
	burst(pos, Color(0.75, 0.68, 0.55), amount, 1.8, 0.6, 1.6, 0.0, -2.0)


func muzzle(pos: Vector3, ours: bool) -> void:
	burst(pos, Color(0.85, 0.85, 0.85), 16, 2.0, 1.2, 3.0, 0.0, 0.8)
	burst(pos, Color(1.0, 0.7, 0.3), 10, 4.0, 0.25, 1.2, 3.0, 0.0)
	flash(pos, Color(1.0, 0.7, 0.4), 4.0 if ours else 2.5)


func impact(pos: Vector3, water: bool) -> void:
	if water:
		burst(pos, Color(0.8, 0.92, 1.0), 30, 5.0, 0.9, 1.4, 0.3, -9.0)
	else:
		burst(pos, Color(0.5, 0.4, 0.3), 24, 4.0, 0.8, 1.6, 0.0, -8.0)


func explosion(pos: Vector3, scale: float) -> void:
	burst(pos, Color(1.0, 0.55, 0.15), int(40 * scale), 6.0 * scale, 0.8, 2.4 * scale, 3.0, -2.0)
	burst(pos, Color(0.25, 0.23, 0.22), int(30 * scale), 2.5, 2.0, 3.5 * scale, 0.0, 1.2)
	flash(pos, Color(1.0, 0.55, 0.2), 8.0 * scale)
