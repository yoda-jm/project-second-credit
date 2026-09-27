class_name FizzFx
extends Bursts
## Fizzlings effects on top of the shared bursts: shock rings from popping bubbles, droplet sprays, gold sparkles
## and short-lived twinkles.

const RING_LIFE := 0.45

var _rings: Array[Dictionary] = []   ## {node, t, life}
var _next_ring := 0
var _ring_mat: ShaderMaterial


func _ready() -> void:
	super._ready()
	_ring_mat = ShaderMaterial.new()
	_ring_mat.shader = load("res://games/fizzlings/view3d/ring.gdshader")
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	for i in 16:
		var m := MeshInstance3D.new()
		m.mesh = q
		m.material_override = _ring_mat
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m.visible = false
		add_child(m)
		_rings.append({"node": m, "t": 1.0, "life": RING_LIFE})


func _process(delta: float) -> void:
	super._process(delta)
	for r in _rings:
		var m: MeshInstance3D = r["node"]
		if not m.visible:
			continue
		r["t"] += delta / r["life"]
		if r["t"] >= 1.0:
			m.visible = false
		else:
			m.set_instance_shader_parameter("life", r["t"])


## A shock ring, facing the camera, that grows to "size" across.
func ring(pos: Vector3, color: Color, size: float, life := RING_LIFE) -> void:
	var r: Dictionary = _rings[_next_ring]
	_next_ring = (_next_ring + 1) % _rings.size()
	var m: MeshInstance3D = r["node"]
	m.position = pos
	m.scale = Vector3.ONE * size
	m.visible = true
	m.set_instance_shader_parameter("color", color)
	m.set_instance_shader_parameter("life", 0.0)
	r["t"] = 0.0
	r["life"] = life


## Droplets flung out of a popping bubble: small bright beads that slow down and sink a little.
func droplets(pos: Vector3, color: Color, amount: int, speed := 3.0) -> void:
	burst(pos, color, amount, speed, 0.55, 0.07, 1.0, -3.0, 0.2, "glow")
	_all_round()


## Gold twinkles thrown about (treats, full bubbles popping).
func sparkles(pos: Vector3, color: Color, amount: int, speed := 2.5) -> void:
	burst(pos, color, amount, speed, 0.8, 0.13, 1.0, -1.5, 1.0, "glow")
	_all_round()


## The burst just fired flies out all round, not in a fountain.
func _all_round() -> void:
	var p: CPUParticles3D = _pool[(_next - 1 + _pool.size()) % _pool.size()]
	p.spread = 180.0
	p.direction = Vector3(0, 1, 0)
