shader_type spatial;
// Fizzlings: the shock ring of a popping bubble, facing the camera, growing and fading ("life" 0..1).

render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

instance uniform vec4 color : source_color = vec4(0.8, 0.95, 1.0, 1.0);
instance uniform float life = 0.0;

void fragment() {
	float r = length(UV - 0.5) * 2.0;
	float rad = mix(0.2, 0.92, 1.0 - pow(1.0 - life, 3.0));
	float w = mix(0.14, 0.03, life);
	float ring = exp(-pow((r - rad) / w, 2.0));
	float fade = (1.0 - life) * (1.0 - life);
	ALBEDO = color.rgb * ring * fade * 2.2 * color.a;
}
