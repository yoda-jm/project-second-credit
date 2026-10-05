// Bloomwand motes, alpha-blended (snow, rain, petals, butterflies, birds): see bloom_mote.gdshaderinc.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_mote.gdshaderinc"

void fragment() {
	vec3 col;
	float a = mote_shape(col);
	ALBEDO = col * energy;
	ALPHA = clamp(a, 0.0, 1.0);
}
