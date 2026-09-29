shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
// Nova Wardens: an expanding shockwave ring (progress 0..1): a thin bright band that widens and fades as it grows.

uniform vec4 color : source_color = vec4(1.0, 0.8, 0.5, 1.0);
uniform float progress = 0.0;
uniform float energy = 3.0;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float radius = progress;
	float width = mix(0.04, 0.18, progress);
	float band = smoothstep(width, 0.0, abs(r - radius));
	float inner = smoothstep(radius, 0.0, r) * 0.25 * (1.0 - progress);   // a soft flash inside, early on
	float fade = (1.0 - progress) * (1.0 - progress);
	ALBEDO = color.rgb * energy * (band + inner) * fade;
	ALPHA = 1.0;
}
