shader_type spatial;
// Hopline canal: green-blue water with a slow swell and two scrolling layers of ripples. Sky colour at grazing angles
// (fresnel), twinkling sun sparkles, the street lamps glittering on it at night, rings and a wake round every log and
// turtle (the view passes where they float), and splash rings where the frog lands or sinks.
// Screen-space reflections (set in the Environment) add the logs and turtles upside down.

render_mode cull_back;

uniform vec3 deep : source_color = vec3(0.05, 0.2, 0.24);
uniform vec3 shallow : source_color = vec3(0.14, 0.38, 0.38);
uniform vec3 sky : source_color = vec3(0.6, 0.75, 0.9);
uniform vec3 sun_dir = vec3(0.4, 0.7, 0.5);      // towards the sun (world)
uniform vec3 sun_col : source_color = vec3(1.0, 0.9, 0.7);
uniform float sparkle = 1.0;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
// riders: (centre x, centre z, half length, how far up 0..1); rider_v: velocity along x
uniform vec4 riders[20];
uniform float rider_v[20];
uniform int rider_count = 0;
// splash rings: (x, z, age in seconds, strength)
uniform vec4 rings[8];
// lamps: (x, y, z, energy), all the same colour
uniform vec4 lamps[16];
uniform int lamp_count = 0;
uniform vec3 lamp_col : source_color = vec3(1.0, 0.75, 0.4);

varying vec3 world_pos;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += sin(world_pos.x * 1.3 + TIME * 1.2) * 0.02 + sin(world_pos.z * 2.1 + TIME * 0.9) * 0.015;
}

void fragment() {
	float t = TIME;
	vec2 p = world_pos.xz;
	// ripples: two layers of the shared water normal map, drifting across each other
	vec3 n1 = texture(normal_map, p * 0.22 + vec2(t * 0.03, t * 0.012)).rgb * 2.0 - 1.0;
	vec3 n2 = texture(normal_map, p * 0.47 + vec2(-t * 0.045, t * 0.02)).rgb * 2.0 - 1.0;
	vec2 slope = n1.xy * 0.8 + n2.xy * 0.55;
	// the riders stir the water: a soft collar of foam, rings running out, a wake behind
	float foam = 0.0;
	for (int i = 0; i < rider_count; i++) {
		vec4 r = riders[i];
		vec2 q = p - r.xy;
		float v = rider_v[i];
		float ax = max(abs(q.x) - r.z, 0.0);
		float d = length(vec2(ax, q.y * 1.35)) - 0.3;
		if (d > 2.2) continue;
		float up = r.w;
		vec2 g = normalize(vec2(sign(q.x) * ax, q.y) + vec2(0.0001));
		float fall = exp(-max(d, 0.0) * 2.6);
		float wave = sin(d * 16.0 - t * 5.0);
		slope += g * wave * fall * 0.55 * (0.35 + 0.65 * up);
		foam += smoothstep(0.1, -0.05, d) * smoothstep(-0.35, -0.05, d) * (0.3 + 0.25 * wave) * up;
		// the wake trails the rider: behind it, on the side it comes from
		float behind = -q.x * sign(v) - r.z;
		if (behind > 0.0) {
			float w = exp(-behind * 0.9) * smoothstep(0.45 + behind * 0.12, 0.0, abs(q.y)) * min(abs(v), 2.0) * 0.16;
			foam += w * (0.5 + 0.5 * sin(behind * 9.0 - t * 6.0 + q.y * 12.0)) * up;
		}
		// a diving turtle leaves a boil of foam
		foam += (1.0 - up) * smoothstep(0.25, -0.2, d) * (0.3 + 0.3 * sin(t * 9.0 + q.x * 7.0));
	}
	for (int i = 0; i < 8; i++) {
		vec4 s = rings[i];
		if (s.w <= 0.0) continue;
		float rad = 0.15 + s.z * 1.5;
		float d = length(p - s.xy) - rad;
		float fade = s.w * clamp(1.0 - s.z / 1.3, 0.0, 1.0);
		float ring = exp(-d * d * 60.0) * fade;
		slope += normalize(p - s.xy + vec2(0.0001)) * ring * 0.9;
		foam += ring * 0.8;
	}
	vec3 n = normalize(vec3(slope.x * 0.35, 1.0, slope.y * 0.35));
	NORMAL_MAP = vec3(slope.x * 0.3 + 0.5, slope.y * 0.3 + 0.5, 1.0);
	NORMAL_MAP_DEPTH = 1.0;
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	vec3 v = normalize(cam - world_pos);
	float fres = pow(1.0 - clamp(dot(n, v), 0.0, 1.0), 4.0);
	vec3 col = mix(deep, shallow, 0.5 + 0.5 * slope.x);
	// the edges of the canal are shallower
	float edge = smoothstep(1.2, 0.0, min(abs(p.y + 0.55), abs(p.y + 5.45)));
	col = mix(col, shallow * 1.15, edge * 0.5);
	col = mix(col, sky, clamp(0.04 + fres * 0.6, 0.0, 1.0));
	foam = clamp(foam, 0.0, 1.0);
	ALBEDO = mix(col, vec3(0.9, 0.96, 1.0), foam * 0.8);
	ROUGHNESS = mix(0.05, 0.5, foam);
	METALLIC = 0.0;
	SPECULAR = 0.6;
	// sparkles: tight glints of the sun on the ripples, twinkling in cells
	vec3 h = normalize(normalize(sun_dir) + v);
	float glint = pow(max(dot(n, h), 0.0), 380.0);
	vec2 cell = floor(p * 7.0);
	float tw = hash(cell);
	vec2 inner = fract(p * 7.0) - 0.5 - (vec2(hash(cell + 3.1), hash(cell + 7.7)) - 0.5) * 0.6;
	float star = smoothstep(0.14, 0.0, length(inner)) + smoothstep(0.03, 0.0, abs(inner.x) * abs(inner.y) * 8.0) * smoothstep(0.3, 0.0, length(inner)) * 0.5;
	float twinkle = step(0.8, tw) * star * pow(max(sin(t * (2.0 + tw * 3.0) + tw * 40.0), 0.0), 4.0);
	float sp = glint * 1.2 + twinkle * (0.25 + pow(max(dot(n, h), 0.0), 16.0)) * 1.6;
	vec3 em = sun_col * sp * sparkle;
	// the lamps glitter on the water at night
	for (int i = 0; i < lamp_count; i++) {
		vec4 l = lamps[i];
		vec3 ld = l.xyz - world_pos;
		float dist2 = dot(ld, ld);
		vec3 hl = normalize(normalize(ld) + v);
		float s = pow(max(dot(n, hl), 0.0), 90.0);
		em += lamp_col * l.w * (s * 3.0 + 0.25 * exp(-dist2 * 0.35)) / (1.0 + dist2 * 0.25);
		// and each lamp on the near quay lays a broken column of light across the canal
		float out_ = -0.5 - p.y;
		if (l.z > -0.5 && out_ > 0.0) {
			float dx = p.x - l.x + slope.x * 0.35 + sin(p.y * 9.0 + t * 2.0) * 0.05;
			float broken = smoothstep(-0.05, 0.6, slope.y * 1.2 + sin(p.y * 13.0 + t * 1.3) * 0.35 + 0.1);
			em += lamp_col * l.w * exp(-dx * dx * 18.0) * exp(-out_ * 0.5) * broken * 0.9;
		}
	}
	EMISSION = em + vec3(0.8, 0.9, 1.0) * foam * 0.06;
}
