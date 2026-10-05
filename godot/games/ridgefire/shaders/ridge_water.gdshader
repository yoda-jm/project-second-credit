// Ridgefire water: the sea, a river, a lead of open water in the ice. A swell and ripples whose normals fade with
// distance (the far water lies calm), the sky's colour by fresnel, the light of glowing things mirrored as long
// shimmering streaks (glow_pos / glow_col: the crater, the lava's mouth; a far source such as the moon is given as a
// direction with w < 0), foam on the shallows (vertex colour R) and the same aerial haze as the land.
shader_type spatial;
render_mode specular_schlick_ggx;

uniform vec3 deep_col : source_color = vec3(0.01, 0.03, 0.06);
uniform vec3 far_col : source_color = vec3(0.05, 0.08, 0.14);
uniform vec3 sky_col : source_color = vec3(0.2, 0.25, 0.4);
uniform vec3 shallow_col : source_color = vec3(0.05, 0.12, 0.14);
uniform vec3 foam_col : source_color = vec3(0.6, 0.65, 0.7);
uniform float wave_height = 0.3;
uniform float wave_scale = 1.0;      // wavelengths (1: 12 to 60 m)
uniform float ripple = 1.0;
uniform float flow = 0.0;            // a river: the ripples run along -z
uniform float gloss = 0.06;
uniform float far_dist = 500.0;
uniform vec4 glow_pos[4];            // xyz, w = radius (m); w < 0: xyz is a direction (the moon)
uniform vec4 glow_col[4];            // rgb, a = streak length (0..1)
uniform vec3 haze_col : source_color = vec3(0.6, 0.65, 0.75);
uniform vec3 haze_sun_col : source_color = vec3(1.0, 0.8, 0.6);
uniform vec3 sun_dir = vec3(0.5, 0.5, 0.5);
uniform float haze_start = 80.0;
uniform float haze_scale = 600.0;
uniform float haze_max = 0.8;
uniform float haze_sun_pow = 6.0;

varying vec3 wpos;
varying float shallow;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

vec3 waves(vec2 p, float t) {
	vec3 r = vec3(0.0);
	vec2 dirs[4] = {vec2(0.2, 1.0), vec2(0.7, 0.8), vec2(-0.5, 0.9), vec2(1.0, 0.25)};
	float len[4] = {60.0, 33.0, 19.0, 12.0};
	for (int i = 0; i < 4; i++) {
		vec2 dd = normalize(dirs[i]);
		float l = len[i] * wave_scale;
		float k = 6.2831 / l;
		float w = sqrt(9.8 * k) * 0.8;
		float a = l / 60.0;
		float ph = dot(dd, p) * k + t * w;
		r.x += a * sin(ph);
		r.yz += a * k * cos(ph) * dd;
	}
	return r;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	shallow = COLOR.r;
	VERTEX.y += waves(wpos.xz, TIME).x * wave_height;
}

void fragment() {
	float t = TIME;
	vec3 to = wpos - CAMERA_POSITION_WORLD;
	float dist = length(to);
	vec3 vd = to / dist;
	float fade = 1.0 / (1.0 + dist * 0.012);
	vec3 w = waves(wpos.xz, t);
	vec2 g = w.yz * wave_height;
	vec2 drift = vec2(t * 0.25, t * 0.12) + vec2(0.0, -flow * t);
	vec2 rp = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * wpos.xz * 0.45 + drift;
	float e = 0.15;
	float n0 = vnoise(rp), nx = vnoise(rp + vec2(e, 0.0)), nz = vnoise(rp + vec2(0.0, e));
	vec2 rp2 = mat2(vec2(0.6, -0.8), vec2(0.8, 0.6)) * wpos.xz * 1.1 - drift * 1.7;
	float m0 = vnoise(rp2), mx = vnoise(rp2 + vec2(e, 0.0)), mz = vnoise(rp2 + vec2(0.0, e));
	g += (vec2(nx - n0, nz - n0) * 0.1 + vec2(mx - m0, mz - m0) * 0.05) / e * ripple;
	g *= fade;
	vec3 nw = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	float far = smoothstep(30.0, far_dist, dist);
	vec3 col = mix(deep_col, far_col, far);
	col = mix(col, shallow_col, shallow * 0.8);
	float fr = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	vec3 em = sky_col * (0.12 + fr * 0.7);
	// mirrored lights: streaks that run down the water towards the viewer, broken by the waves
	vec3 r = reflect(vd, nw);
	for (int i = 0; i < 4; i++) {
		vec4 gp = glow_pos[i];
		vec3 gc = glow_col[i].rgb;
		if (dot(gc, gc) <= 0.0) {
			continue;
		}
		vec3 tg = gp.w < 0.0 ? normalize(gp.xyz) : normalize(gp.xyz - wpos);
		float az = 1.0 - dot(normalize(r.xz), normalize(tg.xz));
		float spread = gp.w < 0.0 ? 0.0004 : max(gp.w / max(length(gp.xyz - wpos), 1.0), 0.002) * 0.4;
		float side = exp(-az / (spread + 0.0004));
		float el = r.y - tg.y;
		float down = exp(-el * el / (0.004 + 0.06 * glow_col[i].a));
		em += gc * side * down * (0.3 + 0.7 * smoothstep(0.3, 0.7, vnoise(wpos.xz * vec2(0.4, 1.2) + vec2(0.0, t * 1.5))));
	}
	float lace = smoothstep(0.7, 0.95, shallow) * smoothstep(0.35, 0.6, vnoise(wpos.xz * 0.9 + vec2(t * 0.3, -t * 0.2)));
	vec3 alb = mix(col, foam_col, lace * 0.6);
	float f = haze_max * (1.0 - exp(-max(dist - haze_start, 0.0) / haze_scale));
	float s = pow(max(dot(vd, normalize(sun_dir)), 0.0), haze_sun_pow);
	ALBEDO = alb * (1.0 - f);
	EMISSION = em * (1.0 - f) + mix(haze_col, haze_sun_col, s) * f;
	ROUGHNESS = gloss + far * 0.04;
	SPECULAR = 0.6;
	METALLIC = 0.0;
}
