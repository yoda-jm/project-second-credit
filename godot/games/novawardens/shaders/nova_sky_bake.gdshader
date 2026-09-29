// Nova Wardens: bakes the still deep sky (nebula and Milky Way, nova_nebula.gdshaderinc) once into a panorama the sky
// dome samples (nova_sky's `pano`): x is the azimuth (0 = straight ahead, -z), y the elevation, over pano_rect
// (az0, az1, el_top, el_bottom in radians). Stored as sqrt(colour) in 8 bits (the dome squares it back).
shader_type canvas_item;
render_mode unshaded;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"
#include "res://games/novawardens/shaders/nova_nebula.gdshaderinc"

uniform vec4 pano_rect = vec4(-1.1, 1.1, 0.62, -0.12);

void fragment() {
	float az = mix(pano_rect.x, pano_rect.y, UV.x);
	float el = mix(pano_rect.z, pano_rect.w, UV.y);
	vec3 d = vec3(sin(az) * cos(el), sin(el), -cos(az) * cos(el));
	vec3 c = nw_nebula(d) + nw_milky(d);
	COLOR = vec4(sqrt(clamp(c, vec3(0.0), vec3(1.0))), 1.0);
}
