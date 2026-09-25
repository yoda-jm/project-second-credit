class_name WhiskerView3D
extends Node3D
## Whisker Alley in 3D, seen from the side (2.5D): the street in front, trash cans, the fence, the washing lines and
## the building behind, at night. Engine (x, y) maps to (x, y, depth); the cat moves between depth layers as it
## climbs. Each room is its own lit interior set, swapped in while the cat is inside.

const E = preload("res://games/whisker/engine/whisker_engine.gd")
const M := "res://games/whisker/art/models/"
const Z_STREET := 1.0
const Z_CAN := 0.55
const Z_FENCE := -0.2
const Z_LINE := -1.3
const Z_WALL := -2.6
const WASHING := ["shirt", "socks", "towel", "dress"]

@export var game: WhiskerGame

var _camera: Camera3D
var _env: Environment
var _moon: DirectionalLight3D
var _fx: WhiskerEffects
var _alley := Node3D.new()
var _room_set: Node3D
var _cat: Node3D
var _cat_anim: AnimationPlayer
var _dog: Node3D
var _dog_anim: AnimationPlayer
var _windows: Array[Dictionary] = []  ## {node, glow: MeshInstance3D, light: OmniLight3D, left: Node3D, right: Node3D, open: float}
var _washing: Array[Dictionary] = []  ## {node, line, x}
var _shoes := {}  ## index -> node (rebuilt each frame from the engine list)
var _shoe_pool: Array[Node3D] = []
var _room_things := {}  ## per-room entity nodes
var _sets := {}  ## room kind -> {node, things}, built once
var _warm := 0  ## frames drawn since the start (the prebuilt rooms hide after the first few)
var _cat_z := Z_STREET
var _time := 0.0
var _shake := 0.0
var _cam_alley := Transform3D()
var _cam_room := Transform3D()
var _cam_hearts := Transform3D()
var _catch_t := 0.0
var _land_t := 0.0


func _ready() -> void:
	_build_world()
	_fx = WhiskerEffects.new()
	add_child(_fx)
	add_child(_alley)
	_build_alley()
	_prebuild_rooms()
	game.started.connect(_on_started)
	if game.engine:
		_on_started(game.engine)


func _on_started(e: WhiskerEngine) -> void:
	if not e.event.is_connected(_on_event):
		e.event.connect(_on_event)
	_leave_room_set()


# ------------------------------------------------------------------ world

func _build_world() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.02, 0.03, 0.09)
	sky_mat.sky_horizon_color = Color(0.12, 0.13, 0.25)
	sky_mat.ground_horizon_color = Color(0.08, 0.08, 0.14)
	sky_mat.ground_bottom_color = Color(0.02, 0.02, 0.04)
	var sky := Sky.new()
	sky.sky_material = sky_mat
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.3, 0.35, 0.55)
	_env.ambient_light_energy = 0.55
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.05
	_env.glow_enabled = true
	_env.glow_intensity = 0.6
	_env.glow_bloom = 0.1
	_env.glow_hdr_threshold = 0.9
	_env.ssao_enabled = true
	_env.fog_enabled = true
	_env.fog_light_color = Color(0.15, 0.17, 0.3)
	_env.fog_density = 0.004
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.2
	_env.adjustment_contrast = 1.1
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	_moon = DirectionalLight3D.new()
	_moon.rotation_degrees = Vector3(-38, 28, 0)
	_moon.light_color = Color(0.65, 0.72, 1.0)
	_moon.light_energy = 0.55
	_moon.shadow_enabled = true
	_moon.shadow_bias = 0.05
	_moon.directional_shadow_max_distance = 60.0
	add_child(_moon)
	_camera = Camera3D.new()
	_camera.fov = 36
	_camera.current = true
	add_child(_camera)
	_cam_alley = _fit(Vector3(E.W * 0.5, E.H * 0.5 - 0.3, 0), Vector2(E.W + 1.0, E.H + 0.5), Vector3(0, 0.12, 1))
	_cam_room = _fit(Vector3(8.0, 4.3, 0), Vector2(16.5, 9.2), Vector3(0, 0.1, 1))
	_cam_hearts = _fit(Vector3(8.0, 6.8, 0), Vector2(16.5, 14.2), Vector3(0, 0.05, 1))
	_camera.transform = _cam_alley


## A camera transform looking at `center` along `dir` from the distance that fits `size` (width, height).
func _fit(center: Vector3, size: Vector2, dir: Vector3) -> Transform3D:
	var aspect := 16.0 / 9.0
	var half_h := maxf(size.y * 0.5, size.x * 0.5 / aspect) * 1.12  # room for the HUD
	var dist := half_h / tan(deg_to_rad(_camera.fov * 0.5))
	var t := Transform3D(Basis(), center + dir.normalized() * dist)
	return t.looking_at(center + Vector3(0, 0.4, 0))


func _scene(name: String) -> Node3D:
	var n: Node3D = (load(M + name + ".glb") as PackedScene).instantiate()
	_dress(n)
	return n


static func _dress(node: Node) -> void:
	var swap := {
		"wood": Pbr.local("planks", Color(0.75, 0.55, 0.38), 0.9),
		"metal": Pbr.local("metal", Color(0.6, 0.62, 0.66), 1.2, 0.8, 0.6),
	}
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and swap.has(mat.resource_name):
				m.set_surface_override_material(i, swap[mat.resource_name])


func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


func _build_alley() -> void:
	var cobbles := Pbr.material("stone_bricks", Color(0.45, 0.45, 0.5), 0.6)
	var brick := Pbr.material("stone_bricks", Color(0.75, 0.42, 0.33), 0.45)
	var dark_wall := Pbr.material("dark_rock", Color(0.3, 0.3, 0.36), 1.0)
	# street, building, the neighbours' walls and a skyline
	_box(_alley, Vector3(E.W * 0.5, -0.25, -1.0), Vector3(E.W + 30, 0.5, 9.0), cobbles)
	_box(_alley, Vector3(E.W * 0.5, E.H * 0.5 + 1.0, Z_WALL - 0.3), Vector3(E.W + 4, E.H + 2.0, 0.6), brick)
	_box(_alley, Vector3(-6.0, 5.0, Z_WALL + 1.0), Vector3(8, 10, 1), dark_wall)
	_box(_alley, Vector3(E.W + 6.0, 6.5, Z_WALL + 1.0), Vector3(8, 13, 1), dark_wall)
	var rng := RandomNumberGenerator.new()
	rng.seed = 44
	var sil := StandardMaterial3D.new()
	sil.albedo_color = Color(0.05, 0.05, 0.1)
	for i in 14:  # rooftops far behind, with a few lit windows
		var w := rng.randf_range(3.0, 6.0)
		var h := rng.randf_range(15.0, 22.0)
		var x := -12.0 + i * 4.2
		_box(_alley, Vector3(x, h * 0.5, -14.0), Vector3(w, h, 1.0), sil)
		for k in rng.randi_range(1, 4):
			var lit := StandardMaterial3D.new()
			lit.albedo_color = Color(1.0, 0.8, 0.45)
			lit.emission_enabled = true
			lit.emission = Color(1.0, 0.75, 0.4)
			lit.emission_energy_multiplier = rng.randf_range(0.6, 1.6)
			_box(_alley, Vector3(x + rng.randf_range(-w * 0.35, w * 0.35), rng.randf_range(4.0, h - 1.0), -13.4), Vector3(0.5, 0.7, 0.1), lit)
	var moon := MeshInstance3D.new()
	var ms := SphereMesh.new()
	ms.radius = 1.6
	ms.height = 3.2
	moon.mesh = ms
	var mm := StandardMaterial3D.new()
	mm.albedo_color = Color(0.95, 0.93, 0.8)
	mm.emission_enabled = true
	mm.emission = Color(1.0, 0.97, 0.85)
	mm.emission_energy_multiplier = 2.5
	moon.material_override = mm
	moon.position = Vector3(E.W - 3.0, E.H + 5.0, -20.0)
	_alley.add_child(moon)
	# fence panels
	for i in int(E.W / 2.0):
		var f := _scene("fence")
		f.position = Vector3(1.0 + i * 2.0, 0, Z_FENCE)
		_alley.add_child(f)
	# trash cans
	for x in E.CAN_X:
		var c := _scene("trash_can")
		c.position = Vector3(x, 0, Z_CAN)
		c.set_meta("x", x)
		_alley.add_child(c)
	# washing lines between two poles, with the washing that rides them
	var rope := StandardMaterial3D.new()
	rope.albedo_color = Color(0.85, 0.82, 0.75)
	for i in E.LINE_Y.size():
		var y: float = E.LINE_Y[i]
		var r := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.025
		cm.bottom_radius = 0.025
		cm.height = E.W + 1.0
		r.mesh = cm
		r.material_override = rope
		r.rotation.z = PI * 0.5
		r.position = Vector3(E.W * 0.5, y, Z_LINE)
		_alley.add_child(r)
		for k in 7:
			var n := _scene(WASHING[(i + k) % WASHING.size()])
			_alley.add_child(n)
			_washing.append({"node": n, "line": i, "x": k * (E.W / 7.0) + i * 1.3})
	for x in [-0.3, E.W + 0.3]:
		_box(_alley, Vector3(x, (E.LINE_Y[2] + 0.4) * 0.5, Z_LINE), Vector3(0.18, E.LINE_Y[2] + 0.4, 0.18), Pbr.material("planks", Color(0.5, 0.36, 0.24), 2.0))
	# windows with shutters, a dark room behind and a warm light when open
	for i in E.WINDOW_X.size() * E.WINDOW_Y.size():
		var col := i % E.WINDOW_X.size()
		var row := i / E.WINDOW_X.size()
		var base := Vector3(E.WINDOW_X[col], E.WINDOW_Y[row], Z_WALL)
		var node := _scene("window")
		node.position = base
		_alley.add_child(node)
		var glow := _box(_alley, base + Vector3(0, 0.75, -0.02), Vector3(1.6, 1.5, 0.05), _glow_mat())
		var left := _scene("shutter")
		left.position = base + Vector3(-0.8, 0, 0.05)
		_alley.add_child(left)
		var right := _scene("shutter")
		right.position = base + Vector3(0.8, 0, 0.05)
		right.rotation.y = PI
		_alley.add_child(right)
		var light := OmniLight3D.new()
		light.position = base + Vector3(0, 0.8, 0.8)
		light.light_color = Color(1.0, 0.75, 0.45)
		light.omni_range = 4.0
		light.light_energy = 0.0
		_alley.add_child(light)
		_windows.append({"glow": glow, "light": light, "left": left, "right": right, "open": 0.0})
	# street lamps
	for x in [5.2, 18.8]:
		var l := _scene("lamp")
		l.position = Vector3(x, 0, Z_STREET + 0.9)
		_alley.add_child(l)
		var ol := OmniLight3D.new()
		ol.position = Vector3(x, 3.9, Z_STREET + 0.2)
		ol.light_color = Color(1.0, 0.78, 0.5)
		ol.light_energy = 2.2
		ol.omni_range = 9.0
		ol.shadow_enabled = true
		_alley.add_child(ol)
	# the cat and the dog
	_cat = _scene("cat")
	_cat.scale = Vector3.ONE * 1.25
	add_child(_cat)
	_cat_anim = _cat.find_child("AnimationPlayer", true, false)
	_dog = _scene("bulldog")
	_dog.scale = Vector3.ONE * 1.3
	_alley.add_child(_dog)
	_dog_anim = _dog.find_child("AnimationPlayer", true, false)
	for p in [_cat_anim, _dog_anim]:
		for a in ["idle", "walk", "run", "swim", "fall"]:
			if p.has_animation(a):
				p.get_animation(a).loop_mode = Animation.LOOP_LINEAR
	for i in 6:
		var b := _scene("boot")
		b.visible = false
		b.scale = Vector3.ONE * 1.4
		_alley.add_child(b)
		_shoe_pool.append(b)


func _glow_mat() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.03, 0.03, 0.05)
	m.emission_enabled = true
	m.emission = Color(1.0, 0.72, 0.4)
	m.emission_energy_multiplier = 0.0
	return m


# ------------------------------------------------------------------ rooms

## Room sets are built once (from a template room of each kind) and reused: building one on the way in made the
## game stall. At start they are all drawn once behind the building, so their shaders compile during the loading
## screen, then hidden.
func _prebuild_rooms() -> void:
	var dummy := WhiskerEngine.new(1)
	for kind in 5:
		var r: WhiskerRoom = [FishbowlRoom, MiceRoom, BirdcageRoom, DogbowlsRoom, HeartsRoom][kind].new()
		r.kind = kind
		r.setup(dummy)
		var set := _build_room_set(r)
		set["node"].position = Vector3(0, 0, -60)  # behind the building: drawn (and compiled) but unseen
		_sets[kind] = set
		r.cleanup(dummy)


func _enter_room_set(e: WhiskerEngine) -> void:
	_leave_room_set()
	_alley.visible = false
	var r := e.room
	var set: Dictionary = _sets[r.kind]
	_room_set = set["node"]
	_room_things = set["things"]
	_room_set.position = Vector3.ZERO
	_room_set.visible = true
	_reset_room_things(r)
	_env.ambient_light_color = Color(0.55, 0.5, 0.45)
	_moon.visible = false


func _reset_room_things(r: WhiskerRoom) -> void:
	var t := _room_things
	match r.kind:
		E.RoomKind.FISHBOWL:
			var fr := r as FishbowlRoom
			for pool in ["fish", "eels"]:
				var need: int = fr.fish.size() if pool == "fish" else fr.eels.size()
				while t[pool].size() < need:
					var n := _scene("goldfish" if pool == "fish" else "eel")
					n.scale = Vector3.ONE * (1.6 if pool == "fish" else 1.3)
					_room_set.add_child(n)
					t[pool].append(n)
				for i in t[pool].size():
					t[pool][i].visible = i < need
		E.RoomKind.MICE:
			for n in t["mice"].values():
				n.queue_free()
			t["mice"].clear()
		E.RoomKind.BIRDCAGE:
			(t["chain"] as Node3D).visible = true
			(t["bird"] as Node3D).visible = true
		E.RoomKind.HEARTS:
			for a in t["arrows"]:
				a.visible = false
	(t["broom"] as Node3D).visible = false


func _build_room_set(r: WhiskerRoom) -> Dictionary:
	var saved_set := _room_set
	var saved_things := _room_things
	_room_set = Node3D.new()
	_room_things = {}
	add_child(_room_set)
	var wallpaper: Color = [Color(0.45, 0.62, 0.7), Color(0.75, 0.62, 0.45), Color(0.62, 0.5, 0.7),
		Color(0.55, 0.68, 0.5), Color(0.35, 0.18, 0.35)][r.kind]
	var paper := ShaderMaterial.new()
	paper.shader = load("res://games/whisker/shaders/wallpaper.gdshader")
	paper.set_shader_parameter("base", wallpaper)
	paper.set_shader_parameter("stripe", wallpaper.lightened(0.18))
	paper.set_shader_parameter("motif", wallpaper.darkened(0.3))
	_box(_room_set, Vector3(8, 7.0, -1.2), Vector3(18, 15, 0.3), paper)
	_box(_room_set, Vector3(8, -0.25, 0), Vector3(18, 0.5, 3.0), Pbr.material("planks", Color(0.7, 0.5, 0.35), 1.2))
	_box(_room_set, Vector3(8, 0.15, -1.0), Vector3(18, 0.3, 0.08), Pbr.material("planks", Color(0.9, 0.88, 0.8), 2.0))
	# the window the cat came in through, with the night outside
	var night := StandardMaterial3D.new()
	night.albedo_color = Color(0.05, 0.07, 0.18)
	night.emission_enabled = true
	night.emission = Color(0.08, 0.1, 0.25)
	_box(_room_set, Vector3(1.2, 6.3, -1.0), Vector3(1.8, 1.8, 0.05), night)
	var win := _scene("window")
	win.position = Vector3(1.2, 5.4, -0.95)
	_room_set.add_child(win)
	# furniture where the engine's platforms are
	for p in r.platforms:
		var k: String = p["kind"]
		if k in ["floor", "cheese", "heart", "top"]:
			continue
		var rect: Rect2 = p["rect"]
		if rect.position.y > 0.1:  # a floating shelf: a plank on two brackets
			_box(_room_set, Vector3(rect.get_center().x, rect.end.y - 0.12, -0.6), Vector3(rect.size.x, 0.24, 1.0), Pbr.material("planks", Color(0.75, 0.55, 0.38), 2.0))
			for sx in [-0.35, 0.35]:
				_box(_room_set, Vector3(rect.get_center().x + sx * rect.size.x, rect.end.y - 0.45, -1.0), Vector3(0.08, 0.5, 0.35), Pbr.material("metal", Color(0.3, 0.3, 0.32), 2.0, 0.8, 0.5))
			continue
		var name := k if ResourceLoader.exists(M + k + ".glb") else "cabinet"
		var n := _scene(name)
		n.position = Vector3(rect.get_center().x, 0, -0.2)
		var src := _natural_size(name)
		n.scale = Vector3(rect.size.x / src.x, rect.end.y / src.y, 1.0)
		_room_set.add_child(n)
	var lamp := OmniLight3D.new()
	lamp.position = Vector3(8, 7.5, 2.0)
	lamp.light_color = Color(1.0, 0.85, 0.65)
	lamp.light_energy = 2.5
	lamp.omni_range = 16.0
	lamp.shadow_enabled = r.kind != E.RoomKind.HEARTS  # the floating hearts would throw heavy blots on the wall
	_room_set.add_child(lamp)
	_room_things.clear()
	match r.kind:
		E.RoomKind.FISHBOWL:
			var bowl := _scene("bowl")
			bowl.position = Vector3(FishbowlRoom.BOWL.get_center().x, FishbowlRoom.BOWL.position.y, 0.0)
			_room_set.add_child(bowl)
			var water := MeshInstance3D.new()
			var wb := BoxMesh.new()
			wb.size = Vector3(FishbowlRoom.BOWL.size.x - 0.1, FishbowlRoom.BOWL.size.y - 0.3, 1.5)
			water.mesh = wb
			var wm := StandardMaterial3D.new()
			wm.albedo_color = Color(0.35, 0.6, 0.85, 0.28)
			wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			wm.roughness = 0.05
			wm.metallic_specular = 0.8
			water.material_override = wm
			water.position = Vector3(FishbowlRoom.BOWL.get_center().x, FishbowlRoom.BOWL.position.y + wb.size.y * 0.5 + 0.2, 0.0)
			_room_set.add_child(water)
			var fr := r as FishbowlRoom
			_room_things["fish"] = []
			for f in fr.fish:
				var n := _scene("goldfish")
				n.scale = Vector3.ONE * 1.6
				_room_set.add_child(n)
				_room_things["fish"].append(n)
			_room_things["eels"] = []
			for eel in fr.eels:
				var n := _scene("eel")
				n.scale = Vector3.ONE * 1.3
				_room_set.add_child(n)
				_room_things["eels"].append(n)
		E.RoomKind.MICE:
			var ch := _scene("cheese")
			ch.position = Vector3((MiceRoom.CHEESE_X.x + MiceRoom.CHEESE_X.y) * 0.5, 0, -0.3)
			_room_set.add_child(ch)
			_room_things["mice"] = {}
		E.RoomKind.BIRDCAGE:
			var cage := _scene("cage")
			_room_set.add_child(cage)
			_room_things["cage"] = cage
			var top := BirdcageRoom.CAGE.end.y + 0.2
			var chain := _box(_room_set, Vector3(BirdcageRoom.CAGE.get_center().x, (top + 9.5) * 0.5, 0), Vector3(0.04, 9.5 - top, 0.04), Pbr.material("metal", Color(0.9, 0.75, 0.4), 2.0, 1.0, 0.4))
			_room_things["chain"] = chain
			var bird := _scene("canary")
			bird.scale = Vector3.ONE * 1.6
			_room_set.add_child(bird)
			_room_things["bird"] = bird
		E.RoomKind.DOGBOWLS:
			var dr := r as DogbowlsRoom
			_room_things["bowls"] = []
			_room_things["dogs"] = []
			for i in DogbowlsRoom.BOWL_X.size():
				var b := _scene("milk_bowl")
				b.position = Vector3(DogbowlsRoom.BOWL_X[i], 0, 0.6)
				b.scale = Vector3.ONE * 1.3
				_room_set.add_child(b)
				var milk := MeshInstance3D.new()
				var disc := CylinderMesh.new()
				disc.top_radius = 0.4
				disc.bottom_radius = 0.36
				disc.height = 0.03
				milk.mesh = disc
				var mm := StandardMaterial3D.new()
				mm.albedo_color = Color(0.97, 0.96, 0.92)
				mm.roughness = 0.2
				milk.material_override = mm
				milk.position = Vector3(0, 0.18, 0)
				b.add_child(milk)
				_room_things["bowls"].append({"bowl": b, "milk": milk})
				var dog := _scene("bulldog")
				dog.scale = Vector3.ONE * 1.3
				_room_set.add_child(dog)
				var zz := Label3D.new()
				zz.text = "z"
				var sf := SystemFont.new()
				sf.font_names = PackedStringArray(["DejaVu Sans", "Arial", "Helvetica", "sans-serif"])
				sf.font_weight = 700
				zz.font = sf
				zz.font_size = 96
				zz.modulate = Color(0.85, 0.9, 1.0)
				zz.billboard = BaseMaterial3D.BILLBOARD_ENABLED
				_room_set.add_child(zz)
				_room_things["dogs"].append({"node": dog, "anim": dog.find_child("AnimationPlayer", true, false), "zz": zz})
		E.RoomKind.HEARTS:
			var hr := r as HeartsRoom
			_room_things["hearts"] = []
			for h in hr.hearts:
				var n := _scene("heart")
				_room_set.add_child(n)
				_room_things["hearts"].append(n)
			_box(_room_set, Vector3(8.0, HeartsRoom.TOP_Y - 0.2, 0), Vector3(2.8, 0.4, 1.2), Pbr.material("stone_bricks", Color(0.95, 0.85, 0.9), 2.0))
			var lady := _scene("lady_cat")
			lady.position = Vector3(hr.lady.x, HeartsRoom.TOP_Y, 0.2)
			lady.scale = Vector3.ONE * 1.25
			lady.rotation.y = -PI * 0.3
			_room_set.add_child(lady)
			var la: AnimationPlayer = lady.find_child("AnimationPlayer", true, false)
			la.get_animation("idle").loop_mode = Animation.LOOP_LINEAR
			la.play("idle")
			_room_things["lady"] = lady
			_room_things["arrows"] = []
			for i in 4:
				var a := _scene("arrow")
				a.scale = Vector3.ONE * 1.5
				a.visible = false
				_room_set.add_child(a)
				_room_things["arrows"].append(a)
			var moonlight := OmniLight3D.new()
			moonlight.position = Vector3(8, HeartsRoom.TOP_Y + 1.0, 2.0)
			moonlight.light_color = Color(1.0, 0.6, 0.8)
			moonlight.light_energy = 2.0
			moonlight.omni_range = 8.0
			_room_set.add_child(moonlight)
	var broom := _scene("broom")
	broom.scale = Vector3.ONE * 1.6
	broom.visible = false
	_room_set.add_child(broom)
	_room_things["broom"] = broom
	var out := {"node": _room_set, "things": _room_things}
	_room_set = saved_set
	_room_things = saved_things
	return out


func _natural_size(name: String) -> Vector2:
	match name:
		"chair": return Vector2(1.4, 1.8)
		"cabinet": return Vector2(1.6, 3.4)
		"dresser": return Vector2(1.6, 2.4)
		"table": return Vector2(7.2, 1.0)
		"stool": return Vector2(1.6, 1.4)
		"shelf": return Vector2(1.5, 2.8)
		"bookcase": return Vector2(1.4, 3.0)
	return Vector2(1.0, 1.0)


func _leave_room_set() -> void:
	if _room_set:
		_room_set.visible = false
		_room_set = null
	_room_things = {}
	_alley.visible = true
	_env.ambient_light_color = Color(0.3, 0.35, 0.55)
	_moon.visible = true


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"enter_room":
			_enter_room_set(e)
			_camera.transform = _room_cam(e)
		"leave_room":
			_leave_room_set()
			_camera.transform = _cam_alley
		"bounce":
			for c in _alley.get_children():
				if c.has_meta("x") and is_equal_approx(c.get_meta("x"), d["x"]):
					var tw := create_tween()
					tw.tween_property(c, "scale", Vector3(1.1, 0.85, 1.1), 0.06)
					tw.tween_property(c, "scale", Vector3.ONE, 0.25).set_trans(Tween.TRANS_ELASTIC)
		"land":
			_land_t = 0.18
			if d["kind"] == "ground":
				_fx.dust(_v(d["pos"], Z_STREET), 5)
		"shoe_hit":
			_fx.stars(_v(d["pos"], _cat_z))
			_shake = 0.4
		"shoe_land":
			_fx.dust(_v(d["pos"], Z_STREET), 6)
		"death":
			_fx.stars(_v(d["pos"], _cat_z))
			_shake = 0.6
		"splash":
			if _room_set:
				_fx.splash(Vector3(d["pos"].x, FishbowlRoom.BOWL.end.y, 0.3))
		"catch":
			_catch_t = 0.5
			_fx.sparkle(Vector3(d["pos"].x, d["pos"].y + 0.3, 0.4))
		"zap":
			_fx.zap(Vector3(d["pos"].x, d["pos"].y, 0.2))
			_shake = 0.5
		"cage_crash":
			_fx.dust(Vector3(d["pos"].x, 0.2, 0.2), 14)
			_shake = 0.4
		"room_won":
			_fx.confetti(Vector3(8, 6, 1))


func _room_cam(e: WhiskerEngine) -> Transform3D:
	return _cam_hearts if e.room and e.room.kind == E.RoomKind.HEARTS else _cam_room


func _v(p: Vector2, z: float) -> Vector3:
	return Vector3(p.x, p.y, z)


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	_warm += 1
	if _warm == 3:  # the loading screen has drawn them: park the prebuilt rooms out of sight
		for set in _sets.values():
			if set["node"] != _room_set:
				set["node"].visible = false
				set["node"].position = Vector3.ZERO
	var e := game.engine
	if e == null:
		return
	_time += delta
	_catch_t = maxf(0.0, _catch_t - delta)
	_land_t = maxf(0.0, _land_t - delta)
	_update_cat(e, delta)
	if _room_set:
		_update_room(e, delta)
	else:
		_update_alley(e, delta)
	_shake = maxf(0.0, _shake - delta * 2.0)
	var base := _room_cam(e) if _room_set else _cam_alley
	var s := _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var sway := Vector3(sin(_time * 0.2) * 0.05, sin(_time * 0.15) * 0.03, 0)  # barely: fine textures shimmer when the view moves
	_camera.transform = Transform3D(base.basis, base.origin + sway + Vector3(sin(_time * 60.0), sin(_time * 53.0), 0) * s)


func _layer_z(e: WhiskerEngine) -> float:
	if e.room:
		return 0.2
	if e.cat.on_ground:
		match e.cat.ground.get("kind", ""):
			"ground": return Z_STREET
			"can": return Z_CAN
			"fence": return Z_FENCE
			"line": return Z_LINE
	var y := e.cat.pos.y
	if y > E.LINE_Y[0] - 0.2:
		return Z_LINE
	if y > E.FENCE_TOP - 0.2:
		return Z_FENCE
	return _cat_z


func _update_cat(e: WhiskerEngine, delta: float) -> void:
	_cat_z = lerpf(_cat_z, _layer_z(e), 1.0 - exp(-delta * 6.0))
	var swimming: bool = e.room != null and e.room.swimming(e)
	_cat.position = Vector3(e.cat.pos.x, e.cat.pos.y, _cat_z)
	var yaw := PI * 0.5 * e.facing
	_cat.rotation.y = lerp_angle(_cat.rotation.y, yaw, 1.0 - exp(-delta * 14.0))
	var state := "idle"
	var speed := 1.0
	if e.phase == E.Phase.DYING:
		state = "die"
	elif swimming:
		state = "swim"
	elif _catch_t > 0.0:
		state = "catch"
	elif not e.cat.on_ground:
		state = "jump" if e.cat.vel.y > 0.0 else "fall"
	elif absf(e.cat.vel.x) > 0.1:
		state = "run"
		speed = 1.1
	var squash := 1.0 - _land_t * 0.8
	_cat.scale = Vector3(1.25 * (2.0 - squash), 1.25 * squash, 1.25)
	if _cat_anim.current_animation != state:
		_cat_anim.play(state, 0.1, speed)
	_cat.visible = e.phase != E.Phase.GAME_OVER and (e.stunned <= 0.0 or fmod(_time, 0.12) < 0.07)  # blinks when hit


func _update_alley(e: WhiskerEngine, delta: float) -> void:
	# windows: shutters swing open, the room lights up
	for i in _windows.size():
		var w := _windows[i]
		var target := 1.0 if e.windows[i]["open"] else 0.0
		w["open"] = move_toward(w["open"], target, delta * 3.0)
		var k: float = smoothstep(0.0, 1.0, w["open"])
		(w["left"] as Node3D).rotation.y = -k * 1.9
		(w["right"] as Node3D).rotation.y = PI + k * 1.9
		var m := (w["glow"] as MeshInstance3D).material_override as StandardMaterial3D
		m.emission_energy_multiplier = k * (1.4 + 0.15 * sin(_time * 7.0 + i))
		(w["light"] as OmniLight3D).light_energy = k * 1.2
	# the washing rides its line
	for wsh in _washing:
		var line: int = wsh["line"]
		wsh["x"] = fposmod(wsh["x"] + E.LINE_SPEED[line] * delta, E.W + 1.0)
		var n: Node3D = wsh["node"]
		n.position = Vector3(wsh["x"] - 0.5, E.LINE_Y[line] - 0.02, Z_LINE - 0.15)
		n.rotation.z = sin(_time * 2.0 + wsh["x"]) * 0.06
	# the dog
	var d := e.dog
	_dog.position = Vector3(d["x"], 0, Z_STREET - 0.1)
	_dog.rotation.y = lerp_angle(_dog.rotation.y, PI * 0.5 * d["dir"], 1.0 - exp(-delta * 10.0))
	var ds := "run" if d["chasing"] and d["alert"] <= 0.0 else ("bark" if d["chasing"] else "walk")
	if _dog_anim.current_animation != ds:
		_dog_anim.play(ds, 0.15)
	# shoes
	for i in _shoe_pool.size():
		var b := _shoe_pool[i]
		b.visible = i < e.shoes.size()
		if b.visible:
			var s: Dictionary = e.shoes[i]
			b.position = Vector3(s["pos"].x, s["pos"].y, Z_FENCE + 0.4)
			b.rotation.z += s["spin"] * delta


func _update_room(e: WhiskerEngine, delta: float) -> void:
	var r := e.room
	if r == null:
		return
	match r.kind:
		E.RoomKind.FISHBOWL:
			var fr := r as FishbowlRoom
			var fish: Array = _room_things.get("fish", [])
			for i in fish.size():
				var n: Node3D = fish[i]
				n.visible = i < fr.fish.size()
				if n.visible:
					var f: Dictionary = fr.fish[i]
					n.position = Vector3(f["pos"].x, f["pos"].y, 0.1)
					n.rotation.y = 0.0 if f["vel"].x < 0.0 else PI
					n.rotation.z = sin(_time * 12.0 + i) * 0.15
			var eels: Array = _room_things.get("eels", [])
			for i in eels.size():
				if i < fr.eels.size():
					var n: Node3D = eels[i]
					n.position = Vector3(fr.eels[i]["pos"].x, fr.eels[i]["pos"].y, 0.1)
					n.rotation.y = PI if cos(fr.eels[i]["phase"]) * fr.eels[i]["dir"] > 0 else 0.0
					n.rotation.x = sin(_time * 9.0) * 0.3
		E.RoomKind.MICE:
			var mr := r as MiceRoom
			var nodes: Dictionary = _room_things["mice"]
			var alive := {}
			for m in mr.mice:
				alive[m["id"]] = true
				if not nodes.has(m["id"]):
					var n := _scene("mouse")
					n.scale = Vector3.ONE * 2.0
					_room_set.add_child(n)
					nodes[m["id"]] = n
				var mn: Node3D = nodes[m["id"]]
				mn.position = Vector3(m["x"], mr.mouse_pos(m).y, 0.9)
				mn.rotation.y = 0.0 if m["dir"] < 0 else PI
				mn.position.y += absf(sin(_time * 30.0)) * 0.05
			for id in nodes.keys():
				if not alive.has(id):
					nodes[id].queue_free()
					nodes.erase(id)
		E.RoomKind.BIRDCAGE:
			var br := r as BirdcageRoom
			var cage: Node3D = _room_things["cage"]
			cage.position = Vector3(BirdcageRoom.CAGE.get_center().x, br.cage_y, 0.0)
			cage.rotation.z = 0.0 if not br.cage_down else sin(_time * 20.0) * 0.1 * br.cage_y
			(_room_things["chain"] as Node3D).visible = not br.cage_down
			var bird: Node3D = _room_things["bird"]
			bird.visible = r.status == 0
			bird.position = Vector3(br.bird["pos"].x, br.bird["pos"].y, 0.3)
			bird.rotation.z = sin(_time * 25.0) * (0.3 if br.bird["free"] else 0.05)
		E.RoomKind.DOGBOWLS:
			var dr := r as DogbowlsRoom
			for i in dr.bowls.size():
				var level: float = dr.bowls[i]
				var milk: MeshInstance3D = _room_things["bowls"][i]["milk"]
				milk.visible = level > 0.0
				milk.position.y = 0.09 + 0.09 * level
				milk.scale = Vector3(0.85 + 0.15 * level, 1.0, 0.85 + 0.15 * level)
				var dd: Dictionary = _room_things["dogs"][i]
				var dog: Node3D = dd["node"]
				var awake: bool = dr.dogs[i]["awake"] > 0.0
				dog.position = Vector3(dr.dogs[i]["x"], 0, 0.3)
				dog.rotation.y = lerp_angle(dog.rotation.y, PI * 0.5 * dr.dogs[i]["dir"] if awake else -PI * 0.5, 1.0 - exp(-delta * 8.0))
				var st := "run" if awake else "idle"
				var anim: AnimationPlayer = dd["anim"]
				if anim.current_animation != st:
					anim.play(st, 0.2, 1.0 if awake else 0.3)
				dog.scale = Vector3(1.3, 1.3 * (1.0 if awake else 0.9 + 0.03 * sin(_time * 2.0 + i)), 1.3)  # snoring
				var zz: Label3D = dd["zz"]
				zz.visible = not awake
				var zt := fmod(_time * 0.6 + i * 0.3, 1.0)
				zz.position = Vector3(dr.dogs[i]["x"] + 0.3 + zt * 0.5, 1.4 + zt * 1.2, 0.5)
				zz.modulate.a = 1.0 - zt
				zz.font_size = int(60 + zt * 60)
		E.RoomKind.HEARTS:
			var hr := r as HeartsRoom
			for i in hr.hearts.size():
				var n: Node3D = _room_things["hearts"][i]
				var rect: Rect2 = hr.hearts[i]["rect"]
				n.position = Vector3(rect.get_center().x, rect.end.y, 0.0)
				n.rotation.z = sin(_time * 1.5 + i) * 0.05
			var arrows: Array = _room_things["arrows"]
			for i in arrows.size():
				var a: Node3D = arrows[i]
				a.visible = i < hr.arrows.size()
				if a.visible:
					a.position = Vector3(hr.arrows[i]["pos"].x, hr.arrows[i]["pos"].y, 0.4)
					a.rotation.y = 0.0 if hr.arrows[i]["dir"] < 0 else PI
	var broom: Node3D = _room_things["broom"]
	broom.visible = r.time_left < 5.0
	if broom.visible:  # the broom sweeps in from the right toward the cat
		var k := 1.0 - r.time_left / 5.0
		broom.position = Vector3(lerpf(17.0, e.cat.pos.x + 0.8, k), 0.0, 0.5)
		broom.rotation.z = 0.35 + sin(_time * 14.0) * 0.25
