class_name KnucklesView3D
extends Node3D
## Neon Knuckles in 3D: a night street built along the stage (x), fighters on the street (z is depth), a side camera
## that follows the scroll. Three themes: the street (neon signs, shop windows, wet asphalt with puddles), the docks
## (planks, water, containers, cranes) and the rooftops (parapets, water tanks, the skyline). Weapons ride the
## fighters' hands (bone attachments).

const B = preload("res://games/knuckles/engine/brawl_engine.gd")
const M := "res://games/knuckles/art/models/"
const MODEL := {"thug": "thug", "knifer": "knifer", "bruiser": "bruiser", "boss": "boss"}
const NEON: Array[Color] = [Color(1.0, 0.2, 0.6), Color(0.2, 0.9, 1.0), Color(0.6, 0.3, 1.0), Color(1.0, 0.75, 0.2), Color(0.3, 1.0, 0.5)]

@export var game: KnucklesGame

var _camera: Camera3D
var _env: Environment
var _set: Node3D
var _fx: KnucklesEffects
var _nodes := {}  ## fighter id -> {node, anim, weapon_slot, weapon}
var _items := {}  ## item id -> node
var _cam_x := 8.0
var _time := 0.0
var _shake := 0.0


func _ready() -> void:
	_build_env()
	_fx = KnucklesEffects.new()
	add_child(_fx)
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _build_env() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.02, 0.02, 0.05)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.25, 0.28, 0.45)
	_env.ambient_light_energy = 0.9
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.1
	_env.glow_enabled = true
	_env.glow_intensity = 0.9
	_env.glow_bloom = 0.15
	_env.glow_hdr_threshold = 0.8
	_env.ssao_enabled = true
	_env.ssr_enabled = true  # the wet street mirrors the neon
	_env.ssr_max_steps = 64
	Look.fog(_env, Color(0.12, 0.1, 0.22), 0.012)
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.3
	_env.adjustment_contrast = 1.12
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-45, -30, 0)
	moon.light_color = Color(0.55, 0.62, 1.0)
	moon.light_energy = 0.35
	moon.shadow_enabled = true
	add_child(moon)
	_camera = Camera3D.new()
	_camera.fov = 42
	_camera.current = true
	add_child(_camera)


func _scene(name: String) -> Node3D:
	return (load(M + name + ".glb") as PackedScene).instantiate()


func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


## A long strip along the stage, cut into short boxes: each piece gets its own nearby lights (the compatibility
## renderer lights a mesh with its eight nearest lights only).
func _strip(L: float, y: float, z: float, size: Vector3, mat: Material) -> void:
	var seg := 12.0
	var x := -10.0
	while x < L - 10.0:
		_box(_set, Vector3(x + seg * 0.5, y, z), Vector3(seg + 0.001, size.y, size.z), mat)
		x += seg


func _glow(c: Color, energy: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.emission_enabled = true
	m.emission = c
	m.emission_energy_multiplier = energy
	return m


func _light(parent: Node3D, pos: Vector3, c: Color, energy: float, rng_: float) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.position = pos
	l.light_color = c
	l.light_energy = energy
	l.omni_range = rng_
	l.light_specular = 1.0
	parent.add_child(l)
	return l


# ------------------------------------------------------------------ the set

func _on_stage(e: BrawlEngine) -> void:
	if _set:
		_set.queue_free()
	_set = Node3D.new()
	add_child(_set)
	_nodes.clear()
	_items.clear()
	e.event.connect(_on_event)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(e.level.name)
	_env.background_color = {"docks": Color(0.03, 0.04, 0.1), "rooftops": Color(0.07, 0.04, 0.14)}.get(e.level.theme, Color(0.02, 0.02, 0.05))
	match e.level.theme:
		"docks": _build_docks(e, rng)
		"rooftops": _build_rooftops(e, rng)
		_: _build_street(e, rng)
	_cam_x = e.scroll + e.view_width * 0.5
	_place_camera(1.0, e)


func _build_street(e: BrawlEngine, rng: RandomNumberGenerator) -> void:
	var L := e.level.length + 30.0
	var asphalt := Pbr.material("dark_rock", Color(0.42, 0.42, 0.48), 0.5, 0.0, 0.5)
	var walk := Pbr.material("stone_bricks", Color(0.5, 0.5, 0.55), 1.2)
	_strip(L, -0.1, 0, Vector3(0, 0.2, 7.0), asphalt)
	_strip(L, 0.05, -3.4, Vector3(0, 0.2, 1.6), walk)          # sidewalk
	_strip(L, 0.05, -2.62, Vector3(0, 0.22, 0.12), _glow(Color(0.7, 0.7, 0.7), 0.0))  # kerb
	_strip(L, 0.05, 3.9, Vector3(0, 0.2, 1.6), walk)            # the near sidewalk
	_strip(L, 0.05, 3.12, Vector3(0, 0.22, 0.12), _glow(Color(0.7, 0.7, 0.7), 0.0))
	var paint := _glow(Color(0.85, 0.8, 0.55), 0.15)  # dashed centre line
	for i in int(L / 4.0):
		_box(_set, Vector3(-9 + i * 4.0, 0.004, 0.4), Vector3(2.0, 0.01, 0.14), paint)
	# puddles: a glossy film that mirrors the neon
	var puddle := StandardMaterial3D.new()
	puddle.albedo_color = Color(0.02, 0.02, 0.04)
	puddle.roughness = 0.02
	puddle.metallic_specular = 1.0
	for i in int(L / 6.0):
		var p := _box(_set, Vector3(-8 + i * 6.0 + rng.randf_range(-2, 2), 0.005, rng.randf_range(-2.0, 2.2)),
			Vector3(rng.randf_range(1.2, 3.0), 0.01, rng.randf_range(0.6, 1.4)), puddle)
		p.rotation.y = rng.randf_range(-0.4, 0.4)
	# the buildings: brick fronts with lit windows, shop windows and neon signs
	var x := -10.0
	while x < L:
		var w := rng.randf_range(6.0, 11.0)
		var h := rng.randf_range(9.0, 18.0)
		var tint := Color.from_hsv(rng.randf_range(0.0, 0.1), rng.randf_range(0.2, 0.5), rng.randf_range(0.35, 0.6))
		_box(_set, Vector3(x + w * 0.5, h * 0.5, -5.0), Vector3(w - 0.2, h, 1.6), Pbr.material("stone_bricks", tint, 0.5))
		# shop window at street level
		var shop := NEON[rng.randi_range(0, NEON.size() - 1)]
		_box(_set, Vector3(x + w * 0.5, 1.4, -4.18), Vector3(w * 0.6, 2.0, 0.05), _glow(shop.lerp(Color(1, 0.85, 0.7), 0.3) * 0.6, 0.35))
		_box(_set, Vector3(x + w * 0.5, 2.5, -4.1), Vector3(w * 0.62, 0.14, 0.12), _glow(Color(0.1, 0.1, 0.12), 0.0))  # frame
		_box(_set, Vector3(x + w * 0.5, 2.9, -4.05), Vector3(w * 0.66, 0.5, 0.9), _glow(shop.darkened(0.55), 0.2))  # awning
		# upper windows
		for fy in range(1, int(h / 3.0)):
			for fx in range(int(w / 2.2)):
				if rng.randf() < 0.55:
					var lit := rng.randf() < 0.6
					_box(_set, Vector3(x + 1.2 + fx * 2.2, fy * 3.0 + 1.0, -4.18), Vector3(1.0, 1.4, 0.05),
						_glow(Color(0.9, 0.62, 0.35) if lit else Color(0.05, 0.06, 0.1), 0.45 if lit else 0.0))
		# a neon sign sticking out, and its light on the street
		if rng.randf() < 0.8:
			var nc := NEON[rng.randi_range(0, NEON.size() - 1)]
			var sign := _box(_set, Vector3(x + w * rng.randf_range(0.2, 0.8), rng.randf_range(3.8, 6.0), -3.9), Vector3(0.18, rng.randf_range(1.2, 2.4), 0.9), _glow(nc, 2.2))
			sign.rotation.y = PI * 0.5
			_light(_set, sign.position + Vector3(0, 0, 1.2), nc, 2.4, 9.0)
		x += w
	# lamps, parked cars, barrels, trash
	var lx := 4.0
	while lx < L:
		var lamp := _scene("street_lamp")
		lamp.position = Vector3(lx, 0, -3.0)
		lamp.rotation.y = PI
		_set.add_child(lamp)
		_light(_set, Vector3(lx, 4.6, -1.6), Color(1.0, 0.8, 0.55), 2.6, 12.0)
		lx += 14.0
	# parked cars behind the fighters, between the lamps (never in front of the fight)
	var cx := 11.0
	while cx < L:
		var car := _scene("car")
		car.position = Vector3(cx, 0, -3.2)
		car.rotation.y = PI if rng.randf() < 0.5 else 0.0
		_set.add_child(car)
		cx += 14.0 * rng.randi_range(2, 3)
	for i in int(L / 12.0):
		var n := _scene("barrel" if i % 3 == 0 else "trash_bags")
		n.position = Vector3(rng.randf_range(0, L - 10), 0, -3.6)
		_set.add_child(n)
		if i % 3 == 0:
			_light(_set, n.position + Vector3(0, 1.4, 0.3), Color(1.0, 0.5, 0.2), 1.5, 5.0)


func _build_docks(e: BrawlEngine, rng: RandomNumberGenerator) -> void:
	var L := e.level.length + 30.0
	_strip(L, -0.1, 0, Vector3(0, 0.2, 7.0), Pbr.material("planks", Color(0.5, 0.42, 0.35), 0.7))
	var water := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(L + 60, 60)
	plane.subdivide_width = 80
	plane.subdivide_depth = 40
	water.mesh = plane
	var wm := ShaderMaterial.new()
	wm.shader = load("res://core/art/shaders/water.gdshader")
	wm.set_shader_parameter("normal_map", load("res://core/art/textures/water/normal.png"))
	wm.set_shader_parameter("deep", Color(0.01, 0.02, 0.05))
	wm.set_shader_parameter("mid", Color(0.02, 0.05, 0.1))
	wm.set_shader_parameter("shallow", Color(0.03, 0.08, 0.14))
	wm.set_shader_parameter("sky", Color(0.1, 0.1, 0.2))
	water.material_override = wm
	water.position = Vector3(L * 0.5, -0.8, -34)
	_set.add_child(water)
	var x := -6.0
	while x < L:
		var stack := rng.randi_range(1, 3)
		for k in stack:
			var c := _scene("container_%d" % rng.randi_range(0, 3))
			c.position = Vector3(x, k * 2.6, -5.5 - rng.randf_range(0, 1.5))
			_set.add_child(c)
		if rng.randf() < 0.4:
			_light(_set, Vector3(x, 6.0, -2.5), Color(1.0, 0.7, 0.35), 2.0, 12.0)
		x += rng.randf_range(6.5, 9.0)
	for cx in range(0, int(L), 40):  # cranes against the sky
		var steel := _glow(Color(0.8, 0.45, 0.15), 0.0)
		_box(_set, Vector3(cx + 10, 12, -16), Vector3(1.2, 24, 1.2), steel)
		_box(_set, Vector3(cx + 10, 23, -12), Vector3(1.0, 1.0, 16), steel)
		_box(_set, Vector3(cx + 10, 24.5, -16), Vector3(0.4, 0.4, 0.4), _glow(Color(1, 0.1, 0.1), 5.0))
	for i in int(L / 15.0):
		var cr := _scene("crate")
		cr.position = Vector3(rng.randf_range(0, L), 0, -3.4)
		_set.add_child(cr)


func _build_rooftops(e: BrawlEngine, rng: RandomNumberGenerator) -> void:
	var L := e.level.length + 30.0
	_strip(L, -0.1, 0, Vector3(0, 0.2, 7.5), Pbr.material("rock", Color(0.45, 0.45, 0.5), 0.6))
	var wall := Pbr.material("stone_bricks", Color(0.45, 0.4, 0.4), 0.8)
	_strip(L, 0.5, -3.8, Vector3(0, 1.0, 0.4), wall)  # parapet
	_strip(L, -10.0, 0, Vector3(0, 20.0, 8.0), wall)
	var x := 0.0
	while x < L:
		var n := _scene("water_tank" if rng.randf() < 0.4 else "ac_unit")
		n.position = Vector3(x, 0, -3.0)
		_set.add_child(n)
		x += rng.randf_range(6.0, 12.0)
	for i in 50:  # the skyline: towers with lit windows and red aircraft lights
		var tx := rng.randf_range(-20, L + 20)
		var th := rng.randf_range(10, 45)
		var tz := rng.randf_range(-40, -18)
		var tw := rng.randf_range(4, 9)
		_box(_set, Vector3(tx, th * 0.5 - 12, tz), Vector3(tw, th, tw), _glow(Color(0.07, 0.07, 0.13), 0.0))
		for k in rng.randi_range(3, 10):
			_box(_set, Vector3(tx + rng.randf_range(-tw * 0.4, tw * 0.4), rng.randf_range(-10, th - 13), tz + tw * 0.5 + 0.05),
				Vector3(0.6, 0.8, 0.05), _glow(NEON[rng.randi_range(0, NEON.size() - 1)].lerp(Color(1, 0.85, 0.6), 0.6), 1.2))
		_box(_set, Vector3(tx, th - 12 + 0.3, tz), Vector3(0.3, 0.3, 0.3), _glow(Color(1, 0.1, 0.1), 6.0))
	# the city's glow on the horizon, and a neon rig every few metres along the roof
	var haze := _box(_set, Vector3(L * 0.5, -2.0, -48), Vector3(L + 120, 16, 0.2), _glow(Color(0.5, 0.2, 0.45), 0.5))
	haze.material_override.albedo_color = Color(0, 0, 0)
	_box(_set, Vector3(L * 0.5, 22, -60), Vector3(3.0, 3.0, 0.2), _glow(Color(0.9, 0.92, 1.0), 2.5)).rotation.z = PI * 0.25  # moon glint
	var lx := 0.0
	var k := 0
	while lx < L:
		var c := NEON[k % NEON.size()]
		_box(_set, Vector3(lx, 1.6, -3.7), Vector3(2.2, 0.12, 0.12), _glow(c, 4.0))  # a neon tube on the parapet
		_light(_set, Vector3(lx, 2.6, -1.8), c, 2.2, 11.0)
		_light(_set, Vector3(lx + 5.0, 5.0, 3.0), Color(0.55, 0.6, 1.0), 1.2, 12.0)  # moonlit fill
		lx += 10.0
		k += 1


# ------------------------------------------------------------------ fighters and items

func _fighter_node(f: Dictionary) -> Dictionary:
	var name: String = "hero_a" if f["player"] == 0 else ("hero_b" if f["player"] == 1 else MODEL.get(f["kind"], "thug"))
	var n := _scene(name)
	_set.add_child(n)
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	for a in ap.get_animation_list():
		ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "walk", "grab", "held"] else Animation.LOOP_NONE
	var skel: Skeleton3D = n.find_child("Skeleton3D", true, false)
	var slot: BoneAttachment3D = null
	if skel:
		slot = BoneAttachment3D.new()
		slot.bone_name = "forearm.R"
		skel.add_child(slot)
	return {"node": n, "anim": ap, "slot": slot, "weapon": "", "wnode": null, "last": ""}


func _set_weapon(d: Dictionary, kind: String) -> void:
	if d["weapon"] == kind:
		return
	if d["wnode"]:
		d["wnode"].queue_free()
		d["wnode"] = null
	d["weapon"] = kind
	if kind != "" and d["slot"]:
		var w := _scene(kind)
		w.position = Vector3(0, 0.26, -0.02)  # in the hand, at the end of the forearm
		w.rotation.x = -PI * 0.5
		d["slot"].add_child(w)
		d["wnode"] = w


func _anim_for(f: Dictionary) -> String:
	match f["state"]:
		B.S.WALK: return "walk"
		B.S.JUMP: return "jump_kick" if f["attack"] == "jump_kick" else "jump"
		B.S.ATTACK:
			var a: String = f["attack"]
			return {"knife": "punch", "crate": "bat", "charge": "walk"}.get(a, a)
		B.S.HITSTUN: return "hit"
		B.S.DOWN: return "ko" if f["hp"] <= 0 else "down"
		B.S.GETUP: return "getup"
		B.S.GRABBED: return "held"
		B.S.GRABBING: return "grab"
		B.S.THROWN: return "thrown"
		B.S.DEAD: return "ko"
	return "idle"


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hit":
			_fx.hit(d["pos"] + Vector3(0, 0, 0.3), d["damage"] >= 14)
			_shake = 0.35 if d["damage"] >= 14 else 0.15
		"knockdown", "slam":
			_fx.dust(d["pos"] + Vector3(0, 0.1, 0))
			if kind == "slam":
				_shake = 0.6
		"ko":
			_fx.ko(d["pos"] + Vector3(0, 1.0, 0))
		"weapon_break":
			var f := e.by_id(d["id"])
			if not f.is_empty():
				_fx.splinters(f["pos"] + Vector3(f["facing"] * 0.8, 1.2, 0))


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	var e := game.engine
	if e == null or _set == null:
		return
	_time += delta
	var alive := {}
	for f in e.fighters:
		alive[f["id"]] = true
		if not _nodes.has(f["id"]):
			_nodes[f["id"]] = _fighter_node(f)
		var d: Dictionary = _nodes[f["id"]]
		var n: Node3D = d["node"]
		n.position = f["pos"]
		n.rotation.y = lerp_angle(n.rotation.y, PI * 0.5 * f["facing"], 1.0 - exp(-delta * 20.0))
		var a := _anim_for(f)
		var ap: AnimationPlayer = d["anim"]
		if a != d["last"] or (f["state"] == B.S.ATTACK and f["t"] < 0.02):
			ap.play(a, 0.06, 1.3 if f["state"] == B.S.ATTACK else 1.0)
			d["last"] = a
		_set_weapon(d, f["weapon"])
		# the fallen fade away; blinking while invulnerable
		n.visible = f["state"] != B.S.DEAD or ap.is_playing() or fmod(_time, 0.2) < 0.1
		if f["state"] == B.S.DEAD and not ap.is_playing():
			n.scale = n.scale.lerp(Vector3(1, 0.01, 1), delta * 2.0)
		if f["invuln"] > 0.0:
			n.visible = fmod(_time, 0.12) < 0.07
	# items on the ground
	var seen := {}
	for it in e.items:
		seen[it["id"]] = true
		if not _items.has(it["id"]):
			var n := _scene(it["kind"])
			n.position = it["pos"] + Vector3(0, 0.05, 0)
			n.rotation = Vector3(PI * 0.5 if it["kind"] != "crate" else 0.0, randf() * TAU, 0)
			_set.add_child(n)
			_items[it["id"]] = n
	for id in _items.keys():
		if not seen.has(id):
			_items[id].queue_free()
			_items.erase(id)
	_place_camera(delta, e)


func _place_camera(delta: float, e: BrawlEngine) -> void:
	_cam_x = lerpf(_cam_x, e.scroll + e.view_width * 0.5, 1.0 - exp(-delta * 4.0))
	_shake = maxf(0.0, _shake - delta * 3.0)
	var s := _shake * _shake * (0.25 if Settings.camera_shake else 0.0)
	var j := Vector3(sin(_time * 70.0), sin(_time * 61.0), 0) * s
	_camera.position = Vector3(_cam_x, 3.4, 10.5) + j
	_camera.look_at(Vector3(_cam_x, 1.1, -0.3) + j)
