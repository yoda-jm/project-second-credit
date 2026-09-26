shader_type spatial;
// Fruitburrow soil seen in cross-section: the CC0 soil texture (ambientCG) mapped on the face, coloured by depth
// in wavy layers: dark humus under the grass, loam, a band of red clay, then grey stony earth deep down.
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 tint : source_color = vec3(1.0, 0.82, 0.62);
uniform float top = 0.5;      // world y of the soil's top
uniform float depth = 14.0;   // how deep the garden goes
uniform float scale = 0.45;
varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float band(float y, float c, float w) { return 1.0 - smoothstep(w * 0.6, w, abs(y - c)); }

void fragment() {
	vec2 uv = abs(wn.z) > 0.5 ? wp.xy * scale : (abs(wn.x) > 0.5 ? wp.zy : wp.xz) * scale;
	vec3 soil = texture(albedo_tex, uv).rgb * tint;
	float d = top - wp.y + sin(wp.x * 0.37) * 0.5 + sin(wp.x * 0.11 + 1.3) * 0.9;  // depth below the grass, wavy
	vec3 k = vec3(1.0);
	k = mix(k, vec3(0.55, 0.45, 0.4), 1.0 - smoothstep(0.6, 1.6, d));        // humus
	k = mix(k, vec3(1.35, 0.95, 0.7), band(d, depth * 0.42, 1.4));          // clay
	k = mix(k, vec3(0.72, 0.72, 0.8), smoothstep(depth * 0.66, depth * 0.8, d));  // deep earth
	ALBEDO = soil * k;
	NORMAL_MAP = texture(normal_tex, uv).rgb;
	ROUGHNESS = 0.95;
}
