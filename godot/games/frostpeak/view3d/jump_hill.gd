class_name FrostpeakHill
extends RefCounted
## The large hill's venue, built from the shared hill (SkiHill) so the picture is what the physics uses: the in-run
## on its concrete piers with the start tower, the take-off table, the knoll between wind nets, the landing slope
## with its painted lines, distance boards and padded fences, the judges' tower and the coaches' platform, TV
## towers and floodlights, and at the bottom the arena: the outrun between grandstands, the standing crowd behind
## the barrier, the big screen, hospitality tents and snow-cats.
## Everything is placed in the hill's own frame (x downhill, y up, z across, the lip at the origin), which sits in
## the valley so that the in-run backs onto the mountains and the outrun meets the valley floor.

const LIP := Vector2(820.0, 0.0)  ## the lip's world x and z
const YAW := PI  ## the hill runs towards -x in the world
const X0 := -430.0  ## the terrain patch, in the hill's frame
const X1 := 470.0
const Z1 := 330.0
const WALL := 1.95  ## the in-run's side walls, out from its centre line
const SIDE_CAM := 97.0  ## the TV tower beside the landing slope (metres of hill, x)
const OUTRUN_STOP := 262.0  ## where the jumpers come to a halt (x)

var v: FrostpeakView3D
var valley: FrostpeakValley
var root: Node3D
var xf: Transform3D
var _noise := FastNoiseLite.new()


static func origin() -> Vector3:
	return Vector3(LIP.x, -SkiHill.outrun_y(), LIP.y)


static func frame() -> Transform3D:
	return Transform3D(Basis(Vector3.UP, YAW), origin())


## Whether a world point lies on the hill's own terrain patch (the valley keeps its trees off it).
static func covers(p: Vector3) -> bool:
	var l := frame().affine_inverse() * Vector3(p.x, 0.0, p.z)
	return l.x > X0 - 20.0 and l.x < X1 + 20.0 and absf(l.z) < Z1 + 20.0


func _init(view: FrostpeakView3D, vl: FrostpeakValley) -> void:
	v = view
	valley = vl
	xf = frame()
	_noise.seed = 19
	_noise.frequency = 0.012
	_noise.fractal_octaves = 3


func world(p: Vector3) -> Vector3:
	return xf * p


func local(p: Vector3) -> Vector3:
	return xf.affine_inverse() * p


# ------------------------------------------------------------------ the ground

## The ground along the hill's axis: the profile for x >= 0; under the in-run a hillside that keeps rising
## behind the start tower into the mountains.
func centre_y(x: float) -> float:
	if x >= 0.0:
		return SkiHill.ground_y(x)
	var t := -x
	return -SkiHill.TABLE_H + t * 0.3 + maxf(0.0, t - 100.0) * 0.25 + maxf(0.0, t - 160.0) * 0.35


## Half the width of the prepared slope (the fences stand here), widening into the arena.
func half_width(x: float) -> float:
	const XS := [-1000.0, 0.0, 60.0, 110.0, 150.0, 195.0, 240.0, 1000.0]
	const WS := [8.0, 11.0, 16.0, 19.0, 24.0, 44.0, 58.0, 62.0]
	for i in XS.size() - 1:
		if x < XS[i + 1]:
			var f: float = (x - XS[i]) / (XS[i + 1] - XS[i])
			return lerpf(WS[i], WS[i + 1], smoothstep(0.0, 1.0, f))
	return WS[WS.size() - 1]


## The terrain's height in the hill's frame.
func terrain_y(x: float, z: float) -> float:
	var y := centre_y(x)
	var d := maxf(0.0, absf(z) - half_width(x))
	var bowl := smoothstep(150.0, 210.0, x)
	y += minf(d * lerpf(0.34, 0.16, bowl) + d * d * lerpf(0.0028, 0.0012, bowl), 70.0)
	y += _noise.get_noise_2d(x, z) * 9.0 * smoothstep(0.0, 45.0, d)
	# into the valley floor and the mountains at the patch's edges
	var e := maxf(smoothstep(170.0, Z1 - 10.0, absf(z)), maxf(smoothstep(380.0, X1 - 10.0, x), smoothstep(-300.0, X0 + 10.0, x)))
	if e > 0.0:
		var w := world(Vector3(x, 0, z))
		y = lerpf(y, valley.height(w.x, w.z) - xf.origin.y, e)
	return y


func ground(x: float, z: float) -> Vector3:
	return Vector3(x, terrain_y(x, z), z)


# ------------------------------------------------------------------ building

func build() -> void:
	root = Node3D.new()
	root.name = "JumpHill"
	root.transform = xf
	v.add_child(root)
	v._into = root
	_terrain()
	_inrun()
	_tower()
	_table()
	_slope()
	_arena()
	# everything solid casts the sun's shadow (the in-run, the towers, the masts, the fences, the crowds); nets and
	# glass would cast solid ones, so they cast none
	for g in root.find_children("*", "GeometryInstance3D", true, false):
		var gi := g as GeometryInstance3D
		var m := gi.material_override as BaseMaterial3D
		if m and m.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
			gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_trees()
	v._into = v


func _terrain() -> void:
	var xs: Array[float] = []
	var x := X0
	while x <= X1:
		xs.append(x)
		x += 2.0 if x > -110.0 and x < 320.0 else 6.0
	var zs: Array[float] = []
	var z := 0.0
	var half: Array[float] = []
	while z <= Z1:
		half.append(z)
		z += 2.5 if z < 60.0 else (6.0 if z < 160.0 else 12.0)
	for i in range(half.size() - 1, 0, -1):
		zs.append(-half[i])
	zs.append_array(half)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for xx in xs:
		for zz in zs:
			st.add_vertex(ground(xx, zz))
	var row := zs.size()
	for i in xs.size() - 1:
		for k in row - 1:
			var a := i * row + k
			for idx in [a, a + row + 1, a + 1, a, a + row, a + row + 1]:
				st.add_index(idx)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = v._snow_mat.shader
	m.set_shader_parameter("shade", Color(0.78, 0.84, 0.95))
	m.set_shader_parameter("sparkle", 1.4)
	m.set_shader_parameter("mark_tex", _markings())
	m.set_shader_parameter("mark_rect", Vector4(0.0, -30.0, 300.0, 60.0))
	m.set_shader_parameter("mark_local", true)
	m.set_shader_parameter("mark_o", xf.origin)
	m.set_shader_parameter("mark_x", xf.basis.x)
	m.set_shader_parameter("mark_z", xf.basis.z)
	mi.material_override = m
	root.add_child(mi)


## The painted landing slope: a thin blue line every 5 m and a stronger one every 10 m, the K line in red, the
## hill size in green, and rows of spruce twigs down both edges of the landing area (4 px a metre, x 0..300,
## z -30..30).
func _markings() -> ImageTexture:
	var img := Image.create(1200, 240, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var paint := func(x0: float, w_px: int, col: Color, z_half: float) -> void:
		var px := int(x0 * 4.0)
		var half := int(z_half * 4.0)
		for w in w_px:
			for y in range(120 - half, 120 + half):
				if px + w >= 0 and px + w < 1200:
					img.set_pixel(px + w, y, col)
	for d in range(50, 146, 5):
		var x := SkiHill.land_point(d).x
		var hw := half_width(x) - 0.6
		var col := Color(0.12, 0.28, 0.85, 0.8 if d % 10 == 0 else 0.4)
		var w := 2 if d % 10 == 0 else 1
		if d == int(SkiHill.K):
			col = Color(0.88, 0.08, 0.1, 0.95)
			w = 2
		elif d == 135:  # the hill size falls at 134
			continue
		paint.call(x, w, col, hw)
	paint.call(SkiHill.land_point(SkiHill.HS).x, 2, Color(0.1, 0.62, 0.25, 0.95), half_width(SkiHill.land_point(SkiHill.HS).x) - 0.6)
	# spruce twigs: dark green dashes along both edges of the landing area
	var twig := Color(0.08, 0.26, 0.12, 0.95)
	var s := 40.0
	while s < 160.0:
		var x := SkiHill.land_point(s).x
		var hw := half_width(x) - 1.6
		for side in [-1.0, 1.0]:
			var y := 120 + int(side * hw * 4.0)
			for dx in 4:
				for dy in 2:
					var px := int(x * 4.0) + dx
					if px < 1200 and y + dy < 240 and y + dy >= 0:
						img.set_pixel(px, y + dy, twig)
		s += 1.6
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


# ------------------------------------------------------------------ the in-run

## A cross-section swept along the in-run: `prof` is [(across, up from the track)] points; `closed` joins the
## last point back to the first.
func _sweep(prof: Array[Vector2], a0: float, a1: float, mat: Material, closed := false, step := 1.0) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var secs := []
	var a := a0
	while true:
		var p := SkiHill.inrun_point(a)
		var th := SkiHill.inrun_angle(a)
		var n := Vector2(sin(th), cos(th))
		var sec: Array[Vector3] = []
		for q in prof:
			sec.append(Vector3(p.x + n.x * q.y, p.y + n.y * q.y, q.x))
		secs.append(sec)
		if a >= a1:
			break
		a = minf(a + step, a1)
	var m := prof.size()
	for i in secs.size() - 1:
		for k in (m if closed else m - 1):
			var k2 := (k + 1) % m
			var q0: Vector3 = secs[i][k]
			var q1: Vector3 = secs[i][k2]
			var q2: Vector3 = secs[i + 1][k2]
			var q3: Vector3 = secs[i + 1][k]
			for vv in [q0, q2, q1, q0, q3, q2]:
				st.add_vertex(vv)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	root.add_child(mi)
	return mi


## A point beside the in-run: `across` from its centre line, `up` from the track, `along` from the gate.
func inrun_at(along: float, across: float, up := 0.0) -> Vector3:
	var p := SkiHill.inrun_point(along)
	var th := SkiHill.inrun_angle(along)
	return Vector3(p.x + sin(th) * up, p.y + cos(th) * up, across)


## The basis of the in-run at `along`: x down the track, y square to it.
func inrun_basis(along: float) -> Basis:
	return Basis(Vector3.BACK, -SkiHill.inrun_angle(along))


func _inrun() -> void:
	var a0 := SkiHill.TOP
	var a1 := SkiHill.INRUN
	var concrete := Pbr.material("metal", Color(0.62, 0.64, 0.68), 0.35, 0.0, 1.2)
	var steel := Pbr.material("metal", Color(0.36, 0.4, 0.46), 0.8, 0.8, 0.6)
	var wall := v._flat(Color(0.08, 0.22, 0.55), 0.45)
	var white := v._flat(Color(0.93, 0.95, 0.98), 0.35)
	var bed := v._flat(Color(0.88, 0.91, 0.96), 0.25)
	var ice := v._flat(Color(0.62, 0.74, 0.86), 0.04)
	ice.metallic_specular = 1.0
	var lamp := v._flat(Color(1.0, 0.95, 0.82), 0.3, 1.6)
	# the deck, the track bed and the two ice grooves the skis ride in
	_sweep([Vector2(-2.7, -0.08), Vector2(2.7, -0.08), Vector2(2.7, -0.6), Vector2(-2.7, -0.6)] as Array[Vector2], a0, a1, concrete, true)
	_sweep([Vector2(-WALL + 0.1, -0.03), Vector2(WALL - 0.1, -0.03)] as Array[Vector2], a0, a1, bed)
	for zc in [-0.14, 0.14]:
		_sweep([Vector2(zc - 0.055, 0.005), Vector2(zc + 0.055, 0.005)] as Array[Vector2], 0.0, a1, ice)
	# side walls with a white cap and a strip of lights along their foot
	for s in [-1.0, 1.0]:
		var w0: float = s * WALL
		var w1: float = s * (WALL + 0.16)
		_sweep([Vector2(w0, -0.08), Vector2(w0, 0.78), Vector2(w1, 0.78), Vector2(w1, -0.08)] as Array[Vector2], a0, a1, wall, true)
		_sweep([Vector2(w0 - s * 0.02, 0.78), Vector2(w0 - s * 0.02, 0.86), Vector2(w1 + s * 0.02, 0.86), Vector2(w1 + s * 0.02, 0.78)] as Array[Vector2], a0, a1, white, true)
		_sweep([Vector2(w0 - s * 0.01, 0.06), Vector2(w0 - s * 0.01, 0.12)] as Array[Vector2], a0, a1, lamp)
	# two box girders under the deck, and the stair down the left side with its railing
	for s in [-1.0, 1.0]:
		_sweep([Vector2(s * 2.35, -0.6), Vector2(s * 2.35, -2.0), Vector2(s * 1.75, -2.0), Vector2(s * 1.75, -0.6)] as Array[Vector2], a0, a1 - 8.0, steel, true, 2.0)
	_sweep([Vector2(-4.0, -0.4), Vector2(-2.7, -0.4), Vector2(-2.7, -0.55), Vector2(-4.0, -0.55)] as Array[Vector2], a0, a1 - 6.0, steel, true)
	_sweep([Vector2(-4.02, 1.05), Vector2(-3.98, 1.05), Vector2(-3.98, 1.0), Vector2(-4.02, 1.0)] as Array[Vector2], a0, a1 - 6.0, steel, true)
	var steps: Array[Transform3D] = []
	var posts: Array[Transform3D] = []
	var heads: Array[Transform3D] = []
	var a := a0
	while a < a1 - 6.0:
		var th := SkiHill.inrun_angle(a)
		var p := inrun_at(a, -3.35, -0.4)
		steps.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.3, 0.02 + 0.3 * tan(th), 1.3)), p + Vector3(0, 0.15 * tan(th), 0)))
		a += 0.3 / cos(th)
	a = a0
	while a < a1:
		posts.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.06, 1.0, 0.06)), inrun_at(a, -4.0, 0.0) + Vector3(0, 0.5, 0)))
		# lamp posts on the right-hand side, heads leaning over the track
		var lp := inrun_at(a, WALL + 0.45, 0.0)
		posts.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.08, 1.8, 0.08)), lp + Vector3(0, 0.9, 0)))
		heads.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.22, 0.08, 0.4)), lp + Vector3(0, 1.8, -0.25)))
		a += 5.0
	_boxes(steps, steel)
	_boxes(posts, steel)
	_boxes(heads, lamp)
	# the piers: pairs of concrete columns under the girders, braced across, wherever the deck is off the ground
	a = a0 + 6.0
	var cols: Array[Transform3D] = []
	var braces: Array[Transform3D] = []
	while a < a1 - 10.0:
		var top := inrun_at(a, 0.0, -2.0)
		var g := centre_y(top.x)
		var h := top.y - g
		if h > 1.2:
			for s in [-1.0, 1.0]:
				var w := 0.8 + h * 0.012
				cols.append(Transform3D(Basis.IDENTITY.scaled(Vector3(w, h + 1.0, w)), Vector3(top.x, (top.y + g - 1.0) * 0.5, s * 2.05)))
			var levels := int(h / 9.0)
			for k in levels:
				var y := g + h * (k + 1) / (levels + 1)
				braces.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.6, 0.6, 4.1)), Vector3(top.x, y, 0.0)))
			# cross bracing in steel between the pairs
			if h > 5.0:
				var diag := sqrt(h * h + 16.0)
				for s in [-1.0, 1.0]:
					var b := Basis(Vector3.RIGHT, s * atan2(4.0, h)).scaled(Vector3(0.12, diag, 0.12))
					braces.append(Transform3D(b, Vector3(top.x, (top.y + g) * 0.5, 0.0)))
		a += 11.0
	_boxes(cols, concrete)
	_boxes(braces, steel)
	# sponsor boards along the outside of the walls, where the side cameras see them
	var banners := v._banner_set()
	a = 4.0
	var bi := 0
	while a < a1 - 10.0:
		for s in [-1.0, 1.0]:
			var p := inrun_at(a + 2.2, s * (WALL + 0.17), 0.36)
			var yaw := 0.0 if s > 0.0 else PI
			var bb := inrun_basis(a + 2.2) * Basis(Vector3.UP, yaw)
			v._quad(p, Vector2(4.2, 0.62), banners[bi % banners.size()], bb)
			bi += 1
		a += 4.6
	# the start gate across the track, and the gate numbers on the wall above it
	var gate := v._scene("start_gate")
	gate.transform = Transform3D(Basis(Vector3.UP, PI * 0.5), inrun_at(0.0, 0.0, 0.3))
	root.add_child(gate)
	for i in 12:
		var ga := -float(i) * 1.1
		var lb := Label3D.new()
		lb.text = str(i + 1)
		lb.font = HudKit.font(true)
		lb.font_size = 64
		lb.pixel_size = 0.0035
		lb.modulate = Color(1, 1, 1)
		lb.outline_size = 0
		lb.transform = Transform3D(inrun_basis(ga) * Basis(Vector3.UP, 0.0), inrun_at(ga, WALL + 0.18, 0.5))
		root.add_child(lb)


## Boxes in one MultiMesh (unit cube scaled by each transform).
func _boxes(xs: Array[Transform3D], mat: Material) -> void:
	if xs.is_empty():
		return
	var b := BoxMesh.new()
	b.material = mat
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = b
	mm.instance_count = xs.size()
	for i in xs.size():
		mm.set_instance_transform(i, xs[i])
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	root.add_child(mi)


## The start tower: a concrete shaft under the top of the in-run, the start platform with the athletes' cabin,
## a glazed lift shaft, the games' name on its flanks and the nations' flags on the rail.
func _tower() -> void:
	var concrete := Pbr.material("metal", Color(0.86, 0.87, 0.89), 0.35, 0.0, 1.2)
	var steel := Pbr.material("metal", Color(0.36, 0.4, 0.46), 0.8, 0.8, 0.6)
	var top := SkiHill.inrun_point(SkiHill.TOP)
	var cx := top.x - 5.0
	var g := centre_y(cx + 6.0) - 2.0
	var deck := top.y - 0.7
	v._box(root, Vector3(cx, (deck + g) * 0.5, 0), Vector3(11.0, deck - g, 10.0), concrete)
	v._box(root, Vector3(cx - 1.0, deck + 0.2, 0), Vector3(15.0, 0.5, 13.0), steel)
	# the tower's bands: dark glazing strips up its faces
	var glass := v._flat(Color(0.18, 0.28, 0.4), 0.08)
	glass.metallic = 0.4
	var y := g + 6.0
	while y < deck - 3.0:
		for s in [-1.0, 1.0]:
			v._box(root, Vector3(cx, y, s * 5.02), Vector3(9.0, 1.2, 0.08), glass)
		v._box(root, Vector3(cx - 5.52, y, 0), Vector3(0.08, 1.2, 8.0), glass)
		y += 5.0
	# the lift shaft on the left, glazed
	var shaft := v._flat(Color(0.55, 0.7, 0.85), 0.05)
	shaft.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	shaft.albedo_color.a = 0.45
	v._box(root, Vector3(cx + 1.0, (deck + 4.0 + g) * 0.5, -6.6), Vector3(2.6, deck + 4.0 - g, 2.6), shaft)
	v._box(root, Vector3(cx + 1.0, deck + 4.1, -6.6), Vector3(3.0, 0.3, 3.0), steel)
	# the athletes' cabin on the platform, looking down the track
	var house := v._scene("start_house")
	house.transform = Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(cx - 6.0, deck + 0.45, 4.2))
	root.add_child(house)
	v._texture(house)
	# the rail and the nations' flags round the platform
	for i in 6:
		var p := Vector3(cx - 8.0 + i * 2.6, deck + 0.45, -6.3)
		v._pole_flag(p, i)
	# the games' name on both flanks of the tower
	var sign := v._banner_mat("FROSTPEAK", Color.WHITE, Color(0.1, 0.25, 0.65), Color(1.0, 0.82, 0.25))
	for s in [-1.0, 1.0]:
		v._quad(Vector3(cx, deck - 4.0, s * 5.08), Vector2(10.4, 2.6), sign, Basis(Vector3.UP, 0.0 if s > 0.0 else PI))


## The take-off table: the in-run's last metres on a solid block, the lip picked out in red, the block's face
## towards the knoll dressed with a banner.
func _table() -> void:
	var concrete := Pbr.material("metal", Color(0.86, 0.87, 0.89), 0.35, 0.0, 1.2)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var a := SkiHill.INRUN - 16.0
	var prev: Array[Vector3] = []
	while true:
		var t := inrun_at(a, 0.0, -0.6)
		var gy := centre_y(t.x) - 1.5
		var sec: Array[Vector3] = [Vector3(t.x, t.y, -2.7), Vector3(t.x, t.y, 2.7), Vector3(t.x, gy, 2.7), Vector3(t.x, gy, -2.7)]
		if not prev.is_empty():
			for k in 4:
				var k2 := (k + 1) % 4
				for vv in [prev[k], sec[k2], prev[k2], prev[k], sec[k], sec[k2]]:
					st.add_vertex(vv)
		prev = sec
		if a >= SkiHill.INRUN:
			break
		a = minf(a + 1.0, SkiHill.INRUN)
	for vv in [prev[0], prev[1], prev[2], prev[0], prev[2], prev[3]]:  # the front face
		st.add_vertex(vv)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = concrete
	root.add_child(mi)
	var lip := v._box(root, Vector3(-0.12, -0.04, 0), Vector3(0.24, 0.1, 5.4), v._flat(Color(0.85, 0.08, 0.1), 0.4))
	lip.basis = Basis(Vector3.BACK, -SkiHill.ALPHA) * Basis.IDENTITY.scaled(Vector3.ONE)
	var banners := v._banner_set()
	v._quad(Vector3(0.02, -1.75, 0), Vector2(5.2, 1.9), banners[0], Basis(Vector3.UP, PI * 0.5))


# ------------------------------------------------------------------ the landing slope

func _slope() -> void:
	var steel := Pbr.material("metal", Color(0.55, 0.58, 0.62), 1.0, 0.8, 0.5)
	var pad := v._flat(Color(0.1, 0.24, 0.62), 0.55)
	var banners := v._banner_set()
	# padded fences along both sides, banners facing the slope
	var x := 3.0
	var bi := 0
	var fence_x: Array[float] = []
	while x < 196.0:
		fence_x.append(x)
		x += 5.0
	for i in fence_x.size():
		var x0 := fence_x[i]
		var x1 := x0 + 5.0
		for s in [-1.0, 1.0]:
			var p0 := Vector3(x0, 0, s * (half_width(x0) + 0.4))
			var p1 := Vector3(x1, 0, s * (half_width(x1) + 0.4))
			p0.y = terrain_y(p0.x, p0.z)
			p1.y = terrain_y(p1.x, p1.z)
			var d := p1 - p0
			var mp := (p0 + p1) * 0.5 + Vector3(0, 0.55, 0)
			var yaw := atan2(-d.z, d.x)
			var tilt := Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, atan2(d.y, Vector2(d.x, d.z).length()))
			var seg := v._box(root, mp, Vector3(d.length() + 0.05, 1.1, 0.25), pad)
			seg.basis = tilt
			var face := tilt * Basis(Vector3.UP, PI if s > 0.0 else 0.0)
			v._quad(mp + tilt * Vector3(0, 0, -0.13 * s), Vector2(d.length() - 0.1, 0.9), banners[bi % banners.size()], face)
			bi += 1
	# wind nets on masts either side of the knoll
	var net := _net_material()
	for s in [-1.0, 1.0]:
		var pts: Array[Vector3] = []
		x = -6.0
		while x <= (86.0 if s < 0.0 else 58.0):  # short on the camera side, which looks across the landing
			var p := Vector3(x, 0, s * (half_width(x) + 4.0))
			p.y = terrain_y(p.x, p.z)
			pts.append(p)
			x += 4.0
		_net(pts, 9.0, net)
		for i in range(0, pts.size(), 2):
			v._box(root, pts[i] + Vector3(0, 4.8, 0), Vector3(0.22, 9.8, 0.22), steel)
	# distance boards on posts beside the fences: blue every 10 m, the K point red, the hill size green
	for d in range(50, 141, 10):
		_distance_board(d, Color(0.95, 0.95, 0.97), Color(0.1, 0.2, 0.6), steel)
	_distance_board(int(SkiHill.K), Color(0.85, 0.1, 0.12), Color.WHITE, steel, "K")
	_distance_board(int(SkiHill.HS), Color(0.1, 0.55, 0.25), Color.WHITE, steel, "HS")
	# the judges' tower beside the landing, looking across it
	var kx := SkiHill.land_point(SkiHill.K).x
	var jt := ground(kx - 18.0, -(half_width(kx - 18.0) + 20.0))
	v._prop("judges_tower", jt + Vector3(0, -0.8, 0), -0.25)
	# the coaches' platform: three steps down the side of the knoll, coaches with their flags
	var coaches: Array[Transform3D] = []
	for k in 3:
		var cxk := 10.0 + k * 8.0
		var cz := -(half_width(cxk) + 9.0)
		var gy := terrain_y(cxk, cz)
		var top := gy + 2.2
		v._box(root, Vector3(cxk, top, cz), Vector3(7.6, 0.25, 5.5), steel)
		for px in [-3.5, 3.5]:
			for pz in [-2.5, 2.5]:
				var gg := terrain_y(cxk + px, cz + pz)
				v._box(root, Vector3(cxk + px, (top + gg) * 0.5, cz + pz), Vector3(0.18, top - gg, 0.18), steel)
		v._box(root, Vector3(cxk, top + 1.0, cz + 2.7), Vector3(7.6, 0.05, 0.05), steel)
		for i in 5:
			coaches.append(Transform3D(Basis(Vector3.UP, 0.25 * sin(i * 2.3 + k)), Vector3(cxk - 3.0 + i * 1.5, top + 0.12, cz + 1.4)))
	v._crowd(coaches, 61, 0.3)
	# TV towers: one by the knoll, the side camera beside the landing, one looking up from the arena
	v._prop("tv_tower", ground(28.0, half_width(28.0) + 10.0), PI + 0.6)
	v._prop("tv_tower", side_cam_base(), PI)
	# floodlight masts down both sides
	for fx in [18.0, 64.0, 110.0, 156.0]:
		for s in [-1.0, 1.0]:
			var p := ground(fx, s * (half_width(fx) + 15.0))
			v._prop("floodlight", p, 0.0 if s < 0.0 else PI)
			if fx > 100.0:
				_flood(p, -s, ground(fx + 18.0, -s * 6.0))
	# spectators along the lower landing slope, on the banks behind the fences
	var rng := RandomNumberGenerator.new()
	rng.seed = 9
	var fans: Array[Transform3D] = []
	for i in 1500:
		var fx := rng.randf_range(96.0, 196.0)
		var s := -1.0 if i % 2 == 0 else 1.0
		var fz := s * (half_width(fx) + rng.randf_range(1.6, 13.0))
		if s > 0.0 and absf(fx - SIDE_CAM) < 5.0:
			continue
		fans.append(Transform3D(Basis(Vector3.UP, (0.0 if s < 0.0 else PI) + rng.randf_range(-0.5, 0.5)), ground(fx, fz)))
	v._crowd(fans, 17, 1.0)
	for i in 12:
		var fx := 104.0 + i * 8.0
		for s in [-1.0, 1.0]:
			v._pole_flag(ground(fx, s * (half_width(fx) + 14.5)), i + (3 if s > 0.0 else 0), 0.0 if s < 0.0 else PI)


func _distance_board(d: int, bg: Color, fg: Color, steel: Material, extra := "") -> void:
	for s in [-1.0, 1.0]:
		var x := SkiHill.land_point(d).x
		var z: float = s * (half_width(x) + 1.3)
		var bp := ground(x, z)
		v._box(root, bp + Vector3(0, 1.3, 0), Vector3(0.1, 2.6, 0.1), steel)
		var board := v._box(root, bp + Vector3(0, 2.5, 0), Vector3(2.4, 1.1, 0.1), v._flat(bg, 0.5))
		board.rotation.y = 0.0 if s < 0.0 else PI
		var lb := Label3D.new()
		lb.text = (extra + " " if extra != "" else "") + str(d)
		lb.font = HudKit.font(true)
		lb.font_size = 110 if extra == "" else 84
		lb.pixel_size = 0.008
		lb.shaded = true
		lb.modulate = fg
		lb.outline_size = 0
		lb.position = Vector3(0, 0, 0.06)
		board.add_child(lb)


func _net_material() -> StandardMaterial3D:
	var img := Image.create(32, 32, true, Image.FORMAT_RGBA8)
	img.fill(Color(0.08, 0.2, 0.3, 0.28))
	for i in 32:
		for k in [0, 1]:
			img.set_pixel(i, k, Color(0.05, 0.12, 0.2, 0.85))
			img.set_pixel(k, i, Color(0.05, 0.12, 0.2, 0.85))
	img.generate_mipmaps()
	var m := StandardMaterial3D.new()
	m.albedo_texture = ImageTexture.create_from_image(img)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.roughness = 0.9
	m.uv1_scale = Vector3(1.0, 1.0, 1.0)
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return m


## A net hung along ground points, `h` metres tall (UVs: a mesh square every 0.25 m).
func _net(pts: Array[Vector3], h: float, mat: Material) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var u := 0.0
	for i in pts.size() - 1:
		var a := pts[i] + Vector3(0, 0.6, 0)
		var b := pts[i + 1] + Vector3(0, 0.6, 0)
		var du := a.distance_to(b) * 4.0
		var q := [[a, Vector2(u, h * 4.0)], [b, Vector2(u + du, h * 4.0)], [b + Vector3(0, h, 0), Vector2(u + du, 0)], [a + Vector3(0, h, 0), Vector2(u, 0)]]
		for k in [0, 1, 2, 0, 2, 3]:
			st.set_uv(q[k][1])
			st.set_normal(Vector3(0, 0, 1))
			st.add_vertex(q[k][0])
		u += du
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	root.add_child(mi)


## Where the side camera's tower stands beside the landing slope, and where its lens is.
func side_cam_base() -> Vector3:
	return ground(SIDE_CAM, half_width(SIDE_CAM) + 12.0)


func side_cam() -> Vector3:
	return world(side_cam_base() + Vector3(0, 9.4, -1.4))


# ------------------------------------------------------------------ the arena

func _arena() -> void:
	var pad := v._flat(Color(0.1, 0.24, 0.62), 0.55)
	var banners := v._banner_set()
	var floor_y := SkiHill.outrun_y()
	# the barrier across the end of the outrun, bowed towards the crowd
	for i in 19:
		var t := -1.0 + i * (2.0 / 18.0)
		var p := Vector3(OUTRUN_STOP + 22.0 + (1.0 - t * t) * 8.0, 0, t * 50.0)
		p.y = terrain_y(p.x, p.z) + 0.6
		var b := v._box(root, p, Vector3(0.4, 1.2, 5.6), pad)
		b.rotation.y = -atan2(-16.0 * t / 50.0, 1.0)
		v._quad(p + Basis(Vector3.UP, b.rotation.y) * Vector3(-0.21, 0, 0), Vector2(5.4, 1.0), banners[(i + 3) % banners.size()], Basis(Vector3.UP, b.rotation.y - PI * 0.5))
	# grandstands down both sides of the outrun, full
	for s in [-1.0, 1.0]:
		for k in 3:
			var cx := 214.0 + k * FrostpeakView3D.SEC
			var p := Vector3(cx, floor_y, s * (half_width(cx) + 2.0))
			p.y = terrain_y(p.x, p.z) - 0.2
			v._stand(Transform3D(Basis(Vector3.UP, PI if s > 0.0 else 0.0), p), 40 + k + (3 if s > 0 else 0))
		var e := Vector3(214.0 - FrostpeakView3D.SEC * 0.5 - 0.2, 0, s * (half_width(214.0) + 2.0))
		e.y = terrain_y(e.x, e.z) - 0.2
		v._prop("grandstand_end", e, PI if s > 0.0 else 0.0)
	# the standing crowd on the terraces behind the barrier
	var rng := RandomNumberGenerator.new()
	rng.seed = 29
	var fans: Array[Transform3D] = []
	for i in 1300:
		var t := rng.randf_range(-1.0, 1.0)
		var depth := rng.randf_range(1.5, 22.0)
		var p := Vector3(OUTRUN_STOP + 22.0 + (1.0 - t * t) * 8.0 + depth, 0, t * 54.0)
		p.y = terrain_y(p.x, p.z) + depth * 0.18
		fans.append(Transform3D(Basis(Vector3.UP, -PI * 0.5 + rng.randf_range(-0.5, 0.5)), p))
	v._crowd(fans, 31, 1.0)
	# terraces for them: steps of packed snow rising away from the barrier
	var terrace := ShaderMaterial.new()
	terrace.shader = v._snow_mat.shader
	for k in 6:
		var dx := 4.0 + k * 3.6
		var tb := v._box(root, Vector3(OUTRUN_STOP + 30.0 + dx, floor_y + (dx + 2.0) * 0.18 * 0.5, 0), Vector3(3.8, (dx + 2.0) * 0.18, 120.0), terrace)
		tb.position.y = terrain_y(OUTRUN_STOP + 30.0 + dx, 0) + (dx) * 0.09 - 0.1
	for i in 10:
		v._pole_flag(ground(OUTRUN_STOP + 26.0, -45.0 + i * 10.0), i + 1, -PI * 0.5)
	# the big screen, turned towards the hill and the stands
	v._scoreboard(ground(OUTRUN_STOP + 6.0, -(half_width(OUTRUN_STOP) + 18.0)), -PI * 0.5 + 0.7, "HS 134")
	v._scoreboard(ground(OUTRUN_STOP + 6.0, half_width(OUTRUN_STOP) + 18.0), -PI * 0.5 - 0.7, "HS 134")
	# hospitality tents and parked snow-cats round the arena
	for i in 7:
		var tz := -95.0 + i * 30.0
		if absf(tz) < 30.0:
			continue
		v._prop("tent", ground(OUTRUN_STOP + 58.0 + (i % 2) * 9.0, tz), -PI * 0.5)
	for s in [-1.0, 1.0]:
		v._prop("snowcat", ground(186.0, s * (half_width(186.0) + 7.0)), PI * 0.5 + s * 0.4)
	# TV tower in the arena, looking up the hill
	v._prop("tv_tower", ground(OUTRUN_STOP + 16.0, 30.0), PI * 0.5)
	# floodlights over the arena
	for s in [-1.0, 1.0]:
		var fp := ground(OUTRUN_STOP - 10.0, s * (half_width(OUTRUN_STOP) + 34.0))
		v._prop("floodlight", fp, 0.0 if s < 0.0 else PI)
		_flood(fp, -s, ground(OUTRUN_STOP - 20.0, -s * 8.0))


## A floodlight's beam: a warm pool on the snow where its mast aims (no shadows: the sun draws those). `face` is the
## side the lamps face (+1 towards +z).
func _flood(mast: Vector3, face: float, aim: Vector3) -> void:
	var sl := SpotLight3D.new()
	sl.position = mast + Vector3(0, 19.9, face * 0.35)
	root.add_child(sl)
	sl.look_at(xf * aim, Vector3.UP)
	sl.light_color = Color(1.0, 0.9, 0.74)
	sl.light_energy = 22.0
	sl.light_specular = 0.3
	sl.spot_range = 150.0
	sl.spot_angle = 30.0
	sl.spot_angle_attenuation = 1.6
	sl.shadow_enabled = false
	sl.distance_fade_enabled = true  # far off the pools are lost in the daylight anyway
	sl.distance_fade_begin = 500.0
	sl.distance_fade_length = 100.0


# ------------------------------------------------------------------ the woods

func _trees() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 8
	var trees: Array[Transform3D] = []
	var rocks: Array[Transform3D] = []
	var far: Array[Transform3D] = []
	var near: Array[Transform3D] = []  ## the woods lining the hill: these cast shadows on the snow
	var n := 0
	while trees.size() + near.size() + far.size() < 5000 and n < 24000:
		n += 1
		var tx := rng.randf_range(X0 + 20.0, X1 - 20.0)
		var tz := rng.randf_range(-Z1 + 10.0, Z1 - 10.0) * (0.35 if n % 2 == 0 else 1.0)  # thickest near the hill
		var hw := half_width(tx)
		if absf(tz) < hw + (14.0 if tx < 0.0 else (22.0 if tx < 200.0 else 60.0)):
			continue
		if tx > 170.0 and tx < OUTRUN_STOP + 90.0 and absf(tz) < 125.0:  # the arena
			continue
		if tx < -60.0 and tx > -130.0 and absf(tz) < 30.0:  # round the tower
			continue
		if _noise.get_noise_2d(tx * 0.5, tz * 0.5) < -0.4:  # clearings
			continue
		var p := ground(tx, tz)
		if absf(tz) > hw + 110.0 or tx < -180.0 or tx > 400.0:
			far.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.5, 3.0)), p - Vector3(0, 0.3, 0)))
			continue
		var t := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.5, 3.0)), p - Vector3(0, 0.3, 0))
		(near if absf(tz) < hw + 70.0 and tx > -140.0 and tx < 330.0 else trees).append(t)
		if (trees.size() + near.size()) % 13 == 0:
			rocks.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.8, 2.2)), p + Vector3(3.0, -0.3, 0)))
	v._into = root
	v._forest(trees, 8, false)
	v._forest(near, 9, true)
	v._forest_far(far)
	v._multi("boulder", rocks)
