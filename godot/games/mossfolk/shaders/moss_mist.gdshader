shader_type spatial;
// Mossfolk: a bank of low mist drifting through the cave, lit faintly from within in the level's colour.

render_mode unshaded, cull_disabled, shadows_disabled, depth_draw_never, fog_disabled;

uniform vec3 col : source_color = vec3(0.3, 0.6, 0.7);
uniform float density = 0.5;
uniform vec2 extent = vec2(100.0, 8.0);
uniform float speed = 0.15;
uniform float seed = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7)) + seed) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0; float a = 0.5;
	for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.1; a *= 0.5; }
	return v;
}

void fragment() {
	vec2 wp = UV * extent;
	float y = 1.0 - UV.y;
	float n = fbm(vec2(wp.x * 0.12 + TIME * speed, wp.y * 0.35 - TIME * speed * 0.3));
	float edge = smoothstep(0.0, 0.25, y) * smoothstep(1.0, 0.35, y);
	float a = smoothstep(0.3, 0.8, n + (0.5 - y) * 0.5) * edge * density;
	ALBEDO = col * (0.7 + 0.6 * n);
	ALPHA = clamp(a, 0.0, 1.0);
}
