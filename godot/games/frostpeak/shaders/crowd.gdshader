shader_type spatial;
// Spectators drawn as one MultiMesh: the coat takes the instance colour, hat and scarf the instance custom colour,
// the face a skin tone from the custom alpha. Some fans bounce on their toes, each at their own pace.

uniform int part = 0;  // 0 coat, 1 hat and scarf, 2 face, 3 fixed colour
uniform vec3 base : source_color = vec3(0.15, 0.15, 0.2);
uniform float rough = 0.85;
uniform float hop = 1.0;

varying vec3 v_col;

float h1(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void vertex() {
	float h = h1(floor(MODEL_MATRIX[3].xz * 7.0));
	float bounce = step(0.6, h) * max(0.0, sin(TIME * (6.0 + 3.0 * h) + h * 40.0));
	VERTEX.y += bounce * 0.1 * hop;
	if (part == 0) {
		v_col = COLOR.rgb * (0.85 + 0.3 * fract(h * 13.0));
	} else if (part == 1) {
		v_col = INSTANCE_CUSTOM.rgb;
	} else if (part == 2) {
		v_col = mix(vec3(0.96, 0.8, 0.68), vec3(0.42, 0.28, 0.2), INSTANCE_CUSTOM.a);
	} else {
		v_col = base;
	}
}

void fragment() {
	ALBEDO = v_col;
	ROUGHNESS = rough;
}
