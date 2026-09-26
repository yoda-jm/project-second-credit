class_name FizzView3D
extends Node3D
## Fizzlings in 3D: an underwater toybox seen straight on. Platforms are glossy tiles in the level's colour, kelp and
## coral sway behind, light ripples down through the water, bubbles wobble and shine with toys struggling inside,
## treats bob and spin, and the axolotls waddle, puff and ride. Tile (x, y) is world ((x - 16) / 2, (13 - y) / 2).

const E = preload("res://games/fizzlings/engine/fizz_engine.gd")
const M := "res://games/fizzlings/art/models/"
const T := 0.5
const SKINS := [Color(1.0, 0.62, 0.72), Color(0.6, 0.7, 1.0)]
const TOY_MODELS := {"beetle": "toy_beetle", "spring": "toy_spring", "flyer": "toy_flyer"}

@export var game: FizzGame

var camera: Camera3D
var _stage: Node3D
var _heroes: Array[Dictionary] = []
var _bubbles := {}    ## id -> {node, trapped (node or null)}
var _toys := {}       ## id -> {node, anim, angry}
var _treats: Array[Node3D] = []
var _ghost: Node3D
var _fx: Bursts
var _time := 0.0
var _mats := {}
var _backdrop_mat: ShaderMaterial


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3((p.x - 16.0) * T, (13.0 - p.y) * T, z)


func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.08, 0.16)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.5, 0.75, 1.0)
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.glow_bloom = 0.06
	env.glow_hdr_threshold = 1.0
	env.fog_enabled = true  # the water hazes what lies behind
	env.fog_light_color = Color(0.05, 0.2, 0.35)
	env.fog_density = 0.09
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-60, 20, 0)
	sun.light_energy = 1.1
	sun.light_color = Color(0.9, 1.0, 1.0)
	sun.shadow_enabled = true
	add_child(sun)
	camera = Camera3D.new()
	camera.fov = 32
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	_build_backdrop()
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String, size := Vector3(0.45, 0.45, 0.45), col := Color(0.8, 0.8, 0.9)) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := SphereMesh.new()
	b.radius = size.x
	b.height = size.x * 2.0
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	b.material = m
	mi.mesh = b
	mi.position.y = size.x
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color, emission := false) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = Color(col, t.albedo_color.a)
				if emission or t.emission_enabled:
					t.emission_enabled = true
					t.emission = col
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.08)


func _build_backdrop() -> void:
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(40, 24)
	q.mesh = qm
	_backdrop_mat = ShaderMaterial.new()
	_backdrop_mat.shader = load("res://games/fizzlings/view3d/deep_water.gdshader")
	q.material_override = _backdrop_mat
	q.position = Vector3(0, 0, -6.0)
	add_child(q)
	var rng := RandomNumberGenerator.new()
	rng.seed = 18
	var props := ["bg_kelp", "bg_kelp", "bg_coral", "bg_shell", "bg_toy_block", "bg_kelp", "bg_coral"]
	for i in 22:
		var kind: String = props[rng.randi_range(0, props.size() - 1)]
		var n := _scene(kind, Vector3(0.4, 1.0, 0.4), Color(0.3, 0.7, 0.5))
		n.position = Vector3(rng.randf_range(-11.0, 11.0), -6.8, rng.randf_range(-5.0, -2.2))
		n.rotation.y = rng.randf_range(-0.6, 0.6)
		n.scale = Vector3.ONE * rng.randf_range(0.8, 1.6)
		add_child(n)
		_play(n.find_child("AnimationPlayer", true, false), "sway", true)
	for x in [-9.5, 9.5, -5.0, 5.5]:
		var col := _scene("bg_bubble_column", Vector3(0.2, 1, 0.2), Color(0.8, 0.9, 1.0))
		col.position = Vector3(x, -6.8, -2.5)
		add_child(col)
		_play(col.find_child("AnimationPlayer", true, false), "rise", true)


func _on_level(e: FizzEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_heroes.clear()
	_bubbles.clear()
	_toys.clear()
	_treats.clear()
	_ghost = null
	var colour: Color = e.level.colour
	_backdrop_mat.set_shader_parameter("tint", colour)
	for y in E.H:
		for x in E.W:
			if not e.is_solid(x, y):
				continue
			var top := y > 0 and not e.is_solid(x, y - 1)
			var n := _scene("tile_top" if top else "tile_block", Vector3(0.25, 0.25, 0.25), colour)
			_tint(n, "tile_face", colour.darkened(0.15 if x <= 1 or x >= E.W - 2 else 0.0))
			n.position = world(Vector2(x + 0.5, y + 0.5))  # tiles have their origin at the centre
			_stage.add_child(n)
	for h in e.heroes:
		var n := _scene("axolotl", Vector3(0.3, 0.8, 0.3), SKINS[h["p"]])
		_tint(n, "fizz_skin", SKINS[h["p"]])
		_stage.add_child(n)
		_heroes.append({"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""})
	_place_camera()


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"blow":
			if d["p"] < _heroes.size():
				_play(_heroes[d["p"]]["anim"], "blow")
				_heroes[d["p"]]["last"] = "blow"
		"pop":
			var c := Color(0.8, 0.95, 1.0) if not d["trapped"] else Color(1.0, 0.85, 0.5)
			_fx.burst(world(d["pos"], 0.3), c, 12 if not d["trapped"] else 24, 2.0, 0.4, 0.06, 1.0, 0.0, 1.0, "glow")
		"trap":
			_fx.burst(world(d["pos"], 0.3), Color(0.7, 0.9, 1.0), 10, 1.5, 0.4, 0.05, 1.0, 0.0, 1.0, "glow")
		"treat":
			_fx.burst(world(d["pos"] + Vector2(0, -0.5), 0.3), Color(1.0, 0.9, 0.4), 14, 2.0, 0.5, 0.07, 1.0, 1.0, 1.0, "glow")
		"die":
			_fx.burst(world(d["pos"] + Vector2(0, -0.8), 0.3), SKINS[d["p"]], 24, 2.5, 0.7, 0.08, 1.0, -2.0, 1.0, "glow")
		"escape":
			_fx.burst(world(d["pos"], 0.3), Color(1.0, 0.4, 0.3), 16, 2.0, 0.4, 0.06, 1.0, 0.0, 1.0, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _heroes.is_empty():
		return
	_backdrop_mat.set_shader_parameter("time_s", _time)
	# heroes
	for i in e.heroes.size():
		var h: Dictionary = e.heroes[i]
		var v: Dictionary = _heroes[i]
		var n: Node3D = v["node"]
		n.visible = h["alive"] and not (h["inv"] > 0.0 and fmod(_time, 0.16) < 0.05)
		n.position = world(h["pos"])
		n.scale = Vector3(h["facing"], 1, 1)
		var want := "idle"
		if e.phase == E.Phase.CLEARED: want = "cheer"
		elif not h["ground"]: want = "jump" if h["vel"].y < 0.0 else "fall"
		elif absf(h["want_x"]) > 0.2: want = "walk"
		var ap: AnimationPlayer = v["anim"]
		if v["last"] == "blow" and ap and ap.is_playing():
			continue
		if v["last"] != want:
			v["last"] = want
			_play(ap, want, want in ["idle", "walk", "fall", "cheer"])
	# bubbles
	var live := {}
	for b in e.bubbles:
		live[b["id"]] = true
		var trapped: bool = not b["trapped"].is_empty()
		if not _bubbles.has(b["id"]) or _bubbles[b["id"]]["has"] != trapped:
			if _bubbles.has(b["id"]):
				(_bubbles[b["id"]]["node"] as Node3D).queue_free()
			var n := _scene("bubble_trap" if trapped else "bubble", Vector3(0.42, 0.42, 0.42), Color(0.8, 0.9, 1.0, 0.4))
			if trapped:
				var toy := _scene(TOY_MODELS.get(b["trapped"]["kind"], "toy_beetle"))
				# the trapped pose is centred on the toy's origin: it sits at the bubble's centre
				n.add_child(toy)
				_play(toy.find_child("AnimationPlayer", true, false), "trapped", true)
			_stage.add_child(n)
			_bubbles[b["id"]] = {"node": n, "has": trapped}
		var node: Node3D = _bubbles[b["id"]]["node"]
		node.position = world(b["pos"], 0.1)
		var wob := 1.0 + sin(_time * 7.0 + b["id"]) * 0.04
		var grow := clampf(b["age"] / 0.12, 0.3, 1.0)
		node.scale = Vector3(wob, 2.0 - wob, 1.0) * grow
		if trapped and b["life"] < 2.0:
			node.scale *= 1.0 + sin(_time * 30.0) * 0.05  # about to break out
	for id in _bubbles.keys():
		if not live.has(id):
			_bubbles[id]["node"].queue_free()
			_bubbles.erase(id)
	# toys
	var alive := {}
	for t in e.toys:
		alive[t["id"]] = true
		if not _toys.has(t["id"]):
			var n := _scene(TOY_MODELS.get(t["kind"], "toy_beetle"), Vector3(0.35, 0.7, 0.35), Color(0.9, 0.7, 0.3))
			_stage.add_child(n)
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			_play(ap, "fly" if t["kind"] == "flyer" else "walk", true)
			_toys[t["id"]] = {"node": n, "angry": false}
		var v: Dictionary = _toys[t["id"]]
		var n: Node3D = v["node"]
		n.position = world(t["pos"])
		n.scale = Vector3(t["facing"], 1, 1)
		if t["angry"] != v["angry"]:
			v["angry"] = t["angry"]
			_tint(n, "toy_paint", Color(1.0, 0.25, 0.2) if t["angry"] else Color(1, 1, 1))
	for id in _toys.keys():
		if not alive.has(id):
			_toys[id]["node"].queue_free()
			_toys.erase(id)
	# treats
	while _treats.size() > e.treats.size():
		_treats.pop_back().queue_free()
	for i in e.treats.size():
		var tr: Dictionary = e.treats[i]
		if i >= _treats.size():
			var n := _scene("treat_" + tr["kind"], Vector3(0.22, 0.4, 0.22), Color(1.0, 0.4, 0.4))
			_stage.add_child(n)
			_treats.append(n)
		elif _treats[i].get_meta("kind", "") != tr["kind"]:
			_treats[i].queue_free()
			_treats[i] = _scene("treat_" + tr["kind"], Vector3(0.22, 0.4, 0.22), Color(1.0, 0.4, 0.4))
			_stage.add_child(_treats[i])
		_treats[i].set_meta("kind", tr["kind"])
		_treats[i].position = world(tr["pos"], 0.05) + Vector3(0, 0.06 + sin(_time * 3.0 + i) * 0.05, 0)
		_treats[i].rotation.y = _time * 1.5 + i
	# the ghost
	if not e.ghost.is_empty():
		if _ghost == null:
			_ghost = _scene("bubble", Vector3(0.6, 0.6, 0.6), Color(0.4, 0.2, 0.5))
			_tint(_ghost, "bubble", Color(0.55, 0.2, 0.7), true)
			_ghost.scale = Vector3.ONE * 1.4
			_stage.add_child(_ghost)
		_ghost.position = world(e.ghost["pos"], 0.4)
	elif _ghost:
		_ghost.queue_free()
		_ghost = null
	_place_camera()


func _place_camera() -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(E.H * T * 0.5 + 0.7, (E.W * T * 0.5 + 0.5) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	camera.position = Vector3(0, 0.2, dist)
	camera.look_at(Vector3(0, 0, 0), Vector3.UP)
