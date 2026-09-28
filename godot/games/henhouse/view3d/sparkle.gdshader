shader_type spatial;
// Henhouse Heist: a four-pointed glint that twinkles over an egg (each egg on its own phase). Faces the camera.

render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.92, 0.65);
instance uniform float phase = 0.0;
instance uniform float boost = 0.0;

void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
}

void fragment() {
	vec2 q = (UV - 0.5) * 2.0;
	float t = TIME * 1.3 + phase * 6.283;
	float tw = pow(max(0.0, sin(t)), 6.0) + boost;  // a quick twinkle now and then
	float ang = t * 0.4;
	mat2 r = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang)));
	vec2 p = r * q;
	float star = exp(-abs(p.x) * 22.0) * exp(-abs(p.y) * 3.0) + exp(-abs(p.y) * 22.0) * exp(-abs(p.x) * 3.0);
	float core = exp(-length(q) * 7.0);
	float halo = exp(-length(q) * 3.0) * 0.25;
	ALBEDO = color * (star * tw * 2.4 + core * (0.6 + tw * 2.0) + halo * (0.4 + tw));
}
