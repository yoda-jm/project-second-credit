shader_type spatial;
// Marble Drift: a soft cloud on a camera-facing quad (our own design, CC BY-SA 4.0), many of them making cloud banks
// and storm towers. Domain-warped noise inside a rounded mass, lit from the sun's side as seen on screen, warm tops
// and cool bellies, silver edges against the sun, lightning (flash) from inside. For a MultiMesh of quads: each
// instance's transform places and sizes it, COLOR.r is its seed, COLOR.g its brightness.
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 lit : source_color = vec3(1.0, 0.92, 0.85);
uniform vec3 shade : source_color = vec3(0.55, 0.5, 0.62);
uniform vec3 sun_dir = vec3(0.3, 0.4, 1.0);
uniform vec3 sun_col : source_color = vec3(1.0, 0.85, 0.6);
uniform float opacity = 1.0;
uniform float puffiness = 0.9;      // how much the noise eats into the billows
uniform vec4 flash = vec4(0.0, 0.0, 30.0, 0.0);   // x, z, radius, strength
uniform vec3 flash_col : source_color = vec3(0.75, 0.8, 1.0);

varying vec4 v_col;
varying vec3 v_wpos;
varying vec2 v_sun;

void vertex() {
	v_col = COLOR;
	vec3 pos = MODEL_MATRIX[3].xyz;
	vec3 to_cam = normalize(CAMERA_POSITION_WORLD - pos);
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), to_cam) + vec3(1e-4, 0.0, 0.0));
	vec3 up = cross(to_cam, right);
	vec3 w = pos + right * VERTEX.x * length(MODEL_MATRIX[0].xyz) + up * VERTEX.y * length(MODEL_MATRIX[1].xyz);
	v_wpos = w;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(w, 1.0);
	vec3 s = normalize(sun_dir);
	v_sun = normalize(vec2(dot(s, right), dot(s, up)) + vec2(1e-4));
}

void fragment() {
	vec2 uv = vec2(UV.x, 1.0 - UV.y);   // y up
	vec2 c = uv - 0.5;
	float seed = v_col.r;
	// round billows: the strongest one gives the shape and a pseudo normal for the shading
	float best = 0.0;
	vec2 nrm = vec2(0.0, 1.0);
	for (int i = 0; i < 6; i++) {
		float fi = float(i);
		float h1 = md_hash(vec2(seed * 31.0, fi));
		float h2 = md_hash(vec2(fi, seed * 13.0));
		float h3 = md_hash(vec2(fi + 3.0, seed * 7.0));
		float br = 0.12 + 0.13 * h3 * (1.0 - abs(fi - 2.5) / 4.0) + 0.06;
		vec2 bc = vec2(-0.3 + 0.12 * fi + 0.05 * (h1 - 0.5), -0.12 + br * 0.6 + 0.12 * h2);
		vec2 dd = (c - bc) / br;
		float v = 1.0 - dot(dd, dd);
		if (v > best) {
			best = v;
			nrm = dd;
		}
	}
	float flat_base = smoothstep(-0.2, -0.1, c.y);
	vec2 q = uv * 3.0 + seed * 17.0 + vec2(clock * 0.008, 0.0);
	vec2 w = vec2(md_noise(q * 0.7), md_noise(q * 0.7 + 4.7)) - 0.5;
	float n = md_fbm(q + w * 0.8, 4);
	float d = (clamp(best, 0.0, 1.0) * 1.15 + (n - 0.5) * puffiness) * flat_base;
	float a = smoothstep(0.05, 0.55, d);
	if (a < 0.003) {
		discard;
	}
	vec3 pn = normalize(vec3(nrm * 0.35 + (vec2(md_noise(q * 2.0), md_noise(q * 2.0 + 9.0)) - 0.5) * 0.6,
			sqrt(max(1.0 - dot(nrm, nrm), 0.05))));
	float l = clamp(dot(pn, normalize(vec3(v_sun, 0.55))) * 0.5 + 0.4 + (n - 0.5) * 0.9 + c.y * 0.5, 0.0, 1.0);
	l *= 0.75 + 0.25 * smoothstep(-0.2, 0.3, c.y);
	vec3 col = mix(shade, lit, l) * (0.8 + 0.3 * v_col.g);
	vec3 vd = normalize(v_wpos - CAMERA_POSITION_WORLD);
	float fs = max(dot(vd, normalize(sun_dir)), 0.0);
	col += sun_col * pow(fs, 3.0) * (1.0 - smoothstep(0.08, 0.3, d)) * 1.2;   // silver edges against the sun
	if (flash.w > 0.0) {
		float fd = length(v_wpos.xz - flash.xy) / flash.z;
		col += flash_col * flash.w * exp(-fd * fd) * (0.4 + 0.8 * (1.0 - l) + n);
	}
	ALBEDO = col;
	ALPHA = a * opacity;
}
