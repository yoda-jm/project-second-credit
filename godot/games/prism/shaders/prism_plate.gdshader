shader_type spatial;
render_mode specular_schlick_ggx;
// Prism Breaker back plate: dark glossy glass behind the field with a faint hex lattice. Shock waves (up to eight,
// "waves": xy = field point, z = age in seconds, w = strength) run across it as rings of light when bricks break.
uniform vec3 base : source_color = vec3(0.012, 0.016, 0.04);
uniform vec3 line_col : source_color = vec3(0.15, 0.45, 1.0);
uniform float pulse = 0.0;
uniform vec4 waves[8];
uniform vec3 wave_cols[8];
uniform float lattice = 0.1;
varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hexdist(vec2 p) {
	p = abs(p);
	return max(dot(p, normalize(vec2(1.0, 1.7320508))), p.x);
}

void fragment() {
	vec2 p = wpos.xy * 1.4;
	vec2 r = vec2(1.0, 1.7320508);
	vec2 h = r * 0.5;
	vec2 a = mod(p, r) - h;
	vec2 b = mod(p - h, r) - h;
	vec2 g = dot(a, a) < dot(b, b) ? a : b;
	float edge = smoothstep(0.44, 0.5, hexdist(g));
	vec3 e = line_col * edge * (lattice + pulse * 0.25);
	for (int i = 0; i < 8; i++) {
		vec4 w = waves[i];
		if (w.w <= 0.0) continue;
		float d = distance(wpos.xy, w.xy);
		float rad = w.z * 9.0;
		float ring = exp(-pow((d - rad) * 3.0, 2.0)) * w.w * exp(-w.z * 2.5);
		e += wave_cols[i] * ring * (0.25 + edge * 1.6);
	}
	// edges of the field fade to black so the frame's neon stands out
	ALBEDO = base;
	ROUGHNESS = 0.32;
	METALLIC = 0.45;
	SPECULAR = 0.35;
	EMISSION = e;
}
