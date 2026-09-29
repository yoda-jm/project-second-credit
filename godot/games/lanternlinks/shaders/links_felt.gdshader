// Lantern Links felt: a short-pile putting carpet. Fine fibre noise in the colour and the normal, soft mowing
// stripes across the lane, a slight sheen at grazing angles, and round holes cut for the cup and pipe mouths.
shader_type spatial;
render_mode cull_back;

uniform vec3 felt_a : source_color = vec3(0.09, 0.36, 0.17);
uniform vec3 felt_b : source_color = vec3(0.12, 0.43, 0.2);
uniform vec4 holes[5];
varying vec3 wpos;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xz;
	for (int i = 0; i < 5; i++) {
		if (holes[i].z > 0.0 && distance(p, holes[i].xy) < holes[i].z) {
			discard;
		}
	}
	// mowing stripes, 0.5 m wide, very soft
	float stripe = smoothstep(0.35, 0.65, 0.5 + 0.5 * sin(p.x * 6.2832 + 0.3 * sin(p.y * 1.3)));
	vec3 c = mix(felt_a, felt_b, stripe * 0.6);
	// fibres: fine noise at two scales
	float n1 = vnoise(p * 180.0);
	float n2 = vnoise(p * 23.0);
	c *= 0.86 + 0.18 * n1 + 0.1 * (n2 - 0.5);
	// wear: slightly paler around the cup where everyone putts
	float wear = 0.0;
	if (holes[0].z > 0.0) {
		wear = smoothstep(0.9, 0.15, distance(p, holes[0].xy)) * 0.08;
	}
	c = mix(c, c * 1.25 + vec3(0.02, 0.03, 0.0), wear);
	ALBEDO = c;
	ROUGHNESS = 0.85 - 0.1 * stripe;
	SPECULAR = 0.3;
	// the pile's micro normal
	float e = 1.0 / 180.0;
	float nx = vnoise((p + vec2(e, 0.0)) * 180.0) - n1;
	float ny = vnoise((p + vec2(0.0, e)) * 180.0) - n1;
	NORMAL_MAP = normalize(vec3(-nx * 1.6, -ny * 1.6, 1.0)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 0.6;
	// sheen: pile catches light at grazing angles
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	BACKLIGHT = vec3(0.05, 0.12, 0.05);
	RIM = fres * 0.5;
	RIM_TINT = 0.6;
}
