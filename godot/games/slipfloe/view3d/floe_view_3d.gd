class_name FloeView3D
extends Node3D
## Slipfloe in 3D: an ice arena on a snowfield under an aurora, seen from above at an angle. Ice blocks glint, the gem
## blocks glow, pushed blocks glide with a spray of frost, shattered ones burst into shards, the walls wobble when
## shaken, mites hatch, scurry, chew and get flattened, and the otter waddles, shoves and dances.
## Cell (x, y) is world (x - 6, 0, y - 7).

const E = preload("res://games/slipfloe/engine/floe_engine.gd")
const M := "res://games/slipfloe/art/models/"
const MITE_TINTS := [Color(0.55, 0.85, 1.0), Color(1.0, 0.6, 0.85), Color(0.7, 1.0, 0.6), Color(1.0, 0.8, 0.45), Color(0.8, 0.65, 1.0)]

@export var game: FloeGame

var camera: Camera3D
var _stage: Node3D
var _blocks := {}      ## cell -> {node, kind}
var _slides := {}      ## id -> node
var _mites := {}       ## id -> {node, anim, last}
var _otter: Node3D
var _otter_anim: AnimationPlayer
var _walls := {}       ## side (Vector2i) -> Array of nodes
var _shake_t := {}     ## side -> seconds
var _fx: Bursts
var _time := 0.0
var _cam_shake := 0.0
var _mats := {}


static func cell(c: Vector2, y := 0.0) -> Vector3:
	return Vector3(c.x - 6.0, y, c.y - 7.0)


func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.04, 0.09)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.7, 0.95)
	env.ambient_light_energy = 0.3
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	env.ssao_enabled = true
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-55, -30, 0)
	moon.light_energy = 0.65
	moon.light_color = Color(0.85, 0.92, 1.0)
	moon.shadow_enabled = true
	moon.shadow_blur = 1.3
	add_child(moon)
	var aurora := OmniLight3D.new()  # green-violet light from the sky
	aurora.position = Vector3(0, 9, -12)
	aurora.light_color = Color(0.4, 1.0, 0.7)
	aurora.light_energy = 0.7
	aurora.omni_range = 26.0
	add_child(aurora)
	camera = Camera3D.new()
	camera.fov = 40
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	_build_world()
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String, size := Vector3(0.9, 0.9, 0.9), col := Color(0.8, 0.9, 1.0)) -> Node3D:
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
				t.albedo_color = Color(col, t.albedo_color.a)
				if t.emission_enabled:
					t.emission = col
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.08)


## The snowfield, the aurora, the floor and walls of the arena, and the camp around it: all fixed.
func _build_world() -> void:
	var snow := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(70, 50)
	snow.mesh = pm
	var sm := StandardMaterial3D.new()
	sm.albedo_color = Color(0.36, 0.42, 0.56)
	sm.roughness = 0.9
	snow.material_override = sm
	snow.position.y = -0.02
	add_child(snow)
	var sky := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(90, 30)
	sky.mesh = qm
	var am := ShaderMaterial.new()
	am.shader = load("res://games/slipfloe/view3d/aurora.gdshader")
	sky.material_override = am
	sky.position = Vector3(0, 10, -24)
	add_child(sky)
	for y in E.H:
		for x in E.W:
			var v: String = ["a", "b", "c"][(x * 7 + y * 3) % 3]
			var t := _scene("floor_tile_" + v, Vector3(1, 0.04, 1), Color(0.75, 0.85, 0.95))
			if not ResourceLoader.exists(M + "floor_tile_" + v + ".glb") and ResourceLoader.exists(M + "floor_tile.glb"):
				t = _scene("floor_tile")
			t.position = cell(Vector2(x, y))
			# a deeper blue floor than the ice, so the blocks stand out
			_tint(t, "floor_snow", Color(0.42, 0.52, 0.72))
			add_child(t)
	# walls: the inner face of a segment is at local z = +0.25; it stands half a cell outside the arena
	for side in [Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0)]:
		var list: Array = []
		var count := E.W if side.x == 0 else E.H
		for i in count:
			var w := _scene("wall_segment", Vector3(1, 0.6, 0.5), Color(0.85, 0.92, 1.0))
			var c := Vector2.ZERO
			match side:
				Vector2i(0, -1): c = Vector2(i, -0.75)
				Vector2i(0, 1): c = Vector2(i, E.H - 1 + 0.75)
				Vector2i(-1, 0): c = Vector2(-0.75, i)
				Vector2i(1, 0): c = Vector2(E.W - 1 + 0.75, i)
			w.position = cell(c)
			w.rotation.y = {Vector2i(0, -1): 0.0, Vector2i(0, 1): PI, Vector2i(-1, 0): PI * 0.5, Vector2i(1, 0): -PI * 0.5}[side]
			add_child(w)
			w.set_meta("base", w.position)
			list.append(w)
		_walls[side] = list
		_shake_t[side] = 0.0
	for c in [Vector2(-0.75, -0.75), Vector2(E.W - 0.25, -0.75), Vector2(-0.75, E.H - 0.25), Vector2(E.W - 0.25, E.H - 0.25)]:
		var k := _scene("wall_corner", Vector3(0.5, 0.7, 0.5), Color(0.85, 0.92, 1.0))
		k.position = cell(c)
		add_child(k)
	# the camp around the arena
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var decor := ["igloo", "pine_snowy", "pine_snowy", "snowman", "ice_rock", "lantern_ice", "pine_snowy"]
	for i in 34:
		var ang := rng.randf() * TAU
		var p := Vector2(cos(ang) * rng.randf_range(9.5, 16.0), sin(ang) * rng.randf_range(10.5, 14.0))
		if absf(p.x) < 8.5 and absf(p.y) < 9.5:
			continue
		if p.y > 8.5 and absf(p.x) < 12.0:
			continue  # keep the near side clear for the camera
		var kind: String = decor[rng.randi_range(0, decor.size() - 1)]
		var n := _scene(kind, Vector3(0.8, 1.2, 0.8), Color(0.9, 0.95, 1.0))
		n.position = Vector3(p.x, 0, p.y)
		n.rotation.y = rng.randf() * TAU
		n.scale = Vector3.ONE * rng.randf_range(0.9, 1.4)
		add_child(n)
		if kind == "lantern_ice":
			var l := OmniLight3D.new()
			l.light_color = Color(0.6, 0.9, 1.0)
			l.light_energy = 1.2
			l.omni_range = 4.0
			l.position.y = 0.8
			n.add_child(l)


func _on_stage(e: FloeEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_blocks.clear()
	_slides.clear()
	_mites.clear()
	_otter = _scene("otter", Vector3(0.5, 0.7, 0.5), Color(0.55, 0.38, 0.25))
	_stage.add_child(_otter)
	_otter.scale = Vector3.ONE * 1.3
	_otter_anim = _otter.find_child("AnimationPlayer", true, false)
	_play(_otter_anim, "idle", true)
	_sync_blocks(e, true)
	_place_camera()


func _block_node(kind: int, egg: bool) -> Node3D:
	var n := _scene("gem_block" if kind == E.GEM else ("ice_block_egg" if egg else "ice_block"))
	return n


func _sync_blocks(e: FloeEngine, quiet := false) -> void:
	for y in E.H:
		for x in E.W:
			var c := Vector2i(x, y)
			var v := e.at(c)
			var have: Dictionary = _blocks.get(c, {})
			if v == E.EMPTY and not have.is_empty():
				(have["node"] as Node3D).queue_free()
				_blocks.erase(c)
			elif v != E.EMPTY and (have.is_empty() or have["kind"] != v or have["egg"] != e.eggs.has(c)):
				if not have.is_empty():
					(have["node"] as Node3D).queue_free()
				var n := _block_node(v, e.eggs.has(c))
				n.position = cell(Vector2(c))
				_stage.add_child(n)
				_blocks[c] = {"node": n, "kind": v, "egg": e.eggs.has(c)}


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"push":
			_play(_otter_anim, "push")
		"shake":
			_play(_otter_anim, "kick_wall")
			_shake_t[d["side"]] = 0.5
			_cam_shake = 0.15
		"slide":
			_sync_blocks(e)
		"stop":
			_sync_blocks(e)
			_fx.burst(cell(Vector2(d["cell"]), 0.3), Color(0.8, 0.95, 1.0), 10, 1.5, 0.4, 0.06, 0.0, -4.0, 0.7)
		"shatter":
			var p := cell(Vector2(d["cell"]), 0.45)
			_fx.burst(p, Color(0.75, 0.92, 1.0), 26, 3.0, 0.6, 0.1, 0.0, -9.0, 1.0)
			_fx.burst(p, Color(0.6, 0.9, 1.0), 12, 2.0, 0.5, 0.06, 1.0, -2.0, 1.0, "glow")
			if d.get("egg", false):
				_fx.burst(p, Color(1.0, 0.85, 0.5), 14, 2.0, 0.6, 0.08, 1.0, -3.0, 1.0, "glow")
			_sync_blocks(e)
		"crush":
			_fx.burst(cell(d["pos"], 0.3), Color(1.0, 0.9, 0.5), 24, 3.0, 0.6, 0.1, 1.0, -5.0, 1.0, "glow")
			_cam_shake = 0.2
		"stomp":
			_fx.burst(cell(d["pos"], 0.2), Color(0.8, 0.9, 1.0), 14, 2.0, 0.4, 0.07, 1.0, -5.0, 1.0, "glow")
		"hatch":
			_sync_blocks(e)
			_fx.burst(cell(Vector2(d["cell"]), 0.4), Color(0.7, 0.95, 1.0), 16, 2.0, 0.5, 0.07, 1.0, -4.0, 1.0, "glow")
		"gems":
			for y in E.H:
				for x in E.W:
					if e.at(Vector2i(x, y)) == E.GEM:
						_fx.burst(cell(Vector2(x, y), 0.6), Color(0.5, 1.0, 1.0), 30, 3.5, 0.9, 0.12, 1.0, -2.0, 1.0, "glow")
						_fx.flash(cell(Vector2(x, y), -1.5), Color(0.5, 1.0, 1.0), 3.0)
		"die":
			_play(_otter_anim, "die")
			_cam_shake = 0.4
		"cleared":
			_play(_otter_anim, "cheer", true)


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _otter == null:
		return
	# the otter
	var o := e.otter
	_otter.position = cell(o["pos"])
	var f := Vector2(o["facing"])
	_otter.rotation.y = lerp_angle(_otter.rotation.y, atan2(-f.x, -f.y), minf(1.0, delta * 18.0))
	if e.phase == E.Phase.PLAY and _otter_anim:
		var cur := _otter_anim.current_animation
		if cur not in ["push", "kick_wall"] or not _otter_anim.is_playing():
			var want := "walk" if o["moving"] else "idle"
			if cur != want:
				_play(_otter_anim, want, true)
	elif e.phase == E.Phase.READY and _otter_anim and _otter_anim.current_animation in ["die", "cheer"]:
		_play(_otter_anim, "idle", true)
	# sliding blocks
	var live := {}
	for s in e.slides:
		live[s["id"]] = true
		if not _slides.has(s["id"]):
			var n := _block_node(s["kind"], s["egg"])
			_stage.add_child(n)
			_slides[s["id"]] = n
		var n: Node3D = _slides[s["id"]]
		n.position = cell(s["pos"])
		if fmod(_time, 0.06) < delta:
			_fx.burst(n.position + Vector3(0, 0.05, 0) - Vector3(s["dir"].x, 0, s["dir"].y) * 0.4, Color(0.9, 0.95, 1.0), 3, 0.8, 0.4, 0.05, 0.0, -1.0, 0.5)
	for id in _slides.keys():
		if not live.has(id):
			_slides[id].queue_free()
			_slides.erase(id)
	# mites
	var alive := {}
	for m in e.mites:
		var id: int = m["id"]
		alive[id] = true
		if not _mites.has(id):
			var n := _scene("mite", Vector3(0.45, 0.5, 0.45), MITE_TINTS[e.stage % MITE_TINTS.size()])
			_tint(n, "mite_body", MITE_TINTS[e.stage % MITE_TINTS.size()])
			n.scale = Vector3.ONE * 1.25
			_stage.add_child(n)
			_mites[id] = {"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""}
		var v: Dictionary = _mites[id]
		var node: Node3D = v["node"]
		node.position = cell(m["pos"])
		var md := Vector2(m["dir"])
		if md != Vector2.ZERO:
			node.rotation.y = lerp_angle(node.rotation.y, atan2(-md.x, -md.y), minf(1.0, delta * 12.0))
		var want := "walk"
		if m["hatch"] > 0.0: want = "hatch"
		elif m["stun"] > 0.0: want = "stunned"
		elif m["chew"] > 0.0: want = "chew"
		elif m["carried"]: want = "stunned"
		if v["last"] != want:
			v["last"] = want
			_play(v["anim"], want, want != "hatch")
	for id in _mites.keys():
		if not alive.has(id):
			var node: Node3D = _mites[id]["node"]
			_play(_mites[id]["anim"], "squash")
			var tw := create_tween()
			tw.tween_property(node, "scale", Vector3(1.4, 0.1, 1.4), 0.25)
			tw.tween_callback(node.queue_free)
			_mites.erase(id)
	# wall wobble
	for side in _walls:
		_shake_t[side] = maxf(0.0, _shake_t[side] - delta)
		var k: float = _shake_t[side]
		for w in _walls[side]:
			var base: Vector3 = w.get_meta("base")
			w.position = base + Vector3(side.x, 0, side.y) * sin(k * 60.0) * k * 0.25
	_cam_shake = maxf(0.0, _cam_shake - delta * 1.5)
	_place_camera()


func _place_camera() -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var j := Vector3(sin(_time * 50.0), 0, cos(_time * 43.0)) * _cam_shake * _cam_shake * (0.3 if Settings.camera_shake else 0.0)
	var need := maxf(9.2, 8.6 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var target := Vector3(0, 0, 0.6)
	camera.position = target + Vector3(0, 0.87, 0.5).normalized() * dist + j
	camera.look_at(target + j, Vector3.UP)
