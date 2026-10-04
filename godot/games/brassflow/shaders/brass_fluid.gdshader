// Brassflow: the glow as a liquid in a tank or vat. Emissive, with slow swirls rising through it, brighter at the
// rim (fresnel) and at the surface; pulse lifts the energy (the alarm, or the flow starting). Its own clock (t).
shader_type spatial;
render_mode blend_mix, cull_back;

uniform float t = 0.0;
uniform vec3 color : source_color = vec3(0.3, 1.0, 0.72);
uniform vec3 deep : source_color = vec3(0.05, 0.45, 0.35);
uniform float energy = 2.2;
uniform float pulse = 0.0;
uniform float alpha = 0.85;

varying vec3 lpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	lpos = VERTEX;
}

void fragment() {
	float a = atan(lpos.z, lpos.x);
	vec2 p = vec2(a * 1.6, lpos.y * 2.2 - t * 0.35);
	float n = vnoise(p * 2.0 + vec2(vnoise(p * 1.3 + t * 0.1) * 2.0, 0.0)) * 0.65 + vnoise(p * 5.0) * 0.35;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	vec3 c = mix(deep, color, 0.45 + 0.55 * n);
	ALBEDO = c * 0.2;
	EMISSION = c * energy * (0.55 + 0.6 * n + 0.8 * fres) * (1.0 + pulse);
	ROUGHNESS = 0.15;
	ALPHA = alpha;
}
