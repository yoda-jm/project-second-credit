// Fuseflight lighthouse beam: an additive cone, bright at the lamp and fading along its length and at its rim.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.95, 0.8);
uniform float strength = 0.22;

void fragment() {
	float along = 1.0 - UV.y;
	float rim = pow(abs(dot(NORMAL, VIEW)), 2.0);
	ALBEDO = color * strength * pow(along, 3.0) * rim;
}
