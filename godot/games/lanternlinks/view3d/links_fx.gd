class_name LinksFx
extends Bursts
## Lantern Links effects on top of the shared Bursts: confetti that tumbles and flutters down, fireworks (a glowing
## rocket with a trail, then a burst in two colours and a flash) and expanding rings on the felt or the water.

const CONFETTI := 140
const RINGS := 8

var _confetti: Array[Dictionary] = []   ## {node, vel, spin, age, life}
var _next_c := 0
var _rings: Array[Dictionary] = []      ## {node, mat, age, life, size}
var _next_r := 0
var _rockets: Array[Dictionary] = []    ## {pos, vel, fuse, cols}
var _paper := {}


func _ready() -> void:
	super._ready()
	var q := QuadMesh.new()
	q.size = Vector2(0.035, 0.022)
	for i in CONFETTI:
		var mi := MeshInstance3D.new()
		mi.mesh = q
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_confetti.append({"node": mi, "vel": Vector3.ZERO, "spin": Vector3.ZERO, "age": 1.0, "life": 0.0})
	var disc := QuadMesh.new()
	disc.size = Vector2(2, 2)
	disc.orientation = PlaneMesh.FACE_Y
	for i in RINGS:
		var mi2 := MeshInstance3D.new()
		mi2.mesh = disc
		var m := ShaderMaterial.new()
		m.shader = _ring_shader()
		mi2.material_override = m
		mi2.visible = false
		mi2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi2)
		_rings.append({"node": mi2, "mat": m, "age": 1.0, "life": 0.0, "size": 1.0})


static var _ring_sh: Shader


static func _ring_shader() -> Shader:
	if _ring_sh == null:
		_ring_sh = Shader.new()
		_ring_sh.code = """shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, shadows_disabled, depth_draw_never;
uniform vec4 col : source_color = vec4(1.0);
uniform float k = 0.0;
void fragment() {
	float r = length(UV - 0.5) * 2.0;
	float w = 0.06 + 0.1 * (1.0 - k);
	float ring = smoothstep(k - w, k, r) * smoothstep(k + w * 0.4, k, r);
	ALBEDO = col.rgb * ring * (1.0 - k) * col.a * 2.0;
}"""
	return _ring_sh


func _paper_mat(c: Color) -> StandardMaterial3D:
	var key := c.to_html()
	if not _paper.has(key):
		var m := StandardMaterial3D.new()
		m.albedo_color = c
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.roughness = 0.4
		m.metallic = 0.3
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = 0.4
		_paper[key] = m
	return _paper[key]


func confetti(pos: Vector3, amount: int, spread := 1.0) -> void:
	var cols := [Color(1.0, 0.3, 0.35), Color(1.0, 0.85, 0.25), Color(0.35, 0.8, 1.0), Color(0.5, 1.0, 0.5), Color(1.0, 0.55, 0.9), Color(1, 1, 1)]
	for i in amount:
		var c: Dictionary = _confetti[_next_c]
		_next_c = (_next_c + 1) % CONFETTI
		var mi: MeshInstance3D = c["node"]
		mi.material_override = _paper_mat(cols[randi() % cols.size()])
		mi.position = pos + Vector3(randf_range(-0.1, 0.1), 0.05, randf_range(-0.1, 0.1))
		mi.visible = true
		c["vel"] = Vector3(randf_range(-1.6, 1.6) * spread, randf_range(2.5, 4.5), randf_range(-1.6, 1.6) * spread)
		c["spin"] = Vector3(randf_range(-12, 12), randf_range(-12, 12), randf_range(-12, 12))
		c["age"] = 0.0
		c["life"] = randf_range(2.2, 3.4)


func ring(pos: Vector3, col: Color, size: float, life: float) -> void:
	var r: Dictionary = _rings[_next_r]
	_next_r = (_next_r + 1) % RINGS
	var mi: MeshInstance3D = r["node"]
	mi.position = pos
	mi.scale = Vector3.ONE * size * 0.2
	mi.visible = true
	(r["mat"] as ShaderMaterial).set_shader_parameter("col", col)
	(r["mat"] as ShaderMaterial).set_shader_parameter("k", 0.0)
	r["age"] = 0.0
	r["life"] = life
	r["size"] = size


## A rocket from `from`, bursting `height` up after `fuse` seconds.
func firework(from: Vector3, height: float, fuse: float, drift := Vector3.ZERO) -> void:
	var palette := [[Color(1.0, 0.45, 0.3), Color(1.0, 0.85, 0.4)], [Color(0.4, 0.8, 1.0), Color(0.9, 0.95, 1.0)],
		[Color(0.7, 1.0, 0.4), Color(1.0, 0.95, 0.5)], [Color(1.0, 0.5, 0.9), Color(0.6, 0.6, 1.0)]]
	_rockets.append({"pos": from, "vel": Vector3(0, height / fuse + 4.9 * fuse, 0) + drift, "fuse": fuse,
		"cols": palette[randi() % palette.size()], "trail": 0.0})


## Makes the burst just fired spread all round (a firework's sphere), not in the usual upward cone.
func _round() -> void:
	_pool[(_next - 1 + _pool.size()) % _pool.size()].spread = 180.0


func burst(pos: Vector3, color: Color, amount: int, speed: float, life: float, size: float, glow: float, gravity: float,
		up: float = 1.0, kind: String = "") -> void:
	super.burst(pos, color, amount, speed, life, size, glow, gravity, up, kind)
	# on a mini-golf scale the sprite itself must be small: size it directly (the pool's quads are 0.4 m)
	var p := _pool[(_next - 1 + _pool.size()) % _pool.size()]
	p.spread = 70.0
	(p.mesh as QuadMesh).size = Vector2.ONE * size * 2.0
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.0


func _process(delta: float) -> void:
	super._process(delta)
	for c in _confetti:
		if c["age"] >= c["life"]:
			continue
		c["age"] += delta
		var mi: MeshInstance3D = c["node"]
		var v: Vector3 = c["vel"]
		v.y -= 6.0 * delta
		v *= 1.0 - minf(1.0, delta * 2.2)   # paper drag: it flutters down
		v.x += sin(c["age"] * 7.0 + mi.position.z * 3.0) * delta * 0.8
		c["vel"] = v
		mi.position += v * delta
		mi.rotation += (c["spin"] as Vector3) * delta
		if c["age"] >= c["life"]:
			mi.visible = false
	for r in _rings:
		if r["age"] >= r["life"]:
			continue
		r["age"] += delta
		var k: float = r["age"] / r["life"]
		var mi2: MeshInstance3D = r["node"]
		mi2.scale = Vector3.ONE * float(r["size"]) * (0.2 + 0.8 * k)
		(r["mat"] as ShaderMaterial).set_shader_parameter("k", k)
		if k >= 1.0:
			mi2.visible = false
	var keep: Array[Dictionary] = []
	for f in _rockets:
		f["fuse"] -= delta
		var v2: Vector3 = f["vel"]
		v2.y -= 9.8 * delta
		f["vel"] = v2
		f["pos"] += v2 * delta
		f["trail"] += delta
		if f["trail"] > 0.04:
			f["trail"] = 0.0
			burst(f["pos"], Color(1.0, 0.8, 0.5), 3, 0.3, 0.5, 0.05, 1.0, -1.0, 1.0, "glow")
		if f["fuse"] <= 0.0:
			var cols: Array = f["cols"]
			burst(f["pos"], cols[0], 70, 5.0, 1.4, 0.12, 1.0, -2.5, 1.0, "glow")
			_round()
			burst(f["pos"], cols[1], 40, 3.2, 1.8, 0.09, 1.0, -1.5, 1.0, "glow")
			_round()
			flash(f["pos"] - Vector3(0, 2.0, 0), cols[0], 5.0)
		else:
			keep.append(f)
	_rockets = keep
