shader_type sky;
// Neon Knuckles night sky: a deep zenith fading to a horizon lit orange-pink by the city, slow clouds lit from
// below by the same glow, a few stars and a hazy moon.
uniform vec3 zenith : source_color = vec3(0.01, 0.012, 0.04);
uniform vec3 horizon : source_color = vec3(0.1, 0.06, 0.16);
uniform vec3 glow : source_color = vec3(0.55, 0.2, 0.35);
uniform float glow_height = 0.12;
uniform vec3 moon_dir = vec3(0.35, 0.2, -1.0);
uniform float cloud_cover = 0.55;
uniform float star_amount = 1.0;

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
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < 5; i++) {
		v += a * noise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

void sky() {
	vec3 d = EYEDIR;
	float h = d.y;
	vec3 c = mix(horizon, zenith, smoothstep(-0.02, 0.55, h));
	c += glow * exp(-max(h, 0.0) / glow_height);
	// stars, dimmed near the glowing horizon
	vec2 sp = vec2(atan(d.x, -d.z), asin(clamp(h, -1.0, 1.0))) * 220.0;
	vec2 cell = floor(sp);
	float r = hash(cell);
	vec2 off = vec2(hash(cell + 3.1), hash(cell + 7.7));
	float star = step(0.985, r) * smoothstep(0.35, 0.0, length(fract(sp) - off));
	c += vec3(0.8, 0.85, 1.0) * star * star_amount * smoothstep(0.05, 0.35, h) * (0.5 + 0.5 * sin(TIME * 2.0 + r * 40.0));
	// the moon and its halo
	float m = dot(d, normalize(moon_dir));
	c += vec3(0.9, 0.92, 1.0) * smoothstep(0.99955, 0.9997, m) * 3.0;
	c += vec3(0.35, 0.4, 0.6) * pow(max(m, 0.0), 300.0) * 0.8 + vec3(0.1, 0.1, 0.18) * pow(max(m, 0.0), 30.0) * 0.4;
	// clouds, lit from below by the city
	if (h > 0.0) {
		vec2 uv = d.xz / (h + 0.08) * 0.9 + vec2(TIME * 0.004, 0.0);
		float n = fbm(uv * 1.6);
		float cov = smoothstep(1.0 - cloud_cover, 1.05 - cloud_cover * 0.5, n);
		vec3 cc = mix(glow * 0.55 + horizon * 0.5, zenith * 2.5 + vec3(0.02, 0.02, 0.04), smoothstep(0.0, 0.5, h));
		cc += vec3(0.25, 0.27, 0.35) * pow(max(m, 0.0), 40.0);  // moonlit edges
		c = mix(c, cc, cov * smoothstep(0.0, 0.06, h) * 0.85);
	}
	COLOR = c;
}
