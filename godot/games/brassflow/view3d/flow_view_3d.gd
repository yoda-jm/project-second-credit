class_name FlowView3D
extends Node3D
## Brassflow in 3D: the board lies on a workbench in a steam workshop at night (BrassWorkshop: brick, gears, lamps,
## the moon through arched windows). Pieces are brass pipes with glass windows; each one flies from the dispenser to
## its cell and lands with a bounce, a scrapped one is flung away in sparks. The glow runs through the glass (a tube
## revealed along the pipe, pulses travelling with it) carrying a light that warms the brass as it goes. A leak
## splashes and hisses; a finished pipeline lights up end to end. The camera looks down over the bench, leans toward
## the glow's head, punches in on loops and leaks, and swings round for a finished pipeline.
## World: cell (col, row) is centred at (col + 0.5, 0, row + 0.5), the board top at y = 0.

const F = preload("res://games/brassflow/engine/flow_engine.gd")
const M := "res://games/brassflow/art/models/"
const WORKSHOP := "res://games/brassflow/view3d/brass_workshop.gd"
const GLOW_SHADER := preload("res://games/brassflow/shaders/flow_glow.gdshader")
const GLOW := Color(0.16, 1.0, 0.55)
const BRASS := Color(0.85, 0.62, 0.3)
const COPPER := Color(0.78, 0.42, 0.26)
const IRON := Color(0.16, 0.15, 0.15)
const DISPENSER_X := -1.4
const DISPENSER_Z := 3.5
const SLOT0_Z := 5.5
const SLOT_STEP := 1.0
## base orientations of the models: the straight runs left-right, the corner opens up and right
const BASE := {"h": [1, 3], "v": [1, 3], "ne": [0, 1], "nw": [0, 1], "se": [0, 1], "sw": [0, 1], "x": [0, 1, 2, 3]}
const RINGS := 18
const SIDES := 12

@export var game: FlowGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _moon: DirectionalLight3D
var _shop: Node3D
var _board: Node3D
var _fx: Bursts
var _pieces := {}            ## cell -> {node, piece, t}
var _glows := {}             ## "x,y,enter" -> MeshInstance3D
var _queue: Array[Dictionary] = []   ## {node, piece}
var _cursor: Node3D
var _ghost: Node3D
var _ghost_piece := ""
var _cursor_pos := Vector3.ZERO
var _source: Node3D
var _head_light: OmniLight3D
var _glow_mat: ShaderMaterial
var _tube_line: ArrayMesh
var _tube_arc: ArrayMesh
var _tube_arc_rev: ArrayMesh
var _glow_y := 0.22
var _glow_r := 0.085
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _sweep := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _lean := Vector3.ZERO
var _celebrate := 0.0
var _flung: Array[Dictionary] = []
var _feed_gear: Node3D
var _feed_spin := 0.0
var _cogs: Array = []          ## [node, rad/s]
var _tank: Node3D
var _outlet: GeometryInstance3D
var _cursor_mats: Array = []   ## [mesh, surface] of the cursor's glowing parts


func _ready() -> void:
	_we = WorldEnvironment.new()
	add_child(_we)
	_moon = DirectionalLight3D.new()
	_moon.shadow_enabled = true
	_moon.directional_shadow_max_distance = 40.0
	add_child(_moon)
	camera = Camera3D.new()
	camera.fov = 36
	camera.far = 400.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 26.0   # this game's sizes: bursts about 0.3 m across
	add_child(_fx)
	_glow_mat = ShaderMaterial.new()
	_glow_mat.shader = GLOW_SHADER
	_glow_mat.set_shader_parameter("colour", GLOW)
	_head_light = OmniLight3D.new()
	_head_light.light_color = GLOW
	_head_light.omni_range = 2.6
	_head_light.light_energy = 0.0
	_head_light.shadow_enabled = false
	add_child(_head_light)
	_build_shop()
	_measure_glow()
	_tube_line = _tube(func(t: float) -> Vector3: return Vector3(-0.5 + t, 0, 0))
	_tube_arc = _tube(func(t: float) -> Vector3:
		var a := lerpf(PI, PI * 0.5, t)
		return Vector3(0.5 + 0.5 * cos(a), 0, -0.5 + 0.5 * sin(a)))
	_tube_arc_rev = _tube(func(t: float) -> Vector3:
		var a := lerpf(PI * 0.5, PI, t)
		return Vector3(0.5 + 0.5 * cos(a), 0, -0.5 + 0.5 * sin(a)))
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


# ------------------------------------------------------------------ the workshop

func _build_shop() -> void:
	if ResourceLoader.exists(WORKSHOP):
		_shop = (load(WORKSHOP) as GDScript).new()
		add_child(_shop)
		_shop.call("build")
		var d: Dictionary = _shop.call("environment")
		_env = _shop.call("make_environment", d)
		_shop.call("setup_sun", _moon, d)
	else:
		_env = Environment.new()
		_env.background_mode = Environment.BG_COLOR
		_env.background_color = Color(0.05, 0.04, 0.035)
		_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		_env.ambient_light_color = Color(0.55, 0.42, 0.3)
		_env.ambient_light_energy = 0.6
		_env.tonemap_mode = Environment.TONE_MAPPER_ACES
		_env.glow_enabled = true
		_env.glow_intensity = 0.8
		_env.glow_hdr_threshold = 1.0
		_env.ssao_enabled = true
		_moon.rotation_degrees = Vector3(-55, -35, 0)
		_moon.light_color = Color(1.0, 0.82, 0.6)
		_moon.light_energy = 1.0
		var bench := _box(Vector3(16, 0.8, 11), Color(0.35, 0.22, 0.13), 0.7)
		bench.position = Vector3(4.3, -0.55, 3.5)
		add_child(bench)
		var lamp := OmniLight3D.new()  # a warm lamp over the bench
		lamp.light_color = Color(1.0, 0.78, 0.5)
		lamp.light_energy = 1.4
		lamp.omni_range = 14.0
		lamp.shadow_enabled = true
		lamp.position = Vector3(4.5, 5.5, 3.0)
		add_child(lamp)
	_we.environment = _env


## The glow tube sits where the models' own glow_path is (its height and thickness), else at a default.
func _measure_glow() -> void:
	var n := _model("pipe_straight")
	if n == null:
		return
	var gp := n.find_child("glow_path", true, false) as MeshInstance3D
	if gp and gp.mesh:
		var bb := gp.mesh.get_aabb()
		var xf := _xform_to(gp, n)
		var c := xf * bb.get_center()
		_glow_y = c.y
		_glow_r = clampf(minf(bb.size.y, bb.size.z) * 0.5 * xf.basis.get_scale().y, 0.03, 0.2)
	n.free()


func _xform_to(node: Node3D, root: Node3D) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var p: Node = node
	while p and p != root:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf


## A tube following a curve (t 0..1 -> cell-local point at the glow's height), UV.x = t.
func _tube(curve: Callable) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings: Array = []
	for i in RINGS + 1:
		var t := float(i) / RINGS
		var p: Vector3 = curve.call(t)
		var q: Vector3 = curve.call(minf(1.0, t + 0.01)) if t < 1.0 else p + (p - curve.call(t - 0.01))
		var tan := (q - p).normalized()
		var side := tan.cross(Vector3.UP).normalized()
		var ring: Array = []
		for j in SIDES + 1:
			var a := TAU * j / SIDES
			var n := side * cos(a) + Vector3.UP * sin(a)
			ring.append([p + Vector3(0, _glow_y, 0) + n * _glow_r, n, Vector2(t, float(j) / SIDES)])
		rings.append(ring)
	for i in RINGS:
		for j in SIDES:
			var quad := [rings[i][j], rings[i + 1][j], rings[i + 1][j + 1], rings[i][j], rings[i + 1][j + 1], rings[i][j + 1]]
			for v in quad:
				st.set_normal(v[1])
				st.set_uv(v[2])
				st.add_vertex(v[0])
	return st.commit()


# ------------------------------------------------------------------ models

func _model(name: String) -> Node3D:
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


func _box(size: Vector3, col: Color, rough := 0.6, metal := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = _mat(col, rough, metal)
	return mi


func _cyl(r: float, h: float, col: Color, rough := 0.3, metal := 0.9) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = r
	c.bottom_radius = r
	c.height = h
	mi.mesh = c
	mi.material_override = _mat(col, rough, metal)
	return mi


## The steps of 90° (about Y, counter-clockwise from above) that turn a base model's openings into a piece's.
static func turns(piece: String) -> int:
	var want: Array = F.PIECES[piece]
	var base: Array = BASE[piece]
	for k in 4:
		var ok := true
		for o in base:
			if not want.has(posmod(o - k, 4)):
				ok = false
		if ok:
			return k
	return 0


func _piece_node(piece: String) -> Node3D:
	var model := "pipe_cross" if piece == "x" else ("pipe_straight" if piece in ["h", "v"] else "pipe_corner")
	var root := Node3D.new()
	var n := _model(model)
	if n == null:
		n = _fallback_piece(piece)
	else:
		for gn in ["glow_path", "glow_path_v"]:
			var gp := n.find_child(gn, true, false) as GeometryInstance3D
			if gp:
				gp.material_override = _glow_mat
				gp.set_instance_shader_parameter("fill", 0.0)
				gp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				root.set_meta(gn, gp)
		n.rotation.y = turns(piece) * PI * 0.5
	root.add_child(n)
	return root


## A stand-in until the models exist: a riveted iron tile and glass pipes with brass flanges.
func _fallback_piece(piece: String) -> Node3D:
	var n := Node3D.new()
	var tile := _box(Vector3(0.94, 0.08, 0.94), IRON, 0.5, 0.6)
	tile.position.y = 0.04
	n.add_child(tile)
	var glass := _mat(Color(0.7, 0.9, 1.0, 0.25), 0.05)
	glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	for o in F.PIECES[piece]:
		var d: Vector2i = F.DIRS[o]
		var arm := _cyl(0.16, 0.5, BRASS)
		arm.material_override = glass
		arm.rotation = Vector3(PI * 0.5, 0, 0) if d.x == 0 else Vector3(0, 0, PI * 0.5)
		arm.position = Vector3(d.x * 0.25, _glow_y, d.y * 0.25)
		n.add_child(arm)
		var fl := _cyl(0.2, 0.06, BRASS, 0.25, 1.0)
		fl.rotation = arm.rotation
		fl.position = Vector3(d.x * 0.46, _glow_y, d.y * 0.46)
		n.add_child(fl)
	var hub := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.19
	s.height = 0.38
	hub.mesh = s
	hub.material_override = _mat(COPPER, 0.25, 1.0)
	hub.position.y = _glow_y
	if piece != "x" and piece not in ["h", "v"]:
		n.add_child(hub)
	return n


func _cell_pos(c: Vector2i) -> Vector3:
	return Vector3(c.x + 0.5, 0.0, c.y + 0.5)


func _slot_pos(i: int) -> Vector3:
	return Vector3(DISPENSER_X, 0.0, SLOT0_Z - i * SLOT_STEP)


# ------------------------------------------------------------------ a level

func _on_level(e: FlowEngine) -> void:
	e.event.connect(_on_event)
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_pieces.clear()
	_glows.clear()
	_queue.clear()
	_celebrate = 0.0
	_head_light.light_energy = 0.0
	# the board: the workshop has its own bed, grid and frame; else an inset grid of tiles in a brass frame
	if _shop == null:
		_fallback_board()
	_build_level(e)


func _fallback_board() -> void:
	var frame := _box(Vector3(F.COLS + 0.4, 0.12, F.ROWS + 0.4), BRASS, 0.3, 1.0)
	frame.position = Vector3(F.COLS * 0.5, -0.07, F.ROWS * 0.5)
	_board.add_child(frame)
	for x in F.COLS:
		for y in F.ROWS:
			var t := _box(Vector3(0.96, 0.04, 0.96), Color(0.2, 0.17, 0.15) if (x + y) % 2 == 0 else Color(0.24, 0.2, 0.17), 0.65, 0.35)
			t.position = Vector3(x + 0.5, -0.01, y + 0.5)
			_board.add_child(t)


func _build_level(e: FlowEngine) -> void:
	# the dispenser
	var disp := _model("dispenser")
	if disp == null:
		disp = _box(Vector3(1.3, 0.2, SLOT_STEP * 5 + 0.3), COPPER, 0.35, 1.0)
		disp.position.y = -0.1
	disp.position += Vector3(DISPENSER_X, 0, DISPENSER_Z)
	_board.add_child(disp)
	_feed_gear = disp.find_child("feed_gear", true, false) as Node3D
	_cogs.clear()
	for i in e.queue.size():
		_push_queue(e.queue[i], i, false)
	# blocks
	for c in e.blocked:
		var b := _model("block")
		if b == null:
			b = _box(Vector3(0.9, 0.3, 0.9), IRON, 0.45, 0.8)
			b.position.y = 0.15
		var holder := Node3D.new()
		holder.position = _cell_pos(c)
		holder.rotation.y = (c.x * 7 + c.y * 3) % 4 * PI * 0.5
		holder.add_child(b)
		_board.add_child(holder)
		for cn in ["cog", "cog_small"]:
			var cog := b.find_child(cn, true, false) as Node3D
			if cog:
				_cogs.append([cog, 1.2 if cn == "cog" else -1.2 * 16.0 / 7.0])
	# the source
	_source = _model("source")
	if _source == null:
		_source = Node3D.new()
		var tank := _cyl(0.35, 1.0, BRASS)
		tank.position.y = 0.5
		_source.add_child(tank)
		var g := _cyl(0.28, 0.8, GLOW, 0.2, 0.0)
		g.material_override = _mat(GLOW, 0.2, 0.0, 2.5)
		g.position.y = 0.55
		g.scale = Vector3(1.05, 1, 1.05)
		_source.add_child(g)
		var spout := _cyl(0.14, 0.5, COPPER)
		spout.rotation.z = PI * 0.5
		spout.position = Vector3(0.3, _glow_y, 0)
		_source.add_child(spout)
	var sh := Node3D.new()
	sh.position = _cell_pos(e.source)
	sh.rotation.y = posmod(1 - e.source_dir, 4) * PI * 0.5
	sh.add_child(_source)
	_board.add_child(sh)
	_tank = _source.find_child("tank_glow", true, false) as Node3D
	_outlet = _source.find_child("outlet_glow", true, false) as GeometryInstance3D
	if _outlet:
		_outlet.material_override = _glow_mat
		_outlet.set_instance_shader_parameter("fill", 0.0)
	# the cursor
	_cursor = _model("cursor")
	if _cursor == null:
		_cursor = Node3D.new()
		for s in 4:
			var bar := _box(Vector3(1.0, 0.06, 0.08), BRASS, 0.3, 1.0)
			bar.rotation.y = s * PI * 0.5
			bar.position = Vector3(0.48 * sin(s * PI * 0.5), 0.05, 0.48 * cos(s * PI * 0.5))
			_cursor.add_child(bar)
	_board.add_child(_cursor)
	_cursor_pos = _cell_pos(e.cursor)
	_ghost = null
	_ghost_piece = ""
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


func _push_queue(piece: String, slot: int, drop: bool) -> void:
	var n := _piece_node(piece)
	n.scale = Vector3.ONE * 0.8
	n.position = _slot_pos(slot) + (Vector3(0, 2.5, -1.5) if drop else Vector3.ZERO)
	_board.add_child(n)
	_queue.append({"node": n, "piece": piece})


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"place":
			var c: Vector2i = d["cell"]
			if _pieces.has(c):
				_fling(_pieces[c]["node"])
			var from := _slot_pos(0)
			if not _queue.is_empty():
				(_queue[0]["node"] as Node3D).queue_free()
				_queue.pop_front()
			var n := _piece_node(d["piece"])
			n.position = from
			_board.add_child(n)
			_pieces[c] = {"node": n, "piece": d["piece"], "t": 0.0, "from": from}
			_push_queue(e.queue[e.queue.size() - 1], _queue.size(), true)
			_feed_spin = 1.0
		"replace":
			var p := _cell_pos(d["cell"]) + Vector3(0, 0.3, 0)
			_fx.burst(p, Color(1.0, 0.7, 0.3), 24, 4.0, 0.5, 0.06, 1.0, -9.0, 1.0, "glow")
			_shake = maxf(_shake, 0.25)
		"flow_start":
			var p := _cell_pos(e.source) + Vector3(0, 1.0, 0)
			_fx.burst(p, Color(0.9, 0.9, 0.85), 10, 1.0, 1.0, 0.1, 0.0, 1.0, 1.0, "smoke")
			_fx.flash(_cell_pos(e.source), GLOW, 2.0)
			_shake = maxf(_shake, 0.3)
		"fill":
			var c: Vector2i = d["cell"]
			var p := _cell_pos(c) + Vector3(0, _glow_y + 0.1, 0)
			_fx.burst(p, GLOW, 6, 1.2, 0.5, 0.05, 1.0, 1.0, 1.0, "glow")
			if _pieces.has(c):
				_pieces[c]["pulse"] = 1.0
			if d["cross_twice"]:
				_fx.burst(p, Color(1.0, 0.85, 0.35), 40, 4.0, 0.9, 0.08, 1.0, -4.0, 1.0, "glow")
				_fx.flash(p, Color(1.0, 0.85, 0.4), 3.0)
				_punch = 0.6
				_punch_at = p
		"spill":
			var c: Vector2i = d["cell"]
			var p := _cell_pos(c)
			p.x = clampf(p.x, -0.2, F.COLS + 0.2)
			p.z = clampf(p.z, -0.2, F.ROWS + 0.2)
			var s := _model("spill")
			if s == null:
				s = MeshInstance3D.new()
				var cyl := CylinderMesh.new()
				cyl.top_radius = 0.6
				cyl.bottom_radius = 0.7
				cyl.height = 0.03
				(s as MeshInstance3D).mesh = cyl
				(s as MeshInstance3D).material_override = _mat(GLOW, 0.1, 0.0, 2.0)
			s.position = p + Vector3(0, 0.02, 0)
			s.scale = Vector3.ONE * 0.1
			_board.add_child(s)
			create_tween().tween_property(s, "scale", Vector3.ONE, 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			_fx.burst(p + Vector3(0, 0.3, 0), GLOW, 60, 5.0, 1.0, 0.08, 1.0, -12.0, 1.0, "glow")
			_fx.burst(p + Vector3(0, 0.4, 0), Color(0.9, 0.95, 0.9), 14, 1.5, 1.4, 0.25, 0.0, 1.0, 1.0, "smoke")
			_fx.flash(p, GLOW, 4.0)
			_shake = 1.0
			_punch = 0.8
			_punch_at = p
			_head_light.position = p + Vector3(0, 0.5, 0)
		"passed":
			_sweep = 1.0
			_celebrate = 3.0
			if _shop:
				_shop.call("alarm", 0.0)
		"failed":
			_shake = maxf(_shake, 0.6)


## A scrapped piece is flung off the board, spinning.
func _fling(n: Node3D) -> void:
	_flung.append({"node": n, "vel": Vector3(randf_range(-2, 2), 6.0, randf_range(1.5, 3.0)), "spin": Vector3(randf_range(-9, 9), randf_range(-6, 6), randf_range(-9, 9)), "t": 0.0})


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 1.6)
	_punch = maxf(0.0, _punch - delta)
	_sweep = maxf(0.0, _sweep - delta * 0.4)
	var e := game.engine
	if e == null or _board == null:
		return
	_place_pieces(e, delta)
	_place_queue(delta)
	_place_glow(e)
	_place_cursor(e, delta)
	_place_machinery(e, delta)
	_alarm(e)
	_celebration(e, delta)
	for f in _flung:
		f["t"] += delta
		var n: Node3D = f["node"]
		f["vel"].y -= 22.0 * delta
		n.position += f["vel"] * delta
		n.rotation += f["spin"] * delta
	for f in _flung.filter(func(f): return f["t"] > 1.5):
		(f["node"] as Node3D).queue_free()
	_flung = _flung.filter(func(f): return f["t"] <= 1.5)
	_place_camera(delta)


## Each new piece flies from the dispenser in an arc and lands with a squash; a filled one swells a little.
func _place_pieces(_e: FlowEngine, delta: float) -> void:
	for c in _pieces:
		var p: Dictionary = _pieces[c]
		var n: Node3D = p["node"]
		p["t"] += delta
		var to := _cell_pos(c)
		const FLY := 0.2
		if p["t"] < FLY:
			var k: float = p["t"] / FLY
			n.position = (p["from"] as Vector3).lerp(to, k) + Vector3(0, sin(k * PI) * 1.4, 0)
			n.scale = Vector3.ONE * lerpf(0.8, 1.0, k)
		else:
			var k: float = minf(1.0, (p["t"] - FLY) / 0.25)
			var sq := sin(k * PI) * 0.18 * (1.0 - k)
			n.position = to
			var pulse: float = p.get("pulse", 0.0)
			p["pulse"] = maxf(0.0, pulse - delta * 3.0)
			var s := 1.0 + pulse * 0.05
			n.scale = Vector3(s + sq, s - sq * 1.5, s + sq)


func _place_queue(delta: float) -> void:
	for i in _queue.size():
		var n: Node3D = _queue[i]["node"]
		n.position = n.position.lerp(_slot_pos(i), minf(1.0, delta * 12.0))
		n.rotation.y = sin(_time * 1.5 + i) * 0.06 if i == 0 else 0.0


## The cogs on blocked cells turn, the dispenser's feed gear spins as the queue moves, the tank drains as the glow goes.
func _place_machinery(e: FlowEngine, delta: float) -> void:
	for c in _cogs:
		(c[0] as Node3D).rotation.y += c[1] * delta
	if _feed_gear:
		_feed_spin = maxf(0.0, _feed_spin - delta * 2.5)
		_feed_gear.rotation.x -= _feed_spin * 9.0 * delta
	if _tank:
		var left := 1.0 - 0.75 * clampf(float(e.filled) / e.length, 0.0, 1.0) if e.flowing else 1.0
		_tank.scale.y = lerpf(_tank.scale.y, left, minf(1.0, delta * 3.0))
	if _outlet:
		var f := 0.0
		if e.flowing:
			f = e.progress if e.head == e.source and e.phase == F.Phase.PLAY else 1.0
		_outlet.set_instance_shader_parameter("fill", f)


## The glow: a tube per filled way through a piece, revealed to the flow's progress; a light rides its head.
func _place_glow(e: FlowEngine) -> void:
	for c in e.grid:
		var filled: Array = e.grid[c]["filled"]
		for enter in filled:
			var key := "%d,%d,%d" % [c.x, c.y, enter]
			if not _glows.has(key):
				_glows[key] = _glow_for(c, e.grid[c]["piece"], enter)
			var f := 1.0
			if e.flowing and c == e.head and enter == e.head_from and e.phase == F.Phase.PLAY:
				f = e.progress
			var g: GeometryInstance3D = _glows[key][0]
			g.set_instance_shader_parameter("fill", f)
			g.set_instance_shader_parameter("reverse", 1.0 if _glows[key][1] else 0.0)
	_glow_mat.set_shader_parameter("speed", 4.0 if e.fast else 1.0)
	if e.flowing and e.phase == F.Phase.PLAY:
		_head_light.light_energy = lerpf(_head_light.light_energy, 2.2, 0.1)
		_head_light.position = _head_point(e) + Vector3(0, 0.35, 0)
	elif e.phase == F.Phase.PLAY:
		_head_light.light_energy = 0.0


## [the glow geometry for a way through a piece, whether it fills from its U = 1 end]: the model's own glow path
## (U = 0 at its base left opening for a straight or a cross's level run, at the top opening for a corner or the
## cross's arch), else a tube of ours.
func _glow_for(c: Vector2i, piece: String, enter: int) -> Array:
	var holder: Node3D = _pieces[c]["node"] if _pieces.has(c) else null
	if holder:
		var k := turns(piece)
		var gn := "glow_path"
		var u0 := posmod(3 - k, 4)
		if piece == "x" and enter in [0, 2]:
			gn = "glow_path_v"
			u0 = 0
		elif piece not in ["h", "v", "x"]:
			u0 = posmod(0 - k, 4)
		if holder.has_meta(gn):
			return [holder.get_meta(gn), enter != u0]
	return [_glow_node(c, piece, enter), false]


func _glow_node(c: Vector2i, piece: String, enter: int) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.material_override = _glow_mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var out := F.exit_of(piece, enter)
	if piece in ["h", "v", "x"]:
		mi.mesh = _tube_line
		mi.rotation.y = posmod(3 - enter, 4) * PI * 0.5
	else:
		var k := turns(piece)
		mi.mesh = _tube_arc if posmod(0 - k, 4) == enter else _tube_arc_rev
		mi.rotation.y = k * PI * 0.5
	mi.position = _cell_pos(c)
	_board.add_child(mi)
	assert(out >= 0)
	return mi


## Where the glow's front is, in the world.
func _head_point(e: FlowEngine) -> Vector3:
	var c := _cell_pos(e.head)
	if e.head == e.source:
		var d: Vector2i = F.DIRS[e.source_dir]
		return c + Vector3(d.x, 0, d.y) * 0.5 * e.progress + Vector3(0, _glow_y, 0)
	var a: Vector2i = F.DIRS[e.head_from]
	var b: Vector2i = F.DIRS[F.exit_of(e.grid[e.head]["piece"], e.head_from)]
	var t := e.progress
	var p := Vector3(a.x, 0, a.y) * 0.5 * (1.0 - t) * (1.0 - t) + Vector3(b.x, 0, b.y) * 0.5 * t * t
	return c + p + Vector3(0, _glow_y, 0)


func _place_cursor(e: FlowEngine, delta: float) -> void:
	var to := _cell_pos(e.cursor)
	_cursor_pos = _cursor_pos.lerp(to, minf(1.0, delta * 22.0))
	_cursor.position = _cursor_pos + Vector3(0, 0.02 + sin(_time * 4.0) * 0.015, 0)
	var ok := e.can_place(e.cursor) and e.phase == F.Phase.PLAY
	_cursor.visible = e.phase == F.Phase.PLAY and not game.over
	var cm := _mat(Color(0.5, 1.0, 0.8) if ok else Color(1.0, 0.35, 0.25), 0.3, 0.6, 1.6 + 0.6 * sin(_time * 6.0))
	for m in _cursor.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var sm := mi.mesh.surface_get_material(si)
			if (sm and sm.resource_name.contains("glow")) or _cursor.get_child_count() == 4:
				mi.set_surface_override_material(si, cm)
	# the next piece hovers, ghostly, over the cursor
	var front: String = e.queue[0] if not e.queue.is_empty() else ""
	if front != _ghost_piece:
		if _ghost:
			_ghost.queue_free()
		_ghost = _piece_node(front) if front != "" else null
		_ghost_piece = front
		if _ghost:
			for g in _ghost.find_children("*", "GeometryInstance3D", true, false):
				(g as GeometryInstance3D).transparency = 0.6
				(g as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_board.add_child(_ghost)
	if _ghost:
		_ghost.visible = ok
		_ghost.position = _cursor_pos + Vector3(0, 0.45 + sin(_time * 3.0) * 0.05, 0)


## As the glow nears a dead end, the workshop sounds the alarm.
func _alarm(e: FlowEngine) -> void:
	if _shop == null:
		return
	var a := 0.0
	if e.flowing and e.phase == F.Phase.PLAY:
		var out: int = e.source_dir if e.head == e.source else F.exit_of(e.grid[e.head]["piece"], e.head_from)
		var nxt: Vector2i = e.head + (F.DIRS[out] as Vector2i)
		var enter := F.opposite(out)
		var ok: bool = F.inside(nxt) and e.grid.has(nxt) and F.accepts(e.grid[nxt]["piece"], enter) \
			and not (e.grid[nxt]["filled"] as Array).has(enter)
		if not ok:
			a = e.progress
	_shop.call("alarm", a)


## A finished pipeline lights up end to end, sparks rising from each piece in turn.
func _celebration(e: FlowEngine, delta: float) -> void:
	if _celebrate <= 0.0:
		return
	var before := _celebrate
	_celebrate -= delta
	var cells: Array = e.grid.keys().filter(func(c): return not (e.grid[c]["filled"] as Array).is_empty())
	cells.sort_custom(func(a, b): return a.x + a.y < b.x + b.y)
	var n := cells.size()
	for i in n:
		var at := 3.0 - 2.0 * float(i) / maxi(1, n)
		if before > at and _celebrate <= at:
			var p := _cell_pos(cells[i]) + Vector3(0, 0.4, 0)
			_fx.burst(p, GLOW if i % 2 == 0 else Color(1.0, 0.8, 0.35), 14, 3.0, 0.8, 0.06, 1.0, -3.0, 1.0, "glow")
			if _pieces.has(cells[i]):
				_pieces[cells[i]]["pulse"] = 1.0


func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_v := tan(deg_to_rad(camera.fov * 0.5))
	var dist := maxf(4.6 / half_v, 7.2 / (half_v * aspect)) * 1.02
	var look := Vector3(4.35, 0.0, 3.75)
	var lean := Vector3.ZERO
	if e and e.flowing and e.phase == F.Phase.PLAY:
		lean = (_head_point(e) - look) * 0.08
	_lean = _lean.lerp(lean, minf(1.0, delta * 1.5))
	look += _lean
	var el := deg_to_rad(57.0)
	var yaw := sin(_time * 0.1) * 0.03
	var off := Vector3(sin(yaw) * cos(el), sin(el), cos(yaw) * cos(el)) * dist
	var pos := look + off
	if _punch > 0.0:
		var k := sin(_punch / 0.8 * PI) * 0.18
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + off * 0.6, k)
	if _sweep > 0.0:
		var k := sin(_sweep * PI)
		var a := (1.0 - _sweep) * TAU * 0.12
		pos = look + Vector3(sin(a) * cos(el), sin(el) - 0.12 * k, cos(a) * cos(el)) * dist * (1.0 - 0.15 * k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.12 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
