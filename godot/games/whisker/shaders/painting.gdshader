shader_type spatial;
// Paintings for the rooms' picture frames, drawn procedurally on the canvas (UV 0-1, v down) with a little brush
// texture: 0 a landscape at dusk, 1 a vase of flowers, 2 a portrait of a ginger cat, 3 a fish on a plate.

uniform int style = 0;

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1, 0)), f.x), mix(hash2(i + vec2(0, 1)), hash2(i + vec2(1, 1)), f.x), f.y);
}
float disc(vec2 p, vec2 c, vec2 r) { return smoothstep(1.0, 0.92, length((p - c) / r)); }

void fragment() {
	vec2 uv = UV;
	float y = 1.0 - uv.y;
	float stroke = noise(vec2(uv.x * 40.0, uv.y * 140.0)) * 0.5 + noise(uv * 60.0) * 0.5;
	vec3 c;
	if (style == 0) {
		c = mix(vec3(0.98, 0.62, 0.34), vec3(0.25, 0.28, 0.52), smoothstep(0.35, 1.0, y));
		c = mix(c, vec3(1.0, 0.88, 0.6), disc(uv, vec2(0.66, 0.5), vec2(0.07, 0.1)));
		float h1 = 0.45 + 0.07 * sin(uv.x * 6.0 + 1.0) + 0.03 * sin(uv.x * 17.0);
		c = mix(c, vec3(0.42, 0.36, 0.5), step(y, h1));
		float h2 = 0.3 + 0.06 * sin(uv.x * 4.0 + 2.5) + 0.015 * sin(uv.x * 31.0);
		c = mix(c, vec3(0.22, 0.32, 0.22), step(y, h2));
		for (int i = 0; i < 3; i++) {  // cypresses
			float tx = 0.18 + float(i) * 0.09;
			float th = 0.55 - float(i) * 0.06;
			float w = 0.035 * (1.0 - smoothstep(0.25, th, y));
			c = mix(c, vec3(0.1, 0.18, 0.12), step(abs(uv.x - tx), w) * step(0.25, y) * step(y, th));
		}
		c = mix(c, vec3(0.85, 0.55, 0.35), step(y, 0.14) * (0.5 + 0.5 * sin(uv.x * 50.0)) * 0.3);
	} else if (style == 1) {
		c = mix(vec3(0.16, 0.2, 0.14), vec3(0.3, 0.32, 0.22), y);
		c = mix(c, vec3(0.45, 0.28, 0.16), step(y, 0.2));
		c = mix(c, vec3(0.3, 0.5, 0.65), disc(uv, vec2(0.5, 0.68), vec2(0.15, 0.17)));
		c = mix(c, vec3(0.3, 0.5, 0.65), step(abs(uv.x - 0.5), 0.07) * step(0.5, uv.y) * step(uv.y, 0.56));
		vec3 cols[4] = vec3[](vec3(0.9, 0.25, 0.3), vec3(1.0, 0.85, 0.3), vec3(0.95, 0.95, 0.9), vec3(0.75, 0.35, 0.8));
		for (int i = 0; i < 9; i++) {
			float a = float(i) * 0.7 - 2.8;
			vec2 fc = vec2(0.5 + sin(a) * (0.12 + 0.1 * hash2(vec2(float(i)))), 0.36 - cos(a) * 0.14 - 0.08 * hash2(vec2(float(i), 2.0)));
			c = mix(c, vec3(0.2, 0.4, 0.2), step(abs(uv.x - mix(0.5, fc.x, (0.5 - uv.y) / (0.5 - fc.y))), 0.006) * step(fc.y, uv.y) * step(uv.y, 0.5));
			c = mix(c, cols[i % 4], disc(uv, fc, vec2(0.07, 0.055)));
		}
	} else if (style == 2) {
		c = mix(vec3(0.12, 0.22, 0.2), vec3(0.2, 0.32, 0.28), disc(uv, vec2(0.5, 0.45), vec2(0.5, 0.5)));
		c = mix(c, vec3(0.3, 0.2, 0.3), step(0.82, uv.y));
		vec3 fur = vec3(0.92, 0.55, 0.22) * (0.85 + 0.2 * sin(uv.x * 40.0 + uv.y * 10.0));
		c = mix(c, fur, disc(uv, vec2(0.5, 0.8), vec2(0.34, 0.2)));  // shoulders
		for (float s = -1.0; s <= 1.0; s += 2.0) {  // ears
			vec2 e = uv - vec2(0.5 + s * 0.19, 0.24);
			c = mix(c, fur, step(abs(e.x) * 1.6 - e.y * 1.0, 0.07) * step(-0.1, e.y) * step(e.y, 0.1));
		}
		c = mix(c, fur, disc(uv, vec2(0.5, 0.47), vec2(0.27, 0.23)));
		c = mix(c, vec3(0.98, 0.93, 0.85), disc(uv, vec2(0.5, 0.56), vec2(0.13, 0.1)));  // muzzle
		for (float s = -1.0; s <= 1.0; s += 2.0) {
			c = mix(c, vec3(0.45, 0.75, 0.3), disc(uv, vec2(0.5 + s * 0.1, 0.44), vec2(0.045, 0.04)));
			c = mix(c, vec3(0.05), disc(uv, vec2(0.5 + s * 0.1, 0.44), vec2(0.012, 0.035)));
		}
		c = mix(c, vec3(0.85, 0.45, 0.5), disc(uv, vec2(0.5, 0.52), vec2(0.025, 0.018)));
		c = mix(c, vec3(0.75, 0.15, 0.2), disc(uv, vec2(0.5, 0.72), vec2(0.18, 0.03)));  // collar
	} else {
		c = mix(vec3(0.25, 0.18, 0.14), vec3(0.4, 0.3, 0.22), y);
		c = mix(c, vec3(0.9, 0.9, 0.85), disc(uv, vec2(0.5, 0.62), vec2(0.4, 0.2)));
		c = mix(c, vec3(0.3, 0.45, 0.65), disc(uv, vec2(0.5, 0.62), vec2(0.3, 0.14)) * 0.3);
		c = mix(c, vec3(0.95, 0.5, 0.15), disc(uv, vec2(0.46, 0.6), vec2(0.2, 0.08)));
		vec2 t = uv - vec2(0.7, 0.6);
		c = mix(c, vec3(0.95, 0.6, 0.2), step(abs(t.y), t.x * 0.9) * step(t.x, 0.12));
		c = mix(c, vec3(0.05), disc(uv, vec2(0.33, 0.58), vec2(0.015, 0.02)));
	}
	c *= 0.88 + 0.22 * stroke;
	c *= 1.0 - 0.35 * smoothstep(0.35, 0.75, length(uv - 0.5));  // a darker varnish at the edges
	ALBEDO = c;
	ROUGHNESS = 0.55;
	SPECULAR = 0.35;
}
