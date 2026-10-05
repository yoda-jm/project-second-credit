// Ridgefire backdrop lights: windows that come on and go off one by one, steady lamps, beacons that blink, the
// lit glass of a dome (panes, a frame, brighter low down), headlights. Unshaded HDR colour (feeds the glow); cells of
// world space vary each light. `tremor` (set by the backdrop when a big blast shakes the ground) makes them flicker.
shader_type spatial;
render_mode unshaded, shadows_disabled, cull_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.8, 0.5);
uniform float energy = 2.5;
uniform float twinkle = 0.0;   // share of windows dark at any time (they swap slowly)
uniform float variety = 0.0;   // per-light brightness spread
uniform float flicker = 0.0;
uniform float blink = 0.0;     // on/off blinking
uniform float blink_rate = 0.5;
uniform float dome = 0.0;      // glass panes in a frame, lit from inside
uniform float tremor = 0.0;
uniform float cell = 1.0;
uniform float fade_far = 0.0;  // dims with distance (m at which it halves)

varying vec3 wpos;
varying vec3 wnrm;

float hash3(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 c = floor(wpos / cell + 0.001);
	float h = hash3(c);
	float k = 1.0;
	vec3 col = color * COLOR.rgb;
	if (variety > 0.0) {
		k *= 1.0 - variety * 0.5 + variety * h;
	}
	if (twinkle > 0.0) {
		float slot = floor(TIME * 0.04 + h * 9.0);
		k *= mix(0.03, 1.0, step(twinkle, hash(vec2(h * 91.0, slot))));
	}
	if (flicker > 0.0) {
		k *= 1.0 + flicker * 0.25 * (sin(TIME * 11.0 + h * 40.0) + sin(TIME * 6.3 + h * 17.0));
	}
	if (blink > 0.0) {
		k *= mix(1.0, step(0.7, fract(TIME * blink_rate + h)), blink);
	}
	if (dome > 0.0) {
		// geodesic panes: a frame of dark struts, the glass brighter low down and towards you
		vec3 n = normalize(wnrm);
		float a = atan(n.z, n.x) * 6.0;
		float b = asin(clamp(n.y, -1.0, 1.0)) * 7.0;
		vec2 g = vec2(a + b * 0.5, b);
		vec2 fr = abs(fract(g) - 0.5);
		float strut = smoothstep(0.42, 0.47, max(fr.x, fr.y));
		float f = abs(dot(NORMAL, VIEW));
		float pane = hash(floor(g));
		col = mix(vec3(1.0, 0.72, 0.42) * 1.4, col, smoothstep(0.05, 0.55, n.y));   // the lamps inside, low down
		k *= mix((0.35 + 0.65 * pow(f, 2.0)) * (0.6 + 0.6 * pane) * mix(1.0, 0.55, smoothstep(-0.2, 1.0, n.y)), 0.05, strut);
	}
	if (tremor > 0.0) {
		k *= 1.0 - tremor * step(0.5, hash(vec2(h, floor(TIME * 18.0))));
	}
	if (fade_far > 0.0) {
		float d = length(wpos - CAMERA_POSITION_WORLD);
		k *= fade_far / (fade_far + d);
	}
	ALBEDO = col * energy * k;
}
