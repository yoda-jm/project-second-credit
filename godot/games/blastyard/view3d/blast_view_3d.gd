class_name BlastView3D
extends Node3D
## Blastyard in 3D: a toy-like arena seen from above at an angle, dressed for its theme (garden, factory, ice),
## glossy bombers in their colours, bombs that swell as the fuse burns down, crosses of fire, crates bursting into
## splinters, spinning power-ups, blocks slamming down in sudden death, and the solo stages' creatures and exit.
## Cell (x, y) is centred at world (x + 0.5, 0, y + 0.5).

const E = preload("res://games/blastyard/engine/blast_engine.gd")
const T = ArenaMap.T
const M := "res://games/blastyard/art/models/"
const COLORS := [Color(0.95, 0.95, 0.97), Color(0.95, 0.25, 0.2), Color(0.25, 0.5, 1.0), Color(1.0, 0.82, 0.2)]
const THEMES := {
	"garden": {"floor": ["grass_lush", Color(0.9, 1.0, 0.85)], "floor_b": Color(0.8, 0.92, 0.75), "sky": [Color(0.35, 0.6, 0.9), Color(0.85, 0.9, 0.95)],
		"sun": Color(1.0, 0.95, 0.85), "ambient": Color(0.6, 0.7, 0.8), "pillar": ["stone_bricks", Color(1.0, 0.95, 0.9)], "crate": ["planks", Color(1.0, 0.8, 0.55)],
		"border": ["stone_bricks", Color(0.85, 0.8, 0.75)], "dress": ["hedge", "flowerpot"]},
	"factory": {"floor": ["metal", Color(0.75, 0.72, 0.7)], "floor_b": Color(0.62, 0.6, 0.58), "sky": [Color(0.2, 0.22, 0.3), Color(0.5, 0.45, 0.42)],
		"sun": Color(1.0, 0.85, 0.65), "ambient": Color(0.55, 0.5, 0.5), "pillar": ["dark_rock", Color(2.0, 1.9, 1.8)], "crate": ["planks", Color(0.85, 0.65, 0.45)],
		"border": ["metal", Color(0.5, 0.48, 0.46)], "dress": ["pipe", "barrel"]},
	"ice": {"floor": ["beach_sand", Color(1.1, 1.18, 1.3)], "floor_b": Color(0.92, 1.0, 1.12), "sky": [Color(0.45, 0.65, 0.95), Color(0.9, 0.95, 1.0)],
		"sun": Color(0.95, 0.97, 1.0), "ambient": Color(0.7, 0.78, 0.9), "pillar": ["rock", Color(1.1, 1.2, 1.35)], "crate": ["planks", Color(0.9, 0.85, 0.8)],
		"border": ["rock", Color(0.85, 0.9, 1.0)], "dress": ["snowdrift", "ice_crystal"]},
}
const PU_COLORS := {"bomb": Color(0.3, 0.4, 1.0), "fire": Color(1.0, 0.45, 0.1), "speed": Color(0.2, 0.95, 0.5), "kick": Color(1.0, 0.85, 0.2), "skull": Color(0.6, 0.2, 0.8)}

@export var game: BlastGame

var camera: Camera3D
var _env: Environment
var _sky_mat: ProceduralSkyMaterial
var _sun: DirectionalLight3D
var _board: Node3D
var _fx: BlastEffects
var _crates := {}    ## cell -> node
var _pillars := {}   ## cell -> node (the sudden-death ones)
var _pups := {}      ## cell -> node
var _bombers := {}   ## slot -> {node, anim, last}
var _bombs := {}     ## id -> node
var _enemies := {}   ## id -> {node, anim}
var _flames: Array[Dictionary] = []  ## {node, t, life}
var _flame_pool: Array[MeshInstance3D] = []
var _exit: Node3D
var _time := 0.0
var _shake := 0.0
var _team_mats := {}


func _ready() -> void:
	_build_env()
	_fx = BlastEffects.new()
	add_child(_fx)
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color(1.0, 0.7, 0.25)
	fm.emission_enabled = true
	fm.emission = Color(1.0, 0.55, 0.15)
	fm.emission_energy_multiplier = 4.0
	fm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for i in 160:
		var f := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.36
		cap.height = 1.1
		f.mesh = cap
		f.material_override = fm
		f.visible = false
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(f)
		_flame_pool.append(f)
	game.round_started.connect(_on_round)
	if game.engine:
		_on_round(game.engine)


func _build_env() -> void:
	_sky_mat = ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = _sky_mat
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 0.88
	_env.glow_enabled = true
	_env.glow_intensity = 0.7
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_env.ssao_intensity = 1.8
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.2
	_env.adjustment_contrast = 1.06
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-58, -35, 0)
	_sun.shadow_enabled = true
	_sun.light_angular_distance = 0.6
	_sun.shadow_blur = 1.2
	_sun.directional_shadow_max_distance = 40.0
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 36
	camera.current = true
	add_child(camera)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()  # a stand-in while a model is missing
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.8, 0.8, 0.8)
	mi.mesh = bm
	mi.position.y = 0.4
	n.add_child(mi)
	return n


func _paint(n: Node, col: Color) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat == null or not mat.resource_name.to_lower().contains("team"):
				continue
			var key := [mat.resource_name, col]
			if not _team_mats.has(key):
				var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				s.albedo_color = col if not mat.resource_name.to_lower().contains("trim") else col.darkened(0.35)
				_team_mats[key] = s
			m.set_surface_override_material(i, _team_mats[key])


## Many copies of a model in one draw (its meshes merged, each with its own materials).
func _multi(model: String, xf: Array[Transform3D], only := "") -> void:
	var root := _scene(model)
	var am := ArrayMesh.new()
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		if only != "" and not _under(mi, only):
			continue
		var src := (mi as MeshInstance3D).mesh
		var local := (mi as MeshInstance3D).transform
		for s_ in src.get_surface_count():
			var st := SurfaceTool.new()
			st.create_from(src, s_)
			var arr := st.commit_to_arrays()
			var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			for i in verts.size():
				verts[i] = local * verts[i]
			arr[Mesh.ARRAY_VERTEX] = verts
			am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			am.surface_set_material(am.get_surface_count() - 1, src.surface_get_material(s_))
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


## Stone under a bright sky: no clear-coat sheen and a touch darker, so blocks keep their colour from above.
func _matte(n: Node) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or mat.emission_enabled:
				continue
			if not _team_mats.has(mat):
				var t := mat.duplicate() as StandardMaterial3D
				t.clearcoat_enabled = false
				t.albedo_color = mat.albedo_color * 0.82
				t.roughness = maxf(mat.roughness, 0.85)
				t.metallic_specular = 0.25
				_team_mats[mat] = t
			m.set_surface_override_material(i, _team_mats[mat])


## Keeps only the child named `keep` (and what hangs under it) among a model's top-level variants.
func _only(n: Node, keep: String) -> void:
	var found := n.find_child(keep, true, false)
	if found == null:
		return
	for c in found.get_parent().get_children():
		if c != found and c is Node3D and (c.name.begins_with("crate_") or c.name.begins_with("floor_")):
			c.queue_free()


func _under(n: Node, name_: String) -> bool:
	var p := n
	while p:
		if p.name == name_:
			return true
		p = p.get_parent()
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


func w(c: Vector2, y := 0.0) -> Vector3:
	return Vector3(c.x, y, c.y)


# ------------------------------------------------------------------ the arena

func _on_round(e: BlastEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_crates.clear()
	_pillars.clear()
	_pups.clear()
	_bombers.clear()
	_bombs.clear()
	_enemies.clear()
	_exit = null
	for f in _flame_pool:
		f.visible = false
	_flames.clear()
	e.event.connect(_on_event)
	var th: Dictionary = THEMES.get(e.map.theme, THEMES["garden"])
	_sky_mat.sky_top_color = th["sky"][0]
	_sky_mat.sky_horizon_color = th["sky"][1]
	_sky_mat.ground_horizon_color = th["sky"][1]
	_sky_mat.ground_bottom_color = th["sky"][1].darkened(0.5)
	Look.sky_ambient(_env, th["ambient"], 0.6)
	_sun.light_color = th["sun"]
	_sun.light_energy = 1.0 if not Look.compat() else 0.8
	var m := e.map
	# the floor: the theme's tiles, then a ground skirt around the arena
	var tname := "floor_tile_" + m.theme
	var tiles: Array[Transform3D] = []
	var tiles_a: Array[Transform3D] = []
	var tiles_b: Array[Transform3D] = []
	for y in m.h:
		for x in m.w:
			var xf := Transform3D(Basis(Vector3.UP, float((x * 3 + y) % 4) * PI * 0.5), Vector3(x + 0.5, 0, y + 0.5))
			tiles.append(xf)
			(tiles_a if (x + y) % 2 == 0 else tiles_b).append(xf)
	if ResourceLoader.exists(M + tname + ".glb"):  # the file holds two tiles, floor_a and floor_b: a checker
		_multi(tname, tiles_a, "floor_a")
		_multi(tname, tiles_b, "floor_b")
	else:
		var fa := Pbr.material(th["floor"][0], th["floor"][1], 0.5)
		for xf in tiles:
			_box(xf.origin + Vector3(0, -0.05, 0), Vector3(1.0, 0.1, 1.0), fa)
	_box(Vector3(m.w * 0.5, -0.2, m.h * 0.5), Vector3(m.w + 30, 0.2, m.h + 30), Pbr.material(th["floor"][0], th["floor_b"].darkened(0.25), 0.3))
	var pillar_mat := Pbr.local(th["pillar"][0], th["pillar"][1], 1.2)
	var border_mat := Pbr.local(th["border"][0], th["border"][1], 1.2)
	for y in m.h:
		for x in m.w:
			var c := Vector2i(x, y)
			var pos := Vector3(x + 0.5, 0, y + 0.5)
			match m.at(c):
				T.PILLAR:
					var edge := x == 0 or y == 0 or x == m.w - 1 or y == m.h - 1
					var nm := ("wall_" if edge else "pillar_") + m.theme
					var n := _scene(nm)
					if not ResourceLoader.exists(M + nm + ".glb"):
						n = Node3D.new()
						var b := _box(Vector3.ZERO, Vector3(0.96, 0.9, 0.96), border_mat if edge else pillar_mat)
						b.position = Vector3(0, 0.45, 0)
						b.reparent(n, false)
					n.position = pos
					_matte(n)
					_board.add_child(n)
				T.CRATE:
					var cr := _scene("crate_" + m.theme)
					_only(cr, "crate_%d" % ((x * 7 + y * 3) % 2))  # the file holds two crates on top of each other
					cr.position = pos
					cr.rotation.y = float((x + y) % 4) * PI * 0.5
					_board.add_child(cr)
					_crates[c] = cr
	# dressing around the arena
	var rng := RandomNumberGenerator.new()
	rng.seed = m.w * 31 + m.h
	for i in 28:
		var side := i % 4
		var t := rng.randf()
		var p := Vector3()
		match side:
			0: p = Vector3(t * m.w, 0, -1.3 - rng.randf() * 2.0)
			1: p = Vector3(t * m.w, 0, m.h + 1.0 + rng.randf() * 2.0)
			2: p = Vector3(-1.3 - rng.randf() * 2.0, 0, t * m.h)
			3: p = Vector3(m.w + 1.3 + rng.randf() * 2.0, 0, t * m.h)
		var kinds: Array = th["dress"]
		var n := _scene(kinds[i % kinds.size()])
		if n.get_child_count() > 0 and not ResourceLoader.exists(M + kinds[i % kinds.size()] + ".glb"):
			n.queue_free()
			continue
		n.position = p
		n.rotation.y = rng.randf() * TAU
		n.scale = Vector3.ONE * rng.randf_range(0.7, 1.0)
		_board.add_child(n)
	# bombers and creatures
	for p in e.players:
		var n := _scene("bomber")
		_board.add_child(n)
		_paint(n, COLORS[p["slot"] % COLORS.size()])
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		if ap:
			for a in ap.get_animation_list():
				ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "walk", "win"] else Animation.LOOP_NONE
		_bombers[p["slot"]] = {"node": n, "anim": ap, "last": "", "dead_t": 0.0}
	for en in e.enemies:
		var n := _scene(en["kind"])
		_board.add_child(n)
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		if ap and ap.has_animation("move"):
			ap.get_animation("move").loop_mode = Animation.LOOP_LINEAR
			ap.play("move")
		_enemies[en["id"]] = {"node": n, "anim": ap, "dead_t": -1.0}
	_place_camera(e)


func _place_camera(e: BlastEngine) -> void:
	var c := Vector3(e.map.w * 0.5, 0, e.map.h * 0.5 + 0.6)
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(e.map.h * 0.53, e.map.w * 0.5 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	camera.position = c + Vector3(0, 0.86, 0.52).normalized() * dist
	camera.look_at(c, Vector3.UP)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"bomb":
			pass
		"explode":
			var cells: Array = d["cells"]
			var centre: Vector2i = d["cell"]
			_flame_at(centre, Vector3.ZERO)
			for c in cells:
				if c != centre:
					var dir := Vector2(c - centre).normalized()
					_flame_at(c, Vector3(dir.x, 0, dir.y))
			_fx.blast(w(Vector2(centre) + Vector2(0.5, 0.5), 0.5), 1.0 + 0.1 * d["fire"])
			_shake = maxf(_shake, 0.35 if d["chain"] else 0.25)
		"crate":
			var c: Vector2i = d["cell"]
			if _crates.has(c):
				var n: Node3D = _crates[c]
				_crates.erase(c)
				_fx.splinters(n.position + Vector3(0, 0.4, 0))
				var tw := create_tween()
				tw.tween_property(n, "scale", Vector3(1.2, 0.05, 1.2), 0.18)
				tw.tween_callback(n.queue_free)
			if d["drop"] != "":
				_add_powerup(c, d["drop"])
			if d.get("exit", false):
				_show_exit(c, false)
		"pickup":
			var c: Vector2i = d["cell"]
			if _pups.has(c):
				_fx.sparkle(_pups[c].position, PU_COLORS.get(d["kind"], Color.WHITE))
				_pups[c].queue_free()
				_pups.erase(c)
		"death":
			_fx.poof(w(d["pos"], 0.5), COLORS[d["slot"] % COLORS.size()])
		"enemy_die":
			var v: Dictionary = _enemies.get(d["id"], {})
			if not v.is_empty():
				v["dead_t"] = 0.0
				_fx.poof(w(d["pos"], 0.4), Color(0.8, 0.5, 1.0))
		"block_drop":
			var c: Vector2i = d["cell"]
			if _crates.has(c):
				_crates[c].queue_free()
				_crates.erase(c)
			if _pups.has(c):
				_pups[c].queue_free()
				_pups.erase(c)
			var n := _scene("pillar_" + e.map.theme)
			n.position = Vector3(c.x + 0.5, 7.0, c.y + 0.5)
			_board.add_child(n)
			var tw := create_tween()
			tw.tween_property(n, "position:y", 0.0, 0.22).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
			tw.tween_callback(func(): _fx.dust(n.position + Vector3(0, 0.1, 0)); _shake = maxf(_shake, 0.12))
		"exit_open":
			_show_exit(d["cell"], true)
	# live powerups that burnt: drop nodes whose cell no longer holds one
	for c in _pups.keys():
		if not e.powerups.has(c):
			_pups[c].queue_free()
			_pups.erase(c)


func _flame_at(c: Vector2i, dir: Vector3) -> void:
	if _flame_pool.is_empty():
		return
	var f: MeshInstance3D = _flame_pool.pop_front()
	_flame_pool.append(f)
	f.visible = true
	var basis := Basis()
	if dir != Vector3.ZERO:
		basis = Basis(Vector3.UP.cross(dir).normalized() if absf(dir.y) < 0.9 else Vector3.RIGHT, PI * 0.5)
	f.transform = Transform3D(basis, Vector3(c.x + 0.5, 0.45, c.y + 0.5))
	_flames.append({"node": f, "t": 0.0, "life": E.FLAME_TIME, "basis": basis})
	_fx.fire(f.position)


func _add_powerup(c: Vector2i, kind: String) -> void:
	var n := _scene("pu_" + kind)
	n.position = Vector3(c.x + 0.5, 0.25, c.y + 0.5)
	_board.add_child(n)
	_pups[c] = n
	if not ResourceLoader.exists(M + "pu_" + kind + ".glb"):
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var m := StandardMaterial3D.new()
			m.albedo_color = PU_COLORS.get(kind, Color.WHITE)
			m.emission_enabled = true
			m.emission = PU_COLORS.get(kind, Color.WHITE)
			m.emission_energy_multiplier = 1.5
			(mi as MeshInstance3D).material_override = m
			mi.scale = Vector3.ONE * 0.5


func _show_exit(c: Vector2i, open_: bool) -> void:
	if _exit == null:
		_exit = _scene("exit_door")
		_exit.position = Vector3(c.x + 0.5, 0, c.y + 0.5)
		_board.add_child(_exit)
	if open_:
		_fx.sparkle(_exit.position + Vector3(0, 0.5, 0), Color(0.5, 1.0, 0.7))


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null:
		return
	_update_bombers(e, delta)
	_update_bombs(e)
	_update_enemies(e, delta)
	for c in _pups:
		var n: Node3D = _pups[c]
		n.rotation.y += delta * 2.0
		n.position.y = 0.25 + 0.08 * sin(_time * 3.0 + c.x)
	var keep: Array[Dictionary] = []
	for f in _flames:
		f["t"] += delta
		var k: float = f["t"] / f["life"]
		var node: MeshInstance3D = f["node"]
		if k >= 1.0:
			node.visible = false
			continue
		var s := (1.0 - k * k) * (1.0 + 0.15 * sin(_time * 40.0 + node.position.x))
		node.transform.basis = (f["basis"] as Basis).scaled(Vector3(s, 1.0, s))
		keep.append(f)
	_flames = keep
	_shake = maxf(0.0, _shake - delta * 2.0)
	_place_camera(e)
	var j := Vector3(sin(_time * 51.0), 0, cos(_time * 43.0)) * _shake * _shake * (0.35 if Settings.camera_shake else 0.0)
	camera.position += j


func _update_bombers(e: BlastEngine, delta: float) -> void:
	for p in e.players:
		var v: Dictionary = _bombers.get(p["slot"], {})
		if v.is_empty():
			continue
		var n: Node3D = v["node"]
		var d: Vector2i = p["dir"]
		n.position = w(p["pos"])
		var yaw := atan2(float(d.x), float(d.y))
		n.rotation.y = lerp_angle(n.rotation.y, yaw, minf(1.0, delta * 14.0))
		var want := "idle"
		if not p["alive"]:
			want = "die"
			v["dead_t"] += delta
			n.visible = v["dead_t"] < 1.6
		elif e.phase == E.Phase.OVER and e.winner == p["slot"]:
			want = "win"
		elif p["moving"]:
			want = "walk"
		if p["skull"] > 0.0 and p["alive"]:
			n.scale = Vector3.ONE * (1.0 + 0.06 * sin(_time * 20.0))
		else:
			n.scale = Vector3.ONE
		if want != v["last"] and v["anim"]:
			v["last"] = want
			var ap: AnimationPlayer = v["anim"]
			if ap.has_animation(want):
				ap.play(want, 0.12)
			if want == "walk":
				ap.speed_scale = p["speed"] / E.BASE_SPEED


func _update_bombs(e: BlastEngine) -> void:
	var seen := {}
	for b in e.bombs:
		seen[b["id"]] = true
		var n: Node3D = _bombs.get(b["id"])
		if n == null:
			n = _scene("bomb")
			_board.add_child(n)
			_bombs[b["id"]] = n
			n.scale = Vector3.ONE * 0.2
		var left: float = b["fuse"] / E.FUSE
		var pulse := 1.0 + (0.08 + 0.18 * (1.0 - left)) * absf(sin(_time * (6.0 + 14.0 * (1.0 - left))))
		n.scale = n.scale.lerp(Vector3.ONE * pulse, 0.3)
		n.position = w(b["pos"])
		var spark := n.find_child("spark", true, false) as Node3D
		if spark:
			spark.scale = Vector3.ONE * (0.7 + 0.6 * randf())
	for id in _bombs.keys():
		if not seen.has(id):
			_bombs[id].queue_free()
			_bombs.erase(id)


func _update_enemies(e: BlastEngine, delta: float) -> void:
	for en in e.enemies:
		var v: Dictionary = _enemies.get(en["id"], {})
		if v.is_empty():
			continue
		var n: Node3D = v["node"]
		if v["dead_t"] >= 0.0:
			v["dead_t"] += delta
			n.scale = Vector3.ONE * maxf(0.0, 1.0 - v["dead_t"] * 2.5)
			continue
		n.position = w(en["pos"], 0.3 if en["kind"] in ["bat", "ghost"] else 0.0)
		var d: Vector2i = en["dir"]
		if d != Vector2i.ZERO:
			n.rotation.y = lerp_angle(n.rotation.y, atan2(float(d.x), float(d.y)), minf(1.0, delta * 10.0))
