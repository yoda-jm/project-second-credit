shader_type sky;
// Prism Breaker sky: a deep violet and blue nebula with drifting dust lanes and a field of twinkling stars.
// "pulse" brightens it on the beat and on combos, "warp" stretches it into light streaks between walls.
uniform float pulse = 0.0;
uniform float warp = 0.0;
uniform vec3 neb_a : source_color = vec3(0.32, 0.06, 0.5);
uniform vec3 neb_b : source_color = vec3(0.02, 0.2, 0.55);
uniform vec3 neb_c : source_color = vec3(0.9, 0.2, 0.5);

float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float noise3(vec3 p) {
	vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash3(i), hash3(i + vec3(1,0,0)), f.x), mix(hash3(i + vec3(0,1,0)), hash3(i + vec3(1,1,0)), f.x), f.y),
	           mix(mix(hash3(i + vec3(0,0,1)), hash3(i + vec3(1,0,1)), f.x), mix(hash3(i + vec3(0,1,1)), hash3(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float fbm(vec3 p) {
	float s = 0.0; float a = 0.5;
	for (int i = 0; i < 5; i++) { s += a * noise3(p); p = p * 2.03 + vec3(1.7, 9.2, 3.1); a *= 0.5; }
	return s;
}
float stars(vec3 d, float scale, float thresh) {
	vec3 p = d * scale;
	vec3 i = floor(p);
	float h = hash3(i);
	if (h < thresh) return 0.0;
	vec3 c = i + 0.5 + (vec3(hash3(i + 3.1), hash3(i + 7.7), hash3(i + 1.3)) - 0.5) * 0.6;
	float r = length(p - c);
	float tw = 0.6 + 0.4 * sin(TIME * (1.0 + h * 4.0) + h * 60.0);
	return smoothstep(0.35, 0.0, r) * tw * (h - thresh) / (1.0 - thresh);
}

void sky() {
	vec3 d = EYEDIR;
	if (AT_CUBEMAP_PASS) {  // the radiance map only needs the broad colours: skip the noise
		COLOR = mix(neb_b, neb_a, 0.5 + 0.5 * d.y) * 0.25;
	} else {
	float t = TIME * 0.012;
	float n = fbm(d * 2.2 + vec3(t, 0.0, -t));
	float m = fbm(d * 4.5 - vec3(0.0, t * 1.5, 0.0) + n * 1.3);
	float lanes = smoothstep(0.35, 0.75, m);
	vec3 col = mix(neb_b, neb_a, smoothstep(0.3, 0.7, n));
	col = mix(col, neb_c, smoothstep(0.62, 0.85, m) * 0.5);
	col *= 0.1 + 0.55 * lanes * lanes;
	// a soft glow where the tunnel vanishes (straight ahead, -Z)
	float ahead = max(dot(d, vec3(0.0, 0.05, -1.0)), 0.0);
	col += vec3(0.25, 0.3, 0.9) * pow(ahead, 12.0) * (0.35 + pulse * 0.6 + warp);
	col *= 1.0 + pulse * 0.7;
	float s = stars(d, 180.0, 0.985) * 1.8 + stars(d, 420.0, 0.99) * 0.9;
	// warp: stars smear towards the vanishing point
	s += warp * stars(normalize(d * vec3(1.0, 1.0, 0.08)), 90.0, 0.97) * 1.5;
	col += vec3(0.85, 0.9, 1.0) * s;
	COLOR = col;
	}
}
