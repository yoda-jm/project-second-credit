// Tinplate Turbo road: a printed-tin road, dark grey with a fine grain and a lacquer sheen, white edge lines, a dashed
// centre line, red-and-white kerbs at the very edges, and the chequered start line. UV.x runs 0..1 across, UV.y is
// metres along. Our own shader (CC BY-SA 4.0).
shader_type spatial;

uniform vec4 road_col : source_color = vec4(0.22, 0.22, 0.25, 1.0);
uniform vec4 line_col : source_color = vec4(0.95, 0.93, 0.85, 1.0);
uniform vec4 kerb_a : source_color = vec4(0.85, 0.15, 0.12, 1.0);
uniform float start_y = 0.0;
uniform float night = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	float x = UV.x;
	float y = UV.y;
	vec3 col = road_col.rgb * (0.9 + 0.12 * hash(floor(vec2(x * 60.0, y * 8.0))));
	// tar patches, hairline cracks and the rubbered line where the cars run
	float patch = noise(vec2(x * 3.0, y * 0.25));
	col *= 0.9 + 0.18 * smoothstep(0.55, 0.8, patch);
	float crack = abs(noise(vec2(x * 9.0, y * 1.1)) - 0.5);
	col *= 1.0 - 0.35 * smoothstep(0.02, 0.0, crack) * step(0.15, x) * step(x, 0.85);
	col *= 1.0 - 0.12 * smoothstep(0.32, 0.45, x) * smoothstep(0.68, 0.55, x);
	// kerbs
	float kerb = step(x, 0.07) + step(0.93, x);
	float stripe = step(0.5, fract(y * 0.8));
	col = mix(col, mix(kerb_a.rgb, vec3(0.95), stripe), kerb);
	// edge lines and the dashed centre
	float edge = (smoothstep(0.075, 0.085, x) - smoothstep(0.1, 0.11, x)) + (smoothstep(0.89, 0.9, x) - smoothstep(0.915, 0.925, x));
	float dash = (smoothstep(0.485, 0.49, x) - smoothstep(0.51, 0.515, x)) * step(0.55, fract(y * 0.35));
	col = mix(col, line_col.rgb, clamp(edge + dash, 0.0, 1.0) * (1.0 - kerb));
	// the start line: a chequer band
	float d = abs(y - start_y);
	if (d < 0.6) {
		float chk = mod(floor(x * 12.0) + floor((y - start_y) * 3.4), 2.0);
		col = mix(col, vec3(chk * 0.95 + 0.03), (1.0 - kerb));
	}
	ALBEDO = col;
	ROUGHNESS = 0.38;
	METALLIC = 0.25;
	SPECULAR = 0.6;
	EMISSION = line_col.rgb * clamp(edge + dash, 0.0, 1.0) * night * 0.4;
}
