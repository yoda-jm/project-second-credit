// Bloomwand clouds (our own, CC BY-SA 4.0): vertex-coloured puffs (lit tops, tinted bellies), soft wrapped light, a
// glow of their own so they stay luminous, and a warm rim where the sun catches their edges.
shader_type spatial;
render_mode diffuse_lambert_wrap, specular_disabled, cull_disabled;

uniform vec3 tint : source_color = vec3(1.0);
uniform float self_light = 0.35;
uniform vec3 rim_col : source_color = vec3(1.0, 0.8, 0.6);
uniform float rim = 0.3;

void fragment() {
	ALBEDO = COLOR.rgb * tint;
	ROUGHNESS = 1.0;
	float f = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 2.5);
	EMISSION = COLOR.rgb * tint * self_light + rim_col * f * rim;
}
