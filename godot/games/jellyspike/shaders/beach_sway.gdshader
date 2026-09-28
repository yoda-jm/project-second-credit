// Jelly Spike beach plants and cloth, vertex-coloured, moving in the sea breeze. kind 0: plants bending by UV.y (the
// height above the plant's foot); 1: palms, the same plus fronds that flutter by UV.x (along the frond); 2: flags
// rippling along UV.x (distance from the pole); 3: bunting swinging by UV.y (depth below the rope). Gusts roll across.
shader_type spatial;
render_mode cull_disabled;

uniform int kind = 0;
uniform float amp = 0.03;
uniform float speed = 1.1;
uniform float rough : hint_range(0.0, 1.0) = 0.8;
uniform float translucency = 0.25;
uniform vec3 tint : source_color = vec3(1.0);

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float gust = 0.6 + 0.4 * sin(TIME * 0.33 + w.x * 0.05);
	if (kind <= 1) {
		float hgt = max(UV.y, 0.0);
		float s = sin(TIME * speed + w.x * 0.21 + w.z * 0.13) + 0.35 * sin(TIME * speed * 2.3 + w.x * 0.9 + w.z * 0.5);
		float d = amp * pow(hgt, 1.3) * s * gust;
		VERTEX.x += d;
		VERTEX.z += d * 0.3;
		if (kind == 1) {
			float f = UV.x;
			float fl = sin(TIME * 3.1 + w.x * 1.7 + w.z * 1.3 + f * 4.0) + 0.5 * sin(TIME * 5.3 + w.z * 2.1 + f * 7.0);
			VERTEX.y += fl * f * f * 0.12 * gust;
			VERTEX.x += fl * f * 0.05;
		}
	} else if (kind == 2) {
		float u = max(UV.x, 0.0);
		float s = sin(TIME * 5.0 - u * 4.5 + UV.y * 0.7) + 0.4 * sin(TIME * 8.3 - u * 8.0);
		VERTEX.z += s * u * 0.16 * gust;
		VERTEX.x -= abs(s) * u * 0.03;
	} else {
		float dep = max(UV.y, 0.0);
		float s = sin(TIME * 2.4 + w.x * 1.9) + 0.5 * sin(TIME * 4.1 + w.x * 3.7);
		VERTEX.z += s * dep * 0.35 * gust;
		VERTEX.x += s * dep * 0.08;
	}
	COLOR.rgb *= tint;
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ROUGHNESS = rough;
	SPECULAR = 0.3;
	BACKLIGHT = COLOR.rgb * translucency;
}
