class_name FrostpeakValley
extends RefCounted
## The alpine valley around the venues: a ring of big ridges with rock bands and a few named-looking horns, a
## glacier in a high cirque behind the jump hill, forests on the lower slopes, the valley floor with its woods, a
## village of chalets round a church, a gondola climbing to a shoulder of the mountains (cabins on the move), and
## cloud banks drifting on the peaks. Heights are one function (`height`), used by everything placed on the ground
## and by the camera flights to stay clear of it.

const C := Vector3(100, 0, 0)  ## the valley's centre
const INNER := 1000.0  ## the mountains rise from here
const VILLAGE := Vector3(300, 0, 470)
const STATION := Vector3(600, 0, 640)  ## the gondola's valley station
const SUMMIT := Vector3(980, 0, 1300)  ## the gondola's top station (height from the terrain)
## [x, z, height, radius] of the big peaks; the first is the horn behind the jump hill
const PEAKS := [[2150.0, -380.0, 1300.0, 260.0], [1950.0, 560.0, 950.0, 320.0], [100.0, -2000.0, 1150.0, 400.0],
	[-1750.0, -650.0, 1050.0, 420.0], [-400.0, 1900.0, 1000.0, 400.0], [1150.0, 1800.0, 850.0, 330.0],
	[1400.0, -1500.0, 950.0, 340.0], [-1500.0, 1150.0, 880.0, 350.0]]
const GLACIER_A := Vector2(2250.0, 110.0)  ## the glacier's head, in the col between the first two peaks
const GLACIER_B := Vector2(1700.0, 70.0)  ## its snout

var v: FrostpeakView3D
var cabins: Array[Node3D] = []
var _cable: Array[Vector3] = []  ## the gondola's loop: up the line on one side, back down the other
var _cable_len := PackedFloat32Array()
var _ridge := FastNoiseLite.new()
var _base := FastNoiseLite.new()
var _patch := FastNoiseLite.new()
var _lo := FastNoiseLite.new()
var _gh := Vector2.ZERO  ## the glacier's surface height at its head and its snout
var _smoke: Array[Vector3] = []


func _init(view: FrostpeakView3D) -> void:
	v = view
	_ridge.seed = 5
	_ridge.frequency = 0.0013
	_ridge.fractal_type = FastNoiseLite.FRACTAL_RIDGED
	_ridge.fractal_octaves = 5
	_ridge.fractal_lacunarity = 2.1
	_ridge.fractal_gain = 0.48
	_base.seed = 11
	_base.frequency = 0.0008
	_patch.seed = 23
	_patch.frequency = 0.004
	_patch.fractal_octaves = 3
	_lo.seed = 31
	_lo.frequency = 0.0035
	_lo.fractal_octaves = 3
	_gh = Vector2(_raw(GLACIER_A.x, GLACIER_A.y), _raw(GLACIER_B.x, GLACIER_B.y))


# ------------------------------------------------------------------ the ground

## The mountains without the glacier (below zero inside the valley).
func _raw(x: float, z: float) -> float:
	var r := Vector2(x - C.x, z - C.z).length()
	# forested foothills first, then the high ridges further out, the highest crest at the back
	var env := pow(smoothstep(INNER + 150.0, 1950.0, r), 1.4) * (1.0 - 0.75 * smoothstep(2450.0, 2900.0, r))
	var rn := _ridge.get_noise_2d(x, z) * 0.5 + 0.5
	var bn := _base.get_noise_2d(x, z) * 0.5 + 0.5
	var foot := smoothstep(INNER - 40.0, INNER + 380.0, r) * (70.0 + rn * 150.0 + bn * 110.0)
	var h := foot + env * (pow(rn, 1.6) * 820.0 + bn * 420.0) - 30.0 + smoothstep(INNER, INNER + 150.0, r) * 20.0
	var near := smoothstep(1450.0, 1850.0, r)
	for pk in PEAKS:
		var d: float = Vector2(x - pk[0], z - pk[1]).length() / pk[3]
		if d < 3.0:
			h += float(pk[2]) * exp(-d * d) * (0.65 + 0.5 * rn) * near
	return h


## The glacier: 0..1 inside its tongue, and how far along it (0 at the head).
func glacier(x: float, z: float) -> Vector2:
	var ab := GLACIER_B - GLACIER_A
	var t := clampf((Vector2(x, z) - GLACIER_A).dot(ab) / ab.length_squared(), -0.2, 1.2)
	var d := Vector2(x, z).distance_to(GLACIER_A + ab * clampf(t, 0.0, 1.0))
	var w := lerpf(200.0, 80.0, clampf(t, 0.0, 1.0)) * (1.0 + 0.15 * sin(t * 9.0))
	var m := smoothstep(w, w * 0.55, d) * smoothstep(-0.15, 0.0, t) * smoothstep(1.08, 0.92, t)
	return Vector2(m, t)


## The ground's height anywhere in the world (the valley floor is 0).
func height(x: float, z: float) -> float:
	var h := _raw(x, z)
	var g := glacier(x, z)
	if g.x > 0.0:
		var t := clampf(g.y, 0.0, 1.0)
		var surf := lerpf(_gh.x, _gh.y, pow(t, 0.8)) + 12.0
		h = lerpf(h, surf, g.x * 0.9)
	# the biathlon venue brings its own rolling ground (BiathlonCourse), in place of the valley's swells
	var bm := BiathlonCourse.mask(x, z)
	return maxf(h, 0.0) + relief(x, z) * (1.0 - smoothstep(0.0, 40.0, h)) * (1.0 - bm) + (BiathlonCourse.ground(x, z) if bm > 0.0 else 0.0)


## The frozen river's centre line (z for an x), winding along the north of the valley.
static func river_z(x: float) -> float:
	return -420.0 + 70.0 * sin(x / 210.0) + 30.0 * sin(x / 77.0 + 1.0)


## Gentle swells of the valley floor, flat round the venues, the village and the river.
func relief(x: float, z: float) -> float:
	var m := smoothstep(170.0, 290.0, Vector2(x, z * 1.3).length())
	m *= smoothstep(90.0, 180.0, Vector2(x - FrostpeakView3D.PLAZA.x, z - FrostpeakView3D.PLAZA.z).length())
	m *= smoothstep(1.1, 1.7, Vector2((x - VILLAGE.x) / 230.0, (z - VILLAGE.z) / 120.0).length())
	m *= smoothstep(60.0, 130.0, Vector2(x - STATION.x, z - STATION.z).length())
	m *= smoothstep(14.0, 60.0, absf(z - river_z(x)))
	if m <= 0.0:
		return 0.0
	return (_lo.get_noise_2d(x, z) * 9.0 + _patch.get_noise_2d(x * 2.5, z * 2.5) * 1.8) * m


## How thick the forest is on the lower slopes (0..1), by altitude and in patches.
func forest(x: float, z: float, h: float) -> float:
	var p := _patch.get_noise_2d(x, z)
	return smoothstep(520.0, 300.0, h) * smoothstep(-0.35, 0.15, p) * smoothstep(-5.0, 30.0, h)


# ------------------------------------------------------------------ building

func build() -> void:
	_build_mountains()
	_build_floor()
	_build_village()
	_build_gondola()
	_build_clouds()


func _build_mountains() -> void:
	var radii: Array[float] = []
	var r := INNER - 20.0
	while r <= 2900.0:
		radii.append(r)
		r += 25.0 if r < 1500.0 else (50.0 if r < 2200.0 else 80.0)
	var steps := 480
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for ri in radii.size():
		for k in steps + 1:
			var a := TAU * k / steps
			var x := C.x + cos(a) * radii[ri]
			var z := C.z + sin(a) * radii[ri]
			var h := height(x, z) if radii[ri] > INNER else minf(height(x, z), 0.0) - 2.0
			var g := glacier(x, z).x
			st.set_color(Color(g, forest(x, z, h), 0.0))
			st.add_vertex(Vector3(x, h, z))
	var row := steps + 1
	for ri in radii.size() - 1:
		for k in steps:
			var i0 := ri * row + k
			var i1 := i0 + 1
			var i2 := i0 + row + 1
			var i3 := i0 + row
			for i in [i0, i2, i1, i0, i3, i2]:
				st.add_index(i)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = load(FrostpeakView3D.SH + "mountain.gdshader")
	m.set_shader_parameter("rock_tex", load("res://core/art/textures/rock/albedo.jpg"))
	m.set_shader_parameter("rock_nrm", load("res://core/art/textures/rock/normal.jpg"))
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	v.add_child(mi)
	# forests on the lower slopes, where the shader paints them: real trees near the valley, for depth
	var rng := RandomNumberGenerator.new()
	rng.seed = 41
	var trees: Array[Transform3D] = []
	var tries := 0
	while trees.size() < 4200 and tries < 26000:
		tries += 1
		var a := rng.randf() * TAU
		var rr := rng.randf_range(INNER + 10.0, INNER + 560.0)
		var x := C.x + cos(a) * rr
		var z := C.z + sin(a) * rr
		if FrostpeakHill.covers(Vector3(x, 0, z)):
			continue
		var h := height(x, z)
		if rng.randf() > forest(x, z, h) or h < 2.0:
			continue
		var slope := Vector2(height(x + 4.0, z) - h, height(x, z + 4.0) - h).length() / 4.0
		if slope > 1.1:
			continue
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(2.6, 4.2)), Vector3(x, h - 0.5, z)))
	v._forest_far(trees)


func _build_floor() -> void:
	# the floor: a grid over the swells, sunk out of sight under the mountains and the jump hill's own ground
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 230
	var size := 2300.0
	for i in n + 1:
		for k in n + 1:
			var x := C.x - size * 0.5 + size * i / n
			var z := C.z - size * 0.5 + size * k / n
			var r := Vector2(x - C.x, z - C.z).length()
			var y := height(x, z) - 3.0 * smoothstep(985.0, 1010.0, r) - 0.1
			if FrostpeakBiathlon.covers(Vector3(x, 0, z)):  # under the venue's own finer ground
				y -= 1.5 * FrostpeakBiathlon.inside(Vector3(x, 0, z))
			if FrostpeakHill.covers(Vector3(x, 0, z)):
				var l := FrostpeakHill.frame().affine_inverse() * Vector3(x, 0, z)
				var inner := minf(minf(l.x - FrostpeakHill.X0, FrostpeakHill.X1 - l.x), FrostpeakHill.Z1 - absf(l.z))
				y -= 2.0 * smoothstep(0.0, 12.0, inner)
			st.add_vertex(Vector3(x, y, z))
	for i in n:
		for k in n:
			var a := i * (n + 1) + k
			for idx in [a, a + n + 2, a + 1, a, a + n + 1, a + n + 2]:
				st.add_index(idx)
	st.generate_normals()
	var floor := MeshInstance3D.new()
	floor.mesh = st.commit()
	floor.material_override = v._snow_mat
	v.add_child(floor)
	# woods: thick on the valley edges, scattered in the middle, kept off the venues, the village and its roads
	var rng := RandomNumberGenerator.new()
	rng.seed = 12
	var trees: Array[Transform3D] = []
	var rocks: Array[Transform3D] = []
	for i in 7000:
		var a := rng.randf() * TAU
		var rr := sqrt(rng.randf_range(0.03, 1.0)) * 1000.0
		var clump := _lo.get_noise_2d(cos(a) * rr * 1.7 + 500.0, sin(a) * rr * 1.7)
		if clump < 0.05 and rng.randf() > 0.12:  # woods in stands, a few lone trees between
			continue
		var p := Vector3(cos(a) * rr + C.x, 0, sin(a) * rr + C.z)
		if FrostpeakHill.covers(p) or p.distance_to(FrostpeakView3D.PLAZA) < 60.0 or FrostpeakBiathlon.covers(p, 10.0):
			continue
		if absf(p.z) < 95.0 and p.x > -120.0 and p.x < 180.0:  # the oval, its stand and car park
			continue
		if _in_village(p, 40.0) or p.distance_to(STATION) < 50.0:
			continue
		if absf(p.z - river_z(p.x)) < 16.0:
			continue
		p.y = height(p.x, p.z)
		trees.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.5, 3.2)), p))
		if rng.randf() < 0.08:
			rocks.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1, rng.randf_range(0.6, 1.2), 1) * rng.randf_range(1.0, 3.0)), p + Vector3(rng.randf_range(-8, 8), -0.2, rng.randf_range(-8, 8))))
	v._forest(trees, 3)
	v._multi("boulder", rocks)


func _in_village(p: Vector3, margin := 0.0) -> bool:
	var q := p - VILLAGE
	var e := Vector2(q.x / (230.0 + margin), q.z / (120.0 + margin))
	return e.length() < 1.0


## The village: chalets along two lanes, hotels round the church square, a few farms scattered outside; warm
## windows, smoking chimneys, packed-snow lanes.
func _build_village() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	var houses: Array[Transform3D] = []
	var hotels: Array[Transform3D] = []
	var lane_mat := ShaderMaterial.new()
	lane_mat.shader = v._snow_mat.shader
	lane_mat.set_shader_parameter("tint", Color(0.86, 0.87, 0.9))
	lane_mat.set_shader_parameter("shade", Color(0.66, 0.68, 0.74))
	lane_mat.set_shader_parameter("sparkle", 0.2)
	# two lanes crossing at the square, gently curved
	var lanes := [[Vector3(-200, 0, -60), Vector3(-60, 0, -10), Vector3(60, 0, 10), Vector3(220, 0, 70)],
		[Vector3(-40, 0, -120), Vector3(-10, 0, -30), Vector3(10, 0, 40), Vector3(60, 0, 125)]]
	for lane in lanes:
		var pts: Array[Vector3] = []
		for i in 40:
			pts.append(VILLAGE + _bez(lane, i / 39.0))
		_lane(pts, 7.0, lane_mat)
		for i in range(1, 39, 2):
			var p := pts[i]
			var dir := (pts[i + 1] - pts[i - 1]).normalized()
			var side := Vector3(-dir.z, 0, dir.x)
			for s in [-1.0, 1.0]:
				if rng.randf() < 0.18 or (p + side * s * 14.0).distance_to(VILLAGE) < 28.0:
					continue
				var q: Vector3 = p + side * s * rng.randf_range(13.0, 17.0) + dir * rng.randf_range(-2.0, 2.0)
				var yaw := atan2(-side.x * s, -side.z * s) + rng.randf_range(-0.12, 0.12)  # the gable front to the lane
				var big := q.distance_to(VILLAGE) < 80.0 and rng.randf() < 0.45
				(hotels if big else houses).append(Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * rng.randf_range(0.9, 1.1)), q))
	for i in 38:  # farms and holiday chalets scattered round the edges
		var a := rng.randf() * TAU
		var q := VILLAGE + Vector3(cos(a) * rng.randf_range(160.0, 280.0), 0, sin(a) * rng.randf_range(90.0, 160.0))
		if FrostpeakHill.covers(q):
			continue
		houses.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU), q))
	for x in houses + hotels:
		x.origin.y = height(x.origin.x, x.origin.z) - 0.3
	v._multi("chalet", houses, v._prop_overrides("chalet"))
	v._multi("hotel", hotels, v._prop_overrides("hotel"))
	var ch := v._prop("church", VILLAGE + Vector3(0, 0, 0), 0.4)
	ch.position.y = -0.2
	# the square: packed snow, a tree with lights, a few people
	var sq := MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 24.0
	disc.bottom_radius = 24.0
	disc.height = 0.1
	disc.radial_segments = 40
	sq.mesh = disc
	sq.material_override = lane_mat
	sq.position = VILLAGE + Vector3(22, 0.02, 20)
	v.add_child(sq)
	var fans: Array[Transform3D] = []
	for i in 60:
		var a := rng.randf() * TAU
		var p := sq.position + Vector3(cos(a), 0, sin(a)) * rng.randf_range(4.0, 20.0)
		p.y = 0.0
		fans.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU), p))
	v._crowd(fans, 91, 0.4, false)
	# smoke from a few chimneys, drifting in the cold air
	for i in 10:
		var h: Transform3D = houses[(i * 7) % houses.size()]
		_chimney(h * Vector3(2.0, 9.0, 2.5))


func _bez(p: Array, t: float) -> Vector3:
	var u := 1.0 - t
	return p[0] * u * u * u + p[1] * 3.0 * u * u * t + p[2] * 3.0 * u * t * t + p[3] * t * t * t


## A flat ribbon on the ground through points.
func _lane(pts: Array[Vector3], width: float, mat: Material) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in pts.size() - 1:
		var d := (pts[i + 1] - pts[i]).normalized()
		var s := Vector3(-d.z, 0, d.x) * width * 0.5
		var a := pts[i] + Vector3(0, 0.03, 0)
		var b := pts[i + 1] + Vector3(0, 0.03, 0)
		for p in [a - s, b - s, b + s, a - s, b + s, a + s]:
			st.set_normal(Vector3.UP)
			st.add_vertex(p)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	v.add_child(mi)


func _chimney(p: Vector3) -> void:
	var smoke := GPUParticles3D.new()
	smoke.amount = 24
	smoke.lifetime = 7.0
	smoke.preprocess = 7.0
	smoke.visibility_aabb = AABB(Vector3(-20, -2, -20), Vector3(40, 40, 40))
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0.3, 1, 0.1)
	pm.spread = 8.0
	pm.initial_velocity_min = 1.2
	pm.initial_velocity_max = 1.8
	pm.gravity = Vector3(0.35, 0.1, 0.1)
	pm.scale_min = 2.0
	pm.scale_max = 3.0
	pm.scale_curve = _curve_tex(Fx.size_curve(true))
	pm.color_ramp = _fade()
	smoke.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(1.6, 1.6)
	smoke.draw_pass_1 = q
	smoke.material_override = Fx.material("smoke", Color(0.9, 0.9, 0.95, 0.5))
	smoke.position = p
	v.add_child(smoke)


func _curve_tex(c: Curve) -> CurveTexture:
	var t := CurveTexture.new()
	t.curve = c
	return t


func _fade() -> GradientTexture1D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 0.0))
	g.add_point(0.15, Color(1, 1, 1, 0.55))
	g.set_color(g.get_point_count() - 1, Color(1, 1, 1, 0.0))
	var t := GradientTexture1D.new()
	t.gradient = g
	return t


# ------------------------------------------------------------------ roads and the river

## Built once the jump hill stands (the roads climb onto its ground): ploughed roads linking the plaza, the oval,
## the village, the gondola and the jump arena, lined with marker poles; the frozen river with its snowy banks.
func build_roads(ground: Callable) -> void:
	var road := ShaderMaterial.new()
	road.shader = v._snow_mat.shader
	road.set_shader_parameter("tint", Color(0.84, 0.85, 0.88))
	road.set_shader_parameter("shade", Color(0.62, 0.64, 0.7))
	road.set_shader_parameter("sparkle", 0.15)
	var routes := [
		[FrostpeakView3D.PLAZA + Vector3(30, 0, 25), Vector3(-300, 0, 120), Vector3(-150, 0, 115), Vector3(-60, 0, 112)],
		[Vector3(-60, 0, 112), Vector3(60, 0, 112), Vector3(80, 0, 330), VILLAGE + Vector3(-200, 0, -60)],
		[VILLAGE + Vector3(220, 0, 70), Vector3(470, 0, 380), Vector3(430, 0, 200), Vector3(490, 0, 110)],
		[VILLAGE + Vector3(60, 0, 125), Vector3(420, 0, 640), Vector3(520, 0, 660), STATION + Vector3(-20, 0, -10)],
		[FrostpeakView3D.PLAZA + Vector3(25, 0, -28), Vector3(-455, 0, -95), Vector3(-450, 0, -160), Vector3(-418, 0, -186)],
	]
	var poles: Array[Transform3D] = []
	for r in routes:
		var pts: Array[Vector3] = []
		for i in 60:
			var p := _bez(r, i / 59.0)
			p.y = ground.call(p) + 0.08
			pts.append(p)
		_lane(pts, 8.0, road)
		var along := 0.0
		for i in pts.size() - 1:
			var d := pts[i + 1] - pts[i]
			var side := Vector3(-d.z, 0, d.x).normalized()
			along += d.length()
			if i % 3 == 0:
				for sd in [-5.0, 5.0]:
					var q: Vector3 = pts[i] + side * sd
					q.y = ground.call(q)
					poles.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.06, 2.0, 0.06)), q + Vector3(0, 1.0, 0)))
	var pole := CylinderMesh.new()
	pole.top_radius = 1.0
	pole.bottom_radius = 1.0
	pole.height = 1.0
	pole.radial_segments = 6
	pole.material = v._flat(Color(0.95, 0.35, 0.08), 0.5)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = pole
	mm.instance_count = poles.size()
	for i in poles.size():
		mm.set_instance_transform(i, poles[i])
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	v.add_child(mi)
	_build_river()


## The frozen river: a ribbon of blue-grey ice between low banks of drifted snow, bushes along its edges.
func _build_river() -> void:
	var pts: Array[Vector3] = []
	var x := -1150.0
	while x <= 1250.0:
		pts.append(Vector3(x, 0.05, river_z(x)))
		x += 10.0
	var ice := StandardMaterial3D.new()
	ice.albedo_color = Color(0.58, 0.7, 0.8)
	ice.roughness = 0.12
	ice.metallic_specular = 0.8
	_lane(pts, 17.0, ice)
	var bank := ShaderMaterial.new()
	bank.shader = v._snow_mat.shader
	bank.set_shader_parameter("bump_scale", 0.6)
	for sd in [-1.0, 1.0]:
		_bank(pts, sd, bank)
	var rng := RandomNumberGenerator.new()
	rng.seed = 55
	var bushes: Array[Transform3D] = []
	for i in 700:
		var bx := rng.randf_range(-1000.0, 1100.0)
		var bz := river_z(bx) + (1.0 if rng.randf() < 0.5 else -1.0) * rng.randf_range(12.0, 30.0)
		if Vector2(bx - C.x, bz - C.z).length() > INNER - 20.0 or FrostpeakHill.covers(Vector3(bx, 0, bz)):
			continue
		bushes.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.6, 1.4)), Vector3(bx, height(bx, bz), bz)))
	v._forest(bushes, 57)


## A low bank of drifted snow along one side of the river.
func _bank(pts: Array[Vector3], side: float, mat: Material) -> void:
	var prof := [Vector2(7.5, 0.0), Vector2(9.0, 0.7), Vector2(11.0, 1.0), Vector2(13.5, 0.6), Vector2(16.0, -0.2)]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in pts.size() - 1:
		var q := []
		for k in [i, i + 1]:
			var d := pts[mini(k + 1, pts.size() - 1)] - pts[maxi(k - 1, 0)]
			var sv := Vector3(-d.z, 0, d.x).normalized() * side
			var row := []
			for pr in prof:
				row.append(pts[k] + sv * pr.x + Vector3(0, pr.y, 0))
			q.append(row)
		for j in prof.size() - 1:
			var a: Vector3 = q[0][j]
			var b: Vector3 = q[1][j]
			var c: Vector3 = q[1][j + 1]
			var e: Vector3 = q[0][j + 1]
			var tri := [a, b, c, a, c, e] if side > 0.0 else [a, c, b, a, e, c]
			for vv in tri:
				st.add_vertex(vv)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	v.add_child(mi)


# ------------------------------------------------------------------ the gondola

func _build_gondola() -> void:
	var a := STATION
	var b := SUMMIT
	b.y = height(b.x, b.z)
	var dir := Vector3(b.x - a.x, 0, b.z - a.z).normalized()
	var yaw := atan2(dir.x, dir.z)  # the stations' fronts (+Z) face along the line
	v._prop("gondola_station", a, yaw)
	v._prop("gondola_station", b - dir * 4.0, yaw + PI)
	var side := Vector3(dir.z, 0, -dir.x)
	# pylons every ~110 m, following the ground; the rope rides 22 m over each
	var span := Vector3(b.x - a.x, 0, b.z - a.z).length()
	var n := int(span / 110.0)
	var tops: Array[Vector3] = [a + Vector3(0, 6.0, 0) + dir * 6.0]
	for i in range(1, n):
		var p := a + (b - a) * (float(i) / n)
		p.y = height(p.x, p.z)
		v._prop("gondola_pylon", p - Vector3(0, 0.5, 0), yaw)
		tops.append(p + Vector3(0, 21.6, 0))
	tops.append(b + Vector3(0, 6.0, 0) - dir * 10.0)
	var rope := v._flat(Color(0.15, 0.15, 0.17), 0.4)
	for s in [-3.0, 3.0]:
		for i in tops.size() - 1:
			var p0: Vector3 = tops[i] + side * s
			var p1: Vector3 = tops[i + 1] + side * s
			var mid := (p0 + p1) * 0.5
			var cyl := CylinderMesh.new()
			cyl.top_radius = 0.09
			cyl.bottom_radius = 0.09
			cyl.height = p0.distance_to(p1)
			cyl.radial_segments = 4
			cyl.rings = 1
			var mi := MeshInstance3D.new()
			mi.mesh = cyl
			mi.material_override = rope
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var up := (p1 - p0).normalized()
			mi.transform = Transform3D(Basis(up.cross(side).normalized(), up, side.normalized()).orthonormalized(), mid)
			v.add_child(mi)
	# the loop: up on the right-hand rope, down on the left
	for p in tops:
		_cable.append(p + side * 3.0)
	for i in range(tops.size() - 1, -1, -1):
		_cable.append(tops[i] - side * 3.0)
	_cable_len.append(0.0)
	for i in range(1, _cable.size()):
		_cable_len.append(_cable_len[i - 1] + _cable[i].distance_to(_cable[i - 1]))
	for i in 26:
		var c := v._prop("gondola_cabin", Vector3.ZERO)
		c.set_meta("s", _cable_len[_cable_len.size() - 1] * i / 26.0)
		cabins.append(c)
	process(0.0)


func process(delta: float) -> void:
	if _cable.is_empty():
		return
	var total := _cable_len[_cable_len.size() - 1]
	for c in cabins:
		var s := fposmod(float(c.get_meta("s")) + delta * 6.0, total)
		c.set_meta("s", s)
		var i := _cable_len.bsearch(s) - 1
		i = clampi(i, 0, _cable.size() - 2)
		var f := (s - _cable_len[i]) / maxf(_cable_len[i + 1] - _cable_len[i], 0.001)
		var p := _cable[i].lerp(_cable[i + 1], f)
		var d := _cable[i + 1] - _cable[i]
		c.position = p
		c.rotation = Vector3(0, atan2(d.x, d.z) + PI * 0.5, 0)


# ------------------------------------------------------------------ clouds

## Cloud banks clinging to the peaks: soft billboards with their own lit, drifting noise.
func _build_clouds() -> void:
	var sh: Shader = load(FrostpeakView3D.SH + "cloud.gdshader")
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for i in 18:
		var a := TAU * i / 18.0 + rng.randf_range(-0.1, 0.1)
		var r := rng.randf_range(1500.0, 2500.0)
		var c := C + Vector3(cos(a) * r, 0, sin(a) * r)
		c.y = clampf(height(c.x, c.z) * rng.randf_range(0.55, 0.85), 380.0, 1000.0)
		var along := Vector3(-sin(a), 0, cos(a))
		for k in 7:  # a bank: a row of soft puffs
			var q := QuadMesh.new()
			var sz := rng.randf_range(160.0, 340.0)
			q.size = Vector2(sz * 1.5, sz)
			var mi := MeshInstance3D.new()
			mi.mesh = q
			var m := ShaderMaterial.new()
			m.shader = sh
			m.set_shader_parameter("seed", rng.randf() * 100.0)
			m.set_shader_parameter("sun_dir", v._to_sun)
			mi.material_override = m
			mi.position = c + along * rng.randf_range(-320.0, 320.0) + Vector3(0, rng.randf_range(-40.0, 50.0), 0)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.extra_cull_margin = 200.0
			v.add_child(mi)
