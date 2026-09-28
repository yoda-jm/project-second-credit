shader_type spatial;
// A groomed ski course: the snow's own white, with the fine ribs a grooming machine leaves along the track, the
// herringbone scratches of skating skis down the middle, and the same glints as the snow. UV: x across (0..1),
// y along (metres). The edges fade into the plain snow the ribbon lies on.

uniform vec3 tint : source_color = vec3(0.95, 0.97, 1.0);
uniform vec3 shade : source_color = vec3(0.8, 0.85, 0.94);
uniform float width = 6.0;

varying vec3 wpos;
varying vec3 wnorm;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float hash2(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float n = noise(wpos * 1.3) * 0.6 + noise(wpos * 4.1) * 0.3 + noise(wpos * 11.0) * 0.1;
	vec3 col = mix(shade, tint, 0.75 + 0.25 * n);
	float edge = smoothstep(0.0, 0.1, UV.x) * smoothstep(1.0, 0.9, UV.x);
	float dist = length(VERTEX);
	float fine = 1.0 - smoothstep(20.0, 70.0, dist);
	// the grooming ribs: fine ridges along the track, a little shadow on one side of each
	float across = UV.x * width;
	float rib = sin(across * 6.2831 / 0.025) * 0.5 + 0.5;
	float ribs = mix(0.5, rib, fine) * edge;
	// skating marks: short slanting scratches either side of the middle, in a herringbone
	float mid = abs(UV.x - 0.5) * width;
	float row = floor(UV.y / 1.6);
	float side = sign(UV.x - 0.5);
	float along = fract(UV.y / 1.6) * 1.6 - side * mid * 0.45 - hash2(vec2(row, side)) * 0.6;
	float mark = smoothstep(0.035, 0.0, abs(along)) * smoothstep(1.3, 0.4, mid) * smoothstep(0.15, 0.3, mid) * step(0.3, hash2(vec2(row * 3.1, side)));
	mark *= fine * edge;
	col *= 1.0 - 0.05 * ribs - 0.1 * mark;
	col = mix(col, col * vec3(0.96, 0.97, 1.0), edge * 0.5);
	ALBEDO = col;
	float e = 0.05;
	float nx = noise((wpos + vec3(e, 0, 0)) * 1.3) - noise(wpos * 1.3);
	float nz = noise((wpos + vec3(0, 0, e)) * 1.3) - noise(wpos * 1.3);
	vec3 bn = normalize(wnorm - vec3(nx, 0.0, nz) * 0.25 * 8.0 * (1.0 - edge * 0.6));
	vec3 cell = floor(wpos * 60.0);
	float h = hash(cell);
	float near = 1.0 - smoothstep(25.0, 90.0, dist);
	float facet = step(0.988, h) * near;
	vec3 tilt = vec3(hash(cell + 17.0), hash(cell + 41.0), hash(cell + 73.0)) * 2.0 - 1.0;
	bn = normalize(mix(bn, normalize(bn + tilt * 0.45), facet));
	NORMAL = normalize((VIEW_MATRIX * vec4(bn, 0.0)).xyz);
	ROUGHNESS = mix(0.7 - 0.1 * edge, 0.06, facet);
	SPECULAR = mix(0.4, 1.0, facet);
	vec3 view_w = (INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz;
	float g = step(0.993, h) * step(0.8, fract(h * 97.0 + dot(view_w, vec3(3.1, 5.7, 2.3))));
	EMISSION = vec3(0.85, 0.92, 1.0) * g * 0.5 * near;
}
