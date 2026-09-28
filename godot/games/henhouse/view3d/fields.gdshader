shader_type spatial;
// Henhouse Heist: the farmland under the playfield, a patchwork of golden wheat, green pasture and ploughed earth
// in rows, darker furrows, lit by the scene so the platforms' long shadows fall on it.

uniform float seed = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xz;
	// fields: a skewed grid of plots
	vec2 g = vec2(p.x * 0.11 + p.y * 0.03, p.y * 0.18);
	vec2 id = floor(g + vec2(noise(p * 0.05) * 0.6, 0.0));
	float h = hash(id + seed);
	vec3 wheat = vec3(0.7, 0.5, 0.2);
	vec3 pasture = vec3(0.26, 0.44, 0.13);
	vec3 earth = vec3(0.45, 0.3, 0.18);
	vec3 lush = vec3(0.38, 0.52, 0.15);
	vec3 col = h < 0.35 ? wheat : (h < 0.65 ? pasture : (h < 0.82 ? lush : earth));
	// rows across each plot, at the plot's own angle
	float ang = hash(id + 3.1) * 3.14;
	vec2 dir = vec2(cos(ang), sin(ang));
	float rows = sin(dot(p, dir) * 9.0) * 0.5 + 0.5;
	col *= 0.82 + 0.25 * rows;
	// hedges between plots
	vec2 f = fract(g + vec2(noise(p * 0.05) * 0.6, 0.0));
	float hedge = smoothstep(0.03, 0.0, min(min(f.x, 1.0 - f.x) * 1.6, min(f.y, 1.0 - f.y)));
	col = mix(col, vec3(0.16, 0.28, 0.1), hedge * 0.85);
	col *= 0.85 + 0.3 * noise(p * 1.7);
	// the farmyard just behind the playfield: trodden grass, a dirt track across
	float yard = smoothstep(-40.0, -32.0, p.y);
	vec3 grass = mix(vec3(0.26, 0.46, 0.12), vec3(0.4, 0.58, 0.16), noise(p * 0.9)) * (0.8 + 0.35 * noise(p * 6.0));
	float track = smoothstep(1.4, 0.6, abs(p.y + 12.0 + sin(p.x * 0.15) * 1.6));
	grass = mix(grass, vec3(0.55, 0.4, 0.26) * (0.85 + 0.3 * noise(p * 4.0)), track * 0.85);
	col = mix(col, grass, yard);
	ALBEDO = col;
	ROUGHNESS = 0.92;
}
