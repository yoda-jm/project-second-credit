class_name FuseView3D
extends Node3D
## Fuseflight in 3D: a festival night (the FuseBackdrop diorama when there is one) and the arena in front of it: dark
## wooden ledges trimmed with strings of little lanterns, the fireworks waiting on their sticks in four paper colours,
## the lit one's fuse spitting sparks and glowing; taking a firework sends it up into the sky to burst in its colour
## (a lit one bigger). The sprite glides with its cape spread; enemies become spinning sparks while the power lasts.
## The camera frames the arena, leans with the sprite, drifts, punches in on a lit catch and swings at a stage clear.
## World = arena units (x 0-16, y 0-12), the play plane at z = 0.

const F = preload("res://games/fuseflight/engine/fuse_engine.gd")
const M := "res://games/fuseflight/art/models/"
const ROCKET_SCALE := 1.5   ## the fireworks are drawn larger than their touch box, to read from the camera
const BACKDROP := "res://games/fuseflight/view3d/fuse_backdrop.gd"
const PAPER := [Color(1.0, 0.3, 0.3), Color(0.3, 0.6, 1.0), Color(1.0, 0.8, 0.25), Color(0.5, 1.0, 0.5)]
const ENEMY_COLORS := {"walker": Color(0.7, 0.4, 1.0), "flyer": Color(1.0, 0.4, 0.6), "orb": Color(0.4, 1.0, 0.9)}

@export var game: FuseGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _moon: DirectionalLight3D
var _stage: Node3D
var _backdrop: Node3D
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _hero_last := ""
var _rockets: Array[Node3D] = []
var _lit_fx: CPUParticles3D
var _lit_light: OmniLight3D
var _enemy_nodes := {}
var _star: Node3D
var _letter_nodes: Array[Node3D] = []
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _sweep := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _mats := {}


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.02, 0.02, 0.06)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.35, 0.35, 0.55)
	_env.ambient_light_energy = 0.5
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.9
	_env.glow_hdr_threshold = 0.9
	_we = WorldEnvironment.new()
	_we.environment = _env
	add_child(_we)
	_moon = DirectionalLight3D.new()
	_moon.rotation_degrees = Vector3(-40, -25, 0)
	_moon.light_color = Color(0.7, 0.75, 1.0)
	_moon.light_energy = 0.5
	_moon.shadow_enabled = true
	add_child(_moon)
	var key := DirectionalLight3D.new()  # a warm festival light on the play pieces only
	key.rotation_degrees = Vector3(-20, 10, 0)
	key.light_color = Color(1.0, 0.85, 0.65)
	key.light_energy = 1.0
	key.light_cull_mask = 2
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 38
	camera.far = 4000.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mat(col: Color, rough := 0.5, emit := 0.0, metal := 0.0) -> StandardMaterial3D:
	var key := "%s|%s|%s|%s" % [col, rough, emit, metal]
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	m.metallic = metal
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	_mats[key] = m
	return m


func _box(size: Vector3, m: Material, at := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = m
	mi.position = at
	return mi


func _sphere(r: float, m: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	mi.mesh = s
	mi.material_override = m
	return mi


func _play_layer(n: Node) -> void:
	for v in n.find_children("*", "VisualInstance3D", true, false):
		(v as VisualInstance3D).layers |= 2
	if n is VisualInstance3D:
		(n as VisualInstance3D).layers |= 2


func _play(ap: AnimationPlayer, anim: String, loop := false, blend := 0.12) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, blend)


func _on_stage(e: FuseEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	for k in _enemy_nodes:
		(_enemy_nodes[k] as Node3D).queue_free()
	_enemy_nodes.clear()
	_stage = Node3D.new()
	add_child(_stage)
	_rockets.clear()
	_letter_nodes.clear()
	_star = null
	var st := e.stage
	_backdrop = null
	if ResourceLoader.exists(BACKDROP):
		_backdrop = (load(BACKDROP) as GDScript).new()
		_stage.add_child(_backdrop)
		_backdrop.call("build", st.theme)
		var d: Dictionary = _backdrop.call("environment_for", st.theme)
		_env = _backdrop.call("make_environment", d)
		_we.environment = _env
		_backdrop.call("setup_sun", _moon, d)
	else:
		var ground := _box(Vector3(40, 0.4, 6), _mat(Color(0.12, 0.1, 0.12), 0.9), Vector3(8, -0.2, 0))
		_stage.add_child(ground)
	# the arena's floor: polished boards with a lantern rail along the front
	_stage.add_child(_box(Vector3(16.6, 0.25, 1.6), _mat(Color(0.35, 0.22, 0.14), 0.45), Vector3(8, -0.125, 0)))
	_lantern_string(Vector3(0, 0.1, 0.75), Vector3(16, 0.1, 0.75), 18)
	# the ledges: dark wood with gold trim and lanterns under their edge
	for p in st.platforms:
		var r: Rect2 = p
		var c := Vector3(r.get_center().x, r.get_center().y, 0)
		_stage.add_child(_box(Vector3(r.size.x, r.size.y, 1.0), _mat(Color(0.28, 0.17, 0.1), 0.5), c))
		_stage.add_child(_box(Vector3(r.size.x + 0.08, 0.05, 1.05), _mat(Color(1.0, 0.75, 0.35), 0.3, 0.6, 0.6), c + Vector3(0, r.size.y * 0.5, 0)))
		_lantern_string(Vector3(r.position.x + 0.1, r.position.y - 0.12, 0.52), Vector3(r.end.x - 0.1, r.position.y - 0.12, 0.52), maxi(2, int(r.size.x * 1.5)))
	# the fireworks
	for i in st.bombs.size():
		var b: Vector2 = st.bombs[i]
		var n := _scene("rocket")
		var col: Color = PAPER[i % PAPER.size()]
		if n == null:
			n = Node3D.new()
			n.add_child(_box(Vector3(0.16, 0.34, 0.16), _mat(col, 0.5, 0.3), Vector3(0, 0.05, 0)))
			n.add_child(_box(Vector3(0.03, 0.3, 0.03), _mat(Color(0.6, 0.45, 0.3)), Vector3(0, -0.25, 0)))
		else:
			for mi in n.find_children("*", "MeshInstance3D", true, false):
				var m := mi as MeshInstance3D
				for k in m.mesh.get_surface_count():
					var sm := m.mesh.surface_get_material(k)
					if sm and sm.resource_name.contains("rocket_paper"):
						m.set_surface_override_material(k, _mat(col, 0.55, 0.15))
		n.position = Vector3(b.x, b.y, 0.05)
		n.scale = Vector3.ONE * ROCKET_SCALE
		n.set_meta("col", col)
		_play_layer(n)
		_stage.add_child(n)
		_rockets.append(n)
	# the lit fuse: sparks and a light, moved to the lit firework
	_lit_fx = CPUParticles3D.new()
	_lit_fx.amount = 40
	_lit_fx.lifetime = 0.5
	_lit_fx.direction = Vector3(0, 1, 0)
	_lit_fx.spread = 60.0
	_lit_fx.initial_velocity_min = 0.6
	_lit_fx.initial_velocity_max = 1.6
	_lit_fx.gravity = Vector3(0, -3.0, 0)
	_lit_fx.scale_amount_min = 0.3
	_lit_fx.scale_amount_max = 0.7
	var q := QuadMesh.new()
	q.size = Vector2(0.06, 0.06)
	_lit_fx.mesh = q
	_lit_fx.material_override = Fx.material("glow", Color(1.0, 0.75, 0.3))
	_lit_fx.emitting = false
	_stage.add_child(_lit_fx)
	_lit_light = OmniLight3D.new()
	_lit_light.light_color = Color(1.0, 0.7, 0.3)
	_lit_light.light_energy = 0.0
	_lit_light.omni_range = 2.2
	_stage.add_child(_lit_light)
	# the sprite
	_hero = Node3D.new()
	var body := _scene("sprite")
	if body == null:
		body = Node3D.new()
		var b := _sphere(0.32, _mat(Color(1.0, 0.65, 0.25), 0.4, 0.5))
		b.position = Vector3(0, 0.45, 0)
		body.add_child(b)
	body.name = "body"
	_hero.add_child(body)
	_hero_anim = body.find_child("AnimationPlayer", true, false)
	_hero_last = ""
	var hl := OmniLight3D.new()
	hl.light_color = Color(1.0, 0.75, 0.4)
	hl.light_energy = 1.0
	hl.omni_range = 2.5
	hl.position = Vector3(0, 0.6, 0.5)
	_hero.add_child(hl)
	_play_layer(_hero)
	_stage.add_child(_hero)
	_sweep = 0.0
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


## A string of little glowing lanterns between two points (one light for the lot, to keep it cheap).
func _lantern_string(a: Vector3, b: Vector3, n: int) -> void:
	for i in n:
		var t := (i + 0.5) / n
		var col: Color = [Color(1.0, 0.6, 0.25), Color(1.0, 0.35, 0.3), Color(1.0, 0.85, 0.4)][i % 3]
		var l := _sphere(0.055, _mat(col, 0.4, 3.0))
		l.position = a.lerp(b, t) + Vector3(0, -sin(t * PI) * 0.08, 0)
		l.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_stage.add_child(l)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"take":
			var i: int = d["i"]
			var n := _rockets[i]
			var col: Color = n.get_meta("col")
			var p := n.position
			n.visible = false
			# it goes up and bursts in its colour
			var big: bool = d["lit"]
			_fx.burst(p, col.lerp(Color.WHITE, 0.3), 26 if big else 14, 3.5 if big else 2.5, 0.7, 0.09, 1.0, -2.0, 1.0, "glow")
			var sky := Vector3(p.x, minf(11.5, p.y + 3.0), -0.5)
			var tw := create_tween()
			var trail := _sphere(0.06, _mat(Color(1.0, 0.85, 0.5), 0.3, 4.0))
			trail.position = p
			_stage.add_child(trail)
			tw.tween_property(trail, "position", sky, 0.35).set_ease(Tween.EASE_OUT)
			tw.tween_callback(func():
				_fx.burst(sky, col, 60 if big else 34, 6.0 if big else 4.5, 1.2, 0.12, 1.0, -1.5, 1.0, "glow")
				_fx.flash(sky + Vector3(0, -1.0, 1.5), col, 2.5 if big else 1.4)
				if _backdrop and _backdrop.has_method("flash"):
					_backdrop.call("flash", sky)
				trail.queue_free())
			if big:
				_punch = 0.4
				_punch_at = p
		"die":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y + 0.4, 0.2), Color(1.0, 0.6, 0.3), 40, 4.0, 0.9, 0.1, 1.0, -3.0, 1.0, "glow")
			_shake = 0.8
			_play(_hero_anim, "die")
			_hero_last = "die"
		"eat":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y + 0.3, 0.2), Color(1.0, 0.95, 0.5), 24, 3.0, 0.6, 0.08, 1.0, -1.0, 1.0, "glow")
		"power":
			_fx.flash(_hero.position + Vector3(0, -1.0, 1.5), Color(1.0, 0.9, 0.5), 3.0)
		"cleared":
			_sweep = 1.0
			_play(_hero_anim, "cheer", true)
			_hero_last = "cheer"
			if _backdrop and _backdrop.has_method("celebrate"):
				_backdrop.call("celebrate")
		"jump":
			_play(_hero_anim, "leap", false, 0.05)
			_hero_last = "leap"
		"land":
			_play(_hero_anim, "land", false, 0.05)
			_hero_last = "land"
			_fx.burst(_hero.position + Vector3(0, 0.05, 0.2), Color(1.0, 0.8, 0.5), 8, 1.2, 0.3, 0.06, 1.0, -3.0, 0.5, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	var h := e.hero
	var hp: Vector2 = h["pos"]
	_hero.position = Vector3(hp.x, hp.y, 0.1)
	var moving := absf(e.move_x) > 0.1
	_hero.rotation.y = lerp_angle(_hero.rotation.y, deg_to_rad(60.0) * float(h["facing"]) if moving else 0.0, minf(1.0, delta * 12.0))
	_hero.visible = not (e.phase == F.Phase.DYING and _hero_last != "die") or fmod(_time, 0.16) < 0.08
	if e.phase == F.Phase.PLAY and not (_hero_last in ["leap", "land"] and _hero_anim and _hero_anim.is_playing()):
		var want := "idle"
		if not h["ground"]:
			want = "glide" if h["gliding"] else ("rise" if h["vel"].y > 0.0 else "fall")
		elif moving:
			want = "run"
		if want != _hero_last:
			_hero_last = want
			_play(_hero_anim, want, true)
	elif e.phase == F.Phase.READY and _hero_last in ["die", "cheer", ""]:
		_hero_last = "idle"
		_play(_hero_anim, "idle", true)
	# the lit fuse
	if e.lit >= 0 and e.lit < _rockets.size():
		var n := _rockets[e.lit]
		var tip := n.find_child("fuse_tip", true, false) as Node3D
		var at: Vector3 = tip.global_position if tip else n.position + Vector3(0, 0.25, 0)
		_lit_fx.position = at
		_lit_fx.emitting = true
		_lit_light.position = at + Vector3(0, 0.1, 0.3)
		_lit_light.light_energy = 2.0 + 0.6 * sin(_time * 30.0)
		n.scale = Vector3.ONE * ROCKET_SCALE * (1.18 + 0.1 * sin(_time * 8.0))
	else:
		_lit_fx.emitting = false
		_lit_light.light_energy = 0.0
	for i in _rockets.size():
		if e.taken[i] == 0 and i != e.lit:
			_rockets[i].rotation.z = sin(_time * 1.5 + i) * 0.06
	_place_enemies(e)
	_place_pickups(e)
	_shake = maxf(0.0, _shake - delta * 1.6)
	_punch = maxf(0.0, _punch - delta)
	_sweep = maxf(0.0, _sweep - delta / 3.0)
	_place_camera(delta)


func _place_enemies(e: FuseEngine) -> void:
	var live := {}
	for en in e.enemies:
		var id: int = en["id"]
		live[id] = true
		var kind: String = "spark" if e.power > 0.0 else en["kind"]
		var n: Node3D = _enemy_nodes.get(id)
		if n == null or n.get_meta("kind") != kind:
			if n:
				_fx.burst(n.position, Color(1, 1, 1), 10, 2.0, 0.4, 0.07, 1.0, 0.0, 1.0, "glow")
				n.queue_free()
			n = _scene(kind)
			if n == null:
				n = _sphere(0.26, _mat(ENEMY_COLORS.get(kind, Color(1.0, 0.95, 0.5)), 0.4, 1.0))
			n.set_meta("kind", kind)
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			for anim in ["walk", "fly", "spin"]:
				if ap and ap.has_animation(anim):
					_play(ap, anim, true)
					break
			_play_layer(n)
			_stage.add_child(n)
			_enemy_nodes[id] = n
		var p: Vector2 = en["pos"]
		n.position = Vector3(p.x, p.y + (0.0 if en["kind"] == "walker" and kind != "spark" else 0.0), 0.1)
		if en["kind"] == "walker":
			n.rotation.y = deg_to_rad(70.0) * float(en["dir"])
		elif en["kind"] == "flyer":
			n.rotation.y = deg_to_rad(40.0) * signf((en["vel"] as Vector2).x)
	for id in _enemy_nodes.keys():
		if not live.has(id):
			(_enemy_nodes[id] as Node3D).queue_free()
			_enemy_nodes.erase(id)


func _place_pickups(e: FuseEngine) -> void:
	if not e.star.is_empty():
		if _star == null:
			_star = _scene("star")
			if _star == null:
				_star = _sphere(0.3, _mat(Color(1.0, 0.9, 0.4), 0.2, 2.5))
			var sl := OmniLight3D.new()
			sl.light_color = Color(1.0, 0.9, 0.5)
			sl.light_energy = 1.2
			sl.omni_range = 2.5
			_star.add_child(sl)
			_play_layer(_star)
			_stage.add_child(_star)
		var p: Vector2 = e.star["pos"]
		_star.position = Vector3(p.x, p.y, 0.1)
		_star.rotation.y = _time * 3.0
	elif _star:
		_star.queue_free()
		_star = null
	while _letter_nodes.size() > e.letters.size():
		_letter_nodes.pop_back().queue_free()
	for i in e.letters.size():
		var l: Dictionary = e.letters[i]
		if i >= _letter_nodes.size() or _letter_nodes[i].get_meta("kind") != l["kind"]:
			var n := _scene("letter_" + str(l["kind"]).to_lower())
			if n == null:
				n = _sphere(0.22, _mat(Color(0.5, 0.9, 1.0) if l["kind"] == "E" else Color(1.0, 0.6, 0.9), 0.3, 1.5))
			n.set_meta("kind", l["kind"])
			_play_layer(n)
			if i < _letter_nodes.size():
				_letter_nodes[i].queue_free()
				_letter_nodes[i] = n
			else:
				_letter_nodes.append(n)
			_stage.add_child(n)
		var p: Vector2 = l["pos"]
		_letter_nodes[i].position = Vector3(p.x, p.y, 0.1)
		_letter_nodes[i].rotation.y = _time * 2.0


## Frames the arena from the front, leaning a little towards the sprite and drifting; a punch towards a lit catch, a
## shake when the sprite is caught, a swing round at a stage clear.
func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(6.6, 8.6 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var hp: Vector2 = e.hero["pos"] if e else Vector2(8, 6)
	var look := Vector3(8.0 + (hp.x - 8.0) * 0.1, 5.9 + (hp.y - 6.0) * 0.06, 0.0)
	var pos := look + Vector3(sin(_time * 0.13) * 0.5, 0.8 + sin(_time * 0.11) * 0.2, dist)
	if _punch > 0.0:
		var k := sin(_punch / 0.4 * PI) * 0.1
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + Vector3(0, 0, dist * 0.7), k)
	if _sweep > 0.0:
		var k := sin(_sweep * PI)
		pos += Vector3(sin((1.0 - _sweep) * PI) * 5.0, 1.5 * k, 2.0 * k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
