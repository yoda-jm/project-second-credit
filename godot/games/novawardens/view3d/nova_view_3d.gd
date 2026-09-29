class_name NovaView3D
extends Node3D
## Nova Wardens in 3D: the last line of defence on a coastal hilltop at night (the NovaBackdrop diorama when there is
## one). The fleet of glowing aliens steps to the march beat; the cannon hovers on the ground line; shots and bombs
## glow and light what they pass; the four shields are voxels, one crystal cube per pixel of the engine's bitmaps,
## eroding for real. Invaders burst into sparks in their colour; the mothership goes up in a big flash. The camera
## drifts, leans with the cannon, looks down a little as the fleet comes lower (the city's alarm rising with it),
## shakes when the cannon is hit and sweeps round when a wave is cleared. World = arcade pixels x 0.05, y up.

const N = preload("res://games/novawardens/engine/nova_engine.gd")
const M := "res://games/novawardens/art/models/"
const BACKDROP := "res://games/novawardens/view3d/nova_backdrop.gd"
const PX := 0.05
const PLAY_LAYER := 2   ## render layer 2: the play pieces, lit by their own key and rim lights
const COLORS := {"squid": Color(1.0, 0.35, 0.9), "crab": Color(0.35, 0.9, 1.0), "octopus": Color(0.55, 1.0, 0.35)}
const BOMB_COLORS := {"rolling": Color(1.0, 0.5, 0.2), "plunger": Color(1.0, 0.25, 0.3), "squiggly": Color(1.0, 0.9, 0.3)}

@export var game: NovaGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _moon: DirectionalLight3D
var _stage: Node3D
var _backdrop: Node3D
var _invaders: Array[Node3D] = []
var _inv_anims: Array = []
var _cannon: Node3D
var _cannon_light: OmniLight3D
var _shot: Node3D
var _bombs: Array[Node3D] = []
var _ufo: Node3D
var _shields: Array[MultiMeshInstance3D] = []
var _fx: NovaFx
var _slow := 0.0   ## seconds of slow motion left (real time), after the cannon is hit
var _time := 0.0
var _shake := 0.0
var _sweep := 0.0
var _recoil := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _mats := {}


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3(p.x * PX, (N.H - p.y) * PX, z)


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.01, 0.01, 0.03)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.25, 0.3, 0.5)
	_env.ambient_light_energy = 0.4
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.9
	_env.glow_bloom = 0.08
	_env.glow_hdr_threshold = 0.9
	_we = WorldEnvironment.new()
	_we.environment = _env
	add_child(_we)
	_moon = DirectionalLight3D.new()
	_moon.rotation_degrees = Vector3(-35, -30, 0)
	_moon.light_color = Color(0.7, 0.8, 1.0)
	_moon.light_energy = 0.6
	_moon.shadow_enabled = true
	add_child(_moon)
	# a key light for the play pieces only (their own render layer): the aliens and the cannon stand out against the
	# night without the backdrop getting any brighter
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-25, 15, 0)
	key.light_color = Color(0.85, 0.9, 1.0)
	key.light_energy = 1.6
	key.light_cull_mask = PLAY_LAYER
	add_child(key)
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(20, 160, 0)
	rim.light_color = Color(0.7, 0.5, 1.0)
	rim.light_energy = 1.2
	rim.light_cull_mask = PLAY_LAYER
	add_child(rim)
	camera = Camera3D.new()
	camera.fov = 36
	camera.far = 4000.0
	camera.current = true
	add_child(camera)
	_fx = NovaFx.new()
	add_child(_fx)
	game.game_started.connect(_on_game)
	if game.engine:
		_on_game(game.engine)


func _mat(col: Color, emit := 0.0, rough := 0.35) -> StandardMaterial3D:
	var key := "%s|%s|%s" % [col, emit, rough]
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	_mats[key] = m
	return m


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _box(size: Vector3, m: Material, at := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = m
	mi.position = at
	return mi


## A fallback alien when the model is missing: a small glowing voxel creature of our own.
func _fallback_alien(kind: String) -> Node3D:
	var n := Node3D.new()
	var col: Color = COLORS[kind]
	var body := _box(Vector3(0.44, 0.26, 0.22), _mat(col.darkened(0.3), 0.6))
	n.add_child(body)
	for sx in [-0.1, 0.1]:
		n.add_child(_box(Vector3(0.07, 0.07, 0.05), _mat(Color(1, 1, 1), 3.0), Vector3(sx, 0.03, 0.12)))
	for lx in [-0.18, -0.06, 0.06, 0.18]:
		var leg := _box(Vector3(0.05, 0.14, 0.05), _mat(col, 1.2), Vector3(lx, -0.18, 0))
		leg.name = "leg"
		n.add_child(leg)
	return n


func _on_game(e: NovaEngine) -> void:
	e.event.connect(_on_event)
	_build(e)


func _build(e: NovaEngine) -> void:
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_invaders.clear()
	_inv_anims.clear()
	_bombs.clear()
	_shields.clear()
	_ufo = null
	# the backdrop
	_backdrop = null
	if ResourceLoader.exists(BACKDROP):
		_backdrop = (load(BACKDROP) as GDScript).new()
		_stage.add_child(_backdrop)
		_backdrop.call("build")
		if _backdrop.has_method("environment_for"):
			var d: Dictionary = _backdrop.call("environment_for")
			_env = _backdrop.call("make_environment", d)
			_we.environment = _env
			_backdrop.call("setup_sun", _moon, d)
	# the ground line
	var ground := _box(Vector3(N.W * PX + 0.4, 0.04, 0.3), _mat(Color(0.3, 1.0, 0.5), 2.2), world(Vector2(N.W * 0.5, 232)))
	_stage.add_child(ground)
	# the fleet
	for i in N.COLS * N.ROWS:
		var kind := e.kind_of(i)
		var n := _scene(kind)
		if n == null:
			n = _fallback_alien(kind)
		_stage.add_child(n)
		_on_play_layer(n)
		_invaders.append(n)
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		if ap and ap.has_animation("march"):
			ap.get_animation("march").loop_mode = Animation.LOOP_NONE
			ap.play("march")
			ap.pause()
		_inv_anims.append(ap)
	# the cannon
	_cannon = _scene("cannon")
	if _cannon == null:
		_cannon = Node3D.new()
		_cannon.add_child(_box(Vector3(0.65, 0.18, 0.3), _mat(Color(0.3, 0.9, 0.6), 0.6)))
		_cannon.add_child(_box(Vector3(0.1, 0.22, 0.1), _mat(Color(0.6, 1.0, 0.8), 2.0), Vector3(0, 0.18, 0)))
	_stage.add_child(_cannon)
	_on_play_layer(_cannon)
	_cannon_light = OmniLight3D.new()
	_cannon_light.light_color = Color(0.4, 1.0, 0.7)
	_cannon_light.light_energy = 0.8
	_cannon_light.omni_range = 2.5
	_cannon_light.position = Vector3(0, 0.3, 0.4)
	_cannon.add_child(_cannon_light)
	# the shot
	_shot = _scene("shot")
	if _shot == null:
		_shot = _box(Vector3(0.05, 0.3, 0.05), _mat(Color(0.7, 1.0, 0.9), 4.0))
	var sl := OmniLight3D.new()
	sl.light_color = Color(0.5, 1.0, 0.8)
	sl.light_energy = 1.2
	sl.omni_range = 2.0
	_shot.add_child(sl)
	_shot.visible = false
	_stage.add_child(_shot)
	# the shields: one crystal cube per pixel
	var cube := BoxMesh.new()
	cube.size = Vector3.ONE * PX * 0.96
	var sm := StandardMaterial3D.new()
	sm.albedo_color = Color(0.2, 0.9, 0.55)
	sm.emission_enabled = true
	sm.emission = Color(0.2, 1.0, 0.55)
	sm.emission_energy_multiplier = 0.7
	sm.roughness = 0.15
	sm.metallic = 0.2
	for s in 4:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = cube
		mm.instance_count = N.SHIELD_W * N.SHIELD_H
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = sm
		_stage.add_child(mmi)
		_shields.append(mmi)
		_refresh_shield(e, s)
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


## Lays out a shield's cubes from its bitmap (a destroyed pixel's cube is scaled away).
func _refresh_shield(e: NovaEngine, s: int) -> void:
	var mm := _shields[s].multimesh
	var bmp: PackedByteArray = e.shields[s]
	var sx := N.shield_x(s)
	for y in N.SHIELD_H:
		for x in N.SHIELD_W:
			var k := y * N.SHIELD_W + x
			var p := world(Vector2(sx + x + 0.5, N.SHIELD_Y + y + 0.5))
			var sc := 1.0 if bmp[k] == 1 else 0.0
			mm.set_instance_transform(k, Transform3D(Basis().scaled(Vector3.ONE * sc), p))


## Puts a piece's meshes on the play layer as well (so the play lights reach them; the camera sees both layers).
func _on_play_layer(n: Node) -> void:
	for v in n.find_children("*", "VisualInstance3D", true, false):
		(v as VisualInstance3D).layers |= PLAY_LAYER
	if n is VisualInstance3D:
		(n as VisualInstance3D).layers |= PLAY_LAYER


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hit":
			# the alien shatters: voxel shards in its colour, a white core, a shockwave ring, sparks and a flash
			var col: Color = COLORS[d["kind"]]
			var p := world(d["pos"], 0.1)
			_fx.shards(p, col, 18, 4.0, 1.2, 1.0)
			_fx.ring(p, col.lerp(Color.WHITE, 0.3), 1.6, 0.4, 4.0)
			_fx.burst(p, col, 36, 5.0, 0.7, 0.14, 1.0, -2.0, 1.0, "glow")
			_fx.burst(p, Color(1, 1, 1), 12, 2.5, 0.3, 0.22, 1.0, 0.0, 1.0, "glow")
			_fx.flash(p + Vector3(0, -1.5, 1.5), col, 2.4)
			_shake = maxf(_shake, 0.18)
		"ufo_hit":
			var p := world(d["pos"], 0.1)
			_fx.shards(p, Color(1.0, 0.45, 0.3), 30, 5.0, 1.4, 1.3)
			_fx.ring(p, Color(1.0, 0.7, 0.4), 2.2, 0.6, 4.0)
			_fx.ring(p, Color(1.0, 0.4, 0.3), 1.2, 0.4, 3.0)
			_fx.burst(p, Color(1.0, 0.4, 0.3), 60, 5.0, 1.0, 0.1, 1.0, -2.0, 1.0, "glow")
			_fx.flash(p + Vector3(0, -2.0, 1.5), Color(1.0, 0.6, 0.4), 3.0)
			_shake = 0.4
			if _backdrop and _backdrop.has_method("flash"):
				_backdrop.call("flash", p)
		"shield":
			_refresh_shield(e, d["index"])
			_fx.burst(world(d["pos"], 0.1), Color(0.3, 1.0, 0.6), 10, 2.0, 0.4, 0.05, 1.0, -4.0, 1.0, "glow")
		"bomb_hit":
			# shot meets bomb: an electric crackle, blue-white sparks and a sharp little ring
			var p := world(d["pos"], 0.1)
			_fx.burst(p, Color(0.6, 0.85, 1.0), 40, 6.0, 0.4, 0.11, 1.0, 0.0, 1.0, "glow")
			_fx.burst(p, Color(1.0, 0.9, 0.6), 14, 3.0, 0.5, 0.16, 1.0, -3.0, 1.0, "glow")
			_fx.shards(p, Color(0.7, 0.9, 1.0), 8, 3.0, 0.8, 0.6)
			_fx.ring(p, Color(0.6, 0.85, 1.0), 1.4, 0.3, 5.0)
			_fx.flash(p + Vector3(0, -1.5, 1.2), Color(0.6, 0.85, 1.0), 1.8)
			_shake = maxf(_shake, 0.15)
		"miss", "bomb_ground":
			_fx.burst(world(d["pos"], 0.1), Color(1.0, 0.8, 0.5), 8, 1.5, 0.3, 0.05, 1.0, -3.0, 1.0, "glow")
		"shot":
			_recoil = 1.0
		"die":
			# the cannon goes up: a white flash and a big shockwave, hull shards, fire, a smoke column, then two
			# secondary blasts; everything slows for a moment
			var p := world(d["pos"], 0.2)
			_fx.flash(p + Vector3(0, -1.5, 1.5), Color(1.0, 0.8, 0.5), 4.0)
			_fx.ring(p, Color(1.0, 0.85, 0.6), 4.5, 0.8, 5.0)
			_fx.ring(p, Color(0.4, 1.0, 0.7), 2.4, 0.5, 4.0)
			_fx.shards(p, Color(0.8, 0.95, 1.0), 30, 5.5, 1.6, 1.6)
			_fx.shards(p, Color(1.0, 0.55, 0.2), 22, 4.5, 1.3, 1.4)
			_fx.burst(p, Color(1.0, 0.6, 0.25), 70, 5.5, 1.0, 0.22, 1.0, -2.0, 1.0, "glow")
			_fx.burst(p, Color(0.35, 0.3, 0.3), 36, 1.8, 2.4, 0.6, 0.0, 1.5, 1.0, "smoke")
			for k in 2:
				get_tree().create_timer(0.25 + 0.2 * k).timeout.connect(func():
					var q := p + Vector3((0.35 if k == 0 else -0.3), 0.15, 0.1)
					_fx.burst(q, Color(1.0, 0.7, 0.3), 34, 3.5, 0.7, 0.18, 1.0, -2.0, 1.0, "glow")
					_fx.ring(q, Color(1.0, 0.75, 0.4), 1.8, 0.4, 4.0)
					_shake = maxf(_shake, 0.5))
			_shake = 1.0
			_slow = 0.6
		"step":
			for i in _inv_anims.size():
				var ap: AnimationPlayer = _inv_anims[i]
				if ap:
					ap.seek(ap.current_animation_length * 0.5 * e.frame, true)
		"cleared":
			_sweep = 1.0
		"wave":
			for s in 4:
				_refresh_shield(e, s)


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _invaders.is_empty():
		return
	var lowest := 0.0
	for i in _invaders.size():
		var n := _invaders[i]
		n.visible = e.alive[i] == 1
		if not n.visible:
			continue
		var p := e.invader_pos(i) + Vector2(N.INV_W, N.INV_H) * 0.5
		lowest = maxf(lowest, p.y)
		n.position = world(p) + Vector3(0, sin(_time * 3.0 + i * 0.7) * 0.02, 0)
		n.rotation.y = sin(_time * 1.3 + i) * 0.15
		if _inv_anims[i] == null:
			# the fallback's legs step with the march
			for leg in n.get_children():
				if leg.name.begins_with("leg"):
					leg.rotation.z = 0.35 * (1.0 if e.frame == 0 else -1.0)
	# the city's alarm rises as the fleet comes down
	if _backdrop and _backdrop.has_method("alarm"):
		_backdrop.call("alarm", clampf((lowest - 120.0) / 90.0, 0.0, 1.0))
	# the cannon
	_recoil = maxf(0.0, _recoil - delta * 8.0)
	_cannon.visible = not (e.phase == N.Phase.DYING and fmod(_time, 0.16) < 0.08)
	_cannon.position = world(Vector2(e.cannon_x + N.CANNON_W * 0.5, N.CANNON_Y + 4)) - Vector3(0, _recoil * 0.05, 0)
	_cannon.rotation.z = lerp_angle(_cannon.rotation.z, -e.move_x * 0.12, 1.0 - exp(-delta * 10.0))
	# the shot
	_shot.visible = not e.shot.is_empty()
	if _shot.visible:
		_shot.position = world(e.shot["pos"], 0.05)
	# bombs
	while _bombs.size() > e.bombs.size():
		_bombs.pop_back().queue_free()
	for i in e.bombs.size():
		var b: Dictionary = e.bombs[i]
		if i >= _bombs.size() or _bombs[i].get_meta("kind") != b["kind"]:
			var bn := _scene("bomb_" + b["kind"])
			if bn == null:
				bn = _box(Vector3(0.08, 0.2, 0.08), _mat(BOMB_COLORS[b["kind"]], 3.0))
			bn.set_meta("kind", b["kind"])
			var bl := OmniLight3D.new()
			bl.light_color = BOMB_COLORS[b["kind"]]
			bl.light_energy = 0.6
			bl.omni_range = 1.2
			bn.add_child(bl)
			if i < _bombs.size():
				_bombs[i].queue_free()
				_bombs[i] = bn
			else:
				_bombs.append(bn)
			_stage.add_child(bn)
		var bn2 := _bombs[i]
		bn2.position = world(b["pos"], 0.05)
		match b["kind"]:
			"rolling": bn2.rotation.y = _time * 12.0
			"squiggly": bn2.rotation.z = sin(_time * 25.0) * 0.5
			_: bn2.rotation.y = _time * 6.0
	# the mothership
	if not e.ufo.is_empty():
		if _ufo == null:
			_ufo = _scene("mothership")
			if _ufo == null:
				_ufo = _box(Vector3(0.8, 0.2, 0.4), _mat(Color(1.0, 0.3, 0.3), 2.0))
			var ul := OmniLight3D.new()
			ul.light_color = Color(1.0, 0.4, 0.4)
			ul.light_energy = 1.5
			ul.omni_range = 3.0
			_ufo.add_child(ul)
			_stage.add_child(_ufo)
		_ufo.position = world(Vector2(e.ufo["x"] + 8.0, N.UFO_Y + 4))
		var lights := _ufo.find_child("lights", true, false) as Node3D
		if lights:
			lights.rotation.y = _time * 4.0
	elif _ufo:
		_ufo.queue_free()
		_ufo = null
	_shake = maxf(0.0, _shake - delta * 1.6)
	_sweep = maxf(0.0, _sweep - delta / 2.5)
	# a moment of slow motion after the cannon is hit (the game's ticks slow with it; real time counts it down)
	if _slow > 0.0:
		if Engine.time_scale > 1.01:
			_slow = 0.0   # a capture is fast-forwarding: leave its time alone
		else:
			Engine.time_scale = 0.35
			_slow -= delta / 0.35
			if _slow <= 0.0:
				Engine.time_scale = 1.0
	_place_camera(delta, false, lowest)


func _place_camera(delta: float, snap := false, lowest := 120.0) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(5.9, 6.4 / aspect)  # half the field (12.8 high, 11.2 wide) with a little margin
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var cx: float = (e.cannon_x + N.CANNON_W * 0.5) * PX if e else 5.6
	var dread := clampf((lowest - 120.0) / 90.0, 0.0, 1.0)
	var look := Vector3(5.6 + (cx - 5.6) * 0.12, 6.4 - dread * 0.6, 0.0)
	var pos := look + Vector3(sin(_time * 0.13) * 0.5 + (cx - 5.6) * 0.1, -1.2 - dread * 0.8 + sin(_time * 0.1) * 0.2, dist)
	if _sweep > 0.0:
		var k := sin(_sweep * PI)
		pos += Vector3(sin((1.0 - _sweep) * TAU) * 2.5, 1.0 * k, -2.0 * k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)


func _exit_tree() -> void:
	if _slow > 0.0:
		Engine.time_scale = 1.0
