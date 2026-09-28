// Pop Voyage lighthouse beam: an additive cone, bright at the lantern and fading along its length and at its rim.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.95, 0.8);
uniform float strength = 0.35;

void fragment() {
	float along = 1.0 - UV.y;
	float rim = pow(abs(dot(NORMAL, VIEW)), 1.5);
	ALBEDO = color * strength * pow(along, 1.6) * rim;
}
