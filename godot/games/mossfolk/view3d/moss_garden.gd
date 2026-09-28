class_name MossGarden
extends Node3D
## Mossfolk's living dressing: the glowing grotto seen through the cave's arches (a bioluminescent sky, layers of
## giant mushroom silhouettes, shafts of light, drifting mist and glowing orbs), giant mushrooms standing in the
## haze behind the slab, and the mushrooms on the ledges: glossy, speckled, breathing, bouncing when a mossling
## passes or lands near them, puffing glowing spores. Each level has its own palette (PALETTES, by theme).

const PX := 0.1
const SHROOM := "res://games/mossfolk/shaders/shroom.gdshader"
## per theme: sky (top, mid, low), glows (a, b), mushroom caps
const PALETTES := [
	{"top": Color(0.01, 0.02, 0.08), "mid": Color(0.04, 0.2, 0.32), "low": Color(0.12, 0.5, 0.55),
		"a": Color(0.25, 1.0, 0.85), "b": Color(0.7, 0.4, 1.0),
		"caps": [Color(0.5, 0.2, 0.9), Color(0.1, 0.55, 0.7), Color(0.85, 0.2, 0.65)]},
	{"top": Color(0.07, 0.02, 0.06), "mid": Color(0.32, 0.1, 0.14), "low": Color(0.8, 0.4, 0.22),
		"a": Color(1.0, 0.72, 0.28), "b": Color(1.0, 0.32, 0.5),
		"caps": [Color(0.9, 0.18, 0.12), Color(0.98, 0.5, 0.08), Color(0.85, 0.22, 0.5)]},
	{"top": Color(0.02, 0.01, 0.08), "mid": Color(0.16, 0.07, 0.38), "low": Color(0.42, 0.2, 0.7),
		"a": Color(0.55, 0.5, 1.0), "b": Color(1.0, 0.3, 0.8),
		"caps": [Color(0.8, 0.12, 0.62), Color(0.22, 0.3, 0.95), Color(0.55, 0.2, 0.95)]},
	{"top": Color(0.01, 0.05, 0.05), "mid": Color(0.04, 0.2, 0.22), "low": Color(0.22, 0.5, 0.4),
		"a": Color(0.7, 1.0, 0.35), "b": Color(0.3, 0.9, 1.0),
		"caps": [Color(0.75, 0.82, 0.12), Color(0.1, 0.62, 0.55), Color(0.98, 0.55, 0.12)]},
	{"top": Color(0.06, 0.01, 0.03), "mid": Color(0.38, 0.06, 0.1), "low": Color(0.95, 0.35, 0.12),
		"a": Color(1.0, 0.5, 0.18), "b": Color(1.0, 0.3, 0.7),
		"caps": [Color(0.85, 0.08, 0.15), Color(1.0, 0.45, 0.05), Color(0.5, 0.15, 0.8)]},
]

var fx: Bursts
var pal: Dictionary
var _shrooms: Array = []     ## {node, meshes, base, s, v, excite, cool, x, y, top, phase, big, spores, next_hic}
var _giants: Array = []      ## [node, base rotation z, phase]
var _mats := {}
var _rng := RandomNumberGenerator.new()
var _time := 0.0
var _lights := 0


## Everything far behind the slab. `lv_w`, `lv_h` in level pixels; the view's centre is about the level's middle.
func build_backdrop(lv_w: int, lv_h: int, theme: int, seed: int) -> void:
	pal = PALETTES[theme % PALETTES.size()]
	_rng.seed = seed
	var w := lv_w * PX
	var h := lv_h * PX
	var cx := w * 0.5
	var cy := h * 0.5
	# how much of the world a layer at depth d (behind the level's plane) must cover: the view widens with depth
	var dist := 46.0
	var vis := func(d: float) -> float: return (dist + d) / dist
	var sky := _quad(Vector2((w + 70.0) * vis.call(36.0), 34.0 * vis.call(36.0) + 20.0), "moss_sky")
	sky.position = Vector3(cx, cy - 36.0 * 0.22, -36.0)
	var sm: ShaderMaterial = sky.material_override
	sm.set_shader_parameter("top", pal["top"])
	sm.set_shader_parameter("mid", pal["mid"])
	sm.set_shader_parameter("low", pal["low"])
	sm.set_shader_parameter("glow_a", pal["a"])
	sm.set_shader_parameter("glow_b", pal["b"])
	sm.set_shader_parameter("extent", (sky.mesh as QuadMesh).size)
	sm.set_shader_parameter("horizon", 0.36)
	sm.set_shader_parameter("energy", 0.75)
	sm.set_shader_parameter("seed", float(seed % 97))
	# two layers of the fungal forest, far and near
	var layers := [[26.0, 0.55, 13.0, 1.0], [15.0, 0.2, 8.0, 1.3]]
	for li in layers.size():
		var d: float = layers[li][0]
		var k: float = vis.call(d)
		var span := Vector2((w + 70.0) * k, 30.0 * k)
		var q := _quad(span, "moss_forest")
		q.position = Vector3(cx, cy - d * 0.22 - span.y * 0.12, -d)
		var m: ShaderMaterial = q.material_override
		m.set_shader_parameter("shade", pal["top"].lerp(Color.BLACK, 0.3))
		m.set_shader_parameter("haze", pal["mid"].lerp(pal["low"], 0.4))
		m.set_shader_parameter("haze_amount", layers[li][1])
		m.set_shader_parameter("glow_a", pal["a"])
		m.set_shader_parameter("glow_b", pal["b"])
		m.set_shader_parameter("extent", span)
		m.set_shader_parameter("cell_w", layers[li][2] * k * 0.6)
		m.set_shader_parameter("ground", span.y * 0.22)
		m.set_shader_parameter("height", Vector2(0.2, 0.5) * span.y)
		m.set_shader_parameter("radius", Vector2(0.06, 0.13) * span.y)
		m.set_shader_parameter("energy", layers[li][3])
		m.set_shader_parameter("seed", float(li * 17 + seed % 31))
	# shafts of light from cracks high up, slanting down behind the slab
	for i in maxi(3, int(w / 16.0)):
		var r := _quad(Vector2(_rng.randf_range(2.0, 4.5), h * 1.6), "moss_ray")
		r.position = Vector3(_rng.randf_range(0.0, w), h * 0.75, _rng.randf_range(-8.5, -4.0))
		r.rotation.z = _rng.randf_range(-0.35, -0.1)
		var rm: ShaderMaterial = r.material_override
		rm.set_shader_parameter("col", (pal["a"] as Color).lerp(Color(1.0, 0.95, 0.85), 0.4))
		rm.set_shader_parameter("energy", _rng.randf_range(0.18, 0.32))
		rm.set_shader_parameter("seed", float(i) * 3.7)
	# mist: a bank low behind the slab and a thin veil drifting in front of the far forest
	for m in [[-3.6, 0.55, 0.12], [-11.0, 0.45, 0.07]]:
		var z: float = m[0]
		var mq := _quad(Vector2((w + 50.0) * vis.call(-z), 7.0), "moss_mist")
		mq.position = Vector3(cx, 2.0 + (0.0 if z > -5.0 else cy * 0.3), z)
		var mm: ShaderMaterial = mq.material_override
		mm.set_shader_parameter("col", (pal["low"] as Color).lerp(pal["a"], 0.3))
		mm.set_shader_parameter("density", m[1])
		mm.set_shader_parameter("speed", m[2])
		mm.set_shader_parameter("extent", (mq.mesh as QuadMesh).size)
		mm.set_shader_parameter("seed", z)


## Giant mushrooms standing in the haze behind the slab, their stems rising from below the view.
func add_giants(lv_w: int, lv_h: int, scene: PackedScene) -> void:
	var w := lv_w * PX
	var x := _rng.randf_range(1.0, 5.0)
	while x < w - 1.0:
		var n := scene.instantiate() as Node3D
		var s := _rng.randf_range(4.0, 6.5)
		n.scale = Vector3.ONE * s
		n.position = Vector3(x, lv_h * PX * _rng.randf_range(0.0, 0.35) - 2.0, _rng.randf_range(-8.6, -6.4))
		n.rotation = Vector3(0.0, _rng.randf() * TAU, _rng.randf_range(-0.12, 0.12))
		add_child(n)
		_dress(n, _rng.randi(), 0.45)
		_giants.append([n, n.rotation.z, _rng.randf() * TAU])
		x += _rng.randf_range(7.0, 13.0)


## Makes a ledge mushroom glossy and alive. (x, y) its foot in level pixels; `big` for the large model.
func add_shroom(n: Node3D, x: int, y: int, big: bool, stage: Node3D) -> void:
	var meshes := _dress(n, _rng.randi(), 1.0)
	var s: float = n.scale.x
	var top := (1.15 if big else 0.45) * s
	var sp := _spores(stage, n.position + Vector3(0, top, 0), (0.45 if big else 0.2) * s, 10 if big else 5)
	# the bigger ones light the ledge round them (a few only: lights cost)
	var light: OmniLight3D = null
	if big and _lights < 8:
		_lights += 1
		light = OmniLight3D.new()
		light.light_color = pal["a"]
		light.light_energy = 0.7
		light.omni_range = 1.6 * s
		light.omni_attenuation = 1.6
		light.light_specular = 0.3
		light.light_volumetric_fog_energy = 0.5
		light.position = n.position + Vector3(0, top * 0.8, 0.5)
		stage.add_child(light)
	_shrooms.append({"node": n, "meshes": meshes, "base": s, "s": 0.0, "v": 0.0, "excite": 0.0, "cool": 0.0,
		"x": x, "y": y, "top": top, "phase": _rng.randf(), "big": big, "spores": sp, "light": light,
		"hic": _rng.randf_range(2.0, 12.0), "kick": -1.0, "kick_s": 0.0})


## Replaces a mushroom model's cap and glowing parts with the shiny shader, coloured from the palette.
func _dress(n: Node, pick: int, energy: float) -> Array:
	var caps: Array = pal["caps"]
	var ci := posmod(pick, caps.size())
	var glow: Color = pal["a"] if posmod(pick >> 3, 3) != 0 else pal["b"]
	var key := "%d|%s|%s" % [ci, glow, energy]
	if not _mats.has(key):
		var cap := ShaderMaterial.new()
		cap.shader = load(SHROOM)
		cap.set_shader_parameter("cap_col", caps[ci])
		cap.set_shader_parameter("glow_col", glow)
		cap.set_shader_parameter("speck_col", glow.lerp(Color.WHITE, 0.6))
		cap.set_shader_parameter("glow_energy", energy)
		var gl := cap.duplicate() as ShaderMaterial
		gl.set_shader_parameter("part", 1)
		_mats[key] = [cap, gl]
	var out := []
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for i in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(i)
			var nm := mat.resource_name if mat else ""
			if nm.contains("cap"):
				m.set_surface_override_material(i, _mats[key][0])
			elif nm.contains("glow"):
				m.set_surface_override_material(i, _mats[key][1])
			elif nm.contains("stem") and energy < 1.0:
				m.set_surface_override_material(i, _stem_mat())
		m.set_instance_shader_parameter("phase", _rng.randf())
		out.append(m)
	return out


## The giants' stems: dusky, tinted by the grotto, so the caps carry the light.
func _stem_mat() -> StandardMaterial3D:
	if not _mats.has("stem"):
		var m := StandardMaterial3D.new()
		m.albedo_color = (pal["mid"] as Color).lerp(Color(0.5, 0.5, 0.5), 0.3)
		m.roughness = 0.75
		m.rim_enabled = true
		m.rim = 0.6
		m.rim_tint = 0.8
		m.emission_enabled = true
		m.emission = (pal["a"] as Color) * 0.08
		_mats["stem"] = m
	return _mats["stem"]


func _spores(parent: Node3D, at: Vector3, r: float, amount: int) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = amount
	p.lifetime = 4.0
	p.preprocess = 4.0
	p.fixed_fps = 30
	p.use_fixed_seed = true
	p.local_coords = false
	p.position = at
	p.visibility_aabb = AABB(Vector3(-2, -1, -2), Vector3(4, 5, 4))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = r
	pm.gravity = Vector3(0, 0.12, 0)
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 60.0
	pm.initial_velocity_min = 0.05
	pm.initial_velocity_max = 0.2
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.4
	pm.turbulence_noise_scale = 2.0
	pm.scale_min = 0.6
	pm.scale_max = 1.4
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.25, 0.7, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 0.6), Color(1, 1, 1, 0)])
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.07, 0.07)
	q.material = Fx.material("glow", (pal["a"] as Color).lerp(Color.WHITE, 0.3) * 1.6)
	p.draw_pass_1 = q
	parent.add_child(p)
	return p


func _quad(size: Vector2, shader: String) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = size
	mi.mesh = q
	var m := ShaderMaterial.new()
	m.shader = load("res://games/mossfolk/shaders/%s.gdshader" % shader)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


## A bump near level pixel (x, y): mushrooms within `radius` pixels bounce, nearer ones harder, after `wave`
## seconds per 100 pixels (a ripple).
func bump(x: float, y: float, strength: float, radius := 40.0, wave := 0.0) -> void:
	for m in _shrooms:
		var d := Vector2(m["x"] - x, (m["y"] - y) * 1.5).length()
		if d > radius:
			continue
		var k := strength * (1.0 - d / radius * 0.6)
		if wave > 0.0:
			m["kick"] = d / 100.0 * wave
			m["kick_s"] = k
		else:
			_kick(m, k)


func _kick(m: Dictionary, k: float) -> void:
	m["v"] += 3.2 * k
	m["excite"] = maxf(m["excite"], minf(1.0, k))
	m["cool"] = 1.0
	var n: Node3D = m["node"]
	if fx and n.visible and k > 0.25:
		var at: Vector3 = n.position + Vector3(0, m["top"], 0.1)
		fx.burst(at, (pal["a"] as Color).lerp(Color.WHITE, 0.25), int(6 + 10 * k * (1.5 if m["big"] else 0.7)),
			0.6 + 0.6 * k, 1.4, 0.07 if m["big"] else 0.05, 1.0, 0.25, 1.0, "glow")


## Each frame: springs, idle breathing, the odd hiccup, and mosslings walking past. `folk` is the engine's list.
func update(delta: float, folk: Array) -> void:
	_time += delta
	for g in _giants:
		(g[0] as Node3D).rotation.z = g[1] + sin(_time * 0.35 + g[2]) * 0.02
	for m in _shrooms:
		var n: Node3D = m["node"]
		if not n.visible or n.has_meta("sinking"):
			if m["spores"].emitting:
				m["spores"].emitting = false
				if m["light"]:
					m["light"].visible = false
			continue
		m["cool"] = maxf(0.0, m["cool"] - delta)
		if m["kick"] >= 0.0:
			m["kick"] -= delta
			if m["kick"] < 0.0:
				_kick(m, m["kick_s"])
		m["hic"] -= delta
		if m["hic"] <= 0.0:
			m["hic"] = _rng.randf_range(5.0, 14.0)
			_kick(m, 0.35)
		if m["cool"] <= 0.0:
			var reach: float = 5.0 + m["top"] * 6.0
			for c in folk:
				if c["state"] in ["gone", "exit"]:
					continue
				if absf(c["x"] - m["x"]) < reach and c["y"] > m["y"] - 30 and c["y"] < m["y"] + 4:
					_kick(m, 0.45)
					break
		# a damped spring: s > 0 squashes (shorter and wider), s < 0 stretches; a kick squashes first
		var a: float = -140.0 * m["s"] - 7.0 * m["v"]
		m["v"] += a * delta
		m["s"] = clampf(m["s"] + m["v"] * delta, -0.35, 0.35)
		var sq: float = m["s"] + 0.03 * sin(_time * 1.8 + m["phase"] * TAU)
		var b: float = m["base"]
		n.scale = Vector3(b * (1.0 + sq * 0.55), b * (1.0 - sq), b * (1.0 + sq * 0.55))
		m["excite"] = maxf(0.0, m["excite"] - delta * 1.2)
		if m["light"]:
			m["light"].light_energy = 0.6 + 0.15 * sin(_time * 1.6 + m["phase"] * TAU) + 1.6 * m["excite"]
		for mi in m["meshes"]:
			(mi as MeshInstance3D).set_instance_shader_parameter("excite", m["excite"])
