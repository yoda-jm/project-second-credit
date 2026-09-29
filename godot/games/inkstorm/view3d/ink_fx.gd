class_name InkFx
extends Bursts
## Inkstorm's own effects on top of the shared bursts: the golden shards of a broken line (tumbling, bouncing on the
## board), rings of light spreading over new land, star flares, and effects set to go off a little later (as a
## claim wave passes over them).

const GLOW := preload("res://games/inkstorm/shaders/ink_glow.gdshader")
const MAX_SHARDS := 320

var _mm: MultiMesh
var _shards: Array[Dictionary] = []  ## {p, v, axis, spin, rot, age, life, s, col}
var _rings: Array[Dictionary] = []   ## {node, mat, age, dur, r0, r1, energy}
var _later: Array[Dictionary] = []   ## {at, fn}
var _t := 0.0


func _init() -> void:
	# sizes in this game's own unit (its median burst about 0.4 m across, a little more at birth)
	size_unit = 20.7


func _ready() -> void:
	super._ready()
	_mm = MultiMesh.new()
	_mm.transform_format = MultiMesh.TRANSFORM_3D
	_mm.use_colors = true
	var pm := PrismMesh.new()
	pm.size = Vector3(0.12, 0.15, 0.03)
	_mm.mesh = pm
	_mm.instance_count = MAX_SHARDS
	_mm.visible_instance_count = 0
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.metallic = 1.0
	mat.roughness = 0.18
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.75, 0.35)
	mat.emission_energy_multiplier = 1.4
	pm.material = mat
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = _mm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


func clear() -> void:
	_shards.clear()
	_later.clear()
	_mm.visible_instance_count = 0
	for r in _rings:
		r["node"].queue_free()
	_rings.clear()


## A shard of gold flung from the line.
func shard(pos: Vector3, vel: Vector3, col: Color) -> void:
	if _shards.size() >= MAX_SHARDS:
		_shards.pop_front()
	var axis := Vector3(randf() - 0.5, randf() - 0.5, randf() - 0.5).normalized()
	_shards.append({"p": pos, "v": vel, "axis": axis if axis.length() > 0.1 else Vector3.UP, "spin": randf_range(8.0, 22.0),
		"rot": randf() * TAU, "age": 0.0, "life": randf_range(1.0, 1.6), "s": randf_range(0.5, 1.2), "col": col})


## A ring of light lying on the land, spreading from r0 to r1 (world units) over dur seconds.
func ring(pos: Vector3, r0: float, r1: float, col: Color, dur: float, energy: float, width := 0.05) -> void:
	_add_quad(pos, r0, r1, col, dur, energy, 2, false, width, 0.0)


## A star flare turned to the camera, swelling and fading.
func star(pos: Vector3, r0: float, r1: float, col: Color, dur: float, energy: float, rays := 1.0) -> void:
	_add_quad(pos, r0, r1, col, dur, energy, 1, true, 0.0, rays)


func _add_quad(pos: Vector3, r0: float, r1: float, col: Color, dur: float, energy: float, mode: int, bb: bool, width: float,
		rays: float) -> void:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(2, 2)
	if not bb:
		q.orientation = PlaneMesh.FACE_Y
	mi.mesh = q
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := ShaderMaterial.new()
	m.shader = GLOW
	m.set_shader_parameter("color", col)
	m.set_shader_parameter("mode", mode)
	m.set_shader_parameter("billboard", bb)
	m.set_shader_parameter("ring", 0.85)
	m.set_shader_parameter("ring_w", width / maxf(r1, 0.01) * 1.0 if width > 0.0 else 0.06)
	m.set_shader_parameter("rays", rays)
	m.set_shader_parameter("spin", 0.6)
	m.set_shader_parameter("energy", 0.0)
	mi.material_override = m
	mi.position = pos
	mi.scale = Vector3.ONE * maxf(r0, 0.001)
	add_child(mi)
	_rings.append({"node": mi, "mat": m, "age": 0.0, "dur": dur, "r0": r0, "r1": r1, "energy": energy})


## Run fn after delay seconds.
func later(delay: float, fn: Callable) -> void:
	_later.append({"at": _t + delay, "fn": fn})


func _process(delta: float) -> void:
	super._process(delta)
	_t += delta
	var due: Array[Dictionary] = []
	for l in _later:
		if l["at"] <= _t:
			due.append(l)
	for l in due:
		_later.erase(l)
		l["fn"].call()
	# shards tumble, bounce on the board and shrink away
	var i := 0
	while i < _shards.size():
		var s: Dictionary = _shards[i]
		s["age"] += delta
		if s["age"] >= s["life"]:
			_shards.remove_at(i)
			continue
		var v: Vector3 = s["v"]
		v.y -= 9.0 * delta
		var p: Vector3 = s["p"] + v * delta
		if p.y < 0.02 and v.y < 0.0:
			p.y = 0.02
			v = Vector3(v.x * 0.55, -v.y * 0.35, v.z * 0.55)
			s["spin"] *= 0.6
		s["v"] = v
		s["p"] = p
		s["rot"] += s["spin"] * delta
		i += 1
	for j in _shards.size():
		var s: Dictionary = _shards[j]
		var k: float = s["age"] / s["life"]
		var sc: float = s["s"] * (1.0 - smoothstep(0.6, 1.0, k))
		_mm.set_instance_transform(j, Transform3D(Basis(s["axis"], s["rot"]).scaled(Vector3.ONE * maxf(sc, 0.001)), s["p"]))
		var c: Color = s["col"]
		var tw := 1.0 + 0.8 * maxf(0.0, sin(s["rot"] * 2.0))  # facets catch the light as they spin
		_mm.set_instance_color(j, Color(c.r * tw, c.g * tw, c.b * tw))
	_mm.visible_instance_count = _shards.size()
	# rings and flares
	i = 0
	while i < _rings.size():
		var r: Dictionary = _rings[i]
		r["age"] += delta
		var k: float = r["age"] / r["dur"]
		if k >= 1.0:
			r["node"].queue_free()
			_rings.remove_at(i)
			continue
		var e := 1.0 - pow(1.0 - k, 3.0)
		r["node"].scale = Vector3.ONE * maxf(0.001, lerpf(r["r0"], r["r1"], e))
		var a := minf(1.0, k * 8.0) * pow(1.0 - k, 1.5)
		r["mat"].set_shader_parameter("energy", r["energy"] * a)
		i += 1
