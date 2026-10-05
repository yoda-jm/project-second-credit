class_name TunnelView3D
extends Node3D
## Tunnel Pop in 3D: a slab of earth cut open in front of a garden under the sky; the tunnels are carved out of it at
## a quarter of a cell (round-cornered, with walls and a dark back), the face shows the four layers, the hero's lamp
## lights the tunnel round him. Creatures walk the tunnels, drift through the earth as eyes, swell as they are pumped
## and burst in confetti; drakes breathe fire through the earth; rocks wobble, fall and crumble; the vegetable glows
## in the middle. World: x = the column, y = minus the row (row 1, the surface lane, at y = -1), the play plane z = 0.

const D = preload("res://games/tunnelpop/engine/pop_dig_engine.gd")
const M := "res://games/tunnelpop/art/models/"
const EARTH_SHADER := preload("res://games/tunnelpop/shaders/tunnel_earth.gdshader")
const TURN := 0.52                ## characters turn this far towards the camera
const S := 4                      ## sub-cells per cell for the carving
const R := 0.44                   ## a tunnel's half width
const FRONT := 0.5
const BACK := -0.5
## layer colours per level (cycling): top to bottom
const PALETTES := [
	[Color(0.88, 0.66, 0.32), Color(0.8, 0.46, 0.22), Color(0.62, 0.3, 0.2), Color(0.42, 0.2, 0.26)],
	[Color(0.75, 0.72, 0.4), Color(0.55, 0.62, 0.32), Color(0.38, 0.45, 0.3), Color(0.25, 0.3, 0.32)],
	[Color(0.8, 0.55, 0.6), Color(0.62, 0.4, 0.55), Color(0.45, 0.3, 0.5), Color(0.28, 0.22, 0.42)],
	[Color(0.62, 0.7, 0.78), Color(0.45, 0.55, 0.68), Color(0.32, 0.4, 0.58), Color(0.2, 0.25, 0.42)],
]
const VEG := ["veg_carrot", "veg_turnip", "veg_mushroom", "veg_pepper", "veg_pumpkin", "veg_eggplant", "veg_pineapple", "veg_melon"]

@export var game: TunnelGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _stage: Node3D
var _earth: MeshInstance3D
var _earth_mat: ShaderMaterial
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _hero_last := ""
var _lamp: OmniLight3D
var _hose: MeshInstance3D
var _foes := {}                   ## id -> {node, anim, last}
var _rocks := {}                  ## id -> node
var _veg: Node3D
var _fires: Array = []
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _punch_at := Vector3.ZERO
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _dirty := true
var _last_hero := Vector2(-9, -9)


func _ready() -> void:
	_we = WorldEnvironment.new()
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.35, 0.6, 0.95)
	sm.sky_horizon_color = Color(0.85, 0.92, 1.0)
	sm.ground_horizon_color = Color(0.6, 0.7, 0.5)
	sm.ground_bottom_color = Color(0.3, 0.35, 0.25)
	sky.sky_material = sm
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.ambient_light_energy = 0.55
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.7
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.12
	_we.environment = _env
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-40, -25, 0)
	_sun.light_energy = 1.25
	_sun.light_color = Color(1.0, 0.95, 0.85)
	_sun.shadow_enabled = true
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 36
	camera.far = 600.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	_fx.size_unit = 22.0
	add_child(_fx)
	_earth_mat = ShaderMaterial.new()
	_earth_mat.shader = EARTH_SHADER
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


func _play(ap: AnimationPlayer, anim: String, loop := true, blend := 0.12) -> void:
	if ap and ap.has_animation(anim):
		ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		ap.play(anim, blend)


static func world(p: Vector2) -> Vector3:
	return Vector3(p.x, -p.y, 0.0)


# ------------------------------------------------------------------ a level

func _on_level(e: DigEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_foes.clear()
	_rocks.clear()
	_fires.clear()
	_veg = null
	var pal: Array = PALETTES[e.level % PALETTES.size()]
	for i in 4:
		_earth_mat.set_shader_parameter("layer%d" % i, pal[i])
	_earth = MeshInstance3D.new()
	_earth.material_override = _earth_mat
	_stage.add_child(_earth)
	_dirty = true
	_build_surface(e)
	_build_frame()
	# the hero, his lamp and his hose
	_hero = Node3D.new()
	var body := _scene("digger")
	if body == null:
		body = Node3D.new()
		var b := MeshInstance3D.new()
		var cap := CapsuleMesh.new()
		cap.radius = 0.25
		cap.height = 0.8
		b.mesh = cap
		b.material_override = _mat(Color(0.3, 0.5, 0.95), 0.4)
		b.position.y = 0.4
		body.add_child(b)
	body.name = "body"
	_hero.add_child(body)
	_hero_anim = body.find_child("AnimationPlayer", true, false)
	_hero_last = ""
	_stage.add_child(_hero)
	_lamp = OmniLight3D.new()
	_lamp.light_color = Color(1.0, 0.85, 0.6)
	_lamp.light_energy = 1.6
	_lamp.omni_range = 3.2
	_lamp.position = Vector3(0, 0.6, 0.6)
	_hero.add_child(_lamp)
	_hose = MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.035
	cyl.bottom_radius = 0.035
	cyl.height = 1.0
	_hose.mesh = cyl
	_hose.material_override = _mat(Color(0.9, 0.85, 0.75), 0.4, 0.3)
	_hose.visible = false
	_stage.add_child(_hose)
	for rk in e.rocks:
		var n := _scene("rock")
		if n == null:
			n = MeshInstance3D.new()
			var sp := SphereMesh.new()
			sp.radius = 0.45
			sp.height = 0.85
			(n as MeshInstance3D).mesh = sp
			(n as MeshInstance3D).material_override = _mat(Color(0.55, 0.5, 0.48), 0.8)
		var crack := n.find_child("crack", true, false) as Node3D
		if crack:
			crack.visible = false   # shown while the rock wobbles
		_stage.add_child(n)
		_rocks[rk["id"]] = n
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


## The garden above: a grass strip on the earth's top, flowers, a fence, a shed, sunflowers counting the levels.
func _build_surface(e: DigEngine) -> void:
	var grass := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(D.COLS + 30.0, 0.18, 6.0)
	grass.mesh = bm
	grass.material_override = Pbr.material("grass_lush", Color(0.8, 1.0, 0.6), 0.25)
	grass.position = Vector3(D.COLS * 0.5 - 0.5, -1.55, -2.5)
	_stage.add_child(grass)
	var far := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(200, 120)
	far.mesh = pm
	far.material_override = Pbr.material("grass", Color(0.75, 0.95, 0.55), 0.05)
	far.position = Vector3(6.5, -1.6, -60)
	_stage.add_child(far)
	var rng := RandomNumberGenerator.new()
	rng.seed = 77 + e.level
	var kinds := ["flower_a", "flower_b", "bush", "flower_a", "flower_b"]
	var x := -12.0
	while x < D.COLS + 12.0:
		var k: String = kinds[rng.randi() % kinds.size()]
		var n := _scene(k)
		if n:
			n.position = Vector3(x + rng.randf_range(-0.3, 0.3), -1.46, rng.randf_range(-4.5, -1.2))
			n.rotation.y = rng.randf() * TAU
			_stage.add_child(n)
		x += rng.randf_range(0.9, 1.8)
	for spec in [["fence", Vector3(-3.0, -1.46, -1.4)], ["fence", Vector3(-5.0, -1.46, -1.4)], ["shed", Vector3(D.COLS + 2.5, -1.46, -3.0)],
			["signpost", Vector3(-1.4, -1.46, -0.9)], ["wheelbarrow", Vector3(D.COLS + 0.5, -1.46, -1.6)]]:
		var n := _scene(spec[0])
		if n:
			n.position = spec[1]
			_stage.add_child(n)
	# a sunflower for each level reached, in a row at the right
	for i in mini(e.level + 1, 10):
		var n := _scene("level_flower")
		if n:
			n.position = Vector3(D.COLS - 0.5 - i * 0.7, -1.46, -0.7)
			n.scale = Vector3.ONE * 0.8
			_stage.add_child(n)
	# the earth runs on beyond the field to either side (not to be dug: the frame marks the field)
	for side in [-1.0, 1.0]:
		var slab := MeshInstance3D.new()
		var b2 := BoxMesh.new()
		b2.size = Vector3(30.0, float(D.ROWS) + 2.0, 1.0)
		slab.mesh = b2
		slab.material_override = _earth_mat
		slab.position = Vector3((D.COLS * 0.5 - 0.5) + side * (D.COLS * 0.5 + 15.0), -1.5 - (float(D.ROWS) + 2.0) * 0.5, 0.0)
		_stage.add_child(slab)
	# and on below it
	var under := MeshInstance3D.new()
	var b3 := BoxMesh.new()
	b3.size = Vector3(D.COLS + 2.0, 12.0, 1.0)
	under.mesh = b3
	under.material_override = _earth_mat
	under.position = Vector3(D.COLS * 0.5 - 0.5, -float(D.ROWS) + 0.5 - 6.0, 0.0)
	_stage.add_child(under)
	# trees along the far edge of the garden
	var z := -9.0
	var tx := -24.0
	while tx < D.COLS + 24.0:
		var n := _scene("bush")
		if n:
			n.position = Vector3(tx, -1.55, z + rng.randf_range(-3.0, 0.0))
			n.scale = Vector3.ONE * rng.randf_range(1.8, 3.2)
			_stage.add_child(n)
		tx += rng.randf_range(2.0, 4.0)


## A wooden frame round the earth's face, like a cut-away display.
func _build_frame() -> void:
	var wood := Pbr.material("planks", Color(0.6, 0.45, 0.32), 0.5)
	var w := float(D.COLS)
	var top := -1.5
	var bottom := -float(D.ROWS) + 0.5
	for spec in [[Vector3(w * 0.5 - 0.5, bottom - 0.25, 0.3), Vector3(w + 1.0, 0.5, 1.0)], [Vector3(-0.75, (top + bottom) * 0.5 - 0.1, 0.3), Vector3(0.5, top - bottom + 0.7, 1.0)],
			[Vector3(w - 0.25, (top + bottom) * 0.5 - 0.1, 0.3), Vector3(0.5, top - bottom + 0.7, 1.0)]]:
		var mi := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = spec[1]
		mi.mesh = b
		mi.material_override = wood
		mi.position = spec[0]
		_stage.add_child(mi)


# ------------------------------------------------------------------ the earth

## Whether the point (engine coordinates) is carved: a dug cell's rounded square, a dug link's corridor, or round the
## hero where he is digging.
func _carved(e: DigEngine, x: float, y: float) -> bool:
	var c := Vector2i(roundi(x), roundi(y))
	var dx := absf(x - c.x)
	var dy := absf(y - c.y)
	if e.is_open(c) and dx < R and dy < R and (dx * dx + dy * dy) < R * R * 1.5:
		return true
	if dy < R:
		var a := Vector2i(floori(x), c.y)
		if e.linked(a, a + Vector2i(1, 0)):
			return true
	if dx < R:
		var a := Vector2i(c.x, floori(y))
		if e.linked(a, a + Vector2i(0, 1)):
			return true
	var hp: Vector2 = e.hero["pos"]
	if Vector2(x, y).distance_to(hp) < R * 1.02:
		return true
	# the stretch he is digging now, back to the last centre
	var back := Vector2(roundf(hp.x), roundf(hp.y))
	if hp.distance_to(back) > 0.01:
		var seg := hp - back
		var t := clampf((Vector2(x, y) - back).dot(seg) / seg.length_squared(), 0.0, 1.0)
		if (back + seg * t).distance_to(Vector2(x, y)) < R:
			return true
	return false


func _build_earth(e: DigEngine) -> void:
	var w := D.COLS * S
	var h := (D.ROWS - 2) * S
	var carved := PackedByteArray()
	carved.resize(w * h)
	for j in h:
		for i in w:
			var x := -0.5 + (i + 0.5) / S
			var y := 1.5 + (j + 0.5) / S
			carved[j * w + i] = 1 if _carved(e, x, y) else 0
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var cs := 1.0 / S
	for j in h:
		var y0 := -(1.5 + j * cs)
		var y1 := y0 - cs
		var i := 0
		while i < w:
			var solid := carved[j * w + i] == 0
			var k := i
			while k < w and (carved[j * w + k] == 0) == solid:
				k += 1
			var x0 := -0.5 + i * cs
			var x1 := -0.5 + k * cs
			if solid:
				# the face
				_quad(st, Vector3(x0, y0, FRONT), Vector3(x1, y0, FRONT), Vector3(x1, y1, FRONT), Vector3(x0, y1, FRONT), Vector3(0, 0, 1), 1.0)
			else:
				# the tunnel's back
				_quad(st, Vector3(x0, y0, BACK), Vector3(x1, y0, BACK), Vector3(x1, y1, BACK), Vector3(x0, y1, BACK), Vector3(0, 0, 1), 0.0)
			i = k
	# the tunnels' walls: where earth meets air, a face from front to back, facing the air
	for j in h:
		for i in w:
			if carved[j * w + i] == 0:
				continue
			var x0 := -0.5 + i * cs
			var y0 := -(1.5 + j * cs)
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var ni: int = i + d.x
				var nj: int = j + d.y
				var wall: bool = nj >= 0 and nj < h and ni >= 0 and ni < w and carved[nj * w + ni] == 0
				if not wall:
					continue
				var nrm := Vector3(-d.x, d.y, 0)
				var a: Vector3
				var b: Vector3
				match d:
					Vector2i(1, 0): a = Vector3(x0 + cs, y0, 0); b = Vector3(x0 + cs, y0 - cs, 0)
					Vector2i(-1, 0): a = Vector3(x0, y0 - cs, 0); b = Vector3(x0, y0, 0)
					Vector2i(0, 1): a = Vector3(x0 + cs, y0 - cs, 0); b = Vector3(x0, y0 - cs, 0)
					_: a = Vector3(x0, y0, 0); b = Vector3(x0 + cs, y0, 0)
				_quad(st, Vector3(a.x, a.y, FRONT), Vector3(b.x, b.y, FRONT), Vector3(b.x, b.y, BACK), Vector3(a.x, a.y, BACK), nrm, 0.0)
	_earth.mesh = st.commit()


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3, face: float) -> void:
	var col := Color(face, 0, 0)
	for v in [a, b, c, a, c, d]:
		st.set_color(col)
		st.set_normal(n)
		st.add_vertex(v)


# ------------------------------------------------------------------ events

func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"dig":
			_dirty = true
			var c: Vector2i = d["cell"]
			_fx.burst(world(Vector2(c)) + Vector3(0, 0, 0.4), (PALETTES[e.level % 4][D.layer_of(c.y)] as Color), 6, 1.5, 0.4, 0.06, 0.0, -6.0, 0.5)
		"pump":
			var n: Dictionary = _foes.get(d["id"], {})
			if not n.is_empty():
				(n["node"] as Node3D).set_meta("squish", 1.0)
		"pop":
			var p := world(d["pos"]) + Vector3(0, 0.1, 0.3)
			for k in 4:
				_fx.burst(p, Color.from_hsv(randf(), 0.7, 1.0), 14, 4.0, 0.7, 0.07, 1.0, -6.0, 1.0, "glow")
			_fx.burst(p, Color(1, 1, 1), 20, 2.0, 0.4, 0.1, 1.0, 0.0, 1.0, "glow")
			_fx.flash(p, Color(1.0, 0.9, 0.7), 2.5)
			_shake = maxf(_shake, 0.3)
			_punch = 0.5
			_punch_at = p
		"crush":
			var p := world(d["pos"])
			_fx.burst(p, Color(0.75, 0.65, 0.5), 30, 3.0, 0.8, 0.2, 0.0, -2.0, 1.0, "smoke")
			_shake = maxf(_shake, 0.5)
		"land":
			var rk := _rock(d["rock"])
			if not rk.is_empty():
				var p := world(Vector2(rk["cell"])) + Vector3(0, -0.3, 0.3)
				_fx.burst(p, Color(0.7, 0.6, 0.5), 26, 3.0, 0.9, 0.18, 0.0, -1.0, 1.0, "smoke")
				_fx.burst(p, Color(0.5, 0.45, 0.4), 16, 4.0, 0.7, 0.1, 0.0, -14.0, 1.0)
				_shake = maxf(_shake, 0.45)
		"fire":
			var a := world(d["from"])
			var b := world(d["to"])
			var fire := CPUParticles3D.new()
			fire.amount = 70
			fire.lifetime = 0.45
			fire.one_shot = false
			fire.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
			fire.emission_box_extents = Vector3(absf(b.x - a.x) * 0.5, 0.18, 0.15)
			fire.position = (a + b) * 0.5 + Vector3(0, 0, 0.5)
			fire.direction = Vector3(signf(b.x - a.x), 0.3, 0)
			fire.initial_velocity_min = 0.5
			fire.initial_velocity_max = 2.0
			fire.gravity = Vector3(0, 1.5, 0)
			fire.scale_amount_min = 0.6
			fire.scale_amount_max = 1.4
			var q := QuadMesh.new()
			q.size = Vector2(0.35, 0.35)
			fire.mesh = q
			fire.material_override = Fx.material("glow", Color(1.0, 0.5, 0.15))
			_stage.add_child(fire)
			var fl := OmniLight3D.new()
			fl.light_color = Color(1.0, 0.5, 0.2)
			fl.light_energy = 3.0
			fl.omni_range = 3.0
			fl.position = fire.position
			_stage.add_child(fl)
			_fires.append([fire, fl, 0.55])
		"veg":
			_veg = _scene(VEG[mini(e.level, VEG.size() - 1)])
			if _veg == null:
				_veg = MeshInstance3D.new()
				var sp := SphereMesh.new()
				sp.radius = 0.3
				sp.height = 0.6
				(_veg as MeshInstance3D).mesh = sp
				(_veg as MeshInstance3D).material_override = _mat(Color(1.0, 0.5, 0.1), 0.3, 0.0, 0.5)
			_veg.position = world(d["pos"]) + Vector3(0, -0.4, 0.1)
			_veg.set_meta("base_y", _veg.position.y)
			_stage.add_child(_veg)
			_fx.burst(_veg.position + Vector3(0, 0.3, 0.3), Color(1.0, 0.9, 0.4), 30, 2.5, 0.8, 0.07, 1.0, -2.0, 1.0, "glow")
		"veg_take":
			if _veg:
				_fx.burst(_veg.position + Vector3(0, 0.3, 0.3), Color(1.0, 0.85, 0.3), 40, 3.5, 0.9, 0.08, 1.0, -3.0, 1.0, "glow")
				_veg.queue_free()
				_veg = null
		"die":
			_shake = 0.6
			_play(_hero_anim, "die", false)
			_hero_last = "die"
		"cleared":
			_play(_hero_anim, "cheer", true)
			_hero_last = "cheer"


func _rock(id: int) -> Dictionary:
	for rk in game.engine.rocks:
		if rk["id"] == id:
			return rk
	return {}


# ------------------------------------------------------------------ every frame

func _process(delta: float) -> void:
	_time += delta
	_shake = maxf(0.0, _shake - delta * 1.6)
	_punch = maxf(0.0, _punch - delta)
	var e := game.engine
	if e == null or _stage == null:
		return
	var hp: Vector2 = e.hero["pos"]
	if _dirty or (e.hero["digging"] and hp.distance_to(_last_hero) > 0.06):
		_build_earth(e)
		_dirty = false
		_last_hero = hp
	_place_hero(e, delta)
	_place_hose(e)
	_place_foes(e, delta)
	_place_rocks(e)
	if _veg:
		_veg.rotation.y += delta * 1.5
		_veg.position.y = float(_veg.get_meta("base_y", _veg.position.y)) + 0.06 * sin(_time * 3.0)
	for f in _fires:
		f[2] -= delta
		if f[2] <= 0.0:
			(f[0] as CPUParticles3D).emitting = false
			(f[1] as OmniLight3D).light_energy = maxf(0.0, (f[1] as OmniLight3D).light_energy - delta * 10.0)
	for f in _fires.filter(func(f): return f[2] < -1.0):
		(f[0] as Node).queue_free()
		(f[1] as Node).queue_free()
	_fires = _fires.filter(func(f): return f[2] >= -1.0)
	_place_camera(delta)


func _place_hero(e: DigEngine, delta: float) -> void:
	var hp: Vector2 = e.hero["pos"]
	_hero.position = world(hp) + Vector3(0, -0.43, 0.05)
	var face: int = e.hero["face"]
	# a three-quarter turn towards the camera, so both eyes show
	_hero.rotation.y = lerp_angle(_hero.rotation.y, -TURN if face == 0 else PI + TURN, minf(1.0, delta * 14.0))
	_hero.visible = not (e.phase == D.Phase.READY and fmod(_time, 0.3) < 0.1 and e.time > 0.5)
	var want := "idle"
	if e.phase == D.Phase.DYING:
		want = "die"
	elif e.phase == D.Phase.CLEARED:
		want = "cheer"
	elif not e.hose.is_empty() and e.hose["id"] >= 0:
		want = "pump"
	elif e.hero["moving"]:
		var d: Vector2i = D.DIRS[e.hero["dir"]]
		want = "dig" if e.hero["digging"] else ("climb" if d.y != 0 else "walk")
	if want != _hero_last:
		_hero_last = want
		_play(_hero_anim, want, want != "die")
	if want == "pump" and _hero_anim and not _hero_anim.is_playing():
		_hero_anim.play("pump")


func _place_hose(e: DigEngine) -> void:
	if e.hose.is_empty():
		_hose.visible = false
		return
	var d: Vector2i = D.DIRS[e.hose["dir"]]
	var len: float = e.hose["len"] * clampf(e.hose["t"] / 0.08, 0.0, 1.0) if e.hose["id"] < 0 else e.hose["len"]
	if len < 0.05:
		_hose.visible = false
		return
	_hose.visible = true
	var a := world(e.hero["pos"]) + Vector3(0, -0.14, 0.1) + Vector3(d.x, -d.y, 0) * 0.3   # from the nozzle
	var dir := Vector3(d.x, -d.y, 0)
	_hose.position = a + dir * (len * 0.5)
	_hose.basis = Basis(Quaternion(Vector3.UP, dir)) * Basis.from_scale(Vector3(1, len, 1))


func _place_foes(e: DigEngine, delta: float) -> void:
	for f in e.foes:
		var id: int = f["id"]
		if not _foes.has(id):
			var n := _scene(f["kind"])
			if n == null:
				n = MeshInstance3D.new()
				var sp := SphereMesh.new()
				sp.radius = 0.35
				sp.height = 0.7
				(n as MeshInstance3D).mesh = sp
				(n as MeshInstance3D).material_override = _mat(Color(1.0, 0.4, 0.3) if f["kind"] == "puffer" else Color(0.3, 0.8, 0.3), 0.4)
			_stage.add_child(n)
			_foes[id] = {"node": n, "anim": n.find_child("AnimationPlayer", true, false), "last": ""}
		var rec: Dictionary = _foes[id]
		var n: Node3D = rec["node"]
		if f["dead"]:
			if n.visible:
				n.visible = false
			continue
		n.position = world(f["pos"]) + Vector3(0, -0.43, 0.0)
		n.rotation.y = lerp_angle(n.rotation.y, -TURN if f["dir"] == 0 else PI + TURN, minf(1.0, delta * 10.0))
		var puff: float = f["puff"]
		var sq: float = n.get_meta("squish", 0.0)
		n.set_meta("squish", maxf(0.0, sq - delta * 6.0))
		var s := 1.0 + puff * 0.28 + sq * 0.12
		n.scale = n.scale.lerp(Vector3(s, s * (1.0 - sq * 0.08), s), minf(1.0, delta * 14.0))
		var body := n.find_child("body", true, false) as Node3D
		if body:
			body.visible = not f["ghost"]
		elif f["ghost"]:
			n.scale = Vector3.ONE * 0.6
		var want := "ghost" if f["ghost"] else ("stunned" if puff > 0.0 else ("breathe" if f["breath"] > 0.0 else "walk"))
		if want != rec["last"]:
			rec["last"] = want
			_play(rec["anim"], want, want != "breathe")


func _place_rocks(e: DigEngine) -> void:
	for rk in e.rocks:
		var n: Node3D = _rocks.get(rk["id"])
		if n == null:
			continue
		var c: Vector2i = rk["cell"]
		var p := Vector3(c.x, -float(rk["y"]) - 0.45, 0.32)   # half sunk in the face, like a boulder in a cutting
		match rk["state"]:
			"wobble":
				p.x += sin(_time * 40.0) * 0.05
				n.rotation.z = sin(_time * 30.0) * 0.06
				var cr := n.find_child("crack", true, false) as Node3D
				if cr:
					cr.visible = true
			"gone":
				n.visible = false
			"land":
				n.scale = Vector3.ONE * maxf(0.2, 1.0 - rk["t"] * 1.2)
		n.position = p


func _place_camera(delta: float, snap := false) -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_v := tan(deg_to_rad(camera.fov * 0.5))
	var dist := maxf(8.6 / half_v, 7.8 / (half_v * aspect))
	var look := Vector3(6.5, -6.9, 0.0)
	var e := game.engine
	if e:
		var hp := world(e.hero["pos"])
		look += (hp - look) * 0.06
	var pos := look + Vector3(sin(_time * 0.11) * 0.3, 0.8 + sin(_time * 0.09) * 0.2, dist)
	if _punch > 0.0:
		var k := sin(_punch / 0.5 * PI) * 0.12
		look = look.lerp(_punch_at, k)
		pos = pos.lerp(_punch_at + Vector3(0, 0, dist * 0.7), k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.15 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
