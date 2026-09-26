class_name NightView3D
extends Node3D
## Nightbite in 3D: a neon maze floating in the dark, seen from high above. Wall cells become tube pieces chosen by
## their neighbours (straight, corner, T, cross, end, single), glowing in the maze's colour; pellets twinkle, power
## orbs pulse, the hero chomps and faces its way, the lantern spirits glide with their eyes on their target, turn
## deep blue and shiver when frightened, and race home as eyes. Cell (x, y) is centred at world (x + 0.5, 0, y + 0.5).

const E = preload("res://games/nightbite/engine/night_engine.gd")
const M := "res://games/nightbite/art/models/"
const NEON := {"violet": Color(0.65, 0.35, 1.0), "cyan": Color(0.2, 0.9, 1.0), "pink": Color(1.0, 0.3, 0.7), "green": Color(0.3, 1.0, 0.5)}
const SPIRIT_COLORS := [Color(1.0, 0.35, 0.25), Color(1.0, 0.55, 0.85), Color(0.35, 0.95, 1.0), Color(1.0, 0.7, 0.25)]
const SCARED := Color(0.18, 0.25, 0.95)

@export var game: NightGame

var camera: Camera3D
var _env: Environment
var _board: Node3D
var _fx: NightEffects
var _pellets := {}   ## cell -> index in the multimesh
var _pellet_mm: MultiMeshInstance3D
var _powers := {}    ## cell -> node
var _hero: Node3D
var _hero_anim: AnimationPlayer
var _spirits: Array[Dictionary] = []
var _bonus: Node3D
var _time := 0.0
var _shake := 0.0
var _mats := {}


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.01, 0.008, 0.03)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.35, 0.3, 0.55)
	_env.ambient_light_energy = 0.5
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 1.1
	_env.glow_bloom = 0.12
	_env.glow_hdr_threshold = 0.8
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-70, -20, 0)
	key.light_energy = 0.5
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 34
	camera.current = true
	add_child(camera)
	_fx = NightEffects.new()
	add_child(_fx)
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.35
	s.height = 0.7
	mi.mesh = s
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color, energy := -1.0) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col, energy]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = col
				if t.emission_enabled or energy > 0.0:
					t.emission_enabled = true
					t.emission = col
					if energy > 0.0:
						t.emission_energy_multiplier = energy
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _on_stage(e: NightEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_pellets.clear()
	_powers.clear()
	_spirits.clear()
	_bonus = null
	e.event.connect(_on_event)
	var m := e.maze
	var neon: Color = NEON.get(m.color, NEON["violet"])
	# the floor: faint tiles under the lanes
	for y in m.h:
		for x in m.w:
			var c := Vector2i(x, y)
			if m.wall(c):
				_wall_piece(m, c, neon)
			elif ResourceLoader.exists(M + "floor_tile.glb"):
				var f := _scene("floor_tile")
				f.position = Vector3(x + 0.5, 0, y + 0.5)
				_board.add_child(f)
	for c in m.gate:
		var g := _scene("gate")
		g.position = Vector3(c.x + 0.5, 0, c.y + 0.5)
		_board.add_child(g)
	# pellets in one multimesh
	var pm := MultiMesh.new()
	pm.transform_format = MultiMesh.TRANSFORM_3D
	var pel := _scene("pellet")
	for mi in pel.find_children("*", "MeshInstance3D", true, false):
		pm.mesh = (mi as MeshInstance3D).mesh
		break
	pel.free()
	pm.instance_count = e.pellets.size()
	var i := 0
	for c in e.pellets:
		pm.set_instance_transform(i, Transform3D(Basis(), Vector3(c.x + 0.5, 0.15, c.y + 0.5)))
		_pellets[c] = i
		i += 1
	_pellet_mm = MultiMeshInstance3D.new()
	_pellet_mm.multimesh = pm
	_board.add_child(_pellet_mm)
	for c in e.powers:
		var p := _scene("power")
		p.position = Vector3(c.x + 0.5, 0.2, c.y + 0.5)
		_board.add_child(p)
		_powers[c] = p
	_hero = _scene("hero")
	_board.add_child(_hero)
	_hero_anim = _hero.find_child("AnimationPlayer", true, false)
	if _hero_anim:
		for a in _hero_anim.get_animation_list():
			_hero_anim.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["chomp", "idle"] else Animation.LOOP_NONE
	var hl := OmniLight3D.new()  # the hero lights the maze around it
	hl.light_color = Color(1.0, 0.75, 0.35)
	hl.light_energy = 1.4
	hl.omni_range = 3.5
	hl.position = Vector3(0, 0.8, 0)
	_hero.add_child(hl)
	for s in e.spirits:
		var n := _scene("spook")
		_board.add_child(n)
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		if ap:
			for a in ap.get_animation_list():
				ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["float", "scared"] else Animation.LOOP_NONE
		_spirits.append({"node": n, "anim": ap, "last": "", "col": SPIRIT_COLORS[s["id"]], "painted": Color.BLACK,
			"body": n.find_child("body", true, false), "eyes": [n.find_child("eye_l", true, false), n.find_child("eye_r", true, false)]})
	_place_camera(e)


## A wall cell with no open cell around it (8 neighbours) is inside a solid block: it gets no piece.
func _inner(m: NightMaze, c: Vector2i) -> bool:
	if not m.wall(c) or c.x < 0 or c.y < 0 or c.x >= m.w or c.y >= m.h:
		return true
	for d in [Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1), Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		var nc: Vector2i = c + d
		if nc.x >= 0 and nc.y >= 0 and nc.x < m.w and nc.y < m.h and not m.wall(nc):
			return false
	return true


func _wall_piece(m: NightMaze, c: Vector2i, neon: Color) -> void:
	if _inner(m, c):
		return
	# connect only along the outline: to neighbouring wall cells that are themselves on an edge
	var up := not _inner(m, c + Vector2i(0, -1))
	var down := not _inner(m, c + Vector2i(0, 1))
	var left := not _inner(m, c + Vector2i(-1, 0))
	var right := not _inner(m, c + Vector2i(1, 0))
	var n_count := int(up) + int(down) + int(left) + int(right)
	var kind := "wall_single"
	var yaw := 0.0
	# pieces are modelled connecting +X (straight: +X and -X; corner: +X and +Z(down); T: -X, +X, +Z; end: +X)
	match n_count:
		4: kind = "wall_cross"
		3:
			kind = "wall_t"
			if not down: yaw = PI
			elif not left: yaw = PI * 0.5
			elif not right: yaw = -PI * 0.5
		2:
			if left and right: kind = "wall_straight"
			elif up and down: kind = "wall_straight"; yaw = PI * 0.5
			else:
				kind = "wall_corner"
				if right and down: yaw = 0.0
				elif down and left: yaw = -PI * 0.5
				elif left and up: yaw = PI
				else: yaw = PI * 0.5
		1:
			kind = "wall_end"
			if right: yaw = 0.0
			elif down: yaw = -PI * 0.5
			elif left: yaw = PI
			else: yaw = PI * 0.5
	var n := _scene(kind)
	n.position = Vector3(c.x + 0.5, 0, c.y + 0.5)
	n.rotation.y = yaw
	_board.add_child(n)
	_tint(n, "wall_neon", neon, 3.0)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"pellet":
			var c: Vector2i = d["cell"]
			if _pellets.has(c):
				_pellet_mm.multimesh.set_instance_transform(_pellets[c], Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))
				_pellets.erase(c)
		"power":
			var c: Vector2i = d["cell"]
			if _powers.has(c):
				_fx.burst_at(_powers[c].position, Color(1.0, 0.85, 0.4))
				_powers[c].queue_free()
				_powers.erase(c)
			_shake = 0.2
		"eat_spirit":
			_fx.burst_at(Vector3(d["pos"].x, 0.4, d["pos"].y), SPIRIT_COLORS[d["id"]])
			_shake = 0.25
		"bonus_show":
			_bonus = _scene("fruit_%d" % d["kind"])
			_bonus.position = Vector3(e.maze.bonus.x + 0.5, 0.25, e.maze.bonus.y + 0.5)
			_board.add_child(_bonus)
		"bonus_eat":
			if _bonus:
				_fx.burst_at(_bonus.position, Color(1.0, 0.9, 0.5))
				_bonus.queue_free()
				_bonus = null
		"died":
			_fx.burst_at(_hero.position + Vector3(0, 0.4, 0), Color(1.0, 0.7, 0.3))
			_shake = 0.5


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _hero == null:
		return
	# hero
	var hp: Vector2 = e.hero["pos"]
	_hero.position = Vector3(hp.x, 0.05, hp.y)
	var hd: Vector2i = e.hero["dir"]
	_hero.rotation.y = lerp_angle(_hero.rotation.y, atan2(float(hd.x), float(hd.y)), minf(1.0, delta * 20.0))
	_hero.visible = not (e.phase == E.Phase.DYING and e.phase_t < 1.3)
	if _hero_anim:
		var want := "die" if e.phase == E.Phase.DYING else ("chomp" if e.hero["moving"] else "idle")
		if _hero_anim.current_animation != want and _hero_anim.has_animation(want):
			_hero_anim.play(want, 0.08)
	# spirits
	var ending := e.fright > 0.0 and e.fright < 2.0 and fmod(_time, 0.4) < 0.2
	for i in e.spirits.size():
		var s := e.spirits[i]
		var v := _spirits[i]
		var n: Node3D = v["node"]
		n.position = Vector3(s["pos"].x, 0.1 + 0.05 * sin(_time * 4.0 + i), s["pos"].y)
		var sd: Vector2i = s["dir"]
		n.rotation.y = lerp_angle(n.rotation.y, atan2(float(sd.x), float(sd.y)), minf(1.0, delta * 12.0))
		var col: Color = v["col"]
		if s["scared"]:
			col = Color(0.95, 0.95, 1.0) if ending else SCARED
		if col != v["painted"]:
			v["painted"] = col
			_tint(n, "team", col, 1.5)
		if v["body"]:
			(v["body"] as Node3D).visible = s["state"] != "eyes" and s["state"] != "entering"
		var want := "scared" if s["scared"] else "float"
		var ap: AnimationPlayer = v["anim"]
		if ap and v["last"] != want and ap.has_animation(want):
			v["last"] = want
			ap.play(want, 0.1)
	# twinkle
	for c in _powers:
		var p: Node3D = _powers[c]
		p.scale = Vector3.ONE * (1.0 + 0.2 * sin(_time * 7.0))
	if _bonus:
		_bonus.rotation.y += delta * 2.0
	_shake = maxf(0.0, _shake - delta * 2.0)
	_place_camera(e)


func _place_camera(e: NightEngine) -> void:
	var m := e.maze
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(m.h * 0.5 + 1.0, (m.w * 0.5 + 1.0) / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var c := Vector3(m.w * 0.5, 0, m.h * 0.5 + 0.3)
	var j := Vector3(sin(_time * 50.0), 0, cos(_time * 43.0)) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	camera.position = c + Vector3(0, 0.95, 0.3).normalized() * dist + j
	camera.look_at(c + j, Vector3.UP)
