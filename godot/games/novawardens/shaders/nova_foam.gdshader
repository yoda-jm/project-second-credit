// Nova Wardens surf: lace foam where the sea meets the rocks, the beaches and the breakwater. Waves roll in towards
// the shore (UV.y runs from the shore (0) out to sea (1); UV.x along the shore in world units), break into a bright
// line at the water's edge and leave broken lace that drains back. Additive, unshaded, moonlit; on `clock`.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(0.72, 0.8, 0.95);
uniform float strength = 0.4;

void fragment() {
	float u = UV.x;
	float v = clamp(UV.y, 0.0, 1.0);
	// each stretch of shore gets its own swell timing
	float along = nw_noise(vec2(u * 0.12, 3.0)) * 2.0;
	float ph = clock * 0.16 + along;
	float wave = fract(ph);
	// the swell's crest runs from the sea (v = 1) up to the shore (v = 0), then the wash drains back
	float crest_v = 1.0 - wave * 1.15;
	float crest = exp(-abs(v - crest_v) * 14.0) * smoothstep(0.0, 0.25, wave);
	float lace = nw_noise(vec2(u * 1.6 + clock * 0.04, v * 6.0 - clock * 0.25))
			* nw_noise(vec2(u * 4.3 - clock * 0.03, v * 13.0 + 1.7));
	lace = smoothstep(0.12, 0.45, lace);
	float edge = exp(-v * 7.0) * (0.55 + 0.45 * smoothstep(0.7, 1.0, wave));
	float wash = smoothstep(crest_v, crest_v + 0.3, v) * (1.0 - v) * lace * 0.7;
	float k = (edge * (0.4 + 0.6 * lace) + crest * (0.35 + 0.65 * lace) + wash) * smoothstep(1.0, 0.7, v);
	ALBEDO = color * strength * k;
}
