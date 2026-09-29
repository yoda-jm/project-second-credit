// Nova Wardens light streaks on the water under the harbour lights: broken, shimmering bands that fade away from
// the light (UV.y from the light (0) to the far end (1)); the colour is the vertex colour. Additive, unshaded.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"

uniform float clock = 0.0;
uniform float strength = 1.2;
uniform float dim = 0.0;
uniform vec3 tint : source_color = vec3(1.0, 0.7, 0.35);

void fragment() {
	float y = UV.y;
	float x = abs(UV.x - 0.5) * 2.0;
	float bands = nw_noise(vec2(UV.x * 3.0 + sin(clock * 0.7 + y * 9.0) * 0.4, y * 26.0 - clock * 0.8));
	bands = smoothstep(0.35, 0.75, bands);
	float k = bands * (1.0 - y) * (1.0 - y) * smoothstep(1.0, 0.2, x);
	vec3 col = COLOR.rgb;
	if (col.r > 0.99 && col.g > 0.99 && col.b > 0.99) {
		col = tint;
	}
	ALBEDO = col * k * strength * (1.0 - 0.6 * dim);
}
