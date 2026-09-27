shader_type spatial;
render_mode unshaded, blend_add, cull_back, depth_draw_never, fog_disabled;
// Prism Breaker tunnel: a neon grid on the inside of a long box behind the field, rushing towards the viewer.
// Rings of light run along it on the beat ("pulse"); "speed" goes up between walls (the warp).
uniform vec3 col_a : source_color = vec3(0.15, 0.55, 1.0);
uniform vec3 col_b : source_color = vec3(0.9, 0.2, 1.0);
uniform float pulse = 0.0;
uniform float speed = 2.0;
uniform float travel = 0.0;   // integrated speed, set by the view (so changes of speed never jump)
uniform float cell = 2.0;
uniform float fade = 0.028;
varying vec3 wpos;
varying vec3 wnrm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float line(float v, float w) {
	float f = abs(fract(v) - 0.5);
	return smoothstep(0.5 - w, 0.5, f);
}

void fragment() {
	float z = wpos.z + travel;
	vec3 an = abs(wnrm);
	float across = an.x > 0.5 ? wpos.y : wpos.x;
	float depth = -wpos.z;
	// thinner lines far away (they alias less)
	float w = mix(0.035, 0.08, clamp(depth / 80.0, 0.0, 1.0));
	float g = max(line(across / cell, w), line(z / cell, w));
	// rings: a bright band every 16 units, plus the beat ring
	float ring = smoothstep(0.93, 1.0, 1.0 - abs(fract(z / 16.0) - 0.5) * 2.0);
	float d = exp(-max(depth, 0.0) * fade);
	vec3 c = mix(col_a, col_b, 0.5 + 0.5 * sin(z * 0.05 + TIME * 0.3));
	float near_fade = smoothstep(-2.0, 6.0, depth);  // no hard edge where the tunnel starts
	float k = (g * 0.3 + ring * 1.0 * (0.35 + pulse)) * d * near_fade;
	ALBEDO = c * k * (0.8 + pulse * 1.2);
}
