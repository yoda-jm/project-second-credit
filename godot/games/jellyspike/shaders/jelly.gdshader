shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_back;
// A jelly blob: translucent candy colour that deepens towards the middle, a bright rim where it turns away, a glossy
// highlight, soft light scattered through it, and a wobble that ripples over the surface (wobble 0..1, set on hits,
// jumps and landings; it settles by itself in the view).

uniform vec4 color : source_color = vec4(0.3, 0.8, 1.0, 1.0);
uniform float wobble = 0.0;
uniform float phase = 0.0;
uniform float alpha = 0.9;

void vertex() {
	float w = sin(VERTEX.y * 9.0 + TIME * 14.0 + phase) * 0.5 + sin(VERTEX.x * 7.0 - TIME * 11.0) * 0.5;
	VERTEX += NORMAL * w * 0.035 * (0.25 + wobble);
}

void fragment() {
	float facing = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float rim = pow(1.0 - facing, 2.5);
	vec3 deep = color.rgb * color.rgb * 0.6;  // deeper and more saturated in the middle
	ALBEDO = mix(deep, color.rgb, 0.4 + 0.6 * facing);
	ALPHA = mix(alpha, 1.0, rim * 0.8);
	EMISSION = color.rgb * (0.08 + rim * 0.7);
	ROUGHNESS = 0.08;
	SPECULAR = 0.9;
	CLEARCOAT = 1.0;
	CLEARCOAT_ROUGHNESS = 0.03;
	BACKLIGHT = color.rgb * 0.8;
	SSS_STRENGTH = 0.6;
}
