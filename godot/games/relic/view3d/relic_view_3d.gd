class_name RelicView3D
extends Node3D
## Relic Run in 3D: a jungle temple seen from the side, one screen at a time (the camera slides to the next screen as
## the explorer crosses into it). Carved stone blocks stand in front of a dark inner wall lit by torches; spikes spring
## from the floor, darts whistle out of carved holes, the boulder rolls, dynamite blows cracked stone apart.
## Tile (x, y) is world (x + 0.5, -(y + 0.5)): one unit a tile, y up.

const E = preload("res://games/relic/engine/relic_engine.gd")
const M := "res://games/relic/art/models/"
const ANIM := {"ground": "idle", "crawl": "crawl", "climb": "climb", "air": "jump"}

@export var game: RelicGame

var camera: Camera3D
var _env: Environment
var _stage: Node3D
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _hero_last := ""
var _cam_pos := Vector3.ZERO
var _tiles := {}          ## cell -> node (only the breakable ones, to remove)
var _spikes: Array[Node3D] = []
var _crushers: Array[Node3D] = []
var _darts := {}
var _shots: Array[Node3D] = []
var _bombs: Array[Node3D] = []
var _enemies := {}
var _pickups: Array[Node3D] = []
var _boulder: Node3D
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _one_shot := 0.0      ## seconds a one-shot hero animation still has


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3(p.x, -p.y, z)


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.03, 0.03, 0.02)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.7, 0.6, 0.45)
	_env.ambient_light_energy = 0.3
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.7
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, -30, 0)
	key.light_energy = 0.9
	key.light_color = Color(1.0, 0.9, 0.75)
	key.shadow_enabled = true
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 34
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 23.3   # this game's sizes: its median burst about 0.4 m across, a little more at birth
	add_child(_fx)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String, size := Vector3(0.9, 0.9, 0.9), col := Color(0.6, 0.5, 0.4)) -> Node3D:
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
	n.add_child(mi)
	return n


func _mesh_of(name: String) -> Mesh:
	var n := _scene(name)
	var mesh: Mesh = null
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		mesh = (mi as MeshInstance3D).mesh
		break
	n.free()
	return mesh


## Many copies of one model's mesh in one draw.
func _multi(name: String, xforms: Array[Transform3D], shade := 0.0) -> void:
	if xforms.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _mesh_of(name)
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	if shade > 0.0:
		# a dark veil over it (the inner wall sits in the gloom behind the lit blocks)
		var veil := StandardMaterial3D.new()
		veil.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		veil.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		veil.albedo_color = Color(0.02, 0.015, 0.01, shade)
		mmi.material_overlay = veil
	_stage.add_child(mmi)


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.1)


func _on_level(e: RelicEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_tiles.clear()
	_spikes.clear()
	_crushers.clear()
	_darts.clear()
	_shots.clear()
	_bombs.clear()
	_enemies.clear()
	_pickups.clear()
	var lv := e.level
	var stone := {"a": [] as Array[Transform3D], "b": [] as Array[Transform3D], "c": [] as Array[Transform3D]}
	var moss: Array[Transform3D] = []
	var back: Array[Transform3D] = []
	var planks: Array[Transform3D] = []
	var ladders: Array[Transform3D] = []
	for y in lv.h:
		for x in lv.w:
			var ch := lv.at(x, y)
			var c := Vector3(x + 0.5, -(y + 0.5), 0)
			back.append(Transform3D(Basis(), c + Vector3(0, 0, -1.0)))
			match ch:
				"#":
					if y > 0 and lv.at(x, y - 1) != "#" and lv.at(x, y - 1) != "B":
						moss.append(Transform3D(Basis(), c))
					else:
						stone[["a", "b", "c"][(x * 7 + y * 13) % 3]].append(Transform3D(Basis(), c))
				"B":
					var n := _scene("breakable", Vector3(1, 1, 1), Color(0.55, 0.45, 0.35))
					n.position = c
					_stage.add_child(n)
					_tiles[Vector2i(x, y)] = n
				"=":
					planks.append(Transform3D(Basis(), c))
				"H":
					ladders.append(Transform3D(Basis(), c + Vector3(0, -0.5, 0.1)))
				"~":
					var w := MeshInstance3D.new()
					var bm := BoxMesh.new()
					bm.size = Vector3(1, 1, 1)
					var wm := StandardMaterial3D.new()
					wm.albedo_color = Color(0.15, 0.35, 0.3, 0.8)
					wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					wm.emission_enabled = true
					wm.emission = Color(0.1, 0.4, 0.3)
					bm.material = wm
					w.mesh = bm
					w.position = c
					_stage.add_child(w)
	for k in stone:
		_multi("tile_stone_" + k, stone[k])
	_multi("tile_moss", moss)
	_multi("tile_brick", back, 0.55)
	_multi("tile_platform", planks)
	_multi("ladder", ladders)
	# torches on the back wall, now and then in open space
	for y in range(1, lv.h - 1):
		for x in range(1, lv.w - 1):
			if lv.at(x, y) == "." and y % 12 == 6 and x % 20 in [4, 15] and lv.at(x, y + 1) != "#":
				var t := _scene("torch", Vector3(0.2, 0.5, 0.2), Color(1.0, 0.6, 0.2))
				t.position = Vector3(x + 0.5, -(y + 0.5), -0.45)
				_stage.add_child(t)
				var l := OmniLight3D.new()
				l.light_color = Color(1.0, 0.65, 0.3)
				l.light_energy = 1.6
				l.omni_range = 5.0
				l.position = Vector3(0, 0.3, 0.4)
				t.add_child(l)
	# the exit
	var door := _scene("exit_door", Vector3(2, 3, 0.4), Color(0.7, 0.6, 0.4))
	door.position = Vector3(lv.exit.x + 0.5, -(lv.exit.y + 1.0), -0.4)
	_stage.add_child(door)
	var dl := OmniLight3D.new()
	dl.light_color = Color(1.0, 0.85, 0.5)
	dl.light_energy = 2.0
	dl.omni_range = 4.0
	dl.position = Vector3(0, 1.5, 1.0)
	door.add_child(dl)
	for s in e.spikes:
		var n := _scene("spikes", Vector3(0.9, 0.8, 0.3), Color(0.7, 0.7, 0.75))
		_stage.add_child(n)
		_spikes.append(n)
	for sh in e.shooters:
		var n := _scene("dart_hole", Vector3(1, 1, 0.2), Color(0.5, 0.45, 0.4))
		n.position = world(Vector2(sh["cell"]) + Vector2(0.5, 0.5), 0.02)
		n.scale.x = sh["dir"]
		_stage.add_child(n)
	for cr in e.crushers:
		var n := _scene("crusher", Vector3(1, 1.5, 1), Color(0.45, 0.4, 0.35))
		_stage.add_child(n)
		_crushers.append(n)
	for pk in e.pickups:
		var n := _scene({"$": ["treasure_idol", "treasure_gem", "treasure_coin"][pk["cell"].x % 3], "a": "ammo_box", "x": "dynamite_box"}[pk["kind"]],
			Vector3(0.4, 0.4, 0.4), Color(1.0, 0.8, 0.3))
		n.position = world(Vector2(pk["cell"]) + Vector2(0.5, 1.0))
		_stage.add_child(n)
		_pickups.append(n)
	if not e.boulder.is_empty():
		_boulder = _scene("boulder", Vector3(1.8, 1.8, 1.8), Color(0.55, 0.5, 0.45))
		_stage.add_child(_boulder)
	else:
		_boulder = null
	_hero = _scene("explorer", Vector3(0.6, 1.4, 0.5), Color(0.8, 0.7, 0.5))
	_hero.scale = Vector3.ONE * 0.88
	_stage.add_child(_hero)
	_hero_anim = _hero.find_child("AnimationPlayer", true, false)
	_hero_last = ""
	_cam_pos = _screen_centre(e)
	_place_camera(1.0)


func _screen_centre(e: RelicEngine) -> Vector3:
	var s := e.screen
	return Vector3(s.x * RelicLevel.SW + RelicLevel.SW * 0.5, -(s.y * RelicLevel.SH + RelicLevel.SH * 0.5), 0)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"shot":
			_one_shot = 0.3
			_play(_hero_anim, "shoot")
			var p: Vector2 = e.hero["pos"] + Vector2(e.hero["facing"] * 0.6, -0.95)
			_fx.burst(world(p, 0.3), Color(1.0, 0.8, 0.4), 6, 2.0, 0.15, 0.06, 1.0, 0.0, 1.0, "glow")
			_fx.flash(world(p, 0.3) + Vector3(0, -2.5, 0.5), Color(1.0, 0.8, 0.4), 1.5)
		"plant":
			_one_shot = 0.5
			_play(_hero_anim, "plant")
		"boom":
			var p := world(d["pos"], 0.4)
			_fx.burst(p, Color(1.0, 0.6, 0.2), 40, 5.0, 0.7, 0.2, 1.0, -4.0, 1.0, "glow")
			_fx.burst(p, Color(0.35, 0.3, 0.25), 30, 3.0, 1.2, 0.3, 0.0, -2.0, 1.0, "smoke")
			_fx.flash(p + Vector3(0, -2.5, 1.0), Color(1.0, 0.6, 0.3), 4.0)
			_shake = 0.5
		"break":
			var c: Vector2i = d["cell"]
			if _tiles.has(c):
				_tiles[c].queue_free()
				_tiles.erase(c)
			_fx.burst(world(Vector2(c) + Vector2(0.5, 0.5), 0.3), Color(0.6, 0.5, 0.4), 16, 3.0, 0.8, 0.12, 0.0, -12.0, 1.0)
		"hit":
			_fx.burst(world(d["pos"], 0.3), Color(0.9, 0.8, 0.6), 10 if not d["dead"] else 22, 2.5, 0.4, 0.08, 1.0, -6.0, 1.0, "glow")
		"dart_hit":
			_fx.burst(world(d["pos"], 0.3), Color(0.8, 0.7, 0.6), 6, 1.5, 0.3, 0.05, 0.0, -6.0, 1.0)
		"crush":
			_shake = 0.35
			if not e.boulder.is_empty() and e.boulder["done"] and _boulder:
				_fx.burst(world(e.boulder["pos"], 0.3), Color(0.55, 0.5, 0.45), 30, 4.0, 1.0, 0.18, 0.0, -12.0, 1.0)
		"die":
			_play(_hero_anim, "die")
			_one_shot = 2.0
			_fx.burst(world(d["pos"] + Vector2(0, -0.7), 0.3), Color(1.0, 0.9, 0.6), 18, 2.5, 0.6, 0.08, 1.0, -3.0, 1.0, "glow")
			_shake = 0.3
		"exit":
			_play(_hero_anim, "cheer", true)
			_one_shot = 9.0
		"pickup":
			_fx.burst(world(d["pos"], 0.3), Color(1.0, 0.85, 0.4), 16, 2.0, 0.5, 0.07, 1.0, 1.0, 1.0, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	# the explorer
	var h := e.hero
	_hero.position = world(h["pos"], 0.23 if h["state"] == "climb" else 0.0)  # on a ladder, just in front of it
	_hero.scale = Vector3(0.88 * h["facing"], 0.88, 0.88)
	_hero.visible = not (e.phase == E.Phase.DYING and e.phase_t < 0.8)
	_one_shot = maxf(0.0, _one_shot - delta)
	if _one_shot <= 0.0:
		var st: String = h["state"]
		var want: String = ANIM.get(st, "idle")
		if st == "ground" and absf(h["vel"].x) > 0.1: want = "walk"
		if st == "air" and h["vel"].y > 0.0: want = "fall"
		if st == "climb" and not (e.up or e.down): want = "climb"
		if want != _hero_last:
			_hero_last = want
			_play(_hero_anim, want, want != "jump")
		# play the cycles at the speed the engine moves (the model's stride per cycle, measured)
		if st == "crawl" and _hero_anim:
			_hero_anim.speed_scale = 2.35 if absf(h["vel"].x) > 0.1 else 0.0
		elif st == "climb" and _hero_anim:
			_hero_anim.speed_scale = 2.6 if (e.up or e.down) else 0.0
		elif _hero_anim:
			_hero_anim.speed_scale = 1.04 if want == "walk" else 1.0
	else:
		_hero_last = ""
		if _hero_anim:
			_hero_anim.speed_scale = 1.0
	# traps
	for i in e.spikes.size():
		var s: Dictionary = e.spikes[i]
		_spikes[i].position = world(Vector2(s["cell"]) + Vector2(0.5, 1.0), 0.0) + Vector3(0, -0.8 * (1.0 - s["up"]), 0)
		_spikes[i].visible = s["up"] > 0.02
	for i in e.crushers.size():
		var cr: Dictionary = e.crushers[i]
		_crushers[i].position = world(Vector2(cr["cell"]) + Vector2(0.5, cr["drop"]), 0.0)
	var live := {}
	for d in e.darts:
		live[d["id"]] = true
		if not _darts.has(d["id"]):
			var n := _scene("dart", Vector3(0.4, 0.05, 0.05), Color(0.7, 0.6, 0.4))
			n.scale.x = d["dir"]
			_stage.add_child(n)
			_darts[d["id"]] = n
		_darts[d["id"]].position = world(d["pos"], 0.1)
	for id in _darts.keys():
		if not live.has(id):
			_darts[id].queue_free()
			_darts.erase(id)
	while _shots.size() < e.shots.size():
		var n := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = Color(1.0, 0.9, 0.5)
		m.emission_enabled = true
		m.emission = Color(1.0, 0.8, 0.4)
		m.emission_energy_multiplier = 3.0
		sm.material = m
		n.mesh = sm
		_stage.add_child(n)
		_shots.append(n)
	for i in _shots.size():
		_shots[i].visible = i < e.shots.size()
		if _shots[i].visible:
			_shots[i].position = world(e.shots[i]["pos"], 0.2)
	while _bombs.size() < e.bombs.size():
		var n := _scene("dynamite", Vector3(0.25, 0.4, 0.25), Color(0.8, 0.2, 0.15))
		_stage.add_child(n)
		_bombs.append(n)
	for i in _bombs.size():
		_bombs[i].visible = i < e.bombs.size()
		if _bombs[i].visible:
			_bombs[i].position = world(e.bombs[i]["pos"], 0.2)
			_bombs[i].scale = Vector3.ONE * (1.0 + 0.15 * sin(_time * (8.0 + (2.0 - e.bombs[i]["fuse"]) * 10.0)))
	for i in e.pickups.size():
		_pickups[i].visible = not e.pickups[i]["taken"]
		_pickups[i].rotation.y = _time * 1.5
	# enemies
	for en in e.enemies:
		var id: int = en["id"]
		if not _enemies.has(id):
			var n := _scene(en["kind"], Vector3(0.6, 1.4, 0.5), Color(0.6, 0.55, 0.45))
			_stage.add_child(n)
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			_play(ap, "fly" if en["kind"] == "bat" else "walk", true)
			if ap:
				ap.speed_scale = {"automaton": 1.33, "skeleton": 1.2}.get(en["kind"], 1.0)
			_enemies[id] = n
		var n: Node3D = _enemies[id]
		if not en["alive"]:
			if n.visible and not n.has_meta("gone"):
				n.set_meta("gone", true)
				var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
				if ap and ap.has_animation("die"):
					ap.speed_scale = 1.0
					_play(ap, "die")
				var tw := create_tween()
				tw.tween_interval(1.6)
				tw.tween_property(n, "scale", Vector3(n.scale.x, 0.02, n.scale.z), 0.3)
				tw.tween_callback(func(): n.visible = false)
			continue
		var bat: bool = en["kind"] == "bat"
		n.position = world(en["pos"] + (Vector2(0, -0.35) if bat else Vector2.ZERO))  # a bat's origin is its body
		n.scale = Vector3(en["facing"] * 0.94, 0.94, 0.94)
	# the boulder rolls
	if _boulder and not e.boulder.is_empty():
		var bp: Vector2 = e.boulder["pos"]
		var old := _boulder.position.x
		_boulder.position = world(bp, 0.0)
		_boulder.rotation.z -= (_boulder.position.x - old) / 0.9
		_boulder.visible = not e.boulder["done"]
		if e.boulder["rolling"] and not e.boulder["done"]:
			_shake = maxf(_shake, 0.12)
	_shake = maxf(0.0, _shake - delta * 1.5)
	_place_camera(delta)


func _place_camera(delta: float) -> void:
	var e := game.engine
	var target := _screen_centre(e)
	_cam_pos = _cam_pos.lerp(target, minf(1.0, delta * 9.0))
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(RelicLevel.SH * 0.5 + 0.9, (RelicLevel.SW * 0.5 + 0.3) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var j := Vector3(sin(_time * 50.0), cos(_time * 43.0), 0) * _shake * _shake * (0.4 if Settings.camera_shake else 0.0)
	camera.position = _cam_pos + Vector3(0, 0.6, dist) + j
	camera.look_at(_cam_pos + Vector3(0, 0.1, 0) + j, Vector3.UP)
