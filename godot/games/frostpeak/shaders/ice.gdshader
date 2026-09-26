shader_type spatial;
// Rink ice: a glossy sheet, faintly blue where it is deep and milky where it was resurfaced, with skate scratches
// that run mostly along the lanes (dulling the reflections), a few deeper gouges, and a fresnel sheen.

uniform vec3 tint : source_color = vec3(0.7, 0.8, 0.92);
uniform vec3 milk : source_color = vec3(0.95, 0.97, 1.0);
uniform float scratches = 1.0;

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float hash2(vec2 q) {  // no sin(): stays exact for big coordinates, so the noise has no seams
	vec2 p = fract(q * vec2(0.3183099, 0.3678794) + 0.1) * 17.0;
	return fract(p.x * p.y * (p.x + p.y));
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1, 0)), f.x), mix(hash2(i + vec2(0, 1)), hash2(i + vec2(1, 1)), f.x), f.y);
}

// short scratches near `angle` (each cell turns its own a little), in cells of `cell` metres
float scratch(vec2 p, float angle, float cell, float density) {
	vec2 d = vec2(cos(angle), sin(angle));
	vec2 q = vec2(dot(p, d), dot(p, vec2(-d.y, d.x))) / cell;
	q.x += hash(vec2(floor(q.y), 3.1)) * 7.0;  // stagger the rows, so no grid shows
	vec2 id = floor(q);
	vec2 f = fract(q);
	float h = hash(id);
	float off = hash(id + 7.3);
	float bend = (hash(id + 1.9) - 0.5) * 0.3;
	float y = f.y - off - (f.x - 0.5) * bend;
	float len = 0.2 + 0.3 * h;
	float line = smoothstep(0.03, 0.0, abs(y)) * smoothstep(len, len - 0.1, abs(f.x - 0.5));
	return line * step(1.0 - density, h) * (0.4 + 0.6 * off);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xz;
	// lanes run along x on the straights and round the centres of the curves: scratches follow the travel
	vec2 c = vec2(sign(p.x) * 50.0, 0.0);
	float along = abs(p.x) > 50.0 ? atan(p.y - c.y, p.x - c.x) + 1.5708 : 0.0;
	float s = 0.0;
	s += scratch(p, along + 0.05, 1.6, 0.55);
	s += scratch(p * 1.37, along - 0.08, 1.1, 0.5) * 0.8;
	s += scratch(p * 0.9, along + 0.6, 2.3, 0.25) * 0.6;
	s = clamp(s * scratches, 0.0, 1.0);
	float cloud = vnoise(p * 0.15) * 0.6 + vnoise(p * 0.6) * 0.4;
	vec3 col = mix(tint, milk, smoothstep(0.35, 0.8, cloud) * 0.45);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	ALBEDO = mix(col, milk, s * 0.6);
	METALLIC = 0.0;
	SPECULAR = 0.45 + 0.25 * fres;
	ROUGHNESS = 0.07 + 0.08 * cloud + 0.35 * s;
	CLEARCOAT = 1.0;
	CLEARCOAT_ROUGHNESS = 0.02 + 0.2 * s;
}
