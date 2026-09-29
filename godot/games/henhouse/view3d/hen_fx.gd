class_name HenFx
extends Bursts
## Henhouse Heist effects on top of the shared bursts: feathers that tumble and drift down (from the hens, from the
## goose's wings), eggs that pop in a sparkle, grain that scatters and bounces, dust where the farmhand lands,
## the goose's wing gusts, confetti at a level clear, and the golden pollen drifting in the evening light.

const CONFETTI := [Color(1.0, 0.3, 0.35), Color(1.0, 0.85, 0.25), Color(0.35, 0.8, 1.0), Color(0.5, 1.0, 0.45),
	Color(1.0, 0.5, 0.9), Color(1.0, 1.0, 1.0)]

var _feathers: Array[CPUParticles3D] = []
var _next_feather := 0
var _confetti: Array[CPUParticles3D] = []
var _pollen: CPUParticles3D
var _feather_mat: StandardMaterial3D


func _init() -> void:
	# sizes in this game's own unit (its median burst about 0.4 m across, a little more at birth)
	size_unit = 21.8


func _ready() -> void:
	super()
	# a feather: a soft, long, slightly glossy blade that tumbles as it falls
	_feather_mat = StandardMaterial3D.new()
	_feather_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_feather_mat.billboard_keep_scale = true
	_feather_mat.vertex_color_use_as_albedo = true
	_feather_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_feather_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_feather_mat.albedo_texture = Fx.material("soft").albedo_texture
	_feather_mat.roughness = 0.6
	_feather_mat.rim_enabled = true
	_feather_mat.rim = 0.6
	_feather_mat.emission_enabled = true
	_feather_mat.emission = Color(0.22, 0.16, 0.1)
	for i in 8:
		var f := CPUParticles3D.new()
		f.one_shot = true
		f.emitting = false
		f.explosiveness = 0.9
		f.local_coords = false
		var q := QuadMesh.new()
		q.size = Vector2(0.16, 0.06)
		f.mesh = q
		f.material_override = _feather_mat
		f.spread = 80.0
		f.direction = Vector3(0, 1, 0.2)
		f.gravity = Vector3(0, -1.4, 0)
		f.damping_min = 2.0
		f.damping_max = 3.5
		f.angle_min = 0.0
		f.angle_max = 360.0
		f.angular_velocity_min = -300.0
		f.angular_velocity_max = 300.0
		f.scale_amount_min = 0.7
		f.scale_amount_max = 1.3
		var fade := Gradient.new()
		fade.offsets = PackedFloat32Array([0.0, 0.75, 1.0])
		fade.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.9), Color(1, 1, 1, 0)])
		f.color_ramp = fade
		add_child(f)
		_feathers.append(f)
	for i in 3:
		var c := CPUParticles3D.new()
		c.one_shot = true
		c.emitting = false
		c.explosiveness = 0.9
		c.amount = 80
		c.lifetime = 3.4
		c.local_coords = false
		var q := QuadMesh.new()
		q.size = Vector2(0.12, 0.07)
		c.mesh = q
		var m := StandardMaterial3D.new()
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.billboard_keep_scale = true
		m.vertex_color_use_as_albedo = true
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.emission_enabled = true
		m.emission = Color(0.3, 0.3, 0.3)
		m.roughness = 0.4
		c.material_override = m
		c.direction = Vector3(0, 1, 0.3)
		c.spread = 50.0
		c.initial_velocity_min = 4.5
		c.initial_velocity_max = 8.0
		c.gravity = Vector3(0, -4.0, 0)
		c.damping_min = 1.6
		c.damping_max = 2.6
		c.angle_min = 0.0
		c.angle_max = 360.0
		c.angular_velocity_min = -540.0
		c.angular_velocity_max = 540.0
		c.scale_amount_min = 0.667
		c.scale_amount_max = 1.33
		var g := Gradient.new()
		g.interpolation_mode = Gradient.GRADIENT_INTERPOLATE_CONSTANT
		g.offsets = PackedFloat32Array([0.0, 0.17, 0.34, 0.5, 0.67, 0.84])
		g.colors = PackedColorArray(CONFETTI)
		c.color_initial_ramp = g
		add_child(c)
		_confetti.append(c)
	# golden pollen and dust motes in the low sun
	_pollen = CPUParticles3D.new()
	_pollen.amount = 70
	_pollen.lifetime = 9.0
	_pollen.preprocess = 9.0
	_pollen.local_coords = false
	_pollen.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_pollen.emission_box_extents = Vector3(12.0, 7.0, 1.5)
	_pollen.position = Vector3(0, 0.0, 0.2)
	_pollen.direction = Vector3(1, 0.3, 0)
	_pollen.spread = 60.0
	_pollen.initial_velocity_min = 0.05
	_pollen.initial_velocity_max = 0.25
	_pollen.gravity = Vector3(0.03, 0.02, 0)
	var pq := QuadMesh.new()
	pq.size = Vector2(0.1, 0.1)
	_pollen.mesh = pq
	_pollen.material_override = Fx.material("glow", Color(1.0, 0.85, 0.5, 0.55))
	_pollen.scale_amount_min = 0.5
	_pollen.scale_amount_max = 1.5
	var pg := Gradient.new()
	pg.offsets = PackedFloat32Array([0.0, 0.3, 0.7, 1.0])
	pg.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.9), Color(1, 1, 1, 0)])
	_pollen.color_ramp = pg
	add_child(_pollen)


func burst(pos: Vector3, color: Color, amount: int, speed: float, life: float, size: float, glow: float, gravity: float,
		up: float = 1.0, kind: String = "") -> void:
	var p := _pool[_next]
	p.damping_min = 0.0
	p.damping_max = 0.0
	p.spread = 70.0
	p.visible = true
	super(pos, color, amount, speed, life, size, glow, gravity, up, kind)


## Feathers from a bird: `n` of them, in `col`, thrown out at `speed` (a flurry when the goose flaps or a hen
## is bumped), drifting down for a couple of seconds.
func feathers(pos: Vector3, col: Color, n := 6, speed := 1.6, dir := Vector3(0, 1, 0.2)) -> void:
	var f := _feathers[_next_feather]
	_next_feather = (_next_feather + 1) % _feathers.size()
	f.position = pos
	f.amount = n
	f.lifetime = 2.2
	f.direction = dir
	f.initial_velocity_min = speed * 0.4
	f.initial_velocity_max = speed
	f.color = col
	f.visible = true
	f.restart()
	f.emitting = true


## An egg collected: a bright pop of sparkles, a ring of glints and a flash of warm light.
func egg_pop(pos: Vector3) -> void:
	burst(pos, Color(1.0, 0.92, 0.6), 22, 2.8, 0.7, 0.09, 1.0, -2.5, 1.0, "glow")
	var p := _pool[_next]
	burst(pos, Color(1.0, 0.95, 0.8), 10, 1.8, 0.4, 0.08, 1.0, 0.0, 0.0, "glow")
	p.spread = 180.0
	burst(pos + Vector3(0, -0.05, 0), Color(1.0, 0.95, 0.85, 0.8), 8, 0.9, 0.5, 0.2, 0.0, -0.5, 0.4, "smoke")
	flash(pos - Vector3(0, 1.8, 0), Color(1.0, 0.85, 0.5), 2.0)


## A grain sack emptied: kernels thrown up that fall and scatter, a puff of chaff.
func grain(pos: Vector3) -> void:
	burst(pos, Color(0.98, 0.82, 0.38), 34, 3.2, 0.9, 0.06, 0.0, -12.0, 1.0)
	burst(pos + Vector3(0, 0.05, 0), Color(0.95, 0.85, 0.6, 0.6), 8, 1.0, 0.8, 0.28, 0.0, -0.2, 0.5, "smoke")
	burst(pos, Color(0.6, 0.9, 1.0), 10, 1.5, 0.6, 0.08, 1.0, 0.5, 1.0, "glow")


func dust(pos: Vector3, big := false) -> void:
	var p := _pool[_next]
	burst(pos + Vector3(0, 0.04, 0), Color(0.9, 0.8, 0.62, 0.75), 12 if big else 5, 1.4 if big else 0.8, 0.55, 0.22 if big else 0.14,
		0.0, -0.4, 0.15, "smoke")
	p.spread = 85.0


## The goose's wing beat: a gust of air behind it and a loose feather now and then.
func gust(pos: Vector3, back: float) -> void:
	var p := _pool[_next]
	burst(pos, Color(1.0, 0.95, 0.85, 0.35), 4, 1.8, 0.5, 0.3, 0.0, -0.3, 0.0, "smoke")
	p.direction = Vector3(back, -0.4, 0.0)
	p.spread = 25.0


## A new level: whatever is still in the air from the last one goes (the camera opens close, it would fill the view).
func clear() -> void:
	for c in _confetti:
		c.visible = false
	for f in _feathers:
		f.visible = false
	for p in _pool:
		p.emitting = false
		p.visible = false


func confetti(pos: Vector3) -> void:
	for i in _confetti.size():
		var c := _confetti[i]
		c.visible = true
		c.position = pos + Vector3((i - 1) * 2.2, -0.3 * absf(i - 1), 0)
		c.direction = Vector3((i - 1) * 0.35, 1, 0.3)
		c.restart()
		c.emitting = true
