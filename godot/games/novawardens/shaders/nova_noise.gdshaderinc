// Nova Wardens: small hash and value-noise helpers shared by the backdrop shaders.

float nw_hash(vec2 p) {
	// sin-free (no banding at large coordinates)
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float nw_hash3(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

vec3 nw_hash33(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.xxy + p.yxx) * p.zyx);
}

float nw_noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(nw_hash(i), nw_hash(i + vec2(1, 0)), u.x), mix(nw_hash(i + vec2(0, 1)), nw_hash(i + vec2(1, 1)), u.x), u.y);
}

float nw_noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float a = mix(nw_hash3(i), nw_hash3(i + vec3(1, 0, 0)), u.x);
	float b = mix(nw_hash3(i + vec3(0, 1, 0)), nw_hash3(i + vec3(1, 1, 0)), u.x);
	float c = mix(nw_hash3(i + vec3(0, 0, 1)), nw_hash3(i + vec3(1, 0, 1)), u.x);
	float d = mix(nw_hash3(i + vec3(0, 1, 1)), nw_hash3(i + vec3(1, 1, 1)), u.x);
	return mix(mix(a, b, u.y), mix(c, d, u.y), u.z);
}

float nw_fbm(vec2 p, int oct) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < oct; i++) {
		v += a * nw_noise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

float nw_fbm3(vec3 p, int oct) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < oct; i++) {
		v += a * nw_noise3(p);
		p = p * 2.02 + vec3(1.7, 9.2, 4.3);
		a *= 0.5;
	}
	return v;
}
