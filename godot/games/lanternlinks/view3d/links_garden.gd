class_name LinksGarden
extends Node3D
## The lantern garden round the course: the sky dome (sun or moon, clouds, stars, far hills with a town), the lawn,
## and round each hole its dressing: lantern posts whose paper lanterns are real lights, string lights swinging
## between them, two floodlights for the night, trees, shrubs, rocks, stone lanterns, a bench, a gazebo or a
## fountain, flowers in the beds, fireflies. The round runs from golden hour (hole 1) into the night (the last
## hole): `set_time` moves the sun, the sky, the fog and the lights along that evening, smoothly.

const H = preload("res://games/lanternlinks/engine/links_hole.gd")
const C = preload("res://games/lanternlinks/view3d/links_course.gd")
const M := "res://games/lanternlinks/art/models/"
const SH := "res://games/lanternlinks/shaders/"
const LANTERN := Color(1.0, 0.66, 0.36)

var env: Environment
var sun: DirectionalLight3D
var moon: DirectionalLight3D
var sky_mat: ShaderMaterial
var _we: WorldEnvironment
var _dome: MeshInstance3D
var _dress: Node3D
var _lights: Array[OmniLight3D] = []
var _floods: Array[SpotLight3D] = []
var _glows: Array[Material] = []       ## lantern paper, bulbs, windows: brighter as night falls
var _bulbs: MultiMeshInstance3D
var _flies: CPUParticles3D
var _scenes := {}
var _tod := 0.0
var _tod_target := 0.0
var _time := 0.0
var _course: LinksCourse


func build() -> void:
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.1, 0.1, 0.15)
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.0
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.8)
	env.set_glow_level(4, 0.6)
	env.fog_enabled = true
	env.fog_sky_affect = 0.0
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.08
	env.adjustment_contrast = 1.05
	env.ssao_enabled = not Look.compat()
	env.ssao_radius = 0.6
	env.ssao_intensity = 1.6
	env.ssr_enabled = not Look.compat()
	env.ssr_max_steps = 48
	env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
	_we = WorldEnvironment.new()
	_we.environment = env
	add_child(_we)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 30.0
	sun.shadow_blur = 1.5
	add_child(sun)
	moon = DirectionalLight3D.new()
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 25.0
	moon.light_color = Color(0.55, 0.65, 1.0)
	moon.rotation_degrees = Vector3(-38, 150, 0)
	add_child(moon)
	# the sky dome, drawn behind everything
	_dome = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 400.0
	sm.height = 800.0
	sm.radial_segments = 48
	sm.rings = 24
	_dome.mesh = sm
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load(SH + "links_sky.gdshader")
	_dome.material_override = sky_mat
	_dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_dome)
	# the lawn
	var lawn := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(300, 300)
	pm.subdivide_depth = 4
	pm.subdivide_width = 4
	lawn.mesh = pm
	lawn.material_override = Pbr.material("grass_lush", Color(0.62, 0.74, 0.5), 0.45)
	lawn.position = Vector3(0, C.GROUND, 0)
	add_child(lawn)
	_dress = Node3D.new()
	add_child(_dress)
	_flies = CPUParticles3D.new()
	_flies.amount = 60
	_flies.lifetime = 6.0
	_flies.preprocess = 6.0
	_flies.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_flies.direction = Vector3(0, 1, 0)
	_flies.spread = 180.0
	_flies.initial_velocity_min = 0.05
	_flies.initial_velocity_max = 0.2
	_flies.gravity = Vector3.ZERO
	_flies.scale_amount_min = 0.03
	_flies.scale_amount_max = 0.05
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	_flies.mesh = q
	_flies.material_override = Fx.material("glow", Color(0.85, 1.0, 0.45))
	var fade := Gradient.new()
	fade.offsets = PackedFloat32Array([0.0, 0.2, 0.5, 0.8, 1.0])
	fade.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0.2), Color(1, 1, 1, 1), Color(1, 1, 1, 0)])
	_flies.color_ramp = fade
	add_child(_flies)
	set_time(0.0, true)


func _scene(name: String) -> PackedScene:
	if not _scenes.has(name):
		var path := M + name + ".glb"
		_scenes[name] = load(path) if ResourceLoader.exists(path) else null
	return _scenes[name]


func _inst(name: String) -> Node3D:
	var s: PackedScene = _scene(name)
	return s.instantiate() if s else null


## Dresses the garden round a hole (deterministic per hole).
func dress(course: LinksCourse, index: int) -> void:
	_course = course
	for c in _dress.get_children():
		c.queue_free()
	_lights.clear()
	_floods.clear()
	_glows.clear()
	var hole := course.hole
	var rng := RandomNumberGenerator.new()
	rng.seed = 1000 + index * 77
	var w := hole.w * H.CELL
	var h := hole.h * H.CELL
	var centre := Vector3(w * 0.5, C.GROUND, h * 0.5)
	var box := Rect2(0, 0, w, h)
	# lantern posts on the lawn round the course, every ~2.8 m, and string lights between them
	var ring := box.grow(1.5)
	var perim := 2.0 * (ring.size.x + ring.size.y)
	var n := maxi(6, roundi(perim / 2.8))
	var posts: Array[Vector3] = []
	for k in n:
		var t := (k + 0.5) / n * perim
		var p := _perimeter(ring, t)
		var post := _inst("lantern_post")
		var lamp_at := Vector3(p.x, C.GROUND + 1.82, p.y)
		if post:
			post.position = Vector3(p.x, C.GROUND, p.y)
			# the arm reaches towards the course
			var to := Vector2(w * 0.5, h * 0.5) - p
			post.rotation.y = -to.angle()
			_dress.add_child(post)
			_glow_of(post)
			var lan := post.find_child("lantern", true, false) as Node3D
			if lan:
				lamp_at = lan.global_position if lan.is_inside_tree() else post.position + Basis(Vector3.UP, post.rotation.y) * Vector3(0.4, 1.7, 0)
				lan.set_meta("sway", rng.randf() * TAU)
		else:
			var pole := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.04
			cm.bottom_radius = 0.05
			cm.height = 1.9
			pole.mesh = cm
			pole.position = Vector3(p.x, C.GROUND + 0.95, p.y)
			pole.material_override = Pbr.material("planks", Color(0.5, 0.35, 0.25))
			_dress.add_child(pole)
			var lan2 := MeshInstance3D.new()
			var sp := SphereMesh.new()
			sp.radius = 0.16
			sp.height = 0.3
			lan2.mesh = sp
			var lm := StandardMaterial3D.new()
			lm.albedo_color = LANTERN
			lm.emission_enabled = true
			lm.emission = LANTERN
			lan2.material_override = lm
			_glows.append(lm)
			lan2.position = lamp_at
			_dress.add_child(lan2)
		posts.append(lamp_at - Vector3(0, 0.1, 0))
		var l := OmniLight3D.new()
		l.light_color = LANTERN
		l.omni_range = 4.0
		l.omni_attenuation = 1.4
		l.position = lamp_at - Vector3(0, 0.05, 0)
		l.shadow_enabled = k % 3 == 0 and not Look.compat()
		l.light_specular = 0.6
		_dress.add_child(l)
		_lights.append(l)
	_string_lights(posts, rng)
	# two floodlights on tall poles at opposite corners keep the course readable at night
	for corner in [Vector2(-1.6, -1.6), Vector2(w + 1.6, h + 1.6)]:
		var pole2 := MeshInstance3D.new()
		var cm2 := CylinderMesh.new()
		cm2.top_radius = 0.05
		cm2.bottom_radius = 0.07
		cm2.height = 4.2
		pole2.mesh = cm2
		pole2.material_override = Pbr.material("metal", Color(0.3, 0.3, 0.32), 1.0, 0.8)
		pole2.position = Vector3(corner.x, C.GROUND + 2.1, corner.y)
		_dress.add_child(pole2)
		var s := SpotLight3D.new()
		s.position = Vector3(corner.x, C.GROUND + 4.2, corner.y)
		s.look_at_from_position(s.position, Vector3(w * 0.5, 0, h * 0.5), Vector3.UP)
		s.spot_range = 16.0
		s.spot_angle = 42.0
		s.spot_angle_attenuation = 0.8
		s.light_color = Color(1.0, 0.9, 0.78)
		s.shadow_enabled = not Look.compat()
		s.shadow_blur = 2.0
		_dress.add_child(s)
		_floods.append(s)
		var head := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.3, 0.18, 0.22)
		head.mesh = bm
		var hm := StandardMaterial3D.new()
		hm.albedo_color = Color(1.0, 0.95, 0.85)
		hm.emission_enabled = true
		hm.emission = Color(1.0, 0.92, 0.8)
		head.material_override = hm
		_glows.append(hm)
		head.position = s.position
		head.rotation = s.rotation
		_dress.add_child(head)
	# trees further out, shrubs and rocks near the course, garden pieces
	var placed: Array[Vector2] = []
	for k in 16:
		var p2 := _around(box, rng, 4.8, 13.0, placed, 2.6)
		if p2.x > -1000.0:
			_put(["tree_round", "tree_tall", "tree_cypress"][rng.randi() % 3], p2, rng, rng.randf_range(0.85, 1.25))
	for k in 18:
		var p3 := _around(box, rng, 0.7, 3.0, placed, 0.9)
		if p3.x > -1000.0:
			_put("bush" if rng.randf() < 0.75 else ["rock_a", "rock_b"][rng.randi() % 2], p3, rng, rng.randf_range(0.8, 1.3))
	for name in ["stone_lantern", "stone_lantern", "bench", "gazebo" if index % 2 == 0 else "fountain"]:
		var r0 := 1.2 if name != "gazebo" and name != "fountain" else 5.0
		var p4 := _around(box, rng, r0, r0 + 2.5, placed, 1.8 if r0 < 3.0 else 3.5)
		if p4.x > -1000.0:
			var node := _put(name, p4, rng, 1.0)
			if node and name in ["bench", "gazebo"]:
				node.look_at(Vector3(centre.x, node.position.y, centre.z), Vector3.UP, true)
			if node and name == "stone_lantern":
				var sl := OmniLight3D.new()
				sl.light_color = LANTERN
				sl.omni_range = 2.2
				sl.position = node.position + Vector3(0, 0.62, 0)
				_dress.add_child(sl)
				_lights.append(sl)
	_flowers(hole, rng)
	_flies.position = Vector3(w * 0.5, 0.5, h * 0.5)
	_flies.emission_box_extents = Vector3(w * 0.5 + 2.0, 0.8, h * 0.5 + 2.0)
	set_time(_tod_target, true)


func _perimeter(r: Rect2, t: float) -> Vector2:
	var a := r.size.x
	var b := r.size.y
	t = fposmod(t, 2.0 * (a + b))
	if t < a:
		return r.position + Vector2(t, 0)
	if t < a + b:
		return r.position + Vector2(a, t - a)
	if t < 2.0 * a + b:
		return r.position + Vector2(a - (t - a - b), b)
	return r.position + Vector2(0, b - (t - 2.0 * a - b))


## A random spot on the lawn between r0 and r1 from the course's rectangle, clear of what is already there.
func _around(box: Rect2, rng: RandomNumberGenerator, r0: float, r1: float, placed: Array[Vector2], gap: float) -> Vector2:
	for attempt in 24:
		var p := Vector2(rng.randf_range(box.position.x - r1, box.end.x + r1), rng.randf_range(box.position.y - r1, box.end.y + r1))
		var q := p.clamp(box.position, box.end)
		var d := p.distance_to(q)
		if d < r0 or d > r1:
			continue
		if placed.any(func(o): return o.distance_to(p) < gap):
			continue
		placed.append(p)
		return p
	return Vector2(-10000, 0)


func _put(name: String, p: Vector2, rng: RandomNumberGenerator, s: float) -> Node3D:
	var n := _inst(name)
	if n == null:
		return null
	if name == "bush":
		var kids := n.get_children()
		for k in kids.size():
			(kids[k] as Node3D).visible = k == rng.randi() % kids.size()
			(kids[k] as Node3D).position = Vector3.ZERO
	n.position = Vector3(p.x, C.GROUND, p.y)
	n.rotation.y = rng.randf() * TAU
	n.scale = Vector3.ONE * s
	_dress.add_child(n)
	_glow_of(n)
	return n


func _glow_of(n: Node) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for s in mesh.get_surface_count():
			var m := mesh.surface_get_material(s)
			if m is StandardMaterial3D and m.resource_name.contains("glow") and not _glows.has(m):
				_glows.append(m)


## Bulbs strung between the lantern posts, sagging in catenaries; warm white with a few pastel ones.
func _string_lights(posts: Array[Vector3], rng: RandomNumberGenerator) -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sp := SphereMesh.new()
	sp.radius = 0.025
	sp.height = 0.05
	sp.radial_segments = 8
	sp.rings = 4
	mm.mesh = sp
	var pts: Array[Vector3] = []
	var cols: Array[Color] = []
	var wire := SurfaceTool.new()
	wire.begin(Mesh.PRIMITIVE_LINES)
	for k in posts.size():
		var a := posts[k]
		var b := posts[(k + 1) % posts.size()]
		var n := maxi(3, int(a.distance_to(b) / 0.32))
		var prev := a
		for s in n + 1:
			var f := float(s) / n
			var p := a.lerp(b, f) - Vector3(0, sin(f * PI) * 0.28, 0)
			wire.add_vertex(prev)
			wire.add_vertex(p)
			prev = p
			if s > 0 and s < n:
				pts.append(p - Vector3(0, 0.03, 0))
				var c := Color(1.0, 0.85, 0.6)
				if rng.randf() < 0.3:
					c = [Color(1.0, 0.55, 0.5), Color(0.6, 0.85, 1.0), Color(0.75, 1.0, 0.6), Color(1.0, 0.8, 0.4)][rng.randi() % 4]
				cols.append(c)
	mm.instance_count = pts.size()
	for i in pts.size():
		mm.set_instance_transform(i, Transform3D(Basis(), pts[i]))
		mm.set_instance_color(i, cols[i])
	_bulbs = MultiMeshInstance3D.new()
	_bulbs.multimesh = mm
	var bm := StandardMaterial3D.new()
	bm.vertex_color_use_as_albedo = true
	bm.emission_enabled = true
	bm.emission = Color(1, 1, 1)
	bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_bulbs.material_override = bm
	_bulbs.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_dress.add_child(_bulbs)
	var wm := MeshInstance3D.new()
	wm.mesh = wire.commit()
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = Color(0.05, 0.05, 0.05)
	wmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	wm.material_override = wmat
	_dress.add_child(wm)


## Flowers in the garden beds (the wall cells), clear of the rails.
func _flowers(hole: LinksHole, rng: RandomNumberGenerator) -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sp := SphereMesh.new()
	sp.radius = 0.03
	sp.height = 0.045
	sp.radial_segments = 6
	sp.rings = 3
	mm.mesh = sp
	var xs: Array[Transform3D] = []
	var cs: Array[Color] = []
	var palette := [Color(1.0, 0.45, 0.6), Color(1.0, 0.95, 0.9), Color(1.0, 0.8, 0.25), Color(0.7, 0.45, 1.0), Color(1.0, 0.5, 0.3)]
	var leaves := MultiMesh.new()
	leaves.transform_format = MultiMesh.TRANSFORM_3D
	var lm := SphereMesh.new()
	lm.radius = 0.07
	lm.height = 0.08
	lm.radial_segments = 8
	lm.rings = 4
	leaves.mesh = lm
	var lx: Array[Transform3D] = []
	for y in hole.h:
		for x in hole.w:
			if hole.kind[y * hole.w + x] != H.WALL:
				continue
			var bed := _course._bed(x, y) if _course else H.CELL
			for k in 3:
				var p := Vector2(x + rng.randf_range(0.28, 0.72), y + rng.randf_range(0.28, 0.72)) * H.CELL
				lx.append(Transform3D(Basis().scaled(Vector3(1.0, rng.randf_range(0.5, 0.9), 1.0)), Vector3(p.x, bed + 0.01, p.y)))
				for f in 2:
					var q := p + Vector2(rng.randf_range(-0.05, 0.05), rng.randf_range(-0.05, 0.05))
					xs.append(Transform3D(Basis(), Vector3(q.x, bed + 0.05 + rng.randf() * 0.02, q.y)))
					cs.append(palette[rng.randi() % palette.size()])
	mm.instance_count = xs.size()
	for i in xs.size():
		mm.set_instance_transform(i, xs[i])
		mm.set_instance_color(i, cs[i])
	var fmi := MultiMeshInstance3D.new()
	fmi.multimesh = mm
	var fm := StandardMaterial3D.new()
	fm.vertex_color_use_as_albedo = true
	fm.roughness = 0.6
	fmi.material_override = fm
	fmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_dress.add_child(fmi)
	leaves.instance_count = lx.size()
	for i in lx.size():
		leaves.set_instance_transform(i, lx[i])
	var lmi := MultiMeshInstance3D.new()
	lmi.multimesh = leaves
	lmi.material_override = Pbr.material("grass_lush", Color(0.45, 0.62, 0.35), 3.0)
	_dress.add_child(lmi)


## 0 = golden hour, 1 = night. `snap` jumps there; otherwise the evening moves on over a few seconds.
func set_time(t: float, snap := false) -> void:
	_tod_target = clampf(t, 0.0, 1.0)
	if snap:
		_tod = _tod_target
		_apply()


static func _k3(t: float, a, b, c):
	if t < 0.5:
		return lerp(a, b, t * 2.0)
	return lerp(b, c, (t - 0.5) * 2.0)


func _apply() -> void:
	var t := _tod
	var elev: float = _k3(t, 16.0, 3.0, -10.0)
	var az := -130.0 + t * 25.0
	sun.rotation_degrees = Vector3(-maxf(elev, 1.0), az, 0)
	sun.light_color = _k3(t, Color(1.0, 0.8, 0.55), Color(1.0, 0.52, 0.3), Color(1.0, 0.4, 0.25))
	sun.light_energy = _k3(t, 2.3, 1.1, 0.0)
	sun.visible = sun.light_energy > 0.02
	moon.light_energy = smoothstep(0.45, 1.0, t) * 0.32
	moon.visible = moon.light_energy > 0.02
	var sd := Basis.from_euler(Vector3(deg_to_rad(-elev), deg_to_rad(az), 0)) * Vector3(0, 0, 1)
	sky_mat.set_shader_parameter("sun_dir", sd)
	sky_mat.set_shader_parameter("top_col", _k3(t, Color(0.3, 0.46, 0.75), Color(0.14, 0.17, 0.38), Color(0.015, 0.025, 0.07)))
	sky_mat.set_shader_parameter("mid_col", _k3(t, Color(0.72, 0.7, 0.78), Color(0.52, 0.36, 0.5), Color(0.04, 0.06, 0.13)))
	sky_mat.set_shader_parameter("horizon_col", _k3(t, Color(1.0, 0.78, 0.52), Color(1.0, 0.5, 0.32), Color(0.1, 0.1, 0.18)))
	sky_mat.set_shader_parameter("ground_col", _k3(t, Color(0.4, 0.35, 0.3), Color(0.25, 0.18, 0.2), Color(0.02, 0.02, 0.04)))
	sky_mat.set_shader_parameter("sun_col", _k3(t, Color(1.0, 0.82, 0.55), Color(1.0, 0.5, 0.28), Color(0.6, 0.25, 0.2)))
	sky_mat.set_shader_parameter("glow_col", _k3(t, Color(1.0, 0.6, 0.3), Color(1.0, 0.4, 0.25), Color(0.3, 0.15, 0.2)))
	sky_mat.set_shader_parameter("sun_disc", 1.0 if elev > -1.0 else 0.0)
	sky_mat.set_shader_parameter("sun_size", 0.05)
	sky_mat.set_shader_parameter("sun_glow", _k3(t, 0.5, 0.6, 0.1))
	sky_mat.set_shader_parameter("sun_hot", 2.2)
	sky_mat.set_shader_parameter("horizon_glow", _k3(t, 0.55, 0.9, 0.15))
	sky_mat.set_shader_parameter("anti_glow", _k3(t, 0.2, 0.5, 0.0))
	sky_mat.set_shader_parameter("streaks", _k3(t, 0.5, 0.7, 0.1))
	sky_mat.set_shader_parameter("cloud_amount", 0.3)
	sky_mat.set_shader_parameter("cloud_glow", _k3(t, 0.4, 0.8, 0.0))
	sky_mat.set_shader_parameter("cloud_col", _k3(t, Color(1.0, 0.9, 0.8), Color(0.9, 0.6, 0.55), Color(0.12, 0.13, 0.2)))
	sky_mat.set_shader_parameter("cloud_shade", _k3(t, Color(0.6, 0.55, 0.65), Color(0.4, 0.3, 0.42), Color(0.05, 0.06, 0.1)))
	sky_mat.set_shader_parameter("stars", smoothstep(0.55, 1.0, t))
	sky_mat.set_shader_parameter("moon", smoothstep(0.5, 0.9, t))
	sky_mat.set_shader_parameter("moon_dir", Vector3(-0.35, 0.42, -0.84))
	sky_mat.set_shader_parameter("hill_col", _k3(t, Color(0.52, 0.5, 0.42), Color(0.3, 0.22, 0.28), Color(0.03, 0.035, 0.06)))
	sky_mat.set_shader_parameter("hill_far", _k3(t, Color(0.78, 0.66, 0.6), Color(0.52, 0.36, 0.44), Color(0.06, 0.07, 0.12)))
	sky_mat.set_shader_parameter("town", smoothstep(0.3, 0.9, t))
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = _k3(t, Color(0.75, 0.72, 0.8), Color(0.62, 0.5, 0.65), Color(0.28, 0.33, 0.55))
	env.ambient_light_energy = _k3(t, 0.8, 0.65, 0.45)
	env.tonemap_exposure = _k3(t, 1.0, 1.05, 1.15)
	env.fog_light_color = _k3(t, Color(1.0, 0.8, 0.6), Color(0.75, 0.48, 0.5), Color(0.06, 0.07, 0.12))
	env.fog_density = _k3(t, 0.004, 0.006, 0.008) * (0.25 if Look.compat() else 1.0)
	env.fog_sun_scatter = _k3(t, 0.25, 0.4, 0.0)
	var lamp := 0.25 + 0.95 * smoothstep(0.05, 0.75, t)
	for l in _lights:
		l.light_energy = lamp * 1.4
	for s in _floods:
		s.light_energy = smoothstep(0.35, 0.9, t) * 3.0
		s.visible = s.light_energy > 0.01
	for m in _glows:
		if m is StandardMaterial3D:
			(m as StandardMaterial3D).emission_energy_multiplier = lamp * 2.2
	if _bulbs:
		(_bulbs.material_override as StandardMaterial3D).emission_energy_multiplier = lamp * 2.6
	if _course:
		for m2 in _course.glow_mats:
			m2.emission_energy_multiplier = 0.4 + lamp * 1.6
	_flies.emitting = t > 0.35
	_flies.visible = t > 0.3


func lamp_level() -> float:
	return 0.25 + 0.95 * smoothstep(0.05, 0.75, _tod)


func night() -> float:
	return _tod


func _process(delta: float) -> void:
	_time += delta
	var cam := get_viewport().get_camera_3d()
	if cam:
		_dome.global_position = cam.global_position
	if absf(_tod - _tod_target) > 0.0005:
		_tod = move_toward(_tod, _tod_target, delta * 0.12)
		_apply()
	# lanterns sway a little and flicker
	for i in _lights.size():
		var l := _lights[i]
		l.light_energy = lamp_level() * 1.4 * (0.93 + 0.07 * sin(_time * 7.0 + i * 1.7) * sin(_time * 3.1 + i))
