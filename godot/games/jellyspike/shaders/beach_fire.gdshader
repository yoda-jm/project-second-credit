// Jelly Spike flames: tongues of fire drawn on crossed quads (UV.y runs up the flame), licking and flickering, white-
// yellow at the root to orange and red at the tips. Additive HDR colour (feeds the bloom).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float energy = 3.0;
uniform float speed = 1.0;

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
}

void fragment() {
	float seed = hash(wpos.xz * 3.1) * 40.0;
	float t = TIME * speed;
	float y = UV.y;
	float x = UV.x * 2.0 - 1.0;
	float n = vnoise(vec2(x * 2.5 + seed, y * 3.5 - t * 3.2)) * 0.65 + vnoise(vec2(x * 5.0 - seed, y * 7.0 - t * 5.1)) * 0.35;
	float sway = (vnoise(vec2(seed, t * 1.3)) - 0.5) * 0.5 * y * y;
	float wid = 0.75 * pow(max(1.0 - y, 0.0), 0.6) * smoothstep(0.0, 0.12, y) + 0.02;
	float xx = x - sway + (n - 0.5) * 0.45 * y;
	float body = smoothstep(wid, wid * 0.35, abs(xx));
	body *= smoothstep(1.0, 0.45, y + (n - 0.5) * 0.55);
	float core = smoothstep(wid * 0.55, 0.0, abs(xx)) * smoothstep(0.7, 0.1, y);
	vec3 c = mix(vec3(1.0, 0.25, 0.05), vec3(1.0, 0.6, 0.15), body);
	c = mix(c, vec3(1.0, 0.92, 0.6), core);
	float k = 0.85 + 0.15 * sin(TIME * 17.0 + seed);
	ALBEDO = c * body * energy * k;
}
