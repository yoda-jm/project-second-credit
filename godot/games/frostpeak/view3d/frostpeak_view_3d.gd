class_name FrostpeakView3D
extends Node3D
## Frostpeak Games in 3D: three venues in one snowy valley ringed by mountains. The speed-skating oval sits at the
## origin, the K90 jump hill at JUMP, the medal plaza with the podium and the cauldron at PLAZA. The venues are
## built from the events' own geometry (lane lengths, in-run slope, landing curve) so the picture matches the rules.
## Banners and painted lettering are drawn once into textures at start (invented names only, no sponsors).

const M := "res://games/frostpeak/art/models/"
const SH := "res://games/frostpeak/shaders/"
const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage
const STRAIGHT := 100.0
const RADIUS := 30.0
const LANES: Array[float] = [2.0, 6.0]  ## lane centres, out from the inner radius (player, rival)
const JUMP := Vector3(700, 56.0, 0)  ## the lip; the outrun, 56 m below, meets the valley floor
const PLAZA := Vector3(-500, 0, 0)
const INRUN_ANGLE := deg_to_rad(35.0)
const BOARDS := 10.5  ## the padded boards, out from the inner radius
const STAND_Z := RADIUS + 13.0  ## the grandstand's front wall, along the front straight
const STAGE_Y := 0.46  ## the medal stage lifts the podium blocks
## the grandstand model's tiers (tools/blender/frostpeak_models.py): row i's tread starts TREAD * i behind Y0,
## its top is RISE * i above Z0; sections are SEC metres wide with SEATS seats a row
const SEC := 24.0
const ROWS := 12
const Y0 := 0.6
const TREAD := 0.85
const Z0 := 1.0
const RISE := 0.42
const SEATS := 40
const COATS: Array[Color] = [Color(0.8, 0.12, 0.12), Color(0.15, 0.3, 0.75), Color(0.95, 0.75, 0.15), Color(0.15, 0.5, 0.3),
	Color(0.92, 0.92, 0.92), Color(0.1, 0.1, 0.12), Color(0.1, 0.12, 0.25), Color(0.3, 0.32, 0.38), Color(0.95, 0.45, 0.1),
	Color(0.12, 0.15, 0.3), Color(0.5, 0.33, 0.2), Color(0.2, 0.22, 0.26), Color(0.8, 0.12, 0.12), Color(0.15, 0.3, 0.75),
	Color(0.55, 0.1, 0.15), Color(0.1, 0.45, 0.5)]
const HATS: Array[Color] = [Color(0.95, 0.95, 0.95), Color(0.85, 0.1, 0.12), Color(0.1, 0.25, 0.7), Color(0.95, 0.8, 0.1),
	Color(0.1, 0.5, 0.25), Color(0.95, 0.5, 0.1), Color(0.6, 0.2, 0.6), Color(0.1, 0.1, 0.1)]

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
var _paint: Array = []  ## [SubViewport, Callable(texture)]: text drawn once, then baked into mipmapped textures
var _boards: Array[Label3D] = []  ## scoreboard lines, rewritten live
var _crowd_mats := {}
var _flag_shader: Shader
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 77
	_flag_shader = load(SH + "flag.gdshader")
	_snow_mat = ShaderMaterial.new()
	_snow_mat.shader = load(SH + "snow.gdshader")
	_ice_mat = ShaderMaterial.new()
	_ice_mat.shader = load(SH + "ice.gdshader")
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
	_bake.call_deferred()


# ------------------------------------------------------------------ helpers

func _scene(name: String) -> Node3D:
	return (load(M + name + ".glb") as PackedScene).instantiate()


func _prop(name: String, pos: Vector3, yaw := 0.0, scale := 1.0) -> Node3D:
	var n := _scene(name)
	n.position = pos
	n.rotation.y = yaw
	n.scale = Vector3.ONE * scale
	add_child(n)
	_texture(n)
	return n


## Gives the props' plain Blender colours real surfaces from the shared CC0 sets: concrete, timber, steel sheet.
func _texture(n: Node3D) -> void:
	var swap := {
		"stand_concrete": Pbr.material("metal", Color(0.92, 0.92, 0.93), 0.35, 0.0, 1.2),
		"timber": Pbr.local("planks", Color(0.7, 0.5, 0.35), 0.8),
		"roof": Pbr.material("metal", Color(0.85, 0.87, 0.9), 0.5, 0.7, 0.6),
		"cladding": Pbr.material("metal", Color(0.42, 0.48, 0.58), 0.7, 0.6, 0.8),
		"plinth": Pbr.material("stone_bricks", Color(0.85, 0.86, 0.9), 0.8),
	}
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and swap.has(mat.resource_name):
				m.set_surface_override_material(i, swap[mat.resource_name])


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


## Paints an athlete in its nation's colours: the suit in the flag's first colour, the panels and stripes in
## whichever other flag colour stands out from it.
func _dress(n: Node3D, nation: int) -> void:
	var flag: Array = Competition.NATIONS[nation]["flag"]
	var col: Color = flag[0]
	var accent: Color = flag[2]
	if _color_dist(accent, col) < 0.3:
		accent = flag[1]
	if _color_dist(accent, col) < 0.3:
		accent = Color(0.1, 0.1, 0.12)
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and mat.resource_name in ["suit", "suit_accent"]:
				var s := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				s.albedo_color = col if mat.resource_name == "suit" else accent
				m.set_surface_override_material(i, s)


func _color_dist(a: Color, b: Color) -> float:
	return Vector3(a.r - b.r, a.g - b.g, a.b - b.b).length()


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


func _first_mesh(model: String) -> Mesh:
	var root := _scene(model)
	var mesh: Mesh = null
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		mesh = (mi as MeshInstance3D).mesh
		break
	root.free()
	return mesh


## Many copies of one model in a MultiMesh. `overrides` swaps materials by name (on a copy of the mesh);
## `colors` and `customs` fill the per-instance colour and custom data the crowd shader reads.
func _multi(model: String, xforms: Array[Transform3D], overrides := {}, colors: Array[Color] = [], customs: Array[Color] = []) -> MultiMeshInstance3D:
	var mesh := _first_mesh(model)
	if not overrides.is_empty():
		mesh = mesh.duplicate() as Mesh
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i)
			var key := mat.resource_name if mat else ""
			if overrides.has(key):
				mesh.surface_set_material(i, overrides[key])
			elif overrides.has("*"):
				mesh.surface_set_material(i, overrides["*"])
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = not colors.is_empty()
	mm.use_custom_data = not customs.is_empty()
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
		if mm.use_colors:
			mm.set_instance_color(i, colors[i % colors.size()])
		if mm.use_custom_data:
			mm.set_instance_custom_data(i, customs[i % customs.size()])
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	add_child(inst)
	return inst


## Spectators: three poses mixed, each with its own coat, hat, scarf and skin tone.
func _crowd(xforms: Array[Transform3D], seed: int, hop := 1.0) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var groups := {"spectator": [], "spectator_clap": [], "spectator_flag": []}
	for x in xforms:
		var r := rng.randf()
		groups["spectator" if r < 0.45 else ("spectator_clap" if r < 0.8 else "spectator_flag")].append(x)
	for model in groups:
		var xs: Array[Transform3D] = []
		xs.assign(groups[model])
		if xs.is_empty():
			continue
		var cols: Array[Color] = []
		var cus: Array[Color] = []
		for i in xs.size():
			cols.append(COATS[rng.randi() % COATS.size()])
			var h: Color = HATS[rng.randi() % HATS.size()]
			if model == "spectator_flag":  # the flag held up is a nation's
				var fl: Array = Competition.NATIONS[rng.randi() % Competition.NATIONS.size()]["flag"]
				h = fl[0]
			h.a = rng.randf() * rng.randf()
			cus.append(h)
		_multi(model, xs, _crowd_overrides(hop), cols, cus)


func _crowd_overrides(hop: float) -> Dictionary:
	var key := str(hop)
	if not _crowd_mats.has(key):
		var sh: Shader = load(SH + "crowd.gdshader")
		var d := {}
		for pair in [["coat", 0, Color.WHITE], ["hat", 1, Color.WHITE], ["scarf", 1, Color.WHITE], ["face", 2, Color.WHITE],
				["trousers", 3, Color(0.13, 0.13, 0.17)], ["spectator_boots", 3, Color(0.2, 0.14, 0.1)], ["dark_steel", 3, Color(0.2, 0.2, 0.22)]]:
			var m := ShaderMaterial.new()
			m.shader = sh
			m.set_shader_parameter("part", pair[1])
			m.set_shader_parameter("base", pair[2])
			m.set_shader_parameter("hop", hop)
			d[pair[0]] = m
		_crowd_mats[key] = d
	return _crowd_mats[key]


## Conifers, a mix of broad pines and slender spruces, with snow lying on the branches.
func _forest(xforms: Array[Transform3D], seed: int) -> void:
	var tm := ShaderMaterial.new()
	tm.shader = load(SH + "tree.gdshader")
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var pines: Array[Transform3D] = []
	var spruces: Array[Transform3D] = []
	for x in xforms:
		(pines if rng.randf() < 0.55 else spruces).append(x)
	_multi("snowy_pine", pines, {"pine_needles": tm})
	_multi("snowy_spruce", spruces, {"pine_needles": tm})


func _flag(pos: Vector3, cols: Array, size := Vector2(2.0, 1.3), yaw := 0.0) -> MeshInstance3D:
	var flag := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = size
	pm.subdivide_width = 12
	pm.subdivide_depth = 4
	pm.orientation = PlaneMesh.FACE_Z
	flag.mesh = pm
	var fm := ShaderMaterial.new()
	fm.shader = _flag_shader
	if cols.size() == 3:
		fm.set_shader_parameter("c0", cols[0])
		fm.set_shader_parameter("c1", cols[1])
		fm.set_shader_parameter("c2", cols[2])
	flag.material_override = fm
	flag.position = pos
	flag.rotation.y = yaw
	add_child(flag)
	return flag


## A flagpole with its nation's flag, the flag's inner edge on the pole.
func _pole_flag(base: Vector3, nation: int, yaw := 0.0) -> void:
	_prop("flagpole", base, yaw)
	_flag(base + Basis(Vector3.UP, yaw) * Vector3(1.07, 7.2, 0), Competition.NATIONS[nation % Competition.NATIONS.size()]["flag"], Vector2(2.0, 1.3), yaw)


## Text drawn once into a texture (a SubViewport, later baked with mipmaps). `use` receives the texture.
func _text_tex(text: String, size: Vector2i, fg: Color, bg: Color, font_size: int, use: Callable, band := Color(0, 0, 0, 0)) -> void:
	var sv := SubViewport.new()
	sv.size = size
	sv.disable_3d = true
	sv.transparent_bg = bg.a < 1.0
	sv.render_target_update_mode = SubViewport.UPDATE_ONCE
	if bg.a > 0.0:
		var cr := ColorRect.new()
		cr.color = bg
		cr.size = Vector2(size)
		sv.add_child(cr)
	if band.a > 0.0:  # two thin stripes along the top and bottom edges
		for y in [size.y * 0.08, size.y * 0.86]:
			var st := ColorRect.new()
			st.color = band
			st.position = Vector2(0, y)
			st.size = Vector2(size.x, size.y * 0.06)
			sv.add_child(st)
	var lb := Label.new()
	lb.text = text
	lb.add_theme_font_override("font", HudKit.font(true))
	lb.add_theme_font_size_override("font_size", font_size)
	lb.add_theme_color_override("font_color", fg)
	lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lb.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lb.size = Vector2(size)
	sv.add_child(lb)
	add_child(sv)
	use.call(sv.get_texture())
	_paint.append([sv, use])


## Once the text viewports have drawn, keep their pictures as mipmapped textures (crisp far away) and free them.
func _bake() -> void:
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	for p in _paint:
		var sv: SubViewport = p[0]
		var img := sv.get_texture().get_image()
		if img and not img.is_empty():
			img.generate_mipmaps()
			(p[1] as Callable).call(ImageTexture.create_from_image(img))
		sv.queue_free()
	_paint.clear()


## An invented banner: a word on a coloured ground with a pinstripe.
func _banner_mat(text: String, fg: Color, bg: Color, band := Color(0, 0, 0, 0)) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.roughness = 0.55
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_text_tex(text, Vector2i(1024, 128), fg, bg, 78, func(t: Texture2D) -> void: m.albedo_texture = t, band)
	return m


func _banner_set() -> Array[StandardMaterial3D]:
	var out: Array[StandardMaterial3D] = []
	var gold := Color(1.0, 0.82, 0.25)
	out.append(_banner_mat("FROSTPEAK", Color.WHITE, Color(0.1, 0.25, 0.65), gold))
	out.append(_banner_mat("GO FOR GOLD", gold, Color(0.06, 0.08, 0.16)))
	for n in Competition.NATIONS:
		var fl: Array = n["flag"]
		var bg: Color = fl[0]
		var fg: Color = fl[1] if _color_dist(fl[1], bg) > 0.4 else (Color.WHITE if bg.get_luminance() < 0.6 else Color(0.08, 0.08, 0.12))
		out.append(_banner_mat(str(n["name"]).to_upper(), fg, bg, fl[2] if _color_dist(fl[2], bg) > 0.3 else Color(0, 0, 0, 0)))
	out.append(_banner_mat("VALLEY OF ICE", Color(0.1, 0.25, 0.6), Color(0.95, 0.96, 0.98), Color(0.1, 0.25, 0.6)))
	return out


func _quad(pos: Vector3, size: Vector2, mat: Material, basis: Basis) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = size
	mi.mesh = q
	mi.material_override = mat
	mi.transform = Transform3D(basis, pos)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


## A line of text on a scoreboard screen: bright, unshaded, amber or white like LED panels.
func _led(parent: Node3D, pos: Vector3, text: String, size: int, col: Color) -> Label3D:
	var lb := Label3D.new()
	lb.text = text
	lb.font = HudKit.font(true)
	lb.font_size = size
	lb.pixel_size = 0.01
	lb.modulate = col
	lb.outline_size = 0
	lb.position = pos
	lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	parent.add_child(lb)
	return lb


## A scoreboard: a title row and two result rows the game rewrites while the event runs.
func _scoreboard(pos: Vector3, yaw: float, title: String) -> void:
	var sb := _prop("scoreboard", pos, yaw)
	var face := 0.19  # the screen, in front of the frame (the model faces +Z)
	var t := _led(sb, Vector3(0, 10.2, face), title, 96, Color(1.0, 0.75, 0.25))
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var a := _led(sb, Vector3(0, 8.6, face), "", 88, Color(0.95, 0.97, 1.0))
	a.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var b := _led(sb, Vector3(0, 7.2, face), "", 88, Color(0.95, 0.97, 1.0))
	b.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boards.append(a)
	_boards.append(b)


# ------------------------------------------------------------------ world

func _build_world() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.16, 0.36, 0.78)
	sky_mat.sky_horizon_color = Color(0.7, 0.8, 0.93)
	sky_mat.sky_curve = 0.12
	sky_mat.ground_horizon_color = Color(0.78, 0.84, 0.94)
	sky_mat.ground_bottom_color = Color(0.6, 0.66, 0.78)
	sky_mat.sun_angle_max = 12.0
	sky_mat.sun_curve = 0.08
	var sky := Sky.new()
	sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	Look.sky_ambient(env, Color(0.7, 0.75, 0.86), 0.6)
	if not Look.compat():  # part sky, part a neutral fill: blue shadows on the snow, but not ink-blue
		env.ambient_light_color = Color(0.78, 0.8, 0.86)
		env.ambient_light_sky_contribution = 0.55
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.88
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.45
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.1
	env.ssao_enabled = true
	env.ssao_radius = 1.2
	env.ssao_intensity = 1.6
	env.ssr_enabled = true  # the ice reflects the stand, the floodlights and the skaters
	env.ssr_max_steps = 48
	Look.fog(env, Color(0.78, 0.85, 0.95), 0.00035)
	env.fog_aerial_perspective = 0.55
	env.fog_sky_affect = 0.4
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.12
	env.adjustment_contrast = 1.1
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.rotation_degrees = Vector3(-30, -62, 0)  # low winter sun from the side: long shadows, relief on the snow
	_sun.light_color = Color(1.0, 0.94, 0.84)
	_sun.light_energy = 1.45
	_sun.light_angular_distance = 0.3
	_sun.shadow_enabled = true
	_sun.shadow_blur = 0.6
	_sun.directional_shadow_max_distance = 260.0
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
	q.size = Vector2(0.1, 0.1)
	_snowfall.draw_pass_1 = q
	_snowfall.material_override = Fx.material("soft", Color(1, 1, 1, 0.85))
	add_child(_snowfall)


## A ring of craggy peaks around the valley: ridged noise for sharp crests, rock on the steep faces, snow on the
## rest; foothills with forests in front, and the snowy valley floor.
func _build_mountains() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ridge := FastNoiseLite.new()
	ridge.seed = 5
	ridge.frequency = 0.0014
	ridge.fractal_type = FastNoiseLite.FRACTAL_RIDGED
	ridge.fractal_octaves = 4
	ridge.fractal_lacunarity = 2.1
	ridge.fractal_gain = 0.45
	var base := FastNoiseLite.new()
	base.seed = 11
	base.frequency = 0.0009
	var centre := Vector3(100, 0, 0)
	var radii: Array[float] = []
	var r := 1000.0
	while r <= 2600.0:
		radii.append(r)
		r += 40.0 if r < 1500.0 else 70.0
	var steps := 360
	var pts := []
	for ri in radii.size():
		var row := []
		for k in steps + 1:
			var a := TAU * k / steps
			var p := centre + Vector3(cos(a) * radii[ri], 0, sin(a) * radii[ri])
			var rr := radii[ri]
			# the envelope: rising from the valley edge, crests around 1500-2000 m out, a last high ridge behind
			var env := smoothstep(1000.0, 1500.0, rr) * (0.75 + 0.25 * smoothstep(2000.0, 2500.0, rr))
			var rn := ridge.get_noise_2d(p.x, p.z) * 0.5 + 0.5
			var bn := base.get_noise_2d(p.x, p.z) * 0.5 + 0.5
			p.y = env * (pow(rn, 1.4) * 420.0 + bn * 300.0) - 30.0 + smoothstep(1000.0, 1150.0, rr) * 20.0
			row.append(p)
		pts.append(row)
	for ri in radii.size() - 1:
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
	m.shader = load(SH + "mountain.gdshader")
	m.set_shader_parameter("rock_tex", load("res://core/art/textures/rock/albedo.jpg"))
	m.set_shader_parameter("rock_nrm", load("res://core/art/textures/rock/normal.jpg"))
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	# the valley floor
	var floor := MeshInstance3D.new()
	var pl := PlaneMesh.new()
	pl.size = Vector2(2300, 2300)
	pl.subdivide_width = 60
	pl.subdivide_depth = 60
	floor.mesh = pl
	floor.position = Vector3(100, -0.1, 0)
	floor.material_override = _snow_mat
	add_child(floor)
	# forests: thick on the valley edges, scattered in the middle, kept off the venues
	var rng := RandomNumberGenerator.new()
	rng.seed = 12
	var trees: Array[Transform3D] = []
	var rocks: Array[Transform3D] = []
	for i in 1100:
		var a := rng.randf() * TAU
		var rr := sqrt(rng.randf_range(0.03, 1.0)) * 960.0
		var p := Vector3(cos(a) * rr + 100.0, 0, sin(a) * rr)
		if p.distance_to(JUMP + Vector3(40, 0, 0)) < 170.0 or p.distance_to(PLAZA) < 60.0:
			continue
		if absf(p.z) < 95.0 and p.x > -120.0 and p.x < 180.0:  # the oval, its stand and car park
			continue
		# clumps: trees gather where a slow noise is high
		if sin(p.x * 0.013) * cos(p.z * 0.011) < -0.35 and rr < 800.0:
			continue
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.5, 3.2)), p))
		if rng.randf() < 0.08:
			rocks.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1, rng.randf_range(0.6, 1.2), 1) * rng.randf_range(1.0, 3.0)), p + Vector3(rng.randf_range(-8, 8), -0.2, rng.randf_range(-8, 8))))
	_forest(trees, 3)
	_multi("boulder", rocks)


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


func _ribbon(lane_r: float, width: float, mat: Material, y := 0.02, n := 240) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var per := 2.0 * STRAIGHT + TAU * (RADIUS + lane_r)
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
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


## A continuous profile swept round the oval: `profile` is [(out, up)] points across, from inside to outside.
## `keep` can skip stretches (returns false where nothing is built).
func _sweep(lane_r: float, profile: Array[Vector2], mat: Material, n := 240, keep := Callable(), bumps := 0.0) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var per := 2.0 * STRAIGHT + TAU * (RADIUS + lane_r)
	var noise := FastNoiseLite.new()
	noise.frequency = 0.08
	for i in n:
		var a := oval_point(per * i / n, lane_r)
		var b := oval_point(per * (i + 1) / n, lane_r)
		if keep.is_valid() and not (keep.call(a.origin) and keep.call(b.origin)):
			continue
		for k in profile.size() - 1:
			var q := []
			for t in [a, b]:
				for pk in [k, k + 1]:
					var pr: Vector2 = profile[pk]
					var o: Vector3 = t.origin
					var bump := noise.get_noise_2d(o.x + pr.x * 3.0, o.z) * bumps * pr.y
					q.append(o - t.basis.x * pr.x + Vector3(0, pr.y + bump, 0))
			for v in [q[0], q[2], q[3], q[0], q[3], q[1]]:
				st.add_vertex(v)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	add_child(mi)
	return mi


func _build_oval() -> void:
	# the ice: lanes from 0 to 8 m out, a warm-up strip inside, a white apron outside
	_ribbon(4.0, 12.0, _ice_mat, 0.0)
	_ribbon(-1.5, 3.0, _ice_mat, 0.0)
	var line_mat := func(c: Color) -> StandardMaterial3D:
		var m := _flat(c, 0.08)
		m.metallic_specular = 0.9
		return m
	_ribbon(0.0, 0.12, line_mat.call(Color(0.1, 0.3, 0.9)), 0.004, 480)
	_ribbon(4.0, 0.1, line_mat.call(Color(0.92, 0.15, 0.15)), 0.004, 480)
	_ribbon(8.0, 0.12, line_mat.call(Color(0.1, 0.3, 0.9)), 0.004, 480)
	_ribbon(-3.0, 0.1, line_mat.call(Color(0.95, 0.95, 0.95)), 0.004, 480)
	# the crossing zone on the back straight: lanes swap here, marked by a dashed band of diagonal stripes
	var cross := line_mat.call(Color(0.92, 0.15, 0.15)) as StandardMaterial3D
	for i in 16:
		var t := oval_point(STRAIGHT * 0.5 + 16.0 + i * 3.0, 4.0)
		var b := _box(self, t.origin + Vector3(0, 0.003, 0), Vector3(0.12, 0.004, 1.2), cross)
		b.basis = t.basis.rotated(Vector3.UP, 0.5)
	# the rubber lane blocks round the inside of the curves
	var blocks: Array[Transform3D] = []
	var per0 := 2.0 * STRAIGHT + TAU * RADIUS
	var s := STRAIGHT
	while s < per0:
		if (s > STRAIGHT and s < STRAIGHT + PI * RADIUS) or s > 2.0 * STRAIGHT + PI * RADIUS:
			blocks.append(oval_point(s, 0.0))
		s += 2.5
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.07
	cyl.bottom_radius = 0.09
	cyl.height = 0.1
	cyl.radial_segments = 10
	cyl.material = _flat(Color(0.95, 0.35, 0.1), 0.5)
	var bmm := MultiMesh.new()
	bmm.transform_format = MultiMesh.TRANSFORM_3D
	bmm.mesh = cyl
	bmm.instance_count = blocks.size()
	for i in blocks.size():
		bmm.set_instance_transform(i, Transform3D(Basis.IDENTITY, blocks[i].origin + Vector3(0, 0.05, 0)))
	var bmi := MultiMeshInstance3D.new()
	bmi.multimesh = bmm
	add_child(bmi)
	# the padded boards: a blue pad with a white cap all the way round
	var pad := _flat(Color(0.1, 0.24, 0.62), 0.55)
	var prof: Array[Vector2] = [Vector2(-0.25, 0.0), Vector2(-0.25, 0.95), Vector2(-0.15, 1.05), Vector2(0.15, 1.05), Vector2(0.25, 0.95), Vector2(0.25, 0.0)]
	_sweep(BOARDS, prof, pad, 300)
	var cap: Array[Vector2] = [Vector2(-0.18, 1.04), Vector2(-0.12, 1.1), Vector2(0.12, 1.1), Vector2(0.18, 1.04)]
	_sweep(BOARDS, cap, _flat(Color(0.95, 0.96, 0.98), 0.4), 300)
	# banners on the inside of the boards along both straights (the TV camera sees the far side)
	var banners := _banner_set()
	var bi := 0
	for side in [-1.0, 1.0]:
		for k in 12:
			var x := -45.0 + k * 90.0 / 11.0
			var z: float = side * (RADIUS + BOARDS - 0.27)
			var basis := Basis.IDENTITY if side < 0.0 else Basis(Vector3.UP, PI)
			_quad(Vector3(x, 0.5, z), Vector2(7.6, 0.85), banners[bi % banners.size()], basis)
			bi += 1
	# a plowed snow bank outside the boards (not in front of the grandstand)
	var bank: Array[Vector2] = [Vector2(0.4, -0.05), Vector2(1.0, 0.55), Vector2(2.0, 0.9), Vector2(3.2, 0.65), Vector2(4.4, -0.05)]
	var bank_mat := ShaderMaterial.new()
	bank_mat.shader = _snow_mat.shader
	bank_mat.set_shader_parameter("bump_scale", 0.6)
	_sweep(BOARDS, bank, bank_mat, 200, func(p: Vector3) -> bool: return not (p.z > 0.0 and absf(p.x) < STRAIGHT * 0.5 + 16.0), 0.8)
	# the finish arch and the finish line (the race starts on the back straight)
	var fin := oval_point(SpeedSkating.DISTANCE, LANES[0])
	var arch := _scene("finish_arch")
	arch.transform = Transform3D(fin.basis.rotated(Vector3.UP, PI * 0.5), oval_point(SpeedSkating.DISTANCE, 4.0).origin)
	add_child(arch)
	_box(self, fin.origin + Vector3(0, 0.004, 0) + fin.basis.x * 2.0, Vector3(0.3, 0.004, 9.0), line_mat.call(Color(0.9, 0.1, 0.1))).basis = fin.basis.rotated(Vector3.UP, PI * 0.5)
	var start := oval_point(0.0, 4.0)
	_box(self, start.origin + Vector3(0, 0.004, 0), Vector3(0.2, 0.004, 8.2), line_mat.call(Color(0.95, 0.95, 0.95))).basis = start.basis.rotated(Vector3.UP, PI * 0.5)
	_build_grandstand()
	# flags along the back straight, behind the snow bank
	for i in 12:
		_pole_flag(Vector3(-STRAIGHT * 0.5 + i * STRAIGHT / 11.0, 0, -RADIUS - 18.0), i)
	# the games' name painted into the infield snow, readable from the TV camera across the ice
	_snow_mat.set_shader_parameter("mark_rect", Vector4(-46.0, -12.0, 92.0, 24.0))
	_text_tex("FROSTPEAK", Vector2i(2048, 520), Color(0.12, 0.3, 0.8), Color(0, 0, 0, 0), 330,
		func(t: Texture2D) -> void: _snow_mat.set_shader_parameter("mark_tex", t))
	# floodlight masts at the four corners, TV towers on the infield, scoreboards at the ends of the stand
	for x in [-STRAIGHT * 0.5 - 22.0, STRAIGHT * 0.5 + 22.0]:
		for z in [-RADIUS - 26.0, RADIUS + 26.0]:
			_prop("floodlight", Vector3(x, 0, z), atan2(-x, -z))
	_prop("tv_tower", Vector3(-STRAIGHT * 0.5 - 12.0, 0, -8.0), PI * 0.75)
	_prop("tv_tower", Vector3(STRAIGHT * 0.5 + 12.0, 0, -8.0), -PI * 0.75)
	_prop("tv_tower", Vector3(0, 0, -RADIUS - 24.0), 0.0)
	_scoreboard(Vector3(-STRAIGHT * 0.5 - 30.0, 0, RADIUS + 22.0), PI - 0.5, "500 M")
	_scoreboard(Vector3(STRAIGHT * 0.5 + 30.0, 0, RADIUS + 22.0), PI + 0.5, "500 M")


## The grandstand: five roofed sections along the front straight, closed by end walls, full of fans; a row of
## nation flags on the roof edge and lettering on the fascia.
func _build_grandstand() -> void:
	var yaw := PI  # the models face +Z; the stand looks at the ice (-Z)
	var seats: Array[Transform3D] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	var fascia := _banner_mat("FROSTPEAK  GAMES", Color.WHITE, Color(0.1, 0.22, 0.55), Color(1.0, 0.82, 0.25))
	for k in 5:
		var cx := (k - 2) * SEC
		_prop("grandstand", Vector3(cx, 0, STAND_Z), yaw)
		for r in ROWS:
			for sidx in SEATS:
				if rng.randf() < 0.12:
					continue
				var xb := -SEC * 0.5 + 1.2 + (sidx + 0.5) * (SEC - 2.4) / SEATS + rng.randf_range(-0.05, 0.05)
				var p := Vector3(cx - xb, Z0 + r * RISE, STAND_Z + Y0 + r * TREAD + 0.14)
				seats.append(Transform3D(Basis(Vector3.UP, PI + rng.randf_range(-0.25, 0.25)).scaled(Vector3.ONE * rng.randf_range(0.92, 1.06)), p))
		# the fascia's lettering, under the roof edge
		_quad(Vector3(cx, 12.0, STAND_Z - 2.44), Vector2(SEC - 1.0, 1.1), fascia, Basis(Vector3.UP, PI))
	for x in [-SEC * 2.5 - 0.2, SEC * 2.5 + 0.2]:
		_prop("grandstand_end", Vector3(x, 0, STAND_Z), yaw)
	_crowd(seats, 5)
	for i in 11:
		var x := -SEC * 2.5 + 2.0 + i * (SEC * 5.0 - 4.0) / 10.0
		var base := Vector3(x, 13.3, STAND_Z + 4.0)
		var pole := _prop("flagpole", base)
		pole.scale = Vector3(1, 0.55, 1)
		_flag(base + Vector3(0.8, 3.7, 0), Competition.NATIONS[i % Competition.NATIONS.size()]["flag"], Vector2(1.5, 1.0))


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


## The terrain's height at (px, pz) relative to the lip, banks included.
func _terrain_y(px: float, pz: float) -> float:
	var y: float = _hill_y(clampf(px, -100.0, 170.0))
	var bank := maxf(0.0, absf(pz) - 17.0)
	y += minf(bank * 0.28 + bank * bank * 0.006, 24.0)  # gentle banks, not walls
	# far from the hill the mountainside settles down to the valley floor, with no edge to see
	var out := maxf(smoothstep(96.0, 160.0, absf(pz)), smoothstep(-110.0, -180.0, px))
	return lerpf(y, -JUMP.y, out)


func _ground(px: float, pz: float) -> Vector3:
	return JUMP + Vector3(px, _terrain_y(px, pz), pz)


func _build_hill() -> void:
	# the terrain: the landing hill and the outrun down the middle, forested banks rising on both sides
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var xs := []
	var x := -180.0
	while x <= 300.0:
		xs.append(x)
		x += 2.5 if x > -100.0 and x < 240.0 else 5.0
	var zs := []
	for k in 81:
		zs.append(-160.0 + k * 4.0)
	for i in xs.size() - 1:
		for k in zs.size() - 1:
			var p := []
			for c in [[i, k], [i + 1, k], [i + 1, k + 1], [i, k + 1]]:
				p.append(_ground(xs[c[0]], zs[c[1]]))
			for v in [p[0], p[2], p[1], p[0], p[3], p[2]]:
				st.add_vertex(v)
	st.generate_normals()
	var terrain := MeshInstance3D.new()
	terrain.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = _snow_mat.shader
	m.set_shader_parameter("shade", Color(0.8, 0.85, 0.95))
	m.set_shader_parameter("mark_tex", _markings())
	m.set_shader_parameter("mark_rect", Vector4(JUMP.x + 40.0, JUMP.z - 15.0, 100.0, 30.0))
	terrain.material_override = m
	add_child(terrain)
	var steel := Pbr.material("metal", Color(0.55, 0.58, 0.62), 1.0, 0.8, 0.5)
	var red := _flat(Color(0.8, 0.12, 0.12), 0.45)
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
	for zz in [-1.6, 1.6]:  # service walkways with railings either side of the track
		var walk := _box(self, mid + Vector3(0, -0.05, zz), Vector3(len, 0.08, 0.9), Pbr.material("metal", Color(0.4, 0.42, 0.46), 2.0, 0.8, 0.6))
		walk.basis = along_basis
		var rail := _box(self, mid + Vector3(0, 0.95, zz * 1.28), Vector3(len, 0.05, 0.05), steel)
		rail.basis = along_basis
	var lamp := _flat(Color(1.0, 0.95, 0.8), 0.3, 4.0)
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
		for zz in [-2.05, 2.05]:
			_box(self, p + Vector3(0, 0.5, zz), Vector3(0.05, 1.0, 0.05), steel)
		a += 7.0
	# the start house on its own trestle at the top, the take-off table at the lip
	var top_p := inrun_point(-2.0)
	var hp := top_p + Vector3(-8.0, -1.2, 0)
	_prop("start_house", hp, PI * 0.5)
	var hg := JUMP.y + _hill_y(hp.x - JUMP.x)
	for dx in [-2.6, 2.6]:
		for dz in [-2.6, 2.6]:
			_box(self, Vector3(hp.x + dx, (hp.y + hg) * 0.5, hp.z + dz), Vector3(0.4, hp.y - hg, 0.4), steel)
	_box(self, hp + Vector3(0, -0.15, 0), Vector3(6.4, 0.3, 6.4), steel)
	var gate := _scene("start_gate")
	gate.position = inrun_point(0.0) + Vector3(0, 0.45, 0)
	gate.rotation.y = PI * 0.5
	add_child(gate)
	var table := _box(self, JUMP + Vector3(-3.0, -0.25, 0), Vector3(6.0, 0.7, 3.2), Pbr.material("planks", Color(0.75, 0.55, 0.38), 1.5))
	table.basis = Basis(Vector3.BACK, -0.18)
	# the judges' tower beside the knoll, glazed side to the landing
	_prop("judges_tower", _ground(55.0, -36.0) + Vector3(0, -0.5, 0), 0.3)
	_prop("tv_tower", _ground(25.0, -24.0), -0.6)
	_prop("tv_tower", _ground(150.0, 26.0), PI + 0.9)
	# padded fences along the landing hill, dressed with banners (inside faces)
	var banners := _banner_set()
	var fx := 8.0
	var bi := 0
	var pad := _flat(Color(0.1, 0.24, 0.62), 0.55)
	while fx < 175.0:
		for zz in [-16.5, 16.5]:
			var p0 := hill_point(fx)
			var p1 := hill_point(fx + 6.0)
			var mp := (p0 + p1) * 0.5 + Vector3(0, 0.55, zz)
			var tilt := Basis(Vector3.BACK, atan2(p1.y - p0.y, 6.0))
			var seg := _box(self, mp, Vector3(6.05, 1.1, 0.25), pad)
			seg.basis = tilt
			var face: float = -0.13 if zz > 0.0 else 0.13
			_quad(mp + Vector3(0, 0, face), Vector2(5.9, 0.9), banners[bi % banners.size()], tilt * (Basis(Vector3.UP, PI) if zz > 0.0 else Basis.IDENTITY))
			bi += 1
		fx += 6.0
	# distance boards on posts beside the fence, the K point in red
	for d in range(60, 131, 10):
		var bp := hill_point(d) + Vector3(0, 0, -18.2)
		bp.y = JUMP.y + _terrain_y(d, -18.2)
		_box(self, bp + Vector3(0, 1.4, 0), Vector3(0.1, 2.8, 0.1), steel)
		var board := _box(self, bp + Vector3(0, 2.6, 0), Vector3(2.2, 1.1, 0.1), _flat(Color(0.95, 0.95, 0.97) if d != 90 else Color(0.85, 0.1, 0.12), 0.5))
		var lb := Label3D.new()
		lb.text = str(d)
		lb.font = HudKit.font(true)
		lb.font_size = 120
		lb.pixel_size = 0.008
		lb.shaded = true
		lb.modulate = Color(0.1, 0.2, 0.6) if d != 90 else Color.WHITE
		lb.outline_size = 0
		lb.position = Vector3(0, 0, 0.06)
		board.add_child(lb)
	# the outrun: a curved barrier with banners, flags, the scoreboard and the crowd on terraces
	for i in 13:
		var ang := -1.0 + i * (2.0 / 12.0)
		var bp := hill_point(200.0) + Vector3(cos(ang) * 6.0 - 6.0, 0.6, sin(ang) * 18.0)
		var b := _box(self, bp, Vector3(0.4, 1.2, 3.2), pad)
		b.rotation.y = -ang
		var q := _quad(bp + Vector3(-0.21, 0, 0).rotated(Vector3.UP, -ang), Vector2(3.1, 1.0), banners[(i + 3) % banners.size()], Basis(Vector3.UP, -PI * 0.5 - ang))
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for i in 8:
		var fzz := -26.0 + i * 7.4
		_pole_flag(_ground(213.0, fzz), i)
	_scoreboard(_ground(236.0, -34.0), -PI * 0.5 + 0.45, "K 90")
	var fans: Array[Transform3D] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 9
	for i in 900:
		var fxx := rng.randf_range(206.0, 228.0)
		var fz := rng.randf_range(-32.0, 32.0)
		fans.append(Transform3D(Basis(Vector3.UP, -PI * 0.5 + rng.randf_range(-0.4, 0.4)), _ground(fxx, fz)))
	for i in 260:  # more fans along the fences of the lower hill
		var fxx := rng.randf_range(110.0, 195.0)
		var side := -1.0 if i % 2 == 0 else 1.0
		var fz := side * rng.randf_range(18.5, 24.0)
		fans.append(Transform3D(Basis(Vector3.UP, (0.0 if side < 0.0 else PI) + rng.randf_range(-0.4, 0.4)), _ground(fxx, fz)))
	_crowd(fans, 17)
	# the forest on the banks, with a few rocks
	var trees: Array[Transform3D] = []
	var rocks: Array[Transform3D] = []
	for i in 520:
		var tx := rng.randf_range(-120.0, 250.0)
		var side := -1.0 if i % 2 == 0 else 1.0
		var tz := side * rng.randf_range(26.0, 110.0)
		if tx > 195.0 and absf(tz) < 45.0:
			continue
		if absf(tx - 55.0) < 10.0 and absf(tz + 36.0) < 8.0:
			continue
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.4, 3.0)), _ground(tx, tz)))
		if i % 11 == 0:
			rocks.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.8, 2.2)), _ground(tx + 3.0, tz) - Vector3(0, 0.3, 0)))
	_forest(trees, 8)
	_multi("boulder", rocks)
	for zz in [-30.0, 30.0]:
		_prop("floodlight", _ground(70.0, zz), 0.0 if zz < 0.0 else PI)


## The hill's painted lines: blue every 10 m, red at the K point, green at the hill size (world XZ over 100 x 30 m
## from x = 40), each broken into dashes like spray paint on snow.
func _markings() -> ImageTexture:
	var img := Image.create(400, 60, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for d in range(40, 141, 10):
		var px := int((d - 40) * 4.0)
		var col := Color(0.85, 0.1, 0.1, 0.95) if d == 90 else Color(0.15, 0.3, 0.85, 0.8)
		for w in 2:
			for y in 60:
				img.set_pixel(clampi(px + w, 0, 399), y, col)
	for y in 60:  # the hill size, a green line at 100 m
		img.set_pixel(240 + 1, y, Color(0.1, 0.6, 0.25, 0.9))
	var t := ImageTexture.create_from_image(img)
	return t


# ------------------------------------------------------------------ the plaza

func _build_plaza() -> void:
	# the plaza: a paved circle cleared of snow, with a low wall of snow around it
	var paving := MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 26.0
	disc.bottom_radius = 26.5
	disc.height = 0.2
	disc.radial_segments = 64
	paving.mesh = disc
	paving.material_override = Pbr.material("stone_bricks", Color(1.5, 1.5, 1.65), 0.35)
	paving.position = PLAZA + Vector3(-4.0, -0.08, 2.0)
	add_child(paving)
	var pod := _prop("podium", PLAZA + Vector3(0, STAGE_Y, 0), PI)
	pod.name = "Podium"
	for i in 3:
		_prop("flagpole", PLAZA + Vector3((i - 1) * 2.4, 0, 6.0))
		var flag := _flag(PLAZA + Vector3((i - 1) * 2.4 + 1.07, 1.0, 5.95), [])
		_flags.append(flag)
	var c := _prop("cauldron", PLAZA + Vector3(-12.0, 0, 4.0))
	var fire := OmniLight3D.new()
	fire.position = c.position + Vector3(0, 4.4, 0)
	fire.light_color = Color(1.0, 0.6, 0.25)
	fire.light_energy = 3.0
	fire.omni_range = 18.0
	add_child(fire)
	var sparks := GPUParticles3D.new()
	sparks.amount = 60
	sparks.lifetime = 1.6
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 0.6
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 20.0
	pm.initial_velocity_min = 1.5
	pm.initial_velocity_max = 3.0
	pm.gravity = Vector3(0, 0.6, 0)
	pm.scale_min = 0.4
	pm.scale_max = 1.0
	sparks.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.35, 0.35)
	sparks.draw_pass_1 = q
	sparks.material_override = Fx.material("glow", Color(1.0, 0.6, 0.2))
	sparks.position = c.position + Vector3(0, 4.0, 0)
	add_child(sparks)
	for i in 3:
		var a := _athlete("skater")
		_podium_people.append(a)
	# lamp posts and nation flags round the plaza, banners on low boards, trees behind
	var banners := _banner_set()
	for i in 10:
		var ang := -2.4 + i * (4.8 / 9.0)
		var p := PLAZA + Vector3(-4.0, 0, 2.0) + Vector3(sin(ang) * 25.0, 0, -cos(ang) * 25.0)
		_pole_flag(p, i, -ang)
	for i in 6:
		var ang := -1.9 + i * (3.8 / 5.0)
		var p := PLAZA + Vector3(sin(ang) * 12.5, 0, -cos(ang) * 12.5)
		var yaw := -ang
		var b := _box(self, p + Vector3(0, 0.45, 0), Vector3(3.6, 0.9, 0.15), _flat(Color(0.1, 0.24, 0.62), 0.55))
		b.rotation.y = yaw
		_quad(p + Vector3(0, 0.45, 0) + Basis(Vector3.UP, yaw) * Vector3(0, 0, 0.08), Vector2(3.5, 0.8), banners[i % banners.size()], Basis(Vector3.UP, yaw))
	var fans: Array[Transform3D] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 21
	for i in 220:
		var a := rng.randf_range(-2.2, 2.2)
		var r := rng.randf_range(14.0, 22.0)
		var p := PLAZA + Vector3(sin(a) * r, 0, -cos(a) * r)
		fans.append(Transform3D(Basis.looking_at(PLAZA - p, Vector3.UP).rotated(Vector3.UP, PI), p))
	_crowd(fans, 23)
	var trees: Array[Transform3D] = []
	for i in 60:
		var a := rng.randf() * TAU
		var r := rng.randf_range(32.0, 55.0)
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.2, 2.4)), PLAZA + Vector3(cos(a) * r - 4.0, 0, sin(a) * r)))
	_forest(trees, 31)


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
		# the podium model is turned to face the camera: silver stands to the winner's right, on screen left
		var spots := [Vector3(0, 1.2 + STAGE_Y, 0), Vector3(1.45, 0.85 + STAGE_Y, 0), Vector3(-1.45, 0.55 + STAGE_Y, 0)]
		for place in mini(3, rk.size()):
			var a := _podium_people[place]
			a.visible = true
			a.position = PLAZA + spots[place]
			a.rotation.y = PI
			_dress(a, game.comp.athletes[rk[place]]["nation"])
			_anim(a, "wave" if place == 0 else "idle")
			_set_flag([1, 2, 0][place], game.comp.athletes[rk[place]]["nation"])
			_flags[[1, 2, 0][place]].position.y = 1.0


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
	_update_boards()


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
			pos.y = maxf(pos.y, JUMP.y + _hill_y(j.fly.x) + 0.45)  # the coarse hill mesh must never swallow the skis
			_jumper.basis = Basis(Vector3.UP, PI * 0.5).rotated(Vector3.BACK, -0.15 - j.angle * 0.8)
			_anim(_jumper, "flight")
			# the TV chase camera: locked to the jumper (a smoothed camera would trail far behind at this speed),
			# beside and a little above, easing out as the flight goes on so the landing hill comes into view
			var out := clampf(j.fly.x / 90.0, 0.0, 1.0)
			var cam := pos + Vector3(-2.5 - out * 1.5, 1.4 + out * 1.6, 6.5 + out * 3.0)
			cam.y = maxf(cam.y, JUMP.y + _hill_y(cam.x - JUMP.x) + 2.5)  # never under the slope behind the jumper
			_snap_camera(cam, pos + Vector3(2.5 + out * 2.0, -0.4 - out * 0.8, 0))  # aimed at the jumper, a little ahead
			_landed_x = j.fly.x
		SkiJump.Stage.LANDED:
			_slide += delta * maxf(0.0, 22.0 - _slide * 0.2)
			var x := minf(_landed_x + _slide, 200.0)
			pos = hill_point(x) + Vector3(0, 0.1, 0)
			_jumper.basis = Basis(Vector3.UP, PI * 0.5)
			_anim(_jumper, "fall" if j.fell else ("telemark" if _slide < 20.0 else "celebrate"))
			# still locked to the jumper while they slide fast, then easing back for the celebration
			var back := clampf(_slide / 60.0, 0.0, 1.0)
			_snap_camera(pos + Vector3(-4.0 - back * 3.0, 2.2 + back * 1.5, 8.0 + back * 5.0), pos + Vector3(3.0 - back * 2.0, 0.6, 0))
	_jumper.position = pos


## The scoreboards follow the event: the running time and the rival's distance on the oval, the distance on the hill.
func _update_boards() -> void:
	if game.comp == null or game.ev == null or _boards.is_empty() or not game.stage in [S.ATTEMPT, S.RESULT]:
		return
	var hs := game.humans()
	if game.athlete >= hs.size():
		return
	var nation: int = game.comp.athletes[hs[game.athlete]]["nation"]
	var code: String = Competition.NATIONS[nation]["code"]
	var a := ""
	var b := ""
	if game.ev is SpeedSkating:
		var s := game.ev as SpeedSkating
		var rival: String = Competition.NATIONS[(nation + 3) % Competition.NATIONS.size()]["code"]
		a = "%s  %05.2f" % [code, s.result if s.result > 0.0 else s.time]
		b = "%s  %3d M" % [rival, int(minf(s.rival_pos, SpeedSkating.DISTANCE))]
	elif game.ev is SkiJump:
		var j := game.ev as SkiJump
		a = "%s  %s" % [code, ("%.1f M" % j.distance) if j.stage == SkiJump.Stage.LANDED else "- - -"]
		b = "HS 100"
	for i in _boards.size():
		var lb := _boards[i]
		var txt := a if i % 2 == 0 else b
		if lb.text != txt:
			lb.text = txt
