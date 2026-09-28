class_name FrostpeakView3D
extends Node3D
## Frostpeak Games in 3D: four venues in one alpine valley (FrostpeakValley). The speed-skating oval sits at the
## origin, the large jump hill (FrostpeakHill) at the valley's head backing onto the mountains, the biathlon stadium
## and its course (FrostpeakBiathlon) in the woods to the north-west, the medal plaza with the podium and the
## cauldron at PLAZA. The venues are built from the events' own geometry (lane lengths, the
## hill's profile) so the picture matches the rules. Between venues the camera flies (FrostpeakFlight) high over
## the valley. Banners and painted lettering are drawn once into textures at start (invented names only).

const M := "res://games/frostpeak/art/models/"
const SH := "res://games/frostpeak/shaders/"
const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage
const STRAIGHT := 100.0
const RADIUS := 30.0
const LANES: Array[float] = [2.0, 6.0]  ## lane centres, out from the inner radius (player, rival)
const PLAZA := Vector3(-500, 0, 0)
const SUN_ELEVATION := 20.0  ## a low winter sun, beside the jump hill (on its left, looking down) and a little down it
const SUN_AZIMUTH := -58.0
const SHADOW_FAR := 700.0  ## how far the sun's shadows reach (4 cascades, the nearest a few centimetres a texel)
const RIM_LAYER := 1 << 10  ## render layer 11: the athletes, lit by the rim light too
const MAX_TURN := 1.2  ## the camera never turns faster than this (radians a second)
const WIPE_COVER := 0.32  ## a replay wipe covers the screen this long after it starts (the cut is hidden there)
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

signal tv_sound(name: String, db: float, pitch: float)  ## the replay's sounds (slowed down with it)

@export var game: FrostpeakGame

var _camera: Camera3D
var _sun: DirectionalLight3D
var _rim: DirectionalLight3D
var _snow_mat: ShaderMaterial
var _ice_mat: ShaderMaterial
var _skater: Node3D
var _rival: Node3D
var _jumper: Node3D
var _jumper_wait: Node3D  ## the next athletes, waiting at the start while the last ones stay where they finished
var _skater_wait: Node3D
var _rival_wait: Node3D
var _podium_people: Array[Node3D] = []
var _flags: Array[MeshInstance3D] = []
var _snowfall: GPUParticles3D
var _cam_pos := Vector3(0, 30, 80)
var _cam_look := Vector3.ZERO
var _cam_vel := Vector3.ZERO
var _look_vel := Vector3.ZERO
var _t := 0.0
var _stage_t := 0.0
var _landed_x := 0.0
var _slide := 0.0
var _slide_v := -1.0
var _paint: Array = []  ## [SubViewport, Callable(texture)]: text drawn once, then baked into mipmapped textures
var _boards: Array[Label3D] = []  ## scoreboard lines, rewritten live
var _crowd_mats := {}
var _flag_shader: Shader
var _rng := RandomNumberGenerator.new()
var _into: Node3D = self  ## where props, instanced sets and flags are added (the hill builds in its own frame)
var valley: FrostpeakValley
var hill: FrostpeakHill
var biathlon: FrostpeakBiathlon
var bview: FrostpeakBiathlonView
var _flight: FrostpeakFlight
var _fly_v0 := Vector3.ZERO  ## how the camera was moving when the flight took over
var _fly_lv0 := Vector3.ZERO
var _flight_key := ""  ## which move the current flight is (so a stage starts it once)
var _shafts: ShaderMaterial
var _to_sun := Vector3.UP
var _stage := -1
var _jcam: FrostpeakJumpCam
var _rec := FrostpeakReplay.new()
var _fov := 50.0
var _fov_cut := false
var _cam_q := Quaternion.IDENTITY
var _turn_v := Vector3.ZERO  ## how the lens is turning (radians a second, about each axis)
var _turn_w := 30.0  ## how closely it follows (1/s): tight on the athletes, softer in flights
var _in_flight := false
var _have_q := false
var _hand_pos := Vector3.ZERO  ## a glide from where the camera was (see _handoff)
var _hand_look := Vector3.ZERO
var _hand_len := 0.0
var _hand_left := 0.0
var _stop_turn := 0.0  ## how far the jumper has turned side-on, stopping in the arena
var _rp_active := false  ## the replay
var _rp_shots: Array = []
var _rp_i := -1
var _rp_t := 0.0  ## live time the replay shows
var _rp_wiped := 0
var _rp_cut := false
var _rp_live: Array = []  ## the live picture to come back to: camera, look, lens, the jumper
var _wipe_t := -1.0
var _ticked := {}  ## values the events move tick by tick: [the previous tick's, the last tick's, which tick]
var _last_lp := Vector3.ZERO  ## the jumper as last drawn (hill frame)
var _land_drop := 0.0  ## how far the jumper still sinks onto the snow, just landed
var _glide := 0.0  ## the skater's glide on past the finish
var _glide_v := 0.0


func _ready() -> void:
	_rng.seed = 77
	_flag_shader = load(SH + "flag.gdshader")
	_snow_mat = ShaderMaterial.new()
	_snow_mat.shader = load(SH + "snow.gdshader")
	_ice_mat = ShaderMaterial.new()
	_ice_mat.shader = load(SH + "ice.gdshader")
	_build_world()
	valley = FrostpeakValley.new(self)
	valley.build()
	_build_oval()
	hill = FrostpeakHill.new(self, valley)
	hill.build()
	biathlon = FrostpeakBiathlon.new(self, valley)
	biathlon.build()
	valley.build_roads(ground_y)
	_jcam = FrostpeakJumpCam.new(func(x: float, z: float) -> float: return hill.terrain_y(x, z))
	_build_plaza()
	_skater = _athlete("skater")
	_rival = _athlete("skater")
	_jumper = _athlete("jumper")
	_jumper_wait = _athlete("jumper")
	_skater_wait = _athlete("skater")
	_rival_wait = _athlete("skater")
	for n in [_jumper_wait, _skater_wait, _rival_wait]:
		n.visible = false
	bview = FrostpeakBiathlonView.new(self, biathlon)
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
	_into.add_child(n)
	_texture(n)
	return n


## Gives the props' plain Blender colours real surfaces from the shared CC0 sets: concrete, timber, steel sheet.
func _swaps() -> Dictionary:
	if not _crowd_mats.has("swaps"):
		_crowd_mats["swaps"] = {
			"stand_concrete": Pbr.material("metal", Color(0.92, 0.92, 0.93), 0.35, 0.0, 1.2),
			"timber": Pbr.local("planks", Color(0.7, 0.5, 0.35), 0.8),
			"roof": Pbr.material("metal", Color(0.85, 0.87, 0.9), 0.5, 0.7, 0.6),
			"cladding": Pbr.material("metal", Color(0.42, 0.48, 0.58), 0.7, 0.6, 0.8),
			"plinth": Pbr.material("stone_bricks", Color(0.85, 0.86, 0.9), 0.8),
		}
	return _crowd_mats["swaps"]


## The same swaps, for a model drawn many times in a MultiMesh.
func _prop_overrides(_model: String) -> Dictionary:
	return _swaps()


func _texture(n: Node3D) -> void:
	var swap := _swaps()
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			if mat and swap.has(mat.resource_name):
				m.set_surface_override_material(i, swap[mat.resource_name])


func _athlete(kind: String) -> Node3D:
	var n := _scene(kind)
	add_child(n)
	for mi in n.find_children("*", "VisualInstance3D", true, false):
		(mi as VisualInstance3D).layers |= RIM_LAYER
	var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
	for a in ap.get_animation_list():
		ap.get_animation(a).loop_mode = Animation.LOOP_LINEAR if a in ["idle", "skate", "glide", "ready", "tuck", "flight", "wave", "celebrate", "telemark", "prone"] else Animation.LOOP_NONE
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
## Many copies of one model in MultiMeshes. `overrides` swaps materials by name (on a copy of the mesh);
## `colors` and `customs` fill the per-instance colour and custom data the crowd shader reads. Big sets are cut
## into 160 m cells, so each cell is culled on its own and, past `vis_end` metres, not drawn at all.
func _multi(model: String, xforms: Array[Transform3D], overrides := {}, colors: Array[Color] = [], customs: Array[Color] = [],
		vis_end := 0.0, shadows := true, proxy: Mesh = null) -> void:
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
	var cells := {}
	for i in xforms.size():
		var o := xforms[i].origin
		var key := Vector2i(floori(o.x / 160.0), floori(o.z / 160.0)) if xforms.size() > 300 else Vector2i.ZERO
		if not cells.has(key):
			cells[key] = []
		cells[key].append(i)
	for key in cells:
		var ids: Array = cells[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = not colors.is_empty()
		mm.use_custom_data = not customs.is_empty()
		mm.mesh = mesh
		mm.instance_count = ids.size()
		for k in ids.size():
			var i: int = ids[k]
			mm.set_instance_transform(k, xforms[i])
			if mm.use_colors:
				mm.set_instance_color(k, colors[i % colors.size()])
			if mm.use_custom_data:
				mm.set_instance_custom_data(k, customs[i % customs.size()])
		var inst := MultiMeshInstance3D.new()
		inst.multimesh = mm
		inst.visibility_range_end = vis_end
		inst.visibility_range_end_margin = vis_end * 0.1
		inst.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF if vis_end > 0.0 else GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		if not shadows or proxy:
			inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_into.add_child(inst)
		if shadows and proxy:  # the shadow drawn from a few dozen triangles instead of a thousand
			var sm := MultiMesh.new()
			sm.transform_format = MultiMesh.TRANSFORM_3D
			sm.mesh = proxy
			sm.instance_count = ids.size()
			for k in ids.size():
				sm.set_instance_transform(k, xforms[ids[k]])
			var si := MultiMeshInstance3D.new()
			si.multimesh = sm
			si.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
			si.visibility_range_end = vis_end
			_into.add_child(si)


## Spectators: three poses mixed, each with its own coat, hat, scarf and skin tone.
func _crowd(xforms: Array[Transform3D], seed: int, hop := 1.0, shadows := true) -> void:
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
		_multi(model, xs, _crowd_overrides(hop), cols, cus, 750.0, shadows, _shadow_proxy("person"))


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
func _forest(xforms: Array[Transform3D], seed: int, shadows := false, vis_end := 1400.0) -> void:
	var tm := ShaderMaterial.new()
	tm.shader = load(SH + "tree.gdshader")
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var pines: Array[Transform3D] = []
	var spruces: Array[Transform3D] = []
	for x in xforms:
		(pines if rng.randf() < 0.55 else spruces).append(x)
	# only the woods lining the hill cast sun shadows (soft, from the low sun); the wide forests cast none
	_multi("snowy_pine", pines, {"pine_needles": tm}, [], [], vis_end, shadows, _shadow_proxy("pine"))
	_multi("snowy_spruce", spruces, {"pine_needles": tm}, [], [], vis_end, shadows, _shadow_proxy("spruce"))


## Shadow stand-ins for the crowds and the woods: a person is a tapered column with a head, a pine or a spruce
## three stacked cones of its outline. Drawn into the shadow map only, they cost a few dozen triangles apiece.
func _shadow_proxy(kind: String) -> Mesh:
	var key := "proxy_" + kind
	if _crowd_mats.has(key):
		return _crowd_mats[key]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# rings of [height, radius], joined into a closed column of 6 sides
	var rings: Array = [[0.0, 0.16], [0.9, 0.18], [1.45, 0.22], [1.52, 0.1], [1.6, 0.12], [1.82, 0.1], [1.88, 0.0]]
	if kind == "pine":
		rings = [[0.0, 0.17], [0.5, 0.17], [0.5, 1.55], [2.2, 0.8], [2.2, 1.2], [3.6, 0.45], [3.6, 0.6], [5.45, 0.0]]
	elif kind == "spruce":
		rings = [[0.0, 0.12], [0.7, 0.12], [0.7, 1.1], [3.2, 0.65], [3.2, 0.8], [5.5, 0.32], [5.5, 0.45], [7.3, 0.0]]
	var sides := 6
	for r in rings.size() - 1:
		for i in sides:
			var a0 := TAU * i / sides
			var a1 := TAU * (i + 1) / sides
			var q: Array[Vector3] = [
				Vector3(cos(a0) * rings[r][1], rings[r][0], sin(a0) * rings[r][1]),
				Vector3(cos(a1) * rings[r][1], rings[r][0], sin(a1) * rings[r][1]),
				Vector3(cos(a1) * rings[r + 1][1], rings[r + 1][0], sin(a1) * rings[r + 1][1]),
				Vector3(cos(a0) * rings[r + 1][1], rings[r + 1][0], sin(a0) * rings[r + 1][1])]
			for k in [0, 2, 1, 0, 3, 2]:
				st.add_vertex(q[k])
	st.generate_normals()
	var mesh := st.commit()
	_crowd_mats[key] = mesh
	return mesh


## Far woods (mountain flanks, the back of the hill): the same conifers as three stacked cones, a few dozen
## triangles each, so thousands cost little.
func _forest_far(xforms: Array[Transform3D]) -> void:
	if not _crowd_mats.has("far_tree"):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var tiers := [[0.9, 3.4, 1.9], [2.6, 4.9, 1.45], [4.2, 6.6, 0.95]]  # base height, tip height, radius
		for t in tiers:
			for i in 7:
				var a0: float = TAU * i / 7.0
				var a1: float = TAU * (i + 1) / 7.0
				var p0 := Vector3(cos(a0) * t[2], t[0], sin(a0) * t[2])
				var p1 := Vector3(cos(a1) * t[2], t[0], sin(a1) * t[2])
				var tip := Vector3(0, t[1], 0)
				var n := (p1 - p0).cross(tip - p0).normalized()
				for v in [p0, tip, p1]:
					st.set_normal(-n if n.y < 0.0 else n)
					st.add_vertex(v)
		var tm := ShaderMaterial.new()
		tm.shader = load(SH + "tree.gdshader")
		var mesh := st.commit()
		mesh.surface_set_material(0, tm)
		_crowd_mats["far_tree"] = mesh
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _crowd_mats["far_tree"]
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_into.add_child(inst)


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
	_into.add_child(flag)
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
	if _crowd_mats.has("banners"):
		return _crowd_mats["banners"]
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
	out.append(_banner_mat("SNOWLINE", Color(0.95, 0.3, 0.1), Color(0.98, 0.97, 0.94)))
	out.append(_banner_mat("PEAK RADIO", Color.WHITE, Color(0.75, 0.1, 0.15), Color.WHITE))
	_crowd_mats["banners"] = out
	return out


func _quad(pos: Vector3, size: Vector2, mat: Material, basis: Basis) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = size
	mi.mesh = q
	mi.material_override = mat
	mi.transform = Transform3D(basis, pos)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_into.add_child(mi)
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
	var sky_mat := ShaderMaterial.new()
	sky_mat.shader = load(SH + "sky.gdshader")
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	Look.sky_ambient(env, Color(0.7, 0.75, 0.86), 0.5)
	if not Look.compat():  # part sky, part a neutral fill: blue shadows on the snow, but not ink-blue
		env.ambient_light_color = Color(0.78, 0.8, 0.86)
		env.ambient_light_sky_contribution = 0.55
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	# graded like a winter broadcast: crisp, a little contrast, cool shadows and warm highlights
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 0.82
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = 0.5
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	# contact shadows where things meet the snow, and light bounced off the sunlit snow into the shade
	env.ssao_enabled = true
	env.ssao_radius = 1.4
	env.ssao_intensity = 1.8
	env.ssao_detail = 0.6
	env.ssao_light_affect = 0.25  # a little of it in the sun too, so feet and fence posts sit on the snow
	env.ssil_enabled = true
	env.ssil_radius = 4.0
	env.ssil_intensity = 0.8
	env.ssr_enabled = true  # the ice reflects the stand, the floodlights and the skaters
	env.ssr_max_steps = 48
	Look.fog(env, Color(0.78, 0.85, 0.95), 0.00028)
	env.fog_aerial_perspective = 0.5
	env.fog_sky_affect = 0.4
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.14
	env.adjustment_contrast = 1.12
	env.adjustment_color_correction = _grade()
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	# a low winter sun, from beside the jump hill and a little down it (the hill runs towards -x). From the chase and
	# side cameras, which look across the landing slope from its right, the sun is ahead: every shadow that falls
	# into their picture comes from something standing in it (the judges' tower, the masts, the jumper), and the
	# shadows of whatever is behind them fall away, out of the picture.
	var el := deg_to_rad(SUN_ELEVATION)
	var az := deg_to_rad(SUN_AZIMUTH)
	_to_sun = Vector3(-cos(el) * cos(az), sin(el), -cos(el) * sin(az)).normalized()
	_sun = DirectionalLight3D.new()
	_sun.basis = Basis.looking_at(-_to_sun, Vector3.UP)
	_sun.light_color = Color(1.0, 0.86, 0.68)
	_sun.light_energy = 1.9
	_sun.light_angular_distance = 0.9  # a soft penumbra that widens away from the caster: sharp at the feet
	_sun.shadow_enabled = true
	_sun.shadow_bias = 0.03
	_sun.shadow_normal_bias = 0.9
	_sun.shadow_blur = 1.0
	_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	_sun.directional_shadow_blend_splits = true
	_shadow_range(SHADOW_FAR)
	add_child(_sun)
	# a cool rim on the athletes from behind them, as a TV lighting rig would give (athletes only)
	_rim = DirectionalLight3D.new()
	_rim.light_color = Color(0.78, 0.88, 1.0)
	_rim.light_energy = 1.6
	_rim.light_specular = 0.6
	_rim.light_cull_mask = RIM_LAYER
	_rim.shadow_enabled = false
	add_child(_rim)
	_camera = Camera3D.new()
	_camera.fov = 50
	_camera.far = 5000.0
	_camera.current = true
	add_child(_camera)
	# light shafts from the low sun: a full-screen pass on the camera (Forward+ only: it reads the depth buffer)
	if not Look.compat():
		var q := QuadMesh.new()
		q.size = Vector2(1, 1)
		var mi := MeshInstance3D.new()
		mi.mesh = q
		_shafts = ShaderMaterial.new()
		_shafts.shader = load(SH + "sun_shafts.gdshader")
		mi.material_override = _shafts
		mi.extra_cull_margin = 16384.0
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.position = Vector3(0, 0, -1)
		_camera.add_child(mi)
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


## The grade, applied after tone mapping: shadows lean blue, highlights warm, the snow stays white.
func _grade() -> GradientTexture1D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.25, 0.6, 1.0])
	g.colors = PackedColorArray([Color(0.0, 0.012, 0.04), Color(0.225, 0.245, 0.275), Color(0.605, 0.6, 0.59), Color(1.0, 0.99, 0.975)])
	var t := GradientTexture1D.new()
	t.gradient = g
	t.width = 256
	return t


## How far the sun's shadows reach (the project's 4096 atlas: 2048 a cascade). The cascades split at 4 %, 12 % and
## 32 % of it, so the nearest (under 30 m) holds the jumper and whatever stands by the camera at about a centimetre
## a texel; they fade out over the last 15 %, so no edge shows where they end.
func _shadow_range(far: float) -> void:
	_sun.directional_shadow_max_distance = far
	_sun.directional_shadow_split_1 = 0.04
	_sun.directional_shadow_split_2 = 0.12
	_sun.directional_shadow_split_3 = 0.32
	_sun.directional_shadow_fade_start = 0.85


## The rim light shines from behind the athlete towards the camera, from a little above and to the sun's side.
func _update_rim() -> void:
	var target := _jumper if _jumper.visible else (bview.athlete if bview.athlete.visible else _skater)
	var back := (target.global_position - _camera.global_position)
	back.y = 0.0
	if back.length() < 0.01:
		return
	back = back.normalized()
	var side := Vector3(_to_sun.x, 0.0, _to_sun.z).normalized()
	var to_light := (back * 1.0 + side * 0.45 + Vector3.UP * 0.55).normalized()
	_rim.basis = Basis.looking_at(-to_light, Vector3.UP)


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


## One grandstand section at `xf` (its front wall at the origin, facing +Z), full of fans, lettering on the fascia.
func _stand(xf: Transform3D, seed: int, fill := 0.9) -> void:
	var st := _prop("grandstand", xf.origin, 0.0)
	st.basis = xf.basis
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var seats: Array[Transform3D] = []
	var yaw := xf.basis.get_euler().y
	for r in ROWS:
		for sidx in SEATS:
			if rng.randf() > fill:
				continue
			var xb := -SEC * 0.5 + 1.2 + (sidx + 0.5) * (SEC - 2.4) / SEATS + rng.randf_range(-0.05, 0.05)
			var p := xf * Vector3(xb, Z0 + r * RISE, -(Y0 + r * TREAD + 0.14))
			seats.append(Transform3D(Basis(Vector3.UP, yaw + rng.randf_range(-0.25, 0.25)).scaled(Vector3.ONE * rng.randf_range(0.92, 1.06)), p))
	_crowd(seats, seed, 1.0, false)
	if not _crowd_mats.has("fascia"):
		_crowd_mats["fascia"] = _banner_mat("FROSTPEAK  GAMES", Color.WHITE, Color(0.1, 0.22, 0.55), Color(1.0, 0.82, 0.25))
	var fascia: Material = _crowd_mats["fascia"]
	_quad(xf * Vector3(0, 12.0, 2.44), Vector2(SEC - 1.0, 1.1), fascia, xf.basis)


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
		if sin(a) < -0.8:  # the camera comes in from the north
			continue
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
	var prev := _stage
	_stage = stage
	_stage_t = 0.0
	var ev := game.comp.event_name() if game.comp else ""
	if prev == S.REPLAY and _rp_active:
		_end_replay()
	_skater.visible = false
	_rival.visible = false
	_jumper.visible = false
	# whoever has just finished stays where they are as the camera leaves (another model waits at the start)
	var stays: bool = stage in [S.STANDINGS, S.NEXT] and prev in [S.RESULT, S.REPLAY]
	bview.athlete.visible = stays and ev == "biathlon"
	bview.waiting.node.visible = false
	_jumper_wait.visible = false
	_skater_wait.visible = false
	_rival_wait.visible = false
	if stays and ev == "speed_skating":
		_skater.visible = true
		_rival.visible = true
	if stays and ev == "ski_jump" and stage == S.NEXT:
		_jumper.visible = true
	for p in _podium_people:
		p.visible = false
	match stage:
		S.PODIUM:
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
		S.INTRO, S.NEXT:
			# the next athlete waits at the start while the camera flies in
			var nation: int = game.comp.athletes[game.current_athlete()]["nation"]
			match ev:
				"ski_jump":
					_jumper_at_gate(nation)
					_fly_to_gate(game.stage_seconds(stage), stage == S.INTRO)
				"speed_skating":
					_skaters_at_start(nation)
					_fly_to_oval(game.stage_seconds(stage), stage == S.INTRO)
				"biathlon":
					bview.wait_at_start(nation)
					_fly_to_stadium(game.stage_seconds(stage), stage == S.INTRO)
		S.REPLAY:
			_jumper.visible = true
			_start_replay()
		S.STANDINGS:
			if ev == "ski_jump" and not _rec.empty():  # the jumper waits in the arena as the camera leaves
				_jumper.visible = true
				_jumper.transform = _rec.xforms[_rec.xforms.size() - 1]
				_anim(_jumper, "celebrate" if not (game.ev as SkiJump).fell else "idle")
			_fly_to_plaza()


func _on_attempt(ev: WinterEvent) -> void:
	var nation: int = game.comp.athletes[game.humans()[game.athlete]]["nation"]
	_rec.clear()
	_ticked.clear()  # a new athlete: nothing to draw between from the last one
	if ev is SpeedSkating:
		_dress(_skater, nation)
		_dress(_rival, (nation + 3) % Competition.NATIONS.size())
		_take_over(_skater, _skater_wait)
		_take_over(_rival, _rival_wait)
	elif ev is Biathlon:
		bview.at_start(nation)
		ev.event.connect(bview.on_event)
		if not _flight_done():
			_handoff(1.4)
	else:
		_dress(_jumper, nation)
		_take_over(_jumper, _jumper_wait)
		_slide = 0.0
		_slide_v = -1.0
		_jcam.reset(FrostpeakJumpCam.GATE)
		if not _flight_done():  # an intro skipped part-way: glide over from where the camera is
			_handoff(1.4)


func _process(delta: float) -> void:
	_t += delta
	_stage_t += delta
	valley.process(delta)
	if game.comp == null:
		_plaza_camera(delta, true)
		_update_shafts()
		return
	bview.update_waiting(delta)
	if _wipe_t >= 0.0:
		_wipe_t += delta
		if _wipe_t > 2.0 * WIPE_COVER:
			_wipe_t = -1.0
	var fov := 50.0
	match game.stage:
		S.ATTEMPT, S.RESULT:
			if game.ev is SpeedSkating:
				_update_skating(game.ev as SpeedSkating, delta)
			elif game.ev is SkiJump:
				fov = _update_jump(game.ev as SkiJump, delta)
			elif game.ev is Biathlon:
				var b := game.ev as Biathlon
				bview.update(b, delta, game.stage == S.RESULT)
				var pl: Array = bview.camera(b, delta)
				_set_camera(pl[0], pl[1], delta)
				fov = pl[2]
				_fov_cut = true  # the rig glides its own lens (into the sight it narrows fast)
		S.REPLAY:
			fov = _update_replay(delta)
		S.INTRO, S.NEXT:
			if not _fly(delta):
				_hold_camera(delta)
			var end_fov: float = {"ski_jump": FrostpeakJumpCam.GATE["fov"], "biathlon": FrostpeakBiathlonView.START["fov"]}.get(game.comp.event_name(), 50.0)
			fov = end_fov if _flight_done() else lerpf(50.0, end_fov, smoothstep(0.6, 1.0, _flight.t / _flight.duration))
		S.STANDINGS:
			if not _fly(delta):
				_hold_camera(delta)
		S.PODIUM:
			for i in 3:
				var f := _flags[i]
				var top := 6.8 - (0.0 if i == 1 else 0.5)
				f.position.y = move_toward(f.position.y, top, delta * 1.6)
			if not _fly(delta):
				_move_camera(PLAZA + Vector3(0, 3.0, -11.0 + sin(_t * 0.2) * 0.5), PLAZA + Vector3(0, 2.2, 1.5), delta, 2.0)
		S.FINAL, S.SETUP, S.MENU:
			_flight_key = ""
			_plaza_camera(delta, false)
	# the lens glides too (a replay cut sets it outright)
	if _fov_cut:
		_fov = fov
		_fov_cut = false
	else:
		_fov = lerpf(_fov, fov, 1.0 - exp(-delta * 4.0))
	_camera.fov = _fov
	_snowfall.position = _camera.position + Vector3(0, 12, 0)
	_update_boards()
	_update_shafts()
	_update_rim()


## Puts the camera at `pos` looking at `look`. Every camera move ends here: a camera that has to take over from
## somewhere else (an intro skipped part-way) glides over from where it was, and the camera never turns faster
## than MAX_TURN, so nothing ever snaps. `cut` is for the replay's cuts (behind a wipe).
func _set_camera(pos: Vector3, look: Vector3, delta: float, cut := false, max_turn := MAX_TURN) -> void:
	if delta > 0.0 and not cut:  # how the camera is moving, so a spring can take over without a jolt
		_cam_vel = (pos - _cam_pos) / delta
		_look_vel = (look - _cam_look) / delta
	else:
		_cam_vel = Vector3.ZERO
		_look_vel = Vector3.ZERO
	_cam_pos = pos
	_cam_look = look
	if cut:
		_hand_left = 0.0
	elif _hand_left > 0.0:
		_hand_left = maxf(0.0, _hand_left - delta)
		var k := 1.0 - _hand_left / maxf(_hand_len, 0.001)
		k = k * k * (3.0 - 2.0 * k)
		pos = _hand_pos.lerp(pos, k)
		look = _hand_look.lerp(look, k)
	var want := Basis.looking_at(look - pos, Vector3.UP).get_rotation_quaternion()
	var q := want
	# the lens follows softly in flights, tightly on the athletes; the change between the two is gradual too
	_turn_w = move_toward(_turn_w, 6.0 if _in_flight else 30.0, delta * 12.0)
	_in_flight = false
	if not cut and _have_q and delta > 0.0:
		# the lens follows where it should look on a critically damped spring (a turn that starts or stops at once
		# still starts and stops smoothly), never faster than max_turn
		var off := _cam_q * want.inverse()
		if off.w < 0.0:
			off = -off
		var x := off.get_axis() * off.get_angle() if off.get_angle() > 0.00001 else Vector3.ZERO
		var d := x
		var e := exp(-_turn_w * delta)
		var tmp := (_turn_v + _turn_w * d) * delta
		var x1 := (d + tmp) * e
		_turn_v = (_turn_v - _turn_w * tmp) * e
		if _turn_v.length() > max_turn:
			_turn_v = _turn_v.normalized() * max_turn
		q = (Quaternion(x1.normalized(), x1.length()) * want) if x1.length() > 0.00001 else want
	else:
		_turn_v = Vector3.ZERO
	_cam_q = q.normalized()
	_have_q = true
	_camera.transform = Transform3D(Basis(_cam_q), pos)


## Starts a glide from where the camera is now to wherever the next move puts it, over `seconds`.
func _handoff(seconds: float) -> void:
	_hand_pos = _camera.position
	_hand_look = _camera.position - _camera.global_basis.z * maxf(10.0, _camera.position.distance_to(_cam_look))
	_hand_len = seconds
	_hand_left = seconds


## Glides the camera towards a pose on critically damped springs (no jolt when it sets off, no overshoot).
func _move_camera(pos: Vector3, look: Vector3, delta: float, speed := 3.0) -> void:
	var p := _spring3(_cam_pos, _cam_vel, pos, speed, delta)
	var l := _spring3(_cam_look, _look_vel, look, speed, delta)
	_set_camera(p[0], l[0], delta)
	_cam_vel = p[1]
	_look_vel = l[1]


static func _spring3(x: Vector3, v: Vector3, to: Vector3, w: float, dt: float) -> Array[Vector3]:
	var d := x - to
	var e := exp(-w * dt)
	var tmp := (v + w * d) * dt
	return [to + (d + tmp) * e, (v - w * tmp) * e]


func _snap_camera(pos: Vector3, look: Vector3) -> void:
	_set_camera(pos, look, 0.0, true)


## Keeps the camera where it is (a flight has landed and nothing else drives it).
func _hold_camera(delta: float) -> void:
	_set_camera(_cam_pos, _cam_look, delta)


func _plaza_camera(delta: float, snap: bool) -> void:
	var a := _t * 0.08
	var pos := PLAZA + Vector3(-12.0 + sin(a) * 22.0, 7.0, 4.0 - cos(a) * 22.0)
	var look := PLAZA + Vector3(-12.0, 4.0, 4.0)
	if snap:
		_snap_camera(pos, look)
	else:
		_move_camera(pos, look, delta, 1.5)


## The ground's height at a world point: the jump hill's terrain on its patch, the valley's elsewhere.
func ground_y(p: Vector3) -> float:
	if FrostpeakHill.covers(p):
		var l := hill.local(p)
		if l.x > FrostpeakHill.X0 and l.x < FrostpeakHill.X1 and absf(l.z) < FrostpeakHill.Z1:
			return hill.terrain_y(l.x, l.z) + hill.xf.origin.y
	return valley.height(p.x, p.z)


# ------------------------------------------------------------------ flights

## The lowest the camera may fly over a point: well over the trees, the rooftops and the pylons, the hill's
## terrain and its in-run tower.
func _clearance(p: Vector3) -> float:
	var need := valley.height(p.x, p.z) + 45.0
	if FrostpeakHill.covers(p):
		var l := hill.local(p)
		need = maxf(need, hill.terrain_y(l.x, l.z) + hill.xf.origin.y + 40.0)
		if l.x > -125.0 and l.x < 12.0 and absf(l.z) < 30.0:  # the in-run and the start tower
			need = maxf(need, hill.xf.origin.y + maxf(0.0, -l.x) * 0.56 + 30.0)
	return need


## For the glide up the hill: over the prepared slope (nothing stands on it) the camera may come down to a dozen
## metres; off it, where the woods, masts and towers are, it keeps high; over the in-run it keeps above the lamps.
func _clearance_hill(p: Vector3) -> float:
	if not FrostpeakHill.covers(p):
		return valley.height(p.x, p.z) + 45.0
	var l := hill.local(p)
	var ground := hill.terrain_y(l.x, l.z) + hill.xf.origin.y
	var open := hill.half_width(l.x) + (4.0 if l.x < 200.0 else 12.0)
	var need := ground + (11.0 if absf(l.z) < open else 34.0)
	if l.x > -125.0 and l.x < 6.0 and absf(l.z) < 7.0:
		need = maxf(need, hill.xf.origin.y + _inrun_y(l.x) + 4.0)
	return need


## The in-run's height (hill frame) over x.
func _inrun_y(x: float) -> float:
	var lo := SkiHill.TOP
	var hi := SkiHill.INRUN
	for i in 24:
		var m := (lo + hi) * 0.5
		if SkiHill.inrun_point(m).x < x:
			lo = m
		else:
			hi = m
	return SkiHill.inrun_point(lo).y


func _start_flight(key: String, pts: Array[Vector3], looks: Array[Vector3], seconds: float, clearance := Callable(),
		paces: Array[float] = [], hold := 0.06) -> void:
	_flight_key = key
	_flight = FrostpeakFlight.new(pts, looks, seconds, clearance if clearance.is_valid() else _clearance, hold, paces)
	_fly_v0 = _cam_vel  # the camera keeps its way on for a moment, fading into the flight
	_fly_lv0 = _look_vel


func _flight_done() -> bool:
	return _flight == null or _flight.done()


## Flies the current flight; false when there is none (or it has landed).
func _fly(delta: float) -> bool:
	if _flight_done():
		return false
	var pl := _flight.step(delta)
	var drift := _flight.t * exp(-_flight.t / 0.6)
	_in_flight = true
	_set_camera(pl[0] + _fly_v0 * drift, pl[1] + _fly_lv0 * drift, delta)
	return true


## The jumper on the bar at the gate, waiting.
func _jumper_at_gate(nation: int) -> void:
	_dress(_jumper_wait, nation)
	_jumper_wait.visible = true
	var lp := hill.inrun_at(0.0, 0.0, 0.08)
	var lb := Basis(Vector3.BACK, -SkiHill.inrun_angle(0.0)) * Basis(Vector3.UP, PI * 0.5)
	_jumper_wait.transform = Transform3D(hill.xf.basis * lb, hill.world(lp))
	_anim(_jumper_wait, "idle")


## The racing model takes over from the one that waited at the start, in the same pose (no pop).
func _take_over(racer: Node3D, waiter: Node3D) -> void:
	if not waiter.visible:
		return
	racer.transform = waiter.transform
	racer.visible = true
	var a: AnimationPlayer = racer.find_child("AnimationPlayer", true, false)
	var b: AnimationPlayer = waiter.find_child("AnimationPlayer", true, false)
	a.play(b.current_animation, 0.0)
	a.seek(b.current_animation_position, true)
	waiter.visible = false


## Into the ski jump, as one slow glide: from far out in the valley the whole hill ahead, in over the arena and up
## the landing slope, past the knoll and the take-off table, up beside the in-run, and round behind the jumper on
## the bar, where the live camera takes over (FrostpeakJumpCam.GATE). `far` starts the glide from the valley (the
## event's intro); otherwise (the next jumper) it starts from the arena.
func _fly_to_gate(seconds: float, far: bool) -> void:
	var gate := hill.inrun_at(0.0, 0.0, 0.08)
	var end := _jcam.pose(gate, FrostpeakJumpCam.GATE)
	var jumper := hill.world(hill.inrun_at(0.0, 0.0, 1.1))
	var pts: Array[Vector3] = [_cam_pos]
	var looks: Array[Vector3] = [_cam_look]
	var paces: Array[float] = [1.0]
	var up := func(x: float, z: float, h: float) -> Vector3: return hill.world(hill.ground(x, z) + Vector3(0, h, 0))
	if far:
		# out over the valley: the whole hill ahead, from the arena to the start tower on the mountainside
		var ahead := hill.world(Vector3(640.0, 20.0, 190.0))
		if _cam_pos.distance_to(ahead) > 500.0:
			var mid := _cam_pos.lerp(ahead, 0.45)
			mid.y = maxf(_cam_pos.y, ahead.y) + 30.0
			pts.append(mid)
			looks.append(_cam_look.lerp(hill.world(Vector3(0, 0, 0)), 0.6))
			paces.append(1.5)
		pts.append_array([ahead, hill.world(Vector3(470.0, -20.0, 110.0))])
		looks.append_array([hill.world(Vector3(40.0, -30.0, 0.0)), hill.world(Vector3(30.0, -22.0, 0.0))])
		paces.append_array([1.5, 1.2])
	pts.append_array([up.call(320.0, 12.0, 28.0), up.call(190.0, 12.0, 21.0), up.call(105.0, 11.0, 16.0),
		up.call(40.0, 10.0, 13.0), hill.world(hill.inrun_at(62.0, 10.0, 9.0)), hill.world(hill.inrun_at(24.0, 8.5, 6.5)),
		hill.world(hill.inrun_at(1.0, 8.0, 5.0)), hill.world(end[0])])
	looks.append_array([hill.world(hill.inrun_at(70.0, 0.0, 0.0)), hill.world(hill.inrun_at(40.0, 0.0, 2.0)), jumper,
		jumper, jumper, jumper, jumper.lerp(hill.world(end[1]), 0.45), hill.world(end[1])])
	paces.append_array([0.85, 0.6, 0.45, 0.36, 0.3, 0.22, 0.09, 0.045])
	_start_flight("gate", pts, looks, seconds, _clearance_hill, paces, 0.08)


## The oval's TV camera at the start: beside the track, level with the skater, a little ahead.
func _skate_cam(pos: float) -> Array[Vector3]:
	var me := oval_point(pos, LANES[0])
	var cam := me.origin - me.basis.x * 10.0 + Vector3(0, 3.2, 0) - me.basis.z * 2.0
	return [cam, me.origin + Vector3(0, 1.0, 0) - me.basis.z * 4.0]


func _skaters_at_start(nation: int) -> void:
	_dress(_skater_wait, nation)
	_dress(_rival_wait, (nation + 3) % Competition.NATIONS.size())
	_skater_wait.visible = true
	_rival_wait.visible = true
	var me := oval_point(0.0, LANES[0])
	var them := oval_point(0.0, LANES[1])
	_skater_wait.transform = Transform3D(me.basis.rotated(me.basis.y, PI), me.origin)
	_rival_wait.transform = Transform3D(them.basis.rotated(them.basis.y, PI), them.origin)
	_anim(_skater_wait, "ready")
	_anim(_rival_wait, "ready")


## Into the oval: over the valley, down past the west curve and along the back straight to the start, where the
## TV camera waits beside the skaters. From close by (the next skater), a low glide back along the straight.
func _fly_to_oval(seconds: float, far: bool) -> void:
	var end := _skate_cam(0.0)
	var pts: Array[Vector3] = [_cam_pos]
	var looks: Array[Vector3] = [_cam_look]
	var paces: Array[float] = [0.7]
	if far and _cam_pos.distance_to(end[0]) > 250.0:
		var dir := Vector3(end[0].x - _cam_pos.x, 0, end[0].z - _cam_pos.z).normalized()
		pts.append_array([_cam_pos + Vector3(0, 40, 0) + dir * 110.0, Vector3(-260, 70, -150), Vector3(-130, 34, -60)])
		looks.append_array([_cam_look.lerp(Vector3(0, 0, 0), 0.5), Vector3(0, 0, -10), Vector3(-20, 0, -20)])
		paces.append_array([1.6, 1.6, 1.0])
	else:
		var mid := (_cam_pos + end[0]) * 0.5 + Vector3(0, 9, 0)
		pts.append(mid)
		looks.append((_cam_look + end[1]) * 0.5)
		paces.append(1.4)
	pts.append_array([end[0] + Vector3(-26, 6, -6), end[0]])
	looks.append_array([end[1], end[1]])
	paces.append_array([0.6, 0.35])
	var clear := func(p: Vector3) -> float:
		return valley.height(p.x, p.z) + 45.0 if Vector2(p.x, p.z).length() > 190.0 else -INF
	_start_flight("oval", pts, looks, seconds, clear, paces, 0.12)


## Into the biathlon stadium: out over the woods, a sweep round past the range and its targets, and down to the
## start line, where the camera waits beside the skier (FrostpeakBiathlonView.START). From close by (the next
## skier), a low glide back along the straight.
func _fly_to_stadium(seconds: float, far: bool) -> void:
	var end := bview.start_pose()
	var pts: Array[Vector3] = [_cam_pos]
	var looks: Array[Vector3] = [_cam_look]
	var paces: Array[float] = [0.7]
	var stadium := Vector3(-335.0, 0.0, -215.0)
	if far and _cam_pos.distance_to(end[0]) > 200.0:
		var dir := Vector3(stadium.x - _cam_pos.x, 0, stadium.z - _cam_pos.z).normalized()
		var rise := _cam_pos + Vector3(0, 45, 0) + dir * minf(120.0, _cam_pos.distance_to(stadium) * 0.2)
		pts.append_array([rise, Vector3(-475, 70, -160), Vector3(-440, 40, -268), Vector3(-330, 22, -272), Vector3(-306, 11, -222)])
		looks.append_array([_cam_look.lerp(stadium, 0.5), stadium + Vector3(0, 0, -30), BiathlonCourse.targets(),
			BiathlonCourse.mat(), end[1]])
		paces.append_array([1.6, 1.3, 0.8, 0.55, 0.4])
	else:
		var mid := (_cam_pos + end[0]) * 0.5 + Vector3(0, 7, 0)
		pts.append(mid)
		looks.append((_cam_look + end[1]) * 0.5)
		paces.append(1.2)
	pts.append_array([end[0] + Vector3(12, 4, -3), end[0]])
	looks.append_array([end[1], end[1]])
	paces.append_array([0.32, 0.24])
	var clear := func(p: Vector3) -> float:
		if FrostpeakBiathlon.covers(p, 20.0):
			return valley.height(p.x, p.z) + (8.0 if biathlon.near(p) < 40.0 else 32.0)
		return valley.height(p.x, p.z) + 45.0
	_start_flight("stadium", pts, looks, seconds, clear, paces, 0.12)


## After an event, to the medal plaza (the standings board shows on the way): the camera rises, crosses the valley
## high enough that it drifts by slowly (higher the further it goes), and comes in over the crowd from the north to
## the podium.
func _fly_to_plaza() -> void:
	var from := _cam_pos
	var end := PLAZA + Vector3(0, 3.0, -11.0)
	var north := PLAZA + Vector3(0, 30, -120)
	var dir := Vector3(north.x - from.x, 0, north.z - from.z).normalized()
	var far := Vector2(north.x - from.x, north.z - from.z).length()
	var back := Vector3(from.x - _cam_look.x, 0, from.z - _cam_look.z).normalized()
	var rise := from + Vector3(0, 18.0 + far * 0.02, 0) + back * 14.0 + dir * far * 0.06  # up and back, still on the athlete
	var mid := from.lerp(north, 0.5)
	mid.y = maxf(from.y, 20.0) + clampf(far * 0.12, 30.0, 160.0)
	# the last leg curves round wide, so the camera is already heading south when it comes in from the north
	var side := 1.0 if from.x > PLAZA.x else -1.0
	var swing := PLAZA + Vector3(side * 90.0, 42.0, -210.0)
	# craning up and away while still on the athlete, then turning to the plaza high over the valley
	var pts: Array[Vector3] = [from, rise, mid]
	var looks: Array[Vector3] = [_cam_look, _cam_look + Vector3(0, 4, 0), _cam_look.lerp(PLAZA + Vector3(0, 0, 120), 0.6) + Vector3(0, 25, 0)]
	var paces: Array[float] = [0.3, 0.45, 0.85]
	if absf(mid.x - PLAZA.x) > 150.0:  # from far east or west: round by the north first
		pts.append(swing)
		looks.append(PLAZA + Vector3(0, 12, 0))
		paces.append(0.6)
	pts.append_array([north, PLAZA + Vector3(0, 21, -58), end])
	looks.append_array([PLAZA + Vector3(0, 4, 30), PLAZA + Vector3(0, 3, 6), PLAZA + Vector3(0, 2.2, 1.5)])
	paces.append_array([0.45, 0.36, 0.24])
	var clear := func(p: Vector3) -> float:
		var r := Vector2(p.x - PLAZA.x, p.z - PLAZA.z).length()
		return valley.height(p.x, p.z) + 34.0 * smoothstep(40.0, 120.0, r)
	_start_flight("plaza", pts, looks, game.stage_seconds(S.STANDINGS), clear, paces, 0.2)


func _update_shafts() -> void:
	if _shafts == null:
		return
	var fwd := -_camera.global_basis.z
	var k := smoothstep(0.35, 0.9, fwd.dot(_to_sun))
	var sp := _camera.global_position + _to_sun * 3000.0
	if k <= 0.0 or _camera.is_position_behind(sp):
		_shafts.set_shader_parameter("strength", 0.0)
		return
	var vp := get_viewport().get_visible_rect().size
	_shafts.set_shader_parameter("sun_uv", _camera.unproject_position(sp) / vp)
	_shafts.set_shader_parameter("strength", k * 1.6)


# ------------------------------------------------------------------ the events

## A value the event moves once a tick, drawn between its last two ticks, so it moves evenly at any frame rate.
func _between(key: String, value: Variant) -> Variant:
	var e: Array = _ticked.get(key, [])
	if e.is_empty() or game.ticks < e[2] or game.ticks - e[2] > 6:
		_ticked[key] = [value, value, game.ticks]
		return value
	if game.ticks != e[2]:
		var k: int = game.ticks - e[2]
		e[0] = e[1] if k == 1 else lerp(e[1], value, float(k - 1) / k)
		e[1] = value
		e[2] = game.ticks
	return lerp(e[0], e[1], game.tick_alpha())


func _update_skating(s: SpeedSkating, delta: float) -> void:
	_skater.visible = true
	_rival.visible = true
	# past the finish the skater glides on, slowing
	if game.stage == S.RESULT:
		if _glide_v < 0.0:
			_glide_v = s.speed  # (the glide starts next frame: this one still draws the last tick)
		else:
			_glide_v = maxf(0.0, _glide_v - delta * (1.2 + _glide_v * 0.12))
			_glide += _glide_v * delta
	else:
		_glide = 0.0
		_glide_v = -1.0
	var sp: float = _between("skater", s.pos) + _glide
	var rp: float = _between("rival", s.rival_pos) + _glide * s.rival_speed / maxf(s.speed, 1.0)
	var me := oval_point(sp, LANES[0])
	var them := oval_point(rp, LANES[1])
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
	# the TV camera: beside the track, level with the skater, a little ahead (the intro flight ends right here)
	var pl := _skate_cam(sp)
	_set_camera(pl[0], pl[1], delta)


## The jump, shot like television by one camera that never cuts (FrostpeakJumpCam): settled behind the jumper on
## the bar, riding down the in-run behind them, swinging round to a three-quarter side view at the take-off,
## tracking the flight and the landing, and coming round in front as they stop in the arena. Every frame is
## recorded for the replay. Returns the lens (field of view).
func _update_jump(j: SkiJump, delta: float) -> float:
	_jumper.visible = true
	var lp := Vector3.ZERO  # the jumper, in the hill's frame
	var lb := Basis.IDENTITY
	var hb := hill.xf.basis
	var c := _jcam
	match j.stage:
		SkiJump.Stage.INRUN:
			lp = _between("jumper", hill.inrun_at(j.along, 0.0, 0.08))
			lb = Basis(Vector3.BACK, -SkiHill.inrun_angle(j.along)) * Basis(Vector3.UP, PI * 0.5)
			_anim(_jumper, "tuck" if j.tuck > 0.5 else "idle")
			if j.phase == WinterEvent.Phase.READY:
				# settling in behind the jumper as the countdown runs
				c.aim("az", 0.32, 0.9)  # a little to the side: the gate's board hides less of the jumper
				c.aim("el", 0.46, 0.9)  # high enough to see over the gate's back board
				c.aim("dist", 8.0, 0.9)
				c.aim("ahead", 9.0, 0.8)
				c.aim("lift", 0.6, 0.9)
				c.aim("fov", 52.0, 1.0)
			else:
				c.aim("az", 0.0, 1.6)
				c.aim("el", 0.27, 1.4)
				c.aim("dist", 7.0 + j.speed * 0.04, 1.5)
				c.aim("pitch", SkiHill.inrun_angle(j.along + 4.0), 3.0)
				c.aim("ahead", 11.0, 1.2)
				c.aim("lift", 0.4, 1.5)
				c.aim("fov", 52.0 + j.speed * 0.18, 1.2)
		SkiJump.Stage.FLIGHT:
			_rec.mark("takeoff")
			lp = Vector3(j.fly.x, j.fly.y + lerpf(0.08, 0.3, smoothstep(0.0, 10.0, j.fly.x)), 0)
			lp.y = maxf(lp.y, SkiHill.ground_y(j.fly.x) + 0.45)  # the hill mesh must never swallow the skis
			lp = _between("jumper", lp)
			lb = Basis(Vector3.BACK, -0.15 - j.angle * 0.8) * Basis(Vector3.UP, PI * 0.5)
			_anim(_jumper, "flight")
			var out := clampf(j.fly.x / 110.0, 0.0, 1.0)
			c.aim("az", 1.02, 1.5)
			c.aim("el", 0.16, 1.4)
			c.aim("dist", 9.0 + out * 6.0, 1.2)
			c.aim("pitch", atan2(-j.vel.y, j.vel.x), 2.5)
			c.aim("ahead", 1.5, 1.2)  # a little room ahead of the jumper, no more
			c.aim("lift", 0.2, 1.5)
			c.aim("fov", 46.0, 1.0)
		SkiJump.Stage.LANDED:
			_rec.mark("landed")
			if _slide_v < 0.0:  # touchdown: slide on from where the jumper was drawn, sinking onto the snow
				_slide_v = 26.0
				_landed_x = _last_lp.x
				_land_drop = maxf(0.0, _last_lp.y - SkiHill.ground_y(_last_lp.x) - 0.05)
			_land_drop = move_toward(_land_drop, 0.0, delta * 3.0)
			var x0 := _landed_x + _slide
			_slide_v = maxf(0.0, _slide_v - delta * (1.0 if x0 < 175.0 else 7.5))
			_slide += _slide_v * delta
			var x := minf(_landed_x + _slide, FrostpeakHill.OUTRUN_STOP)
			var slope := atan2(SkiHill.ground_y(x) - SkiHill.ground_y(x + 1.0), 1.0)
			lp = Vector3(x, SkiHill.ground_y(x) + 0.05 + _land_drop, 0)
			var stopped := _slide_v < 0.5
			_stop_turn = move_toward(_stop_turn, 0.9 if stopped else 0.0, delta * 2.5)
			lb = Basis(Vector3.BACK, -slope) * Basis(Vector3.UP, PI * 0.5 - _stop_turn)
			_anim(_jumper, "fall" if j.fell else ("telemark" if _slide < 25.0 else ("celebrate" if stopped else "idle")))
			var slow := clampf(_slide_v / 26.0, 0.0, 1.0)
			c.aim("az", lerpf(2.2, 1.42, slow), 0.7)
			c.aim("el", lerpf(0.17, 0.2, slow), 0.8)
			c.aim("dist", lerpf(10.5, 13.0, slow), 0.8)
			c.aim("pitch", slope, 2.5)
			c.aim("ahead", 6.0 * slow, 0.8)
			c.aim("lift", 1.0, 0.8)
			c.aim("fov", 42.0, 0.8)
	if game.stage == S.RESULT:  # the result card goes across the middle: frame the jumper low in the picture
		c.aim("lift", 1.0 + c.value["dist"] * tan(deg_to_rad(c.value["fov"] * 0.28)), 1.2)
	if j.phase == WinterEvent.Phase.READY:
		_stop_turn = 0.0
	_last_lp = lp
	c.step(delta)
	var pl := c.pose(lp)
	_set_camera(hill.world(pl[0]), hill.world(pl[1]), delta)
	_jumper.transform = Transform3D(hb * lb, hill.world(lp))
	if j.phase != WinterEvent.Phase.READY:
		var ap: AnimationPlayer = _jumper.find_child("AnimationPlayer", true, false)
		_rec.record(delta, _jumper.transform, StringName(ap.current_animation), ap.current_animation_position)
	return c.value["fov"]


# ------------------------------------------------------------------ the replay

## The replay's shots, each [the cut, the end] in live time with a slow-motion window; built once the attempt is
## recorded, then timed by stepping through it, so the game knows how long the replay runs.
func _start_replay() -> void:
	_rp_active = false
	if _rec.empty():
		game.replay_seconds = 0.5
		return
	var tk: float = _rec.marks.get("takeoff", _rec.length() * 0.4)
	var ld: float = _rec.marks.get("landed", tk + 3.0)
	var end := _rec.length()
	_rp_shots = [{"cam": "takeoff", "from": maxf(0.0, tk - 1.1), "to": tk + 0.6, "slow": Vector2(tk - 0.2, tk + 0.35), "rate": 0.33}]
	if ld - 0.8 - (tk + 0.6) > 0.8:
		_rp_shots.append({"cam": "flight", "from": tk + 0.6, "to": ld - 0.8, "slow": Vector2(-9, -9), "rate": 1.0})
	_rp_shots.append({"cam": "impact", "from": ld - 0.8 if _rp_shots.size() > 1 else tk + 0.6, "to": minf(ld + 0.9, end),
		"slow": Vector2(ld - 0.4, ld + 0.3), "rate": 0.28})
	# time each shot: the cut comes under a wipe (WIPE_COVER after it starts)
	var real := WIPE_COVER
	for sh in _rp_shots:
		sh["start"] = real
		var t: float = sh["from"]
		while t < sh["to"]:
			t += (1.0 / 60.0) * _rp_rate(sh, t)
			real += 1.0 / 60.0
		sh["end"] = real
	game.replay_seconds = real + WIPE_COVER + 0.05
	_rp_i = -1
	_rp_t = 0.0
	_rp_wiped = 0
	_rp_active = true
	_rp_live = [_cam_pos, _cam_look, _fov, _jumper.transform]


## Replay speed at live time t: full speed, easing into slow motion round the moment that matters and back out.
func _rp_rate(sh: Dictionary, t: float) -> float:
	var w: Vector2 = sh["slow"]
	var k := smoothstep(w.x - 0.25, w.x, t) * (1.0 - smoothstep(w.y, w.y + 0.3, t))
	return lerpf(1.0, sh["rate"], k)


func rp_rate() -> float:
	if not _rp_active or _rp_i < 0 or _rp_i >= _rp_shots.size():
		return 1.0
	return _rp_rate(_rp_shots[_rp_i], _rp_t)


## What the replay shows now: "" before the first cut and after the last, else the shot's name.
func rp_shot() -> String:
	if game.stage != S.REPLAY or not _rp_active or _rp_i < 0 or _rp_i >= _rp_shots.size():
		return ""
	return _rp_shots[_rp_i]["cam"]


## How big a biathlon target's hit zone looks on the screen (radius, pixels), for the sight's ring.
func target_px() -> float:
	var p := biathlon.plate()
	if _camera.is_position_behind(p):
		return 20.0
	var a := _camera.unproject_position(p)
	var b := _camera.unproject_position(p + _camera.global_basis.x * Biathlon.TARGET_R)
	return clampf(a.distance_to(b), 4.0, 400.0)


## Seconds since the current wipe started (the screen is covered at WIPE_COVER), or -1.
func wipe_time() -> float:
	return _wipe_t


func _update_replay(delta: float) -> float:
	if not _rp_active:
		_hold_camera(delta)
		return _fov
	var rt := _stage_t
	# which shot: the next one starts at its cut
	var want := -1
	for i in _rp_shots.size():
		if rt >= _rp_shots[i]["start"]:
			want = i
	if rt >= _rp_shots[_rp_shots.size() - 1]["end"]:
		want = _rp_shots.size()
	# a wipe leads each cut, covering the screen as it comes
	while _rp_wiped <= _rp_shots.size():
		var cut: float = _rp_shots[_rp_wiped]["start"] if _rp_wiped < _rp_shots.size() else _rp_shots[_rp_wiped - 1]["end"]
		if rt < cut - WIPE_COVER:
			break
		_wipe_t = rt - (cut - WIPE_COVER)
		_rp_wiped += 1
	if want != _rp_i:
		_rp_i = want
		if want < _rp_shots.size():
			_rp_t = _rp_shots[want]["from"]
			_fov_cut = true
			_rp_cut = true
		else:
			_end_replay()
			return _fov
	if _rp_i < 0:  # the live picture holds until the first cut
		_hold_camera(delta)
		return _fov
	if _rp_i >= _rp_shots.size():
		_hold_camera(delta)
		return _fov
	var sh: Dictionary = _rp_shots[_rp_i]
	var before := _rp_t
	if not _rp_cut:
		_rp_t = minf(_rp_t + delta * _rp_rate(sh, _rp_t), _rec.length())
	var rate := _rp_rate(sh, _rp_t)
	# the take-off and the landing are heard again, as slowed as the picture
	for m in [["takeoff", "takeoff", -4.0], ["landed", "land", -1.0]]:
		var at: float = _rec.marks.get(m[0], -1.0)
		if at >= 0.0 and before < at and _rp_t >= at:
			tv_sound.emit(m[1], m[2], clampf(0.35 + rate * 0.65, 0.4, 1.0))
	var xf := _rec.xform_at(_rp_t)
	_jumper.visible = true
	_jumper.transform = xf
	var an: Array = _rec.anim_at(_rp_t)
	var ap: AnimationPlayer = _jumper.find_child("AnimationPlayer", true, false)
	if ap.current_animation != an[0]:
		ap.play(an[0], 0.0 if _rp_cut else 0.2 * rate, 1.0)
		ap.seek(an[1], true)
	elif _rp_cut or absf(ap.current_animation_position - float(an[1])) > 0.12:
		ap.seek(an[1], true)
	ap.speed_scale = rate
	var p := hill.local(xf.origin)  # the jumper in the hill's frame
	var cam := Vector3.ZERO
	var look := p + Vector3(0, 0.6, 0)
	var half := 2.4  # half the height the lens frames round the jumper, metres
	match sh["cam"]:
		"takeoff":  # low beside the knoll, square to the lip: the jumper springs off the table across the picture
			cam = Vector3(10.0, 2.0, 7.0)  # just above the lip's height, clear of the table's walls and the fences
			half = 2.2
		"flight":  # from the other side, a rail camera running level with the jumper
			var tk: float = _rec.marks.get("takeoff", 0.0)
			var ahead := hill.local(_rec.xform_at(minf(_rp_t + 0.15, _rec.length())).origin)
			cam = p + Vector3(-5.0, 3.5, -9.0)  # (inside the fences, which stand some 12-18 m out)
			cam.y = maxf(cam.y, hill.terrain_y(cam.x, cam.z) + 3.0)
			look = p.lerp(ahead, 0.5) + Vector3(0, 0.4, 0)
			half = 3.2 + (_rp_t - tk) * 0.2
		"impact":  # low on the slope below the landing, looking up at the touchdown
			var lx := hill.local(_rec.xform_at(_rec.marks.get("landed", _rp_t)).origin).x
			cam = Vector3(lx + 24.0, 0, 10.5)
			cam.y = hill.terrain_y(cam.x, cam.z) + 1.4
			half = 2.0
	var fov := clampf(rad_to_deg(2.0 * atan(half / maxf(1.0, cam.distance_to(look)))), 8.0, 55.0)
	_set_camera(hill.world(cam), hill.world(look), delta, _rp_cut, 4.0)
	_rp_cut = false
	return fov


## Back to the live picture: the jumper where they stopped, the camera where it was.
func _end_replay() -> void:
	if not _rp_active:
		return
	_rp_active = false
	_rp_i = _rp_shots.size()
	_jumper.transform = _rp_live[3]
	var ap: AnimationPlayer = _jumper.find_child("AnimationPlayer", true, false)
	ap.speed_scale = 1.0
	if not _rec.empty():
		ap.play(_rec.anims[_rec.anims.size() - 1], 0.0)
	_set_camera(_rp_live[0], _rp_live[1], 0.0, true)
	_fov = _rp_live[2]
	if _wipe_t < 0.0 or _wipe_t > 2.0 * WIPE_COVER:
		_wipe_t = WIPE_COVER  # skipped: the wipe's second half uncovers the live picture


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
		b = "HS 134"
	elif game.ev is Biathlon:
		var bi := game.ev as Biathlon
		a = "%s  %s" % [code, Competition.format("biathlon", bi.result if bi.result > 0.0 else bi.time)]
		b = "RANGE" if bi.stage == Biathlon.Stage.RANGE else ("PENALTY" if bi.stage == Biathlon.Stage.PENALTY else "LAP %d / %d" % [bi.lap() + 1, Biathlon.LAPS])
	for i in _boards.size():
		var lb := _boards[i]
		var txt := a if i % 2 == 0 else b
		if lb.text != txt:
			lb.text = txt
