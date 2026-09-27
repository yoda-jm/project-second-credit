shader_type spatial;
// Fizzlings: the ghost that hunts the slowest hero. A dark, see-through body with a burning violet rim and a wavy,
// trailing hem; it flickers.

render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;

uniform float time_s = 0.0;
uniform vec3 rim : source_color = vec3(0.55, 0.2, 1.0);
uniform vec3 body : source_color = vec3(0.03, 0.0, 0.06);

void vertex() {
	// the lower half ripples into a hem of tatters
	float low = smoothstep(0.1, -1.0, VERTEX.y);
	float a = atan(VERTEX.z, VERTEX.x);
	VERTEX.y -= low * (0.25 + 0.2 * sin(a * 7.0 + time_s * 6.0));
	VERTEX.xz *= 1.0 + low * 0.25 * sin(time_s * 3.0 + VERTEX.y * 4.0);
}

void fragment() {
	float nv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float fres = pow(1.0 - nv, 3.2);
	float flick = 0.8 + 0.2 * sin(time_s * 23.0) * sin(time_s * 7.0);
	// a dark core that swallows the light, with a slow sick swirl, and the burning rim
	float swirl = 0.5 + 0.5 * sin(NORMAL.x * 5.0 + NORMAL.y * 3.0 - time_s * 2.0);
	ALBEDO = body * (0.6 + swirl * 0.8) + rim * fres * 2.2 * flick;
	ALPHA = clamp(0.82 + fres * 0.3, 0.0, 1.0);
}
