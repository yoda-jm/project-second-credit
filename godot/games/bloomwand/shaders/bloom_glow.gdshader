// Bloomwand glowing things (our own, CC BY-SA 4.0): lanterns, windows, a fairy door, glowing mushroom caps and their
// spots, glow-worms, the tower's magic window. Unshaded emissive; `color` times the vertex colour (the tint), with
// optional flicker (a flame), pulse (slow breathing, varied per place), twinkle (glow-worms), variety (per-place
// brightness), rim (brighter towards the edges, as a lit cap seen against the dark). Runs on `clock`.
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(1.0);
uniform float energy = 2.0;
uniform float flicker = 0.0;
uniform float pulse = 0.0;
uniform float pulse_speed = 0.8;
uniform float twinkle = 0.0;
uniform float variety = 0.0;
uniform float rim = 0.0;
uniform float cell = 1.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float h = bw_hash3(floor(wpos / cell + 0.001));
	float k = 1.0;
	vec3 col = color * COLOR.rgb;
	if (variety > 0.0) {
		k *= 1.0 - variety * 0.5 + variety * h;
	}
	if (rim > 0.0) {
		float f = abs(dot(NORMAL, VIEW));
		k *= mix(1.0 + rim, 1.0 - rim * 0.4, f);
		col = mix(col * 1.15 + vec3(0.08), col, f);
	}
	if (pulse > 0.0) {
		k *= 1.0 + pulse * (0.5 * sin(clock * pulse_speed + h * 40.0) + 0.25 * sin(clock * pulse_speed * 2.3 + h * 13.0));
	}
	if (twinkle > 0.0) {
		float s = sin(clock * (0.6 + h * 1.4) + h * 60.0);
		k *= mix(1.0, 0.25 + 0.75 * smoothstep(-0.4, 0.9, s), twinkle);
	}
	if (flicker > 0.0) {
		k *= 1.0 + flicker * 0.25 * (sin(clock * 11.0 + h * 40.0) + sin(clock * 6.3 + h * 17.0));
	}
	ALBEDO = col * energy * k;
}
