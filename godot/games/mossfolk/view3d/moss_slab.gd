class_name MossSlab
extends Node3D
## The level as a solid block of rock: a front face (one quad; the shader cuts the air away from the pixel mask) and
## the carved walls behind it, extruded from the mask's outline (marching squares on the pixel grid) back to the
## slab's rear. The walls are built in chunks of 32 x 32 cells and only the chunks the mosslings dig into are
## rebuilt. Pixel (x, y) is world (x * 0.1, (h - y) * 0.1); the front face sits at z = FRONT, the rear at -DEPTH.
## Grass tufts (a MultiMesh per chunk) cover the level's original upper faces, not the floors dug out later.

const PX := 0.1
const FRONT := 0.35
const DEPTH := 2.4
const BEVEL := 0.1
const CHUNK := 16
## marching squares: corner bits TL 8, TR 4, BR 2, BL 1; edges 0 top, 1 right, 2 bottom, 3 left. The two saddle
## cases keep the solid joined, so builders' stairs stay one piece.
const CASES := [[], [3, 2], [2, 1], [3, 1], [0, 1], [3, 0, 1, 2], [0, 2], [3, 0], [3, 0], [0, 2], [0, 1, 3, 2],
	[0, 1], [3, 1], [1, 2], [3, 2], []]

var w := 0
var h := 0
var terrain: PackedByteArray
var wall_mat: ShaderMaterial
var original: PackedByteArray   ## the terrain as the level began (grass grows only on its upper faces)
var grass_mat: ShaderMaterial
var _grass_mesh: ArrayMesh
var _g := PackedByteArray()   ## solid (1) or air (0), padded with a ring of air: (w + 2) x (h + 2)
var _gw := 0
var _dirty := {}    ## chunks waiting to be rebuilt (a few a frame)
var _chunks := {}   ## Vector2i -> MeshInstance3D
var _grass := {}    ## Vector2i -> MultiMeshInstance3D


func setup(level_w: int, level_h: int, t: PackedByteArray, orig: PackedByteArray, cap_mat: ShaderMaterial,
		walls: ShaderMaterial, grass: ShaderMaterial) -> void:
	w = level_w
	h = level_h
	terrain = t
	original = orig
	wall_mat = walls
	grass_mat = grass
	_grass_mesh = _tuft()
	_gw = w + 2
	_g.resize(_gw * (h + 2))
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(w * PX, h * PX)
	q.mesh = qm
	q.material_override = cap_mat
	q.position = Vector3(w * PX * 0.5, h * PX * 0.5, FRONT)
	add_child(q)
	rebuild(Rect2i(0, 0, w, h), true)


## Marks the chunks touching pixels r for rebuilding (the cells round a pixel start one cell up and left); `now`
## builds them at once (the whole level at the start), otherwise a few go each frame.
func rebuild(r: Rect2i, now := false) -> void:
	for y in range(maxi(0, r.position.y), mini(h, r.end.y)):
		var row := (y + 1) * _gw + 1
		for x in range(maxi(0, r.position.x), mini(w, r.end.x)):
			_g[row + x] = 1 if terrain[y * w + x] != 0 else 0
	var c0 := Vector2i(floori(float(r.position.x) / CHUNK), floori(float(r.position.y) / CHUNK))
	var c1 := Vector2i(floori(float(r.end.x) / CHUNK), floori(float(r.end.y) / CHUNK))
	for cy in range(c0.y, c1.y + 1):
		for cx in range(c0.x, c1.x + 1):
			if now:
				_build(Vector2i(cx, cy))
			else:
				_dirty[Vector2i(cx, cy)] = true


func _process(_delta: float) -> void:
	var n := 0
	for k in _dirty.keys():
		_dirty.erase(k)
		_build(k)
		n += 1
		if n >= 3:
			break


## Cells (i, j) join the centres of pixels (i, j) .. (i + 1, j + 1); chunk k holds cells k*CHUNK - 1 ..
func _build(k: Vector2i) -> void:
	var i0 := k.x * CHUNK - 1
	var j0 := k.y * CHUNK - 1
	if i0 >= w or j0 >= h or i0 + CHUNK < -1 or j0 + CHUNK < -1:
		return
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var tans := PackedFloat32Array()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	var zf := FRONT
	var zm := FRONT - BEVEL
	var zb := -DEPTH
	var tufts: Array[Transform3D] = []
	var g := _g
	var gw := _gw
	for j in range(j0, mini(j0 + CHUNK, h)):
		var top := (j + 1) * gw + 1
		for i in range(i0, mini(i0 + CHUNK, w)):
			var a := top + i
			var tl := g[a]
			var tr := g[a + 1]
			var bl := g[a + gw]
			var br := g[a + gw + 1]
			var cs := tl * 8 + tr * 4 + br * 2 + bl
			if cs == 0 or cs == 15:
				continue
			var segs: Array = CASES[cs]
			for s in range(0, segs.size(), 2):
				var p := _edge(i, j, segs[s])
				var q := _edge(i, j, segs[s + 1])
				# outward: towards the nearest air corner
				var mid := (p + q) * 0.5
				var air := Vector2.ZERO
				var best := 99.0
				for c in 4:
					if (tl if c == 0 else (tr if c == 1 else (br if c == 2 else bl))) != 0:
						continue
					var cp := Vector2(i + 0.5 + float(c == 1 or c == 2), j + 0.5 + float(c >= 2))
					var dd := cp.distance_squared_to(mid)
					if dd < best:
						best = dd
						air = cp
				var d := q - p
				var n := Vector2(d.y, -d.x).normalized()     # pixel space, y down
				if n.dot(air - mid) < 0.0:
					n = -n
					var t := p
					p = q
					q = t
				# to world (y up): the wall runs p -> q with the air on its right, seen from outside
				var nw := Vector3(n.x, -n.y, 0.0)
				var pw := Vector3(p.x * PX, (h - p.y) * PX, 0.0)
				var qw := Vector3(q.x * PX, (h - q.y) * PX, 0.0)
				var dir := Vector3(-nw.y, nw.x, 0.0)
				if (qw - pw).dot(dir) < 0.0:
					var t2 := pw
					pw = qw
					qw = t2
				var up := pw.dot(dir)
				var uq := qw.dot(dir)
				var bent := (nw * 0.55 + Vector3(0, 0, 0.85)).normalized()
				var b := verts.size()
				# the bevelled lip, then the wall back to the rear
				for v in [[pw, zf, bent, up], [qw, zf, bent, uq], [qw, zm, nw, uq], [pw, zm, nw, up], [qw, zb, nw, uq], [pw, zb, nw, up]]:
					var pos: Vector3 = v[0]
					verts.append(Vector3(pos.x, pos.y, v[1]))
					norms.append(v[2])
					tans.append_array([dir.x, dir.y, 0.0, -1.0])
					uvs.append(Vector2(v[3], -v[1]))
				idx.append_array([b, b + 1, b + 2, b, b + 2, b + 3, b + 3, b + 2, b + 4, b + 3, b + 4, b + 5])
				if nw.y > 0.6:
					_grow(mid, pw, qw, tufts)
	_place_grass(k, tufts)
	var old: MeshInstance3D = _chunks.get(k)
	if verts.is_empty():
		if old:
			old.queue_free()
			_chunks.erase(k)
		return
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TANGENT] = tans
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	if old == null:
		old = MeshInstance3D.new()
		old.material_override = wall_mat
		add_child(old)
		_chunks[k] = old
	old.mesh = am


## Tufts along an upward face, in rows from the front lip to the rear, where the level began with open sky.
func _grow(mid: Vector2, pw: Vector3, qw: Vector3, out: Array[Transform3D]) -> void:
	var x := int(mid.x)
	var y := int(mid.y + 0.6)
	if x < 0 or x >= w or y < 1 or y >= h or original[y * w + x] == 0 or original[(y - 1) * w + x] != 0:
		return
	for r in 11:
		var hsh := _hash(x * 131 + r * 7919 + y * 31337)
		if hsh > 0.55:
			continue
		var f := _hash(hsh * 9973.0 + 1.0)
		var z := FRONT - 0.06 - r * 0.24 - f * 0.2
		var p := pw.lerp(qw, _hash(f * 7.0 + 3.0))
		var s := 0.7 + f * 0.8 if r > 0 else 0.55 + f * 0.4
		var basis := Basis(Vector3.UP, hsh * 40.0).scaled(Vector3(s, s * (0.8 + _hash(f + 5.0) * 0.6), s))
		out.append(Transform3D(basis, Vector3(p.x, p.y - 0.01, z)))


func _hash(v: float) -> float:
	return fposmod(sin(v * 12.9898 + 4.1414) * 43758.5453, 1.0)


func _place_grass(k: Vector2i, tufts: Array[Transform3D]) -> void:
	var old: MultiMeshInstance3D = _grass.get(k)
	if tufts.is_empty() or grass_mat == null:
		if old:
			old.queue_free()
			_grass.erase(k)
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _grass_mesh
	mm.instance_count = tufts.size()
	for i in tufts.size():
		mm.set_instance_transform(i, tufts[i])
	if old == null:
		old = MultiMeshInstance3D.new()
		old.material_override = grass_mat
		old.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(old)
		_grass[k] = old
	old.multimesh = mm


## One tuft: five tapered, curved blades; UV.y runs from root to tip (the shader colours and sways by it).
func _tuft() -> ArrayMesh:
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	for bl in 5:
		var a := bl * TAU / 5.0 + 0.4
		var dir := Vector3(cos(a), 0.0, sin(a))
		var side := Vector3(-dir.z, 0.0, dir.x)
		var ht := 0.11 + 0.05 * float(bl % 3) / 2.0
		var lean := 0.035 + 0.02 * float(bl % 2)
		var segs := 3
		for sgi in segs:
			var t0 := float(sgi) / segs
			var t1 := float(sgi + 1) / segs
			var w0 := 0.014 * (1.0 - t0)
			var w1 := 0.014 * (1.0 - t1)
			var c0 := dir * lean * t0 * t0 + Vector3(0, ht * t0, 0) + dir * 0.012
			var c1 := dir * lean * t1 * t1 + Vector3(0, ht * t1, 0) + dir * 0.012
			var quad := [c0 - side * w0, c0 + side * w0, c1 + side * w1, c1 - side * w1]
			var tv := [t0, t0, t1, t1]
			for id in [0, 1, 2, 0, 2, 3]:
				verts.append(quad[id])
				norms.append(Vector3(dir.x * 0.3, 1.0, dir.z * 0.3).normalized())
				uvs.append(Vector2(0.0, tv[id]))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TEX_UV] = uvs
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am


## The midpoint of a cell edge, in pixel coordinates (pixel centres sit at +0.5).
func _edge(i: int, j: int, e: int) -> Vector2:
	match e:
		0: return Vector2(i + 1.0, j + 0.5)
		1: return Vector2(i + 1.5, j + 1.0)
		2: return Vector2(i + 1.0, j + 1.5)
	return Vector2(i + 0.5, j + 1.0)
