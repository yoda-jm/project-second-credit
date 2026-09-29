// Nova Wardens moving lights (the cars on the roads): camera-facing glows drawn from a MultiMesh; each instance's
// custom data is its colour (rgb) and brightness (a). A hot core with a soft halo and a faint horizontal smear.
// Additive, unshaded.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float size = 0.9;

varying vec4 light;

void vertex() {
	light = INSTANCE_CUSTOM;
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	VERTEX *= size;
}

void fragment() {
	vec2 p = (UV - 0.5) * 2.0;
	float r2 = dot(p, p);
	float core = exp(-r2 * 40.0) * 2.5;
	float halo = exp(-r2 * 6.0) * 0.35;
	float smear = exp(-abs(p.y) * 30.0) * exp(-abs(p.x) * 4.0) * 0.3;
	ALBEDO = light.rgb * light.a * (core + halo + smear) * smoothstep(1.0, 0.8, sqrt(r2));
}
