class_name TorchView3D
extends Node3D
## Four Torches in 3D: a dark dungeon of stone floors and brick walls, lit by the heroes' own torches and the sconces
## on the walls (a few real lights follow the party round the nearest ones); doors lift away, the exit glows. Heroes
## wear their colours; monsters pour out of generators that crack as they are hit; missiles spin; treasure gleams.
## The camera follows the party from above at an angle. World: tile (x, y) -> (x + 0.5, 0, y + 0.5), floor at y = 0.

const T = preload("res://games/fourtorches/engine/torch_engine.gd")
const M := "res://games/fourtorches/art/models/"
const WALL_H := 1.5
const TEAM := [Color(0.9, 0.2, 0.15), Color(0.2, 0.45, 0.95), Color(0.95, 0.8, 0.2), Color(0.25, 0.8, 0.3)]
const GEN_MODEL := {"bones": "gen_bones", "hut": "gen_hut", "brazier": "gen_brazier"}
const SHOT_MODEL := {"knight": "throw_axe", "shieldmaiden": "throw_sword", "mage": "fireball", "ranger": "arrow", "imp_fire": "imp_fire", "arrow": "arrow"}
const LIGHTS := 10

@export var game: TorchGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _moon: DirectionalLight3D
var _stage: Node3D
var _heroes: Array = []
var _monsters := {}
var _gens: Array = []
var _items := {}
var _doors := {}
var _shots: Array = []
var _sconces: Array[Vector3] = []
var _lights: Array[OmniLight3D] = []
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.01, 0.01, 0.015)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.5, 0.45, 0.45)
	_env.ambient_light_energy = 0.85
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.9
	_env.glow_hdr_threshold = 0.9
	_env.ssao_enabled = true
	_env.fog_enabled = true
	_env.fog_light_color = Color(0.1, 0.08, 0.07)
	_env.fog_density = 0.02
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.1
	_we = WorldEnvironment.new()
	_we.environment = _env
	add_child(_we)
	_moon = DirectionalLight3D.new()
	_moon.rotation_degrees = Vector3(-60, -30, 0)
	_moon.light_color = Color(0.55, 0.6, 0.85)
	_moon.light_energy = 0.55
	_moon.shadow_enabled = true
	add_child(_moon)
	camera = Camera3D.new()
	camera.fov = 40
	camera.far = 200.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 20.0
	add_child(_fx)
	for i in LIGHTS:
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.65, 0.3)
		l.light_energy = 0.0
		l.omni_range = 5.5
		l.shadow_enabled = i < 3
		add_child(l)
		_lights.append(l)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mat(col: Color, rough := 0.5, metal := 0.0, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	m.metallic = metal
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _play(ap: AnimationPlayer, anim: String, loop := true) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.1)


static func w(p: Vector2) -> Vector3:
	return Vector3(p.x, 0.0, p.y)


static func wc(c: Vector2i) -> Vector3:
	return Vector3(c.x + 0.5, 0.0, c.y + 0.5)


# ------------------------------------------------------------------ a level

func _on_level(e: TorchEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_monsters.clear()
	_items.clear()
	_doors.clear()
	_shots.clear()
	_gens.clear()
	_sconces.clear()
	_build_dungeon(e)
	_heroes.clear()
	for h in e.heroes:
		var n := _scene(h["cls"])
		if n == null:
			n = Node3D.new()
			var b := MeshInstance3D.new()
			var cap := CapsuleMesh.new()
			cap.radius = 0.28
			cap.height = 0.9
			b.mesh = cap
			b.material_override = _mat(TEAM[h["i"] % 4], 0.5)
			b.position.y = 0.45
			n.add_child(b)
		# a ring of the hero's colour at their feet, so you know who's who
		var ring := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 0.38
		tm.outer_radius = 0.45
		ring.mesh = tm
		ring.material_override = _mat(TEAM[h["i"] % 4], 0.4, 0.0, 2.0)
		ring.position.y = 0.03
		ring.scale = Vector3(1, 0.2, 1)
		n.add_child(ring)
		n.scale = Vector3.ONE * 1.25   # heroes read at a glance, as the classic's did
		_stage.add_child(n)
		_heroes.append({"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""})
	for g in e.gens:
		var n := _scene(GEN_MODEL[g["kind"]])
		if n == null:
			n = MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.3
			cm.bottom_radius = 0.5
			cm.height = 1.0
			(n as MeshInstance3D).mesh = cm
			(n as MeshInstance3D).material_override = _mat(Color(0.5, 0.4, 0.35), 0.8)
			n.position.y = 0.5
		var holder := Node3D.new()
		holder.position = wc(g["cell"])
		holder.add_child(n)
		_stage.add_child(holder)
		_gens.append(holder)
	if _cam_pos == Vector3.ZERO:
		_place_camera(e, 1.0, true)


## Floors, walls (only those beside a floor), doors, the exit, sconces on some walls.
func _build_dungeon(e: TorchEngine) -> void:
	var floors: Array[Transform3D] = []
	var walls: Array[Transform3D] = []
	var caps: Array[Transform3D] = []
	for y in T.H:
		for x in T.W:
			var c := Vector2i(x, y)
			var t := e.tile(c)
			var gen_here := false
			for g in e.gens:
				if g["cell"] == c:
					gen_here = true
			if t != 0 or gen_here:
				floors.append(Transform3D(Basis(), wc(c)))
			if t == 0 and not gen_here:
				var beside := false
				for dd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1)]:
					if e.tile(c + dd) != 0:
						beside = true
				if beside:
					walls.append(Transform3D(Basis(), wc(c) + Vector3(0, WALL_H * 0.5, 0)))
					caps.append(Transform3D(Basis(), wc(c) + Vector3(0, WALL_H + 0.01, 0)))
					# a sconce on some walls facing a floor to the south (towards the camera)
					if e.tile(c + Vector2i(0, 1)) == 1 and (x * 7 + y * 3) % 9 == 0:
						_sconce(wc(c) + Vector3(0, 1.0, 0.52))
			if t == 2:
				var d := _scene("door")
				if d == null:
					d = MeshInstance3D.new()
					var bm := BoxMesh.new()
					bm.size = Vector3(1, 1.3, 1)
					(d as MeshInstance3D).mesh = bm
					(d as MeshInstance3D).material_override = _mat(Color(0.45, 0.3, 0.18), 0.7, 0.2)
					d.position.y = 0.65
				var hd := Node3D.new()
				hd.position = wc(c)
				hd.add_child(d)
				_stage.add_child(hd)
				_doors[c] = hd
			elif t == 3:
				var ex := _scene("exit")
				if ex == null:
					ex = MeshInstance3D.new()
					var pm := PlaneMesh.new()
					pm.size = Vector2(0.9, 0.9)
					(ex as MeshInstance3D).mesh = pm
					(ex as MeshInstance3D).material_override = _mat(Color(0.4, 0.8, 1.0), 0.3, 0.0, 3.0)
					ex.position.y = 0.02
				ex.position += wc(c)
				_stage.add_child(ex)
				var el := OmniLight3D.new()
				el.light_color = Color(0.45, 0.8, 1.0)
				el.light_energy = 2.0
				el.omni_range = 4.0
				el.position = wc(c) + Vector3(0, 0.8, 0)
				_stage.add_child(el)
	_batch(PlaneMesh.new(), Pbr.material("stone_bricks", Color(0.55, 0.52, 0.5), 0.5), floors, Vector3(1, 1, 1))
	_batch(BoxMesh.new(), Pbr.material("dark_rock", Color(0.75, 0.7, 0.68), 0.6), walls, Vector3(1, WALL_H, 1))
	_batch(PlaneMesh.new(), Pbr.material("dark_rock", Color(0.32, 0.3, 0.3), 0.6), caps, Vector3(1, 1, 1))
	for it in e.items:
		_item(it)


func _batch(mesh: Mesh, mat: Material, xs: Array[Transform3D], size: Vector3) -> void:
	if mesh is PlaneMesh:
		(mesh as PlaneMesh).size = Vector2(size.x, size.z)
	elif mesh is BoxMesh:
		(mesh as BoxMesh).size = size
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xs.size()
	for i in xs.size():
		mm.set_instance_transform(i, xs[i])
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	_stage.add_child(mmi)


func _sconce(at: Vector3) -> void:
	var n := _scene("torch_wall")
	if n == null:
		n = MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.08
		sm.height = 0.16
		(n as MeshInstance3D).mesh = sm
		(n as MeshInstance3D).material_override = _mat(Color(1.0, 0.6, 0.2), 0.3, 0.0, 6.0)
	n.position = at
	_stage.add_child(n)
	_sconces.append(at)


func _item(it: Dictionary) -> void:
	var n := _scene(it["kind"])
	if n == null:
		n = MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.2
		sm.height = 0.4
		(n as MeshInstance3D).mesh = sm
		(n as MeshInstance3D).material_override = _mat({"key": Color(1.0, 0.85, 0.3), "potion": Color(0.4, 0.6, 1.0)}.get(it["kind"], Color(0.8, 0.5, 0.3)), 0.3, 0.3, 0.6)
		n.position.y = 0.2
	var hd := Node3D.new()
	hd.position = wc(it["cell"])
	hd.add_child(n)
	_stage.add_child(hd)
	_items[it["cell"]] = hd


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"kill":
			var p := w(d["pos"]) + Vector3(0, 0.5, 0)
			_fx.burst(p, Color(0.6, 0.9, 1.0) if d["kind"] == "ghost" else Color(1.0, 0.5, 0.3), 16, 3.0, 0.5, 0.08, 1.0, -3.0, 1.0, "glow")
			_fx.burst(p, Color(0.35, 0.3, 0.3), 8, 1.5, 0.8, 0.2, 0.0, 1.0, 1.0, "smoke")
		"hit":
			var p := w(d["pos"]) + Vector3(0, 0.5, 0)
			_fx.burst(p, Color(1.0, 0.85, 0.5), 5, 2.0, 0.25, 0.05, 1.0, -4.0, 1.0, "glow")
		"gen_hit":
			_fx.burst(w(d["pos"]) + Vector3(0, 0.6, 0), Color(0.8, 0.7, 0.6), 14, 2.5, 0.6, 0.12, 0.0, -6.0, 1.0)
		"gen_break":
			var p := w(d["pos"]) + Vector3(0, 0.6, 0)
			_fx.burst(p, Color(1.0, 0.6, 0.3), 40, 4.0, 0.8, 0.1, 1.0, -4.0, 1.0, "glow")
			_fx.burst(p, Color(0.4, 0.35, 0.3), 20, 2.0, 1.4, 0.3, 0.0, 1.0, 1.0, "smoke")
			_fx.flash(p, Color(1.0, 0.6, 0.3), 3.0)
			_shake = 0.4
		"door":
			for c in d["cells"]:
				if _doors.has(c):
					var n: Node3D = _doors[c]
					create_tween().tween_property(n, "position:y", -1.6, 0.6)
					_doors.erase(c)
		"blast":
			var p := w(d["pos"]) + Vector3(0, 0.5, 0)
			for k in 3:
				_fx.burst(p, Color(0.6, 0.8, 1.0), 60, 9.0, 0.8, 0.12, 1.0, 0.0, 0.2, "glow")
			_fx.flash(p, Color(0.7, 0.8, 1.0), 8.0)
			_shake = 0.8
		"hurt":
			var h := e.heroes[d["h"]]
			_fx.burst(w(h["pos"]) + Vector3(0, 0.6, 0), Color(1.0, 0.3, 0.2), 6, 2.0, 0.3, 0.06, 1.0, -4.0, 1.0, "glow")
		"die":
			var h := e.heroes[d["h"]]
			_fx.burst(w(h["pos"]) + Vector3(0, 0.5, 0), TEAM[d["h"] % 4], 30, 3.0, 0.9, 0.08, 1.0, -2.0, 1.0, "glow")
		"exit":
			for h in e.heroes:
				_fx.burst(w(h["pos"]) + Vector3(0, 0.5, 0), Color(0.5, 0.85, 1.0), 30, 3.0, 1.0, 0.08, 1.0, 2.0, 1.0, "glow")
		"rejoin":
			_fx.burst(w(d["pos"]) + Vector3(0, 0.5, 0), TEAM[d["h"] % 4], 24, 2.5, 0.7, 0.08, 1.0, 1.0, 1.0, "glow")
		"spawn":
			_fx.burst(w(d["pos"]) + Vector3(0, 0.4, 0), Color(0.6, 0.4, 0.8), 8, 1.5, 0.5, 0.15, 0.0, 1.0, 1.0, "smoke")


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 1.8)
	var e := game.engine
	if e == null or _stage == null or _heroes.size() != e.heroes.size():
		return
	for i in e.heroes.size():
		_place_hero(e, i, delta)
	_place_monsters(e, delta)
	_place_items(e)
	_place_gens(e)
	_place_shots(e, delta)
	_place_lights(e)
	_place_camera(e, delta)


func _place_hero(e: TorchEngine, i: int, delta: float) -> void:
	var h := e.heroes[i]
	var rec: Dictionary = _heroes[i]
	var n: Node3D = rec["node"]
	n.position = w(h["pos"])
	var f: Vector2 = h["face"]
	n.rotation.y = lerp_angle(n.rotation.y, atan2(f.x, f.y), minf(1.0, delta * 14.0))
	n.visible = not h["dead"] or rec["last"] == "die"
	var want := "idle"
	if h["dead"]:
		want = "die"
	elif e.phase == T.Phase.EXIT:
		want = "cheer"
	elif h["fire"]:
		want = "attack"
	elif (h["move"] as Vector2).length() > 0.1:
		want = "run"
	if want != rec["last"]:
		rec["last"] = want
		_play(rec["anim"], want, want in ["idle", "run", "cheer", "attack"])


func _place_monsters(e: TorchEngine, delta: float) -> void:
	var live := {}
	for m in e.monsters:
		var id: int = m["id"]
		live[id] = true
		if not _monsters.has(id):
			var n := _scene(m["kind"])
			if n == null:
				n = MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = 0.32
				sm.height = 0.64
				(n as MeshInstance3D).mesh = sm
				(n as MeshInstance3D).material_override = _mat({"ghost": Color(0.7, 0.8, 1.0), "grunt": Color(0.5, 0.4, 0.3), "imp": Color(0.9, 0.3, 0.2), "skeleton": Color(0.9, 0.9, 0.85), "sorcerer": Color(0.5, 0.3, 0.7), "deathshade": Color(0.15, 0.1, 0.15)}[m["kind"]], 0.5)
				n.position.y = 0.35
				var hd := Node3D.new()
				hd.add_child(n)
				n = hd
			var ap := n.find_child("AnimationPlayer", true, false) as AnimationPlayer
			_play(ap, "walk", true)
			_stage.add_child(n)
			_monsters[id] = n
		var n: Node3D = _monsters[id]
		n.position = w(m["pos"]) + Vector3(0, 0.15 * sin(_time * 4.0 + id) if m["kind"] == "ghost" else 0.0, 0)
		var f: Vector2 = m["face"]
		n.rotation.y = lerp_angle(n.rotation.y, atan2(f.x, f.y), minf(1.0, delta * 8.0))
		n.visible = m["fade"] == 0.0 or fmod(_time, 0.4) < 0.05
		n.scale = Vector3.ONE * (1.15 if m["hit_t"] > 0.0 else 1.0)
	for id in _monsters.keys():
		if not live.has(id):
			(_monsters[id] as Node3D).queue_free()
			_monsters.erase(id)


func _place_items(e: TorchEngine) -> void:
	var live := {}
	for it in e.items:
		live[it["cell"]] = true
		if not _items.has(it["cell"]):
			_item(it)
	for c in _items.keys():
		var n: Node3D = _items[c]
		if not live.has(c):
			_fx.burst(n.position + Vector3(0, 0.4, 0), Color(1.0, 0.85, 0.4), 14, 2.0, 0.5, 0.06, 1.0, -2.0, 1.0, "glow")
			n.queue_free()
			_items.erase(c)
		else:
			n.rotation.y += 0.01


func _place_gens(e: TorchEngine) -> void:
	for i in e.gens.size():
		var g: Dictionary = e.gens[i]
		var n: Node3D = _gens[i]
		if g["hp"] <= 0.0:
			n.visible = false
			continue
		for s in 3:
			var part := n.find_child("state_%d" % s, true, false) as Node3D
			if part:
				part.visible = s == int(g["state"])


func _place_shots(e: TorchEngine, delta: float) -> void:
	while _shots.size() < e.missiles.size():
		var n := Node3D.new()
		_stage.add_child(n)
		_shots.append({"node": n, "kind": ""})
	for i in _shots.size():
		var rec: Dictionary = _shots[i]
		var n: Node3D = rec["node"]
		if i >= e.missiles.size():
			n.visible = false
			continue
		var s: Dictionary = e.missiles[i]
		if rec["kind"] != s["kind"]:
			for c in n.get_children():
				c.queue_free()
			var m := _scene(SHOT_MODEL.get(s["kind"], "arrow"))
			if m == null:
				var mi := MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = 0.12
				sm.height = 0.24
				mi.mesh = sm
				mi.material_override = _mat(Color(1.0, 0.7, 0.3), 0.3, 0.0, 3.0)
				m = mi
			n.add_child(m)
			rec["kind"] = s["kind"]
		n.visible = true
		n.position = w(s["pos"]) + Vector3(0, 0.55, 0)
		var v: Vector2 = s["vel"]
		if s["kind"] in ["knight", "shieldmaiden"]:
			n.rotation.y += delta * 18.0
		else:
			n.rotation.y = atan2(v.x, v.y)


## The heroes' torches, and the nearest sconces, get the real lights.
func _place_lights(e: TorchEngine) -> void:
	var k := 0
	for h in e.heroes:
		if h["dead"] or k >= _lights.size():
			continue
		var l := _lights[k]
		l.position = w(h["pos"]) + Vector3(0, 1.2, 0.2)
		l.light_color = Color(1.0, 0.7, 0.4).lerp(TEAM[h["i"] % 4], 0.15)
		l.light_energy = 2.0 + 0.25 * sin(_time * 11.0 + h["i"] * 2.0)
		l.omni_range = 7.5
		k += 1
	var c := w(e.anchor())
	var near := _sconces.duplicate()
	near.sort_custom(func(a, b): return a.distance_squared_to(c) < b.distance_squared_to(c))
	for s in near:
		if k >= _lights.size():
			break
		var l := _lights[k]
		l.position = s + Vector3(0, 0.1, 0.2)
		l.light_color = Color(1.0, 0.6, 0.25)
		l.light_energy = 1.4 + 0.3 * sin(_time * 9.0 + s.x)
		l.omni_range = 4.5
		k += 1
	while k < _lights.size():
		_lights[k].light_energy = 0.0
		k += 1


func _place_camera(e: TorchEngine, delta: float, snap := false) -> void:
	# the screen sits on the human players (the engine keeps everyone inside VIEW round this point)
	var look := w(e.anchor())
	var dist := 13.0
	var el := deg_to_rad(58.0)
	var pos := look + Vector3(0, sin(el), cos(el)) * dist
	var j := Vector3(sin(_time * 47.0), 0, cos(_time * 41.0)) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var k := 1.0 if snap else minf(1.0, delta * 4.0)
	_cam_pos = _cam_pos.lerp(pos, k)
	_cam_look = _cam_look.lerp(look, k)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
