// Ridgefire mist: soft cards of haze lying in the valleys, steam over the sea, blowing snow over the ice (UV 0..1
// over the card; vertex colour alpha is its opacity). The haze drifts slowly and its edges are soft; it takes the
// theme's light colour (tint) and a touch of the sun's warmth on its lit side. Unshaded, blended.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 tint : source_color = vec3(0.8, 0.85, 0.95);
uniform vec3 glow_tint : source_color = vec3(1.0, 0.85, 0.7);
uniform float density = 0.6;
uniform float drift = 1.0;      // m/s along x
uniform float scale = 0.02;     // noise frequency per metre

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < 4; i++) {
		v += a * vnoise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = UV;
	float edge = smoothstep(0.0, 0.3, uv.x) * smoothstep(1.0, 0.7, uv.x) * smoothstep(0.0, 0.45, uv.y) * smoothstep(1.0, 0.55, uv.y);
	vec2 p = vec2(wpos.x - TIME * drift, wpos.y * 3.0 + wpos.z) * scale;
	float n = fbm(p + vec2(0.0, TIME * 0.01));
	float a = edge * smoothstep(0.25, 0.75, n) * density * COLOR.a;
	ALBEDO = mix(tint, glow_tint, uv.y * 0.4) * (0.85 + 0.3 * n);
	ALPHA = clamp(a, 0.0, 1.0);
}
