class_name RidgeView3D
extends Node3D
## Ridgefire in 3D: the ground is a slab cut along the arena (its face shows strata), standing before a deep landscape
## that changes each round (RidgeBackdrop). Blasts bite it and the earth above slumps into the holes (the shown ground
## eases after the engine's). Tanks wear their player's colour, tilt with the ground, turn their barrels; shells trail
## smoke, the MIRV splits, rollers roll, blasts throw fire, smoke, clods and a shock ring, the nuke a mushroom cloud.
## Motes drift with the wind. The camera holds the whole arena, leans after the shots and shakes with the blasts.
## World: x 0..96 along the arena, y up, the battle plane at z = 0.

const R = preload("res://games/ridgefire/engine/ridge_engine.gd")
const M := "res://games/ridgefire/art/models/"
const BACKDROP := "res://games/ridgefire/view3d/ridge_backdrop.gd"
const TERRAIN_SHADER := preload("res://games/ridgefire/shaders/ridge_terrain.gdshader")
const FRONT := 3.0
const BACK := -5.0
const FLOOR := -12.0
## fallback ground colours per theme: top, soil, strata, deep
const GROUNDS := [
	[Color(0.85, 0.55, 0.32), Color(0.62, 0.3, 0.18), Color(0.8, 0.45, 0.28), Color(0.35, 0.18, 0.12)],
	[Color(0.35, 0.6, 0.25), Color(0.45, 0.32, 0.2), Color(0.58, 0.45, 0.3), Color(0.3, 0.28, 0.27)],
	[Color(0.62, 0.62, 0.64), Color(0.4, 0.4, 0.42), Color(0.52, 0.52, 0.55), Color(0.22, 0.22, 0.25)],
	[Color(0.22, 0.2, 0.2), Color(0.3, 0.2, 0.17), Color(0.45, 0.22, 0.12), Color(0.15, 0.1, 0.1)],
	[Color(0.9, 0.93, 0.98), Color(0.5, 0.55, 0.62), Color(0.65, 0.72, 0.8), Color(0.28, 0.3, 0.36)],
]

@export var game: RidgeGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _backdrop: Node3D
var _stage: Node3D
var _ground: MeshInstance3D
var _ground_mat: ShaderMaterial
var _shown := PackedFloat32Array()
var _settling := false
var _tanks: Array[Node3D] = []
var _shots := {}                 ## shot dictionary id -> {node, trail}
var _fx: Bursts
var _motes: CPUParticles3D
var _guide: MeshInstance3D
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _lean := Vector3.ZERO
var _rings: Array[Dictionary] = []
var _theme := -1
var _round := -1
var _flag: Node3D


func _ready() -> void:
	_we = WorldEnvironment.new()
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 160.0
	add_child(_sun)
	var key := DirectionalLight3D.new()   # a soft light on the play pieces only
	key.rotation_degrees = Vector3(-25, 20, 0)
	key.light_energy = 0.5
	key.light_cull_mask = 2
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 38
	camera.far = 3000.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 10.0
	add_child(_fx)
	_ground_mat = ShaderMaterial.new()
	_ground_mat.shader = TERRAIN_SHADER
	game.round_started.connect(_on_round)
	if game.engine:
		_on_round(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mat(col: Color, rough := 0.5, metal := 0.0, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	m.metallic = metal
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _box(size: Vector3, col: Color, at := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = _mat(col, 0.5, 0.3)
	mi.position = at
	return mi


func _play_layer(n: Node) -> void:
	for v in n.find_children("*", "VisualInstance3D", true, false):
		(v as VisualInstance3D).layers |= 2


# ------------------------------------------------------------------ a round

func _on_round(e: RidgeEngine) -> void:
	if not e.event.is_connected(_on_event):
		e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_shots.clear()
	_rings.clear()
	_theme = e.theme
	_round = e.round_i
	# the landscape and its light
	var cols: Array = GROUNDS[_theme % GROUNDS.size()]
	_backdrop = null
	if ResourceLoader.exists(BACKDROP):
		_backdrop = (load(BACKDROP) as GDScript).new()
		_stage.add_child(_backdrop)
		_backdrop.call("build", _theme)
		var d: Dictionary = _backdrop.call("environment_for", _theme)
		_env = _backdrop.call("make_environment", d)
		_backdrop.call("setup_sun", _sun, d)
		var t: Dictionary = d.get("terrain", {})
		if not t.is_empty():
			cols = [t.get("top", cols[0]), t.get("soil", cols[1]), t.get("strata", cols[2]), t.get("deep", cols[3])]
	else:
		_env = Environment.new()
		_env.background_mode = Environment.BG_COLOR
		_env.background_color = Color(0.45, 0.6, 0.85)
		_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		_env.ambient_light_color = Color(0.6, 0.65, 0.8)
		_env.ambient_light_energy = 0.6
		_env.tonemap_mode = Environment.TONE_MAPPER_ACES
		_env.glow_enabled = true
		_sun.rotation_degrees = Vector3(-40, -30, 0)
		_sun.light_energy = 1.2
	_env.ssao_enabled = true
	_we.environment = _env
	_ground_mat.set_shader_parameter("top_col", cols[0])
	_ground_mat.set_shader_parameter("soil_col", cols[1])
	_ground_mat.set_shader_parameter("strata_col", cols[2])
	_ground_mat.set_shader_parameter("deep_col", cols[3])
	_ground = MeshInstance3D.new()
	_ground.material_override = _ground_mat
	_stage.add_child(_ground)
	_shown = e.heights.duplicate()
	_build_ground()
	e.dirty = false
	# the tanks
	_tanks.clear()
	for p in e.players:
		var t := _tank(p)
		_stage.add_child(t)
		_tanks.append(t)
	# the aim guide: a short dotted line out of the muzzle
	_guide = MeshInstance3D.new()
	_guide.material_override = _mat(Color(1.0, 0.95, 0.7), 0.4, 0.0, 2.0)
	_guide.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage.add_child(_guide)
	_build_motes()
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


func _tank(p: Dictionary) -> Node3D:
	var root := Node3D.new()
	var body := _scene("tank")
	if body == null:
		body = Node3D.new()
		var hull := _box(Vector3(3.0, 0.8, 1.6), p["colour"], Vector3(0, 0.55, 0))
		hull.name = "hull"
		body.add_child(hull)
		var turret := Node3D.new()
		turret.name = "turret"
		turret.position = Vector3(0, 1.1, 0)
		body.add_child(turret)
		turret.add_child(_box(Vector3(1.2, 0.5, 1.1), p["colour"]))
		var barrel := Node3D.new()
		barrel.name = "barrel"
		turret.add_child(barrel)
		barrel.add_child(_box(Vector3(1.6, 0.16, 0.16), Color(0.25, 0.25, 0.27), Vector3(0.8, 0, 0)))
	else:
		_paint(body, p["colour"])
	body.name = "body"
	root.add_child(body)
	root.set_meta("colour", p["colour"])
	# a shield bubble, shown while it holds
	var sh := MeshInstance3D.new()
	var sm2 := SphereMesh.new()
	sm2.radius = 2.2
	sm2.height = 3.4
	sh.mesh = sm2
	var smat := _mat(Color(0.5, 0.85, 1.0, 0.15), 0.1, 0.0, 0.8)
	smat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	smat.rim_enabled = true
	smat.rim = 1.0
	smat.cull_mode = BaseMaterial3D.CULL_DISABLED
	sh.material_override = smat
	sh.position.y = 0.9
	sh.name = "shield"
	sh.visible = false
	root.add_child(sh)
	_play_layer(root)
	return root


## Recolours a model's player paint (and tints its pennant or flag cloth).
func _paint(n: Node, col: Color) -> void:
	var pm := _mat(col, 0.35, 0.35)
	pm.clearcoat_enabled = true
	pm.clearcoat = 0.6
	var cloth := _mat(col.lightened(0.25), 0.7)
	cloth.cull_mode = BaseMaterial3D.CULL_DISABLED
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for k in m.mesh.get_surface_count():
			var sm := m.mesh.surface_get_material(k)
			if sm == null:
				continue
			if sm.resource_name.contains("tank_paint"):
				m.set_surface_override_material(k, pm)
			elif sm.resource_name in ["tank_pennant", "flag_cloth"]:
				m.set_surface_override_material(k, cloth)


## The ground slab from the shown heights: the cut face at the front, the top running back, each vertex carrying its
## column's height (UV2.x) for the shader's crust.
func _build_ground() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := _shown.size()
	# the land runs on past both ends of the arena (the end columns' heights, easing down a little)
	var ext := 120
	for i in range(-ext, n - 1 + ext):
		var x0 := i * R.COL
		var x1 := (i + 1) * R.COL
		var h0 := _shown_at(i)
		var h1 := _shown_at(i + 1)
		var hm := maxf(h0, h1)
		# the face
		_quad(st, Vector3(x0, FLOOR, FRONT), Vector3(x1, FLOOR, FRONT), Vector3(x1, h1, FRONT), Vector3(x0, h0, FRONT), Vector3(0, 0, 1), h0, h1)
		# the top, with a rounded lip at the front
		var lip := 0.35
		_quad(st, Vector3(x0, h0 - 0.12, FRONT), Vector3(x1, h1 - 0.12, FRONT), Vector3(x1, h1, FRONT - lip), Vector3(x0, h0, FRONT - lip),
			Vector3(0, 0.7, 0.7).normalized(), hm, hm)
		_quad(st, Vector3(x0, h0, FRONT - lip), Vector3(x1, h1, FRONT - lip), Vector3(x1, h1, BACK), Vector3(x0, h0, BACK), Vector3.UP, hm, hm)
	# the ends
	st.generate_normals()
	_ground.mesh = st.commit()


func _shown_at(i: int) -> float:
	var n := _shown.size()
	if i < 0:
		return _shown[0] - sqrt(float(-i)) * 0.25
	if i >= n:
		return _shown[n - 1] - sqrt(float(i - n + 1)) * 0.25
	return _shown[i]


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, _nrm: Vector3, ha: float, hb: float) -> void:
	# clockwise as seen from the front (Godot's front faces)
	for v in [[a, ha], [c, hb], [b, hb], [a, ha], [d, ha], [c, hb]]:
		st.set_uv2(Vector2(v[1], 0))
		st.set_uv(Vector2((v[0] as Vector3).x * 0.1, (v[0] as Vector3).y * 0.1))
		st.add_vertex(v[0])


## Dust, snow, ash or sparks drifting with the wind across the arena.
func _build_motes() -> void:
	_motes = CPUParticles3D.new()
	_motes.amount = 160
	_motes.lifetime = 9.0
	_motes.preprocess = 9.0
	_motes.local_coords = false
	_motes.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_motes.emission_box_extents = Vector3(60, 25, 6)
	_motes.position = Vector3(48, 28, -2)
	_motes.direction = Vector3(1, 0, 0)
	_motes.spread = 30.0
	_motes.initial_velocity_min = 0.5
	_motes.initial_velocity_max = 1.5
	_motes.scale_amount_min = 0.5
	_motes.scale_amount_max = 1.0
	var q := QuadMesh.new()
	q.size = Vector2(0.12, 0.12) if _theme != 4 else Vector2(0.18, 0.18)
	_motes.mesh = q
	var col: Color = [Color(1.0, 0.85, 0.6, 0.5), Color(1.0, 1.0, 0.9, 0.4), Color(0.8, 0.85, 1.0, 0.3), Color(1.0, 0.5, 0.2, 0.8), Color(1, 1, 1, 0.8)][_theme % 5]
	_motes.material_override = Fx.material("glow" if _theme == 3 else "soft", col)
	_stage.add_child(_motes)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"fire":
			var p: Vector2 = d["pos"]
			var at := Vector3(p.x, p.y, 0)
			_fx.burst(at, Color(1.0, 0.75, 0.4), 18, 5.0, 0.3, 0.18, 1.0, -2.0, 0.3, "glow")
			_fx.burst(at, Color(0.8, 0.78, 0.75), 10, 2.0, 1.2, 0.6, 0.0, 1.0, 0.5, "smoke")
			_fx.flash(at, Color(1.0, 0.8, 0.5), 2.0)
			var t := _tanks[d["player"]]
			t.set_meta("recoil", 1.0)
			_shake = maxf(_shake, 0.25)
		"split":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y, 0), Color(1.0, 0.9, 0.5), 30, 6.0, 0.4, 0.15, 1.0, -3.0, 1.0, "glow")
			_fx.flash(Vector3(p.x, p.y, 0), Color(1.0, 0.85, 0.5), 3.0)
		"blast":
			_blast(d["pos"], d["radius"], d["weapon"])
		"dirt":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y, 0), _ground_col(), 50, 6.0, 0.9, 0.35, 0.0, -14.0, 1.0)
			_fx.burst(Vector3(p.x, p.y, 0), _ground_col().lightened(0.3), 16, 2.0, 1.6, 1.2, 0.0, 0.5, 1.0, "smoke")
			_shake = maxf(_shake, 0.4)
		"dig":
			var a: Vector2 = d["from"]
			var b: Vector2 = d["to"]
			for k in 5:
				var p := a.lerp(b, k / 4.0)
				_fx.burst(Vector3(p.x, p.y, 0.5), _ground_col(), 14, 3.0, 0.7, 0.25, 0.0, -10.0, 1.0)
			_shake = maxf(_shake, 0.3)
		"hit":
			var q := e.players[d["player"]]
			_fx.burst(Vector3(q["x"], q["y"] + 1.0, 0.4), Color(1.0, 0.85, 0.5), 16, 4.0, 0.4, 0.1, 1.0, -8.0, 1.0, "glow")
		"die":
			var q := e.players[d["player"]]
			_wreck(_tanks[d["player"]], Vector3(q["x"], q["y"], 0))
		"round_end":
			if d["winner"] >= 0:
				_punch = 3.0
				var q := e.players[d["winner"]]
				_punch_at = Vector3(q["x"], q["y"] + 1.0, 0)
				# the winner plants a flag in its colour beside it
				var flag := _scene("flag")
				if flag:
					_paint(flag, q["colour"])
					flag.position = Vector3(q["x"] - 2.2, _shown_ground(q["x"] - 2.2) - 2.6, -0.6)
					_stage.add_child(flag)
					create_tween().tween_property(flag, "position:y", _shown_ground(q["x"] - 2.2), 0.9).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
					_flag = flag


func _ground_col() -> Color:
	return (_ground_mat.get_shader_parameter("soil_col") as Color)


## Fire, smoke, clods and a shock ring; the nuke's is a white flash, a fireball and a mushroom of smoke.
func _blast(p: Vector2, r: float, weapon: String) -> void:
	var at := Vector3(p.x, p.y, 0.0)
	var nuke := weapon == "nuke"
	var k := r / 3.0
	_fx.burst(at, Color(1.0, 0.6, 0.2), int(30 * minf(k, 3.0)), 4.0 * k, 0.6, 0.5 * k, 1.0, -2.0, 1.0, "glow")
	_fx.burst(at, Color(1.0, 0.9, 0.6), int(14 * minf(k, 3.0)), 2.0 * k, 0.35, 0.7 * k, 1.0, 0.0, 1.0, "glow")
	_fx.burst(at + Vector3(0, r * 0.3, 0), Color(0.35, 0.32, 0.3), int(18 * minf(k, 3.0)), 1.6 * k, 2.2, 1.1 * k, 0.0, 1.2, 1.0, "smoke")
	_fx.burst(at, _ground_col(), int(40 * minf(k, 3.0)), 7.0 * minf(k, 2.0), 1.1, 0.22, 0.0, -16.0, 1.0)
	_fx.flash(at, Color(1.0, 0.7, 0.4), 4.0 * minf(k, 3.0))
	if _backdrop and _backdrop.has_method("flash"):
		_backdrop.call("flash", at, 3.0 * k)
	if _backdrop and _backdrop.has_method("shake") and r >= 4.0:
		_backdrop.call("shake", clampf(r / 8.0, 0.3, 1.5))
	_ring(at, r * 2.2, 0.5 if not nuke else 1.2)
	_shake = maxf(_shake, clampf(0.35 * k, 0.3, 1.6))
	if nuke:
		_fx.flash(at + Vector3(0, 6, 4), Color(1, 1, 0.95), 14.0)
		for h in 5:
			_fx.burst(at + Vector3(0, 3.0 + h * 3.0, 0), Color(0.45, 0.38, 0.33), 16, 1.0, 4.5, 3.0 - h * 0.2, 0.0, 2.5, 1.0, "smoke")
		_fx.burst(at + Vector3(0, 16.0, 0), Color(1.0, 0.5, 0.2), 40, 4.0, 2.0, 2.2, 1.0, 1.0, 1.0, "glow")
		_fx.burst(at + Vector3(0, 17.0, 0), Color(0.5, 0.42, 0.36), 30, 3.5, 5.0, 3.5, 0.0, 0.8, 1.0, "smoke")
		_punch = 1.5
		_punch_at = at + Vector3(0, 8, 0)


## A ring of light and dust racing out from a blast.
func _ring(at: Vector3, size: float, life: float) -> void:
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.92
	tm.outer_radius = 1.0
	tm.rings = 48
	mi.mesh = tm
	mi.rotation.x = PI * 0.5
	var m := _mat(Color(1.0, 0.85, 0.6, 0.8), 0.5, 0.0, 3.0)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = m
	mi.position = at + Vector3(0, 0, 0.6)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage.add_child(mi)
	_rings.append({"node": mi, "t": 0.0, "life": life, "size": size, "mat": m})


## A destroyed tank: it bursts, its bits fly, a column of smoke stays.
func _wreck(t: Node3D, at: Vector3) -> void:
	var body := t.get_node("body") as Node3D
	var bits := _scene("wreck_bits")
	if bits:
		_paint(bits, (t.get_meta("colour", Color.GRAY) as Color).darkened(0.45))
		bits.position = at
		_stage.add_child(bits)
		for b in bits.get_children():
			var n := b as Node3D
			if n == null:
				continue
			var v := Vector3(randf_range(-6, 6), randf_range(6, 12), randf_range(-1, 3))
			var tw := create_tween().set_parallel()
			tw.tween_method(func(tt: float): n.position = v * tt + Vector3(0, -10.0 * tt * tt, 0); n.rotation = v * tt * 0.6, 0.0, 1.4, 1.4)
	body.visible = false
	var smoke := CPUParticles3D.new()
	smoke.amount = 30
	smoke.lifetime = 4.0
	smoke.direction = Vector3.UP
	smoke.spread = 12.0
	smoke.initial_velocity_min = 1.5
	smoke.initial_velocity_max = 2.5
	smoke.gravity = Vector3(0, 0.4, 0)
	smoke.scale_amount_min = 1.0
	smoke.scale_amount_max = 2.5
	var q := QuadMesh.new()
	q.size = Vector2(1.2, 1.2)
	smoke.mesh = q
	smoke.material_override = Fx.material("smoke", Color(0.2, 0.19, 0.18, 0.7))
	smoke.position = at + Vector3(0, 0.8, 0)
	smoke.local_coords = false
	_stage.add_child(smoke)
	var fire := CPUParticles3D.new()
	fire.amount = 24
	fire.lifetime = 0.8
	fire.direction = Vector3.UP
	fire.initial_velocity_min = 1.0
	fire.initial_velocity_max = 2.0
	fire.scale_amount_min = 0.4
	fire.scale_amount_max = 0.9
	var fq := QuadMesh.new()
	fq.size = Vector2(0.6, 0.6)
	fire.mesh = fq
	fire.material_override = Fx.material("glow", Color(1.0, 0.5, 0.15))
	fire.position = at + Vector3(0, 0.6, 0.3)
	_stage.add_child(fire)


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 1.4)
	_punch = maxf(0.0, _punch - delta)
	var e := game.engine
	if e == null or _stage == null:
		return
	if e.round_i != _round:
		return   # the next round's stage is on its way
	_settle_ground(e, delta)
	_place_tanks(e, delta)
	_place_shots(e)
	_place_guide(e)
	for r in _rings:
		r["t"] += delta
		var k: float = r["t"] / r["life"]
		(r["node"] as Node3D).scale = Vector3.ONE * lerpf(0.3, r["size"], 1.0 - pow(1.0 - minf(k, 1.0), 3.0))
		(r["mat"] as StandardMaterial3D).albedo_color.a = 0.8 * (1.0 - k)
	for r in _rings.filter(func(r): return r["t"] > r["life"]):
		(r["node"] as Node3D).queue_free()
	_rings = _rings.filter(func(r): return r["t"] <= r["life"])
	if _flag and is_instance_valid(_flag):
		var cloth := _flag.find_child("cloth", true, false) as Node3D
		if cloth:
			cloth.rotation.y = sin(_time * 4.0) * 0.25
	if _motes:
		_motes.gravity = Vector3(e.wind * 0.6, -0.15 if _theme != 3 else 0.3, 0)
	_place_camera(delta)


## The shown ground slumps after the engine's: each column eases down (or up) to its new height.
func _settle_ground(e: RidgeEngine, delta: float) -> void:
	if e.dirty:
		e.dirty = false
		_settling = true
	if not _settling:
		return
	var moving := false
	for i in _shown.size():
		var to := e.heights[i]
		var h := _shown[i]
		if absf(to - h) > 0.01:
			_shown[i] = move_toward(h, to, delta * (18.0 + absf(to - h) * 4.0))
			moving = true
	_build_ground()
	_settling = moving


func _place_tanks(e: RidgeEngine, delta: float) -> void:
	for i in e.players.size():
		var p := e.players[i]
		var t := _tanks[i]
		var x: float = p["x"]
		var y: float = p["y"] if e.phase != R.Phase.SETTLE or p["falling"] else _shown_ground(x)
		t.position = Vector3(x, minf(y, maxf(y, _shown_ground(x))), 0)
		var slope := (_shown_ground(x + 1.2) - _shown_ground(x - 1.2)) / 2.4
		var body := t.get_node("body") as Node3D
		var left: bool = p["angle"] > 90.0
		body.rotation = Vector3(0, PI if left else 0.0, atan(slope) * (-1.0 if left else 1.0))
		var barrel := body.find_child("barrel", true, false) as Node3D
		if barrel:
			var a: float = p["angle"] if not left else 180.0 - p["angle"]
			barrel.rotation.z = deg_to_rad(a) - body.rotation.z
			if not barrel.has_meta("rest"):
				barrel.set_meta("rest", barrel.position)
			var rc: float = t.get_meta("recoil", 0.0)
			t.set_meta("recoil", maxf(0.0, rc - delta * 3.0))
			barrel.position = barrel.get_meta("rest") - Vector3(0.25 * sin(rc * PI), 0, 0)
		var pennant := body.find_child("pennant", true, false) as Node3D
		if pennant:
			pennant.rotation.y = sin(_time * 3.0 + i) * 0.35 + (0.4 if not left else -0.4) * clampf(e.wind / 8.0, -1.0, 1.0)
		var sh := t.get_node("shield") as MeshInstance3D
		sh.visible = float(p["shield"]) > 0.0 and p["alive"]
		sh.scale = Vector3.ONE * (1.0 + 0.03 * sin(_time * 3.0 + i))


func _shown_ground(x: float) -> float:
	var f := clampf(x / R.COL, 0.0, _shown.size() - 1.0)
	var i := int(floorf(f))
	return lerpf(_shown[i], _shown[mini(i + 1, _shown.size() - 1)], f - i)


## Each shot in the air: its model along its flight, a trail of smoke; gone shots leave their trail to fade.
func _place_shots(e: RidgeEngine) -> void:
	var live := {}
	for s in e.shots:
		var id := int(s.get("id", 0))
		if id == 0:
			s["id"] = randi() % 1000000 + 1
			id = s["id"]
		live[id] = true
		if not _shots.has(id):
			_shots[id] = _shot_node(s["weapon"])
		var n: Node3D = _shots[id]["node"]
		var p: Vector2 = s["pos"]
		n.position = Vector3(p.x, p.y, 0)
		var v: Vector2 = s["vel"]
		if s["rolling"]:
			n.position.y += 0.35
			n.rotation.z -= v.x * 0.05
		elif v.length() > 0.1:
			n.rotation.z = atan2(v.y, v.x)
		var tr: CPUParticles3D = _shots[id]["trail"]
		tr.position = n.position
	for id in _shots.keys():
		if not live.has(id):
			var d: Dictionary = _shots[id]
			(d["node"] as Node3D).queue_free()
			var tr: CPUParticles3D = d["trail"]
			tr.emitting = false
			get_tree().create_timer(2.0).timeout.connect(tr.queue_free)
			_shots.erase(id)


func _shot_node(weapon: String) -> Dictionary:
	var model: String = {"shell": "shell", "heavy": "shell", "mirv": "missile", "roller": "roller", "dirt": "shell", "digger": "digger", "nuke": "nuke"}.get(weapon, "shell")
	var n := _scene(model)
	if n == null:
		n = MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.25
		sm.height = 0.5
		(n as MeshInstance3D).mesh = sm
		(n as MeshInstance3D).material_override = _mat(Color(0.3, 0.3, 0.32), 0.3, 0.8)
	if weapon == "heavy":
		n.scale = Vector3.ONE * 1.4
	elif weapon == "dirt":
		n.scale = Vector3.ONE * 1.3
	_play_layer(n)
	_stage.add_child(n)
	var tr := CPUParticles3D.new()
	tr.amount = 60
	tr.lifetime = 1.2
	tr.local_coords = false
	tr.direction = Vector3.UP
	tr.spread = 180.0
	tr.initial_velocity_min = 0.1
	tr.initial_velocity_max = 0.4
	tr.gravity = Vector3(0, 0.3, 0)
	tr.scale_amount_min = 0.6
	tr.scale_amount_max = 1.2
	var q := QuadMesh.new()
	q.size = Vector2(0.45, 0.45)
	tr.mesh = q
	var hot := weapon in ["nuke", "mirv"]
	tr.material_override = Fx.material("glow" if hot else "smoke", Color(1.0, 0.6, 0.25, 0.8) if hot else Color(0.85, 0.83, 0.8, 0.55))
	_stage.add_child(tr)
	return {"node": n, "trail": tr}


## The aim guide: a dotted line out of the muzzle, as long as the power, for a player's turn.
func _place_guide(e: RidgeEngine) -> void:
	var show: bool = e.phase == R.Phase.AIM and not e.current()["cpu"]
	_guide.visible = show
	if not show:
		return
	var p := e.current()
	var m := e.muzzle(p)
	var a := deg_to_rad(float(p["angle"]))
	var dir := Vector2(cos(a), sin(a))
	var len := 1.5 + float(p["power"]) / 100.0 * 6.0
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var side := Vector2(-dir.y, dir.x) * 0.07
	var k := 0.0
	while k < len:
		var a0 := m + dir * k
		var a1 := m + dir * minf(k + 0.35, len)
		for v in [a0 - side, a1 - side, a1 + side, a0 - side, a1 + side, a0 + side]:
			st.add_vertex(Vector3(v.x, v.y, 0.3))
		k += 0.6
	_guide.mesh = st.commit()


func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_v := tan(deg_to_rad(camera.fov * 0.5))
	var dist := maxf(27.0 / half_v, 53.0 / (half_v * aspect))
	var look := Vector3(48.0, 20.0, 0.0)
	var lean := Vector3.ZERO
	if e and not e.shots.is_empty():
		var p: Vector2 = e.shots[0]["pos"]
		lean = (Vector3(p.x, clampf(p.y, 0.0, 45.0), 0) - look) * 0.12
	elif e and e.phase == R.Phase.AIM:
		var p := e.current()
		lean = (Vector3(p["x"], p["y"], 0) - look) * 0.08
	_lean = _lean.lerp(lean, minf(1.0, delta * 1.2))
	look += _lean
	var pos := look + Vector3(sin(_time * 0.07) * 2.0, 6.0 + sin(_time * 0.05) * 1.0, dist)
	if _punch > 0.0:
		var k := minf(1.0, sin(minf(_punch, 1.0) * PI * 0.5)) * 0.3
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + Vector3(0, 5, dist * 0.55), k)
	var j := Vector3(sin(_time * 43.0), cos(_time * 37.0), 0) * _shake * _shake * (0.9 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 2.5)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
