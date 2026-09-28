// Pop Voyage puffy clouds: vertex-coloured (white tops, tinted bellies), soft wrapped light and a touch of
// self-illumination so they stay luminous on the sky.
shader_type spatial;
render_mode diffuse_lambert_wrap, specular_disabled, shadows_disabled;

uniform vec3 tint : source_color = vec3(1.0);
uniform float self_light = 0.35;

void fragment() {
	ALBEDO = COLOR.rgb * tint;
	ROUGHNESS = 1.0;
	EMISSION = COLOR.rgb * tint * self_light;
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	EMISSION += tint * rim * 0.25;
}
