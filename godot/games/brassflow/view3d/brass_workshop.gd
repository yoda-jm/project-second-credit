class_name BrassWorkshop
extends Node3D
## The night workshop round the Brassflow board: build() loads art/models/workshop.glb (tools/blender/
## brassflow_models.py: the workbench with the board inlay, brick walls with arched windows, shelves, steam pipes,
## wall gears, the bench machine with its pistons, the clock, hanging lamps, the vat of glow, tools), swaps the named
## materials for the workshop shaders (brick, wood, the night in the windows, the glowing liquid), and adds the life:
## warm lamp lights, cool moonlight through the windows, steam from the vents, bubbles in the vat, turning gears,
## pumping pistons, a running clock (it is nearly midnight). alarm(level) (0..1, as the glow nears an open end) makes
## the vents hiss harder and the lamps flicker towards red, and lights the red alarm lamp.
## The view owns the WorldEnvironment and the key light: it reads environment() (Pop Voyage's backdrop keys) and calls
## make_environment() and setup_sun() with that dictionary (or copies the values).
##
## Space: board space (1 unit per cell, the board's top at y = 0, cells at x 0..10, z 0..7); the bench top is at
## y -0.15. Animation runs on the node's own clock (_t, advanced in _process), so fixed-step captures repeat.

const GLB := "res://games/brassflow/art/models/workshop.glb"
const SH := "res://games/brassflow/shaders/"
const LAMP := Color(1.0, 0.8, 0.58)
const ALARM := Color(1.0, 0.16, 0.06)
const GLOW := Color(0.3, 1.0, 0.72)
## rad/s of each gear about its own axle (meshing gears turn the other way, by their teeth ratio)
const GEARS := {
	"gear_0": 0.22, "gear_1": -0.22 * 28.0 / 15.0,
	"gear_2": -0.3, "gear_3": 0.3 * 23.0 / 12.0,
	"gear_4": 0.9, "gear_5": -0.9 * 16.0 / 9.0, "gear_6": 0.9 * 16.0 / 7.0,
}
const PISTON_STROKE := 0.32
const CLOCK_START := 23.0 + 52.0 / 60.0  ## hours: the clock reads 11:52 when the workshop is built

var root: Node3D
var _t := 0.0
var _alarm := 0.0          ## smoothed
var _alarm_target := 0.0
var _gears: Array = []     ## [node, rest basis, local axis, rad/s]
var _pistons: Array = []   ## [node, rest position, phase]
var _hour: Node3D
var _minute: Node3D
var _hour_rest: Basis
var _minute_rest: Basis
var _lamps: Array[OmniLight3D] = []
var _lamp_mat: StandardMaterial3D
var _alarm_mat: StandardMaterial3D
var _alarm_light: OmniLight3D
var _vents: Array = []     ## [GPUParticles3D, ParticleProcessMaterial]
var _bubbles: GPUParticles3D
var _shaders := {}         ## materials driven by _t: window, fluid
var _fluid: ShaderMaterial
var _moon_spots: Array[SpotLight3D] = []


## The environment the view applies. Keys as PopBackdrop.environment_for: sky_top, sky_horizon, ground_horizon,
## ground_bottom (a ProceduralSkyMaterial for ambient and reflections: warm, the room hides the background),
## sun_color, sun_rotation (degrees, the key light over the bench: a warm work light from the upper left front),
## sun_energy, ambient_color, ambient_energy, fog_color, fog_density, fog_sun_scatter, exposure, glow_intensity,
## glow_threshold, saturation, contrast, night (true: keep the board's own glows strong).
func environment() -> Dictionary:
	return {
		"sky_top": Color("#2a1c14"), "sky_horizon": Color("#6a4a30"),
		"ground_horizon": Color("#4a3020"), "ground_bottom": Color("#1c120c"),
		"sun_color": Color("#ffd9a8"), "sun_rotation": Vector3(-62, -24, 0), "sun_energy": 0.9,
		"ambient_color": Color("#6a5040"), "ambient_energy": 0.45,
		"fog_color": Color("#3a2a20"), "fog_density": 0.006, "fog_sun_scatter": 0.0,
		"exposure": 1.0, "glow_intensity": 0.6, "glow_threshold": 1.0, "saturation": 1.08, "contrast": 1.06,
		"night": true,
	}


## A ready Environment from environment()'s dictionary (the view may use it as is or copy the values).
static func make_environment(d: Dictionary) -> Environment:
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = d["sky_top"]
	sm.sky_horizon_color = d["sky_horizon"]
	sm.ground_horizon_color = d["ground_horizon"]
	sm.ground_bottom_color = d["ground_bottom"]
	sm.sun_angle_max = 20.0
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = d["ambient_color"]
	env.ambient_light_energy = d["ambient_energy"]
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = d["exposure"]
	env.tonemap_white = 6.0
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = d["fog_color"]
	env.fog_density = d["fog_density"]
	env.fog_sun_scatter = d["fog_sun_scatter"]
	env.fog_sky_affect = 0.0
	env.glow_enabled = true
	env.glow_intensity = d["glow_intensity"]
	env.glow_hdr_threshold = d["glow_threshold"]
	env.glow_bloom = 0.03
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.7)
	env.set_glow_level(4, 0.4)
	env.ssao_enabled = not Look.compat()
	env.ssao_radius = 0.5
	env.ssao_intensity = 1.4
	env.adjustment_enabled = true
	env.adjustment_saturation = d["saturation"]
	env.adjustment_contrast = d["contrast"]
	return env


static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 40.0


func build() -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	_t = 0.0
	_alarm = 0.0
	_alarm_target = 0.0
	_gears.clear()
	_pistons.clear()
	_lamps.clear()
	_vents.clear()
	_shaders.clear()
	_moon_spots.clear()
	var packed := load(GLB) as PackedScene
	if packed == null:
		push_error("BrassWorkshop: missing " + GLB)
		return
	root = packed.instantiate() as Node3D
	root.name = "workshop"
	add_child(root)
	_dress(root)
	_collect()
	_add_lights()
	_add_steam()
	_add_bubbles()
	_add_probe()
	_apply(0.0)


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	return m


## Swaps the named materials for the workshop's shaders; the walls, the room and the far props cast no shadows (the
## moonlight comes in through solid brick otherwise), the bench and what stands on it do.
func _dress(r: Node3D) -> void:
	var cache := {}
	for n in r.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		if nm in ["room", "shelves", "clock", "clock_hour", "clock_minute"] or nm.begins_with("lamp_") \
				or nm in ["gear_0", "gear_1", "gear_2", "gear_3", "board_grid", "board_bed"]:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			if not cache.has(mn):
				cache[mn] = _material_for(mn, src)
			var m: Material = cache[mn]
			if m != src:
				mi.set_surface_override_material(i, m)
		if nm == "vat_glass" or nm == "vat_glow":
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _material_for(mn: String, src: Material) -> Material:
	match mn:
		"brick":
			return _shader("brass_brick")
		"bench_wood":
			var m := _shader("brass_wood")
			m.set_shader_parameter("tint_a", Color(0.32, 0.19, 0.1))
			m.set_shader_parameter("tint_b", Color(0.19, 0.1, 0.05))
			m.set_shader_parameter("plank_width", 1.6)
			m.set_shader_parameter("plank_length", 11.0)
			return m
		"floor_wood":
			var m := _shader("brass_wood")
			m.set_shader_parameter("tint_a", Color(0.3, 0.17, 0.09))
			m.set_shader_parameter("tint_b", Color(0.17, 0.09, 0.05))
			m.set_shader_parameter("plank_width", 1.2)
			m.set_shader_parameter("along_z", true)
			m.set_shader_parameter("varnish", 0.6)
			m.set_shader_parameter("wear", 0.6)
			return m
		"shelf_wood":
			var m := _shader("brass_wood")
			m.set_shader_parameter("tint_a", Color(0.3, 0.18, 0.1))
			m.set_shader_parameter("tint_b", Color(0.18, 0.1, 0.05))
			m.set_shader_parameter("plank_width", 0.9)
			m.set_shader_parameter("varnish", 0.5)
			return m
		"window_night_glow", "window_moon_glow":
			var m := _shader("brass_window")
			m.set_shader_parameter("moon", 1.0 if mn == "window_moon_glow" else 0.0)
			_shaders[mn] = m
			return m
		"vat_glow":
			_fluid = _shader("brass_fluid")
			return _fluid
		"lamp_glow":
			_lamp_mat = (src as StandardMaterial3D).duplicate() as StandardMaterial3D
			_lamp_mat.emission_enabled = true
			_lamp_mat.emission = LAMP
			_lamp_mat.emission_energy_multiplier = 6.0
			return _lamp_mat
		"alarm_glow":
			_alarm_mat = (src as StandardMaterial3D).duplicate() as StandardMaterial3D
			_alarm_mat.emission_enabled = true
			_alarm_mat.emission = ALARM
			_alarm_mat.emission_energy_multiplier = 0.3
			return _alarm_mat
		"board_leather":
			var m := (src as StandardMaterial3D).duplicate() as StandardMaterial3D
			m.roughness = 0.75
			m.metallic_specular = 0.3
			return m
	if src is StandardMaterial3D and (mn.contains("glass") or mn.begins_with("bottle_")):
		var g := (src as StandardMaterial3D).duplicate() as StandardMaterial3D
		g.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		g.metallic_specular = 0.9
		g.roughness = 0.05
		return g
	return src


func _collect() -> void:
	for n in root.find_children("gear_*", "MeshInstance3D", true, false):
		var g := n as MeshInstance3D
		var sz := g.mesh.get_aabb().size
		var axis := Vector3.RIGHT if sz.x <= sz.y and sz.x <= sz.z else (Vector3.UP if sz.y <= sz.z else Vector3.BACK)
		_gears.append([g, g.transform.basis, axis, float(GEARS.get(String(g.name), 0.3))])
	for i in 2:
		var p := root.find_child("piston_%d" % i, true, false) as Node3D
		if p:
			_pistons.append([p, p.position, PI * i])
	_hour = root.find_child("clock_hour", true, false) as Node3D
	_minute = root.find_child("clock_minute", true, false) as Node3D
	if _hour:
		_hour_rest = _hour.transform.basis
	if _minute:
		_minute_rest = _minute.transform.basis


func _anchor(n: String) -> Vector3:
	var a := root.find_child(n, true, false) as Node3D
	return a.position if a else Vector3.ZERO


func _add_lights() -> void:
	var i := 0
	while true:
		var a := root.find_child("lamp_light_%d" % i, true, false) as Node3D
		if a == null:
			break
		var l := OmniLight3D.new()
		l.name = "lamp_light_%d" % i
		l.position = a.position + Vector3(0, -0.35, 0)
		l.light_color = LAMP
		l.light_energy = 2.4 if i < 3 else 1.6
		l.omni_range = 13.0
		l.omni_attenuation = 1.2
		l.shadow_enabled = i == 1
		l.light_specular = 0.8
		add_child(l)
		_lamps.append(l)
		i += 1
	# moonlight: a cool soft spot through each window onto the back of the bench, no shadows (the wall is solid)
	for x in [-2.5, 5.0, 12.5]:
		var s := SpotLight3D.new()
		s.name = "moon_%d" % int(x)
		s.position = Vector3(x - 1.5, 9.5, -6.0)
		s.look_at_from_position(s.position, Vector3(x + 0.5, -0.15, -1.0))
		s.light_color = Color(0.55, 0.66, 1.0)
		s.light_energy = 1.4 if x == 5.0 else 0.9
		s.spot_range = 18.0
		s.spot_angle = 22.0
		s.spot_angle_attenuation = 1.6
		s.light_specular = 0.4
		add_child(s)
		_moon_spots.append(s)
	_alarm_light = OmniLight3D.new()
	_alarm_light.name = "alarm_light"
	_alarm_light.position = _anchor("alarm_light")
	_alarm_light.light_color = ALARM
	_alarm_light.light_energy = 0.0
	_alarm_light.omni_range = 9.0
	add_child(_alarm_light)
	# the vat lights its corner
	var v := OmniLight3D.new()
	v.name = "vat_light"
	v.position = _anchor("bubbles_0") + Vector3(0.0, 1.2, 1.2)
	v.light_color = GLOW
	v.light_energy = 0.9
	v.omni_range = 5.0
	add_child(v)


func _particles(name_: String, amount: int, life: float, pos: Vector3, mat: Material, size: float,
		seed_: int) -> Array:
	var p := GPUParticles3D.new()
	p.name = name_
	p.amount = amount
	p.lifetime = life
	p.preprocess = life
	p.fixed_fps = 30
	p.use_fixed_seed = true
	p.seed = seed_
	p.position = pos
	p.visibility_aabb = AABB(Vector3(-3, -1, -3), Vector3(6, 8, 6))
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	q.material = mat
	p.draw_pass_1 = q
	var pm := ParticleProcessMaterial.new()
	p.process_material = pm
	add_child(p)
	return [p, pm]


func _add_steam() -> void:
	var i := 0
	while true:
		var a := root.find_child("vent_%d" % i, true, false) as Node3D
		if a == null:
			break
		var r := _particles("steam_%d" % i, 32, 2.6, a.position, Fx.material("smoke", Color(0.95, 0.93, 0.9)), 1.0,
				41 + i)
		var pm: ParticleProcessMaterial = r[1]
		pm.direction = Vector3(0, 1, 0)
		pm.spread = 12.0
		pm.initial_velocity_min = 0.6
		pm.initial_velocity_max = 1.1
		pm.gravity = Vector3(0.05, 0.25, 0.08)
		pm.damping_min = 0.3
		pm.damping_max = 0.6
		pm.angle_min = -180
		pm.angle_max = 180
		pm.angular_velocity_min = -20
		pm.angular_velocity_max = 20
		pm.scale_min = 0.5
		pm.scale_max = 0.9
		var sc := Curve.new()
		sc.add_point(Vector2(0, 0.3))
		sc.add_point(Vector2(1, 2.6))
		var ct := CurveTexture.new()
		ct.curve = sc
		pm.scale_curve = ct
		var ramp := Gradient.new()
		ramp.set_color(0, Color(1, 1, 1, 0.0))
		ramp.add_point(0.12, Color(1, 1, 1, 0.6))
		ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0.0))
		var gt := GradientTexture1D.new()
		gt.gradient = ramp
		pm.color_ramp = gt
		_vents.append(r)
		i += 1


func _add_bubbles() -> void:
	var a := root.find_child("bubbles_0", true, false) as Node3D
	if a == null:
		return
	var r := _particles("bubbles", 40, 2.4, a.position, Fx.material("glow", Color(0.6, 1.0, 0.85)), 0.12, 77)
	_bubbles = r[0]
	var pm: ParticleProcessMaterial = r[1]
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
	pm.emission_ring_axis = Vector3.UP
	pm.emission_ring_radius = 0.6
	pm.emission_ring_inner_radius = 0.0
	pm.emission_ring_height = 0.1
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 4.0
	pm.initial_velocity_min = 0.5
	pm.initial_velocity_max = 0.9
	pm.gravity = Vector3(0, 0.15, 0)
	pm.scale_min = 0.4
	pm.scale_max = 1.2
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.15
	pm.turbulence_noise_scale = 2.0
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0.0))
	ramp.add_point(0.1, Color(1, 1, 1, 0.8))
	ramp.add_point(0.8, Color(1, 1, 1, 0.7))
	ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = ramp
	pm.color_ramp = gt


func _add_probe() -> void:
	var p := ReflectionProbe.new()
	p.name = "probe"
	p.position = Vector3(5.0, 3.0, 2.0)
	p.size = Vector3(30.0, 14.0, 16.0)
	p.origin_offset = Vector3(0.0, -1.0, 2.0)
	p.box_projection = true
	p.interior = true
	p.update_mode = ReflectionProbe.UPDATE_ONCE
	p.max_distance = 40.0
	add_child(p)


## 0..1: how close the glow is to spilling. The vents hiss harder, the lamps flicker towards red, the alarm lamp
## glows and throbs. Eased on the workshop's clock, so it may be set every frame.
func alarm(level: float) -> void:
	_alarm_target = clampf(level, 0.0, 1.0)


func _process(delta: float) -> void:
	_t += delta
	_alarm = move_toward(_alarm, _alarm_target, delta * 1.5)
	_apply(delta)


func _apply(delta: float) -> void:
	for g in _gears:
		var node: Node3D = g[0]
		node.transform.basis = (g[1] as Basis) * Basis(g[2], float(g[3]) * _t)
	if not _gears.is_empty():
		var crank := float(GEARS["gear_4"]) * _t
		for p in _pistons:
			(p[0] as Node3D).position = (p[1] as Vector3) + Vector3(0, PISTON_STROKE * sin(crank + float(p[2])), 0)
	var hours := CLOCK_START + _t / 3600.0
	if _minute:
		_minute.transform.basis = _minute_rest * Basis(Vector3.BACK, -TAU * fmod(hours, 1.0))
	if _hour:
		_hour.transform.basis = _hour_rest * Basis(Vector3.BACK, -TAU * fmod(hours, 12.0) / 12.0)
	for m in _shaders.values():
		(m as ShaderMaterial).set_shader_parameter("t", _t)
	# the alarm: flicker (a deterministic stutter from the clock), red tint, the alarm lamp throbbing
	var a := _alarm
	var flick := 1.0
	if a > 0.0:
		var s := sin(_t * 23.0) * sin(_t * 7.3 + 1.0) + sin(_t * 41.0) * 0.5
		flick = 1.0 - a * 0.45 * clampf(0.5 + 0.5 * s, 0.0, 1.0)
	var lamp_col := LAMP.lerp(Color(1.0, 0.3, 0.15), a * 0.75)
	for i in _lamps.size():
		var l := _lamps[i]
		l.light_color = lamp_col
		l.light_energy = (2.4 if i < 3 else 1.6) * flick * (1.0 + 0.03 * sin(_t * 1.7 + i))
	if _lamp_mat:
		_lamp_mat.emission = lamp_col
		_lamp_mat.emission_energy_multiplier = 6.0 * flick
	var throb := 0.5 + 0.5 * sin(_t * TAU * (1.2 + a * 1.3))
	if _alarm_mat:
		_alarm_mat.emission_energy_multiplier = 0.3 + a * (2.0 + 6.0 * throb)
	if _alarm_light:
		_alarm_light.light_energy = a * (0.6 + 2.4 * throb)
	if _fluid:
		_fluid.set_shader_parameter("t", _t)
		_fluid.set_shader_parameter("pulse", a * 0.6 * throb)
	for v in _vents:
		var p: GPUParticles3D = v[0]
		var pm: ParticleProcessMaterial = v[1]
		p.speed_scale = 1.0 + a * 1.4
		pm.initial_velocity_min = 0.6 + a * 2.2
		pm.initial_velocity_max = 1.1 + a * 3.4
		p.amount_ratio = 0.55 + 0.45 * a
	if _bubbles:
		_bubbles.speed_scale = 1.0 + a * 1.5
