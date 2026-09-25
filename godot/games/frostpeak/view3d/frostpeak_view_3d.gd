class_name FrostpeakView3D
extends Node3D
## Frostpeak Games in 3D: three venues in one snowy valley ringed by mountains. The speed-skating oval sits at the
## origin, the K90 jump hill at JUMP, the medal plaza with the podium and the cauldron at PLAZA. The venues are
## built from the events' own geometry (lane lengths, in-run slope, landing curve) so the picture matches the rules.

const M := "res://games/frostpeak/art/models/"
const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage
const STRAIGHT := 100.0
const RADIUS := 30.0
const LANES: Array[float] = [2.0, 6.0]  ## lane centres, out from the inner radius (player, rival)
const JUMP := Vector3(700, 0, 0)
const PLAZA := Vector3(-500, 0, 0)
const INRUN_ANGLE := deg_to_rad(35.0)

@export var game: FrostpeakGame

var _camera: Camera3D
var _sun: DirectionalLight3D
var _snow_mat: ShaderMaterial
var _ice_mat: ShaderMaterial
var _skater: Node3D
var _rival: Node3D
var _jumper: Node3D
var _podium_people: Array[Node3D] = []
var _flags: Array[MeshInstance3D] = []
var _snowfall: GPUParticles3D
var _cam_pos := Vector3(0, 30, 80)
var _cam_look := Vector3.ZERO
var _t := 0.0
var _stage_t := 0.0
var _landed_x := 0.0
var _slide := 0.0
var _jump_stage := -1  ## the camera cuts (rather than glides) when the jumper changes stage


func _ready() -> void:
	_snow_mat = ShaderMaterial.new()
	_snow_mat.shader = load("res://games/frostpeak/shaders/snow.gdshader")
	_ice_mat = ShaderMaterial.new()
	_ice_mat.shader = load("res://games/frostpeak/shaders/ice.gdshader")
	_build_world()
	_build_mountains()
	_build_oval()
	_build_hill()
	_build_plaza()
	_skater = _athlete("skater")
	_rival = _athlete("skater")
	_jumper = _athlete("jumper")
	game.stage_changed.connect(_on_stage)
	game.attempt_started.connect(_on_attempt)


# ------------------------------------------------------------------ helpers

func _scene(name: String) -> Node3D:
	return (load(M + name + ".glb") as PackedScene).instantiate()


func _athlete(kind: String) -> Node3D:
	var n := _scene(kind)
	add_child(n)
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	for a in ap.get_animation_list():
		ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "skate", "glide", "ready", "tuck", "flight", "wave", "celebrate", "telemark"] else Animation.LOOP_NONE
	return n


func _anim(n: Node3D, name: String, speed := 1.0) -> void:
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	if ap.current_animation != name:
		ap.play(name, 0.2, speed)
	else:
		ap.speed_scale = speed


## Paints the "suit" material of an athlete in its nation's first flag colour.
func _dress(n: Node3D, nation: int) -> void:
	var col: Color = Competition.NATIONS[nation]["flag"][0]
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and mat.resource_name == "suit":
				var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				s.albedo_color = col
				m.set_surface_override_material(i, s)


func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi


func _flat(color: Color, rough := 0.6, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rough
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = emit
	return m


## Many copies of one model, each tinted (vertex colours on a white material) — spectators, trees.
func _crowd(model: String, xforms: Array[Transform3D], colors: Array[Color]) -> void:
	var root := _scene(model)
	var mesh: Mesh = null
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		mesh = (mi as MeshInstance3D).mesh
		break
	root.free()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = not colors.is_empty()
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
		if mm.use_colors:
			mm.set_instance_color(i, colors[i % colors.size()])
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	add_child(inst)
	if mm.use_colors:  # tint only the coats: keep the other materials, colour the white "coat" by the instance
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i)
			if mat and mat.resource_name == "coat":
				var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				s.vertex_color_use_as_albedo = true
				inst.set_surface_override_material(i, s)


# ------------------------------------------------------------------ world

func _build_world() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.3, 0.5, 0.85)
	sky_mat.sky_horizon_color = Color(0.82, 0.88, 0.96)
	sky_mat.ground_horizon_color = Color(0.85, 0.9, 0.97)
	sky_mat.ground_bottom_color = Color(0.7, 0.75, 0.85)
	sky_mat.sun_angle_max = 20.0
	var sky := Sky.new()
	sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	Look.sky_ambient(env, Color(0.65, 0.72, 0.85), 0.7)
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.85
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.3
	env.glow_hdr_threshold = 1.2
	env.ssao_enabled = true
	env.ssr_enabled = true  # the ice reflects the floodlights and the skaters
	Look.fog(env, Color(0.85, 0.9, 0.97), 0.0009)
	env.fog_aerial_perspective = 0.4
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.15
	env.adjustment_contrast = 1.08
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-24, -65, 0)  # low winter sun from the side: long shadows, relief on the snow
	_sun.light_color = Color(1.0, 0.95, 0.88)
	_sun.light_energy = 1.2
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 250.0
	add_child(_sun)
	_camera = Camera3D.new()
	_camera.fov = 50
	_camera.far = 4000.0
	_camera.current = true
	add_child(_camera)
	# gentle snowfall around the camera
	_snowfall = GPUParticles3D.new()
	_snowfall.amount = 900
	_snowfall.lifetime = 6.0
	_snowfall.visibility_aabb = AABB(Vector3(-40, -30, -40), Vector3(80, 60, 80))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(35, 2, 35)
	pm.direction = Vector3(0.2, -1, 0.1)
	pm.spread = 15.0
	pm.initial_velocity_min = 1.5
	pm.initial_velocity_max = 2.5
	pm.gravity = Vector3(0, -0.4, 0)
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.6
	pm.scale_min = 0.5
	pm.scale_max = 1.0
	_snowfall.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.12, 0.12)
	_snowfall.draw_pass_1 = q
	_snowfall.material_override = Fx.material("soft", Color(1, 1, 1, 0.9))
	add_child(_snowfall)


## A ring of snowy peaks around the whole valley.
func _build_mountains() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var noise := FastNoiseLite.new()
	noise.seed = 5
	noise.frequency = 0.004
	noise.fractal_octaves = 5
	var rings := [900.0, 1150.0, 1400.0, 1700.0, 2100.0]
	var steps := 160
	var pts := []
	for ri in rings.size():
		var row := []
		for k in steps + 1:
			var a := TAU * k / steps
			var p := Vector3(cos(a) * rings[ri], 0, sin(a) * rings[ri]) + Vector3(100, 0, 0)
			var h := 0.0
			if ri > 0 and ri < rings.size() - 1:
				h = (noise.get_noise_2d(p.x, p.z) * 0.5 + 0.55) * (420.0 if ri == 2 else 300.0)
			p.y = h - 40.0
			row.append(p)
		pts.append(row)
	for ri in rings.size() - 1:
		for k in steps:
			var a: Vector3 = pts[ri][k]
			var b: Vector3 = pts[ri][k + 1]
			var c: Vector3 = pts[ri + 1][k + 1]
			var d: Vector3 = pts[ri + 1][k]
			for v in [a, c, b, a, d, c]:
				st.add_vertex(v)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = _snow_mat.shader
	m.set_shader_parameter("shade", Color(0.6, 0.66, 0.8))
	m.set_shader_parameter("sparkle", 0.0)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	# the valley floor
	var floor := MeshInstance3D.new()
	var pl := PlaneMesh.new()
	pl.size = Vector2(3000, 3000)
	pl.subdivide_width = 60
	pl.subdivide_depth = 60
	floor.mesh = pl
	floor.position = Vector3(100, -0.1, 0)
	floor.material_override = _snow_mat
	add_child(floor)
	# forests
	var rng := RandomNumberGenerator.new()
	rng.seed = 12
	var trees: Array[Transform3D] = []
	for i in 700:
		var a := rng.randf() * TAU
		var r := rng.randf_range(160.0, 850.0)
		var p := Vector3(cos(a) * r + 100.0, 0, sin(a) * r)
		if p.distance_to(JUMP + Vector3(40, 0, 0)) < 150.0 or p.distance_to(PLAZA) < 60.0:
			continue
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.8, 3.4)), p))
	_crowd("snowy_pine", trees, [])


# ------------------------------------------------------------------ the oval

## Position and heading on a lane `lane_r` metres out from the inner radius, `s` metres from the start.
func oval_point(s: float, lane_r: float) -> Transform3D:
	var r := RADIUS + lane_r
	var per := 2.0 * STRAIGHT + TAU * r
	s = fposmod(s, per)
	var pos := Vector3.ZERO
	var dir := Vector3.RIGHT
	if s < STRAIGHT:
		pos = Vector3(-STRAIGHT * 0.5 + s, 0, -r)
	elif s < STRAIGHT + PI * r:
		var a := -PI * 0.5 + (s - STRAIGHT) / r
		pos = Vector3(STRAIGHT * 0.5 + cos(a) * r, 0, sin(a) * r)
		dir = Vector3(-sin(a), 0, cos(a))
	elif s < 2.0 * STRAIGHT + PI * r:
		pos = Vector3(STRAIGHT * 0.5 - (s - STRAIGHT - PI * r), 0, r)
		dir = Vector3.LEFT
	else:
		var a := PI * 0.5 + (s - 2.0 * STRAIGHT - PI * r) / r
		pos = Vector3(-STRAIGHT * 0.5 + cos(a) * r, 0, sin(a) * r)
		dir = Vector3(-sin(a), 0, cos(a))
	return Transform3D(Basis.looking_at(dir, Vector3.UP), pos)


func _ribbon(lane_r: float, width: float, mat: Material, y := 0.02) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var per := 2.0 * STRAIGHT + TAU * (RADIUS + lane_r)
	var n := 240
	for i in n:
		var a := oval_point(per * i / n, lane_r)
		var b := oval_point(per * (i + 1) / n, lane_r)
		var sa := a.basis.x * width * 0.5
		var sb := b.basis.x * width * 0.5
		var pa := a.origin + Vector3(0, y, 0)
		var pb := b.origin + Vector3(0, y, 0)
		for v in [pa - sa, pb - sb, pb + sb, pa - sa, pb + sb, pa + sa]:
			st.set_normal(Vector3.UP)
			st.add_vertex(v)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	add_child(mi)


func _build_oval() -> void:
	_ribbon(4.0, 12.0, _ice_mat, 0.0)  # the ice: lanes from 0 to 8 m out, plus a warm-up strip inside
	_ribbon(-1.5, 3.0, _ice_mat, 0.0)
	_ribbon(0.0, 0.15, _flat(Color(0.1, 0.3, 0.9)))
	_ribbon(4.0, 0.15, _flat(Color(0.9, 0.15, 0.15)))
	_ribbon(8.0, 0.15, _flat(Color(0.1, 0.3, 0.9)))
	# padded boards around the outside, on posts
	var per := 2.0 * STRAIGHT + TAU * (RADIUS + 10.5)
	var pad := _flat(Color(0.15, 0.3, 0.75), 0.5)
	for i in 120:
		var t := oval_point(per * i / 120.0, 10.5)
		var b := _box(self, t.origin + Vector3(0, 0.5, 0), Vector3(0.4, 1.0, per / 120.0 + 0.05), pad)
		b.basis = t.basis
	# the finish arch and the start line (the race starts on the back straight)
	var fin := oval_point(SpeedSkating.DISTANCE, LANES[0])
	var arch := _scene("finish_arch")
	arch.transform = Transform3D(fin.basis.rotated(Vector3.UP, PI * 0.5), oval_point(SpeedSkating.DISTANCE, 4.0).origin)
	add_child(arch)
	_box(self, fin.origin + Vector3(0, 0.03, 0) + fin.basis.x * 2.0, Vector3(0.3, 0.02, 9.0), _flat(Color(0.9, 0.1, 0.1))).basis = fin.basis.rotated(Vector3.UP, PI * 0.5)
	# the stand along the front straight, full of spectators in bright coats
	var seats: Array[Transform3D] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for row in 7:
		_box(self, Vector3(0, 0.6 + row * 0.8, RADIUS + 14.0 + row * 1.2), Vector3(STRAIGHT + 20.0, 1.2 + row * 1.6, 1.2), _flat(Color(0.55, 0.57, 0.62)))
		for k in 90:
			var x := -STRAIGHT * 0.5 - 8.0 + k * (STRAIGHT + 16.0) / 90.0 + rng.randf_range(-0.2, 0.2)
			seats.append(Transform3D(Basis(Vector3.UP, PI + rng.randf_range(-0.3, 0.3)), Vector3(x, 1.2 + row * 0.8 + 0.4, RADIUS + 14.0 + row * 1.2)))
	var coats: Array[Color] = [Color(0.9, 0.2, 0.2), Color(0.2, 0.4, 0.9), Color(0.95, 0.8, 0.2), Color(0.2, 0.7, 0.4),
		Color(0.95, 0.95, 0.95), Color(0.6, 0.3, 0.8), Color(1.0, 0.5, 0.2)]
	_crowd("spectator", seats, coats)
	# the grandstand's roof on pillars, and its back wall
	var steel := Pbr.material("metal", Color(0.55, 0.58, 0.62), 1.0, 0.8, 0.5)
	var roof := _box(self, Vector3(0, 12.5, RADIUS + 18.0), Vector3(STRAIGHT + 24.0, 0.4, 12.0), _flat(Color(0.85, 0.2, 0.2), 0.5))
	roof.rotation.x = -0.12
	_box(self, Vector3(0, 6.0, RADIUS + 23.5), Vector3(STRAIGHT + 24.0, 12.0, 0.5), _flat(Color(0.25, 0.27, 0.32), 0.7))
	for i in 9:
		var px := -STRAIGHT * 0.5 - 10.0 + i * (STRAIGHT + 20.0) / 8.0
		_box(self, Vector3(px, 6.0, RADIUS + 12.8), Vector3(0.35, 12.0, 0.35), steel)
	# bright banners on the boards
	var bcols := [Color(0.95, 0.8, 0.2), Color(0.2, 0.45, 0.9), Color(0.95, 0.95, 0.95), Color(0.3, 0.75, 0.45), Color(0.9, 0.3, 0.3)]
	var per_b := 2.0 * STRAIGHT + TAU * (RADIUS + 10.3)
	for i in 60:
		var t := oval_point(per_b * (i + 0.5) / 60.0, 10.3)
		var b := _box(self, t.origin + Vector3(0, 0.55, 0), Vector3(0.05, 0.7, per_b / 60.0 - 0.3), _flat(bcols[i % bcols.size()], 0.5))
		b.basis = t.basis
	# nation flags along the back straight
	for i in 12:
		var fx := -STRAIGHT * 0.5 + i * STRAIGHT / 11.0
		var pole := _scene("flagpole")
		pole.position = Vector3(fx, 0, -RADIUS - 16.0)
		add_child(pole)
		var flag := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(2.0, 1.3)
		pm.subdivide_width = 12
		pm.orientation = PlaneMesh.FACE_Z
		flag.mesh = pm
		var fm := ShaderMaterial.new()
		fm.shader = load("res://games/frostpeak/shaders/flag.gdshader")
		var cols: Array = Competition.NATIONS[i % Competition.NATIONS.size()]["flag"]
		fm.set_shader_parameter("c0", cols[0])
		fm.set_shader_parameter("c1", cols[1])
		fm.set_shader_parameter("c2", cols[2])
		flag.material_override = fm
		flag.position = pole.position + Vector3(1.0, 7.2, 0)
		add_child(flag)
	# the games' name painted in the infield snow
	var name_lb := Label3D.new()
	name_lb.text = "FROSTPEAK"
	name_lb.font = HudKit.font(true)
	name_lb.font_size = 900
	name_lb.pixel_size = 0.02
	name_lb.modulate = Color(0.2, 0.45, 0.9, 0.8)
	name_lb.rotation.x = -PI * 0.5
	name_lb.position = Vector3(0, 0.05, 0)
	add_child(name_lb)
	for x in [-STRAIGHT * 0.5 - 20.0, STRAIGHT * 0.5 + 20.0]:
		for z in [-RADIUS - 25.0, RADIUS + 25.0]:
			var fl := _scene("floodlight")
			add_child(fl)
			fl.position = Vector3(x, 0, z)
			fl.rotation.y = atan2(-x, -z)  # the lamps (+Z) face the rink


# ------------------------------------------------------------------ the jump hill

func inrun_point(along: float) -> Vector3:
	var back := SkiJump.INRUN - along
	return JUMP + Vector3(-back * cos(INRUN_ANGLE), back * sin(INRUN_ANGLE), 0)


func hill_point(x: float) -> Vector3:
	return JUMP + Vector3(x, _hill_y(x), 0)


func _hill_y(x: float) -> float:
	if x < 0.0:
		# under the in-run the hillside falls away, so the track stands on a real tower
		return -x * tan(INRUN_ANGLE) - 2.5 - (-x) * 0.32
	if x <= 125.0:
		return SkiJump.profile(x)
	var y125 := SkiJump.profile(125.0)
	var k := clampf((x - 125.0) / 45.0, 0.0, 1.0)
	return y125 - SkiJump.HILL_SLOPE * 0.5 * 45.0 * (k - k * k * 0.5)  # eases into the flat outrun


func _build_hill() -> void:
	# the terrain: the landing hill and the outrun down the middle, forested banks rising on both sides
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var xs := []
	var x := -100.0
	while x <= 240.0:
		xs.append(x)
		x += 2.5
	var zs := []
	for k in 49:
		zs.append(-96.0 + k * 4.0)
	var h := func(px: float, pz: float) -> float:
		var y: float = _hill_y(minf(px, 170.0))
		var bank := maxf(0.0, absf(pz) - 17.0)
		return y + minf(bank * 0.28 + bank * bank * 0.006, 24.0)  # gentle banks, not walls
	for i in xs.size() - 1:
		for k in zs.size() - 1:
			var p := []
			for c in [[i, k], [i + 1, k], [i + 1, k + 1], [i, k + 1]]:
				p.append(JUMP + Vector3(xs[c[0]], h.call(xs[c[0]], zs[c[1]]), zs[c[1]]))
			for v in [p[0], p[2], p[1], p[0], p[3], p[2]]:
				st.add_vertex(v)
	st.generate_normals()
	var terrain := MeshInstance3D.new()
	terrain.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = _snow_mat.shader
	m.set_shader_parameter("shade", Color(0.84, 0.88, 0.95))
	m.set_shader_parameter("mark_tex", _markings())
	m.set_shader_parameter("mark_rect", Vector4(JUMP.x + 40.0, JUMP.z - 15.0, 100.0, 30.0))
	terrain.material_override = m
	add_child(terrain)
	var steel := Pbr.material("metal", Color(0.55, 0.58, 0.62), 1.0, 0.8, 0.5)
	var red := _flat(Color(0.8, 0.12, 0.12), 0.45)
	var concrete := Pbr.material("rock", Color(0.8, 0.8, 0.82), 0.5)
	# the in-run: a U-shaped channel with ski grooves and lamps, on steel pillars with cross braces
	var len := SkiJump.INRUN + 3.0
	var mid := inrun_point(SkiJump.INRUN * 0.5 - 1.0)
	var along_basis := Basis(Vector3.BACK, -INRUN_ANGLE)
	var track := _box(self, mid + Vector3(0, 0.2, 0), Vector3(len, 0.4, 2.0), _flat(Color(0.9, 0.93, 0.98), 0.12))
	track.basis = along_basis
	for zz in [-0.35, 0.35]:
		var groove := _box(self, mid + Vector3(0, 0.41, zz), Vector3(len, 0.02, 0.14), _flat(Color(0.55, 0.62, 0.72), 0.05))
		groove.basis = along_basis
	for zz in [-1.05, 1.05]:  # low rails with a white cap
		var wall := _box(self, mid + Vector3(0, 0.45, zz), Vector3(len, 0.5, 0.1), red)
		wall.basis = along_basis
		var cap := _box(self, mid + Vector3(0, 0.72, zz), Vector3(len, 0.05, 0.14), _flat(Color(0.95, 0.95, 0.95), 0.4))
		cap.basis = along_basis
	var beam := _box(self, mid + Vector3(0, -0.45, 0), Vector3(len, 0.9, 2.6), steel)
	beam.basis = along_basis
	var lamp := _flat(Color(1.0, 0.95, 0.8), 0.3, 3.0)
	var a := 0.0
	while a <= SkiJump.INRUN:
		var p := inrun_point(a)
		var ground := JUMP.y + _hill_y(p.x - JUMP.x)
		var top := p.y - 0.9
		if top - ground > 0.5:
			for zz in [-1.1, 1.1]:
				_box(self, Vector3(p.x, (top + ground) * 0.5, p.z + zz), Vector3(0.35, top - ground, 0.35), steel)
			var brace := _box(self, Vector3(p.x, (top + ground) * 0.5, p.z), Vector3(0.12, (top - ground) * 1.02, 0.12), steel)
			brace.rotation.x = atan2(3.0, top - ground)
			if top - ground > 6.0:
				_box(self, Vector3(p.x, ground + (top - ground) * 0.5, p.z), Vector3(0.2, 0.2, 3.2), steel)
		for zz in [-1.15, 1.15]:
			_box(self, p + Vector3(0, 0.85, zz), Vector3(0.07, 0.07, 0.07), lamp)
		a += 7.0
	# the start house at the top, the take-off table at the lip
	var top_p := inrun_point(-2.0)
	var house := _box(self, top_p + Vector3(-5.5, 2.5, 0), Vector3(6.0, 5.0, 6.0), concrete)
	_box(self, house.position + Vector3(0, 2.8, 0), Vector3(6.8, 0.5, 6.8), red)
	_box(self, house.position + Vector3(2.99, 0.6, 0), Vector3(0.1, 1.2, 4.0), _flat(Color(1.0, 0.85, 0.55), 0.3, 1.5))
	var gate := _scene("start_gate")
	gate.position = inrun_point(0.0) + Vector3(0, 0.45, 0)
	gate.rotation.y = PI * 0.5
	add_child(gate)
	var table := _box(self, JUMP + Vector3(-3.0, -0.25, 0), Vector3(6.0, 0.7, 3.2), Pbr.material("planks", Color(0.75, 0.55, 0.38), 1.5))
	table.basis = Basis(Vector3.BACK, -0.18)
	# the judges' tower beside the knoll
	var jt := hill_point(55.0) + Vector3(0, 0, -34.0)
	jt.y = JUMP.y + h.call(55.0, -34.0)
	_box(self, jt + Vector3(0, 7.0, 0), Vector3(5.0, 14.0, 5.0), concrete)
	_box(self, jt + Vector3(0, 13.0, 2.51), Vector3(4.4, 1.6, 0.05), _flat(Color(0.6, 0.85, 1.0), 0.05, 0.6))
	_box(self, jt + Vector3(0, 14.3, 0), Vector3(5.6, 0.4, 5.6), red)
	# padded fences along the landing hill, with banners
	var banners := [Color(0.95, 0.8, 0.2), Color(0.2, 0.45, 0.9), Color(0.9, 0.3, 0.3), Color(0.3, 0.75, 0.45), Color(1, 1, 1)]
	var fx := 8.0
	var bi := 0
	while fx < 175.0:
		for zz in [-16.5, 16.5]:
			var p0 := hill_point(fx)
			var p1 := hill_point(fx + 6.0)
			var mp := (p0 + p1) * 0.5 + Vector3(0, 0.55, zz)
			var seg := _box(self, mp, Vector3(6.05, 1.1, 0.3), _flat(banners[bi % banners.size()], 0.6))
			seg.basis = Basis(Vector3.BACK, atan2(p1.y - p0.y, 6.0))
			bi += 1
		fx += 6.0
	# the outrun: a curved barrier, flags and the crowd
	for i in 13:
		var ang := -1.0 + i * (2.0 / 12.0)
		var bp := hill_point(200.0) + Vector3(cos(ang) * 6.0 - 6.0, 0.6, sin(ang) * 18.0)
		var b := _box(self, bp, Vector3(0.4, 1.2, 3.2), red)
		b.rotation.y = -ang
	for i in 8:
		var pole := _scene("flagpole")
		var fzz := -26.0 + i * 7.4
		pole.position = hill_point(205.0) + Vector3(8.0, 0, fzz)
		pole.position.y = JUMP.y + h.call(213.0, fzz)
		add_child(pole)
		var flag := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(2.0, 1.3)
		pm.subdivide_width = 12
		pm.orientation = PlaneMesh.FACE_Z
		flag.mesh = pm
		var fm := ShaderMaterial.new()
		fm.shader = load("res://games/frostpeak/shaders/flag.gdshader")
		var cols: Array = Competition.NATIONS[i % Competition.NATIONS.size()]["flag"]
		fm.set_shader_parameter("c0", cols[0])
		fm.set_shader_parameter("c1", cols[1])
		fm.set_shader_parameter("c2", cols[2])
		flag.material_override = fm
		flag.position = pole.position + Vector3(1.0, 7.2, 0)
		add_child(flag)
	for d in range(60, 131, 10):
		var lb := Label3D.new()
		lb.text = str(d)
		lb.font = HudKit.font(true)
		lb.font_size = 220
		lb.modulate = Color(0.9, 0.15, 0.15) if d == 90 else Color(0.15, 0.25, 0.8)
		lb.position = hill_point(d) + Vector3(0, 2.6, -16.4)
		add_child(lb)
	var fans: Array[Transform3D] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 9
	for i in 700:
		var fxx := rng.randf_range(205.0, 225.0)
		var fz := rng.randf_range(-30.0, 30.0)
		fans.append(Transform3D(Basis(Vector3.UP, -PI * 0.5 + rng.randf_range(-0.4, 0.4)), JUMP + Vector3(fxx, h.call(fxx, fz), fz)))
	_crowd("spectator", fans, [Color(0.9, 0.2, 0.2), Color(0.2, 0.4, 0.9), Color(0.95, 0.8, 0.2), Color(0.2, 0.7, 0.4), Color(1, 1, 1)])
	# the forest on the banks
	var trees: Array[Transform3D] = []
	for i in 420:
		var tx := rng.randf_range(-90.0, 230.0)
		var side := -1.0 if i % 2 == 0 else 1.0
		var tz := side * rng.randf_range(24.0, 90.0)
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.6, 3.2)), JUMP + Vector3(tx, h.call(tx, tz), tz)))
	_crowd("snowy_pine", trees, [])
	for zz in [-28.0, 28.0]:
		var fl := _scene("floodlight")
		add_child(fl)
		fl.position = hill_point(70.0) + Vector3(0, 0, zz)
		fl.position.y = JUMP.y + h.call(70.0, zz)
		fl.rotation.y = 0.0 if zz < 0.0 else PI


## The hill's painted lines: blue every 10 m, red at the K point (world XZ over 100 x 30 m from x = 40).
func _markings() -> ImageTexture:
	var img := Image.create(400, 60, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for d in range(40, 141, 10):
		var px := int((d - 40) * 4.0)
		var col := Color(0.85, 0.1, 0.1, 0.95) if d == 90 else Color(0.15, 0.3, 0.85, 0.7)
		for w in 2:
			for y in 60:
				img.set_pixel(clampi(px + w, 0, 399), y, col)
	return ImageTexture.create_from_image(img)


# ------------------------------------------------------------------ the plaza

func _build_plaza() -> void:
	var pod := _scene("podium")
	pod.position = PLAZA
	add_child(pod)
	for i in 3:
		var pole := _scene("flagpole")
		pole.position = PLAZA + Vector3((i - 1) * 2.4, 0, 6.0)
		add_child(pole)
		var flag := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(2.0, 1.3)
		pm.subdivide_width = 12
		pm.orientation = PlaneMesh.FACE_Z
		flag.mesh = pm
		var fm := ShaderMaterial.new()
		fm.shader = load("res://games/frostpeak/shaders/flag.gdshader")
		flag.material_override = fm
		flag.position = PLAZA + Vector3((i - 1) * 2.4 + 1.0, 1.0, 5.95)
		add_child(flag)
		_flags.append(flag)
	var c := _scene("cauldron")
	c.position = PLAZA + Vector3(-12.0, 0, 4.0)
	add_child(c)
	var fire := OmniLight3D.new()
	fire.position = c.position + Vector3(0, 4.2, 0)
	fire.light_color = Color(1.0, 0.6, 0.25)
	fire.light_energy = 3.0
	fire.omni_range = 18.0
	add_child(fire)
	for i in 3:
		var a := _athlete("skater")
		_podium_people.append(a)
	var fans: Array[Transform3D] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 21
	for i in 160:
		var a := rng.randf_range(-2.2, 2.2)
		var r := rng.randf_range(14.0, 22.0)
		var p := PLAZA + Vector3(sin(a) * r, 0, -cos(a) * r)
		fans.append(Transform3D(Basis.looking_at(PLAZA - p, Vector3.UP).rotated(Vector3.UP, PI), p))
	_crowd("spectator", fans, [Color(0.9, 0.2, 0.2), Color(0.2, 0.4, 0.9), Color(0.95, 0.8, 0.2), Color(0.2, 0.7, 0.4)])


func _set_flag(i: int, nation: int) -> void:
	var cols: Array = Competition.NATIONS[nation]["flag"]
	var m := _flags[i].material_override as ShaderMaterial
	m.set_shader_parameter("c0", cols[0])
	m.set_shader_parameter("c1", cols[1])
	m.set_shader_parameter("c2", cols[2])


# ------------------------------------------------------------------ stages

func _on_stage(stage: int) -> void:
	_stage_t = 0.0
	var ev := game.comp.event_name() if game.comp else ""
	_skater.visible = false
	_rival.visible = false
	_jumper.visible = false
	for p in _podium_people:
		p.visible = false
	if stage == S.PODIUM:
		var rk := game.comp.ranking(game.comp.programme[game.comp.current])
		var spots := [Vector3(0, 1.2, 0), Vector3(-1.45, 0.85, 0), Vector3(1.45, 0.55, 0)]
		for place in mini(3, rk.size()):
			var a := _podium_people[place]
			a.visible = true
			a.position = PLAZA + spots[place]
			a.rotation.y = 0.0
			_dress(a, game.comp.athletes[rk[place]]["nation"])
			_anim(a, "wave" if place == 0 else "idle")
			_set_flag([1, 0, 2][place], game.comp.athletes[rk[place]]["nation"])
			_flags[[1, 0, 2][place]].position.y = 1.0


func _on_attempt(ev: WinterEvent) -> void:
	var nation: int = game.comp.athletes[game.humans()[game.athlete]]["nation"]
	_jump_stage = -1
	if ev is SpeedSkating:
		_dress(_skater, nation)
		_dress(_rival, (nation + 3) % Competition.NATIONS.size())
	else:
		_dress(_jumper, nation)
		_slide = 0.0


func _process(delta: float) -> void:
	_t += delta
	_stage_t += delta
	if game.comp == null:
		_plaza_camera(delta, true)
		return
	match game.stage:
		S.ATTEMPT, S.RESULT:
			if game.ev is SpeedSkating:
				_update_skating(game.ev as SpeedSkating, delta)
			elif game.ev is SkiJump:
				_update_jump(game.ev as SkiJump, delta)
		S.INTRO:
			_flyby(delta)
		S.STANDINGS:
			_flyby(delta)
		S.PODIUM:
			for i in 3:
				var f := _flags[i]
				var top := 6.8 - i * 0.0 - (0.0 if i == 1 else 0.5)
				f.position.y = move_toward(f.position.y, top, delta * 1.6)
			_move_camera(PLAZA + Vector3(0, 3.0, -11.0 + sin(_t * 0.2) * 0.5), PLAZA + Vector3(0, 2.2, 1.5), delta, 2.0)
		S.FINAL, S.SETUP:
			_plaza_camera(delta, false)
	_snowfall.position = _camera.position + Vector3(0, 12, 0)


func _move_camera(pos: Vector3, look: Vector3, delta: float, speed := 3.0) -> void:
	var k := 1.0 - exp(-delta * speed)
	_cam_pos = _cam_pos.lerp(pos, k)
	_cam_look = _cam_look.lerp(look, k)
	_camera.position = _cam_pos
	_camera.look_at(_cam_look)


func _snap_camera(pos: Vector3, look: Vector3) -> void:
	_cam_pos = pos
	_cam_look = look
	_camera.position = pos
	_camera.look_at(look)


func _plaza_camera(delta: float, snap: bool) -> void:
	var a := _t * 0.08
	var pos := PLAZA + Vector3(-12.0 + sin(a) * 22.0, 7.0, 4.0 - cos(a) * 22.0)
	var look := PLAZA + Vector3(-12.0, 4.0, 4.0)
	if snap:
		_snap_camera(pos, look)
	else:
		_move_camera(pos, look, delta, 1.5)


## Event intro and standings: a slow sweep over the venue.
func _flyby(delta: float) -> void:
	var ev := game.comp.event_name()
	var k := _stage_t
	if ev == "speed_skating":
		var a := 0.6 + k * 0.12
		_move_camera(Vector3(cos(a) * 110.0, 32.0, sin(a) * 90.0), Vector3(0, 0, 0), delta, 1.2)
	else:
		_move_camera(JUMP + Vector3(150.0 - k * 12.0, 12.0 + k * 2.0, 55.0), JUMP + Vector3(30.0, -15.0, 0), delta, 1.2)


func _update_skating(s: SpeedSkating, delta: float) -> void:
	_skater.visible = true
	_rival.visible = true
	var me := oval_point(s.pos, LANES[0])
	var them := oval_point(s.rival_pos, LANES[1])
	_skater.transform = Transform3D(me.basis.rotated(me.basis.y, PI), me.origin)
	_rival.transform = Transform3D(them.basis.rotated(them.basis.y, PI), them.origin)
	if s.phase == WinterEvent.Phase.READY:
		_anim(_skater, "ready")
		_anim(_rival, "ready")
	elif s.phase == WinterEvent.Phase.RUN:
		_anim(_skater, "skate" if s.meter < 1.2 else "glide", clampf(0.6 / s.stride_time(), 0.6, 1.8))
		_anim(_rival, "skate", clampf(s.rival_speed / 9.0, 0.5, 1.6))
	else:
		_anim(_skater, "celebrate" if s.result < 42.0 else "glide")
	# the TV camera: beside the track, level with the skater, a little ahead
	var side := -me.basis.x * 10.0
	var cam := me.origin + side + Vector3(0, 3.2, 0) - me.basis.z * 2.0
	if game.stage == S.ATTEMPT and s.phase == WinterEvent.Phase.READY and s.phase_left > 2.7:
		_snap_camera(cam, me.origin)
	_move_camera(cam, me.origin + Vector3(0, 1.0, 0) - me.basis.z * 4.0, delta, 4.0)


func _update_jump(j: SkiJump, delta: float) -> void:
	_jumper.visible = true
	var cut: bool = j.stage != _jump_stage
	_jump_stage = j.stage
	var pos := Vector3.ZERO
	match j.stage:
		SkiJump.Stage.INRUN:
			pos = inrun_point(j.along) + Vector3(0, 0.5, 0)
			_jumper.basis = Basis(Vector3.UP, PI * 0.5).rotated(Vector3.BACK, -INRUN_ANGLE)
			_anim(_jumper, "tuck" if j.tuck > 0.5 else "idle")
			# behind and above, riding down the track with the jumper
			var cam := inrun_point(maxf(-2.0, j.along - 7.0)) + Vector3(0, 1.9, 4.2)
			var ahead := inrun_point(minf(SkiJump.INRUN, j.along + 8.0))
			if j.phase == WinterEvent.Phase.READY and j.phase_left > 2.7:
				_snap_camera(cam, ahead)
			_move_camera(cam, ahead, delta, 6.0)
		SkiJump.Stage.FLIGHT:
			pos = JUMP + Vector3(j.fly.x, j.fly.y + 0.3, 0)
			_jumper.basis = Basis(Vector3.UP, PI * 0.5).rotated(Vector3.BACK, -0.15 - j.angle * 0.8)
			_anim(_jumper, "flight")
			if cut:  # the TV cut to the side camera at the lip
				_snap_camera(pos + Vector3(-3.0, 2.0, 13.0), pos + Vector3(5.0, -1.5, 0))
			_move_camera(pos + Vector3(-3.0, 2.0, 13.0), pos + Vector3(5.0, -1.5, 0), delta, 4.0)
			_landed_x = j.fly.x
		SkiJump.Stage.LANDED:
			_slide += delta * maxf(0.0, 22.0 - _slide * 0.2)
			var x := minf(_landed_x + _slide, 200.0)
			pos = hill_point(x) + Vector3(0, 0.1, 0)
			_jumper.basis = Basis(Vector3.UP, PI * 0.5)
			_anim(_jumper, "fall" if j.fell else ("telemark" if _slide < 20.0 else "celebrate"))
			_move_camera(pos + Vector3(-6.0, 3.5, 14.0), pos + Vector3(3.0, 0.5, 0), delta, 2.5)
	_jumper.position = pos
