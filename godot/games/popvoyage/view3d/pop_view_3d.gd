class_name PopView3D
extends Node3D
## Pop Voyage in 3D: the arena is a stage framed by carved pillars and a lintel, set before a landmark diorama (one per
## stage: a lighthouse, windmills, a desert arch, a temple, a glacier, a volcano, a harbour at night, the aurora).
## Balloons are glossy and squash on the floor; the wire rises with a glowing core; pops burst into rubber shards and
## confetti with a flash. The camera leans with the traveller, punches in on a big pop, shakes when he is caught and
## sweeps back when the stage is cleared. World = game units (x 0-16, y 0-10), the play plane at z = 0.

const P = preload("res://games/popvoyage/engine/pop_engine.gd")
const M := "res://games/popvoyage/art/models/"
const BACKDROP := "res://games/popvoyage/view3d/pop_backdrop.gd"
## balloon colours per size (smallest first), per stage in turn
const PALETTES := [
	[Color(1.0, 0.85, 0.2), Color(0.2, 0.75, 1.0), Color(1.0, 0.35, 0.3), Color(0.95, 0.3, 0.75)],
	[Color(0.4, 1.0, 0.5), Color(1.0, 0.6, 0.15), Color(0.35, 0.45, 1.0), Color(1.0, 0.3, 0.35)],
]
## fallback skies (the backdrop script gives the real ones): sky top, horizon, ground, sun colour, sun pitch/yaw
const SKIES := [
	[Color(0.3, 0.55, 0.95), Color(0.85, 0.92, 1.0), Color(0.3, 0.45, 0.55), Color(1.0, 0.96, 0.88), Vector2(-40, 30)],
	[Color(0.35, 0.6, 1.0), Color(0.9, 0.95, 1.0), Color(0.35, 0.55, 0.3), Color(1.0, 0.97, 0.9), Vector2(-60, 20)],
	[Color(0.35, 0.55, 0.9), Color(1.0, 0.85, 0.65), Color(0.8, 0.6, 0.4), Color(1.0, 0.85, 0.6), Vector2(-35, 40)],
	[Color(0.55, 0.65, 0.8), Color(0.95, 0.9, 0.9), Color(0.4, 0.5, 0.4), Color(1.0, 0.92, 0.85), Vector2(-30, -30)],
	[Color(0.25, 0.5, 0.95), Color(0.85, 0.95, 1.0), Color(0.7, 0.8, 0.9), Color(0.95, 0.97, 1.0), Vector2(-45, 25)],
	[Color(0.2, 0.12, 0.25), Color(0.95, 0.45, 0.25), Color(0.2, 0.12, 0.1), Color(1.0, 0.55, 0.3), Vector2(-12, 50)],
	[Color(0.03, 0.04, 0.12), Color(0.2, 0.15, 0.35), Color(0.05, 0.05, 0.1), Color(0.6, 0.65, 1.0), Vector2(-50, -40)],
	[Color(0.01, 0.03, 0.08), Color(0.1, 0.25, 0.3), Color(0.5, 0.6, 0.7), Color(0.6, 0.9, 0.8), Vector2(-40, 20)],
]

@export var game: PopGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sky: ProceduralSkyMaterial
var _sun: DirectionalLight3D
var _stage: Node3D
var _backdrop: Node3D
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _hero_last := ""
var _shield: MeshInstance3D
var _balls: Array[Node3D] = []
var _wires: Array[Node3D] = []
var _items: Array[Node3D] = []
var _blocks: Array[Node3D] = []
var _block_count := -1
var _ball_mats: Array[StandardMaterial3D] = []
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _sweep := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	_sky = ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = _sky
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.ambient_light_energy = 0.6
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.7
	_env.glow_bloom = 0.05
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_we = WorldEnvironment.new()
	_we.environment = _env
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 60.0
	_sun.light_energy = 1.2
	add_child(_sun)
	var rim := DirectionalLight3D.new()  # a soft light from behind the arena: glints on the balloons' edges
	rim.rotation_degrees = Vector3(-15, 180, 0)
	rim.light_energy = 0.35
	add_child(rim)
	camera = Camera3D.new()
	camera.fov = 36
	camera.far = 4000.0  # the backdrop's sky dome is 1500 away
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	for i in 4:
		var m := StandardMaterial3D.new()
		m.roughness = 0.12
		m.metallic = 0.0
		m.clearcoat_enabled = true
		m.clearcoat = 1.0
		m.clearcoat_roughness = 0.05
		m.rim_enabled = true
		m.rim = 0.6
		m.rim_tint = 0.3
		m.emission_enabled = true
		m.emission_energy_multiplier = 0.12
		_ball_mats.append(m)
	game.level_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mat(col: Color, rough := 0.5, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _box(size: Vector3, col: Color, rough := 0.6) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = _mat(col, rough)
	return mi


func _play(ap: AnimationPlayer, anim: String, loop := false, blend := 0.12) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, blend)


func _on_stage(e: PopEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_balls.clear()
	_wires.clear()
	_items.clear()
	_blocks.clear()
	_block_count = -1
	var th: int = e.stage.theme
	# the palette of this stage's balloons
	var pal: Array = PALETTES[game.index % PALETTES.size()]
	for i in 4:
		_ball_mats[i].albedo_color = pal[i]
		_ball_mats[i].emission = pal[i]
	_apply_sky(th)
	_build_backdrop(th)
	_build_frame(th)
	# the traveller
	_hero = Node3D.new()
	var body := _scene("traveller")
	if body == null:
		body = Node3D.new()
		var torso := _box(Vector3(0.5, 0.7, 0.3), Color(0.85, 0.7, 0.4))
		torso.position = Vector3(0, 0.75, 0)
		body.add_child(torso)
		var head := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.2
		sm.height = 0.4
		head.mesh = sm
		head.material_override = _mat(Color(1.0, 0.8, 0.65))
		head.position = Vector3(0, 1.2, 0)
		body.add_child(head)
		for sx in [-0.12, 0.12]:
			var leg := _box(Vector3(0.15, 0.4, 0.15), Color(0.35, 0.3, 0.25))
			leg.position = Vector3(sx, 0.2, 0)
			body.add_child(leg)
	body.name = "body"
	_hero.add_child(body)
	_hero_anim = body.find_child("AnimationPlayer", true, false)
	_hero_last = ""
	_shield = MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.95
	sph.height = 1.9
	_shield.mesh = sph
	var sm2 := StandardMaterial3D.new()
	sm2.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm2.albedo_color = Color(0.5, 0.9, 1.0, 0.18)
	sm2.emission_enabled = true
	sm2.emission = Color(0.4, 0.8, 1.0)
	sm2.emission_energy_multiplier = 0.6
	sm2.rim_enabled = true
	sm2.rim = 1.0
	sm2.cull_mode = BaseMaterial3D.CULL_DISABLED
	_shield.material_override = sm2
	_shield.position = Vector3(0, 0.7, 0)
	_shield.visible = false
	_hero.add_child(_shield)
	_stage.add_child(_hero)
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


func _apply_sky(th: int) -> void:
	var s: Array = SKIES[th % SKIES.size()]
	_sky.sky_top_color = s[0]
	_sky.sky_horizon_color = s[1]
	_sky.ground_horizon_color = s[1]
	_sky.ground_bottom_color = s[2]
	_sun.light_color = s[3]
	var rot: Vector2 = s[4]
	_sun.rotation_degrees = Vector3(rot.x, rot.y, 0)
	_env.fog_enabled = true
	_env.fog_light_color = s[1]
	_env.fog_density = 0.004
	var night := th in [6, 7]
	_sun.light_energy = 0.5 if night else 1.2
	_env.ambient_light_energy = 0.35 if night else 0.6


## The landmark diorama behind the arena, with its own sky, light, fog and grade.
func _build_backdrop(th: int) -> void:
	if ResourceLoader.exists(PopBackdrop.GLB % th):
		var bd := PopBackdrop.new()
		_stage.add_child(bd)
		bd.build(th)
		var d := bd.environment_for(th)
		_env = PopBackdrop.make_environment(d)
		_we.environment = _env
		PopBackdrop.setup_sun(_sun, d)
		_backdrop = bd
		return
	_backdrop = null
	# a plain ground
	var ground := _box(Vector3(200, 0.2, 120), (SKIES[th % SKIES.size()][2] as Color), 0.9)
	ground.position = Vector3(8, -0.1, -55)
	_stage.add_child(ground)


## The stage frame: a floor of boards, two carved pillars at the walls and a lintel across the top.
func _build_frame(th: int) -> void:
	var night := th in [6, 7]
	var wood := Color(0.93, 0.88, 0.78) if not night else Color(0.5, 0.48, 0.55)  # painted posts, not a heavy frame
	var trim := Color(0.95, 0.75, 0.35)
	if _backdrop == null:  # the backdrop brings its own foreground (boardwalk, path, quay...)
		var floor := _box(Vector3(17.2, 0.3, 2.6), wood.lightened(0.15), 0.7)
		floor.position = Vector3(8, -0.15, 0.2)
		_stage.add_child(floor)
	var lip := _box(Vector3(17.2, 0.06, 0.1), trim, 0.3)
	lip.position = Vector3(8, 0.0, 1.5)
	_stage.add_child(lip)
	for x in [-0.13, 16.13]:
		var pillar := _box(Vector3(0.26, 10.4, 0.26), wood, 0.4)
		pillar.position = Vector3(x, 5.3, 0)
		_stage.add_child(pillar)
		for y in [0.4, 10.2]:
			var cap := _box(Vector3(0.4, 0.16, 0.4), trim, 0.25)
			cap.position = Vector3(x, y, 0)
			_stage.add_child(cap)
		var inlay := _box(Vector3(0.05, 9.6, 0.02), trim, 0.25)
		inlay.position = Vector3(x, 5.2, 0.14)
		_stage.add_child(inlay)
	var lintel := _box(Vector3(16.9, 0.16, 0.2), trim, 0.25)
	lintel.position = Vector3(8, 10.3, 0)
	_stage.add_child(lintel)
	var band := _box(Vector3(16.9, 0.04, 0.02), wood, 0.3)
	band.position = Vector3(8, 10.3, 0.11)
	_stage.add_child(band)
	if night:
		for x in [-0.3, 16.3]:
			var l := OmniLight3D.new()  # lanterns on the pillars, so the arena is lit at night
			l.light_color = Color(1.0, 0.8, 0.5)
			l.light_energy = 2.0
			l.omni_range = 9.0
			l.position = Vector3(x + (0.6 if x < 8 else -0.6), 8.5, 1.2)
			_stage.add_child(l)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"split", "pop":
			var s: int = d["size"]
			var p: Vector2 = d["pos"]
			var col: Color = _ball_mats[s].albedo_color
			var at := Vector3(p.x, p.y, 0)
			_fx.burst(at, col, 14 + s * 8, 3.0 + s, 0.6, 0.12 + s * 0.03, 0.0, -9.0, 0.3)
			_fx.burst(at, Color.from_hsv(randf(), 0.6, 1.0), 10 + s * 4, 4.0, 0.9, 0.06, 1.0, -4.0, 1.0, "glow")
			_fx.flash(at + Vector3(0, -2.0, 2.0), col, 0.8 + s * 0.5)
			if s >= 2:
				_punch = 0.45
				_punch_at = at
				_shake = maxf(_shake, 0.15 * s)
		"block":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y, 0), Color(0.8, 0.7, 0.55), 30, 4.0, 0.9, 0.12, 0.0, -12.0, 0.5, "smoke")
			_shake = 0.3
		"item":
			var p: Vector2 = d["pos"]
			_fx.burst(Vector3(p.x, p.y, 0), Color(1.0, 0.95, 0.6), 12, 2.0, 0.5, 0.08, 1.0, -2.0, 1.0, "glow")
		"take":
			_fx.burst(_hero.position + Vector3(0, 0.8, 0.3), Color(1.0, 0.9, 0.4), 24, 3.0, 0.7, 0.09, 1.0, -2.0, 1.0, "glow")
		"shield_lost":
			_fx.burst(_hero.position + Vector3(0, 0.8, 0), Color(0.5, 0.9, 1.0), 40, 5.0, 0.6, 0.08, 1.0, 0.0, 1.0, "glow")
		"fire":
			_play(_hero_anim, "shoot", false, 0.05)
			_hero_last = "shoot"
		"die":
			_shake = 0.9
			_play(_hero_anim, "die")
			_hero_last = "die"
			_fx.burst(_hero.position + Vector3(0, 0.8, 0.3), Color(1.0, 0.9, 0.6), 30, 3.5, 0.8, 0.1, 1.0, -4.0, 1.0, "glow")
		"cleared":
			_sweep = 1.0
			_play(_hero_anim, "cheer", true)
			_hero_last = "cheer"
			for i in 6:
				_fx.burst(Vector3(2.0 + i * 2.4, 7.5 + (i % 2), -0.5), Color.from_hsv(i / 6.0, 0.7, 1.0), 26, 5.0, 1.3, 0.1, 1.0, -3.0, 1.0, "glow")


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	_place_hero(e, delta)
	_place_balls(e, delta)
	_place_wires(e)
	_place_items(e)
	_place_blocks(e)
	_shake = maxf(0.0, _shake - delta * 1.8)
	_punch = maxf(0.0, _punch - delta)
	_sweep = maxf(0.0, _sweep - delta / 3.5)
	_place_camera(delta)


func _place_hero(e: PopEngine, delta: float) -> void:
	var h := e.hero
	_hero.position = Vector3(h["x"], 0.0, 0.0)
	var moving := absf(float(h["vel"])) > 0.1
	var face := 0.0
	if e.phase == P.Phase.PLAY and moving:
		face = deg_to_rad(65.0) * float(h["facing"])
	_hero.rotation.y = lerp_angle(_hero.rotation.y, face, minf(1.0, delta * 12.0))
	_shield.visible = e.shield
	if e.shield:
		(_shield.material_override as StandardMaterial3D).albedo_color.a = 0.14 + 0.06 * sin(_time * 6.0)
	if e.phase == P.Phase.PLAY and not (_hero_last == "shoot" and _hero_anim and _hero_anim.is_playing()):
		var want := "run" if moving else "idle"
		if want != _hero_last:
			_hero_last = want
			_play(_hero_anim, want, true)
	elif e.phase == P.Phase.READY and _hero_last in ["die", "cheer", ""]:
		_hero_last = "idle"
		_play(_hero_anim, "idle", true)
	if _hero_anim and _hero_last == "run":
		_hero_anim.speed_scale = 1.0
	if _hero_anim == null:
		# the placeholder bobs as he runs
		_hero.get_node("body").position.y = absf(sin(_time * 14.0)) * 0.08 if moving else 0.0


func _ball_node(s: int) -> Node3D:
	var n := _scene("balloon_%d" % s)
	if n == null:
		n = Node3D.new()
		var mi := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = P.RADIUS[s]
		sm.height = P.RADIUS[s] * 2.0
		sm.radial_segments = 32
		sm.rings = 16
		mi.mesh = sm
		n.add_child(mi)
	for node in n.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi.mesh is SphereMesh:
			mi.material_override = _ball_mats[s]
			continue
		# tint the rubber, keep the painted sheen white
		for k in mi.mesh.get_surface_count():
			var sm: Material = mi.mesh.surface_get_material(k)
			if sm and sm.resource_name.begins_with("balloon") and not sm.resource_name.contains("sheen"):
				mi.set_surface_override_material(k, _ball_mats[s])
	n.set_meta("size", s)
	var l := OmniLight3D.new()  # a little light of its own colour on the scene around it
	l.light_color = _ball_mats[s].albedo_color
	l.light_energy = 0.25 + s * 0.1
	l.omni_range = 1.5 + s
	l.shadow_enabled = false
	n.add_child(l)
	return n


func _place_balls(e: PopEngine, delta: float) -> void:
	# one node per balloon, matched by size; rebuilt where sizes change
	while _balls.size() > e.balls.size():
		_balls.pop_back().queue_free()
	for i in e.balls.size():
		var b: Dictionary = e.balls[i]
		var s: int = b["size"]
		if i >= _balls.size():
			var n := _ball_node(s)
			_stage.add_child(n)
			_balls.append(n)
		elif int(_balls[i].get_meta("size")) != s:
			_balls[i].queue_free()
			_balls[i] = _ball_node(s)
			_stage.add_child(_balls[i])
		var n: Node3D = _balls[i]
		var p: Vector2 = b["pos"]
		var r: float = P.RADIUS[s]
		n.position = Vector3(p.x, p.y, 0)
		# squash as it meets the floor (or a block), stretch as it rises fast
		var low := clampf(1.0 - (p.y - r) / (r * 0.6), 0.0, 1.0)
		var v: Vector2 = b["vel"]
		var stretch := clampf(absf(v.y) / 25.0, 0.0, 0.12)
		var sy := 1.0 - low * 0.22 + stretch
		n.scale = Vector3(1.0 / sqrt(sy), sy, 1.0 / sqrt(sy))
		n.position.y -= (1.0 - sy) * r
		n.rotation.z = -p.x * 0.4 / maxf(r, 0.2)  # it rolls as it drifts
		if e.frozen > 0.0:
			n.position.x += sin(_time * 30.0 + i) * 0.02


func _place_wires(e: PopEngine) -> void:
	while _wires.size() > e.wires.size():
		_wires.pop_back().queue_free()
	while _wires.size() < e.wires.size():
		var n := Node3D.new()
		var line := MeshInstance3D.new()
		var cy := CylinderMesh.new()
		cy.top_radius = 0.035
		cy.bottom_radius = 0.035
		cy.height = 1.0
		cy.radial_segments = 8
		line.mesh = cy
		line.name = "line"
		line.material_override = _mat(Color(0.8, 0.95, 1.0), 0.2, 2.2)
		n.add_child(line)
		var tip := _scene("wire")
		if tip == null:
			tip = MeshInstance3D.new()
			var cone := CylinderMesh.new()
			cone.top_radius = 0.0
			cone.bottom_radius = 0.12
			cone.height = 0.3
			(tip as MeshInstance3D).mesh = cone
			(tip as MeshInstance3D).material_override = _mat(Color(0.9, 0.9, 1.0), 0.2, 0.8)
		tip.name = "tip"
		n.add_child(tip)
		var l := OmniLight3D.new()
		l.light_color = Color(0.6, 0.9, 1.0)
		l.light_energy = 0.8
		l.omni_range = 2.0
		l.name = "light"
		n.add_child(l)
		_stage.add_child(n)
		_wires.append(n)
	for i in e.wires.size():
		var w: Dictionary = e.wires[i]
		var n := _wires[i]
		var tip_y: float = w["tip"]
		n.position = Vector3(w["x"], 0.0, 0.05)
		var line: MeshInstance3D = n.get_node("line")
		line.scale = Vector3(1.0 + 0.3 * sin(_time * 40.0), tip_y, 1.0 + 0.3 * sin(_time * 40.0))
		line.position = Vector3(0, tip_y * 0.5, 0)
		(n.get_node("tip") as Node3D).position = Vector3(0, tip_y - (0.3 if _scene_has_tip() else 0.0), 0)
		(n.get_node("light") as Node3D).position = Vector3(0, tip_y, 0.3)
		var mat: StandardMaterial3D = line.material_override
		mat.emission = Color(1.0, 0.85, 0.4) if w["stuck"] else Color(0.6, 0.9, 1.0)


var _tip_checked := false
var _tip_model := false
func _scene_has_tip() -> bool:
	if not _tip_checked:
		_tip_checked = true
		_tip_model = ResourceLoader.exists(M + "wire.glb")
	return _tip_model


func _place_items(e: PopEngine) -> void:
	while _items.size() > e.items.size():
		_items.pop_back().queue_free()
	for i in e.items.size():
		var it: Dictionary = e.items[i]
		if i >= _items.size() or _items[i].get_meta("kind") != it["kind"]:
			var n := _scene("item_" + it["kind"])
			if n == null:
				n = MeshInstance3D.new()
				var sm := SphereMesh.new()
				sm.radius = 0.22
				sm.height = 0.44
				(n as MeshInstance3D).mesh = sm
				var col: Color = {"double": Color(0.5, 0.9, 1.0), "sticky": Color(0.6, 1.0, 0.4), "shield": Color(0.4, 0.7, 1.0),
					"clock": Color(1.0, 0.85, 0.3), "charge": Color(1.0, 0.4, 0.3)}[it["kind"]]
				(n as MeshInstance3D).material_override = _mat(col, 0.2, 1.0)
			n.set_meta("kind", it["kind"])
			if i < _items.size():
				_items[i].queue_free()
				_items[i] = n
			else:
				_items.append(n)
			_stage.add_child(n)
		var n2: Node3D = _items[i]
		var p: Vector2 = it["pos"]
		n2.position = Vector3(p.x, p.y - 0.3 + 0.08 * sin(_time * 4.0 + i), 0.2)
		n2.rotation.y = _time * 2.0
		# blinks before it goes
		n2.visible = it["t"] < 5.5 or fmod(_time, 0.2) < 0.12


func _place_blocks(e: PopEngine) -> void:
	if e.blocks.size() == _block_count:
		return
	_block_count = e.blocks.size()
	for b in _blocks:
		b.queue_free()
	_blocks.clear()
	for bl in e.blocks:
		var r: Rect2 = bl["rect"]
		var n := _scene("block_cracked" if bl["breakable"] else "block")
		if n == null:
			n = _box(Vector3.ONE, Color(0.75, 0.62, 0.45) if not bl["breakable"] else Color(0.6, 0.5, 0.42), 0.7)
		n.scale = Vector3(r.size.x, r.size.y, 0.9)
		n.position = Vector3(r.get_center().x, r.get_center().y, 0)
		_stage.add_child(n)
		_blocks.append(n)


## The camera frames the arena and its frame from in front, leaning with the traveller, drifting a little; a punch
## towards a big pop, a shake when he is caught, a sweep back and round when the stage is cleared.
func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(5.9, 9.2 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var hx: float = e.hero["x"] if e else 8.0
	var look := Vector3(8.0 + (hx - 8.0) * 0.12, 5.0, 0.0)
	var pos := look + Vector3(sin(_time * 0.13) * 0.6, 0.6 + sin(_time * 0.11) * 0.25, dist)
	if _punch > 0.0:
		var k := sin(_punch / 0.45 * PI) * 0.12
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + Vector3(0, 0, dist * 0.7), k)
	if _sweep > 0.0:
		var k := sin(_sweep * PI)
		pos += Vector3(sin((1.0 - _sweep) * PI) * 5.0, 1.5 * k, 3.0 * k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
