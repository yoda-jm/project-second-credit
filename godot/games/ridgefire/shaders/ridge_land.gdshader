// Ridgefire backdrop land: vertex-coloured ground, rock, snow, ice and props. The vertex colour's alpha is the sun's
// visibility baked by tools/blender/ridgefire_backdrops.py (the long shadows of the landforms): it dims the
// directional light only, so the sky's ambient still fills the shadows. Aerial haze by distance (warmer towards the
// sun) fades the far ranges into the sky. Plants bend in the wind by UV.y (height above their foot), flags flutter
// (UV.y = distance from the pole). Omni lights (the explosions' flashes, lamps) light it as usual.
shader_type spatial;
render_mode cull_disabled;

uniform float rough = 0.9;
uniform float spec = 0.0;          // a glossy highlight (ice, metal, glass)
uniform float shininess = 40.0;
uniform float sparkle = 0.0;       // glints in the snow
uniform float translucency = 0.0;  // light through leaves and ice
uniform float sway = 0.0;          // plants: bend amplitude
uniform float flutter = 0.0;       // flags
uniform float wind = 1.0;
uniform float tremor = 0.0;        // set by the backdrop when the ground shakes (a brief quiver of the plants)
uniform vec3 haze_col : source_color = vec3(0.6, 0.65, 0.75);
uniform vec3 haze_sun_col : source_color = vec3(1.0, 0.8, 0.6);
uniform vec3 sun_dir = vec3(0.5, 0.5, 0.5);
uniform float haze_start = 80.0;
uniform float haze_scale = 600.0;
uniform float haze_max = 0.8;
uniform float haze_sun_pow = 6.0;
uniform vec3 glow_tint : source_color = vec3(0.0);   // a light from below (lava, a fire) by height: the self-light
uniform float glow_height = 0.0;
uniform bool debug_vis = false;      // shows the baked sun visibility (the preview's --vis)

varying vec3 wpos;
varying float sunvis;

float hash3(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	sunvis = COLOR.a;
	float hgt = max(UV.y, 0.0);
	if (sway > 0.0 && hgt > 0.0) {
		float gust = 0.6 + 0.4 * sin(TIME * 0.31 + w.x * 0.013);
		float s = sin(TIME * 1.1 * wind + w.x * 0.11 + w.z * 0.07) + 0.35 * sin(TIME * 2.5 * wind + w.x * 0.5 + w.z * 0.3);
		float d = (sway * gust * wind + tremor * 0.6 * sin(TIME * 23.0 + w.x)) * pow(hgt, 1.2) * s;
		VERTEX.x += d;
		VERTEX.z += d * 0.3;
	}
	if (flutter > 0.0 && hgt > 0.0) {
		float ph = TIME * 7.0 * wind - hgt * 1.6 + w.x * 0.1;
		VERTEX.z += flutter * hgt * (sin(ph) * 0.18 + sin(ph * 2.3 + 1.0) * 0.06);
		VERTEX.y += flutter * hgt * sin(ph * 0.7) * 0.05;
	}
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 to = wpos - CAMERA_POSITION_WORLD;
	float d = length(to);
	vec3 vd = to / d;
	float f = haze_max * (1.0 - exp(-max(d - haze_start, 0.0) / haze_scale));
	float s = pow(max(dot(vd, normalize(sun_dir)), 0.0), haze_sun_pow);
	vec3 hz = mix(haze_col, haze_sun_col, s);
	vec3 c = COLOR.rgb;
	ALBEDO = c * (1.0 - f);
	vec3 em = hz * f;
	if (glow_height > 0.0) {
		em += glow_tint * c * exp(-max(wpos.y, 0.0) / glow_height) * (1.0 - f);
	}
	if (sparkle > 0.0) {
		vec3 cell = floor(wpos * 6.0);
		float h = hash3(cell);
		float tw = step(0.985, h) * (0.5 + 0.5 * sin(TIME * 3.0 + h * 50.0));
		em += vec3(0.9, 0.95, 1.0) * tw * sparkle * smoothstep(120.0, 20.0, d) * (1.0 - f);
	}
	EMISSION = em;
	if (debug_vis) {
		ALBEDO = vec3(sunvis);
		EMISSION = vec3(sunvis) * 0.5;
	}
	ROUGHNESS = rough;
	SPECULAR = 0.3;
	BACKLIGHT = c * translucency;
}

void light() {
	float sh = LIGHT_IS_DIRECTIONAL ? sunvis : 1.0;
	float ndl = dot(NORMAL, LIGHT);
	float diff = clamp(ndl, 0.0, 1.0);
	if (translucency > 0.0) {
		diff += clamp(-ndl, 0.0, 1.0) * translucency * 0.6;
	}
	DIFFUSE_LIGHT += diff * ATTENUATION * LIGHT_COLOR * sh / PI;
	if (spec > 0.0) {
		vec3 hv = normalize(LIGHT + VIEW);
		float sp = pow(clamp(dot(NORMAL, hv), 0.0, 1.0), shininess) * spec;
		SPECULAR_LIGHT += sp * ATTENUATION * LIGHT_COLOR * sh * clamp(ndl * 4.0, 0.0, 1.0) / PI;
	}
}
