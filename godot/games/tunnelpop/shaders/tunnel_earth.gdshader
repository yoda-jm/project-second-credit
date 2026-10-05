// Tunnel Pop earth: the cut face of four layers (their colours per level), grainy, with pebbles, roots near the top
// and a darker band between layers; the tunnels' walls and backs in a darker, damper tone. COLOR.r marks the face
// (1) from the tunnel walls and backs (0). Our own shader (CC BY-SA 4.0).
shader_type spatial;
render_mode cull_disabled;

uniform vec4 layer0 : source_color = vec4(0.85, 0.62, 0.3, 1.0);
uniform vec4 layer1 : source_color = vec4(0.78, 0.45, 0.22, 1.0);
uniform vec4 layer2 : source_color = vec4(0.62, 0.3, 0.2, 1.0);
uniform vec4 layer3 : source_color = vec4(0.45, 0.22, 0.25, 1.0);

varying vec3 wpos;
varying float face;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	face = COLOR.r;
	if (COLOR.a < 0.5) { face = 1.0; }   // meshes without vertex colours (the side slabs) are face
}

void fragment() {
	float depth = -wpos.y - 1.5;      // metres below the surface
	float wob = noise(vec2(wpos.x * 0.6, depth)) * 0.6;
	float l = depth + wob;
	vec3 col = l < 3.0 ? layer0.rgb : (l < 6.0 ? layer1.rgb : (l < 9.5 ? layer2.rgb : layer3.rgb));
	float seam = smoothstep(0.18, 0.0, abs(fract((l + 0.0) / 3.0 + 0.5) - 0.5) * 3.0) * step(1.0, l);
	col *= 1.0 - seam * 0.18;
	col *= 0.85 + 0.25 * noise(wpos.xy * 6.0);
	float peb = smoothstep(0.86, 0.93, noise(wpos.xy * 3.3 + 7.0));
	col = mix(col, col * 1.35 + vec3(0.05), peb * 0.6);
	col = mix(col, vec3(0.35, 0.22, 0.12), smoothstep(0.75, 0.9, noise(vec2(wpos.x * 2.0, depth * 0.7))) * step(depth, 2.0) * 0.5);
	// inside a tunnel: damper and darker, deeper towards the back
	if (face < 0.5) {
		col *= 0.7 + 0.25 * smoothstep(-0.5, 0.5, wpos.z);
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
}
