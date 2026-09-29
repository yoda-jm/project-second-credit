class_name PrismEffects
extends Bursts
## Prism Breaker effects: 3D crystal shards that burst out of a broken brick and tumble down in arcs (one multimesh,
## simple physics), sparks off steel and walls, pops for drones and capsules, light flashes, and the ribbons of light
## that trail the balls.

const SHARDS := 700
const SHARD := preload("res://games/prism/shaders/prism_shard.gdshader")
const HIDDEN := Transform3D(Basis(Vector3(0.0001, 0, 0), Vector3(0, 0.0001, 0), Vector3(0, 0, 0.0001)), Vector3(0, 0, -500))

var _mm: MultiMesh
var _shards: Array[Dictionary] = []  ## {p, v, axis, spin, rot, life, max, size, col}
var _free: Array[int] = []
var _trail: ImmediateMesh
var _trails := {}  ## key -> Array[Vector3] (newest first)
var _trail_cols := {}  ## key -> Color
var _rng := RandomNumberGenerator.new()


func _init() -> void:
	# sizes in this game's own unit (its median burst about 0.4 m across, a little more at birth)
	size_unit = 16.9


func _ready() -> void:
	super._ready()
	_rng.seed = 13
	_mm = MultiMesh.new()
	_mm.transform_format = MultiMesh.TRANSFORM_3D
	_mm.use_colors = true
	var pm := PrismMesh.new()  # a sliver: a thin triangular prism reads as a glass splinter
	pm.size = Vector3(1.0, 1.6, 0.35)
	pm.left_to_right = 0.3
	var sm := ShaderMaterial.new()
	sm.shader = SHARD
	pm.material = sm
	_mm.mesh = pm
	_mm.instance_count = SHARDS
	_mm.visible_instance_count = 0
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = _mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.custom_aabb = AABB(Vector3(-40, -40, -20), Vector3(80, 80, 60))
	add_child(mmi)
	_trail = ImmediateMesh.new()
	var tm := StandardMaterial3D.new()
	tm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	tm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	tm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	tm.vertex_color_use_as_albedo = true
	tm.cull_mode = BaseMaterial3D.CULL_DISABLED
	tm.no_depth_test = false
	var tmi := MeshInstance3D.new()
	tmi.mesh = _trail
	tmi.material_override = tm
	tmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	tmi.custom_aabb = AABB(Vector3(-40, -40, -20), Vector3(80, 80, 60))
	add_child(tmi)


## A brick breaks: shards of its colour, most flying out towards the viewer, then falling.
func shatter(pos: Vector3, col: Color, amount := 16, force := 1.0) -> void:
	for i in amount:
		var d := Vector3(_rng.randf_range(-1, 1), _rng.randf_range(-0.6, 1.2), _rng.randf_range(0.3, 1.6)).normalized()
		var p := pos + Vector3(_rng.randf_range(-0.45, 0.45), _rng.randf_range(-0.2, 0.2), _rng.randf_range(-0.1, 0.2))
		_spawn(p, d * _rng.randf_range(2.5, 7.0) * force, col.lerp(Color.WHITE, _rng.randf() * 0.35),
			_rng.randf_range(0.05, 0.13), _rng.randf_range(0.8, 1.5))
	burst(pos, col, 14, 4.0, 0.5, 0.14, 1.0, -9.0, 0.6, "glow")
	flash(pos + Vector3(0, -2.5, 1.2), col, 2.2)  # the flash sits 2.5 above: bring it level, in front


func _spawn(p: Vector3, v: Vector3, col: Color, size: float, life: float) -> void:
	var i: int
	if _free.size() > 0:
		i = _free.pop_back()
	elif _shards.size() < SHARDS:
		i = _shards.size()
		_shards.append({})
	else:
		i = _rng.randi() % SHARDS
	_shards[i] = {"p": p, "v": v, "axis": Vector3(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1), _rng.randf_range(-1, 1)).normalized(),
		"spin": _rng.randf_range(6.0, 16.0), "rot": _rng.randf() * TAU, "life": life, "max": life, "size": size, "col": col}


func spark(pos: Vector3, col: Color) -> void:
	burst(pos, col, 10, 3.5, 0.3, 0.08, 1.0, -4.0, -1.0, "glow")


func pop(pos: Vector3, col: Color) -> void:
	burst(pos, col, 30, 5.0, 0.6, 0.15, 1.0, 0.0, 1.0, "glow")
	flash(pos + Vector3(0, -2.5, 1.2), col, 3.0)  # the flash sits 2.5 above: bring it level, in front


## A ball touches a wall: a short spray of sparks off the frame and a flash on it.
func wall_hit(pos: Vector3, normal: Vector3, col: Color) -> void:
	var p := _pool[_next]
	burst(pos, col, 12, 4.0, 0.3, 0.07, 1.0, -3.0, 0.0, "glow")
	p.direction = normal
	p.spread = 55.0
	flash(pos + Vector3(0, -2.5, 0.8), col, 1.6)


## Records where a ball is this frame; the trail is rebuilt from these in draw_trails().
func trail_point(key: int, pos: Vector3, col: Color) -> void:
	var t: Array = _trails.get(key, [])
	if t.size() > 0 and (t[0] as Vector3).distance_to(pos) > 2.0:
		t.clear()  # a ball index changed hands (multiball): start afresh
	t.push_front(pos)
	if t.size() > 16:
		t.resize(16)
	_trails[key] = t
	_trail_cols[key] = col


func drop_trail(key: int) -> void:
	_trails.erase(key)


func clear_trails(keep: int) -> void:
	for k in _trails.keys():
		if k >= keep:
			_trails.erase(k)


func draw_trails(cam: Camera3D) -> void:
	_trail.clear_surfaces()
	if cam == null:
		return
	var any := false
	for k in _trails:
		var t: Array = _trails[k]
		if t.size() < 3:
			continue
		if not any:
			_trail.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
			any = true
		var col: Color = _trail_cols[k]
		var n := t.size()
		var prev_l := Vector3.ZERO
		var prev_r := Vector3.ZERO
		var prev_c := Color.BLACK
		for i in n:
			var p: Vector3 = t[i]
			var dir: Vector3 = (t[maxi(i - 1, 0)] - t[mini(i + 1, n - 1)])
			if dir.length() < 0.0001:
				dir = Vector3.UP
			var side := dir.cross(cam.global_position - p).normalized()
			var f := 1.0 - float(i) / float(n - 1)
			var w := 0.16 * f + 0.01
			var l := p + side * w
			var r := p - side * w
			var c := Color(col.r * f + f * f * 0.6, col.g * f + f * f * 0.6, col.b * f + f * f * 0.6, f)
			if i > 0:
				for v in [[prev_l, prev_c], [prev_r, prev_c], [l, c], [prev_r, prev_c], [r, c], [l, c]]:
					_trail.surface_set_color(v[1])
					_trail.surface_add_vertex(v[0])
			prev_l = l
			prev_r = r
			prev_c = c
	if any:
		_trail.surface_end()


func _process(delta: float) -> void:
	super._process(delta)
	var n := 0
	for i in _shards.size():
		var s: Dictionary = _shards[i]
		if s.is_empty():
			continue
		s["life"] -= delta
		if s["life"] <= 0.0:
			_shards[i] = {}
			_free.append(i)
			_mm.set_instance_transform(i, HIDDEN)
			continue
		var v: Vector3 = s["v"]
		v.y -= 15.0 * delta
		v *= 1.0 - 0.6 * delta
		s["v"] = v
		s["p"] += v * delta
		s["rot"] += s["spin"] * delta
		var k: float = s["life"] / s["max"]
		var sc: float = s["size"] * minf(1.0, k * 3.0)
		var b := Basis(s["axis"], s["rot"]).scaled(Vector3.ONE * sc)
		_mm.set_instance_transform(i, Transform3D(b, s["p"]))
		var c: Color = s["col"]
		_mm.set_instance_color(i, Color(c.r, c.g, c.b, k * k))
		n = i + 1
	_mm.visible_instance_count = n
	if n == 0 and _free.size() > 0:  # all gone: start the slots again from the front
		_shards.clear()
		_free.clear()
