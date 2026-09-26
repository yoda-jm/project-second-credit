shader_type spatial;
// Old-fashioned wallpaper: two-tone stripes with a damask motif and a little paper grain, above a painted wooden
// wainscot with raised panels and a dado rail. Mapped in world space (x or z along the wall, y up); it darkens a
// little towards the ceiling and the floor, as if under the cornice.

uniform vec3 base : source_color = vec3(0.45, 0.62, 0.7);
uniform vec3 stripe : source_color = vec3(0.55, 0.72, 0.8);
uniform vec3 motif : source_color = vec3(0.3, 0.42, 0.5);
uniform vec3 wainscot : source_color = vec3(0.92, 0.9, 0.84);
uniform float panel_top = 1.3;
uniform float ceiling = 10.2;
uniform bool along_z = false;  // side walls run along z

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1, 0)), f.x), mix(hash2(i + vec2(0, 1)), hash2(i + vec2(1, 1)), f.x), f.y);
}

float damask(vec2 p) {
	// a stylised lily on a staggered grid: a teardrop body, two curling leaves and a small crown
	vec2 g = vec2(p.x * 2.8, p.y * 2.2);
	g.x += floor(g.y) * 0.5;
	vec2 f = fract(g) - 0.5;
	f.x = abs(f.x);
	float body = length(vec2(f.x * 2.2, f.y + 0.05 + f.y * f.y)) - 0.2;
	vec2 l = f - vec2(0.16, -0.08);
	float leaf = length(vec2(l.x * 1.6 + l.y * 0.9, l.y * 2.6)) - 0.12;
	float crown = length(f - vec2(0.0, -0.32)) - 0.05;
	float ring = abs(length(f - vec2(0.0, 0.05)) - 0.34) - 0.012;
	float d = min(min(body, leaf), min(crown, ring * 1.0 + 1.0 * step(0.0, -f.y - 0.1)));
	return smoothstep(0.012, -0.004, d);
}

void fragment() {
	vec2 p = vec2(along_z ? wpos.z : wpos.x, wpos.y);
	float grain = noise(p * 90.0) * 0.5 + noise(p * 7.0) * 0.5;
	vec3 c;
	if (p.y < panel_top) {
		// the wainscot: raised panels (with bevelled edges that catch the light) and a dado rail on top
		vec2 q = vec2(fract(p.x / 1.6), p.y / panel_top);
		float fx = min(q.x, 1.0 - q.x) * 1.6;
		float fy = min(p.y - 0.36, panel_top - 0.14 - p.y);
		float inset = min(fx, fy);
		vec3 nrm = vec3(0.5, 0.5, 1.0);
		c = wainscot;
		if (inset < 0.1) {
			c *= 0.9;
		} else if (inset < 0.16) {  // the bevel of the raised field
			vec2 dir = fx < fy ? vec2(q.x < 0.5 ? -1.0 : 1.0, 0.0) : vec2(0.0, p.y < 0.75 ? -1.0 : 1.0);
			nrm = vec3(0.5 + dir * 0.35, 0.8);
			c *= 1.0;
		}
		float rail = smoothstep(panel_top - 0.14, panel_top - 0.1, p.y);
		c = mix(c, wainscot * 1.05, rail);
		if (rail > 0.0) {
			nrm = vec3(0.5, 0.5 + 0.4 * sin((p.y - panel_top + 0.14) / 0.14 * 3.14159), 0.9);
		}
		c *= 0.94 + 0.08 * grain;
		NORMAL_MAP = nrm;
		ALBEDO = c;
		ROUGHNESS = 0.4;
	} else {
		float s = smoothstep(0.47, 0.5, fract(p.x * 0.7)) * smoothstep(1.0, 0.97, fract(p.x * 0.7));
		float pin = smoothstep(0.015, 0.0, abs(fract(p.x * 0.7) - 0.5)) + smoothstep(0.015, 0.0, abs(fract(p.x * 0.7) - 0.985));
		c = mix(base, stripe, s * 0.55);
		c = mix(c, motif, damask(p) * 0.32 + pin * 0.2);
		c *= 0.9 + 0.14 * grain;
		c *= 1.0 - 0.3 * smoothstep(ceiling - 2.5, ceiling, p.y);  // under the cornice
		ALBEDO = c;
		ROUGHNESS = 0.82;
	}
	c = ALBEDO;
	ALBEDO = c * (1.0 - 0.18 * smoothstep(0.6, 0.0, p.y));  // near the floor
}
