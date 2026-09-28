// Pop Voyage backdrop lights: windows that come on and go off one by one, lamps that flicker, aviation lights that
// blink, lava that pulses and flows. Unshaded HDR colour (feeds the glow). Cells of world space vary each light.
shader_type spatial;
render_mode unshaded, shadows_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.8, 0.5);
uniform float energy = 2.5;
uniform float twinkle = 0.0;   // share of windows that are dark at any time (they swap slowly)
uniform float variety = 0.0;   // per-light brightness and hue spread
uniform float flicker = 0.0;   // fast candle flicker
uniform float blink = 0.0;     // 1 = on/off blinking
uniform float pulse = 0.0;     // slow breathing (lava)
uniform float flow = 0.0;      // moving noise (lava)
uniform float cell = 1.0;

varying vec3 wpos;

float hash3(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 c = floor(wpos / cell + 0.001);
	float h = hash3(c);
	float k = 1.0;
	vec3 col = color;
	if (variety > 0.0) {
		k *= 1.0 - variety * 0.5 + variety * h;
		col = mix(col, col.gbr * 0.4 + col * 0.6, variety * step(0.8, fract(h * 7.0)) * 0.6);
	}
	if (twinkle > 0.0) {
		float slot = floor(TIME * 0.06 + h * 9.0);
		float on = step(twinkle, hash(vec2(h * 91.0, slot)));
		k *= mix(0.04, 1.0, on);
	}
	if (flicker > 0.0) {
		k *= 1.0 + flicker * 0.25 * (sin(TIME * 13.0 + h * 40.0) + sin(TIME * 7.3 + h * 17.0));
	}
	if (blink > 0.0) {
		k *= mix(1.0, step(0.55, fract(TIME * 0.5 + h)), blink);
	}
	if (pulse > 0.0) {
		k *= 1.0 + pulse * 0.35 * sin(TIME * 1.1 + wpos.x * 0.07 + wpos.z * 0.05);
	}
	if (flow > 0.0) {
		float n = vnoise(wpos.xz * 0.6 + vec2(TIME * 0.25, TIME * 0.1)) * 0.6 + vnoise(wpos.xz * 2.1 - TIME * 0.4) * 0.4;
		k *= mix(1.0, 0.45 + 1.1 * n, flow);
		col = mix(col * vec3(1.0, 0.7, 0.4), col + vec3(0.0, 0.25, 0.1), n * flow);
	}
	ALBEDO = col * energy * k;
}
