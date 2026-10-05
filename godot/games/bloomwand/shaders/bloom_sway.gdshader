// Bloomwand foliage, flowers and grass (our own, CC BY-SA 4.0): vertex-coloured, bending in the breeze by UV.y (the
// height of the vertex above its plant's foot, in metres, written by tools/blender/bloomwand_backdrops.py). Light
// shines through leaves and petals (translucency); flowers may glow a little of their own. Runs on `clock`.
shader_type spatial;
render_mode cull_disabled;

uniform float clock = 0.0;
uniform float amp = 0.02;
uniform float speed = 1.0;
uniform float rough : hint_range(0.0, 1.0) = 0.85;
uniform float translucency = 0.35;
uniform vec3 tint : source_color = vec3(1.0);
uniform float self_light = 0.0;
uniform float snow_glow = 0.0;   // pale vertex colours (snow on the boughs) glow a little at night

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float hgt = max(UV.y, 0.0);
	float gust = 0.6 + 0.4 * sin(clock * 0.31 + w.x * 0.05);
	float s = sin(clock * speed + w.x * 0.23 + w.z * 0.13) + 0.35 * sin(clock * speed * 2.3 + w.x * 0.9 + w.z * 0.5);
	float d = amp * pow(hgt, 1.25) * s * gust;
	VERTEX.x += d;
	VERTEX.z += d * 0.3;
	VERTEX.y -= abs(d) * 0.1;
	COLOR.rgb *= tint;
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ROUGHNESS = rough;
	SPECULAR = 0.3;
	BACKLIGHT = COLOR.rgb * translucency;
	float lum = dot(COLOR.rgb, vec3(0.3, 0.59, 0.11));
	EMISSION = COLOR.rgb * (self_light + snow_glow * smoothstep(0.3, 0.7, lum));
}
