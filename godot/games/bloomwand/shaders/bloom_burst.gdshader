// Bloomwand celebration bursts (our own, CC BY-SA 4.0): one MultiMesh instance per burst, its mesh SPARKS quads each
// carrying its direction (VERTEX, on the unit sphere) with a random number and its index in UV2. The instance's
// basis is the burst's size, its origin the centre; INSTANCE_CUSTOM = (start time, kind, hue spread, seed); COLOR its
// colour. Kinds: 0 sparkles (stars flung out, drifting down, twinkling), 1 petals (blown out, then fluttering down),
// 2 a firework (fast, sagging, fading to embers), 3 a pop (a quick small ring). Additive. Runs on `clock`.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform float energy = 3.0;

varying vec2 v_uv;
varying vec3 v_col;
varying float v_a;
varying float v_kind;

void vertex() {
	vec3 centre = MODEL_MATRIX[3].xyz;
	float radius = length(MODEL_MATRIX[0].xyz);
	vec3 dir = VERTEX;
	float rnd = UV2.x;
	float t0 = INSTANCE_CUSTOM.x;
	float kind = INSTANCE_CUSTOM.y;
	float spread = INSTANCE_CUSTOM.z;
	float age = clock - t0;
	float life = kind < 0.5 ? 2.4 : kind < 1.5 ? 3.6 : kind < 2.5 ? 2.2 : 0.7;
	float x = age / life;
	vec3 p = centre;
	float size = 0.0;
	float a = 0.0;
	if (age >= 0.0 && x < 1.0) {
		float sp = 0.7 + 0.6 * rnd;
		if (kind < 0.5) {
			p += dir * radius * sp * (1.0 - exp(-age * 3.2)) + vec3(0.0, -0.35 * age * age, 0.0);
			size = 0.16 * (1.0 - x * 0.5) * (0.6 + 0.8 * fract(rnd * 7.0));
			a = (1.0 - smoothstep(0.6, 1.0, x)) * (0.55 + 0.45 * sin(age * 18.0 + rnd * 40.0));
		} else if (kind < 1.5) {
			vec3 out_ = dir * radius * sp * (1.0 - exp(-age * 2.5));
			p += out_ + vec3(sin(age * 3.0 + rnd * 20.0) * 0.4, -0.8 * age * age * 0.3 - age * 0.5, cos(age * 2.0 + rnd * 9.0) * 0.3);
			size = 0.18 * (0.7 + 0.6 * fract(rnd * 5.0)) * (0.4 + 0.6 * abs(sin(age * 4.0 + rnd * 30.0)));
			a = 1.0 - smoothstep(0.65, 1.0, x);
		} else if (kind < 2.5) {
			p += dir * radius * sp * (1.0 - exp(-age * 4.5)) + vec3(0.0, -0.9 * age * age, 0.0);
			size = 0.22 * (1.0 - x * 0.6);
			a = (1.0 - smoothstep(0.4, 1.0, x)) * (x > 0.5 ? step(0.4, fract(sin(rnd * 300.0 + floor(clock * 24.0)) * 4375.5)) : 1.0);
		} else {
			p += dir * radius * (1.0 - exp(-age * 9.0));
			size = 0.12 * (1.0 - x);
			a = 1.0 - x;
		}
	}
	vec3 right = INV_VIEW_MATRIX[0].xyz;
	vec3 up = INV_VIEW_MATRIX[1].xyz;
	vec3 wp = p + (right * (UV.x * 2.0 - 1.0) + up * (UV.y * 2.0 - 1.0)) * size;
	VERTEX = (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
	v_uv = UV;
	v_a = a;
	v_kind = kind;
	vec3 h = bw_hue(fract(spread * (rnd - 0.5) + 0.0));
	v_col = mix(COLOR.rgb, COLOR.rgb * h * 1.6 + 0.1, spread);
	if (kind > 1.5 && kind < 2.5) {
		v_col = mix(v_col, vec3(1.0, 0.55, 0.2), smoothstep(0.4, 0.9, x));
	}
}

void fragment() {
	vec2 p = v_uv * 2.0 - 1.0;
	float s;
	if (v_kind < 0.5) {
		float star = max(smoothstep(0.14, 0.0, abs(p.x)) * smoothstep(1.0, 0.0, abs(p.y)),
				smoothstep(0.14, 0.0, abs(p.y)) * smoothstep(1.0, 0.0, abs(p.x)));
		s = star + exp(-dot(p, p) * 6.0) * 0.8;
	} else if (v_kind < 1.5) {
		s = smoothstep(1.0, 0.6, length(p * vec2(1.0, 1.6))) * 0.8;
	} else {
		s = exp(-dot(p, p) * 4.0) + exp(-dot(p, p) * 25.0);
	}
	ALBEDO = v_col * s * v_a * energy;
}
