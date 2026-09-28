shader_type sky;
// The winter sky: deep blue overhead fading to a pale haze at the horizon, warm near the low sun, with a sun disc,
// a soft halo, and a layer of drifting fair-weather clouds lit from the sun's side.

uniform vec3 zenith : source_color = vec3(0.13, 0.32, 0.72);
uniform vec3 horizon : source_color = vec3(0.72, 0.8, 0.92);
uniform vec3 below : source_color = vec3(0.62, 0.68, 0.78);
uniform vec3 warm : source_color = vec3(1.0, 0.8, 0.55);
uniform float cover = 0.42;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

float fbm(vec2 p) {
	float s = 0.0;
	float a = 0.5;
	for (int i = 0; i < 5; i++) {
		s += noise(p) * a;
		p = p * 2.07 + vec2(3.1, 1.7);
		a *= 0.5;
	}
	return s;
}

void sky() {
	vec3 d = EYEDIR;
	vec3 sun = LIGHT0_ENABLED ? LIGHT0_DIRECTION : vec3(0.0, 1.0, 0.0);
	float up = d.y;
	float cs = max(dot(d, sun), 0.0);
	vec3 col = mix(horizon, zenith, pow(clamp(up, 0.0, 1.0), 0.42));
	// warm glow round the low sun, spreading along the horizon
	float horiz = 1.0 - clamp(up * 2.5, 0.0, 1.0);
	col = mix(col, warm, pow(cs, 6.0) * 0.45 * (0.4 + 0.6 * horiz));
	col += warm * pow(cs, 64.0) * 0.8;
	if (up < 0.0) {
		col = mix(horizon, below, clamp(-up * 5.0, 0.0, 1.0));
	}
	// clouds on a flat layer overhead
	if (up > 0.01) {
		vec2 uv = d.xz / (up + 0.08) * 1.4 + vec2(TIME * 0.006, TIME * 0.002);
		float n = fbm(uv);
		float c = smoothstep(1.0 - cover, 1.0 - cover + 0.28, n);
		float shape = fbm(uv * 2.3 + 5.0);
		vec3 ccol = mix(vec3(0.72, 0.76, 0.86), vec3(1.02, 1.0, 0.97), clamp(shape * 1.3 - 0.1, 0.0, 1.0));
		ccol += warm * pow(cs, 8.0) * 0.6;  // silver linings near the sun
		float fade = smoothstep(0.01, 0.25, up);
		col = mix(col, ccol, c * fade * 0.85);
	}
	// the sun
	if (LIGHT0_ENABLED && !AT_CUBEMAP_PASS) {
		float disc = smoothstep(0.99985, 0.99992, cs);
		col += vec3(1.0, 0.92, 0.8) * disc * 18.0;
	}
	COLOR = col;
}
