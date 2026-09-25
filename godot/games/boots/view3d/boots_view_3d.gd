class_name BootsView3D
extends Node3D
## Muddy Boots in 3D: a sculpted jungle from the map's tiles (grass, earth, sand, water, cliffs), palms and bushes on
## tree tiles, boulders on rock, huts and the tent, and the squad, the enemy and the hostages as animated figures.
## The camera follows the squad over a map bigger than the screen. Map point (x, y) is at world (x - 0.5, 0, y - 0.5),
## so tile centres sit on whole numbers like the shared water shader expects.

const E = preload("res://games/boots/engine/boots_engine.gd")
const T = preload("res://games/boots/engine/boots_map.gd").T
const M := "res://games/boots/art/models/"
const HEIGHT := {T.LAND: 0.0, T.ROUGH: 0.05, T.WATER: -0.55, T.SHALLOW: -0.14, T.TREE: 0.02, T.ROCK: 0.05,
	T.QUICKSAND: -0.06, T.SNOW: 0.04, T.CLIFF: 1.3}
## land shader channels: red = soil (mud), green = rock (the rock texture is pale: use it sparingly), blue = cold tint
const COLOR := {T.LAND: Color(0, 0, 0), T.ROUGH: Color(0.7, 0.08, 0), T.WATER: Color(1, 0.0, 0), T.SHALLOW: Color(0.9, 0, 0),
	T.TREE: Color(0.15, 0, 0), T.ROCK: Color(0.55, 0.25, 0), T.QUICKSAND: Color(0.9, 0.05, 0.3), T.SNOW: Color(0, 0, 1), T.CLIFF: Color(0.3, 0.6, 0)}
const GREEN := Color(0.25, 0.42, 0.2)
const KHAKI := Color(0.62, 0.55, 0.36)

@export var game: BootsGame

var _camera: Camera3D
var _board: Node3D
var _fx: BootsEffects
var _water_mat: ShaderMaterial
var _people := {}  ## id -> {node, anim, kind}
var _huts := {}    ## id -> node
var _crates := {}  ## id -> node
var _mines: Array[Node3D] = []
var _tracers: Array[MeshInstance3D] = []
var _grenades: Array[MeshInstance3D] = []
var _rockets: Array[Node3D] = []
var _cursor: MeshInstance3D
var _cam_target := Vector3.ZERO
var _time := 0.0
var _shake := 0.0


func _ready() -> void:
	game.view = self
	_build_world()
	_fx = BootsEffects.new()
	add_child(_fx)
	game.mission_started.connect(_on_mission)
	if game.engine:
		_on_mission(game.engine)


func w(p: Vector2, y := 0.0) -> Vector3:
	return Vector3(p.x - 0.5, y, p.y - 0.5)


## The map point under a screen position (on the ground plane), or null.
func screen_to_map(screen: Vector2):
	var from := _camera.project_ray_origin(screen)
	var dir := _camera.project_ray_normal(screen)
	if absf(dir.y) < 0.001:
		return null
	var t := -from.y / dir.y
	if t < 0.0:
		return null
	var hit := from + dir * t
	return Vector2(hit.x + 0.5, hit.z + 0.5)


# ------------------------------------------------------------------ world

func _build_world() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.3, 0.5, 0.75)
	sky_mat.sky_horizon_color = Color(0.75, 0.82, 0.8)
	var sky := Sky.new()
	sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	Look.sky_ambient(env, Color(0.55, 0.65, 0.7), 0.5)
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.95
	env.glow_enabled = true
	env.glow_intensity = 0.4
	env.glow_hdr_threshold = 1.0
	env.ssao_enabled = true
	env.ssao_intensity = 2.0
	env.ssr_enabled = true
	Look.fog(env, Color(0.6, 0.72, 0.65), 0.002)  # the jungle air: a hint of haze
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.25
	env.adjustment_contrast = 1.12
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -30, 0)
	sun.light_color = Color(1.0, 0.95, 0.85)
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 40.0
	add_child(sun)
	_camera = Camera3D.new()
	_camera.fov = 45
	_camera.current = true
	add_child(_camera)
	_cursor = MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.28
	tm.outer_radius = 0.36
	_cursor.mesh = tm
	var cm := StandardMaterial3D.new()
	cm.albedo_color = Color(1.0, 0.85, 0.3)
	cm.emission_enabled = true
	cm.emission = Color(1.0, 0.8, 0.3)
	cm.emission_energy_multiplier = 1.5
	cm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_cursor.material_override = cm
	add_child(_cursor)
	var tracer_mat := StandardMaterial3D.new()
	tracer_mat.albedo_color = Color(1.0, 0.85, 0.4)
	tracer_mat.emission_enabled = true
	tracer_mat.emission = Color(1.0, 0.8, 0.35)
	tracer_mat.emission_energy_multiplier = 4.0
	tracer_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for i in 64:
		var t := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.035
		cap.height = 0.45
		t.mesh = cap
		t.material_override = tracer_mat
		t.visible = false
		add_child(t)
		_tracers.append(t)
	for i in 6:
		var g := MeshInstance3D.new()
		var s := SphereMesh.new()
		s.radius = 0.08
		s.height = 0.16
		g.mesh = s
		g.material_override = Pbr.material("metal", Color(0.3, 0.35, 0.25), 2.0, 0.6, 0.6)
		g.visible = false
		add_child(g)
		_grenades.append(g)
		var r := Node3D.new()
		var body := MeshInstance3D.new()
		var cyl := CapsuleMesh.new()
		cyl.radius = 0.05
		cyl.height = 0.5
		body.mesh = cyl
		body.rotation.x = PI * 0.5
		body.material_override = Pbr.material("metal", Color(0.6, 0.6, 0.55), 2.0, 0.6, 0.5)
		r.add_child(body)
		var trail := CPUParticles3D.new()
		trail.amount = 40
		trail.lifetime = 0.6
		trail.local_coords = false
		trail.gravity = Vector3(0, 0.5, 0)
		trail.initial_velocity_max = 0.2
		var q := QuadMesh.new()
		q.size = Vector2(0.3, 0.3)
		trail.mesh = q
		trail.material_override = Fx.material("smoke", Color(0.85, 0.85, 0.85, 0.7))
		trail.scale_amount_curve = Fx.size_curve(true)
		r.add_child(trail)
		r.visible = false
		add_child(r)
		_rockets.append(r)


func _scene(name: String) -> Node3D:
	return (load(M + name + ".glb") as PackedScene).instantiate()


func _person(kind: String, color: Color) -> Dictionary:
	var n := _scene("hostage" if kind == "hostage" else "soldier")
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and mat.resource_name in ["uniform", "helmet"] and kind != "hostage":
				var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				s.albedo_color = color if mat.resource_name == "uniform" else color.darkened(0.25)
				m.set_surface_override_material(i, s)
	_board.add_child(n)
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	for a in ap.get_animation_list():
		ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "run", "swim", "walk", "wave"] else Animation.LOOP_NONE
	return {"node": n, "anim": ap, "kind": kind, "dead": false}


func _on_mission(e: BootsEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_people.clear()
	_huts.clear()
	_crates.clear()
	_mines.clear()
	e.event.connect(_on_event)
	_build_terrain(e)
	for s in e.soldiers:
		_people[s["id"]] = _person("soldier", GREEN)
	for h in e.hostages:
		_people[h["id"]] = _person("hostage", Color.WHITE)
	for h in e.huts:
		var n := _scene("hut")
		n.position = w(Vector2(h["cell"]) + (Vector2(1, 1) if e.map.source == "text" else Vector2(0.5, 0.5)))
		_board.add_child(n)
		_huts[h["id"]] = n
	for t in e.tents:
		var n := _scene("tent")
		n.position = w(t)
		n.rotation.y = 0.4
		_board.add_child(n)
	for c in e.crates:
		var n := _scene("grenade_crate" if c["kind"] == "grenades" else "rocket_crate")
		n.position = w(c["pos"])
		_board.add_child(n)
		_crates[c["id"]] = n
	for m in e.mines:
		var n := _scene("mine")
		n.position = w(m, -0.02)  # half buried: hard to spot
		_board.add_child(n)
		_mines.append(n)
	var l := e.leader()
	_cam_target = w(l["pos"]) if not l.is_empty() else Vector3.ZERO
	_place_camera(1.0)


func _build_terrain(e: BootsEngine) -> void:
	var m := e.map
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var corner := func(cx: int, cy: int) -> Array:
		var hsum := 0.0
		var col := Color(0, 0, 0)
		var n := 0
		var low := INF
		for dy in [-1, 0]:
			for dx in [-1, 0]:
				var c := Vector2i(cx + dx, cy + dy)
				var t: int = m.at(c) if m.inside(c) else T.LAND
				var hh: float = HEIGHT[t] if t != T.CLIFF else 0.0
				hsum += hh
				low = minf(low, hh)
				col += COLOR[t]
				n += 1
		var high := -INF
		for dy2 in [-1, 0]:
			for dx2 in [-1, 0]:
				var c2 := Vector2i(cx + dx2, cy + dy2)
				var t2: int = m.at(c2) if m.inside(c2) else T.LAND
				if t2 != T.WATER and t2 != T.SHALLOW:
					high = maxf(high, HEIGHT[t2] if t2 != T.CLIFF else 0.0)
		var hv := lerpf(hsum / n, low, 0.5) if high == -INF else maxf(high, lerpf(hsum / n, low, 0.5))
		var jitter := (sin(cx * 12.9898 + cy * 78.233) * 43758.5453)
		jitter = (jitter - floorf(jitter)) * 0.06 - 0.03
		return [Vector3(cx - 0.5, hv + jitter, cy - 0.5), col / n]
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
	var lm := ShaderMaterial.new()
	lm.shader = load("res://core/art/shaders/land.gdshader")
	for t in [["grass", "grass"], ["lush", "grass_lush"], ["sand", "soil"], ["rock", "rock"]]:
		lm.set_shader_parameter(t[0] + "_albedo", load(Pbr.ROOT + t[1] + "/albedo.jpg"))
		lm.set_shader_parameter(t[0] + "_normal", load(Pbr.ROOT + t[1] + "/normal.jpg"))
	ground.material_override = lm
	_board.add_child(ground)
	# water over the map, with a shore mask so it foams at the banks
	var water := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(m.w + 20, m.h + 20)
	plane.subdivide_width = m.w + 20
	plane.subdivide_depth = m.h + 20
	water.mesh = plane
	_water_mat = ShaderMaterial.new()
	_water_mat.shader = load("res://core/art/shaders/water.gdshader")
	_water_mat.set_shader_parameter("normal_map", load("res://core/art/textures/water/normal.png"))
	_water_mat.set_shader_parameter("shallow", Color(0.12, 0.45, 0.35))
	_water_mat.set_shader_parameter("mid", Color(0.05, 0.25, 0.25))
	_water_mat.set_shader_parameter("map_size", Vector2(m.w, m.h))
	_water_mat.set_shader_parameter("shore_mask", _shore_mask(m))
	water.material_override = _water_mat
	water.position = Vector3(m.w * 0.5 - 0.5, -0.1, m.h * 0.5 - 0.5)
	water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_board.add_child(water)
	# cliffs, trees and boulders
	var rock := Pbr.material("rock", Color(0.75, 0.72, 0.68), 1.2)
	var rng := RandomNumberGenerator.new()
	rng.seed = e.map.w * 7 + e.map.h
	var palms: Array[Transform3D] = []
	var bushes: Array[Transform3D] = []
	var stones: Array[Transform3D] = []
	for y in m.h:
		for x in m.w:
			var c := Vector2i(x, y)
			var p := Vector3(x, 0, y)
			match m.at(c):
				T.CLIFF:
					var b := MeshInstance3D.new()
					var bm := BoxMesh.new()
					bm.size = Vector3(1.0, HEIGHT[T.CLIFF], 1.0)
					b.mesh = bm
					b.material_override = rock
					b.position = p + Vector3(0, HEIGHT[T.CLIFF] * 0.5, 0)
					_board.add_child(b)
				T.TREE:
					var border := x == 0 or y == 0 or x == m.w - 1 or y == m.h - 1
					var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.8, 1.15))
					if border or rng.randf() < 0.55:
						palms.append(Transform3D(basis, p + Vector3(rng.randf_range(-0.2, 0.2), 0, rng.randf_range(-0.2, 0.2))))
					bushes.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.9, 1.5)), p))
				T.ROCK:
					stones.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1.2, rng.randf_range(0.8, 1.4), 1.2)), p))
	_multi("palm", palms)
	_multi("bush", bushes)
	_multi("boulder", stones)


func _multi(model: String, xf: Array[Transform3D]) -> void:
	if xf.is_empty():
		return
	var root := _scene(model)
	var mesh: Mesh = null
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		mesh = (mi as MeshInstance3D).mesh
		break
	root.free()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xf.size()
	for i in xf.size():
		mm.set_instance_transform(i, xf[i])
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	_board.add_child(inst)


func _shore_mask(m: BootsMap) -> ImageTexture:
	var k := 4
	var img := Image.create(m.w * k, m.h * k, false, Image.FORMAT_L8)
	for y in m.h * k:
		for x in m.w * k:
			var t := m.at(Vector2i(x / k, y / k))
			img.set_pixel(x, y, Color.BLACK if t == T.WATER or t == T.SHALLOW else Color.WHITE)
	for pass_ in 2:
		img.resize(m.w * k / 2, m.h * k / 2, Image.INTERPOLATE_BILINEAR)
		img.resize(m.w * k, m.h * k, Image.INTERPOLATE_CUBIC)
	return ImageTexture.create_from_image(img)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"shot", "enemy_shot":
			_fx.muzzle(w(d["from"], 0.45) + Vector3(d["dir"].x, 0, d["dir"].y) * 0.3)
		"impact":
			_fx.dirt(w(d["pos"], 0.2))
		"explosion":
			if d["splash"]:
				_fx.splash(w(d["pos"], -0.05))
			else:
				_fx.explosion(w(d["pos"], 0.2), 1.0 if not d["mine"] else 0.8)
			_shake = 0.7
		"hut_destroyed":
			_fx.explosion(w(d["pos"], 0.6), 1.8)
			_shake = 1.0
			if _huts.has(d["id"]):
				var n: Node3D = _huts[d["id"]]
				var tw := create_tween()
				tw.tween_property(n, "scale", Vector3(1.2, 0.2, 1.2), 0.35).set_trans(Tween.TRANS_BACK)
				tw.tween_callback(func(): n.visible = false)
		"enemy_death", "death":
			_fx.hit(w(d["pos"], 0.4))
		"pickup":
			if _crates.has(d["id"]):
				_crates[d["id"]].queue_free()
				_crates.erase(d["id"])
			_fx.sparkle(w(d["pos"], 0.4))
		"rescued":
			_fx.sparkle(w(d["pos"], 0.6))


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	var e := game.engine
	if e == null or _board == null:
		return
	_time += delta
	_update_people(e, delta)
	_update_projectiles(e)
	# mines: pulled out of view once they have gone off
	for i in _mines.size():
		_mines[i].visible = i < e.mines.size()
		if _mines[i].visible:
			_mines[i].position = w(e.mines[i], -0.02)
	# the cursor ring on the ground, the camera after the squad
	_cursor.visible = not game.demo
	_cursor.position = w(e.aim, 0.05)
	_cursor.rotation.y += delta * 2.0
	(_cursor.material_override as StandardMaterial3D).albedo_color = Color(1.0, 0.3, 0.2) if e.firing else Color(1.0, 0.85, 0.3)
	var l := e.leader()
	if not l.is_empty():
		_cam_target = _cam_target.lerp(w(l["pos"]), 1.0 - exp(-delta * 3.0))
	_place_camera(delta)


func _place_camera(delta: float) -> void:
	_shake = maxf(0.0, _shake - delta * 2.5)
	var s := _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var jitter := Vector3(sin(_time * 57.0), 0, sin(_time * 63.0)) * s
	_camera.position = _cam_target + Vector3(0, 13.0, 8.5) + jitter
	_camera.look_at(_cam_target + Vector3(0, 0, 0.8) + jitter)


func _update_people(e: BootsEngine, delta: float) -> void:
	var seen := {}
	for s in e.soldiers:
		_pose(_people.get(s["id"]), s, e, delta, false)
		seen[s["id"]] = true
	for en in e.enemies:
		if not _people.has(en["id"]):
			_people[en["id"]] = _person("enemy", KHAKI)
		_pose(_people[en["id"]], en, e, delta, true)
	for h in e.hostages:
		var p: Dictionary = _people[h["id"]]
		var n: Node3D = p["node"]
		n.visible = not h["rescued"]
		var target := w(h["pos"])
		var moving := n.position.distance_to(target) > 0.002
		if moving:
			var d := target - n.position
			n.rotation.y = lerp_angle(n.rotation.y, atan2(d.x, d.z), 1.0 - exp(-delta * 10.0))
		n.position = target
		var a := "walk" if moving else ("wave" if not h["following"] else "idle")
		if p["anim"].current_animation != a:
			p["anim"].play(a, 0.2)


func _pose(p: Dictionary, u: Dictionary, e: BootsEngine, delta: float, enemy: bool) -> void:
	if p == null:
		return
	var n: Node3D = p["node"]
	var ap: AnimationPlayer = p["anim"]
	if not u["alive"]:
		if not p["dead"]:
			p["dead"] = true
			ap.play("die", 0.1)
			get_tree().create_timer(4.0).timeout.connect(func():
				if is_instance_valid(n):
					var tw := create_tween()
					tw.tween_property(n, "position:y", -0.6, 1.5)
					tw.tween_callback(n.hide))
		return
	var target := w(u["pos"])
	var swim := e.swimming(u["pos"])
	target.y = -0.35 if swim else 0.0
	var d := target - n.position
	var moving := Vector2(d.x, d.z).length() > 0.003
	var shooting: bool = (e.firing and not enemy) or (enemy and u.get("alert", false))
	var face := d
	if shooting:
		var aim_at: Vector2 = e.aim if not enemy else (e.leader()["pos"] if not e.leader().is_empty() else u["pos"])
		face = w(aim_at) - n.position
	if Vector2(face.x, face.z).length() > 0.01:
		n.rotation.y = lerp_angle(n.rotation.y, atan2(face.x, face.z), 1.0 - exp(-delta * 12.0))
	n.position = target
	var a := "swim" if swim else ("shoot" if shooting and not moving else ("run" if moving else "idle"))
	if ap.current_animation != a and not (a == "shoot" and ap.current_animation == "shoot" and ap.is_playing()):
		ap.play(a, 0.12, 1.4 if a == "run" else 1.0)
	elif a == "shoot" and not ap.is_playing():
		ap.play("shoot")


func _update_projectiles(e: BootsEngine) -> void:
	for i in _tracers.size():
		var t := _tracers[i]
		t.visible = i < e.bullets.size()
		if t.visible:
			var b: Dictionary = e.bullets[i]
			t.position = w(b["pos"], 0.45)
			var v: Vector2 = b["vel"]
			t.look_at(t.position + Vector3(v.x, 0, v.y), Vector3.UP)
			t.rotate_object_local(Vector3.RIGHT, PI * 0.5)
	for i in _grenades.size():
		var g := _grenades[i]
		g.visible = i < e.grenades_air.size()
		if g.visible:
			var gr: Dictionary = e.grenades_air[i]
			var k: float = gr["t"] / gr["dur"]
			g.position = w((gr["from"] as Vector2).lerp(gr["to"], k), 0.5 + sin(k * PI) * 2.2)
	for i in _rockets.size():
		var r := _rockets[i]
		r.visible = i < e.rockets_air.size()
		(r.get_child(1) as CPUParticles3D).emitting = r.visible
		if r.visible:
			var ro: Dictionary = e.rockets_air[i]
			r.position = w(ro["pos"], 0.5)
			var v: Vector2 = ro["vel"]
			r.look_at(r.position + Vector3(v.x, 0, v.y), Vector3.UP)
