// Fuseflight fireworks: one MultiMesh instance per burst or rocket, every spark worked out on the GPU from the
// burst's start time and the backdrop's own clock (deterministic, nothing simulated on the CPU).
// The mesh (built by FuseBackdrop) holds N spark quads: VERTEX = the spark's direction on the unit sphere, UV = the
// quad corner (x: tail 0 .. head 1, y: side), UV2 = (a random number, the spark's index / N); one extra quad with
// UV2.x = -1 is the burst's flash. Per instance: the transform's origin is the burst centre (a rocket's launch
// point), its basis turns and scales the burst (scale = radius; a rocket's basis Y is its rise), COLOR the main
// colour, INSTANCE_CUSTOM = (start time, kind, second hue (a rocket: its rise time), seed).
// Kinds: 0 peony, 1 willow, 2 ring, 3 chrysanthemum, 4 glitter, 5 crackle, 6 palm, 7 rocket.
// mirror = 1 draws the reflection: each spark mirrored in the plane y = water_y and laid on the water along the
// view ray (so it sits on the surface, behind the boats and the pier).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float clock = 0.0;
uniform float energy = 3.0;
uniform float mirror = 0.0;
uniform float water_y = -1.0;
uniform float width_scale = 1.0;

varying vec3 v_col;
varying float v_alpha;
varying vec2 v_uv;
varying float v_flash;
varying vec3 v_world;

vec3 hue(float h) {
	return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}

float h1(float x) {
	return fract(sin(x * 127.1 + 3.7) * 43758.5453);
}

vec3 on_water(vec3 p, vec3 cam) {
	vec3 m = vec3(p.x, 2.0 * water_y - p.y, p.z);
	float t = (water_y - cam.y) / min(m.y - cam.y, -0.001);
	return cam + (m - cam) * clamp(t, 0.0, 1.0) + vec3(0.0, 0.03, 0.0);
}

// position of a spark at age a: launched at speed v (world units), slowed by drag, pulled down by gravity
vec3 spark_at(vec3 c, vec3 v, float drag, float grav, float a) {
	return c + v * (1.0 - exp(-drag * a)) - vec3(0.0, grav * a * a * 0.5 / (1.0 + 0.7 * a), 0.0);
}

void vertex() {
	vec3 cam = CAMERA_POSITION_WORLD;
	vec3 c = MODEL_MATRIX[3].xyz;
	mat3 B = mat3(MODEL_MATRIX[0].xyz, MODEL_MATRIX[1].xyz, MODEL_MATRIX[2].xyz);
	float R = length(B[0]);
	float age = clock - INSTANCE_CUSTOM.x;
	int kind = int(INSTANCE_CUSTOM.y + 0.5);
	float p2 = INSTANCE_CUSTOM.z;
	float seed = INSTANCE_CUSTOM.w;
	float rnd = UV2.x;
	float idx = UV2.y;
	float a = max(age, 0.0);
	vec3 head = c;
	vec3 tail = c;
	float alpha = 0.0;
	vec3 col = COLOR.rgb;
	float wid = 1.0;
	bool hide = age < 0.0 || age > 7.0;
	v_flash = 0.0;
	if (rnd < -0.5) {
		// the flash at the heart of a burst
		v_flash = 1.0;
		hide = hide || kind == 7;
		alpha = exp(-a * 9.0) * (kind == 5 ? 0.5 : 0.22);
		col = mix(vec3(1.0, 0.95, 0.85), COLOR.rgb, 0.4);
		vec3 hc = mirror > 0.5 ? on_water(c, cam) : c;
		float rr = R * (kind == 5 ? 1.2 : 0.42) * (mirror > 0.5 ? 0.35 : 1.0);
		vec3 right = INV_VIEW_MATRIX[0].xyz;
		vec3 up = INV_VIEW_MATRIX[1].xyz;
		vec3 wp = hc + (right * (UV.x * 2.0 - 1.0) + up * (UV.y * 2.0 - 1.0)) * rr;
		v_uv = UV;
		v_col = col;
		v_alpha = hide ? 0.0 : alpha;
		v_world = wp;
		VERTEX = hide ? vec3(0.0) : (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
	} else {
		if (kind == 7) {
			// a rocket: spark 0 is the climbing head, sparks 1-10 the embers it sheds
			float T = max(p2, 0.1);
			vec3 rise = B[1];
			int k = int(idx * 160.0 + 0.5);
			hide = hide || k > 10;
			float wob = sin(a * 9.0 + seed * 20.0) * 0.012;
			if (k == 0) {
				float u = clamp(a / T, 0.0, 1.0);
				float ut = clamp((a - 0.16) / T, 0.0, 1.0);
				head = c + rise * (1.0 - (1.0 - u) * (1.0 - u)) + B[0] * wob;
				tail = c + rise * (1.0 - (1.0 - ut) * (1.0 - ut));
				alpha = smoothstep(0.0, 0.05, a) * (1.0 - smoothstep(T - 0.05, T + 0.02, a)) * 0.9;
				col = vec3(1.0, 0.82, 0.55);
				wid = 0.8;
			} else {
				float born = a - float(k) * 0.07;
				float ub = clamp(born / T, 0.0, 1.0);
				float since = float(k) * 0.07;
				head = c + rise * (1.0 - (1.0 - ub) * (1.0 - ub)) - vec3(0.0, 1.2 * since * since, 0.0);
				tail = head + vec3(0.0, 0.05 * length(rise) * 0.02, 0.0);
				float fl = step(0.3, h1(float(k) * 13.0 + floor(a * 25.0) + seed));
				alpha = step(0.0, born) * step(born, T) * (1.0 - since / 0.75) * fl * 0.6;
				col = vec3(1.0, 0.6, 0.25);
				wid = 0.55;
			}
		} else {
			vec3 dir = VERTEX;
			float sp = 1.0 + (rnd - 0.5) * 0.16;
			float drag = 2.2;
			float life = 2.0;
			float grav = 0.32 * R;
			float trail = 0.09;
			vec3 c2 = hue(p2);
			bool second = false;
			if (kind == 1) {          // willow: gold, long, drooping
				drag = 1.5; life = 3.8; grav = 0.6 * R; trail = 0.7; wid = 0.75; sp = 0.85 + rnd * 0.15;
			} else if (kind == 2) {   // ring: a crisp circle, an inner ring in the second colour
				float an = idx * 6.2831853 * 2.0;
				dir = vec3(cos(an), sin(an), 0.0);
				second = idx > 0.5;
				sp = (second ? 0.55 : 1.0) * (1.0 + (rnd - 0.5) * 0.03);
				drag = 2.5; life = 1.8; grav = 0.22 * R; trail = 0.07;
			} else if (kind == 3) {   // chrysanthemum: long trails from the heart, then the colour change
				drag = 2.0; life = 2.4; trail = 0.38; wid = 0.8; second = rnd > 0.35;
			} else if (kind == 4) {   // glitter: a silver shell that strobes as it falls
				drag = 2.3; life = 2.7; grav = 0.45 * R; trail = 0.05; wid = 0.8;
			} else if (kind == 5) {   // crackle: a small quick pop
				drag = 5.0; life = 0.75; grav = 0.25 * R; trail = 0.04; wid = 0.7; sp = 0.6 + rnd * 0.5;
			} else if (kind == 6) {   // palm: a dozen fat comets
				hide = hide || idx > 0.08;
				drag = 1.3; life = 2.8; grav = 0.5 * R; trail = 0.55; wid = 1.9; sp = 1.0 + (rnd - 0.5) * 0.1;
			} else {                  // peony: the classic round shell; half the stars change colour
				second = rnd > 0.5;
			}
			life *= 0.85 + 0.3 * h1(idx * 71.0 + seed);
			vec3 v = B * dir * sp;
			head = spark_at(c, v, drag, grav, a);
			tail = spark_at(c, v, drag, grav, max(a - trail, 0.0));
			alpha = smoothstep(0.0, 0.04, a) * (1.0 - smoothstep(life * 0.55, life, a));
			float late = smoothstep(life * 0.5, life * 0.75, a);
			if (kind == 0 || kind == 3) {
				alpha *= mix(1.0, step(0.35, h1(idx * 91.0 + floor(a * 22.0) + seed)), late);
			}
			if (kind == 4) {
				float st = smoothstep(life * 0.25, life * 0.4, a);
				alpha *= mix(1.0, step(0.72, h1(idx * 53.0 + floor(a * 28.0) + seed)) * 2.2, st);
			}
			// white-hot at the burst, then the star's colour, then (some) the second colour
			vec3 base = col;
			if (kind == 1) {
				base = mix(vec3(1.0, 0.78, 0.38), vec3(1.0, 0.45, 0.15), a / life);
			} else if (kind == 6) {
				base = mix(vec3(1.0, 0.8, 0.45), col, smoothstep(0.3, 0.8, a / life));
			} else if (kind == 4) {
				base = mix(col, vec3(0.9, 0.95, 1.0), 0.6);
			} else if (second) {
				base = mix(col, c2, kind == 2 ? 1.0 : smoothstep(life * 0.35, life * 0.5, a));
			}
			col = mix(vec3(1.0, 0.96, 0.88) * 1.5, base, smoothstep(0.0, 0.16, a));
		}
		if (mirror > 0.5) {
			head = on_water(head, cam);
			tail = on_water(tail, cam);
			tail += vec3(0.0, 0.0, 0.012 * length(head - cam));   // a short smear towards the viewer
			alpha *= 0.42;
		}
		float dist = length(head - cam);
		wid *= 0.0022 * dist * width_scale;
		vec3 axis = head - tail;
		float L = length(axis);
		vec3 ax = L > 1e-4 ? axis / L : vec3(0.0, 1.0, 0.0);
		vec3 vd = normalize(head - cam);
		vec3 cr = cross(ax, vd);
		if (length(cr) < 1e-3) {
			cr = cross(vec3(0.0, 1.0, 0.0), vd);
		}
		vec3 side = normalize(cr);
		vec3 hx = head + ax * wid;
		vec3 tx = tail - ax * wid;
		vec3 wp = mix(tx, hx, UV.x) + side * (UV.y * 2.0 - 1.0) * wid;
		v_uv = UV;
		v_col = col;
		v_alpha = hide ? 0.0 : alpha;
		v_world = wp;
		VERTEX = (hide || alpha <= 0.001) ? vec3(0.0) : (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
	}
}

void fragment() {
	float a;
	if (v_flash > 0.5) {
		vec2 p = v_uv * 2.0 - 1.0;
		a = exp(-dot(p, p) * 5.0) - 0.007;
	} else {
		float across = v_uv.y * 2.0 - 1.0;
		float core = max(1.0 - across * across, 0.0);
		a = core * core * mix(0.08, 1.0, v_uv.x * v_uv.x);
	}
	if (mirror > 0.5) {
		a *= 0.45 + 0.55 * sin(v_world.z * 7.0 + v_world.x * 1.3 + clock * 5.0) * sin(v_world.z * 2.3 - clock * 3.0);
		a = max(a, 0.0);
	}
	ALBEDO = v_col * v_alpha * max(a, 0.0) * energy;
}
