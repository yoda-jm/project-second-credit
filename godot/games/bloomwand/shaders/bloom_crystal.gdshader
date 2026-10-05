// Bloomwand crystals (our own, CC BY-SA 4.0): faceted and luminous. The tint is the vertex colour; light seems to
// come from inside (brighter where you look straight into a facet and at the edges), each facet a little different,
// breathing slowly; glossy, so lamps and flashes glint on them. Runs on `clock`.
shader_type spatial;
render_mode cull_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform float energy = 1.6;
uniform float pulse = 0.25;

varying vec3 wpos;
varying vec3 wnrm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 col = COLOR.rgb;
	float facet = bw_hash3(floor(wnrm * 6.0 + 0.5) + floor(wpos * 0.5));
	float f = abs(dot(NORMAL, VIEW));
	float inner = 0.35 + 0.45 * f * f + 0.6 * pow(clamp(1.0 - f, 0.0, 1.0), 3.0);
	float breathe = 1.0 + pulse * sin(clock * 0.7 + bw_hash3(floor(wpos * 0.25)) * 30.0);
	float glint = smoothstep(0.92, 1.0, facet) * (0.5 + 0.5 * sin(clock * 2.0 + facet * 50.0));
	ALBEDO = col * 0.25;
	ROUGHNESS = 0.08;
	SPECULAR = 0.9;
	EMISSION = col * energy * inner * (0.7 + 0.5 * facet) * breathe + vec3(1.0) * glint * energy * 0.5;
}
