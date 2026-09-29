class_name NovaBackdrop
extends Node3D
## The night behind the Nova Wardens field: the last line of defence on a coastal hilltop. build() loads the diorama
## (art/backdrop/night_coast.glb, made by tools/blender/novawardens_city.py: the crest, the sleeping town and its
## harbour, the lighthouse headland, the radar station and the searchlight batteries), swaps the materials the Blender
## script marks by name for the backdrop shaders, and adds the sky dome (moon, planet, nebula, stars, clouds,
## meteors), the sea (a disc round the camera whose rim is the horizon), the searchlight and lighthouse beams with
## their flares, and a light for the flashes. _process animates it all on the node's own clock (fixed-step safe).
##
## The game reacts through alarm(level) (0..1: as the invaders come lower, the town's air-raid lamps wake and flash
## red, windows go dark, the red pulses in the sky and on the water, the searchlights sweep faster) and flash(pos)
## (a brief flash in the sky towards a big explosion; pos in the play space).
## The view owns the WorldEnvironment and the moonlight: it reads environment_for() (PopBackdrop's keys) and may call
## make_environment() and setup_sun() with that dictionary.
##
## Space: the play field is x 0..11.2, y 0..12.8 on z = 0 (224 x 256 px at 0.05 per px); camera near (5.6, 5.8, 22),
## fov 36, looking a touch up. The crest the cannon stands on is level at y = 0.95 (the game draws its ground line at
## ~1.1). The sea horizon lies near y = 3.8 on the play plane; the middle of the field is kept dark and quiet (the
## towers, the moon, the nebula's heart and the beams' sources are at the sides).

const GLB := "res://games/novawardens/art/backdrop/night_coast.glb"
const SH := "res://games/novawardens/shaders/"
const CAMERA := Vector3(5.6, 5.8, 22.0)
const DOME_RADIUS := 1500.0
const SEA_LEVEL := -12.0
const SEA_RADIUS := 200.0
const MOON_DIR := Vector3(0.4, 0.21, -0.89)
const LIGHTHOUSE_SPEED := 0.55   ## rad/s
const BEAM_COLOR := Color(0.78, 0.86, 1.0)

## The look (one variant). Keys as PopBackdrop's, plus light_from (where the moonlight comes from).
const LOOK := {
	"name": "Coastal Night",
	"sky_top": Color("#02040e"), "sky_mid": Color("#0a1030"), "sky_horizon": Color("#1e2650"),
	"sky_below": Color("#0a0f22"),
	"ground_horizon": Color("#1a2048"), "ground_bottom": Color("#080c1c"),
	"sun_color": Color("#b4c4ff"), "light_from": Vector3(0.55, 0.5, -0.35), "sun_energy": 0.55,
	"ambient_color": Color("#34406e"), "ambient_energy": 0.6,
	"fog_color": Color("#1c2448"), "fog_density": 0.0045, "fog_sun_scatter": 0.0,
	"exposure": 1.05, "glow_intensity": 0.85, "glow_threshold": 0.9, "saturation": 1.1, "contrast": 1.05,
	"night": true,
}

## The searchlights by index (searchlight_<i> in the diorama): [yaw centre, yaw swing, pitch centre, pitch swing,
## speed, phase]. Yaw 0 points away from the camera (-z), positive turns right; pitch is up from the horizontal.
const SEARCH := [
	[-0.55, 0.45, 1.05, 0.22, 0.21, 0.0],
	[-0.25, 0.5, 0.85, 0.2, 0.17, 2.1],
	[0.45, 0.45, 1.0, 0.22, 0.19, 4.0],
	[0.2, 0.5, 0.8, 0.2, 0.23, 1.2],
	[0.35, 0.35, 0.7, 0.15, 0.15, 3.3],
	[-0.4, 0.4, 0.75, 0.15, 0.13, 5.1],
]

var _t := 0.0
var _sweep := 0.0
var _alarm := 0.0
var _alarm_target := 0.0
var _pulse := 0.0
var _flash := 0.0
var _flash_dir := Vector3(0, 0.3, -1)
var _clocked: Array = []        ## every ShaderMaterial that reads `clock`
var _mats := {}
var _sky: ShaderMaterial
var _sea: ShaderMaterial
var _searchlights: Array = []   ## [pivot Node3D, flare material, SEARCH row]
var _lighthouse: Node3D
var _lh_flares: Array = []      ## [flare material, beam sign]
var _dishes: Array = []         ## [node, rad/s]
var _bob: Array = []            ## [node, rest transform, height, rate, phase, roll]
var _flash_light: OmniLight3D
var _meteor_rng := RandomNumberGenerator.new()
var _meteor := {}               ## a, b, start, length
var _next_meteor := 2.2


## The environment the view applies. Keys: sky_top, sky_horizon, ground_horizon, ground_bottom (Color, for a
## ProceduralSkyMaterial: ambient and reflections; the dome covers the background), sun_color, sun_rotation
## (Vector3, degrees, for the DirectionalLight3D: the moonlight), sun_energy, ambient_color, ambient_energy,
## fog_color, fog_density (exponential fog), fog_sun_scatter, exposure, glow_intensity, glow_threshold, saturation,
## contrast, night (true: keep the field's own lights on), name.
func environment_for() -> Dictionary:
	var out := {}
	for k in ["sky_top", "sky_horizon", "ground_horizon", "ground_bottom", "sun_color", "sun_energy", "ambient_color",
			"ambient_energy", "fog_color", "fog_density", "fog_sun_scatter", "exposure", "glow_intensity",
			"glow_threshold", "saturation", "contrast", "night", "name"]:
		out[k] = LOOK[k]
	var l := (LOOK["light_from"] as Vector3).normalized()
	out["sun_rotation"] = Vector3(rad_to_deg(asin(-l.y)), rad_to_deg(atan2(l.x, l.z)), 0.0)
	return out


## A ready Environment from environment_for()'s dictionary (the view may use it as is or copy the values).
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
	env.glow_bloom = 0.02
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	env.set_glow_level(1, 0.6)
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.8)
	env.set_glow_level(4, 0.5)
	env.adjustment_enabled = true
	env.adjustment_saturation = d["saturation"]
	env.adjustment_contrast = d["contrast"]
	return env


## The moonlight.
static func setup_sun(sun: DirectionalLight3D, d: Dictionary) -> void:
	sun.rotation_degrees = d["sun_rotation"]
	sun.light_color = d["sun_color"]
	sun.light_energy = d["sun_energy"]
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 60.0


## 0..1: how close the invaders are to the ground. The backdrop eases towards it.
func alarm(level: float) -> void:
	_alarm_target = clampf(level, 0.0, 1.0)


## A brief flash in the sky towards pos (play space), for a big explosion or the mothership going down.
func flash(pos: Vector3) -> void:
	_flash = 1.0
	_flash_dir = (pos + Vector3(0, 2.0, -12.0) - CAMERA).normalized()
	if _flash_light:
		_flash_light.position = Vector3(pos.x, maxf(pos.y, 2.0), -6.0)


func build() -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	_t = 0.0
	_sweep = 0.0
	_alarm = 0.0
	_alarm_target = 0.0
	_flash = 0.0
	_clocked.clear()
	_mats.clear()
	_searchlights.clear()
	_lh_flares.clear()
	_dishes.clear()
	_bob.clear()
	_lighthouse = null
	_meteor = {}
	_next_meteor = 2.2
	_meteor_rng.seed = 2525
	_add_sky()
	_add_sea()
	var packed := load(GLB) as PackedScene
	if packed == null:
		push_error("NovaBackdrop: missing %s" % GLB)
		return
	var root := packed.instantiate() as Node3D
	root.name = "diorama"
	add_child(root)
	_dress(root)
	_collect(root)
	_flash_light = OmniLight3D.new()
	_flash_light.name = "flash_light"
	_flash_light.light_color = Color("#ffd8b0")
	_flash_light.light_energy = 0.0
	_flash_light.omni_range = 45.0
	_flash_light.omni_attenuation = 1.2
	_flash_light.visible = false
	add_child(_flash_light)
	_apply()


func _shader(n: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SH + n + ".gdshader")
	_clocked.append(m)
	return m


func _add_sky() -> void:
	var dome := MeshInstance3D.new()
	dome.name = "sky"
	var m := SphereMesh.new()
	m.radius = DOME_RADIUS
	m.height = DOME_RADIUS * 2.0
	m.radial_segments = 48
	m.rings = 24
	dome.mesh = m
	dome.position = CAMERA
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dome.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	_sky = _shader("nova_sky")
	_sky.set_shader_parameter("top_col", LOOK["sky_top"])
	_sky.set_shader_parameter("mid_col", LOOK["sky_mid"])
	_sky.set_shader_parameter("horizon_col", LOOK["sky_horizon"])
	_sky.set_shader_parameter("below_col", LOOK["sky_below"])
	var drop := CAMERA.y - SEA_LEVEL
	_sky.set_shader_parameter("horizon_e", -drop / sqrt(drop * drop + SEA_RADIUS * SEA_RADIUS))
	_sky.set_shader_parameter("moon_dir", MOON_DIR.normalized())
	dome.material_override = _sky
	add_child(dome)


## The sea: a flat fan round the camera out to SEA_RADIUS (its rim is the horizon).
func _add_sea() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings := 22
	var segs := 72
	var a0 := deg_to_rad(-88.0)
	var a1 := deg_to_rad(88.0)
	var r0 := 12.0
	var pts: Array = []
	for i in rings + 1:
		var r := r0 * pow(SEA_RADIUS / r0, float(i) / rings)
		var row: Array = []
		for j in segs + 1:
			var a := lerpf(a0, a1, float(j) / segs)
			row.append(Vector3(CAMERA.x + sin(a) * r, SEA_LEVEL, CAMERA.z - cos(a) * r))
		pts.append(row)
	for i in rings:
		for j in segs:
			var q: Array = [pts[i][j], pts[i][j + 1], pts[i + 1][j + 1], pts[i + 1][j]]
			for k in [0, 2, 1, 0, 3, 2]:
				st.set_normal(Vector3.UP)
				st.add_vertex(q[k])
	var mi := MeshInstance3D.new()
	mi.name = "sea"
	mi.mesh = st.commit()
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	_sea = _shader("nova_sea")
	_sea.set_shader_parameter("horizon_col", LOOK["sky_horizon"])
	_sea.set_shader_parameter("sky_col", (LOOK["sky_mid"] as Color).lerp(LOOK["sky_horizon"], 0.35))
	_sea.set_shader_parameter("moon_dir", MOON_DIR.normalized())
	_sea.set_shader_parameter("camera_pos", CAMERA)
	_sea.set_shader_parameter("radius", SEA_RADIUS)
	mi.material_override = _sea
	add_child(mi)


## Swaps the named materials for the backdrop shaders; only the crest casts shadows.
func _dress(root: Node3D) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if nm.begins_with("fg_") \
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var mn := src.resource_name if src else ""
			mi.set_surface_override_material(i, _material_for(mn, src))


func _glow(col: Color, energy: float) -> ShaderMaterial:
	var g := _shader("nova_glow")
	g.set_shader_parameter("color", col)
	g.set_shader_parameter("energy", energy)
	return g


func _material_for(mn: String, src: Material) -> Material:
	if _mats.has(mn):
		return _mats[mn]
	var m: Material
	match mn:
		"window_glow":
			m = _glow(Color("#ffb45e"), 2.3)
			m.set_shader_parameter("twinkle", 0.25)
			m.set_shader_parameter("variety", 0.6)
			m.set_shader_parameter("cell", 0.9)
		"coolwindow_glow":
			m = _glow(Color("#9cc8ff"), 1.9)
			m.set_shader_parameter("twinkle", 0.3)
			m.set_shader_parameter("variety", 0.5)
			m.set_shader_parameter("cell", 0.9)
		"lamp_glow":
			m = _glow(Color("#ff9a40"), 3.2)
			m.set_shader_parameter("flicker", 0.06)
			m.set_shader_parameter("variety", 0.3)
			m.set_shader_parameter("cell", 1.5)
		"blink_glow":
			m = _glow(Color("#ff2418"), 7.0)
			m.set_shader_parameter("blink", 1.0)
			m.set_shader_parameter("cell", 30.0)
		"alarm_glow":
			m = _glow(Color("#ff1a10"), 9.0)
			m.set_shader_parameter("idle", 0.06)
			m.set_shader_parameter("cell", 2.0)
		"lens_glow":
			m = _glow(BEAM_COLOR, 1.3)
		"lantern_glow":
			m = _glow(Color("#ffe2a8"), 6.0)
		"harbour_glow":
			m = _glow(Color.WHITE, 6.0)
			m.set_shader_parameter("use_vertex_color", true)
			m.set_shader_parameter("blink", 0.8)
			m.set_shader_parameter("cell", 40.0)
		"reflect_glow":
			m = _shader("nova_reflect")
			m.set_shader_parameter("tint", Color("#ff9a40"))
		_:
			if src is BaseMaterial3D:
				# the colour lives in the vertex colours (the importer does not always flag it)
				var sm := (src as BaseMaterial3D).duplicate() as BaseMaterial3D
				sm.vertex_color_use_as_albedo = true
				sm.rim_enabled = true
				sm.rim = 0.25
				sm.rim_tint = 0.7
				m = sm
			else:
				m = src
	_mats[mn] = m
	return m


## A descendant's transform in this node's space (works before the backdrop enters the tree).
func _local_xform(n: Node3D) -> Transform3D:
	var tr := n.transform
	var p := n.get_parent()
	while p != self and p is Node3D:
		tr = (p as Node3D).transform * tr
		p = p.get_parent()
	return tr


func _collect(root: Node3D) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 25000
	for n in root.find_children("*", "Node3D", true, false):
		var node := n as Node3D
		var nm := String(node.name)
		if nm == "beam":
			_add_lighthouse(_local_xform(node).origin)
		elif nm.begins_with("searchlight_") and not nm.begins_with("searchlight_mount"):
			var i := nm.trim_prefix("searchlight_").to_int()
			_add_searchlight(_local_xform(node).origin, SEARCH[i % SEARCH.size()])
		elif nm.begins_with("dish_"):
			_dishes.append([node, 0.32 if nm == "dish_0" else -0.55])
		elif nm.begins_with("boat_"):
			_bob.append([node, node.transform, 0.08, 0.7 + 0.4 * rng.randf(), rng.randf() * TAU, 0.03])


## An open cone from the apex (the origin) along -z: length, end radius; UV.y runs from the apex (0) to the end (1).
func _cone(length: float, radius: float, apex_r: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var segs := 20
	var rows := 6
	for i in rows:
		for j in segs:
			var quad: Array = []
			for c in [[i, j], [i, j + 1], [i + 1, j + 1], [i + 1, j]]:
				var t := float(c[0]) / rows
				var a := TAU * float(c[1]) / segs
				var r := lerpf(apex_r, radius, t)
				var rad := Vector3(cos(a), sin(a), 0.0)
				quad.append([rad * r + Vector3(0, 0, -length * t), rad, Vector2(float(c[1]) / segs, t)])
			for k in [0, 1, 2, 0, 2, 3]:
				st.set_normal(quad[k][1])
				st.set_uv(quad[k][2])
				st.add_vertex(quad[k][0])
	return st.commit()


func _flare(pos: Vector3, size: float, col: Color) -> ShaderMaterial:
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	var m := ShaderMaterial.new()
	m.shader = load(SH + "nova_flare.gdshader")
	m.set_shader_parameter("color", col)
	var mi := MeshInstance3D.new()
	mi.name = "flare"
	mi.mesh = q
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# a little towards the camera, so the lamp's own housing does not clip it
	mi.position = pos + (CAMERA - pos).normalized() * 1.2
	add_child(mi)
	return m


func _add_searchlight(p: Vector3, row: Array) -> void:
	var pivot := Node3D.new()
	pivot.name = "searchlight_beam_%d" % _searchlights.size()
	pivot.position = p
	add_child(pivot)
	var beam := MeshInstance3D.new()
	beam.mesh = _cone(150.0, 6.5, 0.45)
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := _shader("nova_beam")
	m.set_shader_parameter("color", BEAM_COLOR)
	m.set_shader_parameter("strength", 0.11)
	m.set_shader_parameter("falloff", 1.1)
	beam.material_override = m
	pivot.add_child(beam)
	var fl := _flare(p, 2.2, BEAM_COLOR)
	_searchlights.append([pivot, fl, row, m])


func _add_lighthouse(p: Vector3) -> void:
	_lighthouse = Node3D.new()
	_lighthouse.name = "lighthouse_beams"
	_lighthouse.position = p
	add_child(_lighthouse)
	var col := Color("#ffe6b8")
	for s in [1.0, -1.0]:
		var beam := MeshInstance3D.new()
		beam.mesh = _cone(70.0, 5.0, 0.5)
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		beam.rotation = Vector3(deg_to_rad(2.0), 0.0 if s > 0 else PI, 0.0)
		var m := _shader("nova_beam")
		m.set_shader_parameter("color", col)
		m.set_shader_parameter("strength", 0.1)
		m.set_shader_parameter("falloff", 1.8)
		beam.material_override = m
		_lighthouse.add_child(beam)
		_lh_flares.append([_flare(p, 7.0, col), s])
	_sea.set_shader_parameter("beam_pos", p)


func _process(delta: float) -> void:
	_t += delta
	_alarm = move_toward(_alarm, _alarm_target, delta * 0.8)
	_sweep += delta * (1.0 + 2.2 * _alarm)
	_flash = maxf(0.0, _flash - delta * 3.2)
	_pulse = pow(maxf(0.0, sin(_t * TAU * (0.5 + 0.5 * _alarm))), 2.0)
	_apply()


## Everything that follows the clock: shaders, beams, flares, dishes, boats, meteors, the flash.
func _apply() -> void:
	for m in _clocked:
		(m as ShaderMaterial).set_shader_parameter("clock", _t)
	var to_cam := Vector3.ZERO
	for s in _searchlights:
		var pivot: Node3D = s[0]
		var row: Array = s[2]
		var ph: float = _sweep * row[4] + row[5]
		var yaw: float = row[0] + row[1] * sin(ph) + 0.12 * sin(ph * 2.3 + 1.0)
		var pitch: float = row[2] + row[3] * sin(ph * 0.71 + 0.5)
		var dir := Vector3(sin(yaw) * cos(pitch), sin(pitch), -cos(yaw) * cos(pitch))
		pivot.basis = Basis.looking_at(dir, Vector3.UP)
		to_cam = (CAMERA - pivot.position).normalized()
		var face := maxf(dir.dot(to_cam), 0.0)
		(s[1] as ShaderMaterial).set_shader_parameter("bright", 0.2 + 3.0 * pow(face, 6.0) + 0.3 * _alarm)
		(s[3] as ShaderMaterial).set_shader_parameter("strength", 0.11 + 0.06 * _alarm)
	if _lighthouse:
		_lighthouse.rotation.y = _t * LIGHTHOUSE_SPEED
		var bd := -_lighthouse.basis.z
		to_cam = (CAMERA - _lighthouse.position).normalized()
		for f in _lh_flares:
			var face := maxf((bd * float(f[1])).dot(to_cam), 0.0)
			(f[0] as ShaderMaterial).set_shader_parameter("bright", 0.5 + 6.0 * pow(face, 10.0))
		_sea.set_shader_parameter("beam_dir", bd)
	for d in _dishes:
		(d[0] as Node3D).rotation.y = _t * float(d[1])
	for b in _bob:
		var node: Node3D = b[0]
		var rest: Transform3D = b[1]
		var ph: float = _t * b[3] + b[4]
		var tr := rest
		tr.origin.y += sin(ph) * b[2]
		tr.basis = rest.basis * Basis(Vector3.BACK, sin(ph * 0.8 + 1.0) * b[5])
		node.transform = tr
	_update_meteor()
	# alarm and flash
	for mn in ["alarm_glow"]:
		if _mats.has(mn):
			(_mats[mn] as ShaderMaterial).set_shader_parameter("alarm", _alarm)
	for mn in ["window_glow", "coolwindow_glow"]:
		if _mats.has(mn):
			(_mats[mn] as ShaderMaterial).set_shader_parameter("dim", 0.45 * _alarm)
	for m in [_sky, _sea]:
		if m:
			m.set_shader_parameter("alarm", _alarm)
			m.set_shader_parameter("alarm_pulse", _pulse)
			m.set_shader_parameter("flash", _flash * _flash)
	if _sky:
		_sky.set_shader_parameter("flash_dir", _flash_dir)
	if _flash_light:
		_flash_light.visible = _flash > 0.01
		_flash_light.light_energy = 8.0 * _flash * _flash


func _update_meteor() -> void:
	if _sky == null:
		return
	if _meteor.is_empty() and _t >= _next_meteor:
		# the view spans about +-0.55 rad across and -0.1..+0.33 rad up: start high, mostly over the sides
		var side := 1.0 if _meteor_rng.randf() < 0.5 else -1.0
		var az := side * _meteor_rng.randf_range(0.2, 0.62)
		var el := _meteor_rng.randf_range(0.2, 0.34)
		var a := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
		var turn := _meteor_rng.randf_range(0.14, 0.24) * side
		var drop := _meteor_rng.randf_range(0.07, 0.12)
		var b := Vector3(sin(az + turn) * cos(el - drop), sin(el - drop), -cos(az + turn) * cos(el - drop))
		_meteor = {"a": a, "b": b, "start": _t, "length": _meteor_rng.randf_range(0.8, 1.3)}
		_next_meteor = _t + _meteor_rng.randf_range(6.0, 13.0)
	if _meteor.is_empty():
		_sky.set_shader_parameter("meteor_t", -1.0)
		return
	var k: float = (_t - float(_meteor["start"])) / float(_meteor["length"])
	if k > 1.0:
		_meteor = {}
		_sky.set_shader_parameter("meteor_t", -1.0)
		return
	_sky.set_shader_parameter("meteor_a", _meteor["a"])
	_sky.set_shader_parameter("meteor_b", _meteor["b"])
	_sky.set_shader_parameter("meteor_t", k)
