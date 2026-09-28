class_name DeepView3D
extends Node3D
## Deep Breath in 3D: a mining diorama seen from the side. Each cavern is dark, lit by the miner's helmet lamp, the
## lanterns on the timber shoring and the glowing keys; the theme dresses the back (crystal veins, pipes, mushrooms,
## cogs, icicles). The camera follows the miner, leans into his jumps, punches in on a key, pulls back when the lift
## opens, and shakes when he falls. Tile (x, y) is world ((x - 16) / 2, (8 - y) / 2), y up.

const E = preload("res://games/deepbreath/engine/deep_engine.gd")
const M := "res://games/deepbreath/art/models/"
const T := 0.5
const MINER_SCALE := 0.53  ## the model is 1.70 tall: 0.9 units is the 1.8 tiles of the rules
const WALK_STRIDE := 1.33 * MINER_SCALE / 0.533  ## units a second the walk cycle covers at speed 1
## per theme: ambient colour, lantern colour, backdrop tint, props to dress the back with, hazard model, rock tint
const THEMES := [
	{"name": "mine", "amb": Color(0.35, 0.3, 0.26), "lamp": Color(1.0, 0.72, 0.4), "back": Color(0.22, 0.16, 0.12),
		"props": ["bg_timber_frame", "bg_lantern"], "hazard": "hazard_plant", "rock": Color(0.62, 0.5, 0.4)},
	{"name": "crystal", "amb": Color(0.3, 0.32, 0.45), "lamp": Color(0.6, 0.8, 1.0), "back": Color(0.12, 0.14, 0.25),
		"props": ["bg_crystal_vein", "bg_lantern", "bg_crystal_vein"], "hazard": "hazard_spikes", "rock": Color(0.5, 0.52, 0.66)},
	{"name": "boiler", "amb": Color(0.4, 0.28, 0.2), "lamp": Color(1.0, 0.55, 0.25), "back": Color(0.25, 0.13, 0.08),
		"props": ["bg_pipe", "bg_lantern", "bg_pipe"], "hazard": "hazard_steam", "rock": Color(0.6, 0.42, 0.32)},
	{"name": "fungus", "amb": Color(0.3, 0.38, 0.3), "lamp": Color(0.6, 1.0, 0.6), "back": Color(0.1, 0.2, 0.12),
		"props": ["bg_mushroom", "bg_lantern", "bg_mushroom"], "hazard": "hazard_plant", "rock": Color(0.45, 0.55, 0.42)},
	{"name": "clockwork", "amb": Color(0.38, 0.34, 0.28), "lamp": Color(1.0, 0.85, 0.5), "back": Color(0.2, 0.17, 0.12),
		"props": ["bg_cog", "bg_lantern", "bg_timber_frame"], "hazard": "hazard_spikes", "rock": Color(0.58, 0.52, 0.42)},
	{"name": "frozen", "amb": Color(0.35, 0.42, 0.55), "lamp": Color(0.75, 0.9, 1.0), "back": Color(0.12, 0.18, 0.28),
		"props": ["bg_icicles", "bg_lantern"], "hazard": "hazard_spikes", "rock": Color(0.7, 0.78, 0.9)},
]
const GUARD_MODEL := {"minecart": "guardian_minecart", "drill": "guardian_drill", "bat": "guardian_bat", "crab": "guardian_crab",
	"gear": "guardian_gear", "snowball": "guardian_snowball"}

@export var game: DeepGame

var camera: Camera3D
var _env: Environment
var _stage: Node3D
var _miner: Node3D
var _miner_anim: AnimationPlayer
var _miner_last := ""
var _lamp: SpotLight3D
var _keys := {}
var _crumbles := {}
var _belts: Array[Node3D] = []
var _belt_mats := {}
var _guards: Array[Dictionary] = []
var _portal: Node3D
var _portal_light: OmniLight3D
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _punch := 0.0          ## a brief zoom towards a key just taken
var _punch_at := Vector3.ZERO
var _pull := 0.0           ## a pull-back when the lift opens
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _mats := {}


static func world(p: Vector2, z := 0.0) -> Vector3:
	return Vector3((p.x - 16.0) * T, (8.0 - p.y) * T, z)


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.01, 0.01, 0.015)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_energy = 0.28
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.9
	_env.glow_bloom = 0.08
	_env.glow_hdr_threshold = 0.9
	_env.ssao_enabled = true
	_env.fog_enabled = true
	_env.fog_density = 0.02
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var key := DirectionalLight3D.new()  # a faint shaft of daylight from far above
	key.rotation_degrees = Vector3(-60, -25, 0)
	key.light_energy = 0.25
	key.shadow_enabled = true
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 34
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String, size := Vector3(0.45, 0.45, 0.45), col := Color(0.5, 0.45, 0.4)) -> Node3D:
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


func _multi(name: String, xforms: Array[Transform3D], tint := Color(-1, 0, 0)) -> void:
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
	if tint.r >= 0.0:
		var veil := StandardMaterial3D.new()
		veil.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		veil.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		veil.blend_mode = BaseMaterial3D.BLEND_MODE_MUL
		veil.albedo_color = tint
		mmi.material_overlay = veil
	_stage.add_child(mmi)


func _play(ap: AnimationPlayer, anim: String, loop := false) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, 0.1)


func _on_level(e: DeepEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_keys.clear()
	_crumbles.clear()
	_belts.clear()
	_guards.clear()
	var lv := e.level
	var th: Dictionary = THEMES[lv.theme % THEMES.size()]
	_env.ambient_light_color = th["amb"]
	_env.fog_light_color = th["back"] * 0.4
	# the rock and the floors
	var rock := {"a": [] as Array[Transform3D], "b": [] as Array[Transform3D], "c": [] as Array[Transform3D]}
	var floors: Array[Transform3D] = []
	for y in DeepLevel.H:
		for x in DeepLevel.W:
			var c := Vector3((x + 0.5 - 16.0) * T, (8.0 - y - 0.5) * T, 0)
			match lv.at(x, y):
				"#": rock["c" if (x * 7 + y * 13) % 17 == 3 else ["a", "b"][(x * 5 + y * 3) % 2]].append(Transform3D(Basis(), c))  # a crystal vein now and then
				"=": floors.append(Transform3D(Basis(), c))
				"~":
					var n := _scene("tile_crumble", Vector3(0.5, 0.2, 0.5), Color(0.6, 0.45, 0.3))
					n.position = c
					_stage.add_child(n)
					_crumbles[Vector2i(x, y)] = n
				"<", ">":
					var n := _scene("tile_conveyor", Vector3(0.5, 0.2, 0.5), Color(0.3, 0.3, 0.32))
					n.position = c
					var dir := -1.0 if lv.at(x, y) == "<" else 1.0
					n.set_meta("dir", dir)
					var belt := n.find_child("belt", true, false) as MeshInstance3D
					if belt and belt.mesh:
						if not _belt_mats.has(dir):
							var bm := belt.mesh.surface_get_material(0).duplicate() as BaseMaterial3D
							if bm:
								bm.texture_repeat = true
							_belt_mats[dir] = bm
						belt.material_override = _belt_mats[dir]
					_stage.add_child(n)
					_belts.append(n)
	for k in rock:
		_multi("tile_rock_" + k, rock[k])
	_multi("tile_floor", floors)
	var panels: Array[Transform3D] = []
	for px in [-6.0, -2.0, 2.0, 6.0]:
		for py in [-4.0, 0.0]:
			panels.append(Transform3D(Basis(), Vector3(px, py, -2.0)))
	_multi("bg_rockwall", panels, th["back"] * 3.0)
	# hazards
	for h in lv.hazards:
		var n := _scene(th["hazard"], Vector3(0.4, 0.4, 0.3), Color(0.6, 1.0, 0.4))
		n.position = world(Vector2(h) + Vector2(0.5, 0.5), 0.0)
		_stage.add_child(n)
		var hap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		_play(hap, "sway", true)
		_play(hap, "puff", true)
	# keys glow, each with its own light
	for k in e.keys:
		var n := _scene("key", Vector3(0.2, 0.25, 0.1), Color(0.6, 1.0, 1.0))
		n.position = world(Vector2(k) + Vector2(0.5, 0.5), 0.1)
		_stage.add_child(n)
		var l := OmniLight3D.new()
		l.light_color = Color(0.55, 0.95, 1.0)
		l.light_energy = 0.9
		l.omni_range = 1.8
		n.add_child(l)
		_keys[k] = n
	# the lift
	_portal = _scene("portal", Vector3(1.0, 1.0, 0.4), Color(0.5, 0.4, 0.3))
	_portal.position = world(Vector2(lv.portal) + Vector2(1.0, 2.0), -0.05)
	_stage.add_child(_portal)
	_portal_light = OmniLight3D.new()
	_portal_light.light_color = Color(1.0, 0.3, 0.2)
	_portal_light.light_energy = 1.2
	_portal_light.omni_range = 2.5
	_portal_light.position = Vector3(0, 0.6, 0.6)
	_portal.add_child(_portal_light)
	# the dressing on the back wall: shoring, lanterns and the theme's pieces, spaced along the cavern
	var props: Array = th["props"]
	for i in 9:
		var kind: String = props[i % props.size()]
		var n := _scene(kind, Vector3(0.3, 1.0, 0.1), th["lamp"])
		var x := -7.2 + i * 1.8
		var yy: float = [-2.5, 0.5, -1.0][i % 3]
		n.position = Vector3(x, yy + (2.6 if kind in ["bg_lantern", "bg_icicles"] else 0.0), -1.0)
		_stage.add_child(n)
		_play(n.find_child("AnimationPlayer", true, false), "turn", true)
		if kind == "bg_lantern" or kind == "bg_crystal_vein":
			var l := OmniLight3D.new()
			l.light_color = th["lamp"]
			l.light_energy = 2.2
			l.omni_range = 3.6
			l.shadow_enabled = false
			l.position = Vector3(0, -0.33 if kind == "bg_lantern" else 0.6, 0.3)
			n.add_child(l)
	# guardians
	for g in e.guards:
		var n := _scene(GUARD_MODEL.get(g["kind"], "guardian_minecart"), Vector3(0.45, 0.6, 0.4), Color(0.7, 0.3, 0.3))
		_stage.add_child(n)
		_play(n.find_child("AnimationPlayer", true, false), "move", true)
		_guards.append({"node": n})
	# the miner, with the lamp on his helmet
	_miner = _scene("miner", Vector3(0.35, 0.9, 0.3), Color(0.8, 0.6, 0.3))
	_miner.scale = Vector3.ONE * MINER_SCALE
	_stage.add_child(_miner)
	_miner_anim = _miner.find_child("AnimationPlayer", true, false)
	_miner_last = ""
	_lamp = SpotLight3D.new()
	_lamp.light_color = Color(1.0, 0.9, 0.7)
	_lamp.light_energy = 4.0
	_lamp.spot_range = 7.0
	_lamp.spot_angle = 32.0
	_lamp.shadow_enabled = true
	_lamp.spot_angle = 40.0
	var mount := _miner.find_child("lamp", true, false) as Node3D
	if mount:
		mount.add_child(_lamp)  # the mount's -Z already points ahead of him, following his head
	else:
		_lamp.position = Vector3(0.2, 1.63, 0.11)
		_lamp.rotation = Vector3(0, -PI * 0.5, 0)
		_miner.add_child(_lamp)
	_lamp.rotation.x -= deg_to_rad(14.0)  # a pool of light on the floor ahead, not only the far wall
	var glow := OmniLight3D.new()  # a soft halo, so the miner is never lost in the dark
	glow.light_color = Color(1.0, 0.85, 0.6)
	glow.light_energy = 0.6
	glow.omni_range = 1.6
	glow.position = Vector3(0, 1.0, 0.6)
	_miner.add_child(glow)
	_cam_pos = Vector3.ZERO
	_place_camera(1.0, true)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"key":
			var c: Vector2i = d["cell"]
			if _keys.has(c):
				var p: Vector3 = _keys[c].position
				_fx.burst(p, Color(0.6, 1.0, 1.0), 26, 3.0, 0.7, 0.1, 1.0, -2.0, 1.0, "glow")
				_fx.flash(p + Vector3(0, -2.5, 0.8), Color(0.6, 1.0, 1.0), 2.5)
				_keys[c].queue_free()
				_keys.erase(c)
				_punch = 0.6
				_punch_at = p
		"open":
			_portal_light.light_color = Color(0.4, 1.0, 0.5)
			_portal_light.light_energy = 2.5
			_play(_portal.find_child("AnimationPlayer", true, false), "open")
			_fx.burst(_portal.position + Vector3(0, 0.5, 0.3), Color(0.5, 1.0, 0.6), 30, 3.0, 0.8, 0.1, 1.0, -1.0, 1.0, "glow")
			_pull = 1.6
		"crumble":
			var c: Vector2i = d["cell"]
			if _crumbles.has(c):
				var n: Node3D = _crumbles[c]
				_fx.burst(n.position, Color(0.55, 0.45, 0.35), 14, 1.5, 0.6, 0.07, 0.0, -8.0, 0.5)
				var tw := create_tween()
				tw.tween_property(n, "position:y", n.position.y - 0.6, 0.35).set_ease(Tween.EASE_IN)
				tw.parallel().tween_property(n, "scale", Vector3(1, 0.1, 1), 0.35)
				tw.tween_callback(n.queue_free)
				_crumbles.erase(c)
		"land":
			_fx.burst(world(e.hero["pos"], 0.2), Color(0.6, 0.55, 0.5), 8, 1.2, 0.4, 0.06, 0.0, -4.0, 0.5)
		"die":
			_play(_miner_anim, "die")
			_miner_last = "die"
			_fx.burst(world(d["pos"] + Vector2(0, -0.9), 0.3), Color(1.0, 0.8, 0.5), 24, 2.5, 0.6, 0.08, 1.0, -3.0, 1.0, "glow")
			_shake = 0.5
		"cleared":
			_play(_miner_anim, "cheer", true)
			_miner_last = "cheer"


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _miner == null:
		return
	var h := e.hero
	_miner.position = world(h["pos"], 0.15)
	_miner.scale = Vector3(MINER_SCALE * h["facing"], MINER_SCALE, MINER_SCALE)
	if e.phase == E.Phase.PLAY:
		var want := "idle"
		if h["state"] == "air":
			want = "jump" if h["vel"].y < 0.0 else "fall"
		elif absf(e.move_x) > 0.1 or absf(h["vel"].x) > 0.1:
			want = "walk"
		if e.air < 8.0 and want == "idle":
			want = "gasp"
		if want != _miner_last:
			_miner_last = want
			_play(_miner_anim, want, want != "jump")
		if _miner_anim:
			_miner_anim.speed_scale = (E.WALK * T / WALK_STRIDE) if want == "walk" else 1.0
	elif e.phase == E.Phase.READY and _miner_last in ["die", "cheer"]:
		_miner_last = ""
	# the lamp flickers a little, and dims as the air goes
	_lamp.light_energy = (3.0 + 1.0 * clampf(e.air / e.level.air, 0.0, 1.0)) * (0.95 + 0.05 * sin(_time * 23.0))
	# crumbling floor shakes while it is stood on
	for c in _crumbles:
		var t: float = e.crumble.get(c, 0.0)
		var n: Node3D = _crumbles[c]
		n.rotation.z = sin(_time * 60.0) * 0.06 * t / E.CRUMBLE_TIME
	for dir in _belt_mats:
		var bm := _belt_mats[dir] as BaseMaterial3D
		if bm:
			bm.uv1_offset.x = fmod(-_time * E.CONVEYOR * T * float(dir) / 0.5, 1.0)
	for b in _belts:
		for rn in ["roller_a", "roller_b"]:
			var roller := b.find_child(rn, true, false) as Node3D
			if roller:
				roller.rotation.z = -_time * E.CONVEYOR * T * float(b.get_meta("dir")) / 0.07
	for k in _keys:
		var n: Node3D = _keys[k]
		n.rotation.y = _time * 2.0
		n.position.y = world(Vector2(k) + Vector2(0.5, 0.5)).y + sin(_time * 3.0 + k.x) * 0.04
	for i in e.guards.size():
		var g: Dictionary = e.guards[i]
		var n: Node3D = _guards[i]["node"]
		n.position = world(g["pos"] - Vector2(0, 0.8 if g["kind"] == "bat" else 0.0), 0.1)
		if g["axis"] == "h":
			n.scale = Vector3(float(g["dir"]), 1, 1)
	_shake = maxf(0.0, _shake - delta * 1.5)
	_punch = maxf(0.0, _punch - delta)
	_pull = maxf(0.0, _pull - delta)
	_place_camera(delta)


## Frames the cavern, following the miner a little and leaning the way he moves; a punch-in towards a key just
## taken, a pull-back when the lift opens.
func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(DeepLevel.H * T * 0.5 + 0.9, (DeepLevel.W * T * 0.5 + 0.4) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var hp := world(e.hero["pos"], 0.0)
	var lean := Vector3(hp.x * 0.22 + float(e.hero["vel"].x) * 0.12, hp.y * 0.18, 0.0)
	var look := lean
	var pos := look + Vector3(hp.x * 0.08, 0.9, dist * 0.93)
	if _punch > 0.0:
		var k := sin(_punch / 0.6 * PI) * 0.35
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + Vector3(0, 0.3, dist * 0.6), k)
	if _pull > 0.0:
		pos += Vector3(0, 0.4, 1.8) * sin(_pull / 1.6 * PI)
	var j := Vector3(sin(_time * 50.0), cos(_time * 43.0), 0) * _shake * _shake * (0.35 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look + j, Vector3.UP)
