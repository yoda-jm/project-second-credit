class_name Pbr
extends RefCounted
## Builds physically based materials from the shared CC0 texture sets in core/art/textures/<name>/.
## Triplanar world mapping, so procedural models need no UVs; `tint` multiplies the colour.

const ROOT := "res://core/art/textures/"

static var _cache := {}


static func material(name: String, tint: Color = Color.WHITE, scale: float = 1.0, metallic: float = 0.0,
		roughness_scale: float = 1.0, vertex_color: bool = false) -> StandardMaterial3D:
	var key := "%s|%s|%s|%s|%s|%s" % [name, tint, scale, metallic, roughness_scale, vertex_color]
	if _cache.has(key):
		return _cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(ROOT + name + "/albedo.jpg")
	m.albedo_color = tint
	m.normal_enabled = true
	m.normal_texture = load(ROOT + name + "/normal.jpg")
	m.normal_scale = 1.2
	m.roughness_texture = load(ROOT + name + "/roughness.jpg")
	m.roughness = roughness_scale
	m.metallic = metallic
	if ResourceLoader.exists(ROOT + name + "/ao.jpg"):
		m.ao_enabled = true
		m.ao_texture = load(ROOT + name + "/ao.jpg")
		m.ao_light_affect = 0.6
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE * scale
	m.uv1_triplanar_sharpness = 4.0
	m.vertex_color_use_as_albedo = vertex_color
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_cache[key] = m
	return m


## The same material mapped in the object's own space: for props that move, spin or squash (a world mapping would
## make the texture slide across them).
static func local(name: String, tint: Color = Color.WHITE, scale: float = 1.0, metallic: float = 0.0,
		roughness_scale: float = 1.0) -> StandardMaterial3D:
	var key := "local|%s|%s|%s|%s|%s" % [name, tint, scale, metallic, roughness_scale]
	if not _cache.has(key):
		var m := material(name, tint, scale, metallic, roughness_scale).duplicate() as StandardMaterial3D
		m.uv1_world_triplanar = false
		_cache[key] = m
	return _cache[key]
