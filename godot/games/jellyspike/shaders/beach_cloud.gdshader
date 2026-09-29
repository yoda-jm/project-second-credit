// Jelly Spike puffy clouds: vertex-coloured (white tops, tinted bellies), soft wrapped light and a touch of
// self-illumination so they stay luminous on the sky. At golden hour (under > 0) the low sun lights them from below:
// the bellies and the side towards the sun glow gold (under_col), the tops fall into a dusky rose (top_col).
shader_type spatial;
render_mode diffuse_lambert_wrap, specular_disabled, shadows_disabled;

uniform vec3 tint : source_color = vec3(1.0);
uniform float self_light = 0.35;
uniform float under = 0.0;
uniform vec3 under_col : source_color = vec3(1.0, 0.62, 0.32);
uniform vec3 top_col : source_color = vec3(0.75, 0.55, 0.7);
uniform vec3 sun_dir = vec3(0.3, 0.05, -0.95);  // towards the sun

void fragment() {
	vec3 base = COLOR.rgb * tint;
	vec3 nw = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	if (under > 0.0) {
		float below = smoothstep(0.35, -0.6, nw.y);
		float facing = clamp(dot(nw.xz, normalize(sun_dir.xz)) * 0.5 + 0.5, 0.0, 1.0);
		base = mix(base * top_col, under_col, below * 0.6);
		EMISSION = under_col * under * (below * 0.9 + facing * facing * 0.35 + rim * 0.8);
		EMISSION += base * self_light;
	} else {
		EMISSION = base * self_light + tint * rim * 0.25;
	}
	ALBEDO = base;
	ROUGHNESS = 1.0;
}
