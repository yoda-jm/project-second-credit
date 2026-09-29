// Jelly Spike sea: a rolling swell that calms towards the shore, turquoise shallows over the sand, and breakers:
// lines of foam that roll in towards the beach once a cycle (UV.y is the distance out from the waterline in metres,
// written by tools/blender/jellyspike_beach.py). The swash strip (beach_swash) runs up the sand on the same clock.
shader_type spatial;
render_mode specular_schlick_ggx;

uniform vec3 deep_col : source_color = vec3(0.02, 0.35, 0.55);
uniform vec3 far_col : source_color = vec3(0.3, 0.6, 0.8);
uniform vec3 shallow_col : source_color = vec3(0.2, 0.85, 0.8);
uniform vec3 sand_col : source_color = vec3(0.85, 0.8, 0.6);
uniform vec3 foam_col : source_color = vec3(0.97, 0.99, 1.0);
uniform vec3 sheen_col : source_color = vec3(0.8, 0.9, 1.0);
uniform float wave_height = 0.12;
uniform float period = 6.5;        // seconds between breakers (shared with the swash)
uniform float breaker_start = 16.0; // metres out where a breaker line forms
uniform float gloss = 0.06;
uniform float specular = 0.25;
uniform float foam = 1.0;
uniform float far_dist = 300.0;
uniform vec3 glint_dir = vec3(0.3, 0.1, -0.95); // towards the sun or the moon: its path of glitter on the water
uniform vec3 glint_col : source_color = vec3(1.0, 0.8, 0.5);
uniform float glint = 0.0;
uniform float glint_path = 0.0;   // a broad warm column under a low sun (golden hour)
uniform float glint_ripple = 2.5; // how rough the mirror is: wider, more broken glitter
uniform float sheen = 0.15;       // how much of the horizon colour the grazing water mirrors

varying vec3 wpos;
varying float dist_out;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

// the breaker clock at x (the same function as beach_swash)
float cycle(float x) {
	return fract(TIME / period + 0.08 * sin(x * 0.045) + 0.05 * sin(x * 0.11 + 1.3));
}

vec3 waves(vec2 p, float t) {
	vec3 r = vec3(0.0);
	vec2 dirs[4] = {vec2(0.1, 1.0), vec2(0.6, 0.8), vec2(-0.5, 0.9), vec2(1.0, 0.25)};
	float len[4] = {11.0, 6.3, 3.4, 2.1};
	for (int i = 0; i < 4; i++) {
		vec2 dd = normalize(dirs[i]);
		float k = 6.2831 / len[i];
		float w = sqrt(9.8 * k) * 0.5;
		float a = len[i] / 11.0;
		float ph = dot(dd, p) * k + t * w;
		r.x += a * sin(ph);
		r.yz += a * k * cos(ph) * dd;
	}
	return r;
}

float crest_at(float x) {
	return breaker_start * (1.0 - cycle(x));
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	dist_out = UV.y;
	float calm = smoothstep(1.0, 30.0, dist_out);
	vec3 w = waves(wpos.xz, TIME);
	float dc = crest_at(wpos.x);
	float swell = exp(-pow((dist_out - dc) / 1.6, 2.0)) * smoothstep(0.0, 5.0, dist_out) * 0.12;
	VERTEX.y += w.x * wave_height * calm + swell;
}

void fragment() {
	float t = TIME;
	float cam_d = length(wpos - CAMERA_POSITION_WORLD);
	float fade = 1.0 / (1.0 + cam_d * 0.025);
	float d = dist_out;
	vec3 w = waves(wpos.xz, t);
	vec2 g = w.yz * wave_height * smoothstep(1.0, 30.0, d);
	vec2 rp = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * wpos.xz * 1.4;
	float e = 0.15;
	float n0 = vnoise(rp + vec2(t * 0.6, t * 0.3));
	float nx = vnoise(rp + vec2(e, 0.0) + vec2(t * 0.6, t * 0.3));
	float nz = vnoise(rp + vec2(0.0, e) + vec2(t * 0.6, t * 0.3));
	vec2 rp2 = mat2(vec2(0.6, -0.8), vec2(0.8, 0.6)) * wpos.xz * 3.3 - vec2(t * 0.9, t * 0.4);
	float m0 = vnoise(rp2), mx = vnoise(rp2 + vec2(e, 0.0)), mz = vnoise(rp2 + vec2(0.0, e));
	g += (vec2(nx - n0, nz - n0) * 0.12 + vec2(mx - m0, mz - m0) * 0.06) / e;
	g *= fade;
	vec3 nw = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	float far = smoothstep(30.0, far_dist, cam_d);
	// colour: sand showing through at the edge, turquoise shallows, deep blue, the far haze colour
	vec3 col = mix(shallow_col, deep_col, smoothstep(3.0, 26.0, d));
	col = mix(col, far_col, far);
	col = mix(col, sand_col, smoothstep(1.4, 0.0, d) * 0.55);
	// caustic shimmer in the shallows
	float ca = vnoise(wpos.xz * 1.7 + vec2(t * 0.35, -t * 0.25)) * vnoise(wpos.xz * 2.3 - vec2(t * 0.3, t * 0.2));
	col += shallow_col * smoothstep(0.25, 0.55, ca) * smoothstep(8.0, 1.0, d) * 0.35;
	float fr = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 5.0);
	col = mix(col, sheen_col, fr * sheen);
	// the breakers: a crest line rolling in, foam trailing behind it, lace in the surf zone
	float dc = crest_at(wpos.x);
	float ph = cycle(wpos.x);
	float fn = vnoise(vec2(wpos.x * 1.3, d * 1.9) + vec2(t * 0.2, 0.0)) * 0.6 + vnoise(wpos.xz * 4.0 + t * 0.3) * 0.4;
	float grow = smoothstep(0.0, 0.35, ph);            // the line forms as it rolls in
	float line = smoothstep(0.55 + 0.3 * grow, 0.0, abs(d - dc) - 0.15) * grow;
	float trail = smoothstep(dc - 0.2, dc + 0.4, d) * smoothstep(dc + 3.5 * grow + 0.5, dc, d) * grow;
	float surf = smoothstep(4.5, 0.5, d);
	float lace = line * smoothstep(0.25, 0.5, fn) + trail * smoothstep(0.5, 0.75, fn) * 0.8
		+ surf * smoothstep(0.55, 0.8, fn) * 0.7;
	lace = clamp(lace, 0.0, 1.0);
	col = mix(col, foam_col, lace * foam * (1.0 - far));
	// the glitter path: sparkles where the ripples mirror the sun (or the moon) to the camera
	if (glint > 0.0) {
		vec3 vd = normalize(wpos - CAMERA_POSITION_WORLD);
		vec3 nwg = normalize(vec3(-g.x * glint_ripple, 1.0, -g.y * glint_ripple));
		float r = max(dot(reflect(vd, nwg), normalize(glint_dir)), 0.0);
		// the smooth column: the reflection of the sun's halo off the gently tilted swell
		vec3 nws = normalize(vec3(-g.x * 0.6, 1.0, -g.y * 0.6));
		float rs = max(dot(reflect(vd, nws), normalize(glint_dir)), 0.0);
		float sparkle = pow(r, 350.0) * 6.0 + pow(r, 40.0) * 0.25;
		float column = (pow(rs, 60.0) * 0.8 + pow(rs, 12.0) * 0.18) * glint_path;
		EMISSION = glint_col * (sparkle + column) * glint * (1.0 - clamp(lace, 0.0, 1.0));
	}
	ALBEDO = col;
	ROUGHNESS = gloss + far * 0.1 + lace * 0.4;
	SPECULAR = specular;
}
