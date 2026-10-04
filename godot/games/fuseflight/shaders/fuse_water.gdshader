// Fuseflight night water: dark and glossy so the light streaks and the fireworks' reflections read on it. A gentle
// swell and ripples (their normals fade with distance so the far water is calm), the sky's colour on it by fresnel,
// and lamps and bursts glinting on it (it is lit, so the backdrop's flash lights shine on it). Vertex colour R marks
// the shallows (a little lighter, with lace along the shore).
shader_type spatial;
render_mode specular_schlick_ggx;

uniform vec3 deep_col : source_color = vec3(0.01, 0.02, 0.05);
uniform vec3 far_col : source_color = vec3(0.04, 0.05, 0.1);
uniform vec3 sky_col : source_color = vec3(0.15, 0.15, 0.3);
uniform vec3 shallow_col : source_color = vec3(0.04, 0.08, 0.1);
uniform vec3 foam_col : source_color = vec3(0.5, 0.55, 0.7);
uniform float wave_height = 0.06;
uniform float ripple = 1.0;
uniform float gloss = 0.05;
uniform float far_dist = 120.0;

varying vec3 wpos;
varying float shallow;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

vec3 waves(vec2 p, float t) {
	vec3 r = vec3(0.0);
	vec2 dirs[4] = {vec2(0.2, 1.0), vec2(0.7, 0.8), vec2(-0.5, 0.9), vec2(1.0, 0.2)};
	float len[4] = {9.0, 5.3, 3.1, 1.9};
	for (int i = 0; i < 4; i++) {
		vec2 dd = normalize(dirs[i]);
		float k = 6.2831 / len[i];
		float w = sqrt(9.8 * k) * 0.45;
		float a = len[i] / 9.0;
		float ph = dot(dd, p) * k + t * w;
		r.x += a * sin(ph);
		r.yz += a * k * cos(ph) * dd;
	}
	return r;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	shallow = COLOR.r;
	VERTEX.y += waves(wpos.xz, TIME).x * wave_height;
}

void fragment() {
	float t = TIME;
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	float fade = 1.0 / (1.0 + dist * 0.03);
	vec3 w = waves(wpos.xz, t);
	vec2 g = w.yz * wave_height;
	vec2 rp = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * wpos.xz * 1.3;
	float e = 0.15;
	float n0 = vnoise(rp + vec2(t * 0.5, t * 0.25));
	float nx = vnoise(rp + vec2(e, 0.0) + vec2(t * 0.5, t * 0.25));
	float nz = vnoise(rp + vec2(0.0, e) + vec2(t * 0.5, t * 0.25));
	vec2 rp2 = mat2(vec2(0.6, -0.8), vec2(0.8, 0.6)) * wpos.xz * 3.1 - vec2(t * 0.8, t * 0.35);
	float m0 = vnoise(rp2), mx = vnoise(rp2 + vec2(e, 0.0)), mz = vnoise(rp2 + vec2(0.0, e));
	g += (vec2(nx - n0, nz - n0) * 0.1 + vec2(mx - m0, mz - m0) * 0.05) / e * ripple;
	g *= fade;
	vec3 nw = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	float far = smoothstep(15.0, far_dist, dist);
	vec3 col = mix(deep_col, far_col, far);
	col = mix(col, shallow_col, shallow * 0.8);
	float fr = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	vec3 sheen = sky_col * fr * 0.6;
	float lace = smoothstep(0.7, 0.95, shallow) * smoothstep(0.35, 0.6, vnoise(wpos.xz * 2.2 + vec2(t * 0.3, -t * 0.2)));
	ALBEDO = mix(col, foam_col, lace * 0.5);
	EMISSION = sheen;
	ROUGHNESS = gloss + far * 0.04;
	SPECULAR = 0.7;
	METALLIC = 0.0;
}
