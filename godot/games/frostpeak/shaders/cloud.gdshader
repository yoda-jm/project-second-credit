shader_type spatial;
// A cloud bank for the far peaks: a billboard (turning about its vertical axis only) filled with drifting,
// billowing noise; bright and warm where it faces the low sun, blue-grey underneath, soft at every edge.
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform float seed = 0.0;
uniform vec3 lit : source_color = vec3(1.0, 0.95, 0.88);
uniform vec3 shade : source_color = vec3(0.62, 0.68, 0.8);
uniform float opacity = 0.8;
uniform vec3 sun_dir = vec3(-0.8, 0.35, -0.4);  // towards the sun (set by the view)
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

float fbm(vec2 p) {
	float s = 0.0;
	float a = 0.5;
	for (int i = 0; i < 5; i++) {
		s += noise(p) * a;
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return s;
}

varying vec3 v_side;

void vertex() {
	// face the camera, upright
	vec3 cam = (INV_VIEW_MATRIX * vec4(0, 0, 0, 1)).xyz;
	vec3 centre = MODEL_MATRIX[3].xyz;
	vec3 to_cam = normalize(vec3(cam.x - centre.x, 0.0, cam.z - centre.z));
	vec3 right = normalize(cross(vec3(0, 1, 0), to_cam));
	vec3 wp = centre + right * VERTEX.x + vec3(0, 1, 0) * VERTEX.y;
	v_side = to_cam;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(wp, 1.0);
}

void fragment() {
	vec2 uv = UV;
	vec2 q = uv * 2.0 - 1.0;
	vec2 p = uv * 2.2 + vec2(seed, seed * 0.37) + vec2(TIME * 0.006, 0.0);
	float n = fbm(p * 1.8);
	// a round, billowing puff: soft all round, flatter underneath
	float r = length(vec2(q.x, q.y * (q.y > 0.0 ? 1.35 : 1.0)));
	float d = smoothstep(1.0, 0.35, r + (n - 0.5) * 0.75);
	// light: brighter towards the top and on the sun's side of the bank
	float facing = clamp(dot(normalize(v_side + vec3(0, 0.3, 0)), normalize(sun_dir)) * 0.5 + 0.5, 0.0, 1.0);
	float l = clamp(0.95 - uv.y * 0.75 + (n - 0.5) * 0.5, 0.0, 1.0) * (0.55 + 0.45 * facing);
	ALBEDO = mix(shade, lit, l);
	// soft where the puff meets the mountainside (no hard line through the rock)
	float depth = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 up = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	float scene_z = -up.z / up.w;
	float soft = clamp((scene_z + VERTEX.z) / 90.0, 0.0, 1.0);
	ALPHA = clamp(d * opacity * soft, 0.0, 1.0);
}
