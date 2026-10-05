// Biosurge: shared noise for the world's shaders (hash, value noise, fbm, voronoi). Our own code, CC BY-SA 4.0.

// integer hashes (exact on every lattice point: float hashes break into tiles on some GPUs)
float bio_h1(vec2 p) {
	uvec2 q = uvec2(ivec2(floor(p))) * uvec2(1597334673U, 3812015801U);
	uint n = (q.x ^ q.y) * 1597334673U;
	return float(n >> 8U) * (1.0 / 16777215.0);
}

vec2 bio_h2(vec2 p) {
	uvec2 q = uvec2(ivec2(floor(p))) * uvec2(1597334673U, 3812015801U);
	uint n = q.x ^ q.y;
	uvec2 r = uvec2(n, n ^ 0x5bd1e995U) * uvec2(1597334673U, 3812015801U);
	r = (r ^ (r >> 15U)) * 2246822519U;
	return vec2(r >> 8U) * (1.0 / 16777215.0);
}

float bio_vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	return mix(mix(bio_h1(i), bio_h1(i + vec2(1.0, 0.0)), u.x),
			mix(bio_h1(i + vec2(0.0, 1.0)), bio_h1(i + vec2(1.0, 1.0)), u.x), u.y);
}

float bio_fbm(vec2 p) {
	return (0.5 * bio_vnoise(p) + 0.25 * bio_vnoise(p * 2.03 + 7.1) + 0.125 * bio_vnoise(p * 4.07 + 3.3)) / 0.875;
}

// x: distance to the nearest feature point, y: an edge measure (F2 - F1, 0 on the cells' borders), z: the cell's id
vec3 bio_voro(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	float id = 0.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 r = g + bio_h2(i + g) * 0.85 + 0.075 - f;
			float d = dot(r, r);
			if (d < d1) {
				d2 = d1;
				d1 = d;
				id = bio_h1(i + g + 31.7);
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	d1 = sqrt(d1);
	return vec3(d1, sqrt(d2) - d1, id);
}

// a heartbeat (lub-dub) or a soft breath, 0..1, period 1
float bio_beat(float t, float heart) {
	float p = fract(t);
	float hb = exp(-pow((p - 0.08) * 16.0, 2.0)) + 0.65 * exp(-pow((p - 0.26) * 16.0, 2.0));
	float br = 0.5 + 0.5 * sin(t * 6.2831853);
	return mix(br, hb, heart);
}
