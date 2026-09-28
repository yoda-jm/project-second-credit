shader_type spatial;
// Henhouse Heist: a band of soft evening clouds on a far quad, drifting slowly. Lit from the low sun's side
// (golden edges), rosy underneath, fading at the quad's edges. Transparent where the sky shows.

render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform float time_s = 0.0;
uniform float drift = 0.004;
uniform float seed = 0.0;
uniform float cover = 0.52;
uniform vec2 sun_uv = vec2(0.72, 0.1);
uniform vec3 lit : source_color = vec3(1.0, 0.86, 0.62);
uniform vec3 shade : source_color = vec3(0.78, 0.5, 0.52);
uniform vec3 far_tint : source_color = vec3(0.98, 0.72, 0.55);
uniform float opacity = 0.9;
uniform vec2 stretch = vec2(3.2, 1.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < 5; i++) {
		v += a * noise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

void fragment() {
	vec2 uv = UV;
	vec2 p = vec2(uv.x * stretch.x + time_s * drift + seed * 13.1, uv.y * stretch.y * 2.2 + seed * 3.7);
	float n = fbm(p * vec2(1.0, 2.6));
	// thicker in the middle of the band, thin at its top and bottom
	float band = smoothstep(0.0, 0.35, uv.y) * smoothstep(1.0, 0.55, uv.y);
	float d = smoothstep(cover, cover + 0.22, n * (0.55 + 0.6 * band));
	// light: the side towards the sun is brighter, the underside rosy
	float n2 = fbm(p * vec2(1.0, 2.6) + normalize(sun_uv - uv) * 0.08);
	float light = clamp(0.5 + (n2 - n) * 6.0 + (1.0 - uv.y) * 0.25, 0.0, 1.0);
	vec3 col = mix(shade, lit, light);
	float near_sun = exp(-length((uv - sun_uv) * vec2(1.6, 3.0)) * 3.0);
	col += vec3(1.0, 0.75, 0.4) * near_sun * 0.7 * d;
	col = mix(col, far_tint, 0.2);
	float edge = smoothstep(0.0, 0.12, uv.x) * smoothstep(1.0, 0.88, uv.x) * smoothstep(0.0, 0.1, uv.y) * smoothstep(1.0, 0.85, uv.y);
	ALBEDO = col;
	ALPHA = d * edge * opacity;
}
