class_name CaveView3D
extends Node3D
## The 3D diorama view of a running cave. The cave is a vertical slice: cell (x, y) sits at (x, -y, 0), blocks
## stand out toward the camera, gravity points down the screen. It only reads the engine; the rules stay in
## CaveEngine. Objects glide between cells using the engine's move list, so motion is smooth at any frame rate.

const E = preload("res://games/glimmerdeep/engine/cave_elements.gd")
const D = preload("res://games/glimmerdeep/engine/cave_directions.gd")
const MODELS := "res://games/glimmerdeep/art/models/"

enum Kind { DIRT, BRICK, STEEL, BOULDER, DIAMOND, FIREFLY, BUTTERFLY, AMOEBA, MAGIC, GATE, PORTAL, HERO, BLAST, OTHER }

@export var game: CaveGame

var _mm: Array[MultiMeshInstance3D] = []
var _counts: Array[int] = []
var _came_from := {}  ## cell index -> previous cell (Vector2) for objects that moved in the last frame
var _camera: Camera3D
var _lamp: OmniLight3D
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _trauma := 0.0
var _time := 0.0
var _hatch_zoom := 1.0
var _fx: CaveEffects
var _backdrop: MeshInstance3D
var _hero_facing := 1.0
var _cells_kind := PackedInt32Array()
var _landed := {}  ## cell index -> time an object landed there (for the squash)


func _ready() -> void:
	_build_environment()
	_build_multimeshes()
	_fx = CaveEffects.new()
	add_child(_fx)
	game.cave_started.connect(_on_cave_started)
	game.frame_done.connect(_on_frame_done)
	if game.engine:
		_on_cave_started(game.engine)


# ---------------------------------------------------------------- setup

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.015, 0.012, 0.02)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.5, 0.52, 0.6)
	env.ambient_light_energy = 0.22
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.1
	env.glow_enabled = true
	env.glow_intensity = 0.9
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 0.9
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	env.ssao_enabled = true
	env.ssao_radius = 0.8
	env.ssao_intensity = 1.6
	env.fog_enabled = true
	env.fog_light_color = Color(0.08, 0.06, 0.1)
	env.fog_density = 0.012
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.0
	env.adjustment_contrast = 1.08
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-38, -28, 0)
	key.light_color = Color(1.0, 0.94, 0.86)
	key.light_energy = 1.0
	key.shadow_enabled = true
	key.directional_shadow_max_distance = 60.0
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-15, 140, 0)
	fill.light_color = Color(0.45, 0.6, 1.0)
	fill.light_energy = 0.35
	add_child(fill)

	_lamp = OmniLight3D.new()
	_lamp.light_color = Color(1.0, 0.8, 0.5)
	_lamp.light_energy = 1.6
	_lamp.omni_range = 7.0
	_lamp.shadow_enabled = true
	add_child(_lamp)

	_camera = Camera3D.new()
	_camera.fov = 42.0
	_camera.current = true
	add_child(_camera)

	_backdrop = MeshInstance3D.new()
	var plane := QuadMesh.new()
	plane.size = Vector2(200, 120)
	_backdrop.mesh = plane
	var bmat := ShaderMaterial.new()
	bmat.shader = load("res://games/glimmerdeep/shaders/backdrop.gdshader")
	_backdrop.material_override = bmat
	add_child(_backdrop)


func _material(kind: int) -> Material:
	match kind:
		Kind.DIRT:
			var m := ShaderMaterial.new()
			m.shader = load("res://games/glimmerdeep/shaders/dirt.gdshader")
			return m
		Kind.DIAMOND:
			var m := ShaderMaterial.new()
			m.shader = load("res://games/glimmerdeep/shaders/gem.gdshader")
			return m
	var s := StandardMaterial3D.new()
	s.vertex_color_use_as_albedo = true
	match kind:
		Kind.BRICK:
			s.albedo_color = Color(0.42, 0.2, 0.14)
			s.roughness = 0.85
		Kind.MAGIC:
			s.albedo_color = Color(0.55, 0.35, 0.75)
			s.emission_enabled = true
			s.emission = Color(0.6, 0.2, 1.0)
			s.emission_energy_multiplier = 0.4
			s.roughness = 0.5
		Kind.STEEL:
			s.albedo_color = Color(0.55, 0.62, 0.72)
			s.metallic = 0.85
			s.roughness = 0.32
		Kind.BOULDER:
			s.albedo_color = Color(0.5, 0.48, 0.46)
			s.roughness = 0.75
		Kind.FIREFLY:
			s.albedo_color = Color(1.0, 0.5, 0.1)
			s.emission_enabled = true
			s.emission = Color(1.0, 0.45, 0.05)
			s.emission_energy_multiplier = 3.0
		Kind.BUTTERFLY:
			s.albedo_color = Color(0.9, 0.3, 1.0)
			s.emission_enabled = true
			s.emission = Color(0.9, 0.25, 1.0)
			s.emission_energy_multiplier = 2.2
			s.cull_mode = BaseMaterial3D.CULL_DISABLED
		Kind.AMOEBA:
			s.albedo_color = Color(0.25, 0.85, 0.3)
			s.emission_enabled = true
			s.emission = Color(0.1, 0.6, 0.15)
			s.emission_energy_multiplier = 0.8
			s.roughness = 0.3
		Kind.GATE:
			s.albedo_color = Color(0.5, 0.48, 0.52)
			s.roughness = 0.8
		Kind.PORTAL:
			s.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			s.albedo_color = Color.WHITE
		Kind.HERO:
			s.albedo_color = Color(1.0, 0.72, 0.15)
			s.roughness = 0.35
			s.metallic = 0.1
			s.emission_enabled = true
			s.emission = Color(1.0, 0.6, 0.1)
			s.emission_energy_multiplier = 0.12
			s.rim_enabled = true
			s.rim = 0.6
		Kind.BLAST:
			s.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			s.albedo_color = Color.WHITE
			s.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_:
			s.albedo_color = Color(0.7, 0.7, 0.7)
	return s


func _mesh(kind: int) -> Mesh:
	match kind:
		Kind.DIRT: return load(MODELS + "dirt.obj")
		Kind.BRICK, Kind.MAGIC: return load(MODELS + "brick.obj")
		Kind.STEEL: return load(MODELS + "steel.obj")
		Kind.BOULDER: return load(MODELS + "boulder.obj")
		Kind.DIAMOND: return load(MODELS + "diamond.obj")
		Kind.FIREFLY: return load(MODELS + "firefly.obj")
		Kind.BUTTERFLY: return load(MODELS + "butterfly.obj")
		Kind.AMOEBA: return load(MODELS + "amoeba.obj")
		Kind.GATE: return load(MODELS + "exit.obj")
		Kind.PORTAL: return load(MODELS + "portal.obj")
		Kind.HERO: return _mesh_from_scene(MODELS + "hero.glb")
		Kind.BLAST:
			var s := SphereMesh.new()
			s.radius = 0.5
			s.height = 1.0
			return s
	var b := BoxMesh.new()
	b.size = Vector3(0.8, 0.8, 0.8)
	return b


static func _mesh_from_scene(path: String) -> Mesh:
	var root := (load(path) as PackedScene).instantiate()
	var found: Mesh = null
	for n in root.find_children("*", "MeshInstance3D", true, false):
		found = (n as MeshInstance3D).mesh
		break
	root.free()
	return found


func _build_multimeshes() -> void:
	for kind in Kind.size():
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = _mesh(kind)
		var inst := MultiMeshInstance3D.new()
		inst.multimesh = mm
		if kind != Kind.HERO:  # the hero keeps the materials made in Blender
			inst.material_override = _material(kind)
		if kind == Kind.PORTAL or kind == Kind.BLAST:
			inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(inst)
		_mm.append(inst)
		_counts.append(0)


static func kind_of(e: int) -> int:
	match e:
		E.DIRT, E.DIRT2, E.DIRT_SLOPED_UP_RIGHT, E.DIRT_SLOPED_UP_LEFT, E.DIRT_SLOPED_DOWN_LEFT, \
				E.DIRT_SLOPED_DOWN_RIGHT, E.DIRT_BALL, E.DIRT_BALL_F, E.DIRT_LOOSE, E.DIRT_LOOSE_F:
			return Kind.DIRT
		E.BRICK, E.BRICK_SLOPED_UP_RIGHT, E.BRICK_SLOPED_UP_LEFT, E.BRICK_SLOPED_DOWN_LEFT, E.BRICK_SLOPED_DOWN_RIGHT, \
				E.BRICK_NON_SLOPED, E.BRICK_EATABLE, E.H_EXPANDING_WALL, E.V_EXPANDING_WALL, E.EXPANDING_WALL, \
				E.FALLING_WALL, E.FALLING_WALL_F:
			return Kind.BRICK
		E.MAGIC_WALL:
			return Kind.MAGIC
		E.STEEL, E.STEEL_SLOPED_UP_RIGHT, E.STEEL_SLOPED_UP_LEFT, E.STEEL_SLOPED_DOWN_LEFT, E.STEEL_SLOPED_DOWN_RIGHT, \
				E.STEEL_EXPLODABLE, E.STEEL_EATABLE, E.H_EXPANDING_STEEL_WALL, E.V_EXPANDING_STEEL_WALL, \
				E.EXPANDING_STEEL_WALL, E.PRE_STEEL_1, E.PRE_STEEL_2, E.PRE_STEEL_3, E.PRE_STEEL_4:
			return Kind.STEEL
		E.STONE, E.STONE_F, E.MEGA_STONE, E.MEGA_STONE_F, E.FLYING_STONE, E.FLYING_STONE_F, E.WAITING_STONE, \
				E.CHASING_STONE, E.NUT, E.NUT_F:
			return Kind.BOULDER
		E.DIAMOND, E.DIAMOND_F, E.FLYING_DIAMOND, E.FLYING_DIAMOND_F:
			return Kind.DIAMOND
		E.AMOEBA, E.AMOEBA_2:
			return Kind.AMOEBA
		E.PRE_OUTBOX, E.OUTBOX, E.PRE_INVIS_OUTBOX, E.INVIS_OUTBOX, E.INBOX:
			return Kind.GATE
		E.SPACE, E.LAVA:
			return -1
	if (E.FLAGS[e] & E.P_PLAYER) != 0 or (e >= E.PRE_PL_1 and e <= E.PRE_PL_3):
		return Kind.HERO
	if (e >= E.FIREFLY_1 and e <= E.FIREFLY_4) or (e >= E.ALT_FIREFLY_1 and e <= E.ALT_FIREFLY_4):
		return Kind.FIREFLY
	if (e >= E.BUTTER_1 and e <= E.BUTTER_4) or (e >= E.ALT_BUTTER_1 and e <= E.ALT_BUTTER_4):
		return Kind.BUTTERFLY
	if (e >= E.EXPLODE_1 and e <= E.EXPLODE_5) or (e >= E.PRE_DIA_1 and e <= E.PRE_DIA_5) \
			or (e >= E.NITRO_EXPL_1 and e <= E.NITRO_EXPL_4) or (e >= E.PRE_STONE_1 and e <= E.PRE_STONE_4):
		return Kind.BLAST
	return Kind.OTHER


# ---------------------------------------------------------------- game events

func _on_cave_started(engine: CaveEngine) -> void:
	for i in _mm.size():
		_mm[i].multimesh.instance_count = engine.w * engine.h
	_came_from.clear()
	_backdrop.position = Vector3(engine.w * 0.5, -engine.h * 0.5, -0.55)
	_hatch_zoom = 1.0
	var mid := Vector3(engine.w * 0.5 - 0.5, -engine.h * 0.5 + 0.5, 0.0)
	_cam_look = mid
	_cam_pos = mid + Vector3(0, -4, maxf(engine.w, engine.h * 1.8) * 1.05)
	_camera.position = _cam_pos
	_camera.look_at(_cam_look)


func _on_frame_done(engine: CaveEngine, _frame_ms: float) -> void:
	_came_from.clear()
	for m in engine.moves:
		var to_x: int = (m.x + D.DX[m.z] + engine.w) % engine.w
		var to_y: int = (m.y + D.DY[m.z] + engine.h) % engine.h
		_came_from[to_y * engine.w + to_x] = Vector2(m.x, m.y)
	if engine.last_horizontal_direction == D.LEFT:
		_hero_facing = -1.0
	elif engine.last_horizontal_direction == D.RIGHT:
		_hero_facing = 1.0
	for ev in engine.events:
		_fx.on_event(ev, engine)
		if ev[0] == "effect" and ev[4]:
			_landed[int(ev[3]) * engine.w + int(ev[2])] = _time
		if ev[0] == "explosion" and Settings.camera_shake:
			_trauma = minf(1.0, _trauma + 0.55)


# ---------------------------------------------------------------- drawing

func _process(delta: float) -> void:
	var engine := game.engine
	if engine == null:
		return
	_time += delta
	var t := game.frame_progress
	for i in _counts.size():
		_counts[i] = 0
	var hero_pos := Vector3(engine.player_x, -engine.player_y, 0)
	var w := engine.w
	var gate_open := engine.gate_open
	for y in engine.h:
		for x in w:
			var i := y * w + x
			var e: int = E.nonscanned_pair(engine.map[i])
			var kind := kind_of(e)
			if kind < 0:
				continue
			var pos := Vector3(x, -y, 0)
			var from = _came_from.get(i)
			if from != null:
				pos = Vector3(from.x, -from.y, 0).lerp(pos, t)
			var squash := 0.0
			var landed = _landed.get(i)
			if landed != null:
				var age: float = _time - landed
				if age < 0.35:
					squash = sin(age / 0.35 * PI) * 0.22 * (1.0 - age / 0.35)
				else:
					_landed.erase(i)
			var basis := Basis()
			var color := Color.WHITE
			match kind:
				Kind.BOULDER:
					var roll := 0.0
					if from != null:
						roll = (from.x - x) * t * PI * 0.5
					basis = Basis.from_scale(Vector3(1.0 + squash, 1.0 - squash, 1.0 + squash)) \
						* Basis(Vector3.BACK, roll) * Basis(Vector3.UP, float(i % 7))
					pos.y -= squash * 0.3
					var tint := 0.85 + 0.15 * sin(i * 1.7)
					color = Color(tint, tint * 0.97, tint * 0.93)
				Kind.DIAMOND:
					basis = Basis.from_scale(Vector3(1.0 + squash, 1.0 - squash, 1.0 + squash)) \
						* Basis(Vector3.UP, _time * 1.6 + i) * Basis(Vector3.RIGHT, 0.25)
				Kind.DIRT:
					basis = Basis(Vector3.UP, float((i * 37) % 4) * PI * 0.5) * Basis.from_scale(Vector3(0.96, 0.96, 0.9))
				Kind.FIREFLY:
					basis = Basis(Vector3.BACK, _time * 5.0 + i)
					pos.z += 0.1 * sin(_time * 6.0 + i)
				Kind.BUTTERFLY:
					var flap := 0.35 + 0.65 * absf(sin(_time * 9.0 + i))
					basis = Basis.from_scale(Vector3(flap, 1, 1)) * Basis(Vector3.RIGHT, -0.3)
				Kind.AMOEBA:
					var wob := 1.0 + 0.06 * sin(_time * 4.0 + i * 1.3)
					basis = Basis.from_scale(Vector3(wob, 2.0 - wob, wob))
				Kind.HERO:
					if e >= E.PRE_PL_1 and e <= E.PRE_PL_3:
						var grow := float(e - E.PRE_PL_1 + 1) / 4.0
						basis = Basis.from_scale(Vector3.ONE * grow)
					else:
						var bob := absf(sin(_time * 12.0)) * 0.06 if from != null else 0.0
						basis = Basis(Vector3.UP, (0.35 if _hero_facing > 0 else -0.35)) \
							* Basis.from_scale(Vector3(1.35, 1.35 - bob, 1.35))
						pos.y += bob
						hero_pos = pos
				Kind.GATE:
					_add(Kind.PORTAL, Transform3D(Basis(), pos + Vector3(0, 0, 0.05)),
						_portal_color(e, gate_open))
				Kind.BLAST:
					var stage := _blast_stage(e)
					basis = Basis.from_scale(Vector3.ONE * (0.6 + stage * 0.35))
					color = Color(1.0, 0.75 - stage * 0.12, 0.3, 1.0 - stage * 0.18) * 3.0
					color.a = 1.0 - stage * 0.18
					if e >= E.PRE_DIA_1 and e <= E.PRE_DIA_5:
						color = Color(0.4, 1.6, 2.2, 1.0 - stage * 0.15)
			_add(kind, Transform3D(basis, pos), color)
	for kind in _mm.size():
		_mm[kind].multimesh.visible_instance_count = _counts[kind]
	_update_camera(engine, hero_pos, delta)
	_lamp.position = hero_pos + Vector3(0.0, 0.6, 1.4)
	_lamp.visible = engine.player_state == CaveRendered.PlayerState.LIVING


func _add(kind: int, xf: Transform3D, color: Color) -> void:
	var mm := _mm[kind].multimesh
	var n := _counts[kind]
	if n >= mm.instance_count:
		return
	mm.set_instance_transform(n, xf)
	mm.set_instance_color(n, color)
	_counts[kind] = n + 1


func _portal_color(e: int, gate_open: bool) -> Color:
	var pulse := 0.5 + 0.5 * sin(_time * 5.0)
	if e == E.INBOX:
		return Color(1.4, 1.1, 0.4) * (0.6 + 0.8 * pulse)
	if e == E.OUTBOX or e == E.INVIS_OUTBOX or (gate_open and e != E.PRE_INVIS_OUTBOX):
		return Color(0.4, 2.4, 0.9) * (0.7 + 0.8 * pulse)
	return Color(0.08, 0.1, 0.12)


static func _blast_stage(e: int) -> int:
	if e >= E.EXPLODE_1 and e <= E.EXPLODE_5: return e - E.EXPLODE_1
	if e >= E.PRE_DIA_1 and e <= E.PRE_DIA_5: return e - E.PRE_DIA_1
	if e >= E.NITRO_EXPL_1 and e <= E.NITRO_EXPL_4: return e - E.NITRO_EXPL_1
	return e - E.PRE_STONE_1


func _update_camera(engine: CaveEngine, hero_pos: Vector3, delta: float) -> void:
	var visible_h := 13.0
	var dist := visible_h * 0.5 / tan(deg_to_rad(_camera.fov * 0.5))
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_w := visible_h * 0.5 * aspect
	var target := hero_pos
	target.x = clampf(target.x, half_w - 1.0, maxf(half_w - 1.0, engine.w - half_w))
	target.y = clampf(target.y, -engine.h + visible_h * 0.5 - 0.5, maxf(-engine.h + visible_h * 0.5, -visible_h * 0.5 + 2.2))
	if engine.hatched:
		_hatch_zoom = maxf(0.0, _hatch_zoom - delta * 1.2)
	var z := _hatch_zoom * _hatch_zoom
	var wide := Vector3(engine.w * 0.5 - 0.5, -engine.h * 0.5 + 0.5, 0.0)
	var look := target.lerp(wide, z)
	var want := look + Vector3(0.0, 4.5 + 2.0 * z, dist + z * dist * 1.1)
	var k := 1.0 - exp(-delta * 4.0)
	_cam_pos = _cam_pos.lerp(want, k)
	_cam_look = _cam_look.lerp(look, k)
	_trauma = maxf(0.0, _trauma - delta * 1.6)
	var shake := _trauma * _trauma * 0.35
	var jitter := Vector3(sin(_time * 53.0), sin(_time * 47.0 + 1.3), 0.0) * shake
	_camera.position = _cam_pos + jitter
	_camera.look_at(_cam_look + jitter * 0.5)
