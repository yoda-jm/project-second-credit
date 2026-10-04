// Fuseflight backdrop lights: paper lanterns (brightest where the paper faces you, a candle's flicker), windows that
// come on and go off one by one, string bulbs in many colours with a chasing pattern, steady lamps and clock faces,
// beacons that blink. Unshaded HDR colour (feeds the glow); cells of world space vary each light.
shader_type spatial;
render_mode unshaded, shadows_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.8, 0.5);
uniform float energy = 2.5;
uniform float paper = 0.0;     // lantern: brighter facing the camera, warm rim
uniform float twinkle = 0.0;   // share of windows that are dark at any time (they swap slowly)
uniform float variety = 0.0;   // per-light brightness spread
uniform float hues = 0.0;      // 1 = every bulb its own colour (fairground string lights)
uniform float chase = 0.0;     // bulbs chasing along x
uniform float flicker = 0.0;   // candle flicker
uniform float blink = 0.0;     // on/off blinking
uniform float cell = 1.0;

varying vec3 wpos;

float hash3(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

vec3 hue(float h) {
	return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 c = floor(wpos / cell + 0.001);
	float h = hash3(c);
	float k = 1.0;
	vec3 col = color * COLOR.rgb;   // lanterns carry their tint in the vertex colour (white elsewhere)
	if (variety > 0.0) {
		k *= 1.0 - variety * 0.5 + variety * h;
	}
	if (hues > 0.0) {
		float pick = floor(h * 6.0);
		vec3 bulb = pick < 1.0 ? vec3(1.0, 0.25, 0.2) : pick < 2.0 ? vec3(1.0, 0.75, 0.2) : pick < 3.0 ? vec3(0.3, 1.0, 0.45)
				: pick < 4.0 ? vec3(0.3, 0.6, 1.0) : pick < 5.0 ? vec3(1.0, 0.35, 0.85) : vec3(1.0, 0.95, 0.85);
		col = mix(col, bulb, hues);
	}
	if (paper > 0.0) {
		// lit paper: the full colour facing you, deeper and dimmer towards the rim, a warm hot spot in the middle
		float f = abs(dot(NORMAL, VIEW));
		col = mix(col * vec3(0.9, 0.45, 0.35), col + vec3(0.0, 0.06, 0.02), pow(f, 1.2));
		k *= mix(0.45, 1.0, f);
	}
	if (twinkle > 0.0) {
		float slot = floor(TIME * 0.05 + h * 9.0);
		float on = step(twinkle, hash(vec2(h * 91.0, slot)));
		k *= mix(0.04, 1.0, on);
	}
	if (flicker > 0.0) {
		k *= 1.0 + flicker * 0.25 * (sin(TIME * 11.0 + h * 40.0) + sin(TIME * 6.3 + h * 17.0));
	}
	if (chase > 0.0) {
		float ph = fract((wpos.x + wpos.z) * 0.35 - TIME * 0.9);
		k *= mix(1.0, 0.35 + 0.9 * smoothstep(0.5, 0.0, abs(ph - 0.5) * 1.0), chase);
	}
	if (blink > 0.0) {
		k *= mix(1.0, step(0.6, fract(TIME * 0.45 + h)), blink);
	}
	ALBEDO = col * energy * k;
}
