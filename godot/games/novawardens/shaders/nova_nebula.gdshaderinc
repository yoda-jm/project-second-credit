// Nova Wardens: the nebula. Domain-warped 3D noise on the sky sphere in two hues (a rose-magenta heart, teal and
// violet wings), shaped into a long diagonal cloud across the upper sky, bright filaments along its edges.
// Needs nova_noise.gdshaderinc. Returns HDR colour to add.

uniform vec3 neb_a : source_color = vec3(0.75, 0.2, 0.55);
uniform vec3 neb_b : source_color = vec3(0.15, 0.55, 0.65);
uniform vec3 neb_c : source_color = vec3(0.35, 0.2, 0.7);
uniform vec3 neb_axis = vec3(-0.35, 0.55, -0.75);   // where the nebula's heart is
uniform float nebula = 0.6;

vec3 nw_nebula(vec3 d, float t) {
	vec3 ax = normalize(neb_axis);
	float near = max(dot(d, ax), 0.0);
	float shape = smoothstep(0.55, 0.98, near);
	if (shape <= 0.0) {
		return vec3(0.0);
	}
	vec3 p = d * 3.2;
	vec3 q = vec3(nw_fbm3(p + vec3(0.0, 0.0, t * 0.003), 4), nw_fbm3(p + vec3(5.2, 1.3, 2.8), 4), 0.0);
	float n = nw_fbm3(p * 1.4 + q * 2.4, 5);
	float fil = 1.0 - abs(n * 2.0 - 1.0);
	fil = pow(fil, 6.0);
	float dens = smoothstep(0.38, 0.8, n) * shape;
	vec3 col = mix(neb_c, neb_a, smoothstep(0.45, 0.75, q.x));
	col = mix(col, neb_b, smoothstep(0.5, 0.8, q.y) * 0.8);
	vec3 c = col * dens * 0.55 + mix(neb_a, vec3(1.0, 0.8, 0.9), 0.4) * fil * shape * 0.22;
	// dark dust in front of the glow
	c *= 1.0 - 0.7 * smoothstep(0.55, 0.75, nw_fbm3(p * 2.6 + 11.0, 3)) * shape;
	return c * nebula;
}
