// Nova Wardens: the post's flag, stirring in the night wind. UV.x runs from the pole (0) to the fly (1); the cloth
// ripples more towards the fly and droops a little when the wind drops. The colour is the vertex colour; lit by the
// moon, with some light through it from behind. On `clock`.
shader_type spatial;
render_mode cull_disabled;

uniform float clock = 0.0;
uniform float wind = 1.0;

float wave(float u, float v) {
	float gust = 0.7 + 0.3 * sin(clock * 0.37) * sin(clock * 0.23 + 1.0);
	return (sin(u * 6.5 - clock * 4.6 + v * 1.2) * 0.13 + sin(u * 13.0 - clock * 7.9 + v * 2.0) * 0.035)
			* u * gust * wind;
}

void vertex() {
	float u = UV.x;
	float v = UV.y;
	float w = wave(u, v);
	float e = 0.02;
	float dwdu = (wave(u + e, v) - w) / e;
	VERTEX.z += w;
	VERTEX.y -= u * u * 0.1 * (1.2 - 0.5 * sin(clock * 0.37));
	NORMAL = normalize(vec3(-dwdu / 1.9, 0.0, 1.0));
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ROUGHNESS = 0.85;
	BACKLIGHT = COLOR.rgb * 0.35;
	EMISSION = COLOR.rgb * 0.05;
}
