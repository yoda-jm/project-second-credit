// Jelly Spike wood and thatch: vertex-coloured, with a procedural grain. tools/blender/jellyspike_beach.py writes
// UV = (metres along the face's longest edge, metres across it), so the streaks run along planks, posts and straw.
// The grain shades the colour and bumps the normal (screen-space derivatives: no tangents needed); straw (thatch 1)
// is coarser and more broken. rim lights the edges against a low sun.
shader_type spatial;

uniform float grain = 1.0;
uniform float thatch = 0.0;
uniform float rough = 0.82;
uniform float rim = 0.0;
uniform float rim_tint = 0.5;
uniform float near_fade = 45.0;  // metres from the camera where the grain fades out (it would only shimmer)

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	vec2 g = UV;
	float cam_d = length(VERTEX);
	float k = grain * smoothstep(near_fade, near_fade * 0.4, cam_d);
	float h;
	if (thatch > 0.5) {
		// straw: fine parallel strands, some darker, broken along their length
		float strand = vnoise(vec2(g.x * 3.0, g.y * 60.0));
		float gap = vnoise(vec2(g.x * 9.0, g.y * 22.0));
		h = strand * 0.75 + gap * 0.25;
	} else {
		// wood: long warped streaks, a finer fibre, the odd knot
		float warp = vnoise(vec2(g.x * 0.8, g.y * 3.0)) * 4.0;
		float streak = 0.5 + 0.5 * sin(g.y * 55.0 + warp * 3.0 + vnoise(vec2(g.x * 2.0, g.y * 8.0)) * 2.0);
		float fibre = vnoise(vec2(g.x * 5.0, g.y * 140.0));
		h = streak * 0.6 + fibre * 0.4;
	}
	vec3 c = COLOR.rgb * mix(1.0, 0.8 + 0.3 * h, k);
	// bump from the grain height (surface gradient from screen-space derivatives)
	vec3 dpdx = dFdx(VERTEX), dpdy = dFdy(VERTEX);
	float dhx = dFdx(h), dhy = dFdy(h);
	vec3 n = normalize(NORMAL);
	vec3 r1 = cross(dpdy, n), r2 = cross(n, dpdx);
	float det = dot(dpdx, r1);
	vec3 grad = sign(det) * (dhx * r1 + dhy * r2);
	NORMAL = normalize(abs(det) * n - grad * 0.006 * k);  // the grain is about 6 mm deep
	ALBEDO = c;
	ROUGHNESS = rough + (h - 0.5) * 0.12 * k;
	SPECULAR = 0.35;
	RIM = rim;
	RIM_TINT = rim_tint;
}
