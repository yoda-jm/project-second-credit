shader_type spatial;
// Marble Drift: the abyss under the courses, a sea of cloud or mist far below (our own design, CC BY-SA 4.0).
// Drawn on a wide flat plane that follows the camera (the pattern stays in world space). Domain-warped noise makes
// the cloud tops, lit from the sun's side, with darker gaps that open into the depth; the sun scatters a sheen
// across it; it fades into the horizon colour with distance. Also the thin wisp layer above it (gap_alpha 0,
// opacity < 1). Lightning (flash) lights it from inside; glow tints it from below (aurora, crystal light).
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, fog_disabled, shadows_disabled;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 lit_col : source_color = vec3(1.0, 0.85, 0.65);
uniform vec3 shade_col : source_color = vec3(0.55, 0.45, 0.55);
uniform vec3 gap_col : source_color = vec3(0.15, 0.12, 0.22);
uniform vec3 horizon_col : source_color = vec3(0.9, 0.75, 0.65);
uniform vec3 sun_dir = vec3(0.0, 0.2, 1.0);
uniform vec3 sun_col : source_color = vec3(1.0, 0.85, 0.6);
uniform float scale = 0.03;          // cloud features per unit
uniform float coverage = 0.6;
uniform float contrast = 1.0;
uniform vec2 drift = vec2(0.04, 0.02);   // in pattern units per second
uniform float sheen = 0.6;
uniform float fade_near = 120.0;
uniform float fade_far = 700.0;
uniform float gap_alpha = 1.0;       // 1 = the gaps are solid gap_col (the main deck), 0 = they are clear (wisps)
uniform float opacity = 1.0;
uniform vec4 flash = vec4(0.0, 0.0, 30.0, 0.0);   // x, z, radius, strength
uniform vec3 flash_col : source_color = vec3(0.75, 0.8, 1.0);
uniform vec3 glow_col : source_color = vec3(0.2, 1.0, 0.6);
uniform float glow = 0.0;
uniform float glow_scale = 0.004;
uniform float detail_oct = 5.0;
uniform float light_oct = 2.0;       // octaves of the sample towards the sun (0: flat lighting, for the wisps)

varying vec3 v_wpos;

void vertex() {
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = v_wpos.xz * scale;
	int oct = int(detail_oct);
	vec2 tm = drift * clock;
	vec2 w = vec2(md_noise(p * 0.45 + tm * 0.5), md_noise(p * 0.45 + vec2(5.2, 1.3) - tm * 0.4)) - 0.5;
	vec2 q = p + w * 1.6 + tm;
	float bill = 1.0 - abs(md_noise(q * 1.3 + 7.0) * 2.0 - 1.0);   // puffy cells
	float dn = md_fbm(q, oct) * 0.86 + bill * 0.14;
	vec3 sd = normalize(sun_dir);
	vec2 sxz = normalize(sd.xz + vec2(1e-4)) * 0.18;
	float dl = light_oct > 0.5 ? md_fbm(q + sxz, int(light_oct)) * 0.86 + bill * 0.14 : dn - 0.04;
	float c = smoothstep(1.0 - coverage - 0.12, 1.0 - coverage + 0.22 / contrast, dn);
	float lightv = clamp((dn - dl) * 6.0 * contrast + 0.5, 0.0, 1.0);
	vec3 col = mix(shade_col, lit_col, lightv);
	col *= 0.85 + 0.3 * smoothstep(0.3, 0.8, dn);
	col = mix(gap_col, col, c);

	vec3 vd = normalize(v_wpos - CAMERA_POSITION_WORLD);
	float fs = max(dot(vd, sd), 0.0);
	col += sun_col * (pow(fs, 5.0) * 0.5 + pow(fs, 40.0) * 0.8) * sheen * (0.4 + 0.6 * c);
	col += sun_col * c * (1.0 - c) * 1.2 * pow(fs, 3.0) * sheen;   // silver linings

	if (glow > 0.0) {
		float gb = md_noise(v_wpos.xz * glow_scale + vec2(clock * 0.01, 0.0));
		col += glow_col * smoothstep(0.35, 0.85, gb) * glow * (0.5 + 0.5 * c);
	}
	if (flash.w > 0.0) {
		float fd = length(v_wpos.xz - flash.xy) / flash.z;
		col += flash_col * flash.w * exp(-fd * fd) * (0.3 + 1.2 * c * dn);
	}

	float dist = length(v_wpos.xz - CAMERA_POSITION_WORLD.xz);
	float fade = smoothstep(fade_near, fade_far, dist);
	col = mix(col, horizon_col, fade);
	ALBEDO = col;
	ALPHA = opacity * mix(gap_alpha, 1.0, c) * mix(1.0, gap_alpha, fade * (1.0 - gap_alpha) );
}
