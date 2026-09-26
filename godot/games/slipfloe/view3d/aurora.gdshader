shader_type spatial;
// Slipfloe sky: a starry night with aurora curtains slowly waving.

render_mode unshaded, cull_disabled;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	vec2 uv = UV;
	vec3 col = mix(vec3(0.03, 0.06, 0.14), vec3(0.0, 0.01, 0.04), uv.y);
	// stars
	vec2 sp = uv * vec2(180.0, 60.0);
	float st = step(0.985, hash(floor(sp))) * (0.5 + 0.5 * sin(TIME * 2.0 + hash(floor(sp)) * 20.0));
	col += vec3(st) * (1.0 - uv.y) * 0.8;
	// curtains: bands whose height waves along x
	for (int i = 0; i < 3; i++) {
		float fi = float(i);
		float wave = noise(vec2(uv.x * 3.0 + fi * 4.1 + TIME * 0.05, TIME * 0.1 + fi)) * 0.35 + 0.25 + fi * 0.08;
		float d = uv.y - (1.0 - wave);
		float band = smoothstep(0.0, 0.03, -d) * exp(d * 7.0) * step(d, 0.0);
		float rays = 0.6 + 0.4 * noise(vec2(uv.x * 60.0 + fi * 13.0, TIME * 0.4));
		vec3 c = mix(vec3(0.2, 1.0, 0.55), vec3(0.6, 0.35, 1.0), smoothstep(0.0, 0.3, -d) * 0.8 + fi * 0.15);
		col += c * band * rays * 0.7;
	}
	ALBEDO = col;
}
