class_name BloomView3D
extends Node3D
## Bloomwand in 3D: the level's blocks and ladders on a fairy-tale stage (a garden, a mushroom ring, a crystal grotto,
## a castle in the clouds, a winter hollow, a thorn tower), each level's backdrop behind it. Fairies wear their
## player's colour; the wand throws a sparkling beam; a caught creature swings in an arc over the fairy's head and is
## slammed down in front and behind with a thud of dust; creatures burst into petals and leave fruit or a letter
## bubble; flowers sway and pop open; magic ladders are rainbows that fade when left. World: x right, y up, a tile a
## unit (x 0..20, y 0..15), the play plane at z = 0.

const B = preload("res://games/bloomwand/engine/bloom_engine.gd")
const M := "res://games/bloomwand/art/models/"
const BACKDROP := "res://games/bloomwand/view3d/bloom_backdrop.gd"
const TURN := 0.42                ## characters turn this far towards the camera
const KINDS := {"g": "grub", "b": "bopper", "s": "snapper", "c": "cloudlet"}
const DRESS := [Color(1.0, 0.45, 0.7), Color(0.25, 0.8, 0.8)]
const PETALS := [Color(1.0, 0.4, 0.55), Color(1.0, 0.85, 0.3), Color(0.6, 0.5, 1.0), Color(1.0, 0.6, 0.25), Color(0.95, 0.95, 1.0)]

@export var game: BloomGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _stage: Node3D
var _backdrop: Node3D
var _fairies: Array = []          ## {node, anim, last}
var _foes := {}                   ## id -> {node, anim, last}
var _flowers := {}                ## Vector2 -> node
var _items := {}                  ## item dictionary hash -> node
var _magic: Array[Node3D] = []
var _beams: Array = []
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO


func _ready() -> void:
	_we = WorldEnvironment.new()
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 80.0
	add_child(_sun)
	var key := DirectionalLight3D.new()   # a soft front light on the play pieces only
	key.rotation_degrees = Vector3(-25, 15, 0)
	key.light_energy = 0.6
	key.light_cull_mask = 2
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 36
	camera.far = 3000.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 22.0
	add_child(_fx)
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


func _play(ap: AnimationPlayer, anim: String, loop := true, blend := 0.1) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, blend)


func _play_layer(n: Node) -> void:
	for v in n.find_children("*", "VisualInstance3D", true, false):
		(v as VisualInstance3D).layers |= 2


## Recolours the surfaces whose material name contains `key`.
func _tint(n: Node, key: String, col: Color, rough := 0.45) -> void:
	var m := _mat(col, rough)
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var mm := mi as MeshInstance3D
		for k in mm.mesh.get_surface_count():
			var sm := mm.mesh.surface_get_material(k)
			if sm and sm.resource_name.contains(key):
				mm.set_surface_override_material(k, m)


# ------------------------------------------------------------------ a level

func _on_level(e: BloomEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_fairies.clear()
	_foes.clear()
	_flowers.clear()
	_items.clear()
	_magic.clear()
	_beams.clear()
	var th := e.lv.theme
	var block_kind := "block"
	var block_tint := Color.WHITE
	_backdrop = null
	if ResourceLoader.exists(BACKDROP):
		_backdrop = (load(BACKDROP) as GDScript).new()
		_stage.add_child(_backdrop)
		_backdrop.call("build", th)
		var d: Dictionary = _backdrop.call("environment_for", th)
		_env = _backdrop.call("make_environment", d)
		_backdrop.call("setup_sun", _sun, d)
		block_kind = {"stone": "block", "wood": "block_b", "crystal": "block_c"}.get(d.get("blocks", "stone"), "block")
		block_tint = d.get("tint", Color.WHITE)
	else:
		_env = Environment.new()
		_env.background_mode = Environment.BG_COLOR
		_env.background_color = [Color(0.55, 0.75, 0.95), Color(0.25, 0.2, 0.4), Color(0.1, 0.12, 0.2), Color(0.95, 0.65, 0.5), Color(0.1, 0.15, 0.3), Color(0.2, 0.15, 0.25)][th % 6]
		_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		_env.ambient_light_color = Color(0.7, 0.7, 0.85)
		_env.ambient_light_energy = 0.6
		_env.tonemap_mode = Environment.TONE_MAPPER_ACES
		_env.glow_enabled = true
		_sun.rotation_degrees = Vector3(-45, -25, 0)
		_sun.light_energy = 1.1
	_we.environment = _env
	# blocks and ladders
	for row in BloomLevel.H:
		for x in BloomLevel.W:
			var ch := e.lv.at(x, row)
			var y := BloomLevel.H - 1 - row
			if ch == "#":
				var b := _scene(block_kind)
				if b == null:
					b = MeshInstance3D.new()
					var bm := BoxMesh.new()
					bm.size = Vector3(1, 1, 1)
					(b as MeshInstance3D).mesh = bm
					(b as MeshInstance3D).material_override = _mat(Color(0.6, 0.55, 0.5), 0.8)
					b.position.y = 0.5
				var holder := Node3D.new()
				holder.position = Vector3(x + 0.5, y, 0)
				holder.add_child(b)
				if block_tint != Color.WHITE:
					for mi in b.find_children("*", "MeshInstance3D", true, false):
						(mi as GeometryInstance3D).set_instance_shader_parameter("tint", block_tint)
				_stage.add_child(holder)
			elif ch == "H":
				var l := _scene("ladder")
				if l == null:
					l = MeshInstance3D.new()
					var lm := BoxMesh.new()
					lm.size = Vector3(0.7, 1.0, 0.08)
					(l as MeshInstance3D).mesh = lm
					(l as MeshInstance3D).material_override = _mat(Color(0.55, 0.38, 0.2), 0.7)
					l.position.y = 0.5
				var holder := Node3D.new()
				holder.position = Vector3(x + 0.5, y, 0.1)
				holder.add_child(l)
				_stage.add_child(holder)
	# flowers
	var k := 0
	for fl in e.flowers:
		var n := _scene("flower")
		if n == null:
			n = MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = 0.18
			sm.height = 0.36
			(n as MeshInstance3D).mesh = sm
		_tint(n, "flower_petal", PETALS[k % PETALS.size()], 0.35)
		n.position = Vector3(fl.x, fl.y - 0.3, 0.1)
		n.rotation.y = randf_range(-0.4, 0.4)
		_play_layer(n)
		_stage.add_child(n)
		_flowers[fl] = n
		k += 1
	# fairies
	for f in e.fairies:
		var n := _scene("fairy")
		if n == null:
			n = Node3D.new()
			var b := MeshInstance3D.new()
			var cap := CapsuleMesh.new()
			cap.radius = 0.22
			cap.height = 0.85
			b.mesh = cap
			b.material_override = _mat(DRESS[f["i"]], 0.4)
			b.position.y = 0.45
			n.add_child(b)
		else:
			_tint(n, "fairy_dress", DRESS[f["i"] % 2], 0.4)
		var glow := OmniLight3D.new()
		glow.light_color = DRESS[f["i"] % 2].lightened(0.4)
		glow.light_energy = 0.8
		glow.omni_range = 2.0
		glow.position = Vector3(0, 0.7, 0.5)
		n.add_child(glow)
		_play_layer(n)
		_stage.add_child(n)
		_fairies.append({"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""})
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"cast":
			var f := e.fairies[d["p"]]
			var p: Vector3 = Vector3(f["pos"].x, f["pos"].y + 0.55, 0.3)
			var beam := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(B.REACH, 0.12, 0.05)
			beam.mesh = bm
			var col: Color = DRESS[d["p"] % 2].lightened(0.5)
			var m := _mat(col, 0.3, 0.0, 4.0)
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			beam.material_override = m
			beam.position = p + Vector3(f["face"] * B.REACH * 0.5, 0, 0)
			_stage.add_child(beam)
			_beams.append([beam, 0.25, m])
			_fx.burst(p + Vector3(f["face"] * 0.5, 0, 0), col, 14, 3.0, 0.4, 0.06, 1.0, 0.0, 1.0, "glow")
		"catch":
			var c := _foe_at(d["id"])
			if not c.is_empty():
				_fx.burst(_v(c["pos"]) + Vector3(0, 0.4, 0.3), Color(1.0, 0.9, 0.6), 24, 2.5, 0.5, 0.07, 1.0, 0.0, 1.0, "glow")
		"slam":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y + 0.1, 0.3), Color(0.85, 0.8, 0.7), 18, 3.0, 0.5, 0.18, 0.0, -2.0, 0.6, "smoke")
			_fx.burst(Vector3(p.x, p.y + 0.3, 0.3), Color(1.0, 0.95, 0.6), 10, 4.0, 0.3, 0.06, 1.0, -6.0, 1.0, "glow")
			_shake = maxf(_shake, 0.25)
		"pop":
			var at := _v(d["pos"]) + Vector3(0, 0.45, 0.3)
			for k in 3:
				_fx.burst(at, PETALS[(k + int(d["id"])) % PETALS.size()], 20, 4.0, 0.9, 0.08, 1.0, -3.0, 1.0, "glow")
			_fx.flash(at, Color(1.0, 0.85, 0.9), 2.5)
			if _backdrop and _backdrop.has_method("flash"):
				_backdrop.call("flash", at)
			_punch = 0.5
			_punch_at = at
		"flower":
			var fl: Vector2 = d["pos"]
			var n: Node3D = _flowers.get(fl)
			if n:
				_fx.burst(n.position + Vector3(0, 0.4, 0.3), Color(1.0, 0.7, 0.85), 18, 2.5, 0.7, 0.06, 1.0, -2.0, 1.0, "glow")
				var tw := create_tween()
				tw.tween_property(n, "scale", Vector3.ONE * 1.5, 0.12)
				tw.tween_property(n, "scale", Vector3.ZERO, 0.2)
				tw.tween_callback(n.queue_free)
				_flowers.erase(fl)
		"bloom":
			for k in 12:
				_fx.burst(Vector3(randf_range(1, 19), randf_range(2, 14), 0.5), PETALS[k % PETALS.size()], 12, 2.0, 1.0, 0.07, 1.0, -1.0, 1.0, "glow")
		"die":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y + 0.5, 0.3), Color(1.0, 1.0, 0.8), 30, 3.0, 0.8, 0.07, 1.0, -2.0, 1.0, "glow")
			_shake = 0.5
		"cleared":
			if _backdrop and _backdrop.has_method("celebrate"):
				_backdrop.call("celebrate")
		"ladder":
			for y in range(int(d["from"]), int(d["to"])):
				var n := _scene("magic_ladder")
				if n == null:
					n = MeshInstance3D.new()
					var lm := BoxMesh.new()
					lm.size = Vector3(0.7, 1.0, 0.05)
					(n as MeshInstance3D).mesh = lm
					var mm := _mat(Color(0.8, 0.6, 1.0, 0.7), 0.2, 0.0, 2.0)
					mm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					(n as MeshInstance3D).material_override = mm
					n.position.y = 0.5
				var holder := Node3D.new()
				holder.position = Vector3(int(d["x"]) + 0.5, y, 0.15)
				holder.scale = Vector3(1, 0.01, 1)
				holder.add_child(n)
				holder.set_meta("x", int(d["x"]))
				holder.set_meta("y", y)
				_stage.add_child(holder)
				_magic.append(holder)
				create_tween().tween_property(holder, "scale", Vector3.ONE, 0.25).set_delay((y - int(d["from"])) * 0.05)
			_fx.burst(Vector3(int(d["x"]) + 0.5, d["from"] + 0.5, 0.4), Color(0.8, 0.7, 1.0), 20, 2.0, 0.6, 0.07, 1.0, 2.0, 1.0, "glow")


func _v(p: Vector2) -> Vector3:
	return Vector3(p.x, p.y, 0.0)


func _foe_at(id: int) -> Dictionary:
	for c in game.engine.foes:
		if c["id"] == id:
			return c
	return {}


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 1.8)
	_punch = maxf(0.0, _punch - delta)
	var e := game.engine
	if e == null or _stage == null or _fairies.size() != e.fairies.size():
		return
	for i in e.fairies.size():
		_place_fairy(e, i, delta)
	_place_foes(e, delta)
	_place_items(e)
	_place_magic(e, delta)
	for fl in _flowers:
		var n: Node3D = _flowers[fl]
		n.rotation.z = sin(_time * 1.6 + fl.x) * 0.08
	for b in _beams:
		b[1] -= delta
		(b[2] as StandardMaterial3D).albedo_color.a = clampf(b[1] / 0.25, 0.0, 1.0)
	for b in _beams.filter(func(b): return b[1] <= 0.0):
		(b[0] as Node).queue_free()
	_beams = _beams.filter(func(b): return b[1] > 0.0)
	_place_camera(delta)


func _place_fairy(e: BloomEngine, i: int, delta: float) -> void:
	var f := e.fairies[i]
	var rec: Dictionary = _fairies[i]
	var n: Node3D = rec["node"]
	n.position = _v(f["pos"])
	var turn := -TURN if f["face"] > 0 else PI + TURN   # a three-quarter turn to the camera
	n.rotation.y = lerp_angle(n.rotation.y, turn, minf(1.0, delta * 12.0))
	n.visible = not f["dead"] or fmod(_time, 0.2) < 0.1
	if f["safe"] > 0.0 and not f["dead"]:
		n.visible = fmod(_time, 0.16) < 0.11
	var want: String = f["anim"]
	if f["dead"]:
		want = "die"
	elif e.phase == B.Phase.CLEARED:
		want = "cheer"
	elif f["holding"] >= 0:
		want = "hold"
	if want != rec["last"]:
		rec["last"] = want
		_play(rec["anim"], want, want != "die")


func _place_foes(e: BloomEngine, delta: float) -> void:
	for c in e.foes:
		var id: int = c["id"]
		if not _foes.has(id):
			var n := _scene(KINDS[c["kind"]])
			if n == null:
				n = MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = 0.35
				sm.height = 0.7
				(n as MeshInstance3D).mesh = sm
				(n as MeshInstance3D).material_override = _mat({"g": Color(0.5, 0.85, 0.3), "b": Color(0.9, 0.4, 0.3), "s": Color(0.3, 0.7, 0.4), "c": Color(0.6, 0.6, 0.75)}[c["kind"]], 0.5)
				n.position.y = 0.35
				var h := Node3D.new()
				h.add_child(n)
				n = h
			_play_layer(n)
			_stage.add_child(n)
			_foes[id] = {"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""}
		var rec: Dictionary = _foes[id]
		var n: Node3D = rec["node"]
		if c["dead"]:
			n.visible = false
			continue
		var p := _v(c["pos"])
		var want := "float" if c["kind"] == "c" else ("climb" if c["climb"] != 0 else "walk")
		if c["held_by"] >= 0:
			# swung over the fairy's head between slams
			var f := e.fairies[c["held_by"]]
			var k: float = clampf(f["slam_t"] / B.SLAM_EVERY, 0.0, 1.0)
			var a := lerpf(float(f["side"]) * 1.45, -float(f["side"]) * 1.45, k * k * (3.0 - 2.0 * k))
			var piv := _v(f["pos"]) + Vector3(0, 0.6, 0.25)
			p = piv + Vector3(sin(a), cos(a), 0) * 1.05 - Vector3(0, 0.35, 0)
			n.rotation.z = -a
			want = "caught"
		else:
			n.rotation.z = lerpf(n.rotation.z, 0.0, minf(1.0, delta * 10.0))
			n.rotation.y = lerp_angle(n.rotation.y, -TURN if c["dir"] > 0 else PI + TURN, minf(1.0, delta * 10.0))
		if c["stun"] > 0.0:
			n.rotation.z = sin(_time * 30.0) * 0.15
		n.position = p
		if want != rec["last"]:
			rec["last"] = want
			_play(rec["anim"], want, true)


func _place_items(e: BloomEngine) -> void:
	var live := {}
	for it in e.items:
		var key := int(it.get("vid", 0))
		if key == 0:
			it["vid"] = randi() % 1000000 + 1
			key = it["vid"]
		live[key] = true
		if not _items.has(key):
			var kind: String = it["kind"]
			var n: Node3D
			if kind.length() == 1:
				n = _scene("letter_bubble")
				if n == null:
					n = MeshInstance3D.new()
					var sm := SphereMesh.new()
					sm.radius = 0.3
					sm.height = 0.6
					(n as MeshInstance3D).mesh = sm
					var bm := _mat(Color(0.7, 0.9, 1.0, 0.4), 0.05)
					bm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					(n as MeshInstance3D).material_override = bm
				var lab := Label3D.new()
				lab.text = kind
				lab.font = HudKit.font(true)
				lab.font_size = 64
				lab.pixel_size = 0.006
				lab.outline_size = 10
				lab.modulate = Color(1.0, 0.85, 0.3)
				lab.position = Vector3(0, 0.3, 0.32)
				n.add_child(lab)
			else:
				n = _scene("fruit_" + kind if kind in ["cherry", "pear", "grapes"] else kind)
				if n == null:
					n = MeshInstance3D.new()
					var sm := SphereMesh.new()
					sm.radius = 0.2
					sm.height = 0.4
					(n as MeshInstance3D).mesh = sm
					(n as MeshInstance3D).material_override = _mat(Color(1.0, 0.3, 0.3), 0.3)
			_play_layer(n)
			_stage.add_child(n)
			_items[key] = n
		var node: Node3D = _items[key]
		node.position = _v(it["pos"]) + Vector3(0, -0.3, 0.1)
		node.rotation.y = _time * 1.5
	for key in _items.keys():
		if not live.has(key):
			var node: Node3D = _items[key]
			_fx.burst(node.position + Vector3(0, 0.3, 0.3), Color(1.0, 0.9, 0.5), 16, 2.5, 0.5, 0.06, 1.0, -2.0, 1.0, "glow")
			node.queue_free()
			_items.erase(key)


func _place_magic(e: BloomEngine, _delta: float) -> void:
	for h in _magic.duplicate():
		var alive := false
		for m in e.magic:
			if int(m["x"]) == int(h.get_meta("x")) and float(h.get_meta("y")) >= float(m["y0"]) - 0.01 and float(h.get_meta("y")) < float(m["y1"]):
				alive = true
				for g in h.find_children("*", "GeometryInstance3D", true, false):
					(g as GeometryInstance3D).transparency = clampf(1.0 - float(m["life"]) / 2.5, 0.0, 0.9) if m["life"] < 2.5 else 0.0
		if not alive:
			h.queue_free()
			_magic.erase(h)


func _place_camera(delta: float, snap := false) -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_v := tan(deg_to_rad(camera.fov * 0.5))
	var dist := maxf(8.4 / half_v, 11.2 / (half_v * aspect))
	var look := Vector3(10.0, 7.4, 0.0)
	var pos := look + Vector3(sin(_time * 0.1) * 0.6, 0.9 + sin(_time * 0.08) * 0.3, dist)
	if _punch > 0.0:
		var k := sin(_punch / 0.5 * PI) * 0.1
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + Vector3(0, 0, dist * 0.7), k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.18 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
