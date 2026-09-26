class_name CratesView3D
extends Node3D
## Crate Keeper in 3D: the puzzle as a lamp-lit corner of a harbour warehouse at dusk, seen from above at an angle.
## Oak boards inside the room, brick walls round it, goal plates that glow, crates that slide with a little squash and
## light up when they sit on a goal, the keeper walking and leaning into the pushes, harbour clutter around.
## Cell (x, y) is centred at world (x, 0, y).

const M := "res://games/crates/art/models/"
const MOVE_TIME := 0.14

@export var game: CratesGame

var camera: Camera3D
var _board: Node3D
var _fx: CratesEffects
var _crates: Array[Node3D] = []    ## by crate index
var _crate_lit: Array[bool] = []
var _keeper: Node3D
var _anim: AnimationPlayer
var _anim_last := ""
var _slides: Array[Dictionary] = []  ## {node, from, to, t}
var _keeper_slide := {}
var _pushing_t := 0.0
var _time := 0.0
var _cam_target := Vector3.ZERO


func _ready() -> void:
	game.view = self
	var env := Environment.new()
	var sky := ProceduralSkyMaterial.new()
	sky.sky_top_color = Color(0.12, 0.14, 0.3)
	sky.sky_horizon_color = Color(0.85, 0.5, 0.35)
	var s := Sky.new()
	s.sky_material = sky
	env.background_mode = Environment.BG_SKY
	env.sky = s
	Look.sky_ambient(env, Color(0.45, 0.42, 0.55), 0.5)
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.0
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_hdr_threshold = 0.95
	env.ssao_enabled = true
	env.ssao_intensity = 1.8
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.15
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()  # low dusk sun through the doors
	sun.rotation_degrees = Vector3(-38, 55, 0)
	sun.light_color = Color(1.0, 0.72, 0.5)
	sun.light_energy = 0.9
	sun.shadow_enabled = true
	sun.shadow_blur = 1.2
	add_child(sun)
	camera = Camera3D.new()
	camera.fov = 36
	camera.current = true
	add_child(camera)
	_fx = CratesEffects.new()
	add_child(_fx)
	game.puzzle_started.connect(_on_puzzle)
	if game.engine:
		_on_puzzle(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.8, 0.8, 0.8)
	mi.mesh = b
	mi.position.y = 0.4
	n.add_child(mi)
	return n


func screen_to_cell(screen: Vector2):
	var from := camera.project_ray_origin(screen)
	var dir := camera.project_ray_normal(screen)
	if absf(dir.y) < 0.001:
		return null
	var t := -from.y / dir.y
	var hit := from + dir * t
	var c := Vector2i(roundi(hit.x), roundi(hit.z))
	return c if game.engine.level.inside(c) or game.engine.crate_at(c) >= 0 else null


func _on_puzzle(e: CratesEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_crates.clear()
	_crate_lit.clear()
	_slides.clear()
	e.event.connect(_on_event)
	var lv := e.level
	for y in lv.h:
		for x in lv.w:
			var c := Vector2i(x, y)
			var p := Vector3(x, 0, y)
			if lv.inside(c):
				var f := _scene("floor_%d" % ((x * 3 + y * 5) % 2))
				f.position = p
				_board.add_child(f)
			elif lv.wall(c):
				var touches := false
				for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1)]:
					if lv.inside(c + d):
						touches = true
				if touches:
					var wn := _scene("window_wall" if (x * 7 + y * 3) % 9 == 0 and y == 0 else "wall_%d" % ((x + y) % 2))
					wn.position = p
					wn.scale = Vector3(1, 0.62, 1)  # low walls: the whole room stays in view
					_board.add_child(wn)
	for g in lv.goals:
		var n := _scene("goal")
		n.position = Vector3(g.x, 0.01, g.y)
		_board.add_child(n)
		var l := OmniLight3D.new()
		l.light_color = Color(0.5, 1.0, 0.6)
		l.light_energy = 0.35
		l.omni_range = 1.6
		l.position = Vector3(g.x, 0.3, g.y)
		_board.add_child(l)
	for i in e.crates.size():
		var n := _scene("crate")
		n.position = Vector3(e.crates[i].x, 0, e.crates[i].y)
		n.rotation.y = float(i % 4) * PI * 0.5
		_board.add_child(n)
		_crates.append(n)
		_crate_lit.append(false)
		_set_lit(i, e.goals.has(e.crates[i]))
	_keeper = _scene("keeper")
	_keeper.scale = Vector3.ONE * 1.3
	_keeper.position = Vector3(e.keeper.x, 0, e.keeper.y)
	_board.add_child(_keeper)
	_anim = _keeper.find_child("AnimationPlayer", true, false)
	if _anim:
		for a in _anim.get_animation_list():
			_anim.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "walk", "push", "cheer"] else Animation.LOOP_NONE
	_anim_last = ""
	# harbour clutter and lamps around the room
	var rng := RandomNumberGenerator.new()
	rng.seed = lv.w * 131 + lv.h
	var kinds := ["barrel", "rope_coil", "sack_pile", "pallet", "crate_stack", "net_pile", "anchor"]
	for i in 16:
		var side := i % 4
		var t := rng.randf()
		var p := Vector3()
		match side:
			0: p = Vector3(-1.2 + t * (lv.w + 1.4), 0, -1.6 - rng.randf())
			1: p = Vector3(-1.2 + t * (lv.w + 1.4), 0, lv.h + 0.6 + rng.randf())
			2: p = Vector3(-1.8 - rng.randf(), 0, t * lv.h)
			3: p = Vector3(lv.w + 0.8 + rng.randf(), 0, t * lv.h)
		var n := _scene(kinds[rng.randi_range(0, kinds.size() - 1)])
		n.position = p
		n.rotation.y = rng.randf() * TAU
		_board.add_child(n)
	for corner in [Vector3(-1.5, 0, -1.5), Vector3(lv.w + 0.5, 0, -1.5), Vector3(-1.5, 0, lv.h + 0.5), Vector3(lv.w + 0.5, 0, lv.h + 0.5)]:
		var lp := _scene("lamp_post")
		lp.position = corner
		_board.add_child(lp)
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.75, 0.45)
		l.light_energy = 1.6
		l.omni_range = 9.0
		l.shadow_enabled = false
		l.position = corner + Vector3(0, 2.4, 0)
		_board.add_child(l)
	var ground := MeshInstance3D.new()  # the quay around the warehouse
	var pm := PlaneMesh.new()
	pm.size = Vector2(lv.w + 40, lv.h + 40)
	ground.mesh = pm
	ground.material_override = Pbr.material("stone_bricks", Color(0.55, 0.52, 0.5), 0.6)
	ground.position = Vector3(lv.w * 0.5, -0.02, lv.h * 0.5)
	_board.add_child(ground)
	_cam_target = Vector3(lv.w * 0.5 - 0.5, 0, lv.h * 0.5 - 0.5)
	_place_camera(e)


func _set_lit(i: int, on: bool) -> void:
	if _crate_lit[i] == on:
		return
	_crate_lit[i] = on
	var old := _crates[i]
	var n := _scene("crate_done" if on else "crate")
	n.transform = old.transform
	_board.add_child(n)
	old.queue_free()
	_crates[i] = n


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"move", "undo":
			_keeper_slide = {"from": Vector3(d["from"].x, 0, d["from"].y), "to": Vector3(d["to"].x, 0, d["to"].y), "t": 0.0}
			var ci: int = d["pushed"]
			if ci >= 0:
				var n: Node3D = _crates[ci]
				_slides.append({"node": n, "from": n.position, "to": Vector3(e.crates[ci].x, 0, e.crates[ci].y), "t": 0.0, "i": ci})
				_pushing_t = 0.35
				_fx.scuff(n.position + Vector3(0, 0.05, 0))
		"redo":
			pass
		"on_goal":
			var ci: int = d["crate"]
			get_tree().create_timer(MOVE_TIME).timeout.connect(func():
				if ci < _crates.size():
					_set_lit(ci, true)
					_fx.glow(_crates[ci].position + Vector3(0, 0.5, 0)))
		"off_goal":
			var ci2: int = d["crate"]
			_set_lit(ci2, false)
		"restart":
			_on_puzzle(e)
		"solved":
			for c in _crates:
				_fx.glow(c.position + Vector3(0, 0.6, 0))


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _keeper == null:
		return
	# the keeper glides to his cell and faces the way he walks
	if not _keeper_slide.is_empty():
		_keeper_slide["t"] += delta / MOVE_TIME
		var k := clampf(_keeper_slide["t"], 0.0, 1.0)
		_keeper.position = (_keeper_slide["from"] as Vector3).lerp(_keeper_slide["to"], k)
		if k >= 1.0:
			_keeper_slide = {}
	else:
		_keeper.position = Vector3(e.keeper.x, 0, e.keeper.y)
	var f := e.face
	_keeper.rotation.y = lerp_angle(_keeper.rotation.y, atan2(float(f.x), float(f.y)), minf(1.0, delta * 16.0))
	var keep: Array[Dictionary] = []
	for s in _slides:
		s["t"] += delta / MOVE_TIME
		var k := clampf(s["t"], 0.0, 1.0)
		var n: Node3D = _crates[s["i"]] if s["i"] < _crates.size() else s["node"]
		if not is_instance_valid(n):
			continue
		n.position = (s["from"] as Vector3).lerp(s["to"], k)
		var sq := sin(k * PI) * 0.06
		n.scale = Vector3(1.0 + sq, 1.0 - sq, 1.0 + sq)
		if k < 1.0:
			keep.append(s)
		else:
			n.scale = Vector3.ONE
	_slides = keep
	# snap anything the slides don't own (undo, restart) to the engine's cells
	if _slides.is_empty():
		for i in _crates.size():
			_crates[i].position = Vector3(e.crates[i].x, 0, e.crates[i].y)
			_set_lit(i, e.goals.has(e.crates[i]))
	_pushing_t = maxf(0.0, _pushing_t - delta)
	var want := "idle"
	if e.solved:
		want = "cheer"
	elif _pushing_t > 0.0:
		want = "push"
	elif not _keeper_slide.is_empty():
		want = "walk"
	if _anim and want != _anim_last and _anim.has_animation(want):
		_anim_last = want
		_anim.play(want, 0.1)
		_anim.speed_scale = {"walk": 1.36, "push": 2.2}.get(want, 1.0)
	_place_camera(e)


func _place_camera(e: CratesEngine) -> void:
	var lv := e.level
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(lv.h * 0.62 + 1.6, (lv.w * 0.62 + 1.2) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	camera.position = _cam_target + Vector3(0, 0.83, 0.56).normalized() * dist
	camera.look_at(_cam_target + Vector3(0, 0, 0.3), Vector3.UP)
