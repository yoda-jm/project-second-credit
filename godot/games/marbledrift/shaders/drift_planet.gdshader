shader_type spatial;
// Marble Drift: a distant planet (our own design, CC BY-SA 4.0). Banded, swirled gas or a rocky crust from noise in
// the sphere's own space, lit by the sun with a soft terminator, a thin glowing atmosphere at the rim and faint
// light on the night side. Unshaded (its own lighting), fog off: far planets stay crisp.
render_mode blend_mix, unshaded, cull_back, fog_disabled, shadows_disabled;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 col_a : source_color = vec3(0.85, 0.6, 0.4);
uniform vec3 col_b : source_color = vec3(0.5, 0.3, 0.25);
uniform vec3 col_c : source_color = vec3(0.95, 0.9, 0.8);
uniform vec3 atmo : source_color = vec3(0.5, 0.7, 1.0);
uniform float atmo_strength = 1.0;
uniform float bands = 7.0;           // 0 = a rocky world
uniform float spin = 0.004;          // rad/s
uniform vec3 sun_dir = vec3(0.3, 0.4, 1.0);
uniform float night = 0.04;

varying vec3 v_on;
varying vec3 v_wn;
varying vec3 v_wpos;

void vertex() {
	v_on = normalize(VERTEX);
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float a = clock * spin;
	vec3 n = v_on;
	n.xz = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a))) * n.xz;
	vec3 col;
	if (bands > 0.0) {
		float warp = md_fbm3(n * 3.0, 4);
		float lat = n.y * bands + warp * 1.4;
		float b = 0.5 + 0.5 * sin(lat * 3.0) * md_fbm3(n * vec3(1.0, 8.0, 1.0), 3);
		col = mix(col_b, col_a, smoothstep(0.2, 0.8, b));
		col = mix(col, col_c, smoothstep(0.62, 0.9, md_fbm3(vec3(n.x * 2.0, lat * 0.6, n.z * 2.0), 4)));
		float storm = 1.0 - smoothstep(0.05, 0.12, length(n - normalize(vec3(0.6, -0.3, 0.7))));
		col = mix(col, col_c * vec3(1.0, 0.8, 0.7), storm);
	} else {
		float h = md_fbm3(n * 4.0, 5);
		col = mix(col_b, col_a, smoothstep(0.35, 0.65, h));
		col = mix(col, col_c, smoothstep(0.62, 0.7, h));
		float cr = md_fbm3(n * 14.0, 2);
		col *= 0.85 + 0.3 * cr;
	}
	vec3 wn = normalize(v_wn);
	vec3 sd = normalize(sun_dir);
	float l = dot(wn, sd);
	float lit = smoothstep(-0.15, 0.45, l);
	vec3 vd = normalize(CAMERA_POSITION_WORLD - v_wpos);
	float rim = pow(1.0 - clamp(dot(wn, vd), 0.0, 1.0), 3.0);
	vec3 c = col * (lit * 1.1 + night);
	c += atmo * rim * atmo_strength * (smoothstep(-0.4, 0.3, l) * 1.4 + 0.08);
	c += atmo * 0.12 * lit * atmo_strength;
	ALBEDO = c;
}
