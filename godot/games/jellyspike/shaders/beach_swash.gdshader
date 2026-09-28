// Jelly Spike swash: the thin sheet of water that runs up the sand after each breaker and slides back, with a lacy
// foam edge and a wet shine left behind (UV = (x, run-up 0 at the waterline .. 1 at the top); the same clock as
// beach_sea).
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, specular_schlick_ggx;

uniform vec3 water_col : source_color = vec3(0.35, 0.85, 0.82);
uniform vec3 foam_col : source_color = vec3(0.97, 0.99, 1.0);
uniform vec3 wet_col : source_color = vec3(0.5, 0.4, 0.28);
uniform float period = 6.5;
uniform float foam = 1.0;
uniform float wet = 1.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float cycle(float x) {
	return fract(TIME / period + 0.08 * sin(x * 0.045) + 0.05 * sin(x * 0.11 + 1.3));
}

void fragment() {
	float x = UV.x;
	float v = UV.y;
	float ph = cycle(x);
	float n_run = floor(TIME / period + 0.08 * sin(x * 0.045) + 0.05 * sin(x * 0.11 + 1.3));
	float reach = 0.55 + 0.45 * vnoise(vec2(x * 0.15, n_run * 3.7));   // each wave runs up its own way
	float s = clamp(ph / 0.7, 0.0, 1.0);
	float edge = reach * pow(sin(3.14159 * s), 0.7) * step(ph, 0.7);
	float edge_n = edge + (vnoise(vec2(x * 2.2, TIME * 0.7)) - 0.5) * 0.06;
	float under = smoothstep(edge_n + 0.01, edge_n - 0.03, v);
	float depth = clamp((edge_n - v) / max(edge_n, 0.05), 0.0, 1.0);
	float fn = vnoise(vec2(x * 3.1, v * 9.0) + vec2(TIME * 0.4, -TIME * 0.8));
	float front = smoothstep(0.07, 0.0, abs(v - edge_n + 0.025)) * step(0.02, edge);
	float lace = front * smoothstep(0.2, 0.55, fn) + under * smoothstep(0.6, 0.85, fn) * 0.5 * (1.0 - depth * 0.5);
	// wet sand where the last wave reached, drying as the cycle goes on
	float wet_line = reach * step(0.35, ph);
	float dry = smoothstep(0.35, 1.0, ph);
	float wet_a = smoothstep(wet_line + 0.02, wet_line - 0.08, v) * (1.0 - under) * (1.0 - dry * 0.8) * wet;
	vec3 col = mix(water_col, foam_col, clamp(lace * foam, 0.0, 1.0));
	float a = under * (0.35 + 0.35 * depth) + lace * foam * 0.9;
	col = mix(wet_col, col, clamp(a / max(a + wet_a * 0.5, 0.001), 0.0, 1.0));
	a = clamp(a + wet_a * 0.45, 0.0, 1.0);
	// below the waterline the sheet is sea: fade it in so no edge shows
	a *= smoothstep(-0.12, -0.03, v);
	ALBEDO = col;
	ALPHA = a;
	ROUGHNESS = mix(0.05, 0.4, lace);
	SPECULAR = 0.7;
}
