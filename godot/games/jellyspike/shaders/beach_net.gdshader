// Jelly Spike net: a square mesh of knotted cord drawn on one quad (UV in metres), anti-aliased and fading to a
// thin veil at a distance.
shader_type spatial;
render_mode cull_disabled, blend_mix, depth_draw_opaque;

uniform vec3 cord : source_color = vec3(0.12, 0.13, 0.16);
uniform float cell = 0.1;
uniform float width = 0.011;

void fragment() {
	vec2 p = UV / cell;
	vec2 fw = fwidth(p) + 1e-4;
	vec2 d = abs(fract(p + 0.5) - 0.5);
	float wl = width / cell;
	vec2 l = smoothstep(wl + fw, wl - fw * 0.5, d);
	float a = max(l.x, l.y);
	// when the cells shrink below a pixel, the mesh becomes a soft veil
	float veil = clamp(max(fw.x, fw.y) * 0.8, 0.0, 1.0);
	a = mix(a, 0.35, veil);
	ALBEDO = cord;
	ALPHA = a;
	ROUGHNESS = 0.8;
}
