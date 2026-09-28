// Pop Voyage backdrop foliage: vertex-coloured, bending in the wind by UV.y (the height of the vertex above its
// plant's foot, in metres, written by tools/blender/popvoyage_backdrops.py). Gusts roll across the scene.
shader_type spatial;
render_mode cull_disabled;

uniform float amp = 0.03;
uniform float speed = 1.2;
uniform float rough : hint_range(0.0, 1.0) = 0.8;
uniform float translucency = 0.25;
uniform vec3 tint : source_color = vec3(1.0);

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float hgt = max(UV.y, 0.0);
	float gust = 0.6 + 0.4 * sin(TIME * 0.35 + w.x * 0.04);
	float s = sin(TIME * speed + w.x * 0.21 + w.z * 0.13) + 0.35 * sin(TIME * speed * 2.3 + w.x * 0.9 + w.z * 0.5);
	float d = amp * pow(hgt, 1.3) * s * gust;
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
}
