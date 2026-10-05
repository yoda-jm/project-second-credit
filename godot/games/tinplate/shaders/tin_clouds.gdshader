// Tinplate Turbo cloud shadows: soft dark patches drifting slowly over the diorama (multiplied over what lies under).
// Our own shader (CC BY-SA 4.0).
shader_type spatial;
render_mode unshaded, blend_mul, cull_disabled, shadows_disabled, depth_draw_never;

uniform float strength = 0.28;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	vec2 p = UV * 7.0 + vec2(TIME * 0.025, TIME * 0.012);
	float n = noise(p) * 0.6 + noise(p * 2.1) * 0.3 + noise(p * 4.3) * 0.1;
	float shade = smoothstep(0.5, 0.75, n);
	ALBEDO = vec3(1.0 - strength * shade);
}
