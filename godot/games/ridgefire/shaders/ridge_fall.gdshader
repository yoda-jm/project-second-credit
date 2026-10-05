// Ridgefire waterfall: white water pouring down a cliff (UV.x across 0..1, UV.y down the fall in metres), streaks
// rushing down and spreading, thinner and more broken at the edges, foam thick at the foot. Lit by the scene (the
// sun and the explosions' flashes) with a little light of its own; blended over the rock behind.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform vec3 water_col : source_color = vec3(0.85, 0.92, 0.97);
uniform vec3 deep_col : source_color = vec3(0.35, 0.5, 0.58);
uniform float speed = 9.0;      // m/s
uniform float height = 50.0;    // the drop, m (the foot's foam)
uniform float self_light = 0.25;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	float t = TIME;
	float y = UV.y;
	float x = UV.x;
	float accel = y * (1.0 + y / max(height, 1.0));   // the water speeds up as it falls: the streaks stretch
	float s1 = vnoise(vec2(x * 38.0, accel * 0.22 - t * speed * 0.22));
	float s2 = vnoise(vec2(x * 90.0 + 3.0, accel * 0.5 - t * speed * 0.5));
	float streak = smoothstep(0.3, 0.8, s1 * 0.65 + s2 * 0.45);
	float edge = smoothstep(0.0, 0.18, x) * smoothstep(1.0, 0.82, x);
	float broken = smoothstep(0.25, 0.6, vnoise(vec2(x * 12.0, accel * 0.08 - t * speed * 0.08)) + edge * 0.5);
	float foot = smoothstep(height * 0.75, height, y);
	vec3 col = mix(deep_col, water_col, streak * 0.7 + 0.3 + foot * 0.4);
	ALBEDO = col;
	ROUGHNESS = 0.35;
	SPECULAR = 0.5;
	EMISSION = col * self_light;
	ALPHA = clamp((0.45 + 0.55 * streak) * broken * edge + foot * 0.6, 0.0, 0.97) * smoothstep(0.0, 1.5, y);
}
