class_name HopView3D
extends Node3D
## Hopline in 3D: a toy canal town seen from behind the start bank. The road is lined with lamps, the canal glints,
## logs bob and turtles dip under, the frog springs from cell to cell, and the hedge at the top holds the five bays.
## Cell (x, row) is world (x - 7, 0, row - 6): the frog hops towards -Z.

const E = preload("res://games/hopline/engine/hop_engine.gd")
const M := "res://games/hopline/art/models/"
const PAINTS := [Color(0.9, 0.25, 0.2), Color(0.2, 0.5, 0.9), Color(0.95, 0.75, 0.2), Color(0.3, 0.75, 0.4), Color(0.9, 0.5, 0.75)]
const LOGS := {3.0: "log_short", 4.0: "log_mid", 6.0: "log_long"}

@export var game: HopGame

var camera: Camera3D
var _stage: Node3D
var _objs: Array = []        ## per lane: Array of nodes (one per object)
var _frog: Node3D
var _frog_anim: AnimationPlayer
var _homes: Array[Node3D] = []
var _fly: Node3D
var _croc: Node3D
var _lady: Node3D
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _mats := {}


static func cell(x: float, row: float, y := 0.0) -> Vector3:
	return Vector3(x - 7.0, y, row - 6.0)


func _ready() -> void:
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.35, 0.55, 0.85)
	sm.sky_horizon_color = Color(0.95, 0.8, 0.65)
	sm.ground_horizon_color = Color(0.6, 0.55, 0.5)
	sky.sky_material = sm
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.4
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.5
	env.glow_hdr_threshold = 1.1
	env.ssao_enabled = true
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -40, 0)
	sun.light_energy = 1.15
	sun.light_color = Color(1.0, 0.92, 0.8)
	sun.shadow_enabled = true
	sun.shadow_blur = 1.2
	sun.directional_shadow_max_distance = 40.0
	add_child(sun)
	camera = Camera3D.new()
	camera.fov = 40
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String, size := Vector3(0.8, 0.4, 0.6), col := Color(0.5, 0.6, 0.4)) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	b.material = m
	mi.mesh = b
	mi.position.y = size.y * 0.5
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = col
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _on_stage(e: HopEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_objs.clear()
	_homes.clear()
	_build_ground(e)
	for r in E.ROWS:
		var nodes: Array = []
		var ln: Dictionary = e.lanes[r]
		var i := 0
		for o in ln["objs"]:
			var n := _object(o, ln, i)
			_stage.add_child(n)
			nodes.append(n)
			i += 1
		_objs.append(nodes)
	_frog = _scene("frog", Vector3(0.5, 0.35, 0.6), Color(0.3, 0.8, 0.3))
	_stage.add_child(_frog)
	_frog_anim = _frog.find_child("AnimationPlayer", true, false)
	_play(_frog_anim, "idle", true)
	for b in 5:
		var h := _scene("frog", Vector3(0.5, 0.35, 0.6), Color(0.3, 0.8, 0.3))
		h.position = cell(E.BAYS[b], 0, 0.02)
		h.rotation.y = PI
		h.visible = false
		_stage.add_child(h)
		_homes.append(h)
	_fly = _scene("fly", Vector3(0.2, 0.2, 0.2), Color(1.0, 1.0, 0.5))
	_fly.visible = false
	_stage.add_child(_fly)
	_croc = _scene("croc", Vector3(0.8, 0.3, 0.8), Color(0.3, 0.5, 0.2))
	_croc.visible = false
	_croc.rotation.y = PI * 0.5
	_stage.add_child(_croc)
	_lady = _scene("lady_frog", Vector3(0.4, 0.3, 0.5), Color(1.0, 0.5, 0.7))
	_lady.visible = false
	_stage.add_child(_lady)
	_place_camera()


func _object(o: Dictionary, ln: Dictionary, i: int) -> Node3D:
	var type: String = o["type"]
	var n: Node3D
	if type.begins_with("turtle"):
		n = Node3D.new()
		for k in int(o["len"]):
			var t := _scene("turtle", Vector3(0.8, 0.3, 0.8), Color(0.3, 0.55, 0.3))
			t.position.x = k + 0.5 - o["len"] * 0.5
			t.rotation.y = PI if ln["dir"] < 0 else 0.0
			_play(t.find_child("AnimationPlayer", true, false), "swim", true)
			n.add_child(t)
	elif ln["river"]:
		n = _scene(LOGS.get(o["len"], "log_mid"), Vector3(o["len"], 0.4, 0.7), Color(0.5, 0.35, 0.2))
		n.rotation.y = 0.0 if i % 2 == 0 else PI  # vary the look of logs (they are symmetric enough)
	else:
		n = _scene(type, Vector3(o["len"], 0.6, 0.7), PAINTS[i % PAINTS.size()])
		_tint(n, "paint", PAINTS[(i + type.length()) % PAINTS.size()])
		n.rotation.y = 0.0 if ln["dir"] > 0 else PI
	return n


## Banks, road, median, the canal and the hedge, a few cells wider than the board on each side, and the town around.
func _build_ground(e: HopEngine) -> void:
	for r in E.ROWS:
		var ln: Dictionary = e.lanes[r]
		for x in range(-5, E.W + 6):
			var tile := ""
			if r == 12 or r == 6:
				tile = "bank_tile" if r == 12 else "median_tile"
			elif r >= 7:
				tile = "road_tile_line" if r != 7 and ResourceLoader.exists(M + "road_tile_line.glb") else "road_tile"
			elif r == 0:
				continue
			else:
				continue
			var t := _scene(tile, Vector3(1, 0.05, 1), Color(0.3, 0.3, 0.32) if r >= 7 and r <= 11 else Color(0.4, 0.65, 0.3))
			t.position = cell(x + 0.5, r, 0.0)
			_stage.add_child(t)
	# the canal: one sheet of water below the banks, with stone edges
	var water := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(E.W + 12, 5.0)
	pm.subdivide_width = 60
	pm.subdivide_depth = 20
	water.mesh = pm
	var wm := ShaderMaterial.new()
	wm.shader = load("res://games/hopline/view3d/canal.gdshader")
	water.material_override = wm
	water.position = cell(7.0, 3.0, -0.1)
	_stage.add_child(water)
	for x in range(-5, E.W + 6):
		for r in [5.5, 0.5]:
			var edge := _scene("water_edge", Vector3(1, 0.15, 0.15), Color(0.6, 0.58, 0.55))
			edge.position = cell(x + 0.5, r, 0.0)
			edge.rotation.y = 0.0 if r > 3 else PI
			_stage.add_child(edge)
	# the hedge row with its bays
	for x in range(-5, E.W + 6):
		var xc := float(x)
		if E.BAYS.has(xc):
			var b := _scene("home_bay", Vector3(1, 0.2, 1), Color(0.3, 0.5, 0.35))
			b.position = cell(xc, 0, 0.0)
			_stage.add_child(b)
		else:
			var h := _scene("hedge_block", Vector3(1, 0.8, 1), Color(0.2, 0.45, 0.2))
			h.position = cell(xc, 0, 0.0)
			_stage.add_child(h)
	# the town: houses behind the hedge and behind the start bank, lamps along the road, trees
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	# houses only behind the hedge: in front they would hide the start bank
	for x in range(-8, E.W + 9, 2):
		var n := _scene("house_a" if rng.randf() < 0.5 else "house_b", Vector3(1.6, 1.8, 1.4), Color(0.85, 0.7, 0.55))
		n.position = cell(x + rng.randf_range(-0.2, 0.2), -1.9, 0.0)
		_stage.add_child(n)
	# a grass verge in front of the start bank
	var verge := MeshInstance3D.new()
	var vm := PlaneMesh.new()
	vm.size = Vector2(E.W + 14, 4.0)
	verge.mesh = vm
	verge.material_override = Pbr.material("grass", Color(0.75, 0.9, 0.6), 0.5)
	verge.position = cell(7.0, 14.5, -0.02)
	_stage.add_child(verge)
	# and the land all round, under everything
	var land := MeshInstance3D.new()
	var lm := PlaneMesh.new()
	lm.size = Vector2(80, 60)
	land.mesh = lm
	land.material_override = Pbr.material("grass", Color(0.6, 0.75, 0.5), 0.5)
	land.position = cell(7.0, 4.0, -0.4)
	_stage.add_child(land)
	for x in range(-4, E.W + 5, 3):
		for r in [6.45, 12.45]:
			var l := _scene("lamp_post", Vector3(0.1, 1.6, 0.1), Color(0.2, 0.2, 0.2))
			l.position = cell(x, r, 0.0)
			_stage.add_child(l)
	for i in 10:
		var t := _scene("tree", Vector3(0.6, 1.5, 0.6), Color(0.25, 0.55, 0.25))
		var front := i % 2 == 0
		t.position = cell(rng.randf_range(-5, E.W + 5) if not front else [-3.5, -2.0, E.W + 2.0, E.W + 3.5, -4.5][i / 2], 13.4 if front else -0.9, 0.0)
		_stage.add_child(t)


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.05)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hop":
			_play(_frog_anim, "hop")
		"land":
			if e.lanes[d["row"]]["river"]:
				_fx.burst(cell(e.x, e.row, 0.1), Color(0.8, 0.9, 1.0), 6, 1.0, 0.4, 0.05, 0.0, -4.0, 1.0)
		"die":
			var p := cell(d["x"], d["row"], 0.2)
			if d["how"] in ["drown", "swept"]:
				_play(_frog_anim, "drown")
				_fx.burst(p, Color(0.7, 0.85, 1.0), 24, 2.0, 0.7, 0.08, 0.0, -6.0, 1.0)
			else:
				_play(_frog_anim, "splat")
				_fx.burst(p, Color(0.4, 0.8, 0.3), 20, 2.0, 0.5, 0.07, 0.0, -6.0, 1.0)
				_shake = 0.3
		"home":
			_homes[d["bay"]].visible = true
			_play(_homes[d["bay"]].find_child("AnimationPlayer", true, false), "home")
			_fx.burst(cell(E.BAYS[d["bay"]], 0, 0.4), Color(1.0, 0.85, 0.4), 20, 2.0, 0.6, 0.08, 1.0, -2.0, 1.0, "glow")
		"all_home":
			for i in 5:
				_fx.burst(cell(E.BAYS[i], 0, 0.6), Color(1.0, 0.8, 0.4), 16, 3.0, 0.8, 0.08, 1.0, -3.0, 1.0, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _frog == null:
		return
	# lanes
	for r in E.ROWS:
		var ln: Dictionary = e.lanes[r]
		var nodes: Array = _objs[r]
		for i in nodes.size():
			var o: Dictionary = ln["objs"][i]
			var n: Node3D = nodes[i]
			var ox := e.obj_x(r, o, e.time)
			var bob := 0.0
			if ln["river"]:
				bob = -0.1 + sin(_time * 2.0 + i + r) * 0.03 - e.sunk(o, e.time) * 0.45
			var np := cell(ox + o["len"] * 0.5, r, bob)
			if not ln["river"] and n.has_meta("last"):
				# roll the wheels by the distance travelled
				var dist: float = np.x - (n.get_meta("last") as Vector3).x
				for w in n.find_children("wheel_*", "Node3D", true, false):
					(w as Node3D).rotation.z -= dist / 0.14 * (1.0 if ln["dir"] > 0 else -1.0)
			n.set_meta("last", np)
			n.position = np
			n.visible = ox + o["len"] > -5.5 and ox < E.W + 5.5
	# the frog: an arc while in the air
	var p := cell(e.x, e.row, 0.0)
	if e.hop_left > 0:
		var k := 1.0 - float(e.hop_left) / E.HOP_TICKS
		p = cell(e.hop_from.x, e.hop_from.y, 0.0).lerp(cell(e.x, e.row, 0.0), k)
		p.y = sin(k * PI) * 0.15  # the hop animation adds its own spring
		if e.lanes[e.row]["river"]:
			p.y += k * 0.1
	elif e.lanes[e.row]["river"]:
		p.y = 0.1 + sin(_time * 2.0) * 0.03  # riding a log or a turtle's back
	_frog.position = p
	var f := Vector2(e.facing)
	_frog.rotation.y = lerp_angle(_frog.rotation.y, atan2(-f.x, -f.y), minf(1.0, delta * 25.0))
	_frog.visible = not (e.phase == E.Phase.DYING and e.phase_t < 0.6)
	if e.phase == E.Phase.PLAY and e.hop_left == 0 and _frog_anim and not _frog_anim.is_playing():
		_play(_frog_anim, "idle", true)
	if e.phase == E.Phase.READY and _frog_anim and _frog_anim.current_animation in ["splat", "drown"]:
		_play(_frog_anim, "idle", true)
	for b in 5:
		_homes[b].visible = e.filled[b]
	_fly.visible = e.fly_bay >= 0
	if _fly.visible:
		_fly.position = cell(E.BAYS[e.fly_bay], 0, 0.45 + sin(_time * 6.0) * 0.08)
	_croc.visible = e.croc_bay >= 0
	if _croc.visible:
		_croc.position = cell(E.BAYS[e.croc_bay], 0, -0.35 + e.croc_rise * 0.35)
	_lady.visible = not e.lady.is_empty()
	if _lady.visible:
		if e.lady.get("on", false):
			_lady.position = _frog.position + Vector3(0, 0.25, 0.05)
			_lady.rotation.y = _frog.rotation.y
		else:
			var o: Dictionary = e.lanes[e.lady["row"]]["objs"][e.lady["obj"]]
			_lady.position = cell(e.obj_x(e.lady["row"], o, e.time) + o["len"] * 0.5, e.lady["row"], 0.25)
	_shake = maxf(0.0, _shake - delta * 1.5)
	_place_camera()


func _place_camera() -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var j := Vector3(sin(_time * 50.0), 0, cos(_time * 43.0)) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var need := maxf(8.2, 10.5 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var target := Vector3(0, 0, 0.4)
	camera.position = target + Vector3(0, 0.78, 0.62).normalized() * dist + j
	camera.look_at(target + j, Vector3.UP)
