// Nova Wardens backdrop lights: windows that come on and go off one by one, street lamps that shimmer, aviation lights
// that blink, the red air-raid lamps that wake with the alarm and flash like beacons. Unshaded HDR (feeds the glow).
// Cells of world space vary each light. Everything runs on `clock`.
shader_type spatial;
render_mode unshaded, shadows_disabled;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(1.0, 0.8, 0.5);
uniform bool use_vertex_color = false;
uniform float energy = 2.5;
uniform float twinkle = 0.0;   // share of lights that are off at any time (they swap slowly)
uniform float variety = 0.0;   // per-light brightness and hue spread
uniform float flicker = 0.0;
uniform float blink = 0.0;     // aviation blink
uniform float alarm = 0.0;     // 0..1: the air-raid lamps
uniform float idle = 0.0;      // the air-raid lamps' glow when all is calm
uniform float dim = 0.0;       // blackout: windows go out as the alarm rises
uniform float cell = 1.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 c = floor(wpos / cell + 0.001);
	float h = nw_hash3(c);
	float k = 1.0;
	vec3 col = use_vertex_color ? COLOR.rgb : color;
	if (variety > 0.0) {
		k *= 1.0 - variety * 0.5 + variety * h;
		col = mix(col, col.gbr * 0.4 + col * 0.6, variety * step(0.85, fract(h * 7.0)) * 0.6);
	}
	if (twinkle > 0.0) {
		float slot = floor(clock * 0.05 + h * 9.0);
		k *= mix(0.03, 1.0, step(twinkle, nw_hash(vec2(h * 91.0, slot))));
	}
	if (dim > 0.0) {
		k *= mix(1.0, 0.04, step(1.0 - dim, h));
	}
	if (flicker > 0.0) {
		k *= 1.0 + flicker * 0.25 * (sin(clock * 13.0 + h * 40.0) + sin(clock * 7.3 + h * 17.0));
	}
	if (blink > 0.0) {
		k *= mix(1.0, step(0.6, fract(clock * 0.55 + h)), blink);
	}
	if (idle > 0.0 || alarm > 0.0) {
		// a rotating beacon: a sharp sweep each turn, faster as the alarm rises
		float ph = fract(clock * (0.6 + 0.9 * alarm) + h);
		float sweep = pow(max(0.0, sin(ph * 6.2832)), 8.0);
		k *= idle + alarm * (0.25 + 2.5 * sweep);
	}
	ALBEDO = col * energy * k;
}
