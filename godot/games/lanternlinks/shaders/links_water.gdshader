// Lantern Links garden water: a still pond (or the ravine's stream). Two scrolling ripple layers for the normal,
// a deep teal body that shows the sky and the lanterns in it (screen-space reflections do the rest), a brighter
// fresnel rim, and a slow current for streams (flow). Rings spread where the ball goes in (splash_*).
shader_type spatial;
render_mode cull_back, specular_schlick_ggx;

uniform vec3 deep : source_color = vec3(0.04, 0.16, 0.17);
uniform vec3 shallow : source_color = vec3(0.12, 0.36, 0.34);
uniform vec3 sky_tint : source_color = vec3(1.0, 0.75, 0.5);   // the sky it mirrors at grazing angles
uniform float flow = 0.0;
uniform vec3 splash_pos = vec3(0.0, -100.0, 0.0);
uniform float splash_t = 10.0;
varying vec3 wpos;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float height(vec2 p, float t) {
	float h = vnoise(p * 3.0 + vec2(t * 0.15 + flow * t, t * 0.1)) * 0.5
		+ vnoise(p * 7.0 - vec2(t * 0.2, -t * 0.12 - flow * t * 2.0)) * 0.3;
	float d = distance(p, splash_pos.xz);
	float ring = sin(d * 40.0 - splash_t * 14.0) * exp(-splash_t * 1.5) * smoothstep(splash_t * 0.9 + 0.1, splash_t * 0.9 - 0.2, d);
	return h + ring * 0.6;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float t = TIME;
	vec2 p = wpos.xz;
	float e = 0.01;
	float h0 = height(p, t);
	float hx = height(p + vec2(e, 0.0), t) - h0;
	float hz = height(p + vec2(0.0, e), t) - h0;
	NORMAL_MAP = normalize(vec3(-hx * 3.0, -hz * 3.0, 1.0)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	ALBEDO = mix(mix(deep, shallow, 0.3 + 0.4 * h0), sky_tint * 0.6, fres * 0.7);
	ROUGHNESS = 0.04;
	METALLIC = 0.0;
	SPECULAR = 0.9;
}
