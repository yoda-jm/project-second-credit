// Marble Drift: small hash and value-noise helpers shared by the course and sky shaders (our own, CC BY-SA 4.0).

float md_hash(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

vec2 md_hash22(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.xx + p3.yz) * p3.zy);
}

float md_hash3(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

float md_noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(md_hash(i), md_hash(i + vec2(1, 0)), u.x), mix(md_hash(i + vec2(0, 1)), md_hash(i + vec2(1, 1)), u.x), u.y);
}

float md_noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float a = mix(md_hash3(i), md_hash3(i + vec3(1, 0, 0)), u.x);
	float b = mix(md_hash3(i + vec3(0, 1, 0)), md_hash3(i + vec3(1, 1, 0)), u.x);
	float c = mix(md_hash3(i + vec3(0, 0, 1)), md_hash3(i + vec3(1, 0, 1)), u.x);
	float d = mix(md_hash3(i + vec3(0, 1, 1)), md_hash3(i + vec3(1, 1, 1)), u.x);
	return mix(mix(a, b, u.y), mix(c, d, u.y), u.z);
}

float md_fbm(vec2 p, int oct) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < oct; i++) {
		v += a * md_noise(p);
		p = mat2(vec2(1.6, 1.2), vec2(-1.2, 1.6)) * p + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

float md_fbm3(vec3 p, int oct) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < oct; i++) {
		v += a * md_noise3(p);
		p = p * 2.02 + vec3(1.7, 9.2, 4.3);
		a *= 0.5;
	}
	return v;
}

// Distance to the nearest of a jittered grid of points (cells of 1 unit) and that point's hash.
vec2 md_cells(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	float best = 8.0, id = 0.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = md_hash22(i + g);
			float d = length(g + o - f);
			if (d < best) {
				best = d;
				id = md_hash(i + g + 7.1);
			}
		}
	}
	return vec2(best, id);
}
