// Bloomwand motes, additive (fireflies, sparkles, wisps, dust in the sunbeams): see bloom_mote.gdshaderinc.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_mote.gdshaderinc"

void fragment() {
	vec3 col;
	float a = mote_shape(col);
	ALBEDO = col * a * energy;
}
