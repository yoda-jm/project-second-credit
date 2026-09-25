class_name Fx
extends RefCounted
## Shared particle materials: soft round sprites instead of flat squares. "glow" is additive (fire, sparks,
## flashes), "smoke" is a soft, noisy puff that stays lit by the scene, "soft" is a plain soft disc (spray, dust).

static var _cache := {}


static func _disc(soft: float) -> GradientTexture2D:
	var key := "disc%s" % soft
	if _cache.has(key):
		return _cache[key]
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(soft, Color(1, 1, 1, 0.6))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 64
	t.height = 64
	_cache[key] = t
	return t


static func _puff() -> NoiseTexture2D:
	if _cache.has("puff"):
		return _cache["puff"]
	var n := FastNoiseLite.new()
	n.frequency = 0.035
	n.fractal_octaves = 4
	var t := NoiseTexture2D.new()
	t.width = 128
	t.height = 128
	t.noise = n
	t.seamless = true
	var g := Gradient.new()  # noise shaped by a radial falloff happens in the material (alpha texture below)
	g.set_color(0, Color(0, 0, 0, 0))
	g.set_color(1, Color(1, 1, 1, 1))
	t.color_ramp = g
	_cache["puff"] = t
	return t


## kind: "glow", "smoke" or "soft"
static func material(kind: String, tint: Color = Color.WHITE) -> StandardMaterial3D:
	var key := "%s|%s" % [kind, tint]
	if _cache.has(key):
		return _cache[key]
	var m := StandardMaterial3D.new()
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_color = tint
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	match kind:
		"glow":
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.albedo_texture = _disc(0.25)
		"smoke":
			m.albedo_texture = _disc(0.5)
			m.detail_enabled = true
			m.detail_mask = _disc(0.7)
			m.detail_albedo = _puff()
			m.detail_blend_mode = BaseMaterial3D.BLEND_MODE_MUL
			m.roughness = 1.0
		"flat":  # lying on a surface (wakes): soft disc, no billboard
			m.billboard_mode = BaseMaterial3D.BILLBOARD_DISABLED
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.albedo_texture = _disc(0.3)
		_:
			m.albedo_texture = _disc(0.4)
			m.roughness = 0.8
	_cache[key] = m
	return m


## A curve that makes particles grow over their life (smoke) or shrink (sparks).
static func size_curve(grow: bool) -> Curve:
	var key := "curve%s" % grow
	if _cache.has(key):
		return _cache[key]
	var c := Curve.new()
	if grow:
		c.add_point(Vector2(0, 0.35))
		c.add_point(Vector2(1, 1.0))
	else:
		c.add_point(Vector2(0, 1.0))
		c.add_point(Vector2(1, 0.15))
	_cache[key] = c
	return c
