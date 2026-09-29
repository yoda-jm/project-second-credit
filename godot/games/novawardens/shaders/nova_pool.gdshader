// Nova Wardens pools of lamplight on the ground under the street and promenade lamps: a soft additive disc (UV 0..1
// across the quad), dimmed in the blackout as the alarm rises. Unshaded.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.6, 0.28);
uniform float strength = 0.28;
uniform float dim = 0.0;

void fragment() {
	vec2 p = (UV - 0.5) * 2.0;
	float r2 = dot(p, p);
	float k = exp(-r2 * 3.5) * smoothstep(1.0, 0.75, sqrt(r2));
	ALBEDO = color * strength * k * (1.0 - 0.7 * dim);
}
