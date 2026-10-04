// Fuseflight bonfire and torch flames: crossed quads (UV.x across, UV.y from the foot 0 to the tip 1) on which a
// flame is drawn from rising noise: white-gold at the heart, orange, red at the licking tips. Additive.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform float energy = 3.0;
uniform float speed = 2.2;

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
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float seed = wpos.x * 3.1 + wpos.z * 1.7;
	vec2 p = vec2(UV.x * 2.0 - 1.0, UV.y);
	float t = TIME * speed;
	float n = vnoise(vec2(p.x * 3.0 + seed, p.y * 3.5 - t)) * 0.6 + vnoise(vec2(p.x * 7.0 - seed, p.y * 7.0 - t * 1.7)) * 0.4;
	float x = p.x + (n - 0.5) * 0.5 * p.y;
	float w = (1.0 - p.y) * (0.75 + 0.3 * n);
	float body = smoothstep(w, w * 0.35, abs(x)) * smoothstep(1.0, 0.55, p.y + (n - 0.5) * 0.5);
	float heat = body * smoothstep(0.9, 0.0, p.y + abs(x) * 0.8);
	vec3 col = mix(vec3(0.9, 0.15, 0.03), vec3(1.0, 0.5, 0.1), smoothstep(0.0, 0.5, heat));
	col = mix(col, vec3(1.0, 0.92, 0.6), smoothstep(0.55, 1.0, heat));
	ALBEDO = col * body * energy * smoothstep(0.0, 0.08, UV.y + 0.05);
}
