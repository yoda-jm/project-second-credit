class_name FruitburrowView3D
extends Node3D
## Fruitburrow in 3D: the garden is a vertical slice of soil seen from the front, like an ant farm. Dug cells open
## onto a darker back wall; fruit and apples sit half out of the soil; the garden surface, trees and sky are on
## top. Cell (x, y) is at (x, -y, 0). Each garden brings the light a little closer to dusk.

const E = preload("res://games/fruitburrow/engine/fruitburrow_engine.gd")
const T = preload("res://games/fruitburrow/engine/garden_map.gd").Terrain
const MODELS := "res://games/fruitburrow/art/models/"
const DECOR := "res://games/bastion/art/models/"
const FRUIT_COLORS: Array[Color] = [Color(0.85, 0.08, 0.12), Color(1.0, 0.85, 0.2), Color(0.7, 0.85, 0.25),
	Color(0.45, 0.15, 0.6), Color(0.95, 0.15, 0.2)]
## sky top, horizon, sun colour, sun energy, sun pitch for gardens 1, 2, 3 (then it loops)
const TIMES_OF_DAY := [
	[Color(0.3, 0.55, 0.9), Color(0.8, 0.88, 0.95), Color(1.0, 0.96, 0.88), 1.2, -55.0],
	[Color(0.35, 0.5, 0.85), Color(0.98, 0.82, 0.6), Color(1.0, 0.85, 0.65), 1.1, -35.0],
	[Color(0.25, 0.25, 0.55), Color(1.0, 0.55, 0.35), Color(1.0, 0.62, 0.4), 0.9, -18.0],
]

@export var game: FruitburrowGame

var _camera: Camera3D
var _sun: DirectionalLight3D
var _sky: ProceduralSkyMaterial
var _fx: FruitburrowEffects
var _soil: MultiMeshInstance3D
var _stone: MultiMeshInstance3D
var _soil_index := {}  ## Vector2i -> instance index
var _soil_scale := {}  ## Vector2i -> current scale (shrinks to 0 when dug)
var _board := Node3D.new()
var _fruit_nodes := {}  ## Vector2i -> Node3D
var _apple_nodes := {}  ## apple id -> Node3D
var _monster_nodes := {}  ## monster id -> Node3D
var _player: Node3D
var _ball: Node3D
var _ball_trail: CPUParticles3D
var _cam_base := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _time := 0.0
var _shake := 0.0
var _last_player_pos := Vector3.ZERO


func _ready() -> void:
	_build_world()
	_fx = FruitburrowEffects.new()
	add_child(_fx)
	add_child(_board)
	game.garden_started.connect(_on_garden)
	if game.engine:
		_on_garden(game.engine)


# ------------------------------------------------------------------ world

func _build_world() -> void:
	_sky = ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = _sky
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.45
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.95
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_hdr_threshold = 1.0
	env.ssao_enabled = true
	env.ssao_intensity = 2.5
	env.fog_enabled = true
	env.fog_light_color = Color(0.8, 0.85, 0.95)
	env.fog_density = 0.0015
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.25
	env.adjustment_contrast = 1.1
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 60.0
	_sun.shadow_bias = 0.05
	_sun.shadow_normal_bias = 1.5
	_sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	add_child(_sun)
	_camera = Camera3D.new()
	_camera.fov = 38
	_camera.current = true
	add_child(_camera)


func _set_time_of_day(level: int) -> void:
	var t: Array = TIMES_OF_DAY[(level - 1) % TIMES_OF_DAY.size()]
	_sky.sky_top_color = t[0]
	_sky.sky_horizon_color = t[1]
	_sky.ground_horizon_color = t[1].darkened(0.2)
	_sky.ground_bottom_color = Color(0.2, 0.18, 0.15)
	_sun.light_color = t[2]
	_sun.light_energy = t[3]
	_sun.rotation_degrees = Vector3(t[4], -30.0, 0)


func _on_garden(e: FruitburrowEngine) -> void:
	for n in _board.get_children():
		n.queue_free()
	_fruit_nodes.clear()
	_apple_nodes.clear()
	_monster_nodes.clear()
	_soil_index.clear()
	_soil_scale.clear()
	if not e.event.is_connected(_on_event):
		e.event.connect(_on_event)
	_set_time_of_day(e.level)
	_build_board(e)
	_fit_camera(e)


func _build_board(e: FruitburrowEngine) -> void:
	var w := e.map.w
	var h := e.map.h
	var soil_mat := Pbr.material("soil", Color(0.95, 0.8, 0.65), 1.2)
	var back_mat := Pbr.material("soil", Color(0.42, 0.32, 0.25), 1.2)
	var frame_mat := Pbr.material("dark_rock", Color(0.55, 0.5, 0.46), 1.0)
	var grass_mat := Pbr.material("grass_lush", Color(0.85, 1.0, 0.8), 1.5)
	var rock_mat := Pbr.material("rock", Color(0.75, 0.73, 0.7), 1.5)
	# soil and stone blocks
	var box := BoxMesh.new()
	box.size = Vector3.ONE
	var soil_cells: Array[Vector2i] = []
	var stone_cells: Array[Vector2i] = []
	for y in h:
		for x in w:
			var c := Vector2i(x, y)
			match e.at(c):
				T.SOIL: soil_cells.append(c)
				T.STONE: stone_cells.append(c)
	_soil = _multimesh(box, soil_mat, soil_cells.size())
	for i in soil_cells.size():
		_soil_index[soil_cells[i]] = i
		_soil_scale[soil_cells[i]] = 1.0
		_soil.multimesh.set_instance_transform(i, Transform3D(Basis(), _cell_pos(soil_cells[i])))
	var rock := BoxMesh.new()
	rock.size = Vector3(0.98, 0.98, 1.02)
	_stone = _multimesh(rock, rock_mat, stone_cells.size())
	for i in stone_cells.size():
		_stone.multimesh.set_instance_transform(i, Transform3D(Basis(), _cell_pos(stone_cells[i])))
	# the back wall of the tunnels, the frame around the slice, the garden surface above
	_block(Vector3(w * 0.5 - 0.5, -h * 0.5 + 0.5, -0.75), Vector3(w, h, 0.5), back_mat)
	_block(Vector3(-4.5, -h * 0.5 + 0.5, -2.0), Vector3(8, h, 5), soil_mat.duplicate())
	_block(Vector3(w + 3.5, -h * 0.5 + 0.5, -2.0), Vector3(8, h, 5), soil_mat.duplicate())
	_block(Vector3(w * 0.5 - 0.5, -h - 1.5, -2.0), Vector3(w + 16, 4, 5), frame_mat)
	_block(Vector3(w * 0.5 - 0.5, 0.65, -9.5), Vector3(w + 40, 0.3, 20), grass_mat)
	_decorate(e)
	# fruit and apples
	for c in e.fruit:
		var n := _fruit_node(e.fruit[c])
		n.position = _cell_pos(c) + Vector3(0, 0, 0.42)
		n.rotation.y = randf_range(-0.5, 0.5)
		_board.add_child(n)
		_fruit_nodes[c] = n
	for a in e.apples:
		var n := _apple_node()
		n.position = _cell_pos(a["cell"]) + Vector3(0, 0, 0.35)
		_board.add_child(n)
		_apple_nodes[a["id"]] = n
	_player = _player_node()
	_board.add_child(_player)
	_ball = _ball_node()
	_board.add_child(_ball)


func _decorate(e: FruitburrowEngine) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = e.level * 17
	var top := 0.8
	for i in 22:
		var x := rng.randf_range(-12.0, e.map.w + 12.0)
		var z := rng.randf_range(-16.0, -2.5)
		var kind: String = ["tree.glb", "pine.glb", "bush.glb", "tree.glb"][rng.randi_range(0, 3)]
		var n := _scene(DECOR + kind)
		n.position = Vector3(x, top, z)
		n.rotation.y = rng.randf() * TAU
		n.scale = Vector3.ONE * rng.randf_range(1.4, 2.4) * (0.6 if kind == "bush.glb" else 1.0)
		_board.add_child(n)
	for i in 60:
		var n := _scene(DECOR + "grass_tuft.glb")
		n.position = Vector3(rng.randf_range(-6.0, e.map.w + 6.0), top, rng.randf_range(-2.2, 0.3))
		n.rotation.y = rng.randf() * TAU
		n.scale = Vector3.ONE * rng.randf_range(0.8, 1.4)
		_board.add_child(n)


func _cell_pos(c: Vector2) -> Vector3:
	return Vector3(c.x, -c.y, 0)


func _block(pos: Vector3, size: Vector3, mat: Material) -> void:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	_board.add_child(mi)


func _multimesh(mesh: Mesh, mat: Material, count: int) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = count
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	inst.material_override = mat
	_board.add_child(inst)
	return inst


func _scene(path: String) -> Node3D:
	var n: Node3D = (load(path) as PackedScene).instantiate()
	_dress(n)
	return n


## Swaps the flat Blender materials of a model for the shared PBR ones, by material name.
static func _dress(node: Node) -> void:
	var swap := {
		"pine": Pbr.material("grass", Color(0.35, 0.55, 0.35), 3.0),
		"leaves": Pbr.material("grass", Color(0.55, 0.8, 0.45), 3.0),
		"bush": Pbr.material("grass", Color(0.45, 0.7, 0.4), 3.0),
		"blade": Pbr.material("grass", Color(0.7, 0.95, 0.55), 4.0),
		"wood": Pbr.material("planks", Color(0.62, 0.42, 0.26), 2.0),
	}
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and swap.has(mat.resource_name):
				m.set_surface_override_material(i, swap[mat.resource_name])


## Pulls the camera back until the whole garden (and a strip of the surface) fits under the HUD.
func _fit_camera(e: FruitburrowEngine) -> void:
	var w := float(e.map.w)
	var h := float(e.map.h)
	_cam_look = Vector3(w * 0.5 - 0.5, -h * 0.5 + 1.2, 0)
	var dir := Vector3(0, 0.28, 1).normalized()
	var vp := get_viewport().get_visible_rect().size
	var corners := [Vector3(-0.8, 1.5, 0.5), Vector3(w - 0.2, 1.5, 0.5), Vector3(-0.8, -h + 0.3, 0.5), Vector3(w - 0.2, -h + 0.3, 0.5)]
	for dist in range(12, 80):
		_camera.position = _cam_look + dir * dist
		_camera.look_at(_cam_look)
		var ok := true
		for c in corners:
			var sp := _camera.unproject_position(c)
			if sp.x < 20 or sp.x > vp.x - 20 or sp.y < 120 or sp.y > vp.y - 30:
				ok = false
				break
		if ok:
			break
	_cam_base = _camera.position


# ------------------------------------------------------------------ placeholder shapes (Blender models later)

func _sphere(r: float, col: Color, rough := 0.35, emit := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	mi.mesh = s
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	mi.material_override = m
	return mi


func _model_or(path: String, fallback: Callable) -> Node3D:
	if ResourceLoader.exists(path):
		return _scene(path)
	return fallback.call()


func _fruit_node(f: int) -> Node3D:
	var names := ["cherries", "banana", "pear", "grapes", "strawberry"]
	return _model_or(MODELS + names[f] + ".glb", func(): return _sphere(0.28, FRUIT_COLORS[f], 0.25))


func _apple_node() -> Node3D:
	return _model_or(MODELS + "apple.glb", func(): return _sphere(0.4, Color(0.8, 0.1, 0.08), 0.3))


func _player_node() -> Node3D:
	return _model_or(MODELS + "gardener.glb", func():
		var n := Node3D.new()
		var body := _sphere(0.3, Color(0.2, 0.45, 0.85), 0.6)
		body.position.y = -0.05
		n.add_child(body)
		var head := _sphere(0.2, Color(1.0, 0.8, 0.6), 0.6)
		head.position.y = 0.3
		n.add_child(head)
		return n)


func _monster_node(kind: int) -> Node3D:
	var path := MODELS + ("plum.glb" if kind == E.Kind.PLUM else "digger.glb")
	return _model_or(path, func():
		var n := Node3D.new()
		n.add_child(_sphere(0.36, Color(0.45, 0.15, 0.55) if kind == E.Kind.PLUM else Color(0.5, 0.33, 0.2), 0.3))
		for s in [-1, 1]:
			var eye := _sphere(0.09, Color.WHITE, 0.2)
			eye.position = Vector3(0.12 * s, 0.1, 0.3)
			n.add_child(eye)
		return n)


func _ball_node() -> Node3D:
	var n := _sphere(0.16, Color(1.0, 0.85, 0.3), 0.2, 3.0)
	n.visible = false
	_ball_trail = CPUParticles3D.new()
	_ball_trail.amount = 40
	_ball_trail.lifetime = 0.35
	_ball_trail.local_coords = false
	_ball_trail.gravity = Vector3.ZERO
	_ball_trail.initial_velocity_min = 0.0
	_ball_trail.initial_velocity_max = 0.2
	var q := QuadMesh.new()
	q.size = Vector2(0.35, 0.35)
	_ball_trail.mesh = q
	_ball_trail.material_override = Fx.material("glow", Color(1.0, 0.75, 0.3))
	_ball_trail.scale_amount_curve = Fx.size_curve(false)
	_ball_trail.emitting = false
	n.add_child(_ball_trail)
	return n


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"dig":
			var c: Vector2i = d["cell"]
			_fx.crumbs(_cell_pos(c) + Vector3(0, 0, 0.3), d["by"] == "player")
		"fruit":
			var c: Vector2i = d["cell"]
			if _fruit_nodes.has(c):
				var n: Node3D = _fruit_nodes[c]
				_fruit_nodes.erase(c)
				var tw := create_tween()
				tw.tween_property(n, "scale", Vector3.ONE * 1.6, 0.08)
				tw.tween_property(n, "scale", Vector3.ZERO, 0.18)
				tw.tween_callback(n.queue_free)
				_fx.sparkle(n.position, FRUIT_COLORS[d["fruit"]])
		"apple_break":
			if _apple_nodes.has(d["id"]):
				var n: Node3D = _apple_nodes[d["id"]]
				_apple_nodes.erase(d["id"])
				_fx.splat(n.position, Color(0.95, 0.85, 0.55))
				n.queue_free()
				_shake = 0.5
		"apple_land":
			_shake = 0.3
			if _apple_nodes.has(d["id"]):
				_fx.dust(_apple_nodes[d["id"]].position + Vector3(0, -0.4, 0), 8)
		"squash":
			_fx.splat(_cell_pos(d["pos"]), Color(0.6, 0.2, 0.7))
			_shake = 0.5
		"monster_hit":
			_fx.pop(_cell_pos(d["pos"]))
		"death":
			_fx.pop(_cell_pos(d["pos"]))
			_shake = 0.8
		"clear":
			_fx.confetti(_cam_look + Vector3(0, 3, 2))
		"transform":
			_fx.dust(_cell_pos(d["cell"]), 12)
		"ball_lost":
			_fx.sparkle(_cell_pos(d["pos"]), Color(1.0, 0.8, 0.3))


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	var e := game.engine
	if e == null or _player == null:
		return
	_time += delta
	_update_soil(e, delta)
	_update_player(e, delta)
	_update_monsters(e, delta)
	_update_apples(e)
	_update_ball(e)
	# camera: a slow sway, a little shake on impacts
	_shake = maxf(0.0, _shake - delta * 2.5)
	var drift := Vector3(sin(_time * 0.13) * 0.5, sin(_time * 0.09) * 0.25, 0)
	var s := _shake * _shake * (0.25 if Settings.camera_shake else 0.0)
	var jitter := Vector3(sin(_time * 63.0), sin(_time * 57.0), 0) * s
	_camera.position = _cam_base + drift + jitter
	_camera.look_at(_cam_look + drift * 0.3)


func _update_soil(e: FruitburrowEngine, delta: float) -> void:
	for c in _soil_scale:
		var k: float = _soil_scale[c]
		if k > 0.0 and e.at(c) != T.SOIL:  # dug: the block crumbles away
			k = maxf(0.0, k - delta * 5.0)
			_soil_scale[c] = k
			var b := Basis().scaled(Vector3(k, k, 1.0) if k > 0.0 else Vector3.ZERO)
			_soil.multimesh.set_instance_transform(_soil_index[c], Transform3D(b, _cell_pos(c)))


func _update_player(e: FruitburrowEngine, delta: float) -> void:
	var pos := _cell_pos(e.pos_of(e.player))
	var moving := pos.distance_to(_last_player_pos) > 0.001
	_last_player_pos = pos
	var dying := e.phase == E.Phase.DYING
	var face: Vector2i = e.player["face"]
	var yaw := 0.0
	if face.x != 0:
		yaw = PI * 0.5 * face.x
	var bob := absf(sin(_time * 14.0)) * 0.08 if moving else 0.0
	_player.position = pos + Vector3(0, -0.2 + bob, 0.05)
	_player.rotation.y = lerp_angle(_player.rotation.y, yaw, 1.0 - exp(-delta * 16.0))
	var target_scale := Vector3.ONE if not dying else Vector3(1.4, 0.2, 1.4)
	if e.phase == E.Phase.GAME_OVER:
		target_scale = Vector3.ZERO
	_player.scale = _player.scale.lerp(target_scale, 1.0 - exp(-delta * 10.0))


func _update_monsters(e: FruitburrowEngine, delta: float) -> void:
	var alive := {}
	for m in e.monsters:
		var id: int = m["id"]
		alive[id] = true
		var n: Node3D = _monster_nodes.get(id)
		if n == null or n.get_meta("kind", -1) != m["kind"]:
			if n:
				n.queue_free()
			n = _monster_node(m["kind"])
			n.set_meta("kind", m["kind"])
			n.scale = Vector3.ONE * 0.01
			_board.add_child(n)
			_monster_nodes[id] = n
		var pos := _cell_pos(e.pos_of(m))
		var dir := Vector3(m["to"].x - m["cell"].x, 0, 0)
		var wob := sin(_time * 10.0 + id) * 0.06
		n.position = pos + Vector3(0, -0.12 + absf(wob), 0.05)
		if dir.x != 0.0:
			n.rotation.y = lerp_angle(n.rotation.y, PI * 0.5 * dir.x * 0.6, 1.0 - exp(-delta * 10.0))
		n.scale = n.scale.lerp(Vector3(1.0 + wob, 1.0 - wob, 1.0 + wob), 1.0 - exp(-delta * 8.0))
	for id in _monster_nodes.keys():
		if not alive.has(id):
			var n: Node3D = _monster_nodes[id]
			_monster_nodes.erase(id)
			n.queue_free()


func _update_apples(e: FruitburrowEngine) -> void:
	for a in e.apples:
		var n: Node3D = _apple_nodes.get(a["id"])
		if n == null:
			continue
		var p := Vector3(a["cell"].x, -a["y"], 0.35 if a["state"] == E.Apple.REST and e.at(a["cell"]) == T.SOIL else 0.05)
		if a["state"] == E.Apple.WOBBLE:
			n.rotation.z = sin(_time * 38.0) * 0.18
		elif a["state"] == E.Apple.FALL:
			n.rotation.z += 0.05
		else:
			n.rotation.z = 0.0
		n.position = n.position.lerp(p, 0.5) if a["state"] != E.Apple.FALL else p


func _update_ball(e: FruitburrowEngine) -> void:
	var flying := not e.ball.is_empty()
	_ball.visible = flying
	_ball_trail.emitting = flying
	if flying:
		_ball.position = _cell_pos(e.pos_of(e.ball)) + Vector3(0, -0.15, 0.1)
