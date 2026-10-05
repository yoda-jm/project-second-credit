// Tinplate Turbo gravel trap: fine stones in a pale bed, raked lines, darker at the edge where it meets the barrier.
// UV.x 0 at the barrier, 1 at the outer edge; UV.y metres along. Our own shader (CC BY-SA 4.0).
shader_type spatial;

uniform vec4 bed : source_color = vec4(0.82, 0.74, 0.6, 1.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec2 g = vec2(UV.x * 30.0, UV.y * 12.0);
	float stone = hash(floor(g));
	vec3 col = bed.rgb * (0.78 + 0.35 * stone);
	col *= 0.92 + 0.08 * sin(UV.y * 18.0 + UV.x * 2.0);
	col *= mix(0.8, 1.0, smoothstep(0.0, 0.15, UV.x));
	ALBEDO = col;
	ROUGHNESS = 0.95;
	ALPHA = smoothstep(1.0, 0.8, UV.x);
}
