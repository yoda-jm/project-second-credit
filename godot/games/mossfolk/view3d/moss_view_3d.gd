class_name MossView3D
extends Node3D
## Mossfolk in 3D: the level is a carved slab of earth standing in a deep cavern, seen from the front; mosslings
## are little rigged creatures walking on it, lit by their lanterns. Glowing crystals, mushrooms and roots fill the
## cave behind; water shimmers in the pits. The camera scrolls along the level. Pixel (x, y) of the level is world
## (x * 0.1, (h - y) * 0.1, 0): 10 pixels to a unit, y up.

const E = preload("res://games/mossfolk/engine/moss_engine.gd")
const M := "res://games/mossfolk/art/models/"
const PX := 0.1
const ANIM := {"walk": "walk", "fall": "fall", "glide": "float", "climb": "climb", "dig": "dig", "bash": "bash",
	"mine": "mine", "build": "build", "block": "block", "shrug": "shrug", "panic": "panic", "splat": "splat",
	"exit": "exit", "drown": "drown"}
## per theme: earth, deep earth, moss, steel, cave light, backdrop
const THEMES := [
	{"earth": Color(0.5, 0.36, 0.24), "earth2": Color(0.33, 0.23, 0.16), "moss": Color(0.38, 0.66, 0.24), "steel": Color(0.36, 0.4, 0.46),
		"light": Color(0.55, 0.85, 1.0), "cave": Color(0.08, 0.1, 0.14)},
	{"earth": Color(0.56, 0.44, 0.34), "earth2": Color(0.38, 0.3, 0.26), "moss": Color(0.55, 0.62, 0.25), "steel": Color(0.4, 0.4, 0.44),
		"light": Color(1.0, 0.75, 0.45), "cave": Color(0.12, 0.09, 0.08)},
	{"earth": Color(0.4, 0.38, 0.44), "earth2": Color(0.26, 0.25, 0.32), "moss": Color(0.3, 0.6, 0.5), "steel": Color(0.34, 0.38, 0.46),
		"light": Color(0.6, 0.6, 1.0), "cave": Color(0.07, 0.07, 0.13)},
	{"earth": Color(0.62, 0.6, 0.58), "earth2": Color(0.42, 0.42, 0.44), "moss": Color(0.5, 0.72, 0.32), "steel": Color(0.4, 0.44, 0.5),
		"light": Color(0.8, 1.0, 0.75), "cave": Color(0.09, 0.12, 0.1)},
	{"earth": Color(0.52, 0.28, 0.2), "earth2": Color(0.3, 0.16, 0.12), "moss": Color(0.72, 0.5, 0.2), "steel": Color(0.3, 0.3, 0.34),
		"light": Color(1.0, 0.55, 0.3), "cave": Color(0.12, 0.06, 0.05)},
]

@export var game: MossGame

var camera: Camera3D
var cam_x := 0.0            ## the camera's centre, in pixels
var _env: Environment
var _stage: Node3D
var _mask: Image
var _mask_tex: ImageTexture
var _front_mat: ShaderMaterial
var _back_mat: ShaderMaterial
var _folk := {}             ## id -> {node, anim, last, label}
var _hatch: Node3D
var _fx: Bursts
var _time := 0.0
var _lv: MossLevel


func px(x: float, y: float, z := 0.0) -> Vector3:
	return Vector3(x * PX, (_lv.h - y) * PX, z)


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_energy = 0.55
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.8
	_env.glow_bloom = 0.06
	_env.glow_hdr_threshold = 0.9
	_env.fog_enabled = true
	_env.fog_density = 0.02
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, -25, 0)
	key.light_energy = 0.9
	key.shadow_enabled = true
	key.light_color = Color(1.0, 0.95, 0.85)
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 32
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String, fallback := Vector3(0.6, 0.8, 0.4), col := Color(0.5, 0.7, 0.4)) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := CapsuleMesh.new()
	b.radius = fallback.x * 0.5
	b.height = fallback.y
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	b.material = m
	mi.mesh = b
	mi.position.y = fallback.y * 0.5
	n.add_child(mi)
	return n


func _on_level(e: MossEngine) -> void:
	e.event.connect(_on_event)
	_lv = e.level
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_folk.clear()
	var th: Dictionary = THEMES[_lv.theme % THEMES.size()]
	_env.background_color = th["cave"]
	_env.ambient_light_color = th["light"].lerp(Color.WHITE, 0.5)
	_env.fog_light_color = th["cave"].lightened(0.1)
	# the terrain mask
	_mask = Image.create(_lv.w, _lv.h, false, Image.FORMAT_R8)
	_refresh(Rect2i(0, 0, _lv.w, _lv.h), e)
	_mask_tex = ImageTexture.create_from_image(_mask)
	var shader: Shader = load("res://games/mossfolk/shaders/moss_terrain.gdshader")
	_front_mat = _terrain_mat(shader, th, false)
	_back_mat = _terrain_mat(shader, th, true)
	for layer in [[_front_mat, 0.0, 1.0], [_back_mat, -0.45, 1.0]]:
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(_lv.w * PX, _lv.h * PX)
		q.mesh = qm
		q.material_override = layer[0]
		q.position = Vector3(_lv.w * PX * 0.5, _lv.h * PX * 0.5, layer[1])
		_stage.add_child(q)
	# the side of the slab: a few stacked copies make it read as solid
	for z in [-0.15, -0.3]:
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(_lv.w * PX, _lv.h * PX)
		q.mesh = qm
		q.material_override = _back_mat
		q.position = Vector3(_lv.w * PX * 0.5, _lv.h * PX * 0.5, z)
		_stage.add_child(q)
	_backdrop(th)
	_water(th)
	# hatch, burrow and traps
	_hatch = _scene("hatch", Vector3(2.0, 0.6, 1.0), Color(0.4, 0.3, 0.2))
	_hatch.position = px(_lv.entrance.x, _lv.entrance.y - 1, 0.05)
	_stage.add_child(_hatch)
	var burrow := _scene("burrow", Vector3(2.0, 2.5, 1.0), Color(0.9, 0.7, 0.3))
	burrow.position = px(_lv.exit.x, _lv.exit.y + 1, 0.0)
	_stage.add_child(burrow)
	_play_loop(burrow, "glow")
	var bl := OmniLight3D.new()
	bl.light_color = Color(1.0, 0.75, 0.4)
	bl.light_energy = 2.0
	bl.omni_range = 4.0
	bl.position = Vector3(0, 1.2, 1.0)
	burrow.add_child(bl)
	for t in _lv.traps:
		var n := _scene("trap_" + t["kind"], Vector3(0.8, 1.0, 0.8), Color(0.6, 0.2, 0.3))
		n.position = px(t["pos"].x, t["pos"].y + 1, 0.05)
		_stage.add_child(n)
		_play_loop(n, "idle")
	cam_x = _lv.entrance.x
	_place_camera(1.0)


func _terrain_mat(shader: Shader, th: Dictionary, back: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = shader
	m.set_shader_parameter("mask", _mask_tex)
	m.set_shader_parameter("mask_soft", _mask_tex)
	m.set_shader_parameter("size", Vector2(_lv.w, _lv.h))
	m.set_shader_parameter("back", back)
	m.set_shader_parameter("col_earth", th["earth"])
	m.set_shader_parameter("col_earth2", th["earth2"])
	m.set_shader_parameter("col_moss", th["moss"])
	m.set_shader_parameter("col_steel", th["steel"])
	m.set_shader_parameter("seed", float(_lv.theme) * 7.3)
	return m


func _refresh(r: Rect2i, e: MossEngine) -> void:
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			var v := e.terrain[y * _lv.w + x]
			_mask.set_pixel(x, y, Color(0.4 * v, 0, 0))


## The cave behind: a far wall, glowing crystals and mushrooms along the ground, roots from the ceiling.
func _backdrop(th: Dictionary) -> void:
	var wall := MeshInstance3D.new()
	var wm := QuadMesh.new()
	wm.size = Vector2(_lv.w * PX + 40.0, _lv.h * PX + 20.0)
	wall.mesh = wm
	var sm := ShaderMaterial.new()
	sm.shader = load("res://games/mossfolk/shaders/cave_wall.gdshader")
	sm.set_shader_parameter("tint", th["cave"].lightened(0.12))
	sm.set_shader_parameter("glow", th["light"])
	wall.material_override = sm
	wall.position = Vector3(_lv.w * PX * 0.5, _lv.h * PX * 0.5, -6.0)
	_stage.add_child(wall)
	var rng := RandomNumberGenerator.new()
	rng.seed = _lv.name.hash()
	# along the ground tops, behind the slab
	var props := ["mushroom_big", "mushroom_small", "crystal_cluster", "fern", "fern", "mushroom_small"]
	var x := 4
	while x < _lv.w - 4:
		x += rng.randi_range(14, 40)
		var y := _top(x)
		if y < 0:
			continue
		var kind: String = props[rng.randi_range(0, props.size() - 1)]
		var n := _scene(kind, Vector3(0.3, 0.4, 0.3), th["moss"])
		n.position = px(x, y, rng.randf_range(-1.2, -0.5))
		n.rotation.y = rng.randf() * TAU
		n.scale = Vector3.ONE * rng.randf_range(0.8, 1.6)
		_stage.add_child(n)
		if kind == "crystal_cluster":
			var l := OmniLight3D.new()
			l.light_color = th["light"]
			l.light_energy = 1.2
			l.omni_range = 3.0
			l.position.y = 0.5
			n.add_child(l)
	for i in _lv.w / 60:
		var r := _scene("root_hang", Vector3(0.1, 0.8, 0.1), th["earth2"])
		r.position = Vector3(rng.randf_range(0.0, _lv.w * PX), _lv.h * PX + 0.5, rng.randf_range(-2.5, -1.0))
		r.scale = Vector3.ONE * rng.randf_range(1.0, 2.0)
		_stage.add_child(r)
	# lanterns on posts here and there, in front
	for i in _lv.w / 160:
		var xx := rng.randi_range(20, _lv.w - 20)
		var yy := _top(xx)
		if yy < 0:
			continue
		var lp := _scene("lantern_post", Vector3(0.1, 1.2, 0.1), Color(1.0, 0.8, 0.4))
		lp.position = px(xx, yy, -0.25)
		_stage.add_child(lp)
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.75, 0.45)
		l.light_energy = 1.4
		l.omni_range = 3.5
		l.position = Vector3(0, 1.1, 0.4)
		lp.add_child(l)


func _top(x: int) -> int:
	for y in range(1, _lv.h):
		if _lv.terrain[y * _lv.w + x] != E.AIR and _lv.terrain[(y - 1) * _lv.w + x] == E.AIR:
			return y
	return -1


func _water(th: Dictionary) -> void:
	for r in _lv.water:
		var q := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3(r.size.x * PX, r.size.y * PX, 1.0)
		q.mesh = b
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(th["light"].darkened(0.3), 0.75)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.emission_enabled = true
		m.emission = th["light"] * 0.35
		m.roughness = 0.1
		q.material_override = m
		q.position = px(r.position.x + r.size.x * 0.5, r.position.y + r.size.y * 0.5, -0.2)
		_stage.add_child(q)


func _play_loop(n: Node, anim: String) -> void:
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR
		ap.play(anim)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hatch":
			var ap: AnimationPlayer = _hatch.find_child("AnimationPlayer", true, false)
			if ap and ap.has_animation("open"):
				ap.play("open")
		"stroke":
			var c: Dictionary = e.folk[d["id"]]
			var th: Dictionary = THEMES[_lv.theme % THEMES.size()]
			_fx.burst(px(c["x"] + c["dir"] * 4, c["y"] - 2, 0.2), th["earth"], 6, 1.5, 0.5, 0.06, 0.0, -6.0, 0.8)
		"pop":
			_fx.burst(px(d["x"], d["y"], 0.3), Color(1.0, 0.7, 0.3), 36, 4.0, 0.7, 0.14, 1.0, -4.0, 1.0, "glow")
			_fx.flash(px(d["x"], d["y"], 0.3) - Vector3(0, 2.5, -1.0), Color(1.0, 0.6, 0.3), 3.0)
		"death":
			if d["how"] == "drown":
				_fx.burst(px(d["x"], d["y"], 0.2), Color(0.6, 0.85, 1.0), 14, 1.2, 0.8, 0.06, 1.0, 1.0, 1.0, "glow")
			elif d["how"] == "splat":
				_fx.burst(px(d["x"], d["y"], 0.2), THEMES[_lv.theme % THEMES.size()]["moss"], 16, 2.0, 0.5, 0.07, 0.0, -6.0, 0.6)
		"saved":
			_fx.burst(px(_lv.exit.x, _lv.exit.y - 8, 0.4), Color(1.0, 0.85, 0.4), 12, 1.5, 0.6, 0.08, 1.0, 1.0, 1.0, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _lv == null:
		return
	if e.changed.size != Vector2i.ZERO:
		_refresh(e.changed, e)
		e.changed = Rect2i()
		_mask_tex.update(_mask)
	var step := clampf(game._acc / E.TICK, 0.0, 1.0)
	for c in e.folk:
		var id: int = c["id"]
		var gone: bool = c["state"] == "gone"
		if not _folk.has(id):
			if gone:
				continue
			var n := _scene("mossling", Vector3(0.5, 0.9, 0.5), Color(0.4, 0.7, 0.35))
			_stage.add_child(n)
			var lb := Label3D.new()
			lb.font = HudKit.font(true)
			lb.font_size = 64
			lb.pixel_size = 0.006
			lb.outline_size = 12
			lb.position = Vector3(0, 1.45, 0.2)
			lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			lb.no_depth_test = true
			n.add_child(lb)
			var l := OmniLight3D.new()  # its lantern
			l.light_color = Color(1.0, 0.8, 0.45)
			l.light_energy = 0.22
			l.omni_range = 1.0
			l.position = Vector3(0.25, 0.7, 0.3)
			n.add_child(l)
			_folk[id] = {"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": "", "label": lb,
				"pos": px(c["x"], c["y"] + 1)}
		var f: Dictionary = _folk[id]
		var node: Node3D = f["node"]
		if gone:
			node.queue_free()
			_folk.erase(id)
			continue
		var target := px(c["x"], c["y"] + 1, 0.0)
		f["pos"] = (f["pos"] as Vector3).lerp(target, minf(1.0, delta * 18.0))
		node.position = f["pos"]
		# the model faces +X with its tool side to the camera: walking left mirrors it
		var sx := 1.4 if c["dir"] > 0 else -1.4
		node.scale = Vector3(move_toward(node.scale.x, sx, delta * 18.0), 1.4, 1.4)
		var want: String = ANIM.get(c["state"], "walk")
		var ap: AnimationPlayer = f["anim"]
		if ap and f["last"] != want and ap.has_animation(want):
			f["last"] = want
			var a := ap.get_animation(want)
			a.loop_mode = Animation.LOOP_NONE if want in ["shrug", "splat", "exit", "drown"] else Animation.LOOP_LINEAR
			ap.play(want, 0.12)
		var lb: Label3D = f["label"]
		var b: int = c["bomb"]
		lb.visible = b >= 0 and c["state"] != "panic"
		if lb.visible:
			lb.text = str(5 - int(b * E.TICK))
			lb.modulate = Color(1.0, 0.85 - b / 170.0, 0.4)
	_place_camera(delta)


## Where the view follows: the player scrolls; the demo follows the busy mosslings.
func _place_camera(delta: float) -> void:
	var e := game.engine
	if not game.demo:
		var sx := 0.0
		if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A): sx -= 1.0
		if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D): sx += 1.0
		var mx := get_viewport().get_mouse_position().x
		var vw := get_viewport().get_visible_rect().size.x
		if DisplayServer.window_is_focused() and mx >= 0.0 and mx < 8.0: sx -= 1.0
		if DisplayServer.window_is_focused() and mx > vw - 8.0 and mx <= vw: sx += 1.0
		cam_x = clampf(cam_x + sx * 260.0 * delta, 0.0, _lv.w)
	if game.demo and e and not e.folk.is_empty():
		var sum := 0.0
		var n := 0
		for c in e.folk:
			if c["state"] != "gone":
				var wgt := 4.0 if c["state"] in ["dig", "bash", "mine", "build", "climb", "glide"] else 1.0
				sum += c["x"] * wgt
				n += int(wgt)
		if n > 0:
			cam_x = lerpf(cam_x, sum / n, minf(1.0, delta * 1.5))
	var vp := get_viewport().get_visible_rect().size
	var aspect := vp.aspect()
	# the level's height fills the view above the skill bar (the lower 18% of the screen)
	var half_h := _lv.h * PX * 0.5 / 0.82
	var dist := half_h / tan(deg_to_rad(camera.fov * 0.5))
	var half_w := half_h * aspect
	var cx := clampf(cam_x * PX, minf(half_w, _lv.w * PX * 0.5), maxf(_lv.w * PX - half_w, _lv.w * PX * 0.5))
	var cy := _lv.h * PX * 0.5 - half_h * 0.18
	camera.position = Vector3(cx, cy + 0.6, dist)
	camera.look_at(Vector3(cx, cy, 0.0), Vector3.UP)


## The level pixel under a screen point (for the cursor).
func pixel_at(screen: Vector2) -> Vector2:
	var o := camera.project_ray_origin(screen)
	var d := camera.project_ray_normal(screen)
	if absf(d.z) < 0.0001:
		return Vector2(-999, -999)
	var p := o + d * (-o.z / d.z)
	return Vector2(p.x / PX, _lv.h - p.y / PX)


## A mossling's screen position (for the HUD's cursor bracket).
func screen_of(c: Dictionary) -> Vector2:
	return camera.unproject_position(px(c["x"], c["y"] - 4, 0.0))
