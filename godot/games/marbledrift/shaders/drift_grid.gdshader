shader_type spatial;
// Marble Drift: the neon grid far below the synth course (our own design, CC BY-SA 4.0). A dark glossy floor with
// glowing lines that scroll towards the camera, pulses running along them, the synthwave sun's reflection, and a
// haze that melts into the horizon. On a wide plane that follows the camera (the grid stays in world space).
render_mode blend_mix, unshaded, cull_disabled, fog_disabled, shadows_disabled;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 floor_col : source_color = vec3(0.04, 0.0, 0.09);
uniform vec3 line_a : source_color = vec3(1.0, 0.2, 0.8);
uniform vec3 line_b : source_color = vec3(0.2, 0.8, 1.0);
uniform vec3 horizon_col : source_color = vec3(0.6, 0.15, 0.5);
uniform vec3 sun_dir = vec3(0.0, 0.1, 1.0);
uniform vec3 sun_col : source_color = vec3(1.0, 0.4, 0.6);
uniform float spacing = 6.0;
uniform float speed = 3.0;           // scroll, units per second, along -z
uniform float energy = 2.2;
uniform float fade_near = 60.0;
uniform float fade_far = 420.0;

varying vec3 v_wpos;

void vertex() {
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = v_wpos.xz / spacing;
	p.y += clock * speed / spacing;
	vec2 fw = fwidth(p);
	vec2 g = abs(fract(p - 0.5) - 0.5) / max(fw, vec2(1e-4));
	float line = 1.0 - min(min(g.x, g.y), 1.0);
	vec2 g2 = abs(fract(p * 0.2 - 0.5) - 0.5) / max(fw * 0.2, vec2(1e-4));
	float major = 1.0 - min(min(g2.x, g2.y), 1.0);
	float wide = exp(-min(abs(fract(p.x - 0.5) - 0.5), abs(fract(p.y - 0.5) - 0.5)) * 14.0);
	// pulses running along the lines
	float lane = floor(p.x + 0.5);
	float pulse = pow(0.5 + 0.5 * sin(p.y * 0.35 - clock * 2.0 + md_hash(vec2(lane, 1.0)) * 6.28), 18.0);
	float dist = length(v_wpos.xz - CAMERA_POSITION_WORLD.xz);
	float fade = smoothstep(fade_near, fade_far, dist);
	float zmix = 0.5 + 0.5 * sin(v_wpos.z * 0.01 + v_wpos.x * 0.004);
	vec3 lc = mix(line_a, line_b, zmix);
	float aa = 1.0 - smoothstep(0.3, 1.0, max(fw.x, fw.y));   // lines merge into a glow far away
	vec3 col = floor_col;
	col += lc * (line * (0.6 + 0.8 * major) * aa + wide * 0.06) * energy;
	col += line_b * pulse * (1.0 - min(abs(fract(p.x - 0.5) - 0.5) / max(fw.x, 1e-4), 1.0)) * energy * 1.5 * aa;
	// the sun's reflection: a vertical smear on the glossy floor
	vec3 vd = normalize(v_wpos - CAMERA_POSITION_WORLD);
	vec3 r = reflect(vd, vec3(0.0, 1.0, 0.0));
	float sr = max(dot(normalize(r), normalize(sun_dir)), 0.0);
	col += sun_col * (pow(sr, 30.0) * 0.8 + pow(sr, 300.0) * 1.5);
	col = mix(col, horizon_col, fade);
	ALBEDO = col;
}
