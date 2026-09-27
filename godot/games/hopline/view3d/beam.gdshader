shader_type spatial;
// Hopline headlight beams at night: a soft additive cone, bright at the lamp, fading along its length and at its
// silhouette, so it reads as light in the air rather than a solid cone.

render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.9, 0.65);
uniform float strength = 0.0;

void fragment() {
	float along = UV.y;  // 0 at the lamp (the cone's tip), 1 at the far end
	float face = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float a = pow(1.0 - along, 2.2) * pow(face, 1.5);
	ALBEDO = color * a * strength;
}
