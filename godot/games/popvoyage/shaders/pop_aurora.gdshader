// Pop Voyage aurora: additive curtains (UV.x along a curtain, UV.y from its hem to its top) that ripple in the solar
// wind; bright green hem, teal body, violet crown, and rays that slide along the fold.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform vec3 hem : source_color = vec3(0.45, 1.0, 0.55);
uniform vec3 body : source_color = vec3(0.1, 0.85, 0.7);
uniform vec3 crown : source_color = vec3(0.55, 0.25, 0.95);
uniform float strength = 0.6;
uniform float fold = 3.0;

float hash(float p) {
	return fract(sin(p * 127.1) * 43758.5453);
}

float n1(float x) {
	float i = floor(x), f = fract(x);
	return mix(hash(i), hash(i + 1.0), f * f * (3.0 - 2.0 * f));
}

void vertex() {
	float u = UV.x;
	float t = TIME;
	VERTEX.z += (sin(u * 11.0 + t * 0.25) * 0.6 + sin(u * 4.3 - t * 0.17)) * fold;
	VERTEX.x += sin(u * 7.0 + t * 0.21) * fold * 0.5;
	VERTEX.y += sin(u * 5.0 - t * 0.3) * fold * 0.4 * UV.y;
}

void fragment() {
	float u = UV.x, v = UV.y;
	float t = TIME;
	float rays = n1(u * 90.0 + t * 0.8) * 0.55 + n1(u * 31.0 - t * 0.35) * 0.45;
	rays = pow(rays, 1.6);
	vec3 c = mix(hem, body, smoothstep(0.02, 0.35, v));
	c = mix(c, crown, smoothstep(0.5, 1.0, v) * 0.8);
	float foot = smoothstep(0.0, 0.05, v) * (1.0 - smoothstep(0.03, 0.25, v) * 0.45);
	float top = 1.0 - smoothstep(0.4, 1.0, v);
	float ends = smoothstep(0.0, 0.12, u) * smoothstep(1.0, 0.88, u);
	float breathe = 0.75 + 0.25 * sin(t * 0.4 + u * 6.0);
	ALBEDO = c * strength * foot * (0.15 + top * 0.85) * (0.2 + rays * 1.4) * ends * breathe;
}
