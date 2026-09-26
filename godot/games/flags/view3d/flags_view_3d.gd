class_name FlagsView3D
extends Node3D
## Iron Flags in 3D: the planet's ground from the map's tiles (with each territory tinted by its owner and dashed
## glowing borders), rock walls, water or lava, bridges, props, the buildings and flags, and the armies: robots
## animated from their rig, vehicles with turrets that turn, guns on their bases. An RTS camera pans (arrows, WASD,
## screen edges), zooms (wheel) and, in the demo, follows the fighting. Map point (x, y) is at world
## (x - 0.5, 0, y - 0.5), as in the shared water shader.

const E = preload("res://games/flags/engine/flags_engine.gd")
const T = FlagsMap.T
const Team = FlagsMap.Team
const M := "res://games/flags/art/models/"
const TEAM_COLOR := {Team.NEUTRAL: Color(0.62, 0.62, 0.6), Team.RED: Color(0.9, 0.18, 0.14), Team.BLUE: Color(0.18, 0.42, 0.95)}
const HEIGHT := {T.GROUND: 0.0, T.ROAD: -0.01, T.WATER: -0.5, T.ROCK: 0.12, T.ROUGH: 0.03, T.BRIDGE: -0.5, T.LAVA: -0.35}
## per planet: ground textures (base, alt, road) with tints, sky, sun, fog, water colours
const PLANETS := {
	"desert": {"base": ["sand", Color(1.05, 0.92, 0.72)], "alt": ["soil", Color(1.0, 0.8, 0.6)], "road": ["rock", Color(0.95, 0.82, 0.66)],
		"rock": Color(0.85, 0.66, 0.48), "sky": [Color(0.35, 0.55, 0.85), Color(0.95, 0.85, 0.7)], "sun": [Vector3(-52, -35, 0), Color(1.0, 0.92, 0.78), 1.35],
		"fog": [Color(0.95, 0.85, 0.7), 0.004], "water": Color(0.1, 0.45, 0.5), "ambient": Color(0.75, 0.7, 0.62)},
	"arctic": {"base": ["beach_sand", Color(1.05, 1.1, 1.2)], "alt": ["sand", Color(0.98, 1.06, 1.22)], "road": ["rock", Color(0.72, 0.76, 0.84)],
		"rock": Color(0.75, 0.8, 0.9), "sky": [Color(0.4, 0.6, 0.9), Color(0.85, 0.9, 0.98)], "sun": [Vector3(-38, -20, 0), Color(1.0, 0.97, 0.94), 1.2],
		"fog": [Color(0.85, 0.9, 1.0), 0.006], "water": Color(0.15, 0.4, 0.55), "ambient": Color(0.7, 0.78, 0.9)},
	"volcanic": {"base": ["dark_rock", Color(0.62, 0.6, 0.6)], "alt": ["soil", Color(0.42, 0.34, 0.3)], "road": ["rock", Color(0.55, 0.52, 0.5)],
		"rock": Color(0.42, 0.38, 0.37), "sky": [Color(0.14, 0.1, 0.12), Color(0.55, 0.36, 0.28)], "sun": [Vector3(-60, 20, 0), Color(1.0, 0.86, 0.76), 1.15],
		"fog": [Color(0.4, 0.3, 0.27), 0.004], "water": Color(0.1, 0.2, 0.2), "ambient": Color(0.52, 0.48, 0.48)},
	"jungle": {"base": ["grass_lush", Color(1.0, 1.0, 1.0)], "alt": ["grass", Color(0.9, 1.0, 0.8)], "road": ["soil", Color(0.9, 0.8, 0.65)],
		"rock": Color(0.7, 0.72, 0.65), "sky": [Color(0.3, 0.5, 0.75), Color(0.75, 0.85, 0.8)], "sun": [Vector3(-55, -30, 0), Color(1.0, 0.95, 0.85), 1.2],
		"fog": [Color(0.6, 0.75, 0.65), 0.004], "water": Color(0.12, 0.45, 0.35), "ambient": Color(0.6, 0.7, 0.62)},
	"city": {"base": ["stone_bricks", Color(0.8, 0.8, 0.82)], "alt": ["rock", Color(0.7, 0.7, 0.72)], "road": ["dark_rock", Color(0.55, 0.55, 0.6)],
		"rock": Color(0.6, 0.6, 0.62), "sky": [Color(0.35, 0.5, 0.75), Color(0.8, 0.82, 0.85)], "sun": [Vector3(-50, -40, 0), Color(1.0, 0.95, 0.88), 1.2],
		"fog": [Color(0.75, 0.78, 0.82), 0.004], "water": Color(0.1, 0.3, 0.4), "ambient": Color(0.68, 0.7, 0.74)},
}

@export var game: FlagsGame

var camera: Camera3D
var _env: Environment
var _sky_mat: ProceduralSkyMaterial
var _sun: DirectionalLight3D
var _board: Node3D
var _fx: FlagsEffects
var _ground_mat: ShaderMaterial
var _owners_img: Image
var _owners_tex: ImageTexture
var _units := {}      ## id -> {node, anim, turret, cls, kind, last}
var _buildings := {}  ## id -> {node, dish}
var _flags := []      ## per zone: {pole, cloth mat}
var _crates := {}     ## index -> node
var _rocks := {}      ## cell -> [multimesh, index]
var _team_mats := {}  ## [resource name, team] -> material
var _shots: Array[Dictionary] = []   ## flying shells, rockets, missiles, tracers
var _tracer_pool: Array[MeshInstance3D] = []
var _shell_pool: Array[MeshInstance3D] = []
var _beam_pool: Array[MeshInstance3D] = []
var _ring_pool: Array[MeshInstance3D] = []
var _cursor: MeshInstance3D
var _cursor_t := 9.0
var _cam_focus := Vector2(20, 20)  ## map point the camera looks at
var _cam_goal := Vector2(20, 20)
var _zoom := 1.0
var _zoom_goal := 1.0
var _time := 0.0
var _shake := 0.0
var _hot := Vector2(-1, -1)  ## the demo camera's point of interest
var _hot_t := 0.0


func _ready() -> void:
	game.view = self
	_build_env()
	_fx = FlagsEffects.new()
	add_child(_fx)
	_build_pools()
	game.map_started.connect(_on_map)
	if game.engine:
		_on_map(game.engine)


func w(p: Vector2, y := 0.0) -> Vector3:
	return Vector3(p.x - 0.5, y, p.y - 0.5)


func focus() -> Vector2:
	return _cam_focus


## The map point under a screen position (on the ground plane), or null.
func screen_to_map(screen: Vector2):
	var from := camera.project_ray_origin(screen)
	var dir := camera.project_ray_normal(screen)
	if absf(dir.y) < 0.001:
		return null
	var t := -from.y / dir.y
	if t < 0.0:
		return null
	var hit := from + dir * t
	return Vector2(hit.x + 0.5, hit.z + 0.5)


## The unit or building under a screen position, or -1.
func pick(screen: Vector2) -> int:
	var e := game.engine
	var best := -1
	var bd := 28.0
	for u in e.units:
		if u["dead"]:
			continue
		var sp := camera.unproject_position(w(u["pos"], 0.4))
		var d := sp.distance_to(screen)
		if d < bd:
			bd = d
			best = u["id"]
	if best >= 0:
		return best
	var p = screen_to_map(screen)
	if p != null:
		for b in e.buildings:
			if Rect2(Vector2(b["cell"]), Vector2(b["size"])).has_point(p):
				return b["id"]
	return -1


func select_box(r: Rect2) -> Array:
	var out := []
	for u in game.engine.units:
		if not u["dead"] and r.has_point(camera.unproject_position(w(u["pos"], 0.3))):
			out.append(u["id"])
	return out


# ------------------------------------------------------------------ setup

func _build_env() -> void:
	_sky_mat = ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = _sky_mat
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.0
	_env.glow_enabled = true
	_env.glow_intensity = 0.5
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_env.ssao_intensity = 1.6
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.2
	_env.adjustment_contrast = 1.08
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 70.0
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 38
	camera.current = true
	add_child(camera)
	_cursor = _ring(Color(1.0, 0.9, 0.4), 0.5)
	_cursor.visible = false


func _ring(c: Color, r: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = r * 0.85
	tm.outer_radius = r
	tm.rings = 24
	mi.mesh = tm
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.emission_enabled = true
	m.emission = c
	m.emission_energy_multiplier = 1.4
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = m
	mi.scale = Vector3(1, 0.25, 1)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


func _glow_mat(c: Color, energy: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.emission_enabled = true
	m.emission = c
	m.emission_energy_multiplier = energy
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return m


func _build_pools() -> void:
	var tracer := _glow_mat(Color(1.0, 0.85, 0.45), 4.0)
	for i in 80:
		var t := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.025
		cap.height = 0.5
		t.mesh = cap
		t.material_override = tracer
		t.visible = false
		t.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(t)
		_tracer_pool.append(t)
	var shell := StandardMaterial3D.new()
	shell.albedo_color = Color(0.25, 0.25, 0.25)
	shell.metallic = 0.8
	shell.emission_enabled = true
	shell.emission = Color(1.0, 0.6, 0.2)
	shell.emission_energy_multiplier = 0.8
	for i in 40:
		var s := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.06
		cap.height = 0.3
		s.mesh = cap
		s.material_override = shell
		s.visible = false
		add_child(s)
		_shell_pool.append(s)
	var beam := _glow_mat(Color(0.35, 1.0, 0.9), 6.0)
	for i in 16:
		var b := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.03
		cm.bottom_radius = 0.03
		cm.height = 1.0
		cm.radial_segments = 6
		b.mesh = cm
		b.material_override = beam
		b.visible = false
		b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(b)
		_beam_pool.append(b)
	for i in 80:
		var r := _ring(Color(0.5, 1.0, 0.5), 0.42)
		r.visible = false
		_ring_pool.append(r)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()  # a stand-in while a model is missing
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.6, 0.6, 0.6)
	mi.mesh = bm
	mi.position.y = 0.3
	n.add_child(mi)
	return n


## Recolours the team parts (materials named "team...") of a model.
func _paint(n: Node, team: int) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat == null or not mat.resource_name.to_lower().contains("team"):
				continue
			var key := [mat.resource_name, team]
			if not _team_mats.has(key):
				var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				var c: Color = TEAM_COLOR[team]
				s.albedo_color = c if not mat.resource_name.to_lower().contains("trim") else c.darkened(0.3)
				_team_mats[key] = s
			m.set_surface_override_material(i, _team_mats[key])


func _on_map(e: FlagsEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_units.clear()
	_buildings.clear()
	_flags.clear()
	_crates.clear()
	_rocks.clear()
	_shots.clear()
	e.event.connect(_on_event)
	var p: Dictionary = PLANETS.get(e.map.planet, PLANETS["desert"])
	_sky_mat.sky_top_color = p["sky"][0]
	_sky_mat.sky_horizon_color = p["sky"][1]
	_sky_mat.ground_horizon_color = p["sky"][1]
	_sky_mat.ground_bottom_color = p["sky"][1].darkened(0.4)
	Look.sky_ambient(_env, p["ambient"], 0.55)
	Look.fog(_env, p["fog"][0], p["fog"][1])
	_sun.rotation_degrees = p["sun"][0]
	_sun.light_color = p["sun"][1]
	_sun.light_energy = p["sun"][2] * (0.72 if Look.compat() else 1.0)
	_env.tonemap_exposure = 0.82 if Look.compat() else 1.0
	_build_ground(e, p)
	_build_rocks(e, p)
	_build_props(e)
	for b in e.buildings:
		_add_building(b)
	for i in e.zones.size():
		_add_flag(e, i)
	for i in e.items.size():
		var it: Dictionary = e.items[i]
		var n := _scene("crate_grenades" if it["kind"] == "grenades" else "crate_rockets")
		n.position = w(Vector2(it["cell"]) + Vector2(0.5, 0.5))
		n.rotation.y = i * 0.7
		_board.add_child(n)
		_crates[i] = n
	for u in e.units:
		_add_unit(u)
	var f := e.fort_of(Team.RED)
	if f.is_empty():
		f = e.fort_of(Team.BLUE)
	_cam_focus = e._center(f) + Vector2(0, 3) if not f.is_empty() and not game.demo else Vector2(e.map.w, e.map.h) * 0.5
	_cam_goal = _cam_focus
	_hot = Vector2(-1, -1)
	_place_camera(1.0)


func _build_ground(e: FlagsEngine, p: Dictionary) -> void:
	var m := e.map
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var corner := func(cx: int, cy: int) -> Array:
		var hs := 0.0
		var low := INF
		var col := Color(0, 0, 0)
		for dy in [-1, 0]:
			for dx in [-1, 0]:
				var t: int = m.at(Vector2i(cx + dx, cy + dy)) if m.inside(Vector2i(cx + dx, cy + dy)) else T.ROCK
				var hh: float = HEIGHT[t]
				hs += hh
				low = minf(low, hh)
				col += Color(1.0 if t == T.ROUGH or t == T.ROCK else 0.0, 1.0 if t == T.ROAD or t == T.BRIDGE else 0.0, 0.0)
		var hv := lerpf(hs / 4.0, low, 0.6)
		var j := sin(cx * 12.9898 + cy * 78.233) * 43758.5453
		j = (j - floorf(j)) * 0.05 - 0.025
		return [Vector3(cx - 0.5, hv + (j if hv > -0.05 else 0.0), cy - 0.5), col / 4.0]
	for y in m.h:
		for x in m.w:
			var a: Array = corner.call(x, y)
			var b: Array = corner.call(x + 1, y)
			var c: Array = corner.call(x + 1, y + 1)
			var d: Array = corner.call(x, y + 1)
			for v in [a, b, c, a, c, d]:
				st.set_color(v[1])
				st.set_uv(Vector2(v[0].x, v[0].z))
				st.add_vertex(v[0])
	st.generate_normals()
	var ground := MeshInstance3D.new()
	ground.mesh = st.commit()
	_ground_mat = ShaderMaterial.new()
	_ground_mat.shader = load("res://games/flags/view3d/shaders/planet.gdshader")
	for k in ["base", "alt", "road"]:
		_ground_mat.set_shader_parameter(k + "_albedo", load(Pbr.ROOT + p[k][0] + "/albedo.jpg"))
		_ground_mat.set_shader_parameter(k + "_normal", load(Pbr.ROOT + p[k][0] + "/normal.jpg"))
		var tint: Color = p[k][1]
		_ground_mat.set_shader_parameter(k + "_tint", Vector3(tint.r, tint.g, tint.b))
	_ground_mat.set_shader_parameter("map_size", Vector2(m.w, m.h))
	var ids := Image.create(m.w, m.h, false, Image.FORMAT_R8)
	for y in m.h:
		for x in m.w:
			var z := m.zone_at(Vector2i(x, y))
			ids.set_pixel(x, y, Color((z + 1) / 255.0, 0, 0))
	_ground_mat.set_shader_parameter("zone_ids", ImageTexture.create_from_image(ids))
	_owners_img = Image.create(m.w, m.h, false, Image.FORMAT_RGBA8)
	_owners_tex = ImageTexture.create_from_image(_owners_img)
	_ground_mat.set_shader_parameter("owners", _owners_tex)
	_paint_owners(e)
	ground.material_override = _ground_mat
	_board.add_child(ground)
	# water and lava sheets
	var has_water := false
	var has_lava := false
	for t in m.terrain:
		has_water = has_water or t == T.WATER or t == T.BRIDGE
		has_lava = has_lava or t == T.LAVA
	if has_water:
		var water := MeshInstance3D.new()
		var plane := PlaneMesh.new()
		plane.size = Vector2(m.w, m.h)
		plane.subdivide_width = m.w
		plane.subdivide_depth = m.h
		water.mesh = plane
		var wm := ShaderMaterial.new()
		wm.shader = load("res://core/art/shaders/water.gdshader")
		wm.set_shader_parameter("normal_map", load("res://core/art/textures/water/normal.png"))
		var wc: Color = p["water"]
		wm.set_shader_parameter("shallow", wc.lightened(0.15))
		wm.set_shader_parameter("mid", wc.darkened(0.3))
		wm.set_shader_parameter("sky", p["sky"][0].lightened(0.3))
		wm.set_shader_parameter("map_size", Vector2(m.w, m.h))
		wm.set_shader_parameter("shore_mask", _mask(m, [T.WATER, T.BRIDGE]))
		water.material_override = wm
		water.position = Vector3(m.w * 0.5 - 0.5, -0.16, m.h * 0.5 - 0.5)
		water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_board.add_child(water)
	if has_lava:
		var lst := SurfaceTool.new()
		lst.begin(Mesh.PRIMITIVE_TRIANGLES)
		for y in m.h:
			for x in m.w:
				if m.at(Vector2i(x, y)) != T.LAVA and not (m.at(Vector2i(x, y)) == T.BRIDGE and _near(m, Vector2i(x, y), T.LAVA)):
					continue
				var o := Vector3(x - 0.5, -0.14, y - 0.5)
				for v in [Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(1, 0, 1), Vector3(0, 0, 0), Vector3(1, 0, 1), Vector3(0, 0, 1)]:
					lst.set_normal(Vector3.UP)
					lst.add_vertex(o + v)
		var lava := MeshInstance3D.new()
		lava.mesh = lst.commit()
		var lm := ShaderMaterial.new()
		lm.shader = load("res://games/flags/view3d/shaders/lava.gdshader")
		lava.material_override = lm
		lava.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_board.add_child(lava)
	# bridges: plank decks with rails on their open sides
	var planks := Pbr.material("planks", Color(0.75, 0.62, 0.48), 1.0)
	var iron := Pbr.material("metal", Color(0.35, 0.33, 0.32), 1.0, 0.7, 0.5)
	for y in m.h:
		for x in m.w:
			var c := Vector2i(x, y)
			if m.at(c) != T.BRIDGE:
				continue
			_box(Vector3(x, 0.1, y), Vector3(1.0, 0.1, 1.0), planks)  # high enough that no swell laps over it
			var vert := m.at(c + Vector2i(0, -1)) == T.BRIDGE or m.at(c + Vector2i(0, 1)) == T.BRIDGE
			for s in [-1, 1]:
				var side := c + (Vector2i(s, 0) if vert else Vector2i(0, s))
				if m.at(side) != T.BRIDGE:
					var off := Vector3(s * 0.46, 0.25, 0) if vert else Vector3(0, 0.25, s * 0.46)
					_box(Vector3(x, 0, y) + off, Vector3(0.06, 0.1, 1.0) if vert else Vector3(1.0, 0.1, 0.06), iron)
			if (x + y) % 2 == 0:
				_box(Vector3(x, -0.2, y), Vector3(0.14, 0.6, 0.14), iron)


func _near(m: FlagsMap, c: Vector2i, t: int) -> bool:
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(2, 0), Vector2i(-2, 0), Vector2i(0, 2), Vector2i(0, -2)]:
		if m.at(c + d) == t:
			return true
	return false


func _box(pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	_board.add_child(mi)
	return mi


func _mask(m: FlagsMap, wet: Array) -> ImageTexture:
	var k := 4
	var img := Image.create(m.w * k, m.h * k, false, Image.FORMAT_L8)
	for y in m.h * k:
		for x in m.w * k:
			img.set_pixel(x, y, Color.BLACK if m.at(Vector2i(x / k, y / k)) in wet else Color.WHITE)
	for pass_ in 2:
		img.resize(m.w * k / 2, m.h * k / 2, Image.INTERPOLATE_BILINEAR)
		img.resize(m.w * k, m.h * k, Image.INTERPOLATE_CUBIC)
	return ImageTexture.create_from_image(img)


func _paint_owners(e: FlagsEngine) -> void:
	var m := e.map
	for y in m.h:
		for x in m.w:
			var z := m.zone_at(Vector2i(x, y))
			var owner: int = e.zones[z]["owner"] if z >= 0 else Team.NEUTRAL
			var c: Color = TEAM_COLOR[owner]
			c.a = 0.0 if z < 0 else (0.35 if owner == Team.NEUTRAL else 1.0)
			_owners_img.set_pixel(x, y, c)
	_owners_tex.update(_owners_img)


func _build_rocks(e: FlagsEngine, p: Dictionary) -> void:
	var m := e.map
	var rng := RandomNumberGenerator.new()
	rng.seed = m.w * 131 + m.h
	var per: Array = [[], [], [], []]
	for y in m.h:
		for x in m.w:
			if m.at(Vector2i(x, y)) != T.ROCK:
				continue
			var k := rng.randi_range(0, 3)
			var s := rng.randf_range(0.95, 1.25)
			var edge := x == 0 or y == 0 or x == m.w - 1 or y == m.h - 1
			var basis := Basis(Vector3.UP, rng.randi_range(0, 3) * PI * 0.5 + rng.randf_range(-0.15, 0.15)).scaled(Vector3(s, s * (1.3 if edge else rng.randf_range(0.8, 1.2)), s))
			per[k].append([Vector2i(x, y), Transform3D(basis, Vector3(x, 0, y) + Vector3(rng.randf_range(-0.08, 0.08), 0, rng.randf_range(-0.08, 0.08)))])
	var tint: Color = p["rock"]
	for k in 4:
		var mmi := _multi("rock_%d" % k, per[k].map(func(a): return a[1]), tint)
		if mmi:
			for i in per[k].size():
				_rocks[per[k][i][0]] = [mmi.multimesh, i]


func _build_props(e: FlagsEngine) -> void:
	var by_kind := {}
	var rng := RandomNumberGenerator.new()
	rng.seed = e.map.w * 17 + e.map.h
	for pr in e.map.props:
		if not by_kind.has(pr["kind"]):
			by_kind[pr["kind"]] = []
		var s := rng.randf_range(0.8, 1.3)
		by_kind[pr["kind"]].append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)),
			Vector3(pr["cell"].x + rng.randf_range(-0.25, 0.25), 0, pr["cell"].y + rng.randf_range(-0.25, 0.25))))
	for k in by_kind:
		_multi(k, by_kind[k], Color.WHITE)


## One draw for many copies of a model (all its surfaces merged into one mesh with their materials).
func _multi(model: String, xf: Array, tint: Color) -> MultiMeshInstance3D:
	if xf.is_empty():
		return null
	var root := _scene(model)
	var am := ArrayMesh.new()
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var src := (mi as MeshInstance3D).mesh
		var local := (mi as MeshInstance3D).transform
		var parent := mi.get_parent()
		while parent and parent != root:
			local = (parent as Node3D).transform * local
			parent = parent.get_parent()
		for s in src.get_surface_count():
			var st := SurfaceTool.new()
			st.create_from(src, s)
			var mat := src.surface_get_material(s)
			if tint != Color.WHITE and mat is StandardMaterial3D:
				mat = (mat as StandardMaterial3D).duplicate()
				mat.albedo_color = mat.albedo_color * tint
			st.set_material(mat)
			var arr := st.commit_to_arrays()
			var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var norms: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
			for i in verts.size():
				verts[i] = local * verts[i]
				if norms.size() > i:
					norms[i] = (local.basis * norms[i]).normalized()
			arr[Mesh.ARRAY_VERTEX] = verts
			if norms.size() > 0:
				arr[Mesh.ARRAY_NORMAL] = norms
			if arr[Mesh.ARRAY_TANGENT] != null:
				arr[Mesh.ARRAY_TANGENT] = null
			am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			am.surface_set_material(am.get_surface_count() - 1, mat)
	root.free()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = am
	mm.instance_count = xf.size()
	for i in xf.size():
		mm.set_instance_transform(i, xf[i])
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	_board.add_child(inst)
	return inst


func _add_building(b: Dictionary) -> void:
	var n := _scene(b["kind"])
	n.position = w(Vector2(b["cell"]) + Vector2(b["size"]) * 0.5)
	_board.add_child(n)
	_paint(n, b["team"])
	var dish := n.find_child("dish", true, false)
	_buildings[b["id"]] = {"node": n, "dish": dish, "team": b["team"], "smoke": 0.0}


func _add_flag(e: FlagsEngine, i: int) -> void:
	var z: Dictionary = e.zones[i]
	if z["flag"].x < 0:
		_flags.append({})
		return
	var pole := _scene("flag_pole")
	pole.position = w(Vector2(z["flag"]) + Vector2(0.5, 0.5))
	_board.add_child(pole)
	_paint(pole, z["owner"])
	var sm := ShaderMaterial.new()
	sm.shader = load("res://games/flags/view3d/shaders/team_flag.gdshader")
	sm.set_shader_parameter("color", TEAM_COLOR[z["owner"]])
	var cloth := pole.find_child("cloth", true, false) as MeshInstance3D
	if cloth:
		cloth.material_override = sm
	else:
		cloth = MeshInstance3D.new()
		pole.add_child(cloth)
	_flags.append({"pole": pole, "cloth": cloth, "mat": sm, "owner": z["owner"]})


func _add_unit(u: Dictionary) -> void:
	var kind: String = u["kind"]
	var model := "robot_" + kind if u["cls"] == "robot" else ("cannon_" + kind if u["cls"] == "cannon" else kind)
	var n := _scene(model)
	_board.add_child(n)
	_paint(n, u["team"])
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap:
		for a in ap.get_animation_list():
			ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "walk", "run", "cheer"] else Animation.LOOP_NONE
	var turret := n.find_child("turret", true, false) as Node3D
	var d := {"node": n, "anim": ap, "turret": turret, "cls": u["cls"], "kind": kind, "last": "", "team": u["team"],
		"ring": null, "dead_t": 0.0}
	_units[u["id"]] = d
	_pose(d, u, 1.0)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"spawn":
			var u := e.by_id(d["id"])
			if not u.is_empty():
				_add_unit(u)
		"shot":
			_shot(d)
			_heat(d["from"])
		"hit":
			var p := w(d["pos"], 0.35)
			if d["weapon"] == "laser":
				_fx.laser_hit(p)
			elif d["weapon"] == "flame":
				_fx.flame(p)
			else:
				_fx.spark(p)
		"blast":
			var big: bool = d["radius"] >= 1.0
			_fx.explosion(w(d["pos"], 0.2), 1.2 if big else 0.7)
			_scorch(d["pos"], d["radius"])
			if _on_screen(d["pos"]):
				_shake = maxf(_shake, 0.35 if big else 0.18)
		"death":
			var v: Dictionary = _units.get(d["id"], {})
			if d["cls"] != "robot":
				_fx.explosion(w(d["pos"], 0.4), 1.6)
				if _on_screen(d["pos"]):
					_shake = maxf(_shake, 0.5)
			_heat(d["pos"])
		"capture":
			var f: Dictionary = _flags[d["zone"]]
			if not f.is_empty():
				f["owner"] = d["team"]
				f["mat"].set_shader_parameter("color", TEAM_COLOR[d["team"]])
				_paint(f["pole"], d["team"])
				_fx.confetti(f["pole"].position + Vector3(0.4, 2.0, 0), TEAM_COLOR[d["team"]])
			_paint_owners(e)
			for b in e.buildings:
				if b["zone"] == d["zone"] and _buildings.has(b["id"]):
					_paint(_buildings[b["id"]]["node"], b["team"])
			for u in e.units:
				if u["cls"] == "cannon" and _units.has(u["id"]) and _units[u["id"]]["team"] != u["team"]:
					_units[u["id"]]["team"] = u["team"]
					_paint(_units[u["id"]]["node"], u["team"])
			_heat(Vector2(e.zones[d["zone"]]["flag"]))
		"board":
			var v2: Dictionary = _units.get(d["vehicle"], {})
			if not v2.is_empty():
				_paint(v2["node"], d["team"])
				v2["team"] = d["team"]
		"pickup":
			for i in e.items.size():
				if e.items[i]["cell"] == d["cell"] and _crates.has(i):
					_fx.confetti(_crates[i].position + Vector3(0, 0.3, 0), Color(1.0, 0.85, 0.3))
					_crates[i].queue_free()
					_crates.erase(i)
		"rock_destroyed":
			var r: Array = _rocks.get(d["cell"], [])
			if not r.is_empty():
				var mm: MultiMesh = r[0]
				var xf := mm.get_instance_transform(r[1])
				_fx.dust(xf.origin + Vector3(0, 0.4, 0), PLANETS.get(e.map.planet, PLANETS["desert"])["rock"])
				mm.set_instance_transform(r[1], Transform3D(Basis().scaled(Vector3(0.9, 0.25, 0.9)), xf.origin))  # rubble
				_rocks.erase(d["cell"])
		"destroyed":
			var bd: Dictionary = _buildings.get(d["id"], {})
			if not bd.is_empty():
				for k in 6:
					var b := e.by_id(d["id"])
					var c := Vector2(b["cell"]) + Vector2(randf() * b["size"].x, randf() * b["size"].y)
					get_tree().create_timer(k * 0.25).timeout.connect(func(): _fx.explosion(w(c, 1.0), 2.0))
				_shake = 1.2
				create_tween().tween_property(bd["node"], "scale", Vector3(1.0, 0.35, 1.0), 1.6).set_trans(Tween.TRANS_BOUNCE)
		"order":
			_cursor.position = w(d["pos"], 0.05)
			_cursor_t = 0.0
			_cursor.visible = true
			(_cursor.material_override as StandardMaterial3D).albedo_color = Color(1.0, 0.3, 0.2) if d["attack"] else Color(0.5, 1.0, 0.5)


func _on_screen(p: Vector2) -> bool:
	return p.distance_to(_cam_focus) < 16.0 * _zoom


## Something happened here: the demo camera drifts towards the busiest place.
func _heat(p: Vector2) -> void:
	if _hot.x < 0 or _time - _hot_t > 6.0 or p.distance_to(_cam_focus) < _hot.distance_to(_cam_focus) - 4.0:
		if _time - _hot_t > 2.5:
			_hot = p
			_hot_t = _time


func _scorch(p: Vector2, r: float) -> void:
	if r < 0.8:
		return
	var n := _scene("crater")
	n.position = w(p, 0.06)  # above the ground's bumps, or only the rim would show
	var tint: Color = PLANETS.get(game.engine.map.planet, PLANETS["desert"])["rock"]
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat:
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = mat.albedo_color * tint * 1.2
				m.set_surface_override_material(i, t)
	n.rotation.y = randf() * TAU
	n.scale = Vector3.ONE * r
	_board.add_child(n)
	get_tree().create_timer(40.0).timeout.connect(func(): if is_instance_valid(n): n.queue_free())


func _shot(d: Dictionary) -> void:
	var e := game.engine
	var src := e.by_id(d["id"])
	var from := w(d["from"], 0.45 if src.get("cls", "robot") == "robot" else 0.7)
	var to := w(d["to"], 0.35)
	var wpn: String = d["weapon"]
	var heavy := wpn in ["tank_gun", "howitzer", "missile", "rocket", "grenade"]
	var dir := (to - from).normalized()
	_fx.muzzle(from + dir * 0.35, heavy)
	match wpn:
		"laser":
			var b: MeshInstance3D = _beam_pool.pop_front()
			_beam_pool.append(b)
			b.visible = true
			b.position = (from + to) * 0.5
			b.look_at_from_position(b.position, to, Vector3.UP if absf(dir.y) < 0.99 else Vector3.RIGHT)
			b.rotate_object_local(Vector3.RIGHT, PI * 0.5)
			b.scale = Vector3(1, from.distance_to(to), 1)
			_shots.append({"node": b, "t": 0.0, "life": 0.12, "kind": "beam"})
		"flame":
			for k in 3:
				_fx.flame(from.lerp(to, 0.3 + k * 0.3))
		_:
			var node: MeshInstance3D
			if heavy:
				node = _shell_pool.pop_front()
				_shell_pool.append(node)
			else:
				node = _tracer_pool.pop_front()
				_tracer_pool.append(node)
			node.visible = true
			var arc := 0.0
			match wpn:
				"howitzer": arc = 3.5
				"grenade": arc = 1.5
				"missile": arc = 2.0
			_shots.append({"node": node, "t": 0.0, "life": maxf(0.06, d["time"]), "from": from, "to": to, "arc": arc,
				"kind": "smoke" if wpn in ["missile", "rocket"] else "shell", "trail": 0.0})


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null:
		return
	_update_units(e, delta)
	_update_shots(delta)
	for id in _buildings:
		var bd: Dictionary = _buildings[id]
		if bd["dish"]:
			bd["dish"].rotation.y += delta * 1.2
		var b := e.by_id(id)
		if not b.is_empty() and b["hp"] < b["max_hp"] * 0.5 and not b["destroyed"]:  # damaged: smoke
			bd["smoke"] -= delta
			if bd["smoke"] <= 0.0:
				bd["smoke"] = 0.35
				_fx.burst(bd["node"].position + Vector3(randf_range(-1, 1), 2.0, randf_range(-1, 1)), Color(0.2, 0.2, 0.2, 0.6), 3, 0.6, 2.0, 0.8, 0.0, 0.8, 1.0, "smoke")
	_cursor_t += delta
	if _cursor.visible:
		_cursor.scale = Vector3.ONE * (1.0 + _cursor_t * 1.5) * Vector3(1, 0.25, 1)
		_cursor.visible = _cursor_t < 0.45
	_camera_input(delta)
	_place_camera(delta)


func _update_units(e: FlagsEngine, delta: float) -> void:
	var sel := {}
	for id in game.selected:
		sel[id] = true
	var ring := 0
	for id in _units.keys():
		var v: Dictionary = _units[id]
		var u := e.by_id(id)
		if u.is_empty():
			v["node"].queue_free()
			_units.erase(id)
			continue
		_pose(v, u, delta)
		if sel.has(id) and ring < _ring_pool.size() and not u["dead"]:
			var r := _ring_pool[ring]
			ring += 1
			r.visible = true
			r.position = w(u["pos"], 0.04)
			r.scale = Vector3.ONE * (1.0 if u["cls"] == "robot" else 2.0) * Vector3(1, 0.25, 1)
	for i in range(ring, _ring_pool.size()):
		_ring_pool[i].visible = false


func _pose(v: Dictionary, u: Dictionary, delta: float) -> void:
	var n: Node3D = v["node"]
	var y := 0.0
	var t := game.engine.map.at(Vector2i(u["pos"].floor()))
	if t == T.BRIDGE:
		y = 0.15
	elif t == T.ROUGH:
		y = 0.03
	n.position = w(u["pos"], y)
	var face: float = PI * 0.5 - u["facing"]
	if v["cls"] == "cannon":
		face = 0.0
	n.rotation.y = lerp_angle(n.rotation.y, face, minf(1.0, delta * 12.0)) if v["last"] != "" else face
	if v["turret"]:
		v["turret"].rotation.y = (PI * 0.5 - u["aim"]) - n.rotation.y
	if v["team"] != u["team"]:
		v["team"] = u["team"]
		_paint(n, u["team"])
	if u["dead"]:
		v["dead_t"] += delta
		if v["cls"] == "robot":
			_play(v, "die")
			if v["dead_t"] > 3.0:
				n.position.y -= (v["dead_t"] - 3.0) * 0.3  # sink into the ground
		elif v["dead_t"] < 0.05:
			_wreck(n)
		n.visible = v["dead_t"] < 5.0 or v["cls"] != "robot"
		return
	if v["cls"] != "robot":
		return
	var want := "idle"
	if u["firing"] > 0.0:
		want = "shoot"
	elif u["moving"]:
		want = "run" if u["kind"] == "psycho" else "walk"
	elif game.engine.phase != E.Phase.PLAY and (game.engine.phase == E.Phase.WON) == (u["team"] == Team.RED):
		want = "cheer"
	_play(v, want)


func _play(v: Dictionary, a: String) -> void:
	if v["last"] == a or v["anim"] == null:
		return
	v["last"] = a
	var ap: AnimationPlayer = v["anim"]
	if ap.has_animation(a):
		ap.play(a, 0.15)


## A destroyed vehicle or gun: blackened, the turret thrown askew, smoke.
func _wreck(n: Node3D) -> void:
	var burnt := StandardMaterial3D.new()
	burnt.albedo_color = Color(0.08, 0.07, 0.07)
	burnt.roughness = 1.0
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = burnt
	var tur := n.find_child("turret", true, false) as Node3D
	if tur:
		tur.rotation.z = 0.5
		tur.position.y -= 0.1


func _update_shots(delta: float) -> void:
	var keep: Array[Dictionary] = []
	for s in _shots:
		s["t"] += delta
		var k: float = s["t"] / s["life"]
		var node: MeshInstance3D = s["node"]
		if k >= 1.0:
			node.visible = false
			continue
		keep.append(s)
		if s["kind"] == "beam":
			node.scale.x = 1.0 - k
			node.scale.z = 1.0 - k
			continue
		var p: Vector3 = s["from"].lerp(s["to"], k) + Vector3(0, sin(k * PI) * s["arc"], 0)
		var ahead: Vector3 = s["from"].lerp(s["to"], minf(1.0, k + 0.05)) + Vector3(0, sin(minf(1.0, k + 0.05) * PI) * s["arc"], 0)
		node.position = p
		if ahead.distance_to(p) > 0.001:
			node.look_at(ahead, Vector3.UP if absf((ahead - p).normalized().y) < 0.99 else Vector3.RIGHT)
			node.rotate_object_local(Vector3.RIGHT, PI * 0.5)
		if s["kind"] == "smoke":
			s["trail"] -= delta
			if s["trail"] <= 0.0:
				s["trail"] = 0.03
				_fx.burst(p, Color(0.8, 0.8, 0.78, 0.5), 2, 0.2, 0.8, 0.25, 0.0, 0.3, 1.0, "smoke")
	_shots = keep


func _camera_input(delta: float) -> void:
	var e := game.engine
	if game.demo:
		if _hot.x >= 0:
			_cam_goal = _cam_goal.lerp(_hot, minf(1.0, delta * 0.6))
		_zoom_goal = 1.0 + 0.12 * sin(_time * 0.1)
	else:
		var pan := Vector2.ZERO
		if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_Q):
			pan.x -= 1
		if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
			pan.x += 1
		if Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_Z):
			pan.y -= 1
		if Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S):
			pan.y += 1
		var mp := get_viewport().get_mouse_position()
		var vs := get_viewport().get_visible_rect().size
		if DisplayServer.window_is_focused() and Rect2(Vector2.ZERO, vs).has_point(mp):
			if mp.x < 6:
				pan.x -= 1
			elif mp.x > vs.x - 6:
				pan.x += 1
			if mp.y < 6:
				pan.y -= 1
			elif mp.y > vs.y - 6:
				pan.y += 1
		_cam_goal += pan.limit_length(1.0) * delta * 18.0 * _zoom
		if Input.is_key_pressed(KEY_SPACE):
			var f := e.fort_of(Team.RED)
			if not f.is_empty():
				_cam_goal = e._center(f) + Vector2(0, 3)
	_cam_goal = _cam_goal.clamp(Vector2(4, 4), Vector2(e.map.w - 4, e.map.h - 2))


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_goal = clampf(_zoom_goal * 0.9, 0.55, 1.6)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_goal = clampf(_zoom_goal * 1.1, 0.55, 1.6)


## Centres the camera on a map point (the minimap).
func look_at_map(p: Vector2) -> void:
	_cam_goal = p


func _place_camera(delta: float) -> void:
	var k := minf(1.0, delta * 6.0)
	_cam_focus = _cam_focus.lerp(_cam_goal, k)
	_zoom = lerpf(_zoom, _zoom_goal, k)
	_shake = maxf(0.0, _shake - delta * 2.5)
	var j := Vector3(sin(_time * 53.0), 0, cos(_time * 47.0)) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var target := w(_cam_focus) + j
	camera.position = target + Vector3(0, 12.5, 8.5) * _zoom
	camera.look_at(target, Vector3.UP)
