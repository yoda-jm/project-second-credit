shader_type spatial;
// Fizzlings: a nearer row of toy silhouettes (blocks, marbles, a crane, spinning tops) between the far water and
// the kelp, tinted by the level, their tops caught by the light. Transparent where there is nothing.

render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 tint : source_color = vec3(0.95, 0.55, 0.7);
uniform vec3 water : source_color = vec3(0.05, 0.2, 0.35);
uniform float time_s = 0.0;
uniform vec2 size = vec2(48.0, 16.0);
uniform float seed = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float box(vec2 p, vec2 b, float r) { vec2 d = abs(p) - b + r; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r; }

float shapes(vec2 q, out float kind) {
	float d = 1e9;
	kind = 0.0;
	float cell = 3.2;
	float ci = floor(q.x / cell);
	for (int k = -1; k <= 1; k++) {
		float c = ci + float(k) + seed * 17.0;
		float h = hash(vec2(c, 5.3));
		vec2 base = vec2((ci + float(k) + 0.5) * cell + (hash(vec2(c, 9.1)) - 0.5) * 1.2, -size.y * 0.5);
		float e = 1e9;
		if (h < 0.5) {  // a stack of blocks
			float s = 0.7 + hash(vec2(c, 1.7)) * 0.6;
			e = box(q - base - vec2(0.0, s), vec2(s), 0.12);
			float s2 = s * (0.55 + hash(vec2(c, 2.2)) * 0.3);
			if (h < 0.35) e = min(e, box(q - base - vec2((hash(vec2(c, 6.6)) - 0.5) * s, s * 2.0 + s2), vec2(s2), 0.1));
		} else if (h < 0.75) {  // a marble or a ball
			float r = 0.6 + hash(vec2(c, 3.3)) * 0.9;
			e = length(q - base - vec2(0.0, r)) - r;
		} else {  // a spinning top
			vec2 t = q - base - vec2(0.0, 1.2);
			e = max(length(t * vec2(1.0, 1.6)) - 1.0, -t.y - 0.9);
			e = min(e, box(t - vec2(0.0, 0.8), vec2(0.12, 0.5), 0.05));
		}
		if (e < d) { d = e; kind = h; }
	}
	return d;
}

void fragment() {
	vec2 q = (UV - 0.5) * size * vec2(1.0, -1.0);
	float kind;
	float d = shapes(q, kind);
	float inside = smoothstep(0.04, -0.04, d);
	float up = clamp((q.y + size.y * 0.5) / size.y, 0.0, 1.0);
	vec3 base = mix(water * 0.7, tint * 0.28 + water * 0.4, 0.5 + 0.4 * (kind - 0.5));
	// light on the top edges, darker towards the sand
	float edge = smoothstep(-0.35, 0.0, d);
	vec3 col = base * (0.6 + up * 0.8) + vec3(0.35, 0.7, 0.9) * edge * 0.35;
	// a soft glow around each silhouette so they separate from the water
	float glow = exp(-max(d, 0.0) * 3.0) * (1.0 - inside) * 0.18;
	ALBEDO = pow(max(mix(vec3(0.3, 0.6, 0.8), col, inside), vec3(0.0)), vec3(2.2));
	ALPHA = clamp(inside * 0.92 + glow, 0.0, 1.0) * smoothstep(size.y * 0.5, size.y * 0.3, q.y);
}
