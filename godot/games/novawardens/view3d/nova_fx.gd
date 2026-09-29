class_name NovaFx
extends Bursts
## Nova Wardens effects, on top of the shared Bursts: voxel shards that tumble, fall and cool from white-hot to their
## colour, and expanding shockwave rings. Pooled, so a busy wave costs no allocations.

const SHARDS := 160
const RINGS := 10

var _shards: Array[Dictionary] = []   ## {node, vel, spin, life, age, col}
var _next_shard := 0
var _rings: Array[Dictionary] = []    ## {node, mat, age, life, size}
var _next_ring := 0
var _shard_mats := {}


func _ready() -> void:
	super._ready()
	var box := BoxMesh.new()
	box.size = Vector3.ONE * 0.09
	for i in SHARDS:
		var mi := MeshInstance3D.new()
		mi.mesh = box
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_shards.append({"node": mi, "vel": Vector3.ZERO, "spin": Vector3.ZERO, "life": 0.0, "age": 1.0})
	var q := QuadMesh.new()
	q.size = Vector2(2, 2)
	for i in RINGS:
		var mi := MeshInstance3D.new()
		mi.mesh = q
		var m := ShaderMaterial.new()
		m.shader = preload("res://games/novawardens/shaders/nova_ring.gdshader")
		mi.material_override = m
		mi.visible = false
		add_child(mi)
		_rings.append({"node": mi, "mat": m, "age": 1.0, "life": 1.0, "size": 1.0})


func _shard_mat(col: Color) -> StandardMaterial3D:
	var key := col.to_html()
	if not _shard_mats.has(key):
		var m := StandardMaterial3D.new()
		m.albedo_color = col
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = 2.5
		m.roughness = 0.3
		_shard_mats[key] = m
	return _shard_mats[key]


## Voxel shards bursting from pos: count of them, flung at up to speed, in col (some white-hot).
func shards(pos: Vector3, col: Color, count: int, speed: float, size := 1.0, life := 0.9) -> void:
	for i in count:
		var s: Dictionary = _shards[_next_shard]
		_next_shard = (_next_shard + 1) % SHARDS
		var n: MeshInstance3D = s["node"]
		n.visible = true
		n.position = pos + Vector3(randf_range(-0.1, 0.1), randf_range(-0.08, 0.08), randf_range(-0.05, 0.05))
		n.scale = Vector3.ONE * size * randf_range(0.6, 1.6)
		n.material_override = _shard_mat(col.lerp(Color.WHITE, 0.6) if i % 4 == 0 else col)
		var dir := Vector3(randf_range(-1, 1), randf_range(-0.6, 1.2), randf_range(-0.4, 0.8)).normalized()
		s["vel"] = dir * randf_range(0.3, 1.0) * speed
		s["spin"] = Vector3(randf_range(-12, 12), randf_range(-12, 12), randf_range(-12, 12))
		s["life"] = life * randf_range(0.7, 1.3)
		s["age"] = 0.0


## A shockwave ring at pos, growing to size over life seconds.
func ring(pos: Vector3, col: Color, size: float, life := 0.45, energy := 3.0) -> void:
	var r: Dictionary = _rings[_next_ring]
	_next_ring = (_next_ring + 1) % RINGS
	var n: MeshInstance3D = r["node"]
	n.visible = true
	n.position = pos + Vector3(0, 0, 0.15)
	r["age"] = 0.0
	r["life"] = life
	r["size"] = size
	var m: ShaderMaterial = r["mat"]
	m.set_shader_parameter("color", col)
	m.set_shader_parameter("energy", energy)


func _process(delta: float) -> void:
	super._process(delta)
	for s in _shards:
		if s["age"] >= s["life"]:
			continue
		s["age"] += delta
		var n: MeshInstance3D = s["node"]
		if s["age"] >= s["life"]:
			n.visible = false
			continue
		var v: Vector3 = s["vel"]
		v.y -= 6.0 * delta
		v *= 1.0 - 1.2 * delta
		s["vel"] = v
		n.position += v * delta
		n.rotation += s["spin"] * delta
		var k: float = s["age"] / s["life"]
		n.scale = n.scale.lerp(Vector3.ZERO, clampf(delta * 2.5 * k, 0.0, 1.0))
	for r in _rings:
		if r["age"] >= r["life"]:
			continue
		r["age"] += delta
		var n: MeshInstance3D = r["node"]
		var k: float = clampf(r["age"] / r["life"], 0.0, 1.0)
		n.scale = Vector3.ONE * r["size"]
		(r["mat"] as ShaderMaterial).set_shader_parameter("progress", k)
		if k >= 1.0:
			n.visible = false
