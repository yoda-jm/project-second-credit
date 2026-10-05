// Biosurge: a drifting veil of haze (water, steam, spores) between the floor and the play plane: two layers at
// different depths give the abyss its parallax. Our own code, CC BY-SA 4.0.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, fog_disabled;

#include "res://games/biosurge/shaders/bio_noise.gdshaderinc"

uniform vec3 mist_color : source_color = vec3(0.1, 0.4, 0.35);
uniform float strength = 0.35;
uniform float glow = 0.6;
uniform float scale = 0.05;
uniform vec2 drift = vec2(0.3, 0.1);
uniform float clock = 0.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xz * scale;
	float a = bio_fbm(p + drift * clock * scale);
	float c = bio_fbm(p * 2.3 - drift.yx * clock * scale * 1.7 + 5.0);
	float m = smoothstep(0.38, 0.85, a * 0.7 + c * 0.4);
	ALBEDO = mist_color * (1.0 + glow * c);
	ALPHA = m * strength;
}
