shader_type spatial;
// Henhouse Heist: the low sun's glow, a soft additive halo with faint rays, far behind everything.

render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.7, 0.4);
uniform float strength = 1.0;
uniform float time_s = 0.0;

void vertex() {
	// always face the camera
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	vec2 q = UV - 0.5;
	float r = length(q) * 2.0;
	float a = atan(q.y, q.x);
	float rays = 0.75 + 0.25 * sin(a * 11.0 + time_s * 0.15) * sin(a * 7.0 - time_s * 0.1);
	float core = exp(-r * 18.0) * 3.0;
	float glow = exp(-r * 4.0) * 0.55 * rays + exp(-r * 1.6) * 0.18;
	ALBEDO = color * (core + glow) * strength * smoothstep(1.0, 0.7, r);
}
