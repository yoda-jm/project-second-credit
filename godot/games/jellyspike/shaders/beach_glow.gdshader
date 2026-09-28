// Jelly Spike lights: paper lanterns and glowing embers. Lit like paper by day (energy 0); from dusk the vertex colour
// glows (HDR emission feeds the bloom), each lantern flickering a little on its own (cells of world space).
shader_type spatial;
render_mode cull_disabled;

uniform float energy = 0.0;
uniform float flicker = 0.15;
uniform float cell = 0.6;
uniform float pulse = 0.0;
uniform vec3 night_tint : source_color = vec3(1.0);

varying vec3 wpos;

float hash3(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float h = hash3(floor(wpos / cell + 0.001));
	float k = 1.0 + flicker * 0.3 * (sin(TIME * 11.0 + h * 40.0) + sin(TIME * 6.7 + h * 17.0));
	k *= 1.0 + pulse * 0.4 * sin(TIME * 1.7 + wpos.x * 2.3 + wpos.z * 1.1);
	ALBEDO = COLOR.rgb;
	ROUGHNESS = 0.7;
	BACKLIGHT = COLOR.rgb * 0.4;
	EMISSION = COLOR.rgb * night_tint * energy * k;
}
