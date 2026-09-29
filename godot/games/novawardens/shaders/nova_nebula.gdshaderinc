// Nova Wardens: the deep sky, baked once into a panorama by nova_sky_bake (so it can afford many octaves). The
// nebula: domain-warped 3D noise on the sky sphere in three hues (a rose-magenta heart, teal and violet wings), shaped
// into a cloud round neb_axis, bright filaments and blue reflection wisps along its edges, dark dust lanes and globules
// in front. The Milky Way: a meandering band round the great circle whose pole is band_axis, a brighter warmer bulge
// towards bulge_dir, rifts of dust, knots of unresolved stars. Needs nova_noise.gdshaderinc. HDR colour to add.

uniform vec3 neb_a : source_color = vec3(0.75, 0.2, 0.55);
uniform vec3 neb_b : source_color = vec3(0.15, 0.55, 0.65);
uniform vec3 neb_c : source_color = vec3(0.35, 0.2, 0.7);
uniform vec3 neb_axis = vec3(-0.35, 0.55, -0.75);   // where the nebula's heart is
uniform float nebula = 0.6;
uniform vec3 band_axis = vec3(0.65, -0.57, -0.5);
uniform vec3 bulge_dir = vec3(-0.6, 0.02, -0.8);
uniform float milky = 0.7;

vec3 nw_nebula(vec3 d) {
	vec3 ax = normalize(neb_axis);
	float near = dot(d, ax);
	float shape = smoothstep(0.62, 0.97, near);
	if (shape <= 0.0) {
		return vec3(0.0);
	}
	vec3 p = d * 3.4;
	vec3 q = vec3(nw_fbm3(p, 5), nw_fbm3(p + vec3(5.2, 1.3, 2.8), 5), nw_fbm3(p + vec3(1.7, 9.2, 4.1), 5));
	vec3 r = vec3(nw_fbm3(p * 1.3 + q * 2.2 + vec3(1.7, 9.2, 0.0), 5),
			nw_fbm3(p * 1.3 + q * 2.2 + vec3(8.3, 2.8, 0.0), 5), 0.0);
	float n = nw_fbm3(p * 1.6 + r * 2.6, 7);
	float fil = pow(1.0 - abs(n * 2.0 - 1.0), 8.0);
	float fil2 = pow(1.0 - abs(nw_fbm3(p * 4.2 + r * 3.0, 6) * 2.0 - 1.0), 14.0);
	float dens = smoothstep(0.36, 0.85, n) * shape;
	vec3 col = mix(neb_c, neb_a, smoothstep(0.4, 0.75, r.x));
	col = mix(col, neb_b, smoothstep(0.45, 0.8, q.y) * 0.85);
	vec3 c = col * dens * 0.55;
	c += mix(neb_a, vec3(1.0, 0.75, 0.85), 0.45) * fil * shape * 0.24;
	c += mix(neb_b, vec3(0.7, 0.95, 1.0), 0.4) * fil2 * smoothstep(0.4, 0.7, q.z) * shape * 0.2;
	// the hot heart, lit by young stars
	float heart = pow(max(near, 0.0), 90.0);
	c += vec3(1.0, 0.72, 0.82) * heart * 0.3 * (0.5 + n);
	// dust lanes and dark globules in front, their edges faintly rim-lit
	float dn = nw_fbm3(p * 2.8 + r * 1.5 + 11.0, 6);
	float dust = smoothstep(0.52, 0.7, dn);
	c *= 1.0 - 0.85 * dust * shape;
	c += col * smoothstep(0.47, 0.52, dn) * (1.0 - dust) * shape * 0.06;
	return c * nebula;
}

vec3 nw_milky(vec3 d) {
	vec3 ax = normalize(band_axis);
	float lat = dot(d, ax);
	lat += (nw_fbm3(d * 3.0 + 4.0, 4) - 0.5) * 0.1;
	float bulge = pow(max(dot(d, normalize(bulge_dir)), 0.0), 5.0);
	float wide = exp(-lat * lat * (60.0 - 20.0 * bulge));
	float core = exp(-lat * lat * 260.0);
	if (wide < 0.002) {
		return vec3(0.0);
	}
	float n = nw_fbm3(d * 6.0, 6);
	float fine = nw_fbm3(d * 24.0 + 7.0, 5);
	float clumps = smoothstep(0.45, 0.8, nw_fbm3(d * 14.0 + 2.0, 5));
	float lanes = smoothstep(0.46, 0.64, nw_fbm3(d * 7.0 + 3.0, 6)) * exp(-lat * lat * 150.0);
	float rift = smoothstep(0.03, 0.0, abs(lat + (nw_fbm3(d * 5.0, 3) - 0.5) * 0.04)) * 0.7;
	float glow = wide * (0.3 + 0.8 * n) + core * (0.4 + 0.9 * fine) * (0.6 + bulge) + clumps * wide * 0.5;
	glow *= (1.0 - 0.8 * lanes) * (1.0 - rift);
	vec3 col = mix(vec3(0.32, 0.38, 0.66), vec3(0.78, 0.64, 0.56), clamp(n * 0.5 + bulge * 0.8, 0.0, 1.0));
	// unresolved stars: a dense fine grain in the band
	float grain = pow(nw_hash3(floor(d * 1700.0)), 40.0) * 3.0 + pow(nw_hash3(floor(d * 900.0) + 5.0), 60.0) * 4.0;
	return (col * glow * 0.1 + vec3(0.85, 0.88, 1.0) * grain * wide * (1.0 - lanes) * 0.08) * milky;
}
