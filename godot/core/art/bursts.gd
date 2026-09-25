class_name Bursts
extends Node3D
## Pooled particle bursts and soft light flashes, shared by the games (each game extends it with its own
## effects). Particles use the soft round materials of Fx, never flat squares.

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
