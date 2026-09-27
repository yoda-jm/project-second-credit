shader_type spatial;
// Fizzlings: a disc facing the camera behind a full bubble: a bright outline ring and a soft halo, additive.

render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.78, 0.2);
uniform float strength = 1.0;
uniform float ring_r = 0.62;

void fragment() {
	float r = length(UV - 0.5) * 2.0;
	float ring = exp(-pow((r - ring_r) / 0.035, 2.0)) * 1.6;
	float halo = pow(smoothstep(1.0, ring_r, r), 2.0) * 0.35 * step(ring_r, r);
	float inner = smoothstep(ring_r, 0.0, r) * 0.18;
	ALBEDO = color * (ring + halo + inner) * strength;
}
