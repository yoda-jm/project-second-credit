shader_type spatial;
// Fizzlings backdrop: deep water tinted by the level, bright towards the rippling surface, with a far skyline of
// giant toys lost in the haze, soft caustics and a glow where the light comes in.

render_mode unshaded, fog_disabled;

uniform vec3 tint : source_color = vec3(0.95, 0.55, 0.7);
uniform float time_s = 0.0;
uniform vec2 size = vec2(64.0, 40.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float box(vec2 p, vec2 b, float r) { vec2 d = abs(p) - b + r; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r; }

// giant toys far away: stacked blocks, balls and the odd tower, one per 5-unit cell
float skyline(vec2 q) {
	float d = 1e9;
	float cell = 5.0;
	float ci = floor(q.x / cell);
	for (int k = -1; k <= 1; k++) {
		float c = ci + float(k);
		float h = hash(vec2(c, 3.1));
		vec2 base = vec2((c + 0.5) * cell + (hash(vec2(c, 7.7)) - 0.5) * 2.0, -15.0);
		if (h < 0.45) {
			float s = 1.6 + hash(vec2(c, 1.3)) * 1.4;
			d = min(d, box(q - base - vec2(0.0, s), vec2(s), 0.3));
			if (h < 0.25) d = min(d, box(q - base - vec2(0.4, s * 2.0 + s * 0.7), vec2(s * 0.7), 0.25));
		} else if (h < 0.7) {
			float r = 1.8 + hash(vec2(c, 2.9)) * 1.5;
			d = min(d, length(q - base - vec2(0.0, r)) - r);
		} else {
			float t = 5.0 + hash(vec2(c, 4.4)) * 5.0;
			d = min(d, box(q - base - vec2(0.0, t * 0.5), vec2(0.9, t * 0.5), 0.4));
			d = min(d, length(q - base - vec2(0.0, t + 0.6)) - 1.2);
		}
	}
	return d;
}

void fragment() {
	vec2 uv = UV;
	vec2 q = (uv - 0.5) * size * vec2(1.0, -1.0);  // local units, y up
	float up = clamp(q.y / (size.y * 0.5) * 0.5 + 0.5, 0.0, 1.0);  // 0 at the bottom, 1 at the top
	vec3 deep = mix(vec3(0.01, 0.05, 0.13), tint * 0.08, 0.3);
	vec3 shallow = mix(vec3(0.08, 0.42, 0.62), tint * 0.6, 0.22);
	vec3 col = mix(deep, shallow, smoothstep(0.1, 0.95, up));
	// the light pool where the sun comes in, top centre, gently moving
	vec2 sun = vec2(sin(time_s * 0.07) * 4.0, size.y * 0.42);
	float pool = exp(-length((q - sun) * vec2(0.06, 0.1)));
	col += vec3(0.3, 0.65, 0.8) * pool * 0.5;
	// the rippling surface near the top
	float surf = noise(vec2(q.x * 0.35 + time_s * 0.3, time_s * 0.2)) * 1.2;
	float band = smoothstep(size.y * 0.3 + surf, size.y * 0.42 + surf, q.y);
	col += vec3(0.45, 0.8, 1.0) * band * 0.3;
	// caustic shimmer
	vec2 p = q * 0.7;
	float c = noise(p + vec2(time_s * 0.4, time_s * 0.3)) * noise(p * 1.7 - vec2(time_s * 0.3, 0.0));
	col += vec3(0.4, 0.75, 0.95) * smoothstep(0.32, 0.62, c) * 0.05 * up;
	// far skyline of giant toys, hazy
	float d = skyline(q + vec2(sin(time_s * 0.05) * 0.5, 0.0));
	vec3 haze = mix(col, deep * 1.4 + tint * 0.05, 0.75);
	col = mix(col, haze, smoothstep(0.3, -0.3, d));
	col += vec3(0.3, 0.6, 0.8) * exp(-abs(d) * 4.0) * 0.12 * smoothstep(-1.0, 0.5, d);  // lit edges
	// soft grain so the gradient never bands
	col += (hash(q * 13.0 + time_s) - 0.5) * 0.012;
	ALBEDO = pow(max(col, vec3(0.0)), vec3(2.2));  // the colours above are picked in sRGB
}
