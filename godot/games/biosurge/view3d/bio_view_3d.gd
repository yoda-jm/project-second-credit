class_name BioView3D
extends Node3D
## Biosurge in 3D: the camera looks down on the cavern (BioWorld: living walls, a glowing abyss below) as it climbs.
## The ship banks into its turns, trails its engines and wears what it has bought (side pods, a rear gun, a drone);
## shots and enemy orbs are drawn in batches; the laser is a beam to the first wall; creatures pulse, turrets track the
## ship, worms snake out of the walls; hits flash, kills burst in light and spores; the boss looms at the end with its
## core glowing. World: engine (x, d) -> (x, 0, -d), the play plane at y = 0.

const B = preload("res://games/biosurge/engine/bio_engine.gd")
const M := "res://games/biosurge/art/models/"
const WORLD := "res://games/biosurge/view3d/bio_world.gd"
const SHOT_COL := Color(0.3, 1.0, 0.9)
const ORB_COL := Color(1.0, 0.45, 0.2)

@export var game: BioGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _stage: Node3D
var _world: Node3D
var _ship: Node3D
var _pods: Array[Node3D] = []
var _drone: Node3D
var _shield: MeshInstance3D
var _laser: MeshInstance3D
var _shots_mm: MultiMeshInstance3D
var _orbs_mm: MultiMeshInstance3D
var _foes := {}
var _drops := {}
var _boss: Node3D
var _fx: Bursts
var _trail: CPUParticles3D
var _time := 0.0
var _shake := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO


func _ready() -> void:
	_we = WorldEnvironment.new()
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	add_child(_sun)
	var key := DirectionalLight3D.new()   # a soft light on the craft and creatures only
	key.rotation_degrees = Vector3(-60, 20, 0)
	key.light_energy = 0.7
	key.light_cull_mask = 2
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 40
	camera.far = 600.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 14.0
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


func _play_layer(n: Node) -> void:
	for v in n.find_children("*", "VisualInstance3D", true, false):
		(v as VisualInstance3D).layers |= 2
	if n is VisualInstance3D:
		(n as VisualInstance3D).layers |= 2


static func w(p: Vector2) -> Vector3:
	return Vector3(p.x, 0.0, -p.y)


func _sphere(r: float, col: Color, emit := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = r
	sm.height = r * 2.0
	mi.mesh = sm
	mi.material_override = _mat(col, 0.4, 0.2, emit)
	return mi


# ------------------------------------------------------------------ a level

func _on_level(e: BioEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_foes.clear()
	_drops.clear()
	_boss = null
	var th := e.level % 5
	_world = null
	if ResourceLoader.exists(WORLD):
		_world = (load(WORLD) as GDScript).new()
		_stage.add_child(_world)
		_world.call("build", th, e.left, e.right, e.islands, e.length)
		var d: Dictionary = _world.call("environment_for", th)
		_env = _world.call("make_environment", d)
		_world.call("setup_sun", _sun, d)
	else:
		_env = Environment.new()
		_env.background_mode = Environment.BG_COLOR
		_env.background_color = Color(0.02, 0.05, 0.06)
		_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		_env.ambient_light_color = Color(0.4, 0.6, 0.6)
		_env.ambient_light_energy = 0.7
		_env.tonemap_mode = Environment.TONE_MAPPER_ACES
		_env.glow_enabled = true
		_sun.rotation_degrees = Vector3(-60, -30, 0)
		_fallback_walls(e)
	_we.environment = _env
	_build_ship(e)
	_shots_mm = _batch(QuadMesh.new(), _mat(SHOT_COL, 0.2, 0.0, 4.0), Vector2(0.18, 0.7))
	_orbs_mm = _batch(SphereMesh.new(), _mat(ORB_COL, 0.2, 0.0, 3.0), Vector2(0.32, 0.32))
	_laser = MeshInstance3D.new()
	var lm := BoxMesh.new()
	lm.size = Vector3(0.22, 0.12, 1.0)
	_laser.mesh = lm
	_laser.material_override = _mat(Color(0.6, 1.0, 1.0), 0.2, 0.0, 6.0)
	_laser.visible = false
	_stage.add_child(_laser)
	if _cam_pos == Vector3.ZERO:
		_place_camera(e, 1.0, true)


func _batch(mesh: Mesh, mat: Material, size: Vector2) -> MultiMeshInstance3D:
	if mesh is QuadMesh:
		(mesh as QuadMesh).size = size
		(mesh as QuadMesh).orientation = PlaneMesh.FACE_Y
	elif mesh is SphereMesh:
		(mesh as SphereMesh).radius = size.x * 0.5
		(mesh as SphereMesh).height = size.x
		(mesh as SphereMesh).radial_segments = 8
		(mesh as SphereMesh).rings = 4
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = 0
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage.add_child(mmi)
	return mmi


## Plain walls until the living ones exist.
func _fallback_walls(e: BioEngine) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in e.left.size() - 1:
		for side in [0, 1]:
			var x0: float = e.left[i] if side == 0 else e.right[i]
			var x1: float = e.left[i + 1] if side == 0 else e.right[i + 1]
			var out := -6.0 if side == 0 else B.W + 6.0
			for q in [[Vector3(out, 1.5, -i), Vector3(x0, 1.5, -i), Vector3(x1, 1.5, -i - 1), Vector3(out, 1.5, -i - 1)]]:
				for v in [q[0], q[1], q[2], q[0], q[2], q[3]]:
					st.add_vertex(v)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := _mat(Color(0.25, 0.5, 0.45), 0.6)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	_stage.add_child(mi)


func _build_ship(e: BioEngine) -> void:
	_ship = Node3D.new()
	var body := _scene("ship")
	if body == null:
		body = Node3D.new()
		var b := MeshInstance3D.new()
		var pm := PrismMesh.new()
		pm.size = Vector3(1.0, 0.3, 1.3)
		b.mesh = pm
		b.rotation.x = -PI * 0.5
		b.material_override = _mat(Color(0.75, 0.85, 0.9), 0.25, 0.8)
		body.add_child(b)
	body.name = "body"
	_ship.add_child(body)
	_pods.clear()
	for spec in [["pod_side", Vector3(-0.75, 0, 0.1), "side"], ["pod_side", Vector3(0.75, 0, 0.1), "side"], ["pod_rear", Vector3(0, 0, 0.6), "rear"]]:
		var pd := _scene(spec[0])
		if pd == null:
			pd = _sphere(0.18, Color(0.6, 0.9, 0.9), 0.5)
		pd.position = spec[1]
		pd.set_meta("needs", spec[2])
		body.add_child(pd)
		_pods.append(pd)
	_shield = _sphere(1.1, Color(0.4, 0.9, 1.0, 0.18), 0.6)
	var sm := _shield.material_override as StandardMaterial3D
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.rim_enabled = true
	sm.rim = 1.0
	_shield.visible = false
	_ship.add_child(_shield)
	var light := OmniLight3D.new()
	light.light_color = Color(0.4, 1.0, 0.9)
	light.light_energy = 1.4
	light.omni_range = 4.0
	light.position = Vector3(0, 1.0, 0.6)
	_ship.add_child(light)
	_trail = CPUParticles3D.new()
	_trail.amount = 50
	_trail.lifetime = 0.35
	_trail.local_coords = false
	_trail.direction = Vector3(0, 0, 1)
	_trail.spread = 10.0
	_trail.initial_velocity_min = 4.0
	_trail.initial_velocity_max = 6.0
	_trail.gravity = Vector3.ZERO
	_trail.scale_amount_min = 0.5
	_trail.scale_amount_max = 1.0
	var q := QuadMesh.new()
	q.size = Vector2(0.22, 0.22)
	_trail.mesh = q
	_trail.material_override = Fx.material("glow", Color(0.3, 0.9, 1.0))
	_ship.add_child(_trail)
	_trail.position = Vector3(0, 0, 0.7)
	_drone = _scene("drone")
	if _drone == null:
		_drone = _sphere(0.2, Color(0.5, 1.0, 0.8), 1.0)
	_stage.add_child(_drone)
	_play_layer(_ship)
	_play_layer(_drone)
	_stage.add_child(_ship)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"hit":
			var p := w(d["pos"]) + Vector3(0, 0.3, 0)
			_fx.burst(p, Color(0.8, 1.0, 0.7) if d["kind"] != "wall" else Color(0.6, 0.9, 0.9), 5, 2.5, 0.25, 0.06, 1.0, 0.0, 1.0, "glow")
		"kill":
			var p := w(d["pos"]) + Vector3(0, 0.3, 0)
			var big: bool = d["kind"] in ["pod", "turret", "crab"]
			_fx.burst(p, Color(1.0, 0.7, 0.3), 30 if big else 18, 5.0 if big else 3.5, 0.6, 0.1, 1.0, 0.0, 1.0, "glow")
			_fx.burst(p, Color(0.5, 0.9, 0.6), 14, 2.5, 0.8, 0.08, 1.0, 0.0, 1.0, "glow")
			_fx.flash(p, Color(1.0, 0.75, 0.4), 3.0 if big else 1.6)
			if _world and _world.has_method("flash"):
				_world.call("flash", p, Color(1.0, 0.7, 0.4))
			_shake = maxf(_shake, 0.25 if big else 0.1)
		"player_hit":
			_shake = maxf(_shake, 0.4)
			_fx.burst(_ship.position + Vector3(0, 0.3, 0), Color(1.0, 0.5, 0.3), 12, 3.0, 0.3, 0.07, 1.0, 0.0, 1.0, "glow")
		"die":
			var p := w(d["pos"]) + Vector3(0, 0.3, 0)
			_fx.burst(p, Color(1.0, 0.9, 0.6), 50, 6.0, 1.0, 0.12, 1.0, 0.0, 1.0, "glow")
			_fx.flash(p, Color(1.0, 0.8, 0.5), 5.0)
			_shake = 1.0
		"credit":
			var p := w(d["pos"]) + Vector3(0, 0.3, 0)
			_fx.burst(p, Color(1.0, 0.9, 0.3), 8, 2.0, 0.3, 0.05, 1.0, 0.0, 1.0, "glow")
		"boss_die":
			var p := w(d["pos"]) + Vector3(0, 1.0, 0)
			for k in 8:
				_fx.burst(p + Vector3(randf_range(-3, 3), 0, randf_range(-2, 2)), Color.from_hsv(0.05 + k * 0.03, 0.8, 1.0), 40, 7.0, 1.4, 0.16, 1.0, 0.0, 1.0, "glow")
			_fx.flash(p, Color(1, 0.9, 0.7), 10.0)
			_shake = 1.6
		"boss_hit":
			if _boss:
				_boss.set_meta("flash", 0.08)


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 1.8)
	var e := game.engine
	if e == null or _stage == null or _ship == null:
		return
	if _world and _world.has_method("update"):
		_world.call("update", camera.position.z, delta)
	_place_ship(e, delta)
	_place_shots(e)
	_place_foes(e, delta)
	_place_drops(e, delta)
	_place_boss(e, delta)
	_place_camera(e, delta)


func _place_ship(e: BioEngine, delta: float) -> void:
	_ship.position = w(e.ship["pos"])
	var body := _ship.get_node("body") as Node3D
	body.rotation.z = lerpf(body.rotation.z, float(e.ship["bank"]) * 1.2, minf(1.0, delta * 10.0))
	_ship.visible = e.phase != B.Phase.DYING and (e.ship["hurt"] <= 0.0 or fmod(_time, 0.1) < 0.06)
	for pd in _pods:
		pd.visible = bool(e.loadout[pd.get_meta("needs")])
	_shield.visible = e.shield > 0.0
	_shield.scale = Vector3.ONE * (1.0 + 0.05 * sin(_time * 10.0))
	_drone.visible = bool(e.loadout["drone"]) and _ship.visible
	_drone.position = w(e.drone_pos())
	_drone.rotation.y += delta * 4.0
	# the laser
	var on: bool = e.firing and e.loadout["laser"] and e.phase in [B.Phase.PLAY, B.Phase.BOSS]
	_laser.visible = on
	if on:
		var reach := e.laser_reach()
		_laser.position = _ship.position + Vector3(0, 0.1, -0.6 - reach * 0.5)
		_laser.scale = Vector3(1.0 + 0.2 * sin(_time * 40.0), 1.0, reach)


func _place_shots(e: BioEngine) -> void:
	var mm := _shots_mm.multimesh
	mm.instance_count = e.shots.size()
	for i in e.shots.size():
		var s: Dictionary = e.shots[i]
		var v: Vector2 = s["vel"]
		var t := Transform3D(Basis(Vector3.UP, atan2(v.x, v.y)), w(s["pos"]) + Vector3(0, 0.25, 0))
		if s["kind"] == "homing":
			t = t.scaled_local(Vector3(1.6, 1, 0.7))
		mm.set_instance_transform(i, t)
	var om := _orbs_mm.multimesh
	om.instance_count = e.bullets.size()
	var pulse := 1.0 + 0.2 * sin(_time * 18.0)
	for i in e.bullets.size():
		om.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ONE * pulse), w(e.bullets[i]["pos"]) + Vector3(0, 0.25, 0)))


func _place_foes(e: BioEngine, delta: float) -> void:
	var live := {}
	for f in e.foes:
		var id: int = f["id"]
		live[id] = true
		if not _foes.has(id):
			var model: String = f["kind"]
			if model == "worm":
				model = "worm_head" if f.get("lead", false) else "worm_seg"
			var n := _scene(model)
			if n == null:
				n = _sphere(B.RADIUS[f["kind"]], Color(0.6, 0.9, 0.5), 0.4)
			_play_layer(n)
			var ap := n.find_child("AnimationPlayer", true, false) as AnimationPlayer
			if ap and ap.get_animation_list().size() > 0:
				var an: String = ap.get_animation_list()[0]
				ap.get_animation(an).loop_mode = Animation.LOOP_LINEAR
				ap.play(an)
			_stage.add_child(n)
			_foes[id] = n
		var n: Node3D = _foes[id]
		if f["dead"]:
			n.visible = false
			continue
		n.position = w(f["pos"])
		match f["kind"]:
			"spinner":
				n.rotation.y += delta * 6.0
			"turret":
				var head := n.find_child("head", true, false) as Node3D
				var to: Vector2 = (e.ship["pos"] as Vector2) - f["pos"]
				if head:
					head.rotation.y = atan2(-to.x, to.y) + PI
			"dart":
				var v: Vector2 = f["vel"]
				if v.length() > 0.1:
					n.rotation.y = atan2(-v.x, -v.y) + PI
			"pod":
				n.scale = Vector3.ONE * (1.0 + 0.06 * sin(_time * 5.0 + id))
			"crab":
				n.rotation.y = PI * 0.5 * float(f.get("side", 1.0))
		if f["flash"] > 0.0:
			n.scale = Vector3.ONE * 1.15
		elif f["kind"] != "pod":
			n.scale = n.scale.lerp(Vector3.ONE, minf(1.0, delta * 10.0))
	for id in _foes.keys():
		if not live.has(id):
			(_foes[id] as Node3D).queue_free()
			_foes.erase(id)


func _place_drops(e: BioEngine, delta: float) -> void:
	var live := {}
	for dr in e.drops:
		var key := int(dr.get("vid", 0))
		if key == 0:
			dr["vid"] = randi() % 1000000 + 1
			key = dr["vid"]
		live[key] = true
		if not _drops.has(key):
			var model: String = "credit" if dr["kind"] == "credit" else "power_" + str(dr["kind"])
			var n := _scene(model)
			if n == null:
				n = _sphere(0.25, Color(1.0, 0.85, 0.3) if dr["kind"] == "credit" else Color(0.4, 0.8, 1.0), 2.0)
			_play_layer(n)
			_stage.add_child(n)
			_drops[key] = n
		var n: Node3D = _drops[key]
		n.position = w(dr["pos"]) + Vector3(0, 0.3 + 0.1 * sin(_time * 4.0 + key), 0)
		n.rotation.y += delta * 3.0
	for key in _drops.keys():
		if not live.has(key):
			(_drops[key] as Node3D).queue_free()
			_drops.erase(key)


func _place_boss(e: BioEngine, delta: float) -> void:
	if e.boss.is_empty():
		return
	if _boss == null:
		_boss = _scene("boss_%d" % (e.level % 5 + 1))
		if _boss == null:
			_boss = _sphere(3.0, Color(0.6, 0.2, 0.3), 0.3)
		_play_layer(_boss)
		_stage.add_child(_boss)
		_boss.position = w(e.boss["pos"]) + Vector3(0, 0, -6.0)
	var dead: bool = e.boss["hp"] <= 0.0
	_boss.visible = not dead
	_boss.position = _boss.position.lerp(w(e.boss["pos"]), minf(1.0, delta * 2.0))
	var t: float = e.boss["t"]
	for part in ["jaw_l", "arm_l"]:
		var p := _boss.find_child(part, true, false) as Node3D
		if p:
			p.rotation.y = sin(t * 2.0) * 0.25
	for part in ["jaw_r", "arm_r"]:
		var p := _boss.find_child(part, true, false) as Node3D
		if p:
			p.rotation.y = -sin(t * 2.0) * 0.25
	var fl: float = _boss.get_meta("flash", 0.0)
	_boss.set_meta("flash", maxf(0.0, fl - delta))
	var core := _boss.find_child("core", true, false) as Node3D
	if core:
		core.scale = Vector3.ONE * (1.0 + 0.08 * sin(t * 6.0) + (0.15 if fl > 0.0 else 0.0))


func _place_camera(e: BioEngine, delta: float, snap := false) -> void:
	var mid := e.scroll + B.SCREEN * 0.5
	var sx: float = (e.ship["pos"].x - B.W * 0.5) * 0.12
	var look := Vector3(B.W * 0.5 + sx, 0.0, -mid)
	var pos := look + Vector3(0, 25.0, 6.5)
	var j := Vector3(sin(_time * 47.0), 0, cos(_time * 41.0)) * _shake * _shake * (0.4 if Settings.camera_shake else 0.0)
	var k := 1.0 if snap else minf(1.0, delta * 6.0)
	_cam_pos = _cam_pos.lerp(pos, k)
	_cam_look = _cam_look.lerp(look, k)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.FORWARD)
