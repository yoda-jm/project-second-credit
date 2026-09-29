// Nova Wardens light beams (searchlights and the lighthouse): an additive cone whose brightness follows how much
// of the beam a ray crosses (dim at the rim, bright down the middle), fading along its length, with slow drifting
// dust and haze in it. Unshaded HDR, feeds the glow. UV.y runs from the lens (0) to the far end (1).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(0.8, 0.88, 1.0);
uniform float strength = 0.08;
uniform float falloff = 1.6;
uniform float dust = 0.5;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float along = UV.y;
	float rim = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float core = pow(rim, 2.2);
	float len = pow(1.0 - along, falloff) * smoothstep(0.0, 0.03, along);
	float n = nw_fbm(wpos.xy * 0.18 + vec2(clock * 0.05, clock * 0.02) + wpos.z * 0.05, 3);
	float haze = mix(1.0, 0.5 + n, dust);
	float hot = exp(-along * 30.0) * 2.0;
	ALBEDO = color * strength * (len * haze + hot) * core;
}
