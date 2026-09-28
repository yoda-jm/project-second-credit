shader_type sky;
// Henhouse Heist: the golden-hour sky. Deep blue-violet overhead, warm apricot at the horizon, a rosy band above it,
// the low sun's disc and glow on the right. "dusk" (0 to 1) sinks the sun and reddens everything as the bonus clock
// runs down. The sky also lights the scene (ambient), so it stays soft and warm.

uniform vec3 zenith : source_color = vec3(0.16, 0.3, 0.62);
uniform vec3 mid : source_color = vec3(0.74, 0.55, 0.66);
uniform vec3 horizon : source_color = vec3(1.0, 0.62, 0.3);
uniform vec3 ground : source_color = vec3(0.45, 0.36, 0.24);
uniform vec3 sun_dir = vec3(0.62, 0.12, -0.78);
uniform float dusk = 0.0;

void sky() {
	vec3 d = EYEDIR;
	float h = d.y;
	vec3 z = mix(zenith, vec3(0.2, 0.2, 0.46), dusk);
	vec3 m = mix(mid, vec3(0.86, 0.46, 0.5), dusk);
	vec3 hz = mix(horizon, vec3(1.0, 0.5, 0.26), dusk);
	vec3 col = mix(hz, m, smoothstep(0.0, 0.2, h));
	col = mix(col, z, smoothstep(0.16, 0.7, h));
	vec3 s = normalize(sun_dir - vec3(0.0, dusk * 0.08, 0.0));
	float c = max(dot(d, s), 0.0);
	// a wide warm glow, a tighter bloom and the disc itself
	col += vec3(1.0, 0.5, 0.2) * pow(c, 8.0) * (0.4 + dusk * 0.3);
	col += vec3(1.0, 0.75, 0.45) * pow(c, 90.0) * 0.6;
	col += vec3(1.0, 0.92, 0.7) * smoothstep(0.9993, 0.9997, c) * 3.0;
	if (h < 0.0) {
		col = mix(hz * 0.9, ground, smoothstep(0.0, -0.25, h));
	}
	COLOR = col;
}
