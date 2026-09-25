class_name CaveEffects
extends Node3D
## Particles and light flashes driven by the engine's events (dig dust, gem sparkles, explosions, landings).
## Emitters are pooled one-shot CPUParticles3D, which work the same with every renderer.

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")

var _pool: Array[CPUParticles3D] = []
var _next := 0
var _flashes: Array[OmniLight3D] = []
var _next_flash := 0
var _materials := {}


func _ready() -> void:
	for i in 48:
		var p := CPUParticles3D.new()
		p.one_shot = true
		p.emitting = false
		p.explosiveness = 0.9
		p.local_coords = false
		var q := QuadMesh.new()
		q.size = Vector2(0.12, 0.12)
		p.mesh = q
		add_child(p)
		_pool.append(p)
	for i in 6:
		var l := OmniLight3D.new()
		l.light_energy = 0.0
		l.omni_range = 5.0
		add_child(l)
		_flashes.append(l)


func _material(color: Color, glow: float) -> StandardMaterial3D:
	var key := "%s/%s" % [color, glow]
	if not _materials.has(key):
		var m := StandardMaterial3D.new()
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if glow > 0.0 else BaseMaterial3D.SHADING_MODE_PER_PIXEL
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.vertex_color_use_as_albedo = true
		m.albedo_color = color * (1.0 + glow)
		_materials[key] = m
	return _materials[key]


func burst(pos: Vector3, color: Color, amount: int, speed: float, life: float, size: float, glow: float,
		gravity: float = -9.0) -> void:
	var p := _pool[_next]
	_next = (_next + 1) % _pool.size()
	p.position = pos
	p.amount = amount
	p.lifetime = life
	p.direction = Vector3(0, 1, 0.4)
	p.spread = 180.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector3(0, gravity, 0)
	p.scale_amount_min = size * 0.5
	p.scale_amount_max = size
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 1))
	fade.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = fade
	p.material_override = _material(color, glow)
	p.restart()
	p.emitting = true


func flash(pos: Vector3, color: Color, energy: float) -> void:
	var l := _flashes[_next_flash]
	_next_flash = (_next_flash + 1) % _flashes.size()
	l.position = pos + Vector3(0, 0, 1.0)
	l.light_color = color
	l.light_energy = energy


func _process(delta: float) -> void:
	for l in _flashes:
		l.light_energy = maxf(0.0, l.light_energy - delta * 10.0)


func on_event(ev: Array, engine: CaveEngine) -> void:
	var pos := Vector3(ev[2], -ev[3], 0.3) if ev.size() >= 4 and ev[2] is int else Vector3.ZERO
	match ev[0]:
		"eat":
			var el: int = ev[1]
			if el == E.DIAMOND or el == E.FLYING_DIAMOND:
				burst(pos, Color(0.4, 0.95, 1.0), 26, 4.0, 0.7, 1.0, 2.5, -2.0)
				flash(pos, Color(0.4, 0.9, 1.0), 3.0)
			elif (E.FLAGS[el] & E.P_DIRT) != 0:
				burst(pos, Color(0.4, 0.26, 0.14), 14, 2.2, 0.5, 1.2, 0.0)
		"effect":
			if not ev[4]:
				return
			var el: int = ev[1]
			if el == E.STONE or el == E.STONE_F or el == E.MEGA_STONE:
				burst(pos + Vector3(0, -0.45, 0), Color(0.55, 0.5, 0.45), 10, 1.6, 0.45, 1.0, 0.0, -4.0)
			elif el == E.DIAMOND or el == E.DIAMOND_F:
				burst(pos, Color(0.5, 0.95, 1.0), 6, 1.5, 0.4, 0.6, 2.0, -2.0)
		"explosion":
			burst(pos, Color(1.0, 0.55, 0.15), 60, 7.0, 0.9, 2.2, 3.0, -3.0)
			burst(pos, Color(0.3, 0.28, 0.26), 30, 3.0, 1.4, 2.5, 0.0, 1.0)
			flash(pos, Color(1.0, 0.6, 0.25), 9.0)
		"sound":
			if ev[1] == "crack" and engine.gate_open:
				for y in engine.h:
					for x in engine.w:
						var e := engine.map[y * engine.w + x]
						if e == E.OUTBOX or e == E.PRE_OUTBOX:
							flash(Vector3(x, -y, 0.3), Color(0.4, 1.0, 0.6), 8.0)
