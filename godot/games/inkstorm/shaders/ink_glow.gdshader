shader_type spatial;
// Inkstorm: a soft additive glow. mode 0: a strip laid under the line (UV.y across it, UV.x along: light flows
// with the line); mode 1: a round halo (UV centred), turned to the camera when billboard is on; mode 2: a ring
// of light (radius ring 0..1 of the quad, width ring_w).

render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec4 color : source_color = vec4(1.0, 0.75, 0.3, 1.0);
uniform float energy = 1.0;
uniform int mode = 0;
uniform bool billboard = false;
uniform float ring = 0.8;
uniform float ring_w = 0.08;
uniform float rays = 0.0;         // halo: a star of soft rays
uniform float spin = 0.0;

void vertex() {
	if (billboard) {
		float sc = length(MODEL_MATRIX[0].xyz);
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0] * sc, INV_VIEW_MATRIX[1] * sc, INV_VIEW_MATRIX[2] * sc, MODEL_MATRIX[3]);
		VERTEX.z += 1.2;  // drawn towards the camera, so the board does not cut the flare in half
	}
}

void fragment() {
	float a = 0.0;
	if (mode == 0) {
		float d = abs(UV.y - 0.5) * 2.0;
		a = exp(-d * d * 5.0) * (0.75 + 0.25 * sin(UV.x * 10.0 - TIME * 8.0));
	} else {
		vec2 p = UV * 2.0 - 1.0;
		float r = length(p);
		if (mode == 1) {
			a = exp(-r * r * 6.0) + exp(-r * 18.0) * 0.8;
			if (rays > 0.0) {
				float ang = atan(p.y, p.x) + TIME * spin;
				a += rays * pow(abs(cos(ang * 2.0)), 40.0) * exp(-r * 3.0) + rays * 0.5 * pow(abs(cos(ang * 2.0 + 0.785)), 60.0) * exp(-r * 4.0);
			}
		} else {
			float d = (r - ring) / ring_w;
			a = exp(-d * d) + exp(-abs(d) * 0.6) * 0.15;
			a *= smoothstep(1.0, 0.92, r);
		}
	}
	if (mode == 1) a *= smoothstep(1.0, 0.75, length(UV * 2.0 - 1.0));  // fade out well inside the quad
	ALBEDO = color.rgb * a * energy * color.a;
}
