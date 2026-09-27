shader_type spatial;
// Fizzlings: a four-pointed twinkle (treats, gold pops). Camera-facing, additive; "phase" staggers the twinkles.

render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.95, 0.7);
uniform float time_s = 0.0;
instance uniform float phase = 0.0;
instance uniform float rate = 1.0;

void vertex() {
	float tw = pow(max(0.0, sin(time_s * 3.1 * rate + phase)), 6.0);
	mat4 bb = mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	float s = length(MODEL_MATRIX[0].xyz) * (0.2 + tw);
	float rot = time_s * 1.3 + phase;
	mat4 spin = mat4(vec4(cos(rot) * s, sin(rot) * s, 0, 0), vec4(-sin(rot) * s, cos(rot) * s, 0, 0), vec4(0, 0, 1, 0), vec4(0, 0, 0, 1));
	MODELVIEW_MATRIX = VIEW_MATRIX * bb * spin;
}

void fragment() {
	vec2 q = (UV - 0.5) * 2.0;
	float star = max(0.0, 1.0 - abs(q.x) * 9.0 - abs(q.y) * 1.1) + max(0.0, 1.0 - abs(q.y) * 9.0 - abs(q.x) * 1.1);
	float core = exp(-dot(q, q) * 18.0);
	ALBEDO = color * (star * 2.5 + core * 2.0);
}
