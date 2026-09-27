class_name HopFx
extends Bursts
## Hopline effects on top of the shared bursts: dust where the frog lands, splashes, bubbles over diving turtles,
## a sparkle trail round the fly, honk bursts, confetti and a fireworks show when all five bays fill, and the little
## lights of the air over the canal (pollen in the afternoon, gnats at sunset, blinking fireflies at night).

const CONFETTI := [Color(1.0, 0.3, 0.35), Color(1.0, 0.85, 0.25), Color(0.35, 0.8, 1.0), Color(0.5, 1.0, 0.45),
	Color(1.0, 0.5, 0.9), Color(1.0, 1.0, 1.0)]
const SHELLS := [Color(1.0, 0.45, 0.3), Color(1.0, 0.85, 0.35), Color(0.45, 0.85, 1.0), Color(0.6, 1.0, 0.5),
	Color(1.0, 0.5, 0.95)]

var _confetti: Array[CPUParticles3D] = []
var _air: CPUParticles3D
var _fly_trail: CPUParticles3D
var _shows: Array[Dictionary] = []   ## pending fireworks: {t, pos, col}
var _rockets: Array[Dictionary] = [] ## rising rockets: {node, from, to, t, col}
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	super()
	_rng.seed = 5
	for i in 3:
		var c := CPUParticles3D.new()
		c.one_shot = true
		c.emitting = false
		c.explosiveness = 0.92
		c.amount = 90
		c.lifetime = 3.2
		c.local_coords = false
		var q := QuadMesh.new()
		q.size = Vector2(0.12, 0.07)
		c.mesh = q
		var m := StandardMaterial3D.new()
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.vertex_color_use_as_albedo = true
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.emission_enabled = true
		m.emission = Color(0.25, 0.25, 0.25)
		m.roughness = 0.4
		c.material_override = m
		c.direction = Vector3(0, 1, 0.3)
		c.spread = 55.0
		c.initial_velocity_min = 4.0
		c.initial_velocity_max = 7.5
		c.gravity = Vector3(0, -4.0, 0)
		c.damping_min = 1.6
		c.damping_max = 2.6
		c.angle_min = 0.0
		c.angle_max = 360.0
		c.angular_velocity_min = -540.0
		c.angular_velocity_max = 540.0
		c.scale_amount_min = 0.7
		c.scale_amount_max = 1.4
		var g := Gradient.new()
		g.interpolation_mode = Gradient.GRADIENT_INTERPOLATE_CONSTANT
		g.offsets = PackedFloat32Array([0.0, 0.17, 0.34, 0.5, 0.67, 0.84])
		g.colors = PackedColorArray(CONFETTI)
		c.color_initial_ramp = g
		add_child(c)
		_confetti.append(c)
	# the air over the canal
	_air = CPUParticles3D.new()
	_air.amount = 40
	_air.lifetime = 6.0
	_air.preprocess = 6.0
	_air.local_coords = false
	_air.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_air.emission_box_extents = Vector3(11.0, 0.45, 2.6)
	_air.position = Vector3(0, 0.75, -3.0)
	_air.direction = Vector3(1, 0.2, 0)
	_air.spread = 180.0
	_air.initial_velocity_min = 0.05
	_air.initial_velocity_max = 0.3
	_air.gravity = Vector3(0, 0.02, 0)
	var aq := QuadMesh.new()
	aq.size = Vector2(0.16, 0.16)
	_air.mesh = aq
	_air.scale_amount_min = 0.4
	_air.scale_amount_max = 1.0
	add_child(_air)
	# the fly's sparkle trail
	_fly_trail = CPUParticles3D.new()
	_fly_trail.amount = 24
	_fly_trail.lifetime = 0.9
	_fly_trail.local_coords = false
	_fly_trail.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	_fly_trail.emission_sphere_radius = 0.18
	_fly_trail.direction = Vector3(0, 1, 0)
	_fly_trail.spread = 180.0
	_fly_trail.initial_velocity_min = 0.1
	_fly_trail.initial_velocity_max = 0.5
	_fly_trail.gravity = Vector3(0, 0.3, 0)
	var fq := QuadMesh.new()
	fq.size = Vector2(0.12, 0.12)
	_fly_trail.mesh = fq
	_fly_trail.material_override = Fx.material("glow", Color(1.0, 0.95, 0.5))
	_fly_trail.scale_amount_curve = Fx.size_curve(false)
	_fly_trail.scale_amount_min = 0.5
	_fly_trail.scale_amount_max = 1.2
	_fly_trail.emitting = false
	add_child(_fly_trail)


## The air's little lights for the time of day: 0 afternoon pollen, 1 sunset gnats, 2 night fireflies.
func set_air(mood: int) -> void:
	var g := Gradient.new()
	match mood:
		2:
			_air.amount = 46
			_air.material_override = Fx.material("glow", Color(0.75, 1.0, 0.35))
			# fireflies blink: on and off several times over their life
			g.offsets = PackedFloat32Array([0.0, 0.1, 0.2, 0.3, 0.42, 0.55, 0.65, 0.78, 0.9, 1.0])
			g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0.1), Color(1, 1, 1, 0),
				Color(1, 1, 1, 1), Color(1, 1, 1, 0.05), Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0.2),
				Color(1, 1, 1, 0)])
			_air.scale_amount_min = 0.5
			_air.scale_amount_max = 1.1
		1:
			_air.amount = 30
			_air.material_override = Fx.material("glow", Color(1.0, 0.6, 0.3, 0.55))
			g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0.8), Color(1, 1, 1, 0)])
			g.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
			_air.scale_amount_min = 0.25
			_air.scale_amount_max = 0.6
		_:
			_air.amount = 34
			_air.material_override = Fx.material("glow", Color(1.0, 0.92, 0.6, 0.45))
			g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0.7), Color(1, 1, 1, 0)])
			g.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
			_air.scale_amount_min = 0.2
			_air.scale_amount_max = 0.5
	_air.color_ramp = g
	_air.restart()


func burst(pos: Vector3, color: Color, amount: int, speed: float, life: float, size: float, glow: float, gravity: float,
		up: float = 1.0, kind: String = "") -> void:
	var p := _pool[_next]
	p.damping_min = 0.0  # a firework shell may have left its drag on this emitter
	p.damping_max = 0.0
	super(pos, color, amount, speed, life, size, glow, gravity, up, kind)


func fly_trail(on: bool, pos: Vector3) -> void:
	_fly_trail.position = pos
	if _fly_trail.emitting != on:
		_fly_trail.emitting = on


func dust(pos: Vector3) -> void:
	burst(pos + Vector3(0, 0.05, 0), Color(0.85, 0.78, 0.65, 0.7), 10, 1.2, 0.5, 0.22, 0.0, -0.5, 0.25, "smoke")


func splash(pos: Vector3, big := false) -> void:
	burst(pos, Color(0.85, 0.95, 1.0), 26 if big else 12, 2.6 if big else 1.6, 0.6, 0.09, 0.0, -7.0, 1.0)
	burst(pos + Vector3(0, 0.05, 0), Color(0.9, 0.97, 1.0, 0.6), 6, 0.7, 0.5, 0.28, 0.0, -0.3, 0.2, "smoke")


func bubbles(pos: Vector3, n := 6) -> void:
	burst(pos, Color(0.8, 0.95, 1.0), n, 0.5, 0.9, 0.08, 0.0, 1.2, 1.0)


func honk(pos: Vector3, dir: float) -> void:
	var p := _pool[_next]
	burst(pos, Color(1.0, 0.9, 0.4), 10, 3.0, 0.35, 0.1, 1.0, 0.0, 0.2, "glow")
	p.direction = Vector3(dir, 0.35, 0)
	p.spread = 30.0
	flash(pos, Color(1.0, 0.85, 0.5), 1.5)


func sparkle(pos: Vector3, col: Color, n := 16) -> void:
	burst(pos, col, n, 2.4, 0.7, 0.1, 1.0, -1.5, 1.0, "glow")


func confetti(pos: Vector3, wide := true) -> void:
	for i in _confetti.size():
		if not wide and i > 0:
			break
		var c := _confetti[i]
		c.position = pos + (Vector3((i - 1) * 6.0, 0, 0) if wide else Vector3.ZERO)
		c.amount = 90 if wide else 50
		c.restart()
		c.emitting = true


## A fireworks show over the hedge: n shells over `seconds`.
func fireworks(center: Vector3, n: int, seconds: float) -> void:
	for i in n:
		_shows.append({"t": seconds * float(i) / n + _rng.randf_range(0.0, 0.2),
			"pos": center + Vector3(_rng.randf_range(-7.5, 7.5), _rng.randf_range(4.0, 6.5), _rng.randf_range(-2.0, 0.5)),
			"col": SHELLS[i % SHELLS.size()]})


func _process(delta: float) -> void:
	super(delta)
	for s in _shows:
		s["t"] -= delta
		if s["t"] <= 0.0:
			var from: Vector3 = s["pos"] * Vector3(1, 0, 1) + Vector3(0, 0.5, 0)
			var r := MeshInstance3D.new()
			var q := QuadMesh.new()
			q.size = Vector2(0.25, 0.25)
			r.mesh = q
			r.material_override = Fx.material("glow", Color(1.0, 0.8, 0.5))
			add_child(r)
			_rockets.append({"node": r, "from": from, "to": s["pos"], "t": 0.0, "col": s["col"]})
	_shows = _shows.filter(func(s): return s["t"] > 0.0)
	for r in _rockets:
		r["t"] += delta / 0.55
		var k: float = minf(1.0, r["t"])
		var n: MeshInstance3D = r["node"]
		n.position = (r["from"] as Vector3).lerp(r["to"], 1.0 - (1.0 - k) * (1.0 - k))
		if k < 1.0 and _rng.randf() < 0.5:
			burst(n.position, Color(1.0, 0.75, 0.4), 2, 0.3, 0.35, 0.07, 1.0, -1.0, -1.0, "glow")
		if k >= 1.0:
			var c: Color = r["col"]
			var p := _pool[_next]
			burst(n.position, c, 60, 4.0, 1.3, 0.14, 1.0, -1.6, 1.0, "glow")
			p.spread = 180.0
			p.damping_min = 2.0
			p.damping_max = 3.0
			var p2 := _pool[_next]
			burst(n.position, Color(1, 1, 1), 24, 2.2, 0.6, 0.1, 1.0, -1.0, 1.0, "glow")
			p2.spread = 180.0
			flash(n.position - Vector3(0, 1.5, 0), c, 5.0)
			n.queue_free()
	_rockets = _rockets.filter(func(r): return r["t"] < 1.0)
