class_name FrostpeakBobVenue
extends RefCounted
## The bobsled run in the picture, built from the shared line (BobTrack) so what you see is what the rules use: a
## wooded spur running down from the mountains at the north of the valley (its own finer ground, the run's bed cut
## into it and banked up where the run sits proud), the ice channel with its tall banks in the curves and the white
## coping along its walls, the start (a roofed start ramp, the start house, the first timing eye), lamps along the
## run, boards naming the curves, crowds behind snow fences at the horseshoe, the labyrinth and the finish, the
## timing eyes, and the finish area at the foot (the arch over the run, a grandstand along the run-out, the
## scoreboard, the nations' flags). The spur is dressed with conifers, kept clear of the run.

const X0 := -60.0  ## the venue's own ground (world x, z)
const X1 := 300.0
const Z0 := -1235.0
const Z1 := -395.0
const CELL := 3.0
const GRID := 4.0  ## the run's bed: a grid of what the ground under and beside the run is cut or built up to
const PAD := 12.0  ## the start ramp's flat pad behind the start block
const RIDGE_A := Vector2(110.0, -1175.0)  ## the spur: its crest from the mountains' foot down to the valley floor
const RIDGE_B := Vector2(115.0, -455.0)
const RIDGE_TOP := 120.0
const COPE := 0.35  ## the coping along the top of the walls
const STAND_S := 986.0  ## the finish grandstand, beside the run-out

static var _gw := PackedFloat32Array()  ## per grid point: the bed's weights, weighted heights, how much of it, distance
static var _gy := PackedFloat32Array()
static var _gc := PackedFloat32Array()
static var _gd := PackedFloat32Array()
static var _gnx := 0
static var _gnz := 0

var v: FrostpeakView3D
var valley: FrostpeakValley
var root: Node3D
var ice_mat: ShaderMaterial


static func covers(p: Vector3, margin := 0.0) -> bool:
	return p.x > X0 - margin and p.x < X1 + margin and p.z > Z0 - margin and p.z < Z1 + margin


## 0 at the edge of the venue's ground, 1 once well inside it (where the valley's own ground sinks out of sight).
static func inside(p: Vector3) -> float:
	var d := minf(minf(p.x - X0, X1 - p.x), minf(p.z - Z0, Z1 - p.z))
	return smoothstep(0.0, 12.0, d)


## The spur the run comes down: a broad crest from the mountains' foot to the valley floor, falling away at its sides.
static func ridge(x: float, z: float) -> float:
	var ab := RIDGE_B - RIDGE_A
	var l2 := ab.length_squared()
	var q := Vector2(x, z) - RIDGE_A
	var t := q.dot(ab) / l2
	var d := absf(q.x * ab.y - q.y * ab.x) / sqrt(l2)
	if d > 230.0 or t < -0.1 or t > 1.0:
		return 0.0
	return RIDGE_TOP * pow(1.0 - clampf(t, 0.0, 1.0), 1.25) * (1.0 - smoothstep(80.0, 230.0, d)) * smoothstep(-0.1, 0.02, t)


## The run's centre line, the start pad behind the block included (s < 0).
static func centre(s: float) -> Vector3:
	if s >= 0.0:
		return BobTrack.point(s)
	var d := BobTrack.dir(0.0)
	return BobTrack.point(0.0) + Vector3(d.x, 0.0, d.y) * s


static func _build_grid() -> void:
	if not _gw.is_empty():
		return
	_gnx = int((X1 - X0) / GRID) + 1
	_gnz = int((Z1 - Z0) / GRID) + 1
	var n := _gnx * _gnz
	_gw.resize(n)
	_gy.resize(n)
	_gc.resize(n)
	_gd.resize(n)
	_gw.fill(0.0)
	_gy.fill(0.0)
	_gc.fill(0.0)
	_gd.fill(999.0)
	var r := 40.0
	var cells := int(r / GRID) + 1
	var s := -PAD - 4.0
	while s <= BobTrack.length() + 4.0:
		var p := centre(minf(s, BobTrack.length()))
		if s > BobTrack.length():
			var d := BobTrack.dir(BobTrack.length())
			p += Vector3(d.x, 0.0, d.y) * (s - BobTrack.length())
		var ci := int(round((p.x - X0) / GRID))
		var ck := int(round((p.z - Z0) / GRID))
		for i in range(maxi(0, ci - cells), mini(_gnx, ci + cells + 1)):
			for k in range(maxi(0, ck - cells), mini(_gnz, ck + cells + 1)):
				var dd := Vector2(X0 + i * GRID - p.x, Z0 + k * GRID - p.z).length()
				if dd > r:
					continue
				var j := i * _gnz + k
				var wk := exp(-(dd * dd) / 100.0)
				_gw[j] += wk
				_gy[j] += wk * p.y
				_gc[j] = maxf(_gc[j], 1.0 - smoothstep(6.0, 34.0, dd))
				_gd[j] = minf(_gd[j], dd)
		s += 1.0


## The bed's grid at (x, z), bilinear: weights, weighted heights, how much of the bed, distance to the run.
static func _grid(x: float, z: float) -> Vector4:
	_build_grid()
	var fx := clampf((x - X0) / GRID, 0.0, _gnx - 1.001)
	var fz := clampf((z - Z0) / GRID, 0.0, _gnz - 1.001)
	var i := int(fx)
	var k := int(fz)
	var u := fx - i
	var t := fz - k
	var out := Vector4.ZERO
	for c in [[0, 0, (1.0 - u) * (1.0 - t)], [1, 0, u * (1.0 - t)], [0, 1, (1.0 - u) * t], [1, 1, u * t]]:
		var j: int = (i + c[0]) * _gnz + k + c[1]
		var wt: float = c[2]
		out += Vector4(_gw[j], _gy[j], _gc[j], _gd[j]) * wt
	return out


## The ground with the spur and the run's bed: `h` is the valley's own height at (x, z).
static func adjust(x: float, z: float, h: float) -> float:
	var base := maxf(h, ridge(x, z))
	if not covers(Vector3(x, 0.0, z)):
		return base
	var g := _grid(x, z)
	if g.z <= 0.0 or g.x < 0.0001:
		return base
	return lerpf(base, g.y / g.x - 0.35, g.z)


## How far a ground point is from the run (metres, near enough), for the woods.
static func near(x: float, z: float) -> float:
	if not covers(Vector3(x, 0.0, z)):
		return 999.0
	return _grid(x, z).w


func _init(view: FrostpeakView3D, vl: FrostpeakValley) -> void:
	v = view
	valley = vl


func ground(x: float, z: float) -> Vector3:
	return Vector3(x, valley.height(x, z), z)


func build() -> void:
	root = Node3D.new()
	root.name = "Bobsled"
	v.add_child(root)
	v._into = root
	_terrain()
	_channel()
	_start()
	_finish()
	_dressing()
	_woods()
	v._into = v


# ------------------------------------------------------------------ the ground

func _terrain() -> void:
	var nx := int((X1 - X0) / CELL)
	var nz := int((Z1 - Z0) / CELL)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in nx + 1:
		for k in nz + 1:
			var x := X0 + i * CELL
			var z := Z0 + k * CELL
			st.add_vertex(Vector3(x, valley.height(x, z) - 0.02, z))
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


# ------------------------------------------------------------------ the channel

## The channel's cross-section at s, as [lateral points (x across, y up, u along the surface), floor weight], for
## the ice from the top of the left wall to the top of the right; `side` walls use BobTrack's shape.
func _ice_row(s: float) -> Array:
	var sc := maxf(s, 0.0)
	var fh := BobTrack.floor_half(sc)
	var out := []
	var na := 8
	for side in [-1.0, 1.0]:
		var rb := BobTrack.wall_r(sc, side)
		var pts := []
		for i in na + 1:
			var al := PI * 0.5 * (1.0 - float(i) / na)
			pts.append([side * (fh + rb * sin(al)), rb * (1.0 - cos(al)), side * (fh + rb * al), 0.0 if i < na else 1.0])
		if side < 0.0:
			out.append_array(pts)
			out.append([0.0, 0.0, 0.0, 1.0])
		else:
			pts.reverse()
			out.append_array(pts)
	return out


## The coping and the outer face down to the ground, one side: from the top of the ice outwards and down.
func _shell_row(s: float, side: float, c: Vector3, rt: Vector3) -> Array:
	var sc := maxf(s, 0.0)
	var rb := BobTrack.wall_r(sc, side)
	var fh := BobTrack.floor_half(sc)
	var lip := 0.18 + 0.1 * (rb - BobTrack.WALL / (PI * 0.5))
	var top := rb + lip
	var xo := fh + rb + COPE
	var gp := c + rt * (side * (xo + 0.2))
	var bottom := minf(valley.height(gp.x, gp.z) - c.y - 0.4, -0.4)
	var pts := [[fh + rb, rb], [fh + rb, top], [xo - 0.06, top + 0.05], [xo, top - 0.02], [xo, bottom]]
	var out := []
	for p in pts:
		out.append(c + rt * (side * p[0]) + Vector3(0, p[1], 0))
	if side < 0.0:
		out.reverse()
	return out


func _strip(st: SurfaceTool, a: Array, b: Array) -> void:
	for k in a.size() - 1:
		var q: Array = [a[k], b[k], b[k + 1], a[k + 1]]
		for idx in [0, 1, 2, 0, 2, 3]:
			st.add_vertex(q[idx])


func _channel() -> void:
	ice_mat = ShaderMaterial.new()
	ice_mat.shader = load(FrostpeakView3D.SH + "bob_ice.gdshader")
	var ice := SurfaceTool.new()
	ice.begin(Mesh.PRIMITIVE_TRIANGLES)
	var shell := SurfaceTool.new()
	shell.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rows := []
	var shells := [[], []]
	var s := -PAD
	var end := BobTrack.length()
	while s <= end + 0.01:
		var c := centre(s)
		var rt := BobTrack.right(maxf(s, 0.0))
		var row := []
		for p in _ice_row(s):
			row.append([c + rt * p[0] + Vector3(0, p[1], 0), Vector2(p[2], s), p[3]])
		rows.append(row)
		shells[0].append(_shell_row(s, -1.0, c, rt))
		shells[1].append(_shell_row(s, 1.0, c, rt))
		s += 1.0 if s < end - 1.0 or s >= end else end - s
	for i in rows.size() - 1:
		var a: Array = rows[i]
		var b: Array = rows[i + 1]
		for k in a.size() - 1:
			var q: Array = [a[k], b[k], b[k + 1], a[k + 1]]
			for n in [0, 1, 2, 0, 2, 3]:
				ice.set_uv(q[n][1])
				ice.set_color(Color(q[n][2], 0, 0))
				ice.add_vertex(q[n][0])
		for sd in 2:
			_strip(shell, shells[sd][i], shells[sd][i + 1])
	# the run-out's end: a padded wall across the channel
	ice.generate_normals()
	shell.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = ice.commit()
	mi.material_override = ice_mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF  # (the walls' coping and outer faces cast the banks' shadows)
	root.add_child(mi)
	var sm := MeshInstance3D.new()
	sm.mesh = shell.commit()
	sm.material_override = _white()
	root.add_child(sm)
	var e := BobTrack.length()
	var pad := v._box(root, centre(e) + Vector3(0, 0.9, 0), Vector3(4.2, 1.8, 1.0), v._flat(Color(0.1, 0.24, 0.62), 0.55))
	var d := BobTrack.dir(e)
	pad.basis = Basis(Vector3.UP, -atan2(d.y, d.x) + PI * 0.5)
	var back := v._box(root, centre(-PAD) + Vector3(0, 0.5, 0), Vector3(3.8, 1.0, 0.4), _white())
	back.basis = Basis(Vector3.UP, -atan2(BobTrack.dir(0.0).y, BobTrack.dir(0.0).x) + PI * 0.5)


func _white() -> Material:
	return v._swaps()["stand_concrete"]


## A world transform on the run at s, `off` metres to the right of the centre line and `up` above the floor, facing
## along the run (+z forward, like the models).
func frame(s: float, off := 0.0, up := 0.0) -> Transform3D:
	var d := BobTrack.dir(maxf(s, 0.0))
	var fwd := Vector3(d.x, 0.0, d.y)
	var rt := BobTrack.right(maxf(s, 0.0))
	return Transform3D(Basis(-rt, Vector3.UP, fwd), centre(s) + rt * off + Vector3(0, up, 0))


## How far out from the centre the outside of the channel's wall is, on a side (+1 right).
func outer(s: float, side: float) -> float:
	var sc := maxf(s, 0.0)
	return BobTrack.floor_half(sc) + BobTrack.wall_r(sc, side) + COPE


## The top of the channel's wall on a side at s (world), and its height above the floor.
func wall_top(s: float, side: float) -> Vector3:
	var sc := maxf(s, 0.0)
	var rb := BobTrack.wall_r(sc, side)
	return centre(s) + BobTrack.right(sc) * (side * (BobTrack.floor_half(sc) + rb + COPE * 0.5)) + Vector3(0, rb + 0.2, 0)


## Where the trackside TV cameras stand (the woods and the crowds keep clear of them): up on the inside of the
## horseshoe, on the inside between the labyrinth's second and third bends, on the TV tower by the last straight.
func tv_spot(name: String) -> Vector3:
	var cs := BobTrack.curves()
	match name:
		"horseshoe":
			var c: Array = cs[3]
			var mid: float = (c[0] + c[1]) * 0.5
			var inside := signf(c[2])
			return frame(mid, inside * (outer(mid, inside) + 7.0)).origin + Vector3(0, 9.0, 0)
		"labyrinth":
			var c: Array = cs[6]
			var at: float = c[1] - 4.0
			var inside := signf(c[2])
			return frame(at, inside * (outer(at, inside) + 6.0)).origin + Vector3(0, 9.0, 0)
		"finish":
			var tw := frame(BobTrack.FINISH - 30.0, 14.0)  # on the TV tower beside the last straight
			return tw.origin + tw.basis.x * 1.4 + Vector3(0, 6.8, 0)
	return Vector3.ZERO


# ------------------------------------------------------------------ the start

func _start() -> void:
	var wood := Pbr.local("planks", Color(0.7, 0.5, 0.35), 0.8)
	var roof: Material = v._swaps()["roof"]
	var steel := Pbr.material("metal", Color(0.3, 0.33, 0.36), 0.7, 0.8, 0.5)
	# the roof over the start ramp: timber posts either side, a shallow pitched roof with snow on it
	var s := -PAD + 1.0
	while s <= 22.0:
		for side in [-1.0, 1.0]:
			var f := frame(s, side * (outer(s, side) + 0.4))
			f.origin.y = maxf(f.origin.y, valley.height(f.origin.x, f.origin.z))
			var post := v._box(root, f.origin + Vector3(0, 2.1, 0), Vector3(0.22, 4.2, 0.22), wood)
			post.basis = f.basis
		s += 5.5
	for side in [-1.0, 1.0]:
		var mid := frame(5.0, side * 1.25, 4.45)
		var r := v._box(root, mid.origin, Vector3(3.0, 0.16, PAD + 24.0), roof)
		r.basis = mid.basis * Basis(Vector3.FORWARD, side * 0.2)
		var snow := v._box(root, mid.origin + Vector3(0, 0.14, 0), Vector3(2.9, 0.1, PAD + 23.6), v._snow_mat)
		snow.basis = r.basis
	var sign := v._banner_mat("START", Color.WHITE, Color(0.75, 0.1, 0.15), Color.WHITE)
	var sf := frame(20.5, 0.0, 3.6)
	v._quad(sf.origin, Vector2(3.4, 0.8), sign, sf.basis * Basis(Vector3.UP, PI))
	# the start house beside the pad, the coaches' stand
	var hf := frame(-6.0, -9.5)
	var rt0 := BobTrack.right(0.0)
	v._prop("start_house", ground(hf.origin.x, hf.origin.z), atan2(rt0.x, rt0.z))  # its glazed front to the ramp
	# the timing eyes at the start line
	_eye(BobTrack.START_LINE, steel)
	for i in 3:
		v._pole_flag(ground(hf.origin.x + 4.0 * i, hf.origin.z + 10.0), i + 2, PI)
	# a few people round the start: coaches, officials, the other crews
	var rng := RandomNumberGenerator.new()
	rng.seed = 131
	var fans: Array[Transform3D] = []
	for i in 26:
		var fs := rng.randf_range(-6.0, 30.0)
		var side := -1.0 if i % 3 else 1.0
		var f := frame(fs, side * (outer(fs, side) + rng.randf_range(1.5, 4.0)))
		var p := ground(f.origin.x, f.origin.z)
		fans.append(Transform3D(Basis(Vector3.UP, atan2(side * f.basis.x.x, side * f.basis.x.z) + rng.randf_range(-0.6, 0.6)), p))
	v._crowd(fans, 133)


## A timing eye across the run at s: a post each side with a red eye, and a strip on the ice.
func _eye(s: float, steel: Material) -> void:
	for side in [-1.0, 1.0]:
		var f := frame(s, side * (outer(s, side) + 0.2))
		var top := wall_top(s, side)
		var base := ground(f.origin.x, f.origin.z)
		var h := maxf(top.y + 0.6 - base.y, 0.9)
		var post := v._box(root, base + Vector3(0, h * 0.5, 0), Vector3(0.08, h, 0.08), steel)
		post.basis = f.basis
		v._box(root, base + Vector3(0, h - 0.05, 0), Vector3(0.14, 0.12, 0.14), v._flat(Color(1.0, 0.15, 0.1), 0.3, 3.0))


# ------------------------------------------------------------------ the finish

func _finish() -> void:
	var fs := BobTrack.FINISH
	var arch := v._scene("finish_arch")
	var d := BobTrack.dir(fs)
	var across := BobTrack.right(fs)
	arch.transform = Transform3D(Basis(across, Vector3.UP, across.cross(Vector3.UP)), centre(fs) + Vector3(0, -0.1, 0))
	root.add_child(arch)
	var line := v._box(root, centre(fs) + Vector3(0, 0.03, 0), Vector3(0.25, 0.02, BobTrack.FLOOR * 2.0 + 0.2), v._flat(Color(0.85, 0.08, 0.1), 0.4))
	line.basis = Basis(Vector3.UP, -atan2(d.y, d.x))
	var steel := Pbr.material("metal", Color(0.3, 0.33, 0.36), 0.7, 0.8, 0.5)
	_eye(fs, steel)
	for sp in BobTrack.SPLITS:
		_eye(sp, steel)
	# the grandstand along the run-out on its right, facing it, and people along the fence on the left
	var sf := frame(STAND_S, 16.0)
	var sp := ground(sf.origin.x, sf.origin.z)
	var face := sf.basis.x  # towards the run
	var yaw := atan2(face.x, face.z)
	for k in 2:
		var along := sf.basis.z * ((k - 0.5) * FrostpeakView3D.SEC)
		var p := sp + along
		p.y = valley.height(p.x, p.z) - 0.2
		v._stand(Transform3D(Basis(Vector3.UP, yaw), p), 140 + k, 0.8)
	for e in [-1.0, 1.0]:
		var p: Vector3 = sp + sf.basis.z * (e * (FrostpeakView3D.SEC + 0.2))
		v._prop("grandstand_end", ground(p.x, p.z) + Vector3(0, -0.2, 0), yaw)
	# the scoreboard across from the stand, the nations' flags, the TV tower, tents
	var bf := frame(STAND_S + 6.0, -22.0)
	v._scoreboard(ground(bf.origin.x, bf.origin.z), atan2(-face.x, -face.z) + 0.25, "BOBSLED")
	for i in 6:
		var ff := frame(fs - 20.0 + i * 7.0, -9.5)
		v._pole_flag(ground(ff.origin.x, ff.origin.z), i, atan2(-face.x, -face.z) + PI * 0.5)
	var tf := frame(fs - 30.0, 14.0)
	v._prop("tv_tower", ground(tf.origin.x, tf.origin.z), yaw)
	for i in 3:
		var tn := frame(STAND_S + 34.0 + i * 12.0, 18.0)
		v._prop("tent", ground(tn.origin.x, tn.origin.z), yaw)
	var rng := RandomNumberGenerator.new()
	rng.seed = 151
	var fans: Array[Transform3D] = []
	for i in 180:
		var s := rng.randf_range(fs - 95.0, fs + 30.0)
		var side := -1.0 if i % 4 else 1.0
		if side > 0.0 and s > STAND_S - 30.0:
			continue
		var f := frame(s, side * (outer(s, side) + rng.randf_range(2.8, 5.5)))
		var p := ground(f.origin.x, f.origin.z)
		fans.append(Transform3D(Basis(Vector3.UP, atan2(side * f.basis.x.x, side * f.basis.x.z) + rng.randf_range(-0.5, 0.5)), p))
	v._crowd(fans, 153)
	_fence(fs - 100.0, fs + 32.0, -1.0, 2.3)
	_fence(fs - 100.0, STAND_S - 32.0, 1.0, 2.3)


## A red snow fence along the run between s0 and s1 on a side, `off` metres beyond the channel's wall.
func _fence(s0: float, s1: float, side: float, off: float) -> void:
	var xs: Array[Transform3D] = []
	var s := s0
	while s < s1:
		var f := frame(s, side * (outer(s, side) + off))
		var p := ground(f.origin.x, f.origin.z)
		xs.append(Transform3D(f.basis.scaled(Vector3(0.05, 1.1, 2.0)), p + Vector3(0, 0.55, 0)))
		s += 2.0
	if xs.is_empty():
		return
	var mesh := BoxMesh.new()
	mesh.material = v._flat(Color(0.95, 0.35, 0.08), 0.6)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xs.size()
	for i in xs.size():
		mm.set_instance_transform(i, xs[i])
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	root.add_child(mi)


# ------------------------------------------------------------------ along the run

func _dressing() -> void:
	# lamps along the run, on alternate sides, their heads leaning over the ice
	var poles: Array[Transform3D] = []
	var heads: Array[Transform3D] = []
	var s := 8.0
	var side := 1.0
	while s < BobTrack.length() - 5.0:
		var top := wall_top(s, side)
		var f := frame(s, side * (outer(s, side) + 0.5))
		var base := f.origin
		base.y = maxf(valley.height(base.x, base.z), top.y - 0.4)
		var h := top.y - base.y + 3.4
		poles.append(Transform3D(Basis.IDENTITY.scaled(Vector3(0.07, h, 0.07)), base + Vector3(0, h * 0.5, 0)))
		heads.append(Transform3D(f.basis.scaled(Vector3(0.9, 0.12, 0.3)), base + Vector3(0, h, 0) + f.basis.x * side * 0.4))
		s += 22.0
		side = -side
	var pm := CylinderMesh.new()
	pm.top_radius = 1.0
	pm.bottom_radius = 1.0
	pm.height = 1.0
	pm.radial_segments = 6
	pm.material = v._flat(Color(0.25, 0.27, 0.3), 0.5)
	var hm := BoxMesh.new()
	hm.material = v._flat(Color(1.0, 0.95, 0.85), 0.3, 2.5)
	for pair in [[pm, poles], [hm, heads]]:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = pair[0]
		var xs: Array = pair[1]
		mm.instance_count = xs.size()
		for i in xs.size():
			mm.set_instance_transform(i, xs[i])
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = mm
		root.add_child(mi)
	# a board at each curve's entry: its number and its name, on the outside
	var cs := BobTrack.curves()
	for i in cs.size():
		var c: Array = cs[i]
		var out := -signf(c[2])
		var at: float = c[0] - 4.0
		var f := frame(at, out * (outer(at, out) + 1.6))
		var p := ground(f.origin.x, f.origin.z)
		var m := v._banner_mat("%d  %s" % [i + 1, c[4]], Color(0.08, 0.12, 0.3), Color(0.97, 0.97, 0.98), Color(0.1, 0.25, 0.6))
		var b := Basis(Vector3.UP, atan2(-f.basis.z.x, -f.basis.z.z))  # facing up the run, to the sled coming
		v._quad(p + Vector3(0, 2.3, 0), Vector2(3.6, 0.55), m, b)
		for e in [-1.6, 1.6]:
			v._box(root, p + b * Vector3(e, 1.1, -0.02), Vector3(0.06, 2.2, 0.06), v._flat(Color(0.25, 0.27, 0.3), 0.5))
	# crowds behind snow fences on the outside of the horseshoe and along the labyrinth, banners on the walls there
	var rng := RandomNumberGenerator.new()
	rng.seed = 161
	var fans: Array[Transform3D] = []
	var banners := v._banner_set()
	var bi := 0
	var cams: Array[Vector3] = [tv_spot("horseshoe"), tv_spot("labyrinth")]
	for spot in [[3, 1.0, 190], [5, 1.0, 110], [6, 1.0, 90], [7, 1.0, 90], [1, 1.0, 60], [8, 1.0, 80]]:
		var c: Array = cs[spot[0]]
		var out := -signf(c[2])
		var s0: float = c[0] - 10.0
		var s1: float = c[1] + 10.0
		_fence(s0, s1, out, 3.0)
		for i in int(spot[2]):
			var fs := rng.randf_range(s0, s1)
			var f := frame(fs, out * (outer(fs, out) + rng.randf_range(4.0, 9.0)))
			var p := ground(f.origin.x, f.origin.z)
			if Vector2(p.x - cams[0].x, p.z - cams[0].z).length() < 7.0 or Vector2(p.x - cams[1].x, p.z - cams[1].z).length() < 7.0:
				continue
			fans.append(Transform3D(Basis(Vector3.UP, atan2(out * f.basis.x.x, out * f.basis.x.z) + rng.randf_range(-0.5, 0.5)), p))
		var bs := s0 + 4.0
		while bs < s1 - 4.0:  # sponsors' boards along the outside of the bank, facing the crowd
			var f := frame(bs, out * (outer(bs, out) + 0.02))
			var top := wall_top(bs, out)
			var yw := atan2(out * f.basis.x.x, out * f.basis.x.z)
			v._quad(Vector3(f.origin.x, top.y - 0.9, f.origin.z) - f.basis.x * out * 0.0, Vector2(3.6, 0.8), banners[bi % banners.size()],
				Basis(Vector3.UP, yw + PI))
			bi += 1
			bs += 4.0
	v._crowd(fans, 163)


# ------------------------------------------------------------------ the woods

func _woods() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 171
	var near_t: Array[Transform3D] = []  ## by the run: their shadows fall across it
	var mid_t: Array[Transform3D] = []
	var far_t: Array[Transform3D] = []
	var fin := centre(BobTrack.FINISH)
	var spots: Array[Vector3] = [tv_spot("horseshoe"), tv_spot("labyrinth")]
	for i in 9000:
		var p := Vector3(rng.randf_range(X0 + 4.0, X1 - 4.0), 0.0, rng.randf_range(Z0 + 4.0, Z1 - 4.0))
		var d := near(p.x, p.z)
		if d < 9.0 + rng.randf() * 6.0:
			continue
		if Vector2(p.x - fin.x, p.z - fin.z).length() < 80.0 and p.z > fin.z - 40.0:  # the finish area
			continue
		var clear := true
		for sp in spots:  # the TV cameras see out
			if Vector2(p.x - sp.x, p.z - sp.z).length() < 16.0:
				clear = false
		if not clear:
			continue
		p.y = valley.height(p.x, p.z)
		if p.y < 1.0 and d > 60.0 and rng.randf() < 0.7:  # thinner on the valley floor
			continue
		var xf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(1.5, 2.9)), p - Vector3(0, 0.3, 0))
		if d < 45.0:
			if rng.randf() < 0.6:
				(near_t if d < 24.0 else mid_t).append(xf)
		else:
			far_t.append(xf)
	v._forest(near_t, 173, true, 420.0)
	v._forest(mid_t, 175, false, 420.0)
	v._forest_far(far_t)
