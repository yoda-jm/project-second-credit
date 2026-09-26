class_name PrismView3D
extends Node3D
## Prism Breaker in 3D: the field stands upright in a riveted sci-fi frame over a dark circuit backdrop, seen from a
## little below. Crystal bricks glow in six colours (hard ones sit in metal and crack as they are hit), the paddle-ship
## stretches and shrinks, the ball trails light, capsules tumble down with their letter, drones spin in through the
## doors in the top, and the break door opens in the right wall. Field (x, y down) is world (x - 6.5, 8.5 - y, 0).

const E = preload("res://games/prism/engine/prism_engine.gd")
const M := "res://games/prism/art/models/"
const T := 0.8  # frame thickness
const COLORS := {"a": Color(1.0, 0.22, 0.3), "b": Color(1.0, 0.55, 0.12), "c": Color(1.0, 0.88, 0.2),
	"d": Color(0.2, 1.0, 0.45), "e": Color(0.2, 0.55, 1.0), "f": Color(0.72, 0.3, 1.0), "H": Color(0.75, 0.95, 1.0),
	"S": Color(0.7, 0.75, 0.8), "G": Color(1.0, 0.8, 0.3)}
const CAPSULES := {"wide": ["W", Color(0.25, 0.55, 1.0)], "laser": ["L", Color(1.0, 0.25, 0.25)],
	"catch": ["C", Color(0.25, 1.0, 0.45)], "slow": ["S", Color(1.0, 0.6, 0.15)], "multi": ["M", Color(0.3, 0.95, 1.0)],
	"life": ["+", Color(0.6, 0.6, 0.7)], "break": ["B", Color(1.0, 0.35, 0.9)]}

@export var game: PrismGame

var camera: Camera3D
var _board: Node3D
var _fx: PrismEffects
var _bricks := {}  ## cell -> node
var _paddle: Node3D
var _pw := 2.0
var _balls: Array[Node3D] = []
var _bolts: Array[Node3D] = []
var _capsules: Array[Node3D] = []
var _drones := {}  ## id -> node
var _gates: Array[Node3D] = []
var _gate_open := [0.0, 0.0]
var _warp: Node3D
var _warp_open := 0.0
var _time := 0.0
var _shake := 0.0
var _mats := {}
var _bumps := {}  ## cell -> seconds of a bump left


static func W(p: Vector2, z := 0.0) -> Vector3:
	return Vector3(p.x - 6.5, 8.5 - p.y, z)


func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.01, 0.012, 0.03)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.4, 0.45, 0.65)
	env.ambient_light_energy = 0.45
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.9
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 0.9
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, -30, 0)
	key.light_energy = 1.1
	key.shadow_enabled = true
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(20, 40, 0)
	fill.light_energy = 0.35
	fill.light_color = Color(0.55, 0.65, 1.0)
	add_child(fill)
	camera = Camera3D.new()
	camera.fov = 38
	camera.current = true
	add_child(camera)
	_fx = PrismEffects.new()
	add_child(_fx)
	_build_frame()
	game.stage_started.connect(_on_stage)
	if game.engine:
		_on_stage(game.engine)


func _scene(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var n := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.9, 0.4, 0.3)
	mi.mesh = b
	n.add_child(mi)
	return n


func _tint(n: Node, match_name: String, col: Color, energy := -1.0, albedo := 1.0) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i) as StandardMaterial3D
			if mat == null or not mat.resource_name.contains(match_name):
				continue
			var key := [mat.resource_name, col, energy, albedo]
			if not _mats.has(key):
				var t := mat.duplicate() as StandardMaterial3D
				var a := t.albedo_color.a
				t.albedo_color = Color(col * albedo, a)
				if t.emission_enabled or energy > 0.0:
					t.emission_enabled = true
					t.emission = col
					if energy > 0.0:
						t.emission_energy_multiplier = energy
				_mats[key] = t
			m.set_surface_override_material(i, _mats[key])


## The frame stays for the whole game: sides, top with the two drone doors, corners, the break door, the backdrop.
func _build_frame() -> void:
	var f := Node3D.new()
	add_child(f)
	var back := _scene("backdrop")
	back.position = W(Vector2(6.5, 8.5), -0.7)
	f.add_child(back)
	for y in 17:
		var l := _scene("frame_side")
		l.position = W(Vector2(-T * 0.5, y + 0.5))
		l.rotation.z = PI
		f.add_child(l)
		if y < 15:
			var r := _scene("frame_side")
			r.position = W(Vector2(E.W + T * 0.5, y + 0.5))
			f.add_child(r)
	_warp = _scene("warp_gate")
	_warp.position = W(Vector2(E.W + T * 0.5, E.WARP_Y))
	f.add_child(_warp)
	for x in 13:
		if x in [3, 4, 8, 9]:
			continue
		var t := _scene("frame_top")
		t.position = W(Vector2(x + 0.5, -T * 0.5))
		f.add_child(t)
	for gx in E.GATES:
		var g := _scene("gate")
		g.position = W(Vector2(gx, -T * 0.5))
		f.add_child(g)
		_gates.append(g)
	for cx in [-T * 0.5, E.W + T * 0.5]:
		var c := _scene("frame_corner")
		c.position = W(Vector2(cx, -T * 0.5))
		f.add_child(c)


func _on_stage(e: PrismEngine) -> void:
	if _board:
		_board.queue_free()
	_board = Node3D.new()
	add_child(_board)
	_bricks.clear()
	_drones.clear()
	_balls.clear()
	_bolts.clear()
	_capsules.clear()
	_bumps.clear()
	e.event.connect(_on_event)
	for c in e.bricks:
		var kind: String = e.bricks[c]["kind"]
		var n := _scene({"H": "brick_hard", "S": "brick_steel", "G": "brick_gold"}.get(kind, "brick"))
		n.position = W(Vector2(c.x + 0.5, E.TOP + c.y * 0.5 + 0.25))
		if kind in "abcdefH":
			_tint(n, "brick_glass", COLORS[kind], 0.5, 0.3)  # dark glass that glows in its colour
			_tint(n, "brick_core", COLORS[kind], 2.2 if kind != "H" else 1.2)
		_board.add_child(n)
		_bricks[c] = n
	_paddle = _scene("paddle")
	_board.add_child(_paddle)
	var pl := OmniLight3D.new()
	pl.light_color = Color(0.4, 0.8, 1.0)
	pl.light_energy = 0.8
	pl.omni_range = 3.0
	pl.position = Vector3(0, 0.3, 0.8)
	_paddle.add_child(pl)
	_pw = e.paddle_w
	_place_camera()


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"brick":
			var c := Vector2i(d["col"], d["row"])
			if not _bricks.has(c):
				return
			var n: Node3D = _bricks[c]
			var col: Color = COLORS[d["kind"]]
			if d["broken"]:
				_fx.shatter(n.position + Vector3(0, 0, 0.3), col)
				n.queue_free()
				_bricks.erase(c)
				_shake = maxf(_shake, 0.08)
			else:
				_bumps[c] = 0.18
				_fx.spark(n.position + Vector3(0, -0.25, 0.3), col.lightened(0.4))
				if d["kind"] == "H" and e.bricks.has(c):
					var taken: int = (2 + mini(e.stage / 2, 3)) - int(e.bricks[c]["hits"])
					var cr := n.get_node_or_null("crack")
					if cr:
						cr.queue_free()
					var crack := _scene("brick_crack_%d" % clampi(taken, 1, 2))
					crack.name = "crack"
					n.add_child(crack)
		"drone":
			_gate_open[E.GATES.find(d["x"])] = 1.2
		"drone_pop":
			_fx.pop(W(d["pos"], 0.2), Color(1.0, 0.5, 0.9))
		"capsule":
			_fx.pop(W(Vector2(e.paddle_x, E.PADDLE_Y), 0.3), CAPSULES[d["kind"]][1])
		"lose_ball":
			_shake = 0.4
		"warp":
			_fx.pop(W(Vector2(E.W, E.WARP_Y), 0.3), Color(1.0, 0.4, 0.9))


func _pool(arr: Array[Node3D], count: int, model: String, setup: Callable = Callable()) -> void:
	while arr.size() < count:
		var n := _scene(model)
		_board.add_child(n)
		if setup.is_valid():
			setup.call(n)
		arr.append(n)
	for i in arr.size():
		arr[i].visible = i < count


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _paddle == null:
		return
	# paddle: stretch towards the engine's width
	_pw = move_toward(_pw, e.paddle_w, delta * 6.0)
	_paddle.position = W(Vector2(e.paddle_x, E.PADDLE_Y + 0.05))
	var mid := _paddle.get_node_or_null("mid") as Node3D
	if mid:
		mid.scale.x = _pw - 1.0
		(_paddle.get_node("end_l") as Node3D).position.x = -(_pw - 1.0) * 0.5
		(_paddle.get_node("end_r") as Node3D).position.x = (_pw - 1.0) * 0.5
	_paddle.visible = not (e.phase == E.Phase.LOST or e.phase == E.Phase.OVER)
	_paddle.rotation.z = lerp_angle(_paddle.rotation.z, clampf((e.paddle_x - e.target_x) * 0.05, -0.08, 0.08), minf(1.0, delta * 10.0))
	# balls, with a glow each
	_pool(_balls, e.balls.size(), "ball", func(n):
		var l := OmniLight3D.new()
		l.light_color = Color(0.6, 0.9, 1.0)
		l.light_energy = 0.9
		l.omni_range = 2.2
		l.position = Vector3(0, 0, 0.4)
		n.add_child(l))
	for i in e.balls.size():
		var b: Dictionary = e.balls[i]
		_balls[i].position = W(b["pos"])
		var ring := _balls[i].get_node_or_null("ring") as Node3D
		if ring:
			ring.rotation.y += delta * 6.0
	# laser bolts
	_pool(_bolts, e.bolts.size(), "laser_bolt")
	for i in e.bolts.size():
		_bolts[i].position = W(e.bolts[i]["pos"], 0.0)
	# capsules: a letter on a coloured band, rolling as they fall
	_pool(_capsules, e.capsules.size(), "capsule", func(n):
		var lb := Label3D.new()
		lb.name = "letter"
		lb.font = HudKit.font(true)
		lb.font_size = 80
		lb.pixel_size = 0.0045
		lb.position = Vector3(0, -0.01, 0.26)
		lb.outline_size = 22
		lb.outline_modulate = Color(0.02, 0.03, 0.08)
		lb.no_depth_test = true
		lb.render_priority = 2
		n.scale = Vector3.ONE * 1.35
		n.add_child(lb))
	for i in e.capsules.size():
		var cp: Dictionary = e.capsules[i]
		var n := _capsules[i]
		n.position = W(cp["pos"], 0.1)
		var info: Array = CAPSULES[cp["kind"]]
		var lb := n.get_node("letter") as Label3D
		if lb.text != info[0]:
			lb.text = info[0]
			_tint(n, "capsule_band", info[1], 0.7)
		n.rotation.x = sin(_time * 5.0 + i) * 0.35
	# drones
	var alive := {}
	for dr in e.drones:
		alive[dr["id"]] = true
		if not _drones.has(dr["id"]):
			var n := _scene("drone_%d" % dr["kind"])
			_board.add_child(n)
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			if ap and ap.has_animation("spin"):
				ap.get_animation("spin").loop_mode = Animation.LOOP_LINEAR
				ap.play("spin")
			_drones[dr["id"]] = n
		_drones[dr["id"]].position = W(dr["pos"], 0.1)
	for id in _drones.keys():
		if not alive.has(id):
			_drones[id].queue_free()
			_drones.erase(id)
	# doors
	for i in _gates.size():
		_gate_open[i] = maxf(0.0, _gate_open[i] - delta)
		var door := _gates[i].get_node_or_null("door") as Node3D
		if door:
			door.scale.y = move_toward(door.scale.y, 0.05 if _gate_open[i] > 0.0 else 1.0, delta * 4.0)
	var wd := _warp.get_node_or_null("door") as Node3D
	if wd:
		wd.scale.y = move_toward(wd.scale.y, 0.05 if e.warp_open else 1.0, delta * 2.5)
	# bumped bricks
	for c in _bumps.keys():
		_bumps[c] -= delta
		if _bricks.has(c):
			var k: float = maxf(_bumps[c], 0.0) / 0.18
			(_bricks[c] as Node3D).scale = Vector3.ONE * (1.0 + 0.12 * k)
		if _bumps[c] <= 0.0:
			_bumps.erase(c)
	_shake = maxf(0.0, _shake - delta * 1.5)
	_place_camera()


func _place_camera() -> void:
	var aspect := get_viewport().get_visible_rect().size.aspect()
	# the field and its frame, about 15 x 18.5, fill the height (or the width on a narrow screen)
	var need := maxf(10.4, 8.6 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var j := Vector3(sin(_time * 50.0), cos(_time * 43.0), 0) * _shake * _shake * (0.4 if Settings.camera_shake else 0.0)
	var target := Vector3(0, -0.6, 0)
	camera.position = target + Vector3(0.0, -0.22, 1.0).normalized() * dist + j
	camera.look_at(target + j, Vector3.UP)


## The field x under a screen position (for the mouse).
func field_x_at(screen: Vector2) -> float:
	var o := camera.project_ray_origin(screen)
	var d := camera.project_ray_normal(screen)
	# intersect with the plane z = 0
	if absf(d.z) < 0.0001:
		return game.engine.paddle_x if game.engine else 6.5
	var t := -o.z / d.z
	var p := o + d * t
	return p.x + 6.5
