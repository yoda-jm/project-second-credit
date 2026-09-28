shader_type spatial;
// Henhouse Heist: the far country at golden hour, three ranges of rolling hills fading into the warm haze, lines
// of poplars on the nearest ridge, the low sun's glow behind them. Transparent above the hills.

render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec2 size = vec2(160.0, 24.0);
uniform vec3 haze : source_color = vec3(1.0, 0.76, 0.52);
uniform vec3 near_col : source_color = vec3(0.42, 0.42, 0.3);
uniform vec3 far_col : source_color = vec3(0.72, 0.52, 0.52);
uniform float sun_x = 0.7;
uniform float seed = 0.0;
uniform float layers_near = 1.0;  // 1: the nearest range has poplars

float hash(float x) { return fract(sin(x * 91.7) * 43758.5453); }
float n1(float x) {
	float i = floor(x);
	float f = fract(x);
	float u = f * f * (3.0 - 2.0 * f);
	return mix(hash(i), hash(i + 1.0), u);
}
float ridge(float x, float s, float amp, float base) {
	return base + amp * (n1(x * 0.07 + s) * 0.6 + n1(x * 0.19 + s * 2.0) * 0.3 + n1(x * 0.6 + s) * 0.1);
}

void fragment() {
	vec2 q = vec2((UV.x - 0.5) * size.x, (1.0 - UV.y) * size.y);  // metres: x across, y up from the bottom
	float a = 0.0;
	vec3 col = haze;
	for (int i = 0; i < 3; i++) {
		float k = float(i) / 2.0;  // 0 far, 1 near
		float h = ridge(q.x, 3.1 * float(i) + 1.0 + seed, mix(9.0, 5.0, k), mix(6.0, 1.5, k));
		float inside = smoothstep(0.08, -0.08, q.y - h);
		if (i == 2 && layers_near > 0.5) {
			// poplars along the nearest ridge, in clumps
			float cell = 1.3;
			float c = floor(q.x / cell);
			float th = (1.8 + hash(c) * 2.0) * step(0.5, n1(c * 0.23 + 7.0));
			float tx = (fract(q.x / cell) - 0.5) * cell;
			float hc = ridge((c + 0.5) * cell, 3.1 * float(i) + 1.0 + seed, mix(9.0, 5.0, k), mix(6.0, 1.5, k));
			float e = length(vec2(tx / 0.42, (q.y - hc - th * 0.45) / max(th * 0.55, 0.01)));
			inside = max(inside, smoothstep(1.05, 0.95, e) * step(0.1, th));
		}
		vec3 c = mix(far_col, near_col, k);
		// the haze thickens towards the low sun
		float sun = exp(-abs(UV.x - sun_x) * 5.0);
		c = mix(c, haze, (1.0 - k) * 0.45 + sun * 0.3 * (1.0 - k * 0.5));
		// soft lit tops
		c += haze * 0.25 * smoothstep(-1.2, 0.0, q.y - h) * inside;
		col = mix(col, c, inside);
		a = max(a, inside);
	}
	// the foot of the hills melts into the haze
	col = mix(col, haze, smoothstep(3.0, 0.0, q.y) * 0.5);
	ALBEDO = col;
	ALPHA = a;
}
