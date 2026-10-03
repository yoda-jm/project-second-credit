shader_type spatial;
// Marble Drift: the backdrop's particles (our own design, CC BY-SA 4.0): shape 0 a soft glowing dot (motes, glints,
// snow), shape 1 a rain streak (stretched along the particle's own up axis, which follows its velocity, and turned
// to face the camera). Additive; the colour comes from the particle (COLOR) times emit.
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform int shape = 0;
uniform float emit = 1.0;

varying vec4 v_col;

void vertex() {
	v_col = COLOR;
	vec3 pos = MODEL_MATRIX[3].xyz;
	vec3 to_cam = normalize(CAMERA_POSITION_WORLD - pos);
	if (shape == 1) {
		vec3 up = MODEL_MATRIX[1].xyz;
		float len = length(up);
		up /= max(len, 1e-4);
		vec3 right = normalize(cross(up, to_cam)) * length(MODEL_MATRIX[0].xyz);
		vec3 w = pos + right * VERTEX.x + up * len * VERTEX.y;
		POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(w, 1.0);
	} else {
		vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), to_cam) + vec3(1e-4, 0.0, 0.0));
		vec3 up = cross(to_cam, right);
		float s = length(MODEL_MATRIX[0].xyz);
		vec3 w = pos + (right * VERTEX.x + up * VERTEX.y) * s;
		POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(w, 1.0);
	}
}

void fragment() {
	vec2 c = UV - 0.5;
	float a;
	if (shape == 1) {
		a = (1.0 - smoothstep(0.0, 0.5, abs(c.x))) * smoothstep(0.5, 0.1, abs(c.y));
	} else {
		float r = length(c) * 2.0;
		a = exp(-r * r * 5.0) + (1.0 - smoothstep(0.0, 0.25, r)) * 0.6;
	}
	ALBEDO = v_col.rgb * a * v_col.a * emit;
}
