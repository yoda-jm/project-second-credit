shader_type spatial;
// Mossfolk: the deep glow beyond the cave's arches, far behind everything. A bioluminescent gradient in the
// level's colours, slow curtains of light high up, a bright band low down where the grotto glows, and faint
// twinkling specks (spores caught in the light).

render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 top : source_color = vec3(0.02, 0.03, 0.1);
uniform vec3 mid : source_color = vec3(0.05, 0.25, 0.35);
uniform vec3 low : source_color = vec3(0.15, 0.5, 0.55);
uniform vec3 glow_a : source_color = vec3(0.3, 1.0, 0.9);
uniform vec3 glow_b : source_color = vec3(0.7, 0.4, 1.0);
uniform vec2 extent = vec2(200.0, 90.0);
uniform float horizon = 0.3;       // where the bright band sits, from the bottom (0) to the top (1)
uniform float energy = 1.0;
uniform float seed = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0; float a = 0.5;
	for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
	return v;
}

void fragment() {
	vec2 wp = UV * extent;
	float y = 1.0 - UV.y;
	vec3 col = mix(low, mid, smoothstep(horizon - 0.12, horizon + 0.2, y));
	col = mix(col, top, smoothstep(horizon + 0.15, 0.95, y));
	// the bright band round the horizon, rippling
	float band = exp(-pow((y - horizon - 0.03 * sin(wp.x * 0.05 + TIME * 0.05)) * 7.0, 2.0));
	col += mix(glow_a, glow_b, 0.5 + 0.5 * sin(wp.x * 0.02 + seed)) * band * 0.45;
	// curtains: vertical folds drifting sideways, fading at top and bottom
	float cx = wp.x * 0.07 + seed;
	float fold = fbm(vec2(cx + TIME * 0.02, y * 1.5 - TIME * 0.01));
	float ribbon = smoothstep(0.55, 0.8, fbm(vec2(cx * 0.6 + fold * 1.6 + TIME * 0.015, 3.0)));
	float curtain = ribbon * smoothstep(horizon + 0.05, horizon + 0.3, y) * smoothstep(1.0, 0.6, y);
	curtain *= 0.6 + 0.4 * noise(vec2(wp.x * 0.3, y * 12.0 - TIME * 0.2));
	col += mix(glow_a, glow_b, smoothstep(0.3, 0.7, fold)) * curtain * 0.55;
	// specks: a sparse grid of tiny lights
	vec2 g = wp * 1.4;
	vec2 cell = floor(g);
	float h = hash(cell + seed);
	vec2 f = fract(g) - 0.5 - (vec2(hash(cell + 3.1), hash(cell + 7.7)) - 0.5) * 0.6;
	float speck = smoothstep(0.09, 0.0, length(f)) * step(0.93, h) * (0.4 + 0.6 * sin(TIME * (0.6 + h * 2.0) + h * 30.0));
	col += mix(glow_a, vec3(1.0), 0.5) * max(speck, 0.0) * smoothstep(horizon - 0.1, horizon + 0.3, y) * 0.7;
	ALBEDO = col * energy;
}
