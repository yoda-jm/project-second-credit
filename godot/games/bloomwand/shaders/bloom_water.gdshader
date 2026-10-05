// Bloomwand water (our own, CC BY-SA 4.0), three moods: a brook (ripples running downstream, the sky on it by
// fresnel, sunlit glints), a glowing pool (light welling up from below in slow caustics, a sheen on top), and a frozen
// pond (smooth and glassy, faint cracks, frost creeping in from the banks). Vertex colour R marks the shallows (the
// banks). It is lit, so the scene's lamps and flashes shine on it. Runs on `clock`.
shader_type spatial;
render_mode specular_schlick_ggx;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 deep_col : source_color = vec3(0.05, 0.12, 0.12);
uniform vec3 shallow_col : source_color = vec3(0.2, 0.3, 0.2);
uniform vec3 sky_col : source_color = vec3(0.6, 0.75, 0.85);
uniform vec3 glow_col : source_color = vec3(0.2, 0.9, 1.0);
uniform vec3 frost_col : source_color = vec3(0.85, 0.9, 1.0);
uniform float glow = 0.0;        // the pool's light from below
uniform float ice = 0.0;         // 1: frozen
uniform vec2 flow = vec2(0.25, 1.0);
uniform float ripple = 1.0;
uniform float glints = 1.0;

varying vec3 wpos;
varying float shallow;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	shallow = COLOR.r;
}

vec2 grad(vec2 p) {
	float e = 0.12;
	float n0 = bw_noise(p), nx = bw_noise(p + vec2(e, 0.0)), nz = bw_noise(p + vec2(0.0, e));
	return vec2(nx - n0, nz - n0) / e;
}

void fragment() {
	float t = clock;
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	float fade = 1.0 / (1.0 + dist * 0.04);
	vec2 p = wpos.xz;
	vec2 g;
	if (ice > 0.5) {
		g = grad(p * 0.8) * 0.02;
	} else {
		g = grad(p * 1.4 - flow * t * 0.9) * 0.09 + grad(p * 3.3 - flow * t * 1.6 + 4.0) * 0.05;
		g += grad(vec2(p.x * 0.6, p.y * 0.25) - flow * t * 0.5) * 0.06;
	}
	g *= ripple * fade;
	vec3 nw = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	float fr = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	vec3 col = mix(deep_col, shallow_col, shallow);
	vec3 em = sky_col * fr * 0.7;
	if (glow > 0.0) {
		vec2 q = p * 0.35 + vec2(t * 0.05, -t * 0.03);
		float c1 = bw_noise(q * 2.0 + bw_noise(q * 1.3 + t * 0.1) * 2.0);
		float caust = pow(1.0 - abs(c1 * 2.0 - 1.0), 6.0);
		float well = 0.65 + 0.35 * sin(t * 0.6 + p.x * 0.3);
		em += glow_col * glow * (0.55 * (1.0 - shallow * 0.7) + 0.6 * caust) * well;
	}
	if (ice > 0.5) {
		vec2 cell = p * 0.45;
		vec2 ic = floor(cell), fc = fract(cell);
		float md = 8.0, md2 = 8.0;
		for (int y = -1; y <= 1; y++) {
			for (int x = -1; x <= 1; x++) {
				vec2 o = vec2(float(x), float(y));
				vec2 r = o + vec2(bw_hash(ic + o), bw_hash(ic + o + 7.0)) - fc;
				float d = dot(r, r);
				if (d < md) { md2 = md; md = d; } else if (d < md2) { md2 = d; }
			}
		}
		float crack = 1.0 - smoothstep(0.0, 0.035, sqrt(md2) - sqrt(md));
		float frost = smoothstep(0.3, 1.0, shallow + 0.4 * bw_fbm(p * 1.2, 3) - 0.2);
		col = mix(col, frost_col, frost);
		em += frost_col * crack * 0.12 * (1.0 - frost);
		ROUGHNESS = mix(0.06, 0.6, frost);
	} else {
		ROUGHNESS = 0.05;
		if (glints > 0.0) {
			vec2 gc = floor(p * 6.0);
			float h = bw_hash(gc + floor(t * 3.0) * 0.37);
			float sp = step(0.985, h) * smoothstep(0.5, 0.0, length(fract(p * 6.0) - 0.5)) * fade;
			em += vec3(1.0, 0.95, 0.8) * sp * glints * 1.5;
		}
		float lace = smoothstep(0.75, 0.98, shallow) * smoothstep(0.4, 0.7, bw_noise(p * 2.5 + flow * t));
		col = mix(col, vec3(0.85, 0.9, 0.9), lace * 0.5);
	}
	ALBEDO = col;
	EMISSION = em;
	SPECULAR = 0.7;
	METALLIC = 0.0;
}
