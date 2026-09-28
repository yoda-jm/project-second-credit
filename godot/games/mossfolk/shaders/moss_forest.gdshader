shader_type spatial;
// Mossfolk: one layer of the fungal forest seen through the cave's arches: rolling ground and giant mushrooms as
// dark shapes against the glow, their gills and spots lit, a lit rim round each cap. Opaque (cut out), so the layers
// behind are not drawn where a nearer one covers them. Layers at different depths (nearer ones darker, farther ones
// paler in the haze) give the parallax.

render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 shade : source_color = vec3(0.03, 0.06, 0.1);   // the silhouettes
uniform vec3 haze : source_color = vec3(0.1, 0.3, 0.4);      // what they fade into
uniform float haze_amount = 0.3;
uniform vec3 glow_a : source_color = vec3(0.3, 1.0, 0.9);
uniform vec3 glow_b : source_color = vec3(0.8, 0.4, 1.0);
uniform vec2 extent = vec2(200.0, 60.0);
uniform float cell_w = 9.0;         // one mushroom (or none) per cell of this width
uniform float ground = 6.0;         // the ground's height above the quad's bottom
uniform vec2 height = vec2(8.0, 18.0);
uniform vec2 radius = vec2(2.0, 5.0);
uniform float energy = 1.0;
uniform float seed = 0.0;

float hash(float n) { return fract(sin(n * 127.1 + seed * 13.7) * 43758.5453); }
float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7)) + seed) * 43758.5453); }
float noise(float x) { float i = floor(x); float f = fract(x); return mix(hash(i), hash(i + 1.0), f * f * (3.0 - 2.0 * f)); }

void fragment() {
	vec2 wp = vec2(UV.x, 1.0 - UV.y) * extent;
	float g = ground + (noise(wp.x * 0.08) - 0.5) * 3.0 + (noise(wp.x * 0.31 + 5.0) - 0.5) * 0.8;
	float solid = step(wp.y, g);
	vec3 glow = vec3(0.0);
	float ci = floor(wp.x / cell_w);
	for (int k = -3; k <= 3; k++) {   // a big cap (and its lean) can reach two or three cells away: check them all, or it is cut off
		float i = ci + float(k);
		if (hash(i) < 0.25) continue;
		float H = g + mix(height.x, height.y, hash(i + 0.31));
		float r = mix(radius.x, radius.y, hash(i + 0.57));
		float lean = (hash(i + 0.73) - 0.5) * r * 0.9;
		float cx = (i + 0.2 + 0.6 * hash(i + 0.91)) * cell_w;
		float t = clamp(wp.y / H, 0.0, 1.0);
		float sw = r * 0.13 * (1.3 - 0.45 * t);
		float sx = cx + lean * t * t;
		float bob = sin(TIME * 0.5 + i * 1.7) * 0.15;   // the caps breathe a little
		if (abs(wp.x - sx) < sw && wp.y < H + bob) solid = 1.0;
		vec2 d = vec2(wp.x - (cx + lean), wp.y - H - bob);
		float e = length(d / vec2(r, r * 0.6));
		vec3 gc = mix(glow_a, glow_b, step(0.5, hash(i + 0.13)));
		if (d.y > -r * 0.1 && e < 1.0) {
			solid = 1.0;
			// gills: a glowing band on the underside; spots on the dome
			glow += gc * smoothstep(r * 0.18, -r * 0.1, d.y) * 1.4;
			vec2 sp = d * 3.2 / r;
			float s = smoothstep(0.34, 0.12, length(fract(sp) - 0.5)) * step(0.55, hash2(floor(sp) + i));
			glow += mix(gc, vec3(1.0), 0.4) * s * (0.6 + 0.4 * sin(TIME * 1.3 + i + floor(sp.x) * 2.0));
			glow += gc * smoothstep(0.75, 1.0, e) * 0.35;    // a lit rim
		}
		// a faint glow along the stem
		glow += gc * solid * smoothstep(sw, 0.0, abs(wp.x - sx)) * step(wp.y, H) * 0.12 * t;
	}
	if (solid < 0.5) discard;
	ALBEDO = mix(shade, haze, haze_amount) + glow * energy;
}
