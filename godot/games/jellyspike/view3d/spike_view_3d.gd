class_name SpikeView3D
extends Node3D
## Jelly Spike in 3D: a beach court (the diorama from SpikeBeach when there is one: noon, sunset or night by match),
## two jelly blobs and a beach ball. The blobs are translucent candy with eyes that follow the ball; they stretch as
## they jump, squash as they land and quiver when the ball hits them. The ball spins with its flight and a soft
## shadow on the sand shows where it is. Sand sprays where the ball lands. The camera leans towards the ball, rises
## when it flies high, punches in on a hard spike and closes in on match point. World = game units, z = 0 the court.

const S = preload("res://games/jellyspike/engine/spike_engine.gd")
const COLORS := [Color(0.1, 0.6, 1.0), Color(1.0, 0.3, 0.25)]

@export var game: SpikeGame

var camera: Camera3D
var _env: Environment
var _we: WorldEnvironment
var _sun: DirectionalLight3D
var _stage: Node3D
var _beach: SpikeBeach
var _board: Array[Label3D] = []
var _blobs: Array[Node3D] = []
var _jelly: Array[ShaderMaterial] = []
var _eyes: Array = []            ## per blob: [pupil nodes]
var _wob := [0.0, 0.0]
var _squash := [0.0, 0.0]        ## > 0 squashed (landing), < 0 stretched (jumping)
var _ball: Node3D
var _ball_mesh: MeshInstance3D
var _ball_shadow: MeshInstance3D
var _fx: Bursts
var _time := 0.0
var _shake := 0.0
var _punch := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _was_ground := [true, true]
var _bubbles: Array = []         ## per blob: [[node, x, z, speed, phase]]
var _ball_light: OmniLight3D
var _bubble_mat: StandardMaterial3D
var _trail_t := 0.0


func _ready() -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var psm := ProceduralSkyMaterial.new()
	psm.sky_top_color = Color(0.25, 0.55, 0.95)
	psm.sky_horizon_color = Color(0.8, 0.92, 1.0)
	psm.ground_horizon_color = Color(0.8, 0.92, 1.0)
	psm.ground_bottom_color = Color(0.9, 0.8, 0.6)
	sky.sky_material = psm
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.ambient_light_energy = 0.45
	_env.tonemap_exposure = 0.85
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.glow_enabled = true
	_env.glow_intensity = 0.6
	_env.glow_hdr_threshold = 1.0
	_env.ssao_enabled = true
	_we = WorldEnvironment.new()
	_we.environment = _env
	add_child(_we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 50.0
	_sun.rotation_degrees = Vector3(-50, 25, 0)
	_sun.light_energy = 1.3
	add_child(_sun)
	camera = Camera3D.new()
	camera.fov = 36
	camera.far = 4000.0
	camera.current = true
	add_child(camera)
	_fx = Bursts.new()
	add_child(_fx)
	game.match_started.connect(_on_match)
	if game.engine:
		_on_match(game.engine)


func _mat(col: Color, rough := 0.5, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _sphere(r: float, mat: Material, segs := 32) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = segs
	s.rings = segs / 2
	mi.mesh = s
	mi.material_override = mat
	return mi


func _on_match(e: SpikeEngine) -> void:
	e.event.connect(_on_event)
	if _stage:
		_stage.queue_free()
	_stage = Node3D.new()
	add_child(_stage)
	_build_beach(game.matches % 3)
	_blobs.clear()
	_jelly.clear()
	_eyes.clear()
	_bubbles.clear()
	for s in 2:
		var root := Node3D.new()
		var body := Node3D.new()
		body.name = "body"
		root.add_child(body)
		var jm := ShaderMaterial.new()
		jm.shader = preload("res://games/jellyspike/shaders/jelly.gdshader")
		jm.set_shader_parameter("color", COLORS[s])
		jm.set_shader_parameter("phase", float(s) * 2.0)
		var blob := _sphere(S.BLOB_R, jm, 48)
		blob.scale = Vector3(1.05, 1.12, 0.95)
		blob.position = Vector3(0, 0.08, 0)
		body.add_child(blob)
		# a glossy core inside the jelly: a darker heart that shows through
		var core := _sphere(S.BLOB_R * 0.45, _mat(COLORS[s].darkened(0.4), 0.3, 0.3))
		core.position = Vector3(0, -0.05, 0)
		body.add_child(core)
		var pupils := []
		for ex in [-0.2, 0.2]:
			var eye := _sphere(0.14, _mat(Color(1, 1, 1), 0.15), 16)
			eye.position = Vector3(ex, 0.28, 0.46)
			body.add_child(eye)
			var pupil := _sphere(0.07, _mat(Color(0.05, 0.05, 0.1), 0.1), 12)
			pupil.position = Vector3(0, 0, 0.1)
			eye.add_child(pupil)
			pupils.append(pupil)
		# bubbles rising through the jelly, catching the light
		if _bubble_mat == null:
			_bubble_mat = StandardMaterial3D.new()
			_bubble_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			_bubble_mat.albedo_color = Color(1, 1, 1, 0.25)
			_bubble_mat.roughness = 0.02
			_bubble_mat.metallic_specular = 1.0
			_bubble_mat.rim_enabled = true
			_bubble_mat.rim = 1.0
			_bubble_mat.emission_enabled = true
			_bubble_mat.emission = Color(1, 1, 1)
			_bubble_mat.emission_energy_multiplier = 0.25
		var bl := []
		for bi in 7:
			var bub := _sphere(0.03 + 0.012 * (bi % 3), _bubble_mat, 10)
			body.add_child(bub)
			bl.append([bub, randf_range(-0.3, 0.3), randf_range(-0.2, 0.25), randf_range(0.25, 0.5), randf()])
		_bubbles.append(bl)
		var glow := OmniLight3D.new()  # the jelly lights the sand a little in its own colour
		glow.light_color = COLORS[s]
		glow.light_energy = 0.5
		glow.omni_range = 2.0
		glow.position = Vector3(0, 0.2, 0.5)
		root.add_child(glow)
		_stage.add_child(root)
		_blobs.append(root)
		_jelly.append(jm)
		_eyes.append(pupils)
	_wob = [0.0, 0.0]
	_squash = [0.0, 0.0]
	_ball = Node3D.new()
	var bm := ShaderMaterial.new()
	bm.shader = preload("res://games/jellyspike/shaders/beach_ball.gdshader")
	_ball_mesh = _sphere(S.BALL_R, bm, 32)
	_ball.add_child(_ball_mesh)
	_ball_light = OmniLight3D.new()  # a power ball burns
	_ball_light.light_color = Color(1.0, 0.55, 0.2)
	_ball_light.light_energy = 0.0
	_ball_light.omni_range = 4.0
	_ball.add_child(_ball_light)
	_stage.add_child(_ball)
	_ball_shadow = MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 0.4
	disc.bottom_radius = 0.4
	disc.height = 0.01
	_ball_shadow.mesh = disc
	var sm := StandardMaterial3D.new()
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.albedo_color = Color(0.0, 0.0, 0.05, 0.3)
	_ball_shadow.material_override = sm
	_ball_shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_stage.add_child(_ball_shadow)
	if _cam_pos == Vector3.ZERO:
		_place_camera(1.0, true)


## The beach diorama (noon, golden hour or a moonlit luau), with the score on its scoreboard.
func _build_beach(variant: int) -> void:
	_beach = SpikeBeach.new()
	_stage.add_child(_beach)
	_beach.build(variant)
	var d := _beach.environment_for(variant)
	_env = SpikeBeach.make_environment(d)
	_we.environment = _env
	SpikeBeach.setup_sun(_sun, d)
	# the score, painted on the scoreboard's face
	var at := _beach.global_transform * _beach.score_anchor()
	_board.clear()
	for s in 2:
		var l := Label3D.new()
		l.font = load("res://core/fonts/kenney_future.ttf")
		l.font_size = 96
		l.pixel_size = 0.006
		l.modulate = COLORS[s].lightened(0.2)
		l.outline_size = 0
		l.shaded = false
		l.double_sided = false
		l.text = "0"
		l.transform = at * Transform3D(Basis(), Vector3((-0.7 if s == 0 else 0.7), -0.05, 0.03))
		_stage.add_child(l)
		_board.append(l)


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"touch":
			var s: int = d["side"]
			var sp: float = d["speed"]
			_wob[s] = 1.0
			var bp: Vector2 = e.ball["pos"]
			_fx.burst(Vector3(bp.x, bp.y, 0.2), COLORS[s].lightened(0.3), 8 + int(sp), 2.0 + sp * 0.2, 0.4, 0.06, 1.0, -6.0, 1.0, "glow")
			if sp > 13.0:
				_punch = 0.4
				_shake = 0.3
		"power":
			var s: int = d["side"]
			var bp: Vector2 = e.ball["pos"]
			_fx.burst(Vector3(bp.x, bp.y, 0.2), Color(1.0, 0.6, 0.2), 50, 7.0, 0.6, 0.1, 1.0, -3.0, 1.0, "glow")
			_fx.flash(Vector3(bp.x, bp.y, 1.0), Color(1.0, 0.6, 0.3), 3.0)
			_punch = 0.5
			_shake = 0.6
			_wob[s] = 1.0
		"armed":
			var bp: Vector2 = e.blobs[d["side"]]["pos"]
			_fx.burst(Vector3(bp.x, bp.y + 0.4, 0.2), Color(1.0, 0.85, 0.4), 24, 3.0, 0.5, 0.07, 1.0, 2.0, 1.0, "glow")
		"jump":
			_squash[d["side"]] = -0.35
		"land":
			_squash[d["side"]] = 0.4
			var bp: Vector2 = e.blobs[d["side"]]["pos"]
			_fx.burst(Vector3(bp.x, 0.05, 0.2), Color(0.95, 0.85, 0.65), 8, 1.5, 0.5, 0.07, 0.0, -6.0, 0.5, "smoke")
		"floor":
			var x: float = d["x"]
			_fx.burst(Vector3(x, 0.05, 0.1), Color(0.95, 0.85, 0.6), 30, 4.0, 0.8, 0.09, 0.0, -9.0, 0.8, "smoke")
			_shake = 0.4
		"point":
			var s: int = d["side"]
			_beach.cheer(s)
			for i in 2:
				_board[i].text = str(e.score[i])
			var pop := create_tween()  # the new digit pops (scale, never font_size)
			_board[s].scale = Vector3.ONE * 1.4
			pop.tween_property(_board[s], "scale", Vector3.ONE, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			var hx: float = S._home(s)
			_fx.burst(Vector3(hx, 2.5, 0), COLORS[s], 30, 5.0, 1.0, 0.08, 1.0, -4.0, 1.0, "glow")
		"match":
			var s: int = d["winner"]
			for i in 5:
				_fx.burst(Vector3(2.0 + i * 3.0, 6.0 + (i % 2), -1.0), Color.from_hsv(i / 5.0, 0.7, 1.0), 30, 5.0, 1.4, 0.1, 1.0, -3.0, 1.0, "glow")
			_squash[s] = 0.5


func _process(delta: float) -> void:
	_time += delta
	var e := game.engine
	if e == null or _blobs.is_empty():
		return
	var bp: Vector2 = e.ball["pos"]
	for s in 2:
		var b: Dictionary = e.blobs[s]
		var n := _blobs[s]
		var p: Vector2 = b["pos"]
		n.position = Vector3(p.x, p.y - S.BLOB_R, 0)
		# squash and stretch settle like a spring
		_squash[s] = lerpf(_squash[s], 0.0, 1.0 - exp(-delta * 7.0))
		var sq: float = _squash[s] + sin(_time * 30.0) * _wob[s] * 0.06
		if not b["ground"]:
			sq = minf(sq, -0.12 * clampf(b["vel"].y / S.JUMP_V, -1.0, 1.0))
		var body: Node3D = n.get_node("body")
		body.scale = Vector3(1.0 + sq * 0.5, 1.0 - sq, 1.0 + sq * 0.5)
		body.position.y = S.BLOB_R * (1.0 - sq) - 0.0
		# a lean into the way it moves
		body.rotation.z = lerp_angle(body.rotation.z, -float(e.move[s]) * 0.12, 1.0 - exp(-delta * 8.0))
		_wob[s] = maxf(0.0, _wob[s] - delta * 1.5)
		_jelly[s].set_shader_parameter("wobble", _wob[s])
		_jelly[s].set_shader_parameter("charge", 1.0 if e.armed[s] else (0.25 if e.power[s] >= 1.0 else 0.0))
		for bb in _bubbles[s]:
			# rise from the bottom of the jelly to the top, wobbling, then start again
			var k: float = fmod(_time * bb[3] + bb[4], 1.0)
			(bb[0] as Node3D).position = Vector3(bb[1] + sin(_time * 3.0 + bb[4] * 9.0) * 0.04, S.BLOB_R * (-0.7 + 1.4 * k), bb[2])
			(bb[0] as Node3D).scale = Vector3.ONE * (0.6 + 0.6 * k) * smoothstep(1.0, 0.85, k)
		# the eyes follow the ball
		var look := Vector2(bp.x - p.x, bp.y - p.y - 0.3).normalized() * 0.05
		for pupil in _eyes[s]:
			(pupil as Node3D).position = Vector3(look.x, look.y, 0.1)
	_ball.position = Vector3(bp.x, bp.y, 0)
	var fire: bool = e.ball.get("fire", false)
	_ball_light.light_energy = lerpf(_ball_light.light_energy, 3.0 if fire else 0.0, 1.0 - exp(-delta * 12.0))
	if fire:
		_trail_t -= delta
		if _trail_t <= 0.0:
			_trail_t = 0.025
			_fx.burst(Vector3(bp.x, bp.y, 0.0), Color(1.0, 0.5 + randf() * 0.3, 0.15), 3, 0.6, 0.35, 0.09, 1.0, 1.0, 1.0, "glow")
	var v: Vector2 = e.ball["vel"]
	_ball_mesh.rotate_z(-v.x / S.BALL_R * delta * 0.5)
	_ball_mesh.rotate_x(v.y * delta * 0.2)
	var hgt := clampf(bp.y / 8.0, 0.0, 1.0)
	_ball_shadow.position = Vector3(bp.x, 0.02, 0.0)
	_ball_shadow.scale = Vector3.ONE * lerpf(1.0, 0.5, hgt)
	(_ball_shadow.material_override as StandardMaterial3D).albedo_color.a = lerpf(0.35, 0.08, hgt)
	_shake = maxf(0.0, _shake - delta * 1.8)
	_punch = maxf(0.0, _punch - delta)
	_place_camera(delta)


## Side-on, leaning towards the ball and rising when it flies high; closer on match point; a punch on a hard spike.
func _place_camera(delta: float, snap := false) -> void:
	var e := game.engine
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var need := maxf(5.2, 9.0 / aspect)
	var dist := need / tan(deg_to_rad(camera.fov * 0.5))
	var bp: Vector2 = e.ball["pos"] if e else Vector2(8, 3)
	var match_point := e and e.phase != S.Phase.OVER and maxi(e.score[0], e.score[1]) >= S.TARGET - 1 \
		and absi(e.score[0] - e.score[1]) >= 1
	# a high ball: pull back (and look up only a little), so the blobs on the sand stay in the picture
	var high := maxf(0.0, bp.y - 5.5)
	var look := Vector3(8.0 + (bp.x - 8.0) * 0.12, 3.6 + high * 0.3, 0.0)
	dist += high * 0.9
	if match_point:
		dist *= 0.92
	var pos := look + Vector3(1.6 + sin(_time * 0.15) * 0.5, 1.0 + sin(_time * 0.12) * 0.2, dist)  # a little to the side: the net reads as a net
	if _punch > 0.0:
		var k := sin(_punch / 0.4 * PI) * 0.08
		pos = pos.lerp(Vector3(bp.x, bp.y, dist * 0.7), k)
	var j := Vector3(sin(_time * 47.0), cos(_time * 41.0), 0) * _shake * _shake * (0.25 if Settings.camera_shake else 0.0)
	var k2 := 1.0 if snap else minf(1.0, delta * 3.0)
	_cam_pos = _cam_pos.lerp(pos, k2)
	_cam_look = _cam_look.lerp(look, k2)
	camera.position = _cam_pos + j
	camera.look_at(_cam_look, Vector3.UP)
