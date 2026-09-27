class_name HenView3D
extends Node3D
## Henhouse Heist in 3D: a farmyard at golden hour seen from the side. Brick platforms with grass on top, wooden
## ladders, the lifts on their ropes, eggs in straw nests, grain sacks, a barn, a silo and a windmill behind; the
## farmhand, the hens and, on goose stages, the goose bursting out of its cage.
## Tile (x, y) is world ((x - 16) / 2, (13 - y) / 2), y up.

const E = preload("res://games/henhouse/engine/hen_engine.gd")
const M := "res://games/henhouse/art/models/"
const T := 0.5
const HERO_SCALE := 0.647
## hen colours: feather, speckle (the same as the feather hides the speckles)
const FEATHERS := [[Color(1.0, 0.98, 0.94), Color(1.0, 0.98, 0.94)], [Color(0.62, 0.32, 0.12), Color(0.62, 0.32, 0.12)],
	[Color(0.62, 0.62, 0.6), Color(0.08, 0.08, 0.08)], [Color(0.95, 0.8, 0.55), Color(0.95, 0.8, 0.55)]]

@export var game: HenGame

var camera: Camera3D
var _stage: Node3D
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _hero_last := ""
var _hens: Array[Dictionary] = []
var _eggs := {}
var _grain := {}
var _lifts: Array[Node3D] = []
var _goose: Node3D
var _goose_anim: AnimationPlayer
var _cage: Node3D
var _fx: Bursts
var _time := 0.0
var _mats := {}


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3((p.x - 16.0) * T, (13.0 - p.y) * T, z)


func _ready() -> void:
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.35, 0.55, 0.85)
	sm.sky_horizon_color = Color(1.0, 0.78, 0.55)
	sm.ground_horizon_color = Color(0.6, 0.5, 0.4)
	sky.sky_material = sm
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.5
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.5
	env.glow_hdr_threshold = 1.1
	env.fog_enabled = true  # golden haze: the farm behind stays back
	env.fog_light_color = Color(1.0, 0.82, 0.6)
	env.fog_mode = Environment.FOG_MODE_DEPTH  # it starts behind the playfield
	env.fog_depth_begin = 28.0
	env.fog_depth_end = 70.0
	env.fog_density = 0.65
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-28, -40, 0)
	sun.light_energy = 1.2
	sun.light_color = Color(1.0, 0.85, 0.65)
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


func _scene(name: String, size := Vector3(0.4, 0.4, 0.4), col := Color(0.8, 0.6, 0.4)) -> Node3D:
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


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.1)


func _build_backdrop() -> void:
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(90, 40)
	ground.mesh = pm
	ground.material_override = Pbr.material("grass", Color(0.8, 0.9, 0.6), 0.4)
	ground.position = Vector3(0, -6.6, -12)
	add_child(ground)
	var rng := RandomNumberGenerator.new()
	rng.seed = 20
	for spec in [["bg_hill", Vector3(-6, -6.6, -12), 1.6], ["bg_hill", Vector3(8, -6.6, -14), 1.8], ["bg_barn", Vector3(-11, -6.6, -7), 1.0],
			["bg_silo", Vector3(-8.2, -6.6, -8), 1.0], ["bg_windmill", Vector3(11, -6.6, -9), 1.1], ["bg_tree", Vector3(6.5, -6.6, -5), 1.2],
			["bg_tree", Vector3(-3, -6.6, -9), 1.4], ["bg_haybale", Vector3(9.5, -6.6, -3), 1.0], ["bg_haybale", Vector3(-9.8, -6.6, -2.6), 1.0],
			["bg_fence", Vector3(-6, -6.6, -2.2), 1.0], ["bg_fence", Vector3(-4, -6.6, -2.2), 1.0], ["bg_fence", Vector3(5, -6.6, -2.2), 1.0]]:
		var n := _scene(spec[0], Vector3(2, 3, 2), Color(0.7, 0.3, 0.2))
		var sp: Vector3 = spec[1]
		n.position = Vector3(sp.x * 1.6, sp.y, sp.z * 1.8 - 4.0)
		n.scale = Vector3.ONE * spec[2]
		add_child(n)
		_play(n.find_child("AnimationPlayer", true, false), "turn", true)


func _on_level(e: HenEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_hens.clear()
	_eggs.clear()
	_grain.clear()
	_lifts.clear()
	_goose = null
	_cage = null
	var lv := e.level
	for y in E.H:
		for x in E.W:
			var c := Vector2(x + 0.5, y + 0.5)
			if lv.solid[y * E.W + x] == 1:
				var top := y == 0 or lv.solid[(y - 1) * E.W + x] == 0
				var n := _scene("brick", Vector3(0.5, 0.5, 0.5), Color(0.75, 0.35, 0.25))
				_tint(n, "brick_face", Color(0.7, 0.3, 0.2))
				var grass := n.find_child("brick_top", true, false)
				if grass and not top:
					(grass as Node3D).visible = false  # grass only where the sky is above
				n.position = world(c)
				_stage.add_child(n)
			elif lv.ladder[y * E.W + x] == 1:
				var n := _scene("ladder", Vector3(0.45, 0.5, 0.05), Color(0.6, 0.4, 0.2))
				n.position = world(Vector2(x + 0.5, y + 1.0), 0.3)
				_stage.add_child(n)
	for c in e.eggs:
		var n := _scene("egg", Vector3(0.2, 0.25, 0.2), Color(0.9, 0.75, 0.55))
		n.position = world(Vector2(c) + Vector2(0.5, 1.0), 0.5)
		_stage.add_child(n)
		_eggs[c] = n
	for c in e.grain:
		var n := _scene("grain", Vector3(0.25, 0.25, 0.25), Color(0.9, 0.8, 0.4))
		n.position = world(Vector2(c) + Vector2(0.5, 1.0), 0.5)
		_stage.add_child(n)
		_grain[c] = n
	for i in e.lifts.size():
		var n := _scene("lift", Vector3(1.0, 0.1, 0.5), Color(0.6, 0.45, 0.3))
		_stage.add_child(n)
		_lifts.append(n)
	if lv.cage.x >= 0:
		_cage = _scene("cage", Vector3(1.0, 1.2, 0.6), Color(0.6, 0.5, 0.35))
		_cage.position = world(Vector2(lv.cage.x + 1.0, lv.cage.y + 2.0), -0.1)
		_stage.add_child(_cage)
		if lv.goose:
			_goose = _scene("goose", Vector3(0.6, 0.9, 0.5), Color(0.95, 0.95, 0.95))
			_goose.scale = Vector3.ONE * 0.55
			_stage.add_child(_goose)
			_goose_anim = _goose.find_child("AnimationPlayer", true, false)
			_play(_goose_anim, "idle", true)
			_goose.position = _cage.position + Vector3(-0.15, 0.12, 0.0) * 1.0
	for hn in e.hens:
		var n := _scene("hen", Vector3(0.4, 0.4, 0.3), Color(0.95, 0.95, 0.9))
		var fc: Array = FEATHERS[(hn["id"] + e.stage) % FEATHERS.size()]
		_tint(n, "hen_feather", fc[0])
		_tint(n, "hen_speckle", fc[1])
		n.scale = Vector3.ONE * 0.6
		_stage.add_child(n)
		_hens.append({"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""})
	_hero = _scene("farmhand", Vector3(0.4, 1.0, 0.3), Color(0.3, 0.5, 0.8))
	_hero.scale = Vector3.ONE * HERO_SCALE
	_stage.add_child(_hero)
	_hero_anim = _hero.find_child("AnimationPlayer", true, false)
	_hero_last = ""
	_place_camera()


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"egg":
			var c: Vector2i = d["cell"]
			if _eggs.has(c):
				_fx.burst(_eggs[c].position + Vector3(0, 0.15, 0.2), Color(1.0, 0.9, 0.6), 14, 1.8, 0.5, 0.06, 1.0, -2.0, 1.0, "glow")
				_eggs[c].queue_free()
				_eggs.erase(c)
		"grain":
			var c: Vector2i = d["cell"]
			if _grain.has(c):
				_fx.burst(_grain[c].position + Vector3(0, 0.15, 0.2), Color(0.95, 0.85, 0.45), 18, 1.5, 0.6, 0.05, 0.0, -6.0, 1.0)
				_grain[c].queue_free()
				_grain.erase(c)
		"peck":
			pass
		"goose_free":
			if _cage:
				_play(_cage.find_child("AnimationPlayer", true, false), "open")
			_play(_goose_anim, "fly", true)
		"die":
			_play(_hero_anim, "die")
			_hero_last = "die"
			_fx.burst(world(d["pos"] + Vector2(0, -1.0), 0.3), Color(1.0, 0.9, 0.7), 18, 2.0, 0.6, 0.07, 1.0, -3.0, 1.0, "glow")
		"cleared":
			_play(_hero_anim, "cheer", true)
			_hero_last = "cheer"


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	# some grain is eaten by hens: drop it from the view too
	for c in _grain.keys():
		if not e.grain.has(c):
			_grain[c].queue_free()
			_grain.erase(c)
	var h := e.hero
	_hero.position = world(h["pos"], 0.5)
	_hero.scale = Vector3(HERO_SCALE * h["facing"], HERO_SCALE, HERO_SCALE)
	if e.phase == E.Phase.PLAY:
		var st: String = h["state"]
		var want := "idle"
		match st:
			"walk": want = "walk" if absf(e.move_x) > 0.1 else "idle"
			"climb": want = "climb"
			"jump": want = "jump"
			"fall": want = "fall"
		if want != _hero_last:
			_hero_last = want
			_play(_hero_anim, want, want != "jump")
		if _hero_anim:
			# the cycles at the engine's speeds (the model's stride: walk 1.75 units/s, climb 0.94 units/s)
			if st == "climb":
				_hero_anim.speed_scale = (E.CLIMB * T / 0.94) if (e.up or e.down) else 0.0
			else:
				_hero_anim.speed_scale = E.WALK * T / 1.75 if want == "walk" else 1.0
	elif e.phase == E.Phase.READY and _hero_last in ["die", "cheer"]:
		_hero_last = ""
		if _hero_anim:
			_hero_anim.speed_scale = 1.0
	for i in e.hens.size():
		var hn: Dictionary = e.hens[i]
		var v: Dictionary = _hens[i]
		var n: Node3D = v["node"]
		n.position = world(hn["pos"], 0.5)
		if hn["dir"].x != 0:
			n.scale = Vector3(0.6 * hn["dir"].x, 0.6, 0.6)
		var want := "peck" if hn["peck"] > 0.0 else ("climb" if hn["climb"] else "walk")
		if v["last"] != want:
			v["last"] = want
			_play(v["anim"], want, true)
			if v["anim"]:
				(v["anim"] as AnimationPlayer).speed_scale = hn["speed"] * T / 0.73 if want == "walk" else 1.0
	for i in _lifts.size():
		_lifts[i].position = world(Vector2(e.level.lift_col + 1.0, e.lifts[i]), 0.2)
		var rope := _lifts[i].find_child("rope", true, false) as Node3D
		if rope:
			# the rope reaches up to the top of the shaft
			var top_y := (13.0 - E.LIFT_TOP) * T
			rope.scale.y = maxf(0.01, top_y - (_lifts[i].position.y + 1.72))
	for c in _eggs:
		_eggs[c].rotation.y = sin(_time * 2.0 + c.x) * 0.3
	if _goose and not e.goose.is_empty():
		var gp: Vector2 = e.goose["pos"]
		_goose.position = world(gp + Vector2(0, 0.8), 0.6)
		var gv: Vector2 = e.goose["vel"]
		if absf(gv.x) > 0.05:
			_goose.scale = Vector3(0.55 * signf(gv.x), 0.55, 0.55)
	_place_camera()


func _place_camera() -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(E.H * T * 0.5 + 0.8, (E.W * T * 0.5 + 0.4) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	camera.position = Vector3(0, 0.3, dist)
	camera.look_at(Vector3(0, 0.1, 0), Vector3.UP)
