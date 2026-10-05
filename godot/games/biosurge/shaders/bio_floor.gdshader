// Biosurge: the abyss floor far below the play plane: dark living tissue, veins, glowing pools that breathe.
// World-space patterns (xz), a gentle relief raised in the vertex stage. Our own code, CC BY-SA 4.0.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#include "res://games/biosurge/shaders/bio_noise.gdshaderinc"

uniform vec3 ground_color : source_color = vec3(0.02, 0.06, 0.05);
uniform vec3 ridge_color : source_color = vec3(0.06, 0.16, 0.13);
uniform vec3 pool_color : source_color = vec3(0.2, 1.0, 0.7);
uniform vec3 vein_color : source_color = vec3(0.3, 0.9, 0.6);
uniform float pool_energy = 2.5;
uniform float vein_energy = 0.8;
uniform float pool_share = 0.35;
uniform float relief = 1.6;
uniform float clock = 0.0;
uniform float pulse_rate = 0.5;
uniform float heart = 0.0;
uniform float flow = 0.0;

varying vec3 wpos;

// glowing pools round some of the cells' feature points: x the pool (sharp-edged), y a soft halo
vec2 pools(vec2 p, float share, float t) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 acc = vec2(0.0);
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			float id = bio_h1(i + g + 31.7);
			if (id < 1.0 - share) {
				continue;
			}
			vec2 r = g + bio_h2(i + g) * 0.7 + 0.15 - f;
			float rad = 0.09 + 0.1 * fract(id * 13.7);
			float d = length(r) / rad;
			float b = bio_beat(t + id * 3.0, heart);
			acc.x += smoothstep(1.0, 0.8, d) * (0.6 + 0.4 * b) * (0.55 + 0.45 * smoothstep(0.3, 0.95, d));
			acc.y += exp(-d * d * 0.7) * (0.5 + 0.5 * b);
		}
	}
	return acc;
}

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float h = bio_fbm(w.xz * 0.06) - 0.5;
	VERTEX.y += h * relief * 2.0;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xz;
	float n = bio_fbm(p * 0.09 + vec2(clock * flow, 0.0));
	float wob = (n - 0.5) * 0.5;
	vec2 pl = pools(p * 0.11 + wob, pool_share, clock * pulse_rate);
	float pool = clamp(pl.x, 0.0, 1.0);
	float b = bio_beat(clock * pulse_rate, heart);
	float ridge = smoothstep(0.35, 0.75, n);
	vec3 alb = mix(ground_color, ridge_color, ridge);
	float vn = bio_fbm(p * 0.18 + 4.0);
	float vein = 1.0 - smoothstep(0.0, 0.035, abs(vn - 0.5));
	float ripple = bio_fbm(p * 0.6 + vec2(clock * 0.15, -clock * 0.1));
	vec3 emit = pool_color * pool * pool_energy * (0.45 + 0.9 * ripple);
	emit += pool_color * pl.y * 0.12 * pool_energy;
	emit += vein_color * vein * vein_energy * (0.4 + 0.6 * b) * (0.4 + pl.y);
	ALBEDO = alb * (1.0 - pool * 0.7);
	ROUGHNESS = mix(0.5, 0.1, pool);
	EMISSION = emit;
}
