// Brassflow workshop wood (bench top, floor, shelves, legs): planks in world space with grain, knots and a satin
// varnish. Planks run along X (or along Z with along_z), the side faces take the grain as end/edge grain.
shader_type spatial;

uniform vec3 tint_a : source_color = vec3(0.42, 0.23, 0.11);
uniform vec3 tint_b : source_color = vec3(0.30, 0.15, 0.07);
uniform float plank_width = 1.4;
uniform float plank_length = 9.0;
uniform bool along_z = false;
uniform float varnish = 0.35;   // roughness of the varnish
uniform float wear = 0.0;       // lighter, rougher patches (the floor)

varying vec3 wpos;
varying vec3 wnrm;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = abs(wnrm);
	// u along the grain, v across it
	vec2 uv = along_z ? vec2(wpos.z, wpos.x) : vec2(wpos.x, wpos.z);
	if (n.y < 0.6) {
		uv = n.x > n.z ? vec2(wpos.z, wpos.y) : vec2(wpos.x, wpos.y);
		if (along_z && n.x > n.z) {
			uv = vec2(wpos.z, wpos.y);
		}
	}
	float row = floor(uv.y / plank_width);
	float off = hash(vec2(row, 1.7)) * plank_length;
	float col_i = floor((uv.x + off) / plank_length);
	vec2 id = vec2(row, col_i);
	float across = fract(uv.y / plank_width);
	float along = fract((uv.x + off) / plank_length);
	float seam = smoothstep(0.0, 0.012, across) * smoothstep(1.0, 0.988, across)
		* smoothstep(0.0, 0.002, along) * smoothstep(1.0, 0.998, along);
	float h = hash(id);
	// grain: stretched noise rings warped along the plank
	float w = vnoise(vec2(uv.x * 0.35, uv.y * 3.0 + h * 40.0)) * 2.0;
	float rings = sin((uv.y * 14.0 + w * 3.0 + h * 20.0) * 3.14159);
	float fine = vnoise(vec2(uv.x * 2.0, uv.y * 60.0));
	float g = 0.5 + 0.25 * rings + 0.25 * fine;
	// a knot now and then
	vec2 kp = vec2(fract((uv.x + off) / plank_length) * plank_length, across * plank_width);
	vec2 kc = vec2(hash(id + 3.1) * plank_length, (0.3 + 0.4 * hash(id + 5.7)) * plank_width);
	float kd = length((kp - kc) * vec2(0.5, 1.6));
	float knot = hash(id + 9.9) < 0.35 ? (1.0 - smoothstep(0.03, 0.16, kd)) : 0.0;
	vec3 col = mix(tint_b, tint_a, g) * (0.85 + 0.3 * h);
	col = mix(col, tint_b * 0.5, knot * 0.8);
	float worn = wear * smoothstep(0.55, 0.8, vnoise(uv * 0.6));
	col = mix(col, col * 1.35 + 0.03, worn);
	ALBEDO = col * mix(0.45, 1.0, seam);
	ROUGHNESS = mix(varnish + 0.15 * fine, 0.8, worn);
	SPECULAR = 0.45;
}
