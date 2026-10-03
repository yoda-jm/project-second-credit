shader_type spatial;
// Marble Drift: neon wireframes, the synth theme's mountains and floating shapes (our own design, CC BY-SA 4.0).
// A dark glossy body with glowing edges. The mesh is unindexed and each triangle's vertices carry the colours red,
// green and blue (barycentric), so the edges are where one of them is near zero. UV.y (0..1) blends the line colour.
render_mode blend_mix, cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform float clock = 0.0;
uniform vec3 body : source_color = vec3(0.03, 0.0, 0.06);
uniform vec3 line_a : source_color = vec3(1.0, 0.2, 0.8);
uniform vec3 line_b : source_color = vec3(0.2, 0.8, 1.0);
uniform float energy = 2.5;
uniform float width = 1.2;           // line width in pixels
uniform float fill = 0.12;           // glow of the faces

void fragment() {
	vec3 b = COLOR.rgb;
	vec3 fw = fwidth(b);
	vec3 e = smoothstep(vec3(0.0), fw * width, b);
	float line = 1.0 - min(min(e.x, e.y), e.z);
	vec3 lc = mix(line_a, line_b, clamp(UV.y, 0.0, 1.0));
	float pulse = 0.85 + 0.15 * sin(clock * 1.5 + UV.y * 6.0);
	ALBEDO = body;
	ROUGHNESS = 0.2;
	SPECULAR = 0.6;
	EMISSION = lc * (line * energy * pulse + fill * (1.0 - UV.y) * 0.5 + fill * 0.2);
}
