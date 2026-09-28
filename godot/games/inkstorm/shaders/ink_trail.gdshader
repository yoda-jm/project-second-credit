shader_type spatial;
// Inkstorm: the line being drawn, a tube of polished gold (silver-blue when drawn slowly) with highlights flowing
// towards the pen, twinkling sparkles and a hot, fresh tip. UV.x is the distance along the line (world units),
// UV.y the angle round the tube (0..1). The fuse chars what it has burnt (burnt: distance it has reached); a broken
// line (break_c, break_r) is gone within break_r of break_c, its shards flying off.

render_mode cull_back;

uniform float slow = 0.0;          // 0 gold, 1 silver-blue
uniform float length_ = 1.0;       // the line's length
uniform float burnt = -1.0;        // how far the fuse has burnt (-1: unlit)
uniform float break_c = 0.0;
uniform float break_r = -1.0;
uniform float fade = 1.0;

float hash(float n) { return fract(sin(n * 12.9898) * 43758.5453); }

void fragment() {
	float s = UV.x;
	if (break_r >= 0.0 && abs(s - break_c) < break_r) discard;
	vec3 gold = vec3(1.0, 0.7, 0.24);
	vec3 silver = vec3(0.62, 0.8, 1.0);
	vec3 base = mix(gold, silver, slow);
	// polished metal: bright rim along the top, deeper at the sides
	float ang = UV.y * 6.2831853;
	float top = 0.5 + 0.5 * cos(ang);
	// light running along the line towards the pen, and a slower swell
	float flow = pow(0.5 + 0.5 * sin(s * 16.0 - TIME * 10.0), 8.0);
	float swell = pow(0.5 + 0.5 * sin(s * 3.5 - TIME * 3.0), 3.0);
	// sparkles: a few spots twinkle at a time
	float cell = floor(s * 30.0) + floor(UV.y * 5.0) * 131.0;
	float h = hash(cell);
	float tw = step(0.8, h) * pow(max(0.0, sin(TIME * (4.0 + h * 5.0) + h * 60.0)), 20.0);
	// the fresh end near the pen burns hottest
	float tip = smoothstep(length_ - 1.2, length_, s);
	vec3 col = base;
	float glow = 0.05 + top * 0.06 + flow * 0.55 + swell * 0.08 + tip * (0.25 + 0.15 * sin(TIME * 9.0));
	// a polished highlight running along the crown of the tube
	float crown = pow(top, 14.0);
	vec3 em = base * glow * mix(1.0, 0.7, slow) + vec3(1.0, 0.95, 0.85) * (tw * 3.5 + crown * (0.35 + flow * 0.6));
	em *= mix(1.0, 0.6, slow);
	// what the fuse has burnt is charred ink, smouldering near the flame
	if (burnt >= 0.0 && s < burnt) {
		float ember = exp(-(burnt - s) * 5.0);
		col = mix(vec3(0.05, 0.03, 0.03), vec3(0.4, 0.12, 0.03), ember);
		em = vec3(1.0, 0.3, 0.05) * ember * 2.5 + vec3(0.25, 0.06, 0.0) * pow(max(0.0, sin(s * 40.0 + TIME * 7.0)), 6.0) * ember;
	}
	ALBEDO = col;
	METALLIC = 1.0;
	ROUGHNESS = 0.16 - tw * 0.08;
	SPECULAR = 0.8;
	EMISSION = em * fade;
}
