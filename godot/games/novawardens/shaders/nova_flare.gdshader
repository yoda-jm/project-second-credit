// Nova Wardens lens flare: a camera-facing glow at a lamp (searchlight lens, the lighthouse lantern) that swells
// when its beam turns towards the camera, with a thin horizontal streak. Additive, unshaded; `bright` set per frame.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(0.85, 0.9, 1.0);
uniform float bright = 1.0;
uniform float streak = 0.6;

void vertex() {
	// billboard, scaled with the distance kept (a flare stays a flare)
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
			vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	vec2 p = (UV - 0.5) * 2.0;
	float r = length(p);
	float g = exp(-r * r * 9.0) * 1.5 + exp(-r * 3.5) * 0.25;
	float s = exp(-abs(p.y) * 60.0) * exp(-abs(p.x) * 2.2) * max(1.0 - p.x * p.x, 0.0) * streak;
	float k = g * smoothstep(1.0, 0.7, r) + s;
	ALBEDO = color * k * bright;
}
