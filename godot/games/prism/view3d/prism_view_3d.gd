class_name PrismView3D
extends Node3D
## Prism Breaker in 3D: the field stands upright in a neon arena at the mouth of a long grid tunnel under a nebula
## sky, seen in perspective from below and behind the paddle, the camera drifting gently. Thick crystal bricks refract
## their glowing cores and light up when hit or when a shock wave from a broken neighbour runs through them; the ball
## is a moving light that throws the bricks' shadows on the glossy back plate, and trails a ribbon. Bricks burst into
## tumbling shards; the paddle-ship fires thrusters; capsules and laser bolts glow; the walls flash where the ball
## bounces; the tunnel and sky pulse on the music's beat and brighten with combos. A cleared wall explodes and the
## camera swoops while the tunnel goes to warp; the next wall flies in from the deep.
## Field (x, y down) is world (x - 6.5, 8.5 - y, 0).

const E = preload("res://games/prism/engine/prism_engine.gd")
const M := "res://games/prism/art/models/"
const SH := "res://games/prism/shaders/"
const T := 0.8  # frame thickness
const BEAT := 60.0 / 128.0  # the theme's tempo
const DEPTH := 1.7  # bricks are thicker than the models: deep crystal blocks
const COLORS := {"a": Color(1.0, 0.22, 0.3), "b": Color(1.0, 0.55, 0.12), "c": Color(1.0, 0.88, 0.2),
	"d": Color(0.2, 1.0, 0.45), "e": Color(0.2, 0.55, 1.0), "f": Color(0.72, 0.3, 1.0), "H": Color(0.75, 0.95, 1.0),
	"S": Color(0.7, 0.75, 0.8), "G": Color(1.0, 0.8, 0.3)}
const CAPSULES := {"wide": ["W", Color(0.25, 0.55, 1.0)], "laser": ["L", Color(1.0, 0.25, 0.25)],
	"catch": ["C", Color(0.25, 1.0, 0.45)], "slow": ["S", Color(1.0, 0.6, 0.15)], "multi": ["M", Color(0.3, 0.95, 1.0)],
	"life": ["+", Color(0.6, 0.6, 0.7)], "break": ["B", Color(1.0, 0.35, 0.9)]}
## per wall: the arena neon, the outer rim, the tunnel's two colours
const PALETTES := [
	[Color(0.2, 0.75, 1.0), Color(1.0, 0.25, 0.8), Color(0.15, 0.5, 1.0), Color(0.85, 0.2, 1.0)],
	[Color(1.0, 0.35, 0.75), Color(0.3, 0.8, 1.0), Color(0.9, 0.2, 0.7), Color(0.25, 0.4, 1.0)],
	[Color(0.3, 1.0, 0.7), Color(0.4, 0.5, 1.0), Color(0.1, 0.9, 0.7), Color(0.3, 0.3, 1.0)],
	[Color(1.0, 0.6, 0.2), Color(0.9, 0.2, 0.5), Color(1.0, 0.45, 0.15), Color(0.8, 0.15, 0.6)],
]

@export var game: PrismGame

var camera: Camera3D
var _board: Node3D
var _fx: PrismEffects
var _bricks := {}  ## cell -> node
var _brick_mesh := {}  ## cell -> MeshInstance3D carrying the crystal (for the flash)
var _flash := {}  ## cell -> hit flash left (0..1)
var _lit := {}  ## cell -> the flash last sent to the crystal (only changes are sent)
var _paddle: Node3D
var _thrust: Array[CPUParticles3D] = []
var _pw := 2.0
var _squash := 0.0
var _balls: Array[Node3D] = []
var _bolts: Array[Node3D] = []
var _capsules: Array[Node3D] = []
var _drones := {}  ## id -> node
var _gates: Array[Node3D] = []
var _gate_open := [0.0, 0.0]
var _warp: Node3D
var _time := 0.0
var _stage_t := 0.0
var _shake := 0.0
var _mats := {}
var _bumps := {}  ## cell -> seconds of a bump left
var _crystal: ShaderMaterial
var _env: Environment
var _sky: ShaderMaterial
var _tunnel: ShaderMaterial
var _plate: ShaderMaterial
var _neon: StandardMaterial3D   ## the frame's inner light strips (one material, animated)
var _rim: StandardMaterial3D    ## the arena's outer neon tubes
var _danger: StandardMaterial3D ## the line below the paddle
var _palette := 0
var _neon_hit := 0.0
var _danger_hit := 0.0
var _waves: Array[Dictionary] = []  ## {pos: Vector2 (world xy), t, s, col}
var _pulse := 0.0
var _combo := 0
var _travel := 0.0
var _warp_speed := 0.0
var _clear_t := -1.0   ## seconds since the wall was cleared (-1: not cleared)
var _doomed := {}      ## cell -> seconds until it explodes (the clear-wall blast)
var _fireworks: Array[Dictionary] = []  ## {t: seconds to go, pos, col}: rainbow bursts over a cleared wall
var _dist := 30.0
var _fit_aspect := 0.0
var _audio: Node


static func W(p: Vector2, z := 0.0) -> Vector3:
	return Vector3(p.x - 6.5, 8.5 - p.y, z)


func _ready() -> void:
	_env = Environment.new()
	_sky = ShaderMaterial.new()
	_sky.shader = load(SH + "prism_sky.gdshader")
	var sky := Sky.new()
	sky.sky_material = _sky
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.35, 0.4, 0.7)
	_env.ambient_light_energy = 0.3
	_env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.0
	_env.tonemap_white = 6.0
	_env.glow_enabled = true
	_env.glow_normalized = true
	for i in 7:
		_env.set_glow_level(i, [0.0, 0.6, 1.0, 1.0, 0.8, 0.6, 0.4][i])
	_env.glow_intensity = 1.0
	_env.glow_strength = 1.0
	_env.glow_bloom = 0.02
	_env.glow_hdr_threshold = 1.0
	_env.glow_hdr_scale = 2.0
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.15
	_env.adjustment_contrast = 1.05
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, -30, 0)
	key.light_energy = 0.55
	key.light_color = Color(0.75, 0.8, 1.0)
	key.shadow_enabled = true
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(20, 40, 0)
	fill.light_energy = 0.25
	fill.light_color = Color(0.9, 0.4, 1.0)
	add_child(fill)
	camera = Camera3D.new()
	camera.fov = 40
	camera.far = 400.0
	camera.current = true
	add_child(camera)
	_crystal = ShaderMaterial.new()
	_crystal.shader = load(SH + "prism_crystal.gdshader")
	_fx = PrismEffects.new()
	add_child(_fx)
	_build_stage()
	_build_frame()
	_audio = get_parent().get_node_or_null("Audio")
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.9, 0.4, 0.3)
	mi.mesh = b
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color, energy := -1.0, albedo := 1.0) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col, energy, albedo]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				var a := t.albedo_color.a
				t.albedo_color = Color(col * albedo, a)
				if t.emission_enabled or energy > 0.0:
					t.emission_enabled = true
					t.emission = col
					if energy > 0.0:
						t.emission_energy_multiplier = energy
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


## Every surface whose material is called match_name gets mat instead; returns the mesh instances touched.
func _swap(n: Node, match_name: String, mat: Material) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var sm := m.mesh.surface_get_material(i)
			if sm and sm.resource_name.contains(match_name):
				m.set_surface_override_material(i, mat)
				if not out.has(m):
					out.append(m)
	return out


func _glow_mat(col: Color, energy: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0, 0, 0)
	m.emission_enabled = true
	m.emission = col
	m.emission_energy_multiplier = energy
	return m


## The world around the field: the tunnel receding behind it, the back plate, drifting motes, the neon rim.
func _build_stage() -> void:
	_tunnel = ShaderMaterial.new()
	_tunnel.shader = load(SH + "prism_tunnel.gdshader")
	var box := BoxMesh.new()
	box.size = Vector3(44, 34, 200)
	box.flip_faces = true
	var tun := MeshInstance3D.new()
	tun.mesh = box
	tun.material_override = _tunnel
	tun.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	tun.position = Vector3(0, 1.0, -100.0 - 1.5)
	add_child(tun)
	_plate = ShaderMaterial.new()
	_plate.shader = load(SH + "prism_plate.gdshader")
	var q := QuadMesh.new()
	q.size = Vector2(E.W + T * 2.0, E.H + T + 0.6)
	var plate := MeshInstance3D.new()
	plate.mesh = q
	plate.material_override = _plate
	plate.position = Vector3(0, 8.5 + T - (E.H + T + 0.6) * 0.5, -0.55)
	add_child(plate)
	# dust motes drifting through the tunnel: they give the depth its parallax as the camera moves
	var motes := CPUParticles3D.new()
	motes.amount = 220
	motes.lifetime = 14.0
	motes.preprocess = 14.0
	motes.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	motes.emission_box_extents = Vector3(20, 15, 26)
	motes.position = Vector3(0, 1, -40)
	motes.direction = Vector3(0, 0, 1)
	motes.spread = 5.0
	motes.gravity = Vector3.ZERO
	motes.initial_velocity_min = 1.0
	motes.initial_velocity_max = 2.5
	motes.scale_amount_min = 0.462
	motes.scale_amount_max = 1.54
	var qm := QuadMesh.new()
	qm.size = Vector2(0.5, 0.5)
	motes.mesh = qm
	motes.material_override = Fx.material("glow", Color(0.5, 0.7, 1.0, 0.5))
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0))
	fade.set_color(1, Color(1, 1, 1, 0))
	fade.add_point(0.2, Color(1, 1, 1, 1))
	fade.add_point(0.8, Color(1, 1, 1, 1))
	motes.color_ramp = fade
	motes.local_coords = false
	add_child(motes)
	# the arena's outer neon: tubes around the front edge of the frame, and the line under the paddle
	_rim = _glow_mat(Color(1.0, 0.25, 0.8), 4.0)
	var x0 := -6.5 - T - 0.06
	var yt := 8.5 + T + 0.06
	var yb := 8.5 - E.H - 0.4
	for seg in [[Vector3(x0, (yt + yb) * 0.5, 0.62), Vector3(0.07, yt - yb, 0.07)],
			[Vector3(-x0, (yt + yb) * 0.5, 0.62), Vector3(0.07, yt - yb, 0.07)],
			[Vector3(0, yt, 0.62), Vector3(-x0 * 2.0 + 0.07, 0.07, 0.07)],
			[Vector3(x0, (yt + yb) * 0.5, -0.4), Vector3(0.05, yt - yb, 0.05)],
			[Vector3(-x0, (yt + yb) * 0.5, -0.4), Vector3(0.05, yt - yb, 0.05)],
			[Vector3(0, yt, -0.4), Vector3(-x0 * 2.0 + 0.05, 0.05, 0.05)]]:
		var bm := BoxMesh.new()
		bm.size = seg[1]
		var mi := MeshInstance3D.new()
		mi.mesh = bm
		mi.material_override = _rim
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.position = seg[0]
		add_child(mi)
	_danger = _glow_mat(Color(1.0, 0.15, 0.35), 1.2)
	var dl := BoxMesh.new()
	dl.size = Vector3(E.W, 0.03, 0.03)
	var dmi := MeshInstance3D.new()
	dmi.mesh = dl
	dmi.material_override = _danger
	dmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dmi.position = W(Vector2(6.5, E.H + 0.05), -0.4)
	add_child(dmi)


## The frame stays for the whole game: sides, top with the two drone doors, corners, the break door.
func _build_frame() -> void:
	var f := Node3D.new()
	add_child(f)
	_neon = _glow_mat(Color(0.2, 0.75, 1.0), 5.0)
	for y in 17:
		var l := _scene("frame_side")
		l.position = W(Vector2(-T * 0.5, y + 0.5))
		l.rotation.z = PI
		f.add_child(l)
		if y < 15:
			var r := _scene("frame_side")
			r.position = W(Vector2(E.W + T * 0.5, y + 0.5))
			f.add_child(r)
	_warp = _scene("warp_gate")
	_warp.position = W(Vector2(E.W + T * 0.5, E.WARP_Y))
	f.add_child(_warp)
	for x in 13:
		if x in [3, 4, 8, 9]:
			continue
		var t := _scene("frame_top")
		t.position = W(Vector2(x + 0.5, -T * 0.5))
		f.add_child(t)
	for gx in E.GATES:
		var g := _scene("gate")
		g.position = W(Vector2(gx, -T * 0.5))
		f.add_child(g)
		_gates.append(g)
	for cx in [-T * 0.5, E.W + T * 0.5]:
		var c := _scene("frame_corner")
		c.position = W(Vector2(cx, -T * 0.5))
		f.add_child(c)
	# dark gunmetal with the light strips as one animated neon
	_tint(f, "frame_plate", Color(0.07, 0.08, 0.12))
	_tint(f, "frame_metal", Color(0.05, 0.055, 0.08))
	_tint(f, "frame_chrome", Color(0.55, 0.6, 0.75))
	_swap(f, "frame_glow", _neon)


func _on_stage(e: PrismEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_bricks.clear()
	_brick_mesh.clear()
	_flash.clear()
	_lit.clear()
	_drones.clear()
	_balls.clear()
	_bolts.clear()
	_capsules.clear()
	_bumps.clear()
	_doomed.clear()
	_fireworks.clear()
	_waves.clear()
	_thrust.clear()
	_fx.clear_trails(0)
	_clear_t = -1.0
	_stage_t = 0.0
	_combo = 0
	_palette = game.stage % PALETTES.size()
	e.event.connect(_on_event)
	for c in e.bricks:
		var kind: String = e.bricks[c]["kind"]
		var n := _scene({"H": "brick_hard", "S": "brick_steel", "G": "brick_gold"}.get(kind, "brick"))
		n.position = _brick_pos(c)
		n.scale = Vector3(1, 1, DEPTH)
		if kind in "abcdefH":
			_tint(n, "brick_core", COLORS[kind], 2.0 if kind != "H" else 1.2)
			for mi in _swap(n, "brick_glass", _crystal):
				mi.set_instance_shader_parameter("tint", COLORS[kind] if kind != "H" else Color(0.55, 0.75, 0.95))
				_brick_mesh[c] = mi
		_board.add_child(n)
		_bricks[c] = n
	_paddle = _scene("paddle")
	_board.add_child(_paddle)
	var pl := OmniLight3D.new()
	pl.light_color = Color(0.4, 0.8, 1.0)
	pl.light_energy = 2.0
	pl.omni_range = 4.0
	pl.position = Vector3(0, 0.5, 0.9)
	_paddle.add_child(pl)
	for side in [-1.0, 1.0]:
		var p := CPUParticles3D.new()
		p.amount = 28
		p.lifetime = 0.22
		p.local_coords = false
		p.direction = Vector3(0, -1, 0.4)
		p.spread = 12.0
		p.gravity = Vector3.ZERO
		p.initial_velocity_min = 2.5
		p.initial_velocity_max = 4.0
		p.scale_amount_min = 0.615
		p.scale_amount_max = 1.38
		p.scale_amount_curve = Fx.size_curve(false)
		var qm := QuadMesh.new()
		qm.size = Vector2(0.5, 0.5)
		p.mesh = qm
		p.material_override = Fx.material("glow", Color(0.35, 0.75, 1.0))
		var g := Gradient.new()
		g.set_color(0, Color(1.0, 1.0, 1.0, 0.8))
		g.set_color(1, Color(0.9, 0.2, 1.0, 0.0))
		p.color_ramp = g
		p.position = Vector3(side, -0.12, 0.0)
		_paddle.add_child(p)
		_thrust.append(p)
	_pw = e.paddle_w
	_fit_aspect = 0.0
	_place_camera(0.0)


func _brick_pos(c: Vector2i) -> Vector3:
	return W(Vector2(c.x + 0.5, E.TOP + c.y * 0.5 + 0.25))


func _wave(pos: Vector3, col: Color, s := 1.0) -> void:
	# many waves at once (lasers, the clear) share the light, so the plate never turns into a mess of rings
	var busy := 0
	for w in _waves:
		if w["t"] < 0.5:
			busy += 1
	s /= 1.0 + busy * 0.35
	_waves.push_front({"pos": Vector2(pos.x, pos.y), "t": 0.0, "s": s, "col": col})
	if _waves.size() > 8:
		_waves.resize(8)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"brick":
			var c := Vector2i(d["col"], d["row"])
			if not _bricks.has(c):
				return
			var n: Node3D = _bricks[c]
			var col: Color = COLORS[d["kind"]]
			if d["broken"]:
				_break(c, col, 1.0)
				_combo += 1
				_pulse = minf(1.0, _pulse + 0.12 + minf(_combo, 10) * 0.02)
				_shake = maxf(_shake, 0.1 + minf(_combo, 8) * 0.015)
			else:
				_bumps[c] = 0.18
				_flash[c] = 1.0
				_fx.spark(n.position + Vector3(0, -0.25, 0.4), col.lightened(0.4))
				if d["kind"] == "H" and e.bricks.has(c):
					var taken: int = (2 + mini(e.stage / 2, 3)) - int(e.bricks[c]["hits"])
					var cr := n.get_node_or_null("crack")
					if cr:
						cr.queue_free()
					var crack := _scene("brick_crack_%d" % clampi(taken, 1, 2))
					crack.name = "crack"
					n.add_child(crack)
		"paddle":
			_squash = 1.0
			_combo = 0
			var p := W(Vector2(d["x"], E.PADDLE_Y - 0.2), 0.3)
			_fx.spark(p, Color(0.5, 0.9, 1.0))
			_fx.flash(p + Vector3(0, -2.5, 0.6), Color(0.4, 0.8, 1.0), 1.5)
		"wall":
			_neon_hit = 1.0
			for b in e.balls:
				var bp: Vector2 = b["pos"]
				var nrm := Vector3.ZERO
				if bp.x < 0.3: nrm = Vector3.RIGHT
				elif bp.x > E.W - 0.3: nrm = Vector3.LEFT
				elif bp.y < 0.3: nrm = Vector3.DOWN
				if nrm != Vector3.ZERO:
					_fx.wall_hit(W(bp, 0.2) - nrm * 0.15, nrm, _pal(0).lightened(0.3))
		"launch":
			var p := W(Vector2(e.paddle_x, E.PADDLE_Y))
			_wave(p, Color(0.4, 0.8, 1.0), 0.6)
			_fx.pop(p + Vector3(0, 0.3, 0.3), Color(0.4, 0.8, 1.0))
		"drone":
			_gate_open[E.GATES.find(d["x"])] = 1.2
		"drone_pop":
			var p := W(d["pos"], 0.2)
			_fx.pop(p, Color(1.0, 0.5, 0.9))
			_fx.shatter(p, Color(1.0, 0.5, 0.9), 10, 0.8)
		"capsule":
			var p := W(Vector2(e.paddle_x, E.PADDLE_Y), 0.3)
			var col: Color = CAPSULES[d["kind"]][1]
			_fx.pop(p, col)
			_wave(p, col, 1.2)
			_pulse = 1.0
		"laser":
			for dx in [-e.paddle_w * 0.4, e.paddle_w * 0.4]:
				_fx.spark(W(Vector2(e.paddle_x + dx, E.PADDLE_Y - 0.4), 0.2), Color(1.0, 0.35, 0.3))
		"lose_ball":
			_shake = 0.6
			_danger_hit = 1.0
			var p := W(Vector2(clampf(e.paddle_x, 1.0, 12.0), E.H), 0.2)
			_fx.pop(p, Color(1.0, 0.2, 0.3))
			_wave(p, Color(1.0, 0.15, 0.3), 1.5)
			_combo = 0
		"cleared":
			_clear()
		"warp":
			_fx.pop(W(Vector2(E.W, E.WARP_Y), 0.3), Color(1.0, 0.4, 0.9))
			_clear()


## A brick goes: shards, a flash, a shock wave that lights its neighbours.
func _break(c: Vector2i, col: Color, force: float) -> void:
	var n: Node3D = _bricks[c]
	_fx.shatter(n.position + Vector3(0, 0, 0.3), col, 16, force)
	_wave(n.position, col, force)
	n.queue_free()
	_bricks.erase(c)
	_brick_mesh.erase(c)
	_flash.erase(c)


## The wall is done: whatever is left (steel, gold) blows up in a ring from the centre, the camera swoops and the
## tunnel goes to warp.
func _clear() -> void:
	if _clear_t >= 0.0:
		return
	_clear_t = 0.0
	_shake = 0.5
	_pulse = 1.0
	var mid := Vector3(0, 3.0, 0)
	_wave(mid, Color(1, 1, 1), 2.0)
	_fx.flash(mid + Vector3(0, -2.5, 3.0), Color(0.8, 0.9, 1.0), 6.0)
	for c in _bricks:
		_doomed[c] = 0.25 + (_bricks[c] as Node3D).position.distance_to(mid) * 0.06
	for b in _balls:
		if b.visible:
			_fx.pop(b.position, Color(0.6, 0.9, 1.0))
	var rng := RandomNumberGenerator.new()
	rng.seed = game.stage * 7 + 3
	for i in 9:
		_fireworks.append({"t": 0.15 + i * 0.16, "pos": Vector3(rng.randf_range(-5.0, 5.0), rng.randf_range(-3.0, 7.0), 0.6),
			"col": COLORS["abcdef"[i % 6]]})


func _pal(i: int) -> Color:
	return PALETTES[_palette][i]


func _pool(arr: Array[Node3D], count: int, model: String, setup: Callable = Callable()) -> void:
	while arr.size() < count:
		var n := _scene(model)
		_board.add_child(n)
		if setup.is_valid():
			setup.call(n)
		arr.append(n)
	for i in arr.size():
		arr[i].visible = i < count


func _beat() -> float:
	var t := _time
	if _audio:
		var mp = _audio.get("_music")
		if mp is AudioStreamPlayer and (mp as AudioStreamPlayer).playing:
			t = (mp as AudioStreamPlayer).get_playback_position()
	return exp(-fmod(t, BEAT) * 7.0)


func _process(delta: float) -> void:
	_time += delta
	_stage_t += delta
	var e := game.engine
	if e == null or _paddle == null:
		return
	_update_world(delta)
	_update_bricks(delta, e)
	# paddle: stretch towards the engine's width, squash on a hit, thrusters at its ends
	_pw = move_toward(_pw, e.paddle_w, delta * 6.0)
	_squash = maxf(0.0, _squash - delta * 5.0)
	_paddle.position = W(Vector2(e.paddle_x, E.PADDLE_Y + 0.05))
	_paddle.scale = Vector3(1.0 + _squash * 0.06, 1.0 - _squash * 0.25, 1.0)
	var mid := _paddle.get_node_or_null("mid") as Node3D
	if mid:
		mid.scale.x = _pw - 1.0
		(_paddle.get_node("end_l") as Node3D).position.x = -(_pw - 1.0) * 0.5
		(_paddle.get_node("end_r") as Node3D).position.x = (_pw - 1.0) * 0.5
	var moving := absf(e.target_x - e.paddle_x)
	for i in _thrust.size():
		var p := _thrust[i]
		p.position.x = (_pw * 0.5 - 0.15) * (-1.0 if i == 0 else 1.0)
		p.initial_velocity_max = 3.0 + minf(moving, 2.0) * 2.0
		p.emitting = _paddle.visible
	_paddle.visible = not (e.phase == E.Phase.LOST or e.phase == E.Phase.OVER)
	_paddle.rotation.z = lerp_angle(_paddle.rotation.z, clampf((e.paddle_x - e.target_x) * 0.05, -0.08, 0.08), minf(1.0, delta * 10.0))
	# balls: a light each (the first casts the bricks' shadows), a ribbon of light behind
	_pool(_balls, e.balls.size(), "ball", func(n):
		var l := OmniLight3D.new()
		l.name = "light"
		l.light_color = Color(0.6, 0.9, 1.0)
		l.light_energy = 3.0
		l.omni_range = 5.0
		l.omni_attenuation = 1.6
		l.position = Vector3(0, 0, 0.5)
		l.shadow_enabled = _balls.is_empty()
		l.shadow_bias = 0.05
		n.add_child(l)
		var halo := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(1.3, 1.3)
		halo.mesh = q
		var hm := Fx.material("glow", Color(0.5, 0.85, 1.0, 0.8)).duplicate() as StandardMaterial3D
		hm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		halo.material_override = hm
		halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		n.add_child(halo))
	for i in e.balls.size():
		var b: Dictionary = e.balls[i]
		var n := _balls[i]
		n.visible = _clear_t < 0.0
		n.position = W(b["pos"], 0.0)
		var ring := n.get_node_or_null("ring") as Node3D
		if ring:
			ring.rotation.y += delta * 6.0
		var hot := clampf((float(b["speed"]) - E.SPEED0) / (E.SPEED_MAX - E.SPEED0), 0.0, 1.0)
		var col := Color(0.35, 0.8, 1.0).lerp(Color(1.0, 0.45, 0.85), hot)
		(n.get_node("light") as OmniLight3D).light_color = col.lightened(0.3)
		if b["held"] > -90.0:
			_fx.drop_trail(i)  # resting on the paddle: no trail
		else:
			_fx.trail_point(i, n.position, col)
	_fx.clear_trails(e.balls.size() if _clear_t < 0.0 else 0)
	_fx.draw_trails(camera)
	# laser bolts, each a red light
	_pool(_bolts, e.bolts.size(), "laser_bolt", func(n):
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.3, 0.25)
		l.light_energy = 2.0
		l.omni_range = 2.5
		l.position = Vector3(0, 0, 0.4)
		n.add_child(l))
	for i in e.bolts.size():
		_bolts[i].position = W(e.bolts[i]["pos"], 0.0)
		_bolts[i].scale = Vector3(1.0, 1.4, 1.0)
	# capsules: a letter on a coloured band, rocking as they fall, each a small light of its colour
	_pool(_capsules, e.capsules.size(), "capsule", func(n):
		var lb := Label3D.new()
		lb.name = "letter"
		lb.font = HudKit.font(true)
		lb.font_size = 80
		lb.pixel_size = 0.0045
		lb.position = Vector3(0, -0.01, 0.26)
		lb.outline_size = 22
		lb.outline_modulate = Color(0.02, 0.03, 0.08)
		lb.no_depth_test = true
		lb.render_priority = 2
		var l := OmniLight3D.new()
		l.name = "light"
		l.light_energy = 1.6
		l.omni_range = 2.5
		l.position = Vector3(0, 0, 0.5)
		n.add_child(l)
		n.scale = Vector3.ONE * 1.35
		n.add_child(lb))
	for i in e.capsules.size():
		var cp: Dictionary = e.capsules[i]
		var n := _capsules[i]
		n.position = W(cp["pos"], 0.15)
		var info: Array = CAPSULES[cp["kind"]]
		var lb := n.get_node("letter") as Label3D
		if lb.text != info[0]:
			lb.text = info[0]
			_tint(n, "capsule_band", info[1], 1.4)
			(n.get_node("light") as OmniLight3D).light_color = info[1]
		n.rotation.x = sin(_time * 5.0 + i) * 0.35
		n.rotation.y = sin(_time * 3.1 + i * 2.0) * 0.25
		(n.get_node("light") as OmniLight3D).light_energy = 1.3 + 0.5 * sin(_time * 10.0 + i)
	# drones
	var alive := {}
	for dr in e.drones:
		alive[dr["id"]] = true
		if not _drones.has(dr["id"]):
			var n := _scene("drone_%d" % dr["kind"])
			_board.add_child(n)
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			if ap and ap.has_animation("spin"):
				ap.get_animation("spin").loop_mode = Animation.LOOP_LINEAR
				ap.play("spin")
			var l := OmniLight3D.new()
			l.light_color = Color(1.0, 0.5, 0.9)
			l.light_energy = 1.0
			l.omni_range = 2.0
			l.position = Vector3(0, 0, 0.5)
			n.add_child(l)
			_drones[dr["id"]] = n
		_drones[dr["id"]].position = W(dr["pos"], 0.1)
	for id in _drones.keys():
		if not alive.has(id):
			_drones[id].queue_free()
			_drones.erase(id)
	# doors
	for i in _gates.size():
		_gate_open[i] = maxf(0.0, _gate_open[i] - delta)
		var door := _gates[i].get_node_or_null("door") as Node3D
		if door:
			door.scale.y = move_toward(door.scale.y, 0.05 if _gate_open[i] > 0.0 else 1.0, delta * 4.0)
	var wd := _warp.get_node_or_null("door") as Node3D
	if wd:
		wd.scale.y = move_toward(wd.scale.y, 0.05 if e.warp_open else 1.0, delta * 2.5)
	_shake = maxf(0.0, _shake - delta * 1.5)
	_place_camera(delta)


## Sky, tunnel, plate and neon: the beat, the combo pulse, the warp between walls, the shock waves.
func _update_world(delta: float) -> void:
	var beat := _beat()
	_pulse = maxf(0.0, _pulse - delta * 1.2)
	_neon_hit = maxf(0.0, _neon_hit - delta * 4.0)
	_danger_hit = maxf(0.0, _danger_hit - delta * 1.5)
	if _clear_t >= 0.0:
		_clear_t += delta
		_warp_speed = minf(1.0, _warp_speed + delta * 0.8)
	else:
		_warp_speed = maxf(0.0, _warp_speed - delta * 0.7)
	var p := beat * 0.3 + _pulse * 0.8
	var speed := 3.0 + minf(_combo, 12) * 0.5 + _warp_speed * _warp_speed * 70.0
	_travel += speed * delta
	_tunnel.set_shader_parameter("travel", _travel)
	_tunnel.set_shader_parameter("pulse", p)
	_tunnel.set_shader_parameter("col_a", _pal(2))
	_tunnel.set_shader_parameter("col_b", _pal(3))
	_sky.set_shader_parameter("pulse", p * 0.5)
	_sky.set_shader_parameter("warp", _warp_speed)
	_neon.emission = _pal(0).lerp(Color.WHITE, _neon_hit * 0.5)
	_neon.emission_energy_multiplier = 3.5 + beat * 1.0 + _neon_hit * 5.0 + _pulse * 2.0
	_rim.emission = _pal(1)
	_rim.emission_energy_multiplier = 2.5 + beat * 2.0 + _pulse * 3.0
	_danger.emission_energy_multiplier = 1.0 + 0.4 * sin(_time * 3.0) + _danger_hit * 12.0
	_env.glow_intensity = 1.0 + _pulse * 0.35
	for w in _waves:
		w["t"] += delta
	_waves = _waves.filter(func(w): return w["t"] < 1.6)
	var wv := PackedVector4Array()
	var wc := PackedVector3Array()
	for i in 8:
		if i < _waves.size():
			var w: Dictionary = _waves[i]
			wv.append(Vector4(w["pos"].x, w["pos"].y, w["t"], w["s"]))
			var c: Color = w["col"]
			wc.append(Vector3(c.r, c.g, c.b))
		else:
			wv.append(Vector4(0, 0, 0, 0))
			wc.append(Vector3.ZERO)
	_plate.set_shader_parameter("waves", wv)
	_plate.set_shader_parameter("wave_cols", wc)
	_plate.set_shader_parameter("pulse", p)
	_plate.set_shader_parameter("line_col", _pal(2))


## Bricks fly in from the deep at the start of a wall, flash when hit or when a wave passes, blow up on a clear.
func _update_bricks(delta: float, e: PrismEngine) -> void:
	for c in _doomed.keys():
		_doomed[c] -= delta
		if _doomed[c] <= 0.0:
			_doomed.erase(c)
			if _bricks.has(c):
				var kind: String = e.bricks[c]["kind"] if e.bricks.has(c) else "S"
				_break(c, COLORS.get(kind, Color.WHITE), 1.4)
				_shake = maxf(_shake, 0.25)
	for f in _fireworks:
		f["t"] -= delta
		if f["t"] <= 0.0:
			_fx.shatter(f["pos"], f["col"], 28, 1.3)
			_fx.pop(f["pos"], f["col"])
			_wave(f["pos"], f["col"], 0.8)
			_neon_hit = 1.0
	_fireworks = _fireworks.filter(func(f): return f["t"] > 0.0)
	for c in _bricks:
		var n: Node3D = _bricks[c]
		var target := _brick_pos(c)
		# arrival: row by row from the top, each brick from far behind with a little overshoot
		var t := clampf((_stage_t - 0.15 - c.y * 0.07 - absf(c.x - 6) * 0.025) / 0.55, 0.0, 1.0)
		var k := 1.0 - pow(1.0 - t, 3.0)
		var ov := sin(t * PI) * 0.35
		n.position = target + Vector3((c.x - 6.0) * 0.6 * (1.0 - k), 0, 16.0 * (1.0 - k) - ov)
		n.rotation.y = (1.0 - k) * 2.5 * (1.0 if c.x < 6.5 else -1.0)
		n.rotation.x = (1.0 - k) * -1.5
		var bump: float = maxf(_bumps.get(c, 0.0), 0.0) / 0.18
		n.scale = Vector3(1.0 + 0.12 * bump, 1.0 + 0.12 * bump, DEPTH)
		if _brick_mesh.has(c):
			var f: float = _flash.get(c, 0.0)
			f = maxf(0.0, f - delta * 4.0)
			if f > 0.0:
				_flash[c] = f
			else:
				_flash.erase(c)
			var wf := 0.0
			for w: Dictionary in _waves:
				var d := Vector2(target.x, target.y).distance_to(w["pos"])
				var rad: float = w["t"] * 9.0
				wf += exp(-pow((d - rad) * 1.6, 2.0)) * w["s"] * exp(-w["t"] * 2.5) * 0.3
			var lit := f + wf + (1.0 - k) * 0.25
			if absf(lit - float(_lit.get(c, -1.0))) > 0.01:
				_lit[c] = lit
				_brick_mesh[c].set_instance_shader_parameter("flash", lit)
	for c in _bumps.keys():
		_bumps[c] -= delta
		if _bumps[c] <= 0.0:
			_bumps.erase(c)


func _fit(aspect: float) -> void:
	# the distance at which the arena (frame and the line under the paddle) fills the screen, bisected
	var pts: Array[Vector3] = []
	for x in [-7.4, 7.4]:
		for y in [9.4, -8.9]:
			for z in [0.7, -0.5]:
				pts.append(Vector3(x, y, z))
	var lo := 10.0
	var hi := 90.0
	var vp := get_viewport().get_visible_rect().size
	var margin := Vector2(vp.x * 0.02, vp.y * 0.035)
	for i in 22:
		var mid := (lo + hi) * 0.5
		_aim(mid, 0.0, 0.0, Vector3.ZERO)
		var ok := true
		for p in pts:
			if camera.is_position_behind(p):
				ok = false
				break
			var s := camera.unproject_position(p)
			if s.x < margin.x or s.y < margin.y or s.x > vp.x - margin.x or s.y > vp.y - margin.y:
				ok = false
				break
		if ok:
			hi = mid
		else:
			lo = mid
	_dist = hi
	_fit_aspect = aspect


func _aim(dist: float, yaw: float, pitch: float, jitter: Vector3) -> void:
	var target := Vector3(0, 0.1, 0)
	var dir := Vector3(0, -0.46 - pitch, 1.0).normalized().rotated(Vector3.UP, yaw)
	camera.position = target + dir * dist + jitter
	camera.look_at(target + jitter * 0.5, Vector3.UP)


func _place_camera(_delta: float) -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	if absf(aspect - _fit_aspect) > 0.001:
		_fit(aspect)
	var e := game.engine
	# a slow drift, a little lean towards the paddle, the fly-in at the start of a wall, the swoop when it is cleared
	var lean := ((e.paddle_x - 6.5) * 0.006) if e else 0.0
	var yaw := sin(_time * 0.21) * 0.035 + lean
	var pitch := sin(_time * 0.17) * 0.02
	var dist := _dist
	var intro := clampf(1.0 - _stage_t / 1.6, 0.0, 1.0)
	intro = intro * intro * (3.0 - 2.0 * intro)
	yaw += intro * 0.5
	pitch += intro * 0.35
	dist *= 1.0 + intro * 0.5
	if _clear_t >= 0.0:
		var s := clampf(_clear_t / 2.6, 0.0, 1.0)
		var sw := sin(s * PI)
		yaw += -sw * 0.38
		pitch += sw * 0.12
		dist *= 1.0 - sw * 0.1
	var j := Vector3(sin(_time * 50.0), cos(_time * 43.0), 0) * _shake * _shake * (0.5 if Settings.camera_shake else 0.0)
	_aim(dist, yaw, pitch, j)


## The field x under a screen position (for the mouse).
func field_x_at(screen: Vector2) -> float:
	var o := camera.project_ray_origin(screen)
	var d := camera.project_ray_normal(screen)
	# intersect with the plane z = 0
	if absf(d.z) < 0.0001:
		return game.engine.paddle_x if game.engine else 6.5
	var t := -o.z / d.z
	var p := o + d * t
	return p.x + 6.5
