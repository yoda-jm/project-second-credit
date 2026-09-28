// Pop Voyage birds: a simple body and two wings that beat (vertices away from the body rise and fall).
shader_type spatial;
render_mode cull_disabled;

uniform vec3 color : source_color = vec3(0.95, 0.95, 0.95);
uniform vec3 tip : source_color = vec3(0.2, 0.2, 0.25);
uniform float rate = 7.0;
instance uniform float phase = 0.0;
instance uniform float glide = 0.0;

varying float span;

void vertex() {
	span = abs(VERTEX.x);
	float f = sin(TIME * rate + phase * 6.283);
	float beat = mix(f, 0.15, glide);
	VERTEX.y += beat * span * 0.7;
}

void fragment() {
	ALBEDO = mix(color, tip, smoothstep(0.35, 0.5, span));
	ROUGHNESS = 0.8;
}
