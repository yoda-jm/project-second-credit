// Ridgefire smoke: the volcano's plume, steam where lava meets the sea, smoke from a chimney. Soft puffs (one
// MultiMesh instance each, worked out from the backdrop's clock like ridge_rise: origin where it starts, basis X its
// size; INSTANCE_CUSTOM = (phase, period s, rise m, growth); COLOR its tint) that billow up, bend with the wind and
// spread, lit from below by the fire (glow_col, strongest near the source) and by the moon from one side; lightning
// flickers in them (flash). Blended, camera-facing.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float clock = 0.0;
uniform vec3 wind = vec3(-60.0, 0.0, 0.0);   // drift in m per period, growing with the height
uniform vec3 glow_col : source_color = vec3(1.0, 0.35, 0.08);
uniform float glow_reach = 0.35;             // share of the rise the fire lights
uniform vec3 shade_col : source_color = vec3(0.05, 0.045, 0.05);
uniform vec3 lit_col : source_color = vec3(0.25, 0.25, 0.3);
uniform float opacity = 0.75;
uniform float flash = 0.0;
uniform vec3 flash_pos = vec3(0.0);

varying vec2 v_uv;
varying float v_alpha;
varying float v_u;
varying vec3 v_col;
varying float v_seed;
varying vec3 v_wp;
varying vec3 v_center;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	vec3 base = MODEL_MATRIX[3].xyz;
	float size = length(MODEL_MATRIX[0].xyz);
	float phase = INSTANCE_CUSTOM.x;
	float period = max(INSTANCE_CUSTOM.y, 0.1);
	float rise = INSTANCE_CUSTOM.z;
	float grow = INSTANCE_CUSTOM.w;
	float u = fract(clock / period + phase);
	float cyc = floor(clock / period + phase);
	float s = fract(sin(phase * 91.7 + cyc * 13.1) * 43758.5);
	float h = rise * (1.0 - pow(1.0 - u, 1.6));
	vec3 p = base + vec3((s - 0.5) * size * 0.8, h, (fract(s * 7.3) - 0.5) * size * 0.5) + wind * u * u;
	size *= 1.0 + grow * u;
	vec3 right = INV_VIEW_MATRIX[0].xyz;
	vec3 up = INV_VIEW_MATRIX[1].xyz;
	float an = s * 6.2831 + u * (s - 0.5) * 1.5;
	vec2 rv = vec2(cos(an) * VERTEX.x - sin(an) * VERTEX.y, sin(an) * VERTEX.x + cos(an) * VERTEX.y);
	vec3 wp = p + (right * rv.x + up * rv.y) * size;
	v_uv = UV;
	v_u = u;
	v_seed = s;
	v_alpha = smoothstep(0.0, 0.1, u) * (1.0 - smoothstep(0.55, 1.0, u));
	v_col = COLOR.rgb;
	v_wp = wp;
	v_center = p;
	VERTEX = (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
}

void fragment() {
	vec2 p = v_uv * 2.0 - 1.0;
	float r = length(p);
	float n = vnoise(p * 2.5 + v_seed * 17.0) * 0.6 + vnoise(p * 5.0 + v_seed * 5.0) * 0.4;
	float a = smoothstep(1.0, 0.35, r + (n - 0.5) * 0.55);
	// lit from below near the source, from the side higher up
	float below = clamp(-p.y * 0.5 + 0.5, 0.0, 1.0);
	float fire = (1.0 - smoothstep(0.0, glow_reach, v_u)) * (0.4 + 0.6 * below);
	vec3 col = mix(shade_col, lit_col, clamp(0.35 + 0.5 * (p.x * 0.4 + p.y * 0.6) + n * 0.3, 0.0, 1.0)) * v_col;
	col += glow_col * fire * (0.6 + 0.6 * n);
	if (flash > 0.0) {
		float d = length(v_center - flash_pos);
		col += vec3(0.75, 0.75, 1.0) * flash * exp(-d / 120.0) * (0.5 + n);
	}
	ALBEDO = col;
	ALPHA = clamp(a * v_alpha * opacity, 0.0, 1.0);
}
