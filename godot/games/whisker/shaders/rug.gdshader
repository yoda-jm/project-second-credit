shader_type spatial;
// A wool rug lying on the floor (a plane, UV 0-1): a fringe at both short ends, a patterned border and a field
// with a central medallion and a scatter of small motifs.

uniform vec3 field : source_color = vec3(0.55, 0.12, 0.12);
uniform vec3 border : source_color = vec3(0.12, 0.14, 0.3);
uniform vec3 accent : source_color = vec3(0.92, 0.78, 0.5);
uniform vec2 size = vec2(12.0, 3.2);  // metres, for the proportions of the pattern

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1, 0)), f.x), mix(hash2(i + vec2(0, 1)), hash2(i + vec2(1, 1)), f.x), f.y);
}

void fragment() {
	vec2 m = UV * size;  // metres
	float fringe = 0.22;
	float x = min(m.x, size.x - m.x);
	float y = min(m.y, size.y - m.y);
	vec3 c;
	if (x < fringe) {  // tassels
		float t = step(0.4, fract(m.y * 14.0)) * step(noise(vec2(m.y * 30.0, 1.0)) * 0.08, x);
		if (t < 0.5) discard;
		c = accent * 0.85;
	} else {
		x -= fringe;
		float e = min(x, y);
		if (e < 0.08 || (e > 0.5 && e < 0.56)) {
			c = accent;
		} else if (e < 0.5) {
			c = border;
			vec2 q = vec2(fract((x < y ? m.y : m.x) * 2.5) - 0.5, (e - 0.29) * 4.0);
			float diamond = step(abs(q.x) + abs(q.y) * 0.6, 0.3) - step(abs(q.x) + abs(q.y) * 0.6, 0.18);
			c = mix(c, accent * 0.9, diamond);
		} else {
			c = field;
			vec2 cpos = (m - size * 0.5) / vec2(size.y * 0.55, size.y * 0.32);
			float r = abs(cpos.x) + abs(cpos.y);
			c = mix(c, border, step(r, 1.0) - step(r, 0.82));
			c = mix(c, accent * 0.8, step(r, 0.55) - step(r, 0.45));
			c = mix(c, border, step(r, 0.2));
			vec2 g = fract(m * 1.6) - 0.5;
			float motif = step(length(g), 0.09) * step(1.1, r);
			c = mix(c, accent * 0.75, motif * 0.8);
		}
	}
	float wool = noise(m * 40.0) * 0.6 + noise(m * 9.0) * 0.4;
	c *= 0.82 + 0.3 * wool;
	ALBEDO = c;
	ROUGHNESS = 0.97;
	SPECULAR = 0.2;
}
