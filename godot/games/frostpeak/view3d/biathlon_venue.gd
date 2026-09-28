class_name FrostpeakBiathlon
extends RefCounted
## The biathlon venue, built from the shared course (BiathlonCourse) so the picture is what the rules use: its own
## finer ground over the valley's, the groomed course with its marker poles, the stadium (the start and finish
## arch, a grandstand, fences with banners, the scoreboard, wax cabins), the range beside the straight (the firing
## mats, lane boards, wind flags, the targets fifty metres off in front of a snow berm) and the penalty loop, woods
## lining the course and spectators on the climb. The player's lane's five targets have white flaps that snap up
## over the black when hit.

const X0 := -478.0  ## the venue's own ground (world x, z)
const X1 := -190.0
const Z0 := -345.0
const Z1 := -138.0
const CELL := 2.5
const LANES := 10
const LANE_W := 2.6
const PLATE_Y := 0.8  ## the target plates' centre, above the ground
const FLOODLIGHTS: Array[Vector2] = [Vector2(-440, -160), Vector2(-445, -250), Vector2(-228, -170), Vector2(-222, -252)]

var v: FrostpeakView3D
var valley: FrostpeakValley
var root: Node3D
var flaps: Array[MeshInstance3D] = []  ## the player's targets' flaps (hidden until hit)
var _near := PackedFloat32Array()  ## per ground cell: metres to the course (or the stadium), for the woods
var _nx := 0
var _nz := 0


static func covers(p: Vector3, margin := 0.0) -> bool:
	return p.x > X0 - margin and p.x < X1 + margin and p.z > Z0 - margin and p.z < Z1 + margin


## 0 at the edge of the venue's ground, 1 once well inside it (where the valley's floor sinks out of sight).
static func inside(p: Vector3) -> float:
	var d := minf(minf(p.x - X0, X1 - p.x), minf(p.z - Z0, Z1 - p.z))
	return smoothstep(0.0, 10.0, d)


func _init(view: FrostpeakView3D, vl: FrostpeakValley) -> void:
	v = view
	valley = vl


func height(x: float, z: float) -> float:
	return valley.height(x, z)


func ground(x: float, z: float) -> Vector3:
	return Vector3(x, height(x, z), z)


## The centre of lane `k`'s target plate (k = 0 is the player's).
func plate(k := 0) -> Vector3:
	var t := BiathlonCourse.targets()
	var p := Vector3(t.x + k * LANE_W, 0.0, t.z)
	p.y = height(p.x, p.z) + PLATE_Y
	return p


## A point on target `i`'s face (aim offsets in metres on the plate: x to the right as the shooter sees it, y up).
func on_plate(aim: Vector2, k := 0) -> Vector3:
	return plate(k) + Vector3(aim.x, aim.y, 0.06)


func build() -> void:
	root = Node3D.new()
	root.name = "Biathlon"
	v.add_child(root)
	v._into = root
	_terrain()
	_near_field()
	_track()
	_stadium()
	_range()
	_course_dressing()
	_woods()
	v._into = v


# ------------------------------------------------------------------ ground and course

func _terrain() -> void:
	var nx := int((X1 - X0) / CELL)
	var nz := int((Z1 - Z0) / CELL)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in nx + 1:
		for k in nz + 1:
			var x := X0 + i * CELL
			var z := Z0 + k * CELL
			st.add_vertex(Vector3(x, height(x, z) - 0.02, z))
	for i in nx:
		for k in nz:
			var a := i * (nz + 1) + k
			for idx in [a, a + nz + 2, a + 1, a, a + nz + 1, a + nz + 2]:
				st.add_index(idx)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = v._snow_mat
	root.add_child(mi)


## How far each ground cell is from the course, the penalty loop or the stadium (the woods keep clear).
func _near_field() -> void:
	_nx = int((X1 - X0) / CELL) + 1
	_nz = int((Z1 - Z0) / CELL) + 1
	_near.resize(_nx * _nz)
	_near.fill(999.0)
	var stamp := func(p: Vector3, r: float) -> void:
		var ci := int((p.x - X0) / CELL)
		var ck := int((p.z - Z0) / CELL)
		var n := int(r / CELL) + 1
		for i in range(maxi(0, ci - n), mini(_nx, ci + n + 1)):
			for k in range(maxi(0, ck - n), mini(_nz, ck + n + 1)):
				var d := Vector2(X0 + i * CELL - p.x, Z0 + k * CELL - p.z).length()
				var j := i * _nz + k
				if d < _near[j]:
					_near[j] = d
	var s := 0.0
	while s < BiathlonCourse.lap():
		stamp.call(BiathlonCourse.point(s), 40.0)
		s += 2.0
	for u in range(0, int(BiathlonCourse.pen_loop()), 3):
		stamp.call(BiathlonCourse.pen_point(u), 30.0)
	for f in FLOODLIGHTS:
		stamp.call(Vector3(f.x, 0, f.y), 8.0)
	# the stadium, the range and the stands: one clear block
	var x := -420.0
	while x < -255.0:
		var z := -275.0
		while z < -160.0:
			stamp.call(Vector3(x, 0, z), 12.0)
			z += 6.0
		x += 6.0


func near(p: Vector3) -> float:
	var i := clampi(int(round((p.x - X0) / CELL)), 0, _nx - 1)
	var k := clampi(int(round((p.z - Z0) / CELL)), 0, _nz - 1)
	return _near[i * _nz + k]


## The width of the groomed course at s: wide through the stadium, a skating lane elsewhere.
func width(s: float) -> float:
	var lap := BiathlonCourse.lap()
	var st := smoothstep(95.0, 80.0, s) + smoothstep(lap - 50.0, lap - 35.0, s)
	return lerpf(6.0, 8.5, clampf(st, 0.0, 1.0))


## A groomed ribbon along points (each with its side vector and width), its edges sunk into the snow so it has no
## step at its sides; UV: x across (0..1), y along (metres).
func _ribbon(pts: Array[Vector3], sides: Array[Vector3], widths: Array[float], along: Array[float], mat: Material) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var across := [-1.0, -0.86, 0.0, 0.86, 1.0]
	var lift := [-0.04, 0.035, 0.05, 0.035, -0.04]
	var rows := []
	for i in pts.size():
		var row := []
		for k in across.size():
			var q: Vector3 = pts[i] + sides[i] * (widths[i] * 0.5 * across[k])
			q.y = height(q.x, q.z) + lift[k]
			row.append([q, Vector2((across[k] + 1.0) * 0.5, along[i])])
		rows.append(row)
	for i in pts.size() - 1:
		for k in across.size() - 1:
			var q: Array = [rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]]
			for idx in [0, 1, 2, 0, 2, 3]:
				st.set_uv(q[idx][1])
				st.add_vertex(q[idx][0])
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)


func _track() -> void:
	var mat := ShaderMaterial.new()
	mat.shader = load(FrostpeakView3D.SH + "track.gdshader")
	var pts: Array[Vector3] = []
	var sides: Array[Vector3] = []
	var widths: Array[float] = []
	var along: Array[float] = []
	var lap := BiathlonCourse.lap()
	var s := 0.0
	while s <= lap + 0.01:
		var d := BiathlonCourse.dir(s)
		pts.append(BiathlonCourse.point(s))
		sides.append(Vector3(-d.y, 0.0, d.x))
		widths.append(width(s))
		along.append(s)
		s += 1.0
	_ribbon(pts, sides, widths, along, mat)
	# the penalty loop, narrower
	pts.clear()
	sides.clear()
	widths.clear()
	along.clear()
	var n := int(BiathlonCourse.pen_loop())
	for u in n + 1:
		var a := BiathlonCourse.pen_point(u - 0.5)
		var b := BiathlonCourse.pen_point(u + 0.5)
		var d := (b - a).normalized()
		pts.append(BiathlonCourse.pen_point(u))
		sides.append(Vector3(-d.z, 0.0, d.x))
		widths.append(4.0)
		along.append(u)
	_ribbon(pts, sides, widths, along, mat)


# ------------------------------------------------------------------ the stadium

func _stadium() -> void:
	var line := BiathlonCourse.point(0.0)
	var pad := v._flat(Color(0.1, 0.24, 0.62), 0.55)
	var banners := v._banner_set()
	# the start and finish arch over the straight, the lines on the snow
	var arch := v._scene("finish_arch")
	arch.transform = Transform3D(Basis(Vector3.UP, PI * 0.5).rotated(Vector3.UP, 0.0), line)
	arch.basis = Basis.looking_at(Vector3(1, 0, 0), Vector3.UP).rotated(Vector3.UP, PI * 0.5)
	root.add_child(arch)
	v._box(root, line + Vector3(0, 0.06, 0), Vector3(0.25, 0.02, 8.6), v._flat(Color(0.85, 0.08, 0.1), 0.4))
	# the grandstand south of the straight, looking north across the stadium to the range
	for k in 3:
		var p := Vector3(-372.0 + k * FrostpeakView3D.SEC, 0.0, -176.0)
		p.y = height(p.x, p.z) - 0.2
		v._stand(Transform3D(Basis(Vector3.UP, PI), p), 70 + k, 0.55)
	for x in [-372.0 - FrostpeakView3D.SEC * 0.5 - 0.2, -324.0 + FrostpeakView3D.SEC * 0.5 + 0.2]:
		v._prop("grandstand_end", ground(x, -176.0) + Vector3(0, -0.2, 0), PI)
	# padded fences along the straight (the penalty loop inside the south one) with banners to the camera
	var bi := 0
	for side in [-1.0, 1.0]:
		var z: float = -184.0 if side > 0.0 else -204.8
		var x := -404.0
		while x < -262.0:
			if side < 0.0 and x > -352.0 and x < -322.0:  # the range's opening
				x += 4.0
				continue
			var p := ground(x + 2.0, z) + Vector3(0, 0.55, 0)
			v._box(root, p, Vector3(4.0, 1.1, 0.25), pad)
			v._quad(p + Vector3(0, 0, -0.13 * side), Vector2(3.9, 0.9), banners[bi % banners.size()], Basis(Vector3.UP, PI if side > 0.0 else 0.0))
			bi += 1
			x += 4.0
	# fans along the fence in front of the stand, and along the finish straight's end
	var rng := RandomNumberGenerator.new()
	rng.seed = 81
	var fans: Array[Transform3D] = []
	for i in 160:
		var x := rng.randf_range(-400.0, -266.0)
		var z := rng.randf_range(-183.2, -180.5)
		if x > -386.0 and x < -312.0:
			continue
		fans.append(Transform3D(Basis(Vector3.UP, PI + rng.randf_range(-0.4, 0.4)), ground(x, z)))
	v._crowd(fans, 83)
	# the scoreboard at the west end, the TV tower, flags, wax cabins, snow-cats
	v._scoreboard(ground(-420.0, -190.0), PI * 0.5 + 0.35, "BIATHLON")
	v._prop("tv_tower", ground(-300.0, -168.0), PI)
	for i in 5:  # the nations' flags at both ends of the stadium
		v._pole_flag(ground(-418.0, -214.0 + i * 8.0), i, PI * 0.5)
		v._pole_flag(ground(-266.0, -218.0 + i * 8.0), i + 1, -PI * 0.5)
	for i in 4:
		v._prop("tent", ground(-440.0, -150.0 - i * 16.0), PI * 0.5)
	v._prop("snowcat", ground(-262.0, -165.0), 0.6)
	for f in FLOODLIGHTS:
		v._prop("floodlight", ground(f.x, f.y), atan2(-(f.x + 335.0), -(f.y + 205.0)))


# ------------------------------------------------------------------ the range

func _range() -> void:
	var mat_c := BiathlonCourse.mat()
	var wood := Pbr.local("planks", Color(0.72, 0.52, 0.34), 0.8)
	var steel := Pbr.material("metal", Color(0.3, 0.33, 0.36), 0.7, 0.8, 0.5)
	var dark := v._flat(Color(0.08, 0.09, 0.1), 0.6)
	var white := v._flat(Color(0.96, 0.96, 0.97), 0.45)
	var black := v._flat(Color(0.02, 0.02, 0.025), 0.7)
	var green := v._flat(Color(0.1, 0.3, 0.2), 0.6)
	for k in range(-4, LANES - 4):
		var x := mat_c.x + k * LANE_W
		# the firing mat (the shooter lies along it, facing the targets) and the lane board in front of it
		var m := ground(x, mat_c.z - 1.6)
		v._box(root, m + Vector3(0, 0.03, 0), Vector3(1.5, 0.06, 3.3), wood)
		var nb := ground(x, mat_c.z - 3.8)
		v._box(root, nb + Vector3(0, 0.35, 0), Vector3(0.06, 0.7, 0.06), steel)
		var board := v._box(root, nb + Vector3(0, 0.78, 0), Vector3(0.5, 0.36, 0.04), v._flat(Color(0.95, 0.8, 0.2) if k == 0 else Color(0.95, 0.95, 0.97), 0.5))
		var lb := Label3D.new()
		lb.text = str(k + 5)
		lb.font = HudKit.font(true)
		lb.font_size = 72
		lb.pixel_size = 0.004
		lb.modulate = Color(0.08, 0.08, 0.1)
		lb.outline_size = 0
		lb.shaded = true
		lb.position = Vector3(0, 0, 0.03)
		board.add_child(lb)
		# the rifle rack behind the mat
		var rk := ground(x - 0.5, mat_c.z + 1.4)
		v._box(root, rk + Vector3(0, 0.5, 0), Vector3(0.9, 0.06, 0.12), wood)
		# the target frame: a dark plate on legs, a white face with five black targets
		var p := plate(k)
		v._box(root, p, Vector3(0.78, 0.26, 0.1), dark)
		v._box(root, p + Vector3(0, 0, 0.052), Vector3(0.7, 0.16, 0.01), white)
		for leg in [-0.32, 0.32]:
			var g := ground(p.x + leg, p.z)
			v._box(root, Vector3(p.x + leg, (g.y + p.y) * 0.5, p.z - 0.03), Vector3(0.06, p.y - g.y, 0.06), dark)
		v._box(root, p + Vector3(0, 0.22, 0.02), Vector3(0.3, 0.14, 0.02), v._flat(Color(0.95, 0.8, 0.2) if k == 0 else Color(0.95, 0.95, 0.97), 0.5))
		for i in Biathlon.SHOTS:
			var c := p + Vector3(Biathlon.target(i).x, 0.0, 0.058)
			var disc := _disc(c, Biathlon.TARGET_R, black)
			var flap := _disc(c + Vector3(0, 0, 0.004), Biathlon.TARGET_R * 1.12, white)
			flap.visible = false
			if k == 0:
				flaps.append(flap)
			elif (k * 7 + i * 3) % 5 < 2:
				flap.visible = true  # the lanes beside have been shooting too
			disc.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# the berm behind the targets, its face dressed with a banner, and low side walls
	var berm := ShaderMaterial.new()
	berm.shader = v._snow_mat.shader
	berm.set_shader_parameter("bump_scale", 0.6)
	var t0 := plate(-4)
	var t1 := plate(LANES - 5)
	var cx := (t0.x + t1.x) * 0.5
	var bz := t0.z - 4.0
	var bh := height(cx, bz)
	var b := v._box(root, Vector3(cx, bh + 1.6, bz - 1.5), Vector3(t1.x - t0.x + 14.0, 3.6, 5.0), berm)
	b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var sign := v._banner_mat("FROSTPEAK  RANGE", Color.WHITE, Color(0.1, 0.25, 0.65), Color(1.0, 0.82, 0.25))
	v._quad(Vector3(cx, bh + 2.3, bz + 1.02), Vector2(t1.x - t0.x + 4.0, 1.4), sign, Basis.IDENTITY)
	for sx in [t0.x - 5.0, t1.x + 5.0]:
		v._box(root, Vector3(sx, bh + 0.8, (t0.z + mat_c.z) * 0.5), Vector3(0.6, 1.6, 44.0), berm)
	# wind flags on thin poles down both sides of the range and between the lanes, halfway
	for z in [mat_c.z - 12.0, mat_c.z - 26.0, mat_c.z - 40.0]:
		for x in [t0.x - 3.2, t1.x + 3.2]:
			var g := ground(x, z)
			v._box(root, g + Vector3(0, 1.6, 0), Vector3(0.04, 3.2, 0.04), steel)
			var f := v._flag(g + Vector3(0.35, 2.9, 0), [Color(0.95, 0.4, 0.1), Color(0.95, 0.95, 0.95), Color(0.95, 0.4, 0.1)], Vector2(0.7, 0.3), 0.0)
			f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# a green screen of netting behind the mats (the stadium side)
	v._box(root, ground(cx, mat_c.z + 2.6) + Vector3(0, 0.05, 0), Vector3(t1.x - t0.x + 6.0, 0.1, 0.3), green)


func _disc(c: Vector3, r: float, mat: Material) -> MeshInstance3D:
	var cyl := CylinderMesh.new()
	cyl.top_radius = r
	cyl.bottom_radius = r
	cyl.height = 0.006
	cyl.radial_segments = 24
	cyl.rings = 1
	var mi := MeshInstance3D.new()
	mi.mesh = cyl
	mi.material_override = mat
	mi.transform = Transform3D(Basis(Vector3.RIGHT, PI * 0.5), c)
	root.add_child(mi)
	return mi


## Closes the player's target `i` (a hit).
func hit(i: int) -> void:
	if i >= 0 and i < flaps.size():
		flaps[i].visible = true


func reset_targets() -> void:
	for f in flaps:
		f.visible = false


# ------------------------------------------------------------------ the course and the woods

func _course_dressing() -> void:
	# marker poles down both sides (orange, every 10 m), a red-and-white rope on the climb
	var poles: Array[Transform3D] = []
	var lap := BiathlonCourse.lap()
	var s := 95.0
	while s < lap - 50.0:
		var d := BiathlonCourse.dir(s)
		var side := Vector3(-d.y, 0.0, d.x)
		for k in [-1.0, 1.0]:
			var q: Vector3 = BiathlonCourse.point(s) + side * (width(s) * 0.5 + 1.2) * k
			q.y = height(q.x, q.z)
			poles.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.05, 1.6, 0.05)), q + Vector3(0, 0.8, 0)))
		s += 10.0
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
	root.add_child(mi)
	# spectators on the climb and the top of the hill, behind the poles
	var rng := RandomNumberGenerator.new()
	rng.seed = 91
	var fans: Array[Transform3D] = []
	for section in [[110.0, 175.0, 220], [205.0, 235.0, 70]]:
		for i in int(section[2]):
			var fs := rng.randf_range(section[0], section[1])
			var d := BiathlonCourse.dir(fs)
			var side := Vector3(-d.y, 0.0, d.x) * (-1.0 if i % 3 == 0 else 1.0)
			var q := BiathlonCourse.point(fs) + side * (width(fs) * 0.5 + rng.randf_range(4.8, 8.5))  # clear of the camera
			q.y = height(q.x, q.z)
			var face := -side
			fans.append(Transform3D(Basis.looking_at(-face, Vector3.UP).rotated(Vector3.UP, rng.randf_range(-0.5, 0.5)), q))
	v._crowd(fans, 93)


func _woods() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 95
	var near: Array[Transform3D] = []
	var far: Array[Transform3D] = []
	for i in 9000:
		var p := Vector3(rng.randf_range(X0 + 4.0, X1 - 4.0), 0.0, rng.randf_range(Z0 + 4.0, Z1 - 4.0))
		var d := near(p)
		if d < 11.0 + rng.randf() * 4.0:
			continue
		if valley._lo.get_noise_2d(p.x * 2.0, p.z * 2.0) < -0.25 and d > 30.0:  # glades
			continue
		if p.z > -150.0 or (p.x < -430.0 and p.z > -200.0):  # the road in and the wax cabins
			continue
		p.y = height(p.x, p.z)
		var xf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.4, 2.8)), p - Vector3(0, 0.3, 0))
		if d < 30.0:
			if rng.randf() < 0.55:  # (thinned: close by, fewer do)
				near.append(xf)
		else:
			far.append(xf)
	# the trees lining the course in full (seen close, casting shadows), the woods behind as light cones
	v._forest(near, 96, true, 600.0)
	v._forest_far(far)
