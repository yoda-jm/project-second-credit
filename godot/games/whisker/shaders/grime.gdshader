shader_type spatial;
render_mode unshaded, blend_mul, depth_draw_never, shadows_disabled, fog_disabled, cull_disabled;
// Weathering laid over the building's brick wall: soot near the ground and under the cornice, rain streaks
// running down from each window sill, and blotches. Multiplies what is behind it (world space: x along the wall).

uniform vec4 windows_x = vec4(4.0, 9.0, 14.0, 19.0);
uniform vec3 rows_y = vec3(6.3, 8.4, 10.5);
uniform float top = 13.2;

float hash(float n) { return fract(sin(n) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash(dot(i, vec2(1.0, 57.0)));
	float b = hash(dot(i + vec2(1, 0), vec2(1.0, 57.0)));
	float c = hash(dot(i + vec2(0, 1), vec2(1.0, 57.0)));
	float d = hash(dot(i + vec2(1, 1), vec2(1.0, 57.0)));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xy;
	float dirt = 0.0;
	dirt += 0.45 * smoothstep(2.5, 0.0, p.y);
	dirt += 0.35 * smoothstep(top - 1.8, top, p.y);
	dirt += 0.18 * smoothstep(0.45, 0.8, noise(p * 0.9)) + 0.1 * noise(p * 3.0);
	for (int i = 0; i < 4; i++) {
		float dx = abs(p.x - windows_x[i]);
		for (int j = 0; j < 3; j++) {
			float below = rows_y[j] - 0.45 - p.y;
			float streak = smoothstep(0.85, 0.5, dx) * step(0.0, below) * exp(-below * 0.9);
			streak *= 0.5 + 0.5 * noise(vec2(p.x * 9.0, p.y * 0.8));
			dirt += 0.5 * streak;
		}
	}
	ALBEDO = vec3(1.0 - clamp(dirt, 0.0, 0.7)) * vec3(1.0, 0.98, 0.96);
}
