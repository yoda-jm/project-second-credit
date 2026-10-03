shader_type spatial;
// Marble Drift: a planet's rings (our own design, CC BY-SA 4.0). On a flat annulus whose UV.x is the radius (0 inner,
// 1 outer): fine bands with gaps, lit on both faces, darkened where the planet's shadow falls across them.
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, fog_disabled, shadows_disabled;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform vec3 col_a : source_color = vec3(0.9, 0.8, 0.65);
uniform vec3 col_b : source_color = vec3(0.55, 0.45, 0.4);
uniform vec3 sun_dir = vec3(0.3, 0.4, 1.0);
uniform vec3 planet_centre = vec3(0.0);
uniform float planet_radius = 100.0;
uniform float opacity = 0.85;

varying vec3 v_wpos;

void vertex() {
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float r = UV.x;
	float b = md_noise(vec2(r * 60.0, 0.5)) * 0.6 + md_noise(vec2(r * 230.0, 2.5)) * 0.4;
	float gap = smoothstep(0.02, 0.0, abs(r - 0.62)) + smoothstep(0.012, 0.0, abs(r - 0.33)) * 0.8;
	float a = smoothstep(0.0, 0.05, r) * smoothstep(1.0, 0.92, r) * (0.35 + 0.65 * b) * (1.0 - gap);
	vec3 col = mix(col_b, col_a, b);
	// the planet's shadow: does the ray towards the sun hit the sphere?
	vec3 sd = normalize(sun_dir);
	vec3 oc = v_wpos - planet_centre;
	float bb = dot(oc, sd);
	float cc = dot(oc, oc) - planet_radius * planet_radius;
	float shadow = (bb < 0.0 && bb * bb - cc > 0.0) ? 0.15 : 1.0;
	ALBEDO = col * (0.25 + 0.95 * shadow);
	ALPHA = a * opacity;
}
