class_name Look
extends RefCounted
## Environment helpers shared by the games, so scenes look alike in both renderers. The compatibility renderer
## (software captures, older GPUs) lights with the sky far brighter than Forward+ and fogs much harder: there the
## ambient becomes a flat colour matching the sky, and the fog is thinned.


static func compat() -> bool:
	return RenderingServer.get_current_rendering_method() == "gl_compatibility"


## Sky ambient in Forward+; a flat colour (roughly the sky's average) in the compatibility renderer.
static func sky_ambient(env: Environment, color: Color, energy: float) -> void:
	if compat():
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = color
		env.ambient_light_energy = energy * 0.7
	else:
		env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
		env.ambient_light_energy = energy


static func fog(env: Environment, color: Color, density: float) -> void:
	env.fog_enabled = true
	env.fog_light_color = color
	env.fog_density = density * (0.25 if compat() else 1.0)
