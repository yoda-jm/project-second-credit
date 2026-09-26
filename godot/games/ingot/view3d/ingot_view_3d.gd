class_name IngotView3D
extends Node3D
## Ingot Run in 3D: the level as a lit cross-section of an old temple mine, seen from the front and a little above.
## Cell (x, y) sits at world (x, -y, 0): bricks, stone, ladders and ropes in the grid plane, carved walls behind,
## lanterns and torches giving warm pools of light, the runner and the guards animated from their rigs, holes
## crumbling open and refilling, gold glinting, and the exit ladder rising in light when the last gold is taken.

const T = IngotLevel.T
const M := "res://games/ingot/art/models/"
const GUARD_COLORS := [Color(0.7, 0.12, 0.1), Color(0.55, 0.15, 0.5), Color(0.15, 0.35, 0.6), Color(0.6, 0.35, 0.1)]

@export var game: IngotGame

var camera: Camera3D
var _env: Environment
var _board: Node3D
var _fx: IngotEffects
var _bricks := {}      ## cell -> node (the diggable ones)
var _gold := {}        ## cell -> node
var _hidden: Array[Node3D] = []  ## the exit ladder pieces, shown when revealed
var _runner := {}
var _guards := {}      ## index -> {node, anim, last, face}
var _time := 0.0
var _shake := 0.0
var _cam := Vector3.ZERO
var _mats := {}


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color(0.03, 0.025, 0.03)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color(0.55, 0.45, 0.4)
	_env.ambient_light_energy = 0.45
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.tonemap_exposure = 1.05
	_env.glow_enabled = true
	_env.glow_intensity = 0.8
	_env.glow_hdr_threshold = 0.9
	_env.ssao_enabled = true
	_env.ssao_intensity = 1.6
	Look.fog(_env, Color(0.12, 0.08, 0.06), 0.01)
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, -20, 0)
	key.light_color = Color(1.0, 0.85, 0.7)
	key.light_energy = 0.55
	key.shadow_enabled = true
	add_child(key)
	camera = Camera3D.new()
	camera.fov = 34
	camera.current = true
	add_child(camera)
	_fx = IngotEffects.new()
	add_child(_fx)
	game.level_started.connect(_on_level)
	if game.engine:
		_on_level(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.9, 0.9, 0.9)
	mi.mesh = b
	n.add_child(mi)
	return n


## A model that stands in a cell: models are built with Z up and the cell's floor at -0.5; Godot's import turns
## Blender Z into Y, so the node goes at the cell's centre.
func _place(n: Node3D, c: Vector2i, z := 0.0) -> void:
	n.position = Vector3(c.x, -c.y, z)
	_board.add_child(n)


func _shade(n: Node, k: float) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null:
				continue
			var key := [mat, k]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				t.albedo_color = mat.albedo_color * Color(k, k * 0.95, k * 0.9)
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


func _paint_robe(n: Node, col: Color) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and mat.resource_name.contains("team"):
				var key := [mat.resource_name, col]
				if not _mats.has(key):
					var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					s.albedo_color = col
					_mats[key] = s
				m.set_surface_override_material(i, _mats[key])


func _on_level(e: IngotEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_bricks.clear()
	_gold.clear()
	_hidden.clear()
	_guards.clear()
	e.event.connect(_on_event)
	var lv := e.level
	var rng := RandomNumberGenerator.new()
	rng.seed = lv.w * 97 + lv.gold.size()
	for y in lv.h:
		for x in lv.w:
			var c := Vector2i(x, y)
			# the carved wall behind every cell
			var bw := _scene("back_wall_%d" % (0 if rng.randf() < 0.7 else rng.randi_range(1, 2)))
			_place(bw, c, -1.0)
			_shade(bw, 0.38)  # the wall behind sits in shadow, so the platforms stand out
			match lv.tiles[y * lv.w + x]:
				T.BRICK:
					var b := _scene("brick_%d" % ((x + y) % 2))
					_place(b, c)
					_bricks[c] = b
				T.TRAP:
					_place(_scene("trap_brick"), c)
				T.SOLID:
					_place(_scene("stone"), c)
				T.LADDER:
					_place(_scene("ladder"), c)
				T.BAR:
					_place(_scene("bar"), c)
				T.HIDDEN_LADDER:
					var h := _scene("exit_ladder")
					_place(h, c)
					h.visible = false
					_hidden.append(h)
	for c in lv.gold:
		var g := _scene("gold")
		g.scale = Vector3.ONE * 1.4
		_place(g, c)
		_gold[c] = g
	# a frame around the level, torches and lanterns for warm light
	for x in range(-1, lv.w + 1):
		_place(_scene("stone"), Vector2i(x, lv.h))
		_place(_scene("stone"), Vector2i(x, -1))
	for y in range(-1, lv.h + 1):
		_place(_scene("stone"), Vector2i(-1, y))
		_place(_scene("stone"), Vector2i(lv.w, y))
	var lights := 0
	for y in range(0, lv.h, 4):
		for x in range(2, lv.w, 6):
			var c := Vector2i(x + (y / 4) % 3, y)
			if c.x >= lv.w:
				continue
			var t := _scene("torch" if (x + y) % 2 == 0 else "lantern")
			_place(t, c, -0.45)
			var l := OmniLight3D.new()
			l.light_color = Color(1.0, 0.62, 0.3)
			l.light_energy = 1.3
			l.omni_range = 6.0
			l.position = Vector3(c.x, -c.y + 0.3, 0.6)
			_board.add_child(l)
			lights += 1
	# the characters
	_runner = {"node": _scene("runner"), "last": "", "face": 1}
	_runner["node"].scale = Vector3.ONE * 1.2
	_board.add_child(_runner["node"])
	_runner["anim"] = _runner["node"].find_child("AnimationPlayer", true, false)
	_loop(_runner["anim"])
	for i in e.guards.size():
		var n := _scene("guard")
		n.scale = Vector3.ONE * 1.2
		_board.add_child(n)
		_paint_robe(n, GUARD_COLORS[i % GUARD_COLORS.size()])
		var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
		_loop(ap)
		_guards[i] = {"node": n, "anim": ap, "last": "", "face": 1}
	_cam = Vector3(lv.w * 0.5 - 0.5, -lv.h * 0.5 + 0.5, 0)
	_place_camera(e, 1.0)


func _loop(ap: AnimationPlayer) -> void:
	if ap == null:
		return
	for a in ap.get_animation_list():
		ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "run", "climb", "bar", "hang", "fall", "trapped", "cheer"] else Animation.LOOP_NONE


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"dig":
			var c: Vector2i = d["cell"]
			_fx.dig(Vector3(c.x, -c.y + 0.3, 0.3))
			if _bricks.has(c):
				var b: Node3D = _bricks[c]
				var tw := create_tween()
				tw.tween_property(b, "scale", Vector3(1.0, 0.05, 1.0), 0.25)
		"refill":
			var c: Vector2i = d["cell"]
			if _bricks.has(c):
				var b: Node3D = _bricks[c]
				create_tween().tween_property(b, "scale", Vector3.ONE, 0.2).set_trans(Tween.TRANS_BACK)
				_fx.dust(Vector3(c.x, -c.y, 0.3))
		"gold":
			var c: Vector2i = d["cell"]
			if _gold.has(c):
				_fx.sparkle(_gold[c].position + Vector3(0, 0, 0.3))
				_gold[c].queue_free()
				_gold.erase(c)
		"all_gold":
			for h in _hidden:
				h.visible = true
				h.scale = Vector3(1, 0.01, 1)
				create_tween().tween_property(h, "scale", Vector3.ONE, 0.5).set_trans(Tween.TRANS_BACK)
				_fx.sparkle(h.position)
		"trapped", "crushed":
			var c: Vector2i = d["cell"]
			_fx.dust(Vector3(c.x, -c.y, 0.3))
			if kind == "crushed":
				_shake = 0.3
		"respawn":
			var c: Vector2i = d["cell"]
			_fx.sparkle(Vector3(c.x, -c.y, 0.3))
		"died":
			_shake = 0.5
	# gold a guard dropped (or carried off) shows where the engine has it
	for c in e.gold:
		if not _gold.has(c):
			var g := _scene("gold")
			_place(g, c)
			_gold[c] = g
	for c in _gold.keys():
		if not e.gold.has(c):
			_gold[c].queue_free()
			_gold.erase(c)


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null:
		return
	# holes: a brick's scale follows its hole (open, then closing in the last moments)
	for c in e.holes:
		if _bricks.has(c):
			var t: float = e.holes[c]
			var k := 0.05 if t < IngotEngine.HOLE_OPEN else lerpf(0.05, 1.0, (t - IngotEngine.HOLE_OPEN) / IngotEngine.HOLE_REFILL)
			if t > IngotEngine.DIG_TIME:
				_bricks[c].scale = Vector3(1.0, k, 1.0)
	_update_actor(_runner, e.runner, e, delta, true)
	for i in e.guards.size():
		if _guards.has(i):
			_update_actor(_guards[i], e.guards[i], e, delta, false)
	for c in _gold:
		_gold[c].rotation.y = sin(_time * 1.5 + c.x) * 0.3
	_place_camera(e, delta)


func _update_actor(v: Dictionary, a: Dictionary, e: IngotEngine, delta: float, is_runner: bool) -> void:
	var n: Node3D = v["node"]
	var p := e.pos(a)
	n.position = Vector3(p.x, -p.y - 0.5, 0.1)
	n.visible = a["state"] != "respawn"
	var here := e.at(a["cell"])
	var want := "idle"
	var faced := true  # run and bar face the way of travel; the rest face the camera
	match a["state"]:
		"move":
			var d: Vector2i = a["to"] - a["cell"]
			if d.y != 0:
				want = "climb" if (here == T.LADDER or e.at(a["to"]) == T.LADDER) else "fall"
				faced = false
			elif here == T.BAR or e.at(a["to"]) == T.BAR:
				want = "bar"
			else:
				want = "run"
		"fall": want = "fall"; faced = false
		"dig": want = "dig_left" if a["face"] < 0 else "dig_right"; faced = false
		"trapped": want = "trapped"; faced = false
		"climb_out": want = "climb_out"; faced = false
		"dead": want = "die"; faced = false
		_:
			faced = false
			if here == T.BAR:
				want = "hang"
			elif here == T.LADDER and not e.supported(a["cell"] + Vector2i(0, 0), a):
				want = "climb"
			if is_runner and e.phase == IngotEngine.Phase.CLEARED:
				want = "cheer"
	if a["state"] == "climb_out":
		n.position.y = -a["cell"].y - 0.5  # the clip lifts the body itself
	var yaw := 0.0
	if faced:
		yaw = PI * 0.5 if a["face"] > 0 else -PI * 0.5
	n.rotation.y = lerp_angle(n.rotation.y, yaw, minf(1.0, delta * 14.0))
	var ap: AnimationPlayer = v["anim"]
	if ap and want != v["last"] and ap.has_animation(want):
		v["last"] = want
		ap.play(want, 0.1)
	if ap and want == "run":
		ap.speed_scale = a["speed"] / (1.89 if is_runner else 1.51) * 0.5
	elif ap and want in ["climb", "bar"]:
		ap.speed_scale = a["speed"] / 1.5
	elif ap:
		ap.speed_scale = 1.0


func _place_camera(e: IngotEngine, delta: float) -> void:
	var lv := e.level
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_h := maxf(lv.h * 0.5 + 1.3, (lv.w * 0.5 + 1.3) / aspect)
	var dist := half_h / tan(deg_to_rad(camera.fov * 0.5))
	var target := Vector3(lv.w * 0.5 - 0.5, -lv.h * 0.5 + 0.5, 0)
	_cam = _cam.lerp(target, minf(1.0, delta * 3.0))
	_shake = maxf(0.0, _shake - delta * 2.0)
	var j := Vector3(sin(_time * 50.0), cos(_time * 43.0), 0) * _shake * _shake * (0.3 if Settings.camera_shake else 0.0)
	camera.position = _cam + Vector3(0, 1.8, dist) + j
	camera.look_at(_cam + j, Vector3.UP)
