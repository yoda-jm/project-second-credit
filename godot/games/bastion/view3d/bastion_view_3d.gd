class_name BastionView3D
extends Node3D
## 3D coastal diorama of a Bastion Coast game. Cell (x, y) sits at (x, 0, y). Reads the engine each frame and
## reacts to its events (shots, impacts, sinking ships). Also turns mouse positions into map cells.

const MODELS := "res://games/bastion/art/models/"
const LAND_H := 0.35
const PLAYER := Color(0.35, 0.65, 1.0)

@export var game: BastionGame

var _camera: Camera3D
var _land: MultiMeshInstance3D
var _walls: MultiMeshInstance3D
var _rubble: MultiMeshInstance3D
var _balls: MultiMeshInstance3D
var _ghost: MultiMeshInstance3D
var _ghost_mat: StandardMaterial3D
var _cross: MeshInstance3D
var _castles: Array[Node3D] = []
var _cannons := {}  ## Vector2i -> Node3D
var _ships := {}    ## ship id -> Node3D
var _sinking: Array = []  ## [node, age]
var _fx: BastionEffects
var _time := 0.0
var _shake := 0.0
var _cam_base := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _land_dirty := true
var _decor := {}  ## prop name -> MultiMeshInstance3D
var _sea_mat: ShaderMaterial
var _zone: MultiMeshInstance3D   ## territory overlay
var _edge: MultiMeshInstance3D   ## glowing territory border
var _zone_pulse := 0.0
var _last_enclosed := 0
var _wakes := {}  ## ship id -> CPUParticles3D
var _holes: MultiMeshInstance3D
var _blocked_cache := ""
var _blocked_t := 0.0


func _ready() -> void:
	game.view = self
	_build_world()
	_fx = BastionEffects.new()
	add_child(_fx)
	game.started.connect(_on_started)
	if game.engine:
		_on_started(game.engine)


func _build_world() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.25, 0.45, 0.8)
	sky_mat.sky_horizon_color = Color(0.75, 0.82, 0.9)
	sky_mat.ground_horizon_color = Color(0.6, 0.7, 0.8)
	var sky := Sky.new()
	sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.25
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.9
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.25
	env.glow_hdr_threshold = 1.1
	env.ssao_enabled = true
	env.ssr_enabled = true  # the sea reflects the coast, castles and ships
	env.ssr_max_steps = 48
	env.ssr_fade_in = 0.2
	env.ssr_fade_out = 2.0
	env.fog_enabled = true
	env.fog_light_color = Color(0.7, 0.8, 0.9)
	env.fog_density = 0.0015
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.3
	env.adjustment_contrast = 1.2
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -35, 0)
	sun.light_color = Color(1.0, 0.95, 0.85)
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 80.0
	sun.shadow_bias = 0.08
	sun.shadow_normal_bias = 2.5  # the steep cone roofs otherwise shimmer with shadow acne
	sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY  # no sun disc in the sky: no hard blob reflected in the sea
	add_child(sun)
	_camera = Camera3D.new()
	_camera.fov = 40
	_camera.current = true
	add_child(_camera)

	var sea := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(160, 120)
	plane.subdivide_width = 120
	plane.subdivide_depth = 90
	sea.mesh = plane
	var wm := ShaderMaterial.new()
	wm.shader = load("res://games/bastion/shaders/water.gdshader")
	_sea_mat = wm
	wm.set_shader_parameter("normal_map", load("res://core/art/textures/water/normal.png"))
	sea.material_override = wm
	sea.position = Vector3(20, 0.0, 14)
	sea.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(sea)

	var tile := BoxMesh.new()
	tile.size = Vector3(1.0, LAND_H + 0.3, 1.0)
	var lm := ShaderMaterial.new()
	lm.shader = load("res://games/bastion/shaders/land.gdshader")
	for t in [["grass", "grass"], ["lush", "grass_lush"], ["sand", "beach_sand"], ["rock", "rock"]]:
		lm.set_shader_parameter(t[0] + "_albedo", load(Pbr.ROOT + t[1] + "/albedo.jpg"))
		lm.set_shader_parameter(t[0] + "_normal", load(Pbr.ROOT + t[1] + "/normal.jpg"))
	_land = _mm(tile, lm, true)
	_walls = _mm(load(MODELS + "wall.obj"), Pbr.material("stone_bricks", Color(1.0, 0.96, 0.9), 1.4), false)
	var rub: StandardMaterial3D = Pbr.material("rock", Color(0.35, 0.3, 0.28), 2.0).duplicate()
	rub.emission_enabled = true
	rub.emission = Color(1.0, 0.35, 0.05)
	rub.emission_energy_multiplier = 0.8
	_rubble = _mm(load(MODELS + "rubble.obj"), rub, false)
	var bm := StandardMaterial3D.new()
	bm.albedo_color = Color(0.1, 0.1, 0.1)
	bm.metallic = 0.8
	bm.roughness = 0.3
	_balls = _mm(load(MODELS + "ball.obj"), bm, false)
	_ghost_mat = StandardMaterial3D.new()
	_ghost_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ghost_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ghost_mat.vertex_color_use_as_albedo = true
	var gbox := BoxMesh.new()
	gbox.size = Vector3(0.94, 0.5, 0.94)
	_ghost = _mm(gbox, _ghost_mat, false)
	_ghost.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var zq := QuadMesh.new()
	zq.size = Vector2(1, 1)
	zq.orientation = PlaneMesh.FACE_Y
	var zm := StandardMaterial3D.new()
	zm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	zm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	zm.vertex_color_use_as_albedo = true
	zm.albedo_color = Color(0.35, 0.65, 1.0, 1.0)
	_zone = _mm(zq, zm, false)
	_zone.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var eb := BoxMesh.new()
	eb.size = Vector3(1.0, 0.06, 0.08)
	var em := StandardMaterial3D.new()
	em.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	em.vertex_color_use_as_albedo = true
	em.albedo_color = Color(1.4, 2.2, 3.5)
	_edge = _mm(eb, em, false)
	_edge.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var hb := CylinderMesh.new()  # a glowing beacon standing in each hole
	hb.top_radius = 0.3
	hb.bottom_radius = 0.42
	hb.height = 1.6
	var hm := StandardMaterial3D.new()
	hm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	hm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	hm.vertex_color_use_as_albedo = true
	_holes = _mm(hb, hm, false)
	_holes.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_holes.multimesh.instance_count = 64
	for prop in ["grass_tuft", "bush", "stones", "pine", "tree"]:
		var mmi := _mm(_mesh_of(MODELS + prop + ".glb"), null, false)
		_decor[prop] = mmi
	_cross = MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.55
	torus.outer_radius = 0.7
	_cross.mesh = torus
	var cm := StandardMaterial3D.new()
	cm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	cm.albedo_color = Color(1.0, 0.3, 0.2)
	cm.emission_enabled = true
	cm.emission = Color(1.0, 0.3, 0.2)
	cm.emission_energy_multiplier = 2.0
	_cross.material_override = cm
	add_child(_cross)


func _mm(mesh: Mesh, mat: Material, colors: bool) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = mesh
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	if mat:
		inst.material_override = mat
	add_child(inst)
	return inst


static func _mesh_of(path: String) -> Mesh:
	var root := (load(path) as PackedScene).instantiate()
	_dress(root)
	var found: Mesh = null
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		found = mi.mesh.duplicate()
		for i in found.get_surface_count():
			var o := mi.get_surface_override_material(i)
			if o:
				found.surface_set_material(i, o)
		break
	root.free()
	return found


static func _scene_node(path: String) -> Node3D:
	var n: Node3D = (load(path) as PackedScene).instantiate()
	_dress(n)
	return n


## Swaps the flat Blender materials of a model for the shared PBR ones, by material name.
static func _dress(node: Node) -> void:
	var swap := {
		"stone": Pbr.material("stone_bricks", Color(1.0, 0.97, 0.92), 2.0),
		"dark_stone": Pbr.material("rock", Color(0.6, 0.58, 0.56), 2.0),
		"wood": Pbr.material("planks", Color(0.62, 0.42, 0.26), 2.0),
		"hull": Pbr.material("planks", Color(0.42, 0.27, 0.16), 1.6),
		"iron": Pbr.material("metal", Color(0.3, 0.3, 0.33), 2.0, 0.85, 0.7),
		"pine": Pbr.material("grass", Color(0.35, 0.55, 0.35), 3.0),
		"leaves": Pbr.material("grass", Color(0.55, 0.8, 0.45), 3.0),
		"bush": Pbr.material("grass", Color(0.45, 0.7, 0.4), 3.0),
		"blade": Pbr.material("grass", Color(0.7, 0.95, 0.55), 4.0),
	}
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and swap.has(mat.resource_name):
				m.set_surface_override_material(i, swap[mat.resource_name])


func _on_started(e: BastionEngine) -> void:
	for n in _castles: n.queue_free()
	for k in _cannons: _cannons[k].queue_free()
	for k in _ships: _ships[k].queue_free()
	_castles.clear()
	_cannons.clear()
	_ships.clear()
	var n := e.map.w * e.map.h
	for inst in [_land, _walls, _rubble, _ghost, _zone]:
		inst.multimesh.instance_count = n
	_edge.multimesh.instance_count = n * 4
	_last_enclosed = 0
	_sea_mat.set_shader_parameter("shore_mask", _shore_mask(e))
	_sea_mat.set_shader_parameter("map_size", Vector2(e.map.w, e.map.h))
	_balls.multimesh.instance_count = 64
	for k in _decor:
		_decor[k].multimesh.instance_count = n
	for c in e.map.castles:
		var node := _scene_node(MODELS + "castle.glb")
		node.position = Vector3(c.x + 0.5, LAND_H, c.y + 0.5)
		add_child(node)
		_castles.append(node)
	e.event.connect(_on_event)
	_land_dirty = true
	_cam_look = Vector3(e.map.w * 0.5 - 0.5, 0, e.map.h * 0.5 + 1.0)
	_fit_camera(e)


## A small texture of the map (1 = land), blurred, so the sea knows where the shallows and the shore are.
func _shore_mask(e: BastionEngine) -> ImageTexture:
	var k := 4
	var img := Image.create(e.map.w * k, e.map.h * k, false, Image.FORMAT_L8)
	for y in e.map.h * k:
		for x in e.map.w * k:
			img.set_pixel(x, y, Color.WHITE if e.map.at(x / k, y / k) != CoastMap.Terrain.WATER else Color.BLACK)
	for pass_ in 3:  # cheap blur: shrink and grow back
		img.resize(e.map.w * k / 2, e.map.h * k / 2, Image.INTERPOLATE_BILINEAR)
		img.resize(e.map.w * k, e.map.h * k, Image.INTERPOLATE_CUBIC)
	return ImageTexture.create_from_image(img)


## Pulls the camera back along its viewing direction until the whole map is on screen.
func _fit_camera(e: BastionEngine) -> void:
	var dir := Vector3(0, 21, 17).normalized()
	var corners := [Vector3(-0.5, 0, -0.5), Vector3(e.map.w - 0.5, 0, -0.5), Vector3(-0.5, 0, e.map.h - 0.5),
		Vector3(e.map.w - 0.5, 0, e.map.h - 0.5)]
	var dist := 12.0
	var vp := get_viewport().get_visible_rect().size
	while dist < 80.0:
		_camera.position = _cam_look + dir * dist
		_camera.look_at(_cam_look)
		var ok := true
		for c in corners:
			var sp := _camera.unproject_position(c)
			if _camera.is_position_behind(c) or sp.x < 0 or sp.y < 60 or sp.x > vp.x or sp.y > vp.y - 50:
				ok = false
				break
		if ok:
			break
		dist += 0.5
	_cam_base = _cam_look + dir * dist


## Map cell under a screen position (null when off the board).
func screen_to_cell(screen: Vector2):
	var from := _camera.project_ray_origin(screen)
	var dir := _camera.project_ray_normal(screen)
	if absf(dir.y) < 0.001:
		return null
	var t := (LAND_H - from.y) / dir.y
	var p := from + dir * t
	return Vector2(p.x, p.z)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"cannon_placed":
			var node := _scene_node(MODELS + "cannon.glb")
			node.position = Vector3(d["pos"].x + 0.5, LAND_H, d["pos"].y + 0.5)
			node.scale = Vector3.ONE * 0.01
			add_child(node)
			create_tween().tween_property(node, "scale", Vector3.ONE, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			_cannons[d["pos"]] = node
			_fx.dust(node.position, 14)
		"wall_placed", "castle_claimed", "enclosed":
			_land_dirty = true
			if kind == "enclosed":
				if d["cells"] > _last_enclosed + 2:
					_zone_pulse = 1.0  # a new area closed: flash it
				_last_enclosed = d["cells"]
			if kind == "wall_placed":
				for c in d["cells"]:
					_fx.dust(Vector3(c.x, LAND_H + 0.3, c.y), 5)
		"shot":
			var from: Vector2 = d["from"]
			_fx.muzzle(Vector3(from.x, LAND_H + 0.6, from.y), d["ours"])
			if d["ours"]:
				_shake = maxf(_shake, 0.15)
		"impact":
			var at: Vector2 = d["at"]
			var water: bool = e.map.at(roundi(at.x), roundi(at.y)) == CoastMap.Terrain.WATER
			_fx.impact(Vector3(at.x, (0.1 if water else LAND_H + 0.2), at.y), water)
		"wall_destroyed":
			_land_dirty = true
			_shake = maxf(_shake, 0.35)
			_fx.explosion(Vector3(d["at"].x, LAND_H + 0.4, d["at"].y), 0.7)
		"ship_hit":
			_fx.explosion(Vector3(d["at"].x, 0.5, d["at"].y), 0.6)
		"ship_sunk":
			_fx.explosion(Vector3(d["at"].x, 0.5, d["at"].y), 1.4)
			var node: Node3D = _ships.get(d["id"])
			if node:
				_ships.erase(d["id"])
				_sinking.append([node, 0.0])
		"phase":
			_land_dirty = true
			if d["phase"] == BastionEngine.Phase.BUILD:
				for k in _ships:
					_sinking.append([_ships[k], 0.0])
				_ships.clear()


func _process(delta: float) -> void:
	var e := game.engine
	if e == null:
		return
	_time += delta
	if _land_dirty:
		_rebuild_board(e)
		_land_dirty = false
	_zone_pulse = maxf(0.0, _zone_pulse - delta * 0.8)
	var za := 0.3 + 0.08 * sin(_time * 3.0) + 0.45 * _zone_pulse
	for i in _zone.multimesh.visible_instance_count:
		_zone.multimesh.set_instance_color(i, Color(0.35, 0.65, 1.0, za))
	for i in _edge.multimesh.visible_instance_count:
		_edge.multimesh.set_instance_color(i, Color(1, 1, 1, 1) * (0.8 + 0.4 * sin(_time * 4.0 + i * 0.3) + _zone_pulse))
	_blocked_t -= delta
	if _blocked_t <= 0.0:
		_blocked_cache = e.blocked()
		_blocked_t = 0.25
	_update_holes(e)
	_update_ships(e, delta)
	_update_balls(e)
	_update_cursor(e)
	_update_cannons(e)
	for c in e.map.castles.size():
		var home := c == e.home_castle
		var enclosed := e.enclosed_castles.has(c)
		_castles[c].scale = Vector3.ONE * (1.08 if home else 1.0)
		for mi in _castles[c].find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).transparency = 0.0 if enclosed or e.phase == BastionEngine.Phase.CHOOSE else 0.2
	# camera: a slow drift around the board, a little shake on impacts
	_shake = maxf(0.0, _shake - delta * 1.5)
	var drift := Vector3(sin(_time * 0.05) * 1.5, 0, cos(_time * 0.04) * 0.8)
	var jitter := Vector3(sin(_time * 61.0), sin(_time * 53.0), 0) * _shake * _shake * (0.6 if Settings.camera_shake else 0.0)
	_camera.position = _cam_base + drift + jitter
	_camera.look_at(_cam_look + drift * 0.3)


func _rebuild_board(e: BastionEngine) -> void:
	var li := 0
	var wi := 0
	var ri := 0
	for y in e.map.h:
		for x in e.map.w:
			var t := e.map.at(x, y)
			if t == CoastMap.Terrain.WATER:
				continue
			var shore := 0.0
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, -1)]:
				if e.map.at(x + d.x, y + d.y) == CoastMap.Terrain.WATER:
					shore = 1.0
			var rock := 1.0 if t == CoastMap.Terrain.ROCK else 0.0
			var h := LAND_H + (0.5 if rock > 0.0 else 0.0) + 0.03 * sin(x * 1.3 + y * 0.7)
			_land.multimesh.set_instance_transform(li, Transform3D(Basis.from_scale(Vector3(1, (h + 0.3) / (LAND_H + 0.3), 1)),
				Vector3(x, h * 0.5 - 0.15, y)))
			_land.multimesh.set_instance_color(li, Color(shore, rock, float(e.is_ours(x, y)), 1))
			li += 1
			var cellv := e.cell(x, y)
			if cellv == BastionEngine.Cell.WALL:
				_walls.multimesh.set_instance_transform(wi, Transform3D(Basis(), Vector3(x, LAND_H, y)))
				wi += 1
			elif cellv == BastionEngine.Cell.RUBBLE:
				_rubble.multimesh.set_instance_transform(ri, Transform3D(Basis(Vector3.UP, float(x * 7 + y)), Vector3(x, LAND_H, y)))
				ri += 1
	_land.multimesh.visible_instance_count = li
	_place_decor(e)
	var zi := 0
	var ei := 0
	for y in e.map.h:
		for x in e.map.w:
			if not e.is_ours(x, y):
				continue
			_zone.multimesh.set_instance_transform(zi, Transform3D(Basis(), Vector3(x, LAND_H + 0.02, y)))
			zi += 1
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if not e.is_ours(x + d.x, y + d.y) and e.cell(x + d.x, y + d.y) != BastionEngine.Cell.WALL:
					var basis := Basis() if d.y != 0 else Basis(Vector3.UP, PI * 0.5)
					_edge.multimesh.set_instance_transform(ei, Transform3D(basis, Vector3(x + d.x * 0.46, LAND_H + 0.05, y + d.y * 0.46)))
					ei += 1
	_zone.multimesh.visible_instance_count = zi
	_edge.multimesh.visible_instance_count = ei
	_walls.multimesh.visible_instance_count = wi
	_rubble.multimesh.visible_instance_count = ri


## Grass, flowers, bushes, stones and trees on free land, from a fixed pattern (hidden under anything built).
func _place_decor(e: BastionEngine) -> void:
	var counts := {}
	for k in _decor:
		counts[k] = 0
	for y in e.map.h:
		for x in e.map.w:
			if not e.map.is_land(x, y) or e.map.castle_at(x, y) >= 0 or e.cell(x, y) != BastionEngine.Cell.EMPTY:
				continue
			var h := absi((x * 73856093) ^ (y * 19349663)) % 1000
			var prop := ""
			if h < 260: prop = "grass_tuft"
			elif h < 300: prop = "bush"
			elif h < 330: prop = "stones"
			elif h < 355: prop = "pine"
			elif h < 375: prop = "tree"
			if prop == "":
				continue
			var off := Vector3(float(h % 7) / 7.0 - 0.45, 0, float(h % 11) / 11.0 - 0.45) * 0.5
			var xf := Transform3D(Basis(Vector3.UP, float(h)).scaled(Vector3.ONE * (0.8 + float(h % 5) * 0.1)),
				Vector3(x, LAND_H, y) + off)
			_decor[prop].multimesh.set_instance_transform(counts[prop], xf)
			counts[prop] += 1
	for k in _decor:
		_decor[k].multimesh.visible_instance_count = counts[k]


func _update_ships(e: BastionEngine, delta: float) -> void:
	for s in e.ships:
		var node: Node3D = _ships.get(s["id"])
		if node == null:
			node = _scene_node(MODELS + ["ship_small.glb", "ship_medium.glb", "ship_large.glb"][s["size"] - 1])
			add_child(node)
			_ships[s["id"]] = node
		var pos := Vector3(s["pos"].x, 0.12 + 0.05 * sin(_time * 2.0 + s["id"]), s["pos"].y)
		var heading: Vector2 = s["target"] - s["pos"]
		if heading.length() > 0.05:
			var want := atan2(heading.x, heading.y)  # ships face +Z (Blender's -Y)
			node.rotation.y = lerp_angle(node.rotation.y, want, 1.0 - exp(-delta * 3.0))
		node.rotation.z = 0.06 * sin(_time * 1.7 + s["id"])
		node.position = pos
		var wake: CPUParticles3D = _wakes.get(s["id"])
		if wake == null:
			wake = _make_wake()
			_wakes[s["id"]] = wake
		wake.position = pos - node.global_transform.basis.z * -0.6 * float(s["size"])
		wake.emitting = heading.length() > 0.2
	for id in _wakes.keys():
		if not _ships.has(id):  # ship gone: let its wake fade out, then free it
			var w: CPUParticles3D = _wakes[id]
			_wakes.erase(id)
			w.emitting = false
			get_tree().create_timer(2.5).timeout.connect(w.queue_free)
	for entry in _sinking.duplicate():
		var node: Node3D = entry[0]
		entry[1] += delta
		node.position.y -= delta * 0.5
		node.rotation.x += delta * 0.4
		node.visible = node.position.y > -0.9  # gone once under the surface (no glow through the water)
		if entry[1] > 3.0:
			node.queue_free()
			_sinking.erase(entry)


## Pulsing red markers on the cells that still need a wall to seal a castle (not when it is wide open).
func _update_holes(e: BastionEngine) -> void:
	var n := 0
	var show := e.phase == BastionEngine.Phase.BUILD or e.phase == BastionEngine.Phase.CANNONS
	if show:
		var pulse := 0.55 + 0.45 * sin(_time * 7.0)
		for c in e.castle_holes:
			var holes: Array = e.castle_holes[c]
			# beacons for the home castle, and for other castles only once they are close to sealed
			if holes.size() > BastionEngine.HOLE_LIMIT or (c != e.home_castle and holes.size() > 6):
				continue
			for h in holes:
				if n >= 64:
					break
				var grow := 0.85 + 0.25 * pulse
				_holes.multimesh.set_instance_transform(n, Transform3D(Basis.from_scale(Vector3(grow, 0.6 + 0.4 * pulse, grow)),
					Vector3(h.x, LAND_H + 0.5, h.y)))
				_holes.multimesh.set_instance_color(n, Color(3.0, 0.2, 0.1, 0.35 + 0.45 * pulse))
				n += 1
	_holes.multimesh.visible_instance_count = n


func _make_wake() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 40
	p.lifetime = 2.2
	p.local_coords = false
	p.direction = Vector3(0, 1, 0)
	p.spread = 30.0
	p.initial_velocity_min = 0.05
	p.initial_velocity_max = 0.2
	p.gravity = Vector3.ZERO
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.2
	var q := QuadMesh.new()
	q.size = Vector2(0.35, 0.35)
	q.orientation = PlaneMesh.FACE_Y
	p.mesh = q
	p.material_override = Fx.material("flat", Color(1, 1, 1, 0.7))
	p.scale_amount_curve = Fx.size_curve(true)
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.8))
	fade.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = fade
	add_child(p)
	return p


func _update_balls(e: BastionEngine) -> void:
	var i := 0
	for b in e.balls:
		var k: float = clampf(b["t"] / b["dur"], 0.0, 1.0)
		var p: Vector2 = b["from"].lerp(b["to"], k)
		var arc: float = 4.0 * k * (1.0 - k) * (1.5 + b["dur"] * 1.5)
		_balls.multimesh.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ONE * 1.4), Vector3(p.x, LAND_H + 0.6 + arc, p.y)))
		i += 1
		if i >= 64:
			break
	_balls.multimesh.visible_instance_count = i


func _update_cursor(e: BastionEngine) -> void:
	var n := 0
	_cross.visible = e.phase == BastionEngine.Phase.BATTLE and not game.demo
	var pulse := 0.6 + 0.4 * sin(_time * 8.0)
	match e.phase:
		BastionEngine.Phase.BUILD:
			var at := Vector2i(e.cursor.round())
			var ok := e.can_place_piece(at)
			var grey := _blocked_cache == "piece"
			for c in e.piece_cells_at(at):
				_ghost.multimesh.set_instance_transform(n, Transform3D(Basis(), Vector3(c.x, LAND_H + 0.35, c.y)))
				var gc := Color(0.5, 0.5, 0.5) if grey else (Color(0.3, 1.0, 0.4) if ok else Color(1.0, 0.25, 0.2))
				_ghost.multimesh.set_instance_color(n, gc * Color(1, 1, 1, 0.55 * pulse))
				n += 1
		BastionEngine.Phase.CANNONS:
			if e.cannons_to_place > 0:
				var at := Vector2i(e.cursor.round())
				var ok := e.can_place_cannon(at)
				for dy in 2:
					for dx in 2:
						_ghost.multimesh.set_instance_transform(n, Transform3D(Basis(), Vector3(at.x + dx, LAND_H + 0.3, at.y + dy)))
						_ghost.multimesh.set_instance_color(n, (Color(0.3, 0.7, 1.0) if ok else Color(1.0, 0.25, 0.2)) * Color(1, 1, 1, 0.5 * pulse))
						n += 1
		BastionEngine.Phase.CHOOSE:
			var c := e.map.castle_at(roundi(e.cursor.x), roundi(e.cursor.y))
			if c < 0:
				c = e._nearest_castle(e.cursor)
			var p := e.map.castles[c]
			for y in range(p.y - 1, p.y + 3):
				for x in range(p.x - 1, p.x + 3):
					if x == p.x - 1 or x == p.x + 2 or y == p.y - 1 or y == p.y + 2:
						_ghost.multimesh.set_instance_transform(n, Transform3D(Basis.from_scale(Vector3(1, 0.3, 1)), Vector3(x, LAND_H + 0.1, y)))
						_ghost.multimesh.set_instance_color(n, Color(1.0, 0.85, 0.3, 0.6 * pulse))
						n += 1
		BastionEngine.Phase.BATTLE:
			_cross.position = Vector3(e.cursor.x, LAND_H + 0.5, e.cursor.y)
			_cross.rotation.y = _time * 2.0
	_ghost.multimesh.visible_instance_count = n


func _update_cannons(e: BastionEngine) -> void:
	for c in e.cannons:
		var node: Node3D = _cannons.get(c["pos"])
		if node == null:
			continue
		if e.phase == BastionEngine.Phase.BATTLE:
			var aim: Vector2 = e.cursor - (Vector2(c["pos"]) + Vector2(0.5, 0.5))
			if game.demo and not e.ships.is_empty():
				aim = e.ships[0]["pos"] - (Vector2(c["pos"]) + Vector2(0.5, 0.5))
			# the models face +Z (Blender's -Y), hence the half turn
			node.rotation.y = lerp_angle(node.rotation.y, atan2(aim.x, aim.y), 0.15)
		for mi in node.find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).transparency = 0.0 if c["active"] else 0.5
