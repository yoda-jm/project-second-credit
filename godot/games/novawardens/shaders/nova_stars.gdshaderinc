// Nova Wardens: the star field. Three layers of cells on the sky sphere (fine dust, ordinary stars, a few bright ones
// with a soft cross), each star its own colour temperature and twinkle (the Milky Way is baked: nova_nebula).
// Needs nova_noise.gdshaderinc. Returns HDR colour to add.

vec3 nw_star_layer(vec3 d, float scale, float density, float size, float bright, float t, float twinkle) {
	vec3 p = d * scale;
	vec3 cell = floor(p);
	vec3 h = nw_hash33(cell);
	if (h.x > density) {
		return vec3(0.0);
	}
	vec3 centre = cell + 0.25 + 0.5 * nw_hash33(cell + 7.1);
	float r = length(p - centre);
	float core = smoothstep(size, 0.0, r);
	float tw = 1.0 - twinkle + twinkle * (0.55 + 0.45 * sin(t * (1.7 + h.y * 5.0) + h.z * 60.0))
			* (0.8 + 0.2 * sin(t * 7.3 + h.y * 30.0));
	vec3 col = mix(vec3(0.62, 0.74, 1.0), vec3(1.0, 0.86, 0.66), h.z);
	col = mix(col, vec3(1.0), 0.4);
	return col * core * core * tw * bright * (0.4 + 0.6 * h.y / density);
}

vec3 nw_stars(vec3 d, float t, float amount, float calm) {
	vec3 c = vec3(0.0);
	float k = amount * (1.0 - 0.5 * calm);
	c += nw_star_layer(d, 700.0, 0.2, 0.3, 0.7, t, 0.5);
	c += nw_star_layer(d.yzx, 330.0, 0.06, 0.26, 1.4, t, 0.6);
	c += nw_star_layer(d.zxy, 140.0, 0.02, 0.18, 3.5, t, 0.35);
	return c * k;
}
