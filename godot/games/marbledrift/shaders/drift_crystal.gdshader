shader_type spatial;
// Marble Drift: giant crystals and ice spires (our own design, CC BY-SA 4.0). Faceted glossy shells with light
// inside: a glow that climbs from the dark base to a bright tip, veins and clouds deep in the stone (seen with a
// little parallax), a fresnel rim, a slow breathing pulse. Mesh: UV.y = 0 at the base .. 1 at the tip; COLOR.r is a
// per-crystal phase, COLOR.g its brightness.
render_mode blend_mix, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 shell : source_color = vec3(0.1, 0.05, 0.2);
uniform vec3 core : source_color = vec3(0.7, 0.3, 1.0);
uniform vec3 tip : source_color = vec3(0.6, 0.9, 1.0);
uniform float energy = 1.6;
uniform float roughness = 0.08;
uniform float pulse = 0.25;
uniform float veins = 1.0;
uniform float frost = 0.0;           // ice: a frosted, whiter shell

varying vec3 v_lpos;
varying vec3 v_wn;
varying vec3 v_wpos;

void vertex() {
	v_lpos = VERTEX;
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float h = UV.y;
	float ph = COLOR.r * 6.28;
	float br = COLOR.g;
	vec3 wn = normalize(v_wn);
	vec3 vd = normalize(CAMERA_POSITION_WORLD - v_wpos);
	float nv = clamp(dot(wn, vd), 0.0, 1.0);
	vec3 inner = v_lpos * 0.35 - vd * 0.6;
	float cl = md_fbm3(inner + vec3(0.0, clock * 0.03, 0.0), 3);
	float vn = 1.0 - smoothstep(0.0, 0.05, abs(md_noise3(inner * 1.7 + 3.0) - 0.5));
	float pl = 1.0 + pulse * sin(clock * 0.9 + ph + h * 3.0);
	vec3 glow = mix(core, tip, smoothstep(0.55, 1.0, h)) * (0.04 + 1.3 * pow(h, 2.2)) * (0.45 + 1.0 * cl);
	glow += core * vn * veins * 0.25 * (0.2 + h);
	// a bright band where the facets meet the tip
	glow += tip * smoothstep(0.02, 0.0, abs(h - 0.8 - 0.05 * sin(ph))) * 0.6;
	float fres = pow(1.0 - nv, 4.0);
	ALBEDO = mix(shell, vec3(0.85, 0.92, 1.0), frost * (0.5 + 0.5 * cl));
	ROUGHNESS = roughness + frost * 0.15 * cl;
	METALLIC = 0.0;
	SPECULAR = 0.9;
	CLEARCOAT = 1.0;
	CLEARCOAT_ROUGHNESS = 0.03;
	EMISSION = (glow * energy * pl + core * fres * 0.5 * energy) * br;
}
