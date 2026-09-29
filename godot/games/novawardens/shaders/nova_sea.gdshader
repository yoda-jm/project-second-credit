// Nova Wardens night sea: a calm, glossy dark bay. Slow ripples (their normals fade with distance), the sky's
// gradient reflected by fresnel, the moon's glittering path, the lighthouse beam sweeping over the water, and a
// far edge that melts into the sky's horizon colour (the sea is a disc round the camera; its rim is the horizon).
shader_type spatial;
render_mode unshaded, fog_disabled, shadows_disabled;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 deep_col : source_color = vec3(0.01, 0.02, 0.05);
uniform vec3 sky_col : source_color = vec3(0.06, 0.08, 0.18);      // what the water reflects high up
uniform vec3 horizon_col : source_color = vec3(0.14, 0.16, 0.3);   // the sky at the horizon (the rim fades to it)
uniform vec3 moon_dir = vec3(0.4, 0.21, -0.89);
uniform vec3 moon_col : source_color = vec3(0.85, 0.9, 1.0);
uniform float glint = 1.0;
uniform vec3 camera_pos = vec3(5.6, 5.8, 22.0);
uniform float radius = 200.0;
uniform vec3 beam_pos = vec3(-39.0, 4.0, -86.0);   // the lighthouse lantern
uniform vec3 beam_dir = vec3(1.0, 0.0, 0.0);       // where its beam points now (either way)
uniform vec3 beam_col : source_color = vec3(1.0, 0.9, 0.7);
uniform float beam = 0.35;
uniform vec3 city_col : source_color = vec3(1.0, 0.6, 0.3);
uniform float city_glow = 0.12;
uniform float alarm = 0.0;
uniform float alarm_pulse = 0.0;
uniform float flash = 0.0;
uniform vec3 flash_col : source_color = vec3(1.0, 0.85, 0.7);

varying vec3 wpos;

vec2 ripple_grad(vec2 p, float t) {
	float e = 0.12;
	vec2 a = p * 0.35 + vec2(t * 0.05, t * 0.02);
	vec2 b = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * p * 1.1 - vec2(t * 0.09, -t * 0.04);
	float a0 = nw_noise(a), ax = nw_noise(a + vec2(e, 0.0)), az = nw_noise(a + vec2(0.0, e));
	float b0 = nw_noise(b), bx = nw_noise(b + vec2(e, 0.0)), bz = nw_noise(b + vec2(0.0, e));
	return (vec2(ax - a0, az - a0) * 0.9 + vec2(bx - b0, bz - b0) * 0.45) / e;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 v = wpos - camera_pos;
	float dist = length(v.xz);
	vec3 vd = normalize(v);
	float fade = 1.0 / (1.0 + dist * 0.02);
	// long swell stretched along x (so the glitter breaks into horizontal flecks), plus fine ripples
	vec2 g = ripple_grad(wpos.xz * vec2(0.6, 1.6), clock) * 0.08;
	g += ripple_grad(wpos.xz * vec2(1.8, 4.5) + 7.0, clock * 1.6) * 0.03;
	g *= mix(0.35, 1.0, fade);
	vec3 n = normalize(vec3(-g.x, 1.0, -g.y));
	vec3 r = reflect(vd, n);
	float fr = 0.02 + 0.98 * pow(1.0 - clamp(dot(-vd, n), 0.0, 1.0), 5.0);
	float re = max(r.y, 0.0);
	vec3 refl = mix(horizon_col, sky_col, smoothstep(0.0, 0.25, re));
	vec3 col = mix(deep_col, refl, clamp(fr, 0.0, 1.0));
	// the moon's path: a sharp glint and a broader sheen, broken by the ripples
	vec3 md = normalize(moon_dir);
	float m = max(dot(r, md), 0.0);
	float path = pow(m, 900.0) * 6.0 + pow(m, 120.0) * 0.9 + pow(m, 18.0) * 0.08;
	float sparkle = 0.5 + 0.5 * sin(clock * 3.0 + nw_hash(floor(wpos.xz * vec2(1.5, 4.0))) * 40.0);
	col += moon_col * path * glint * mix(0.6, 1.2, sparkle);
	// the lighthouse beam brushing the water
	vec2 bp = wpos.xz - beam_pos.xz;
	float bl = length(bp);
	vec2 bd = normalize(beam_dir.xz);
	float along = abs(dot(bp, bd));
	float across = abs(bp.x * bd.y - bp.y * bd.x);
	float cone = smoothstep(0.06 * along + 1.0, 0.0, across) * exp(-along * 0.025) * smoothstep(3.0, 12.0, bl);
	col += beam_col * beam * cone * (0.4 + 0.6 * fr * 4.0);
	// the town's light on the near water, and the alarm's red
	float near_shore = exp(-max(dist - 110.0, 0.0) * 0.02) * smoothstep(60.0, 110.0, dist);
	col += city_col * city_glow * near_shore * (0.5 + fr);
	col += vec3(1.0, 0.06, 0.03) * alarm * (0.3 + 0.7 * alarm_pulse) * near_shore * 0.12;
	col += flash_col * flash * 0.04 * (0.3 + fr * 3.0);
	// the rim melts into the horizon
	col = mix(col, horizon_col, smoothstep(radius * 0.55, radius * 0.99, dist));
	ALBEDO = col;
}
