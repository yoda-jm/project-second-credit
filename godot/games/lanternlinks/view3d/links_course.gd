class_name LinksCourse
extends Node3D
## One hole in 3D, built from its LinksHole so the felt is exactly what the ball rolls on: the felt (a mesh sampled
## from the hole's own surface, bumps and the cup's dip included; sand and ice in their own materials), wooden rails
## along every wall, raised garden beds on the wall cells, stone sides where the course drops (steps, the plinth,
## ponds, the ravine), water, the cup with its liner and flag, the tee mat, booster arrows, and the gadgets: the
## windmill, bumpers, sliding blocks, the turnstile, glass pipes and the loop. `update` moves the gadgets with the
## hole clock. World: x east, y up, z south (the plan's y); the garden lawn is at y = GROUND.

const H = preload("res://games/lanternlinks/engine/links_hole.gd")
const P = preload("res://games/lanternlinks/engine/links_physics.gd")
const M := "res://games/lanternlinks/art/models/"
const SH := "res://games/lanternlinks/shaders/"

const GROUND := -0.6
const RAIL_T := 0.09
const RAIL_H := 0.1
const BED := 0.05
const RAVINE := -1.5
const POND := 0.32      ## a pond's floor, below its cell's height
const WATER := 0.07     ## the water surface, below its cell's height
const PIPE_PEAK := 0.9  ## the glass pipe's arc rises this far over its mouths

var hole: LinksHole
var gadget_nodes: Array = []
var flag: Node3D
var felt_mat: ShaderMaterial
var water_mat: ShaderMaterial
var glow_mats: Array[StandardMaterial3D] = []   ## lamps on the gadgets, brighter at night
var bounds := AABB()
var _flag_lift := 0.0


func build(h: LinksHole) -> void:
	hole = h
	for c in get_children():
		c.queue_free()
	gadget_nodes.clear()
	glow_mats.clear()
	felt_mat = ShaderMaterial.new()
	felt_mat.shader = load(SH + "links_felt.gdshader")
	var holes_uni: Array[Vector4] = [Vector4(h.cup.x, h.cup.y, H.CUP_R, 0)]
	for g in h.gadgets:
		if g["type"] == "pipe":
			holes_uni.append(Vector4(g["a"].x, g["a"].y, H.PIPE_R, 0))
			holes_uni.append(Vector4(g["b"].x, g["b"].y, H.PIPE_R, 0))
	while holes_uni.size() < 5:
		holes_uni.append(Vector4(-100, -100, 0, 0))
	felt_mat.set_shader_parameter("holes", holes_uni)
	water_mat = ShaderMaterial.new()
	water_mat.shader = load(SH + "links_water.gdshader")
	_felt()
	_walls()
	_skirts()
	_water_and_ravine()
	_cup()
	_tee()
	_boosts()
	for g in h.gadgets:
		gadget_nodes.append(_gadget(g))
	bounds = AABB(Vector3(0, GROUND, 0), Vector3(h.w * H.CELL, 1.0, h.h * H.CELL))


# --- helpers ---

func _node(name: String) -> Node3D:
	var path := M + name + ".glb"
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	return null


func _mesh(st: SurfaceTool, mat: Material, shadows := true) -> MeshInstance3D:
	var arrays := st.commit_to_arrays()
	var verts = arrays[Mesh.ARRAY_VERTEX]
	var mi := MeshInstance3D.new()
	if verts == null or (verts as PackedVector3Array).is_empty():
		add_child(mi)   # nothing of this kind on this hole: an empty node
		return mi
	if arrays[Mesh.ARRAY_TEX_UV] != null:
		st.generate_tangents()
	mi.mesh = st.commit()
	mi.material_override = mat
	if not shadows:
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


func _std(col: Color, rough := 0.5, metal := 0.0, emit := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	m.metallic = metal
	if emit > 0.0:
		m.emission_enabled = true
		m.emission = col
		m.emission_energy_multiplier = emit
	return m


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3) -> void:
	# a b c d counter-clockwise seen from the front
	var n := (b - a).cross(d - a).normalized()
	if n.length_squared() < 0.5:
		n = (c - b).cross(a - b).normalized() * -1.0
	for v in [a, b, c, a, c, d]:
		st.set_normal(n)
		st.set_uv(Vector2(v.x + v.z, v.y))
		st.add_vertex(v)


## Height of cell i's surface at p (its own floor, so edges don't jump to the neighbour's), and the normal there.
func _top(i: int, p: Vector2) -> float:
	return hole.cell_floor(i, p).x + hole.extras(p).x


func _normal(i: int, p: Vector2) -> Vector3:
	var s := hole.cell_floor(i, p) + hole.extras(p)
	return Vector3(-s.y, 1.0, -s.z).normalized()


func _open(k: int) -> bool:
	return k > H.WALL and k != H.WATER and k != H.CHASM


func _kind(x: int, y: int) -> int:
	if x < 0 or y < 0 or x >= hole.w or y >= hole.h:
		return H.OUT
	return hole.kind[y * hole.w + x]


## A garden bed's height: a little over the highest open cell beside it.
func _bed(x: int, y: int) -> float:
	var best := -INF
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var k := _kind(x + dx, y + dy)
			if k > H.WALL and k != H.CHASM:
				var i := (y + dy) * hole.w + x + dx
				var r: Array = hole.ramp.get(i, [])
				best = maxf(best, maxf(r[3], r[4]) if not r.is_empty() else hole.base[i])
	return (best if best > -INF else 0.0) + BED


# --- the felt ---

func _felt() -> void:
	var felt := SurfaceTool.new()
	var sand := SurfaceTool.new()
	var ice := SurfaceTool.new()
	for st in [felt, sand, ice]:
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for y in hole.h:
		for x in hole.w:
			var i := y * hole.w + x
			var k := hole.kind[i]
			if not _open(k):
				continue
			var st: SurfaceTool = sand if k == H.SAND else (ice if k == H.ICE else felt)
			var o := Vector2(x, y) * H.CELL
			var fine := hole.extras(o + Vector2.ONE * H.CELL * 0.5).length() > 0.0 or _near_smooth(o)
			var n := 8 if fine else 2
			if hole.diag[i] != 0:
				n = maxi(n, 4)
			var s := H.CELL / n
			for qy in n:
				for qx in n:
					var p00 := o + Vector2(qx, qy) * s
					var p10 := p00 + Vector2(s, 0)
					var p11 := p00 + Vector2(s, s)
					var p01 := p00 + Vector2(0, s)
					var tris: Array
					# split along the bank's line in a bank cell, so its open half is exact
					if hole.diag[i] == 1 or hole.diag[i] == 2:
						tris = [[p00, p10, p01], [p10, p11, p01]]
					else:
						tris = [[p00, p10, p11], [p00, p11, p01]]
					for t in tris:
						if hole.diag[i] != 0:
							var cen: Vector2 = (t[0] + t[1] + t[2]) / 3.0
							if H._in_diag(hole.diag[i], cen / H.CELL - Vector2(x, y)):
								continue
						for v in t:
							var vv: Vector2 = v
							st.set_normal(_normal(i, vv))
							st.set_uv(vv)
							st.add_vertex(Vector3(vv.x, _top(i, vv), vv.y))
	var fm := _mesh(felt, felt_mat)
	fm.name = "felt"
	var sm := Pbr.material("sand", Color(1.0, 0.93, 0.8), 1.6)
	_mesh(sand, sm)
	var im := StandardMaterial3D.new()
	im.albedo_color = Color(0.75, 0.9, 1.0)
	im.roughness = 0.08
	im.metallic_specular = 0.8
	im.clearcoat_enabled = true
	im.clearcoat = 1.0
	_mesh(ice, im)


func _near_smooth(o: Vector2) -> bool:
	var c := o + Vector2.ONE * H.CELL * 0.5
	for b in hole.bumps:
		if c.distance_to(b[0]) < b[1] + H.CELL:
			return true
	return c.distance_to(hole.cup) < H.DIP_R + H.CELL


# --- walls: rails, garden beds, the plinth ---

func _walls() -> void:
	var rails := SurfaceTool.new()
	var beds := SurfaceTool.new()
	var sides := SurfaceTool.new()
	for st in [rails, beds, sides]:
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var dirs := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
	for y in hole.h:
		for x in hole.w:
			var i := y * hole.w + x
			var k := hole.kind[i]
			if k == H.OUT:
				continue
			if k == H.WALL:
				var top := _bed(x, y)
				var o := Vector3(x * H.CELL, top, y * H.CELL)
				_quad(beds, o, o + Vector3(H.CELL, 0, 0), o + Vector3(H.CELL, 0, H.CELL), o + Vector3(0, 0, H.CELL))
				# its sides where the ground beside it is lower: the plinth, a pond, the ravine, a lower bed
				for d in dirs:
					var nk := _kind(x + d.x, y + d.y)
					var low := GROUND
					if nk == H.WALL:
						low = _bed(x + d.x, y + d.y)
					elif nk == H.CHASM:
						low = RAVINE
					elif nk == H.WATER:
						low = hole.base[(y + d.y) * hole.w + x + d.x] - POND
					elif nk != H.OUT:
						continue   # an open cell: the rail covers this side
					if low < top - 0.001:
						_side(sides, Vector2i(x, y), d, top, low)
				continue
			if not _open(k) and k != H.WATER:
				continue
			# rails along the walls around an open (or water) cell
			if hole.diag[i] != 0:
				_diag_rail(rails, beds, x, y, hole.diag[i])
			if k == H.WATER:
				continue
			for d in dirs:
				var nk2 := _kind(x + d.x, y + d.y)
				if nk2 > H.WALL:
					continue
				_rail(rails, x, y, d)
	var wood := Pbr.material("planks", Color(0.72, 0.5, 0.34), 1.2)
	_mesh(rails, wood).name = "rails"
	_mesh(beds, Pbr.material("grass_lush", Color(1.0, 1.1, 0.9), 1.4)).name = "beds"
	_mesh(sides, Pbr.material("stone_bricks", Color(0.85, 0.8, 0.75), 1.4)).name = "plinth"


## A vertical face on the side `d` of cell c, from `top` down to `low`.
func _side(st: SurfaceTool, c: Vector2i, d: Vector2i, top: float, low: float) -> void:
	var a: Vector2
	var b: Vector2
	var o := Vector2(c) * H.CELL
	match d:
		Vector2i(0, -1): a = o + Vector2(H.CELL, 0); b = o
		Vector2i(1, 0): a = o + Vector2(H.CELL, H.CELL); b = o + Vector2(H.CELL, 0)
		Vector2i(0, 1): a = o + Vector2(0, H.CELL); b = o + Vector2(H.CELL, H.CELL)
		_: a = o; b = o + Vector2(0, H.CELL)
	_quad(st, Vector3(a.x, low, a.y), Vector3(b.x, low, b.y), Vector3(b.x, top, b.y), Vector3(a.x, top, a.y))


## A wooden rail along the edge `d` of open cell (x, y), standing on the wall's side of the line and following the
## felt's height; it reaches past its ends at outer corners so corners close.
func _rail(st: SurfaceTool, x: int, y: int, d: Vector2i) -> void:
	var i := y * hole.w + x
	var o := Vector2(x, y) * H.CELL
	var along: Vector2
	var start: Vector2
	match d:
		Vector2i(0, -1): start = o; along = Vector2(1, 0)
		Vector2i(1, 0): start = o + Vector2(H.CELL, 0); along = Vector2(0, 1)
		Vector2i(0, 1): start = o + Vector2(H.CELL, H.CELL); along = Vector2(-1, 0)
		_: start = o + Vector2(0, H.CELL); along = Vector2(0, -1)
	var out := Vector2(d)
	var t0 := 0.0
	var t1 := H.CELL
	# at an outer corner the wall goes on round the corner: reach over it
	var before := Vector2i(x, y) - Vector2i(along)
	var after := Vector2i(x, y) + Vector2i(along)
	if _kind(before.x, before.y) <= H.WALL:
		t0 -= RAIL_T
	if _kind(after.x, after.y) <= H.WALL:
		t1 += RAIL_T
	var n := 4
	var prev_in := Vector3.ZERO
	var prev_out := Vector3.ZERO
	var prev_low := 0.0
	for s in n + 1:
		var t := lerpf(t0, t1, float(s) / n)
		var p := start + along * t
		var inner := p.clamp(o, o + Vector2.ONE * H.CELL)
		var hgt := _top(i, inner + (Vector2.ONE * H.CELL * 0.5 - (inner - o)).normalized() * 0.001) + RAIL_H
		var low := minf(_top(i, inner), _bed(x + d.x, y + d.y)) - 0.03
		var vin := Vector3(p.x, hgt, p.y)
		var vout := Vector3(p.x + out.x * RAIL_T, hgt, p.y + out.y * RAIL_T)
		if s > 0:
			_quad(st, prev_in, vin, vout, prev_out)                                                  # top
			_quad(st, Vector3(prev_in.x, prev_low, prev_in.z), Vector3(vin.x, low, vin.z), vin, prev_in)   # the lane side
			_quad(st, prev_out, vout, Vector3(vout.x, low, vout.z), Vector3(prev_out.x, prev_low, prev_out.z))
		prev_in = vin
		prev_out = vout
		prev_low = low
	# end caps
	for e in [[t0, -1.0], [t1, 1.0]]:
		var p2: Vector2 = start + along * float(e[0])
		var inner2 := p2.clamp(o, o + Vector2.ONE * H.CELL)
		var hg := _top(i, inner2) + RAIL_H
		var lo := hg - RAIL_H - 0.05
		var a := Vector3(p2.x, hg, p2.y)
		var b := a + Vector3(out.x, 0, out.y) * RAIL_T
		if e[1] < 0:
			_quad(st, Vector3(b.x, lo, b.z), Vector3(a.x, lo, a.z), a, b)
		else:
			_quad(st, Vector3(a.x, lo, a.z), Vector3(b.x, lo, b.z), b, a)


## A bank cell: a rail along its face and a bed on its solid half.
func _diag_rail(rails: SurfaceTool, beds: SurfaceTool, x: int, y: int, d: int) -> void:
	var i := y * hole.w + x
	var o := Vector2(x, y) * H.CELL
	var c := H.CELL
	var a: Vector2
	var b: Vector2
	var solid_corner: Vector2
	match d:
		1: a = o + Vector2(0, c); b = o + Vector2(c, 0); solid_corner = o
		2: a = o + Vector2(c, 0); b = o + Vector2(0, c); solid_corner = o + Vector2(c, c)
		3: a = o; b = o + Vector2(c, c); solid_corner = o + Vector2(c, 0)
		_: a = o + Vector2(c, c); b = o; solid_corner = o + Vector2(0, c)
	var into := (solid_corner - (a + b) * 0.5).normalized()
	var hb := hole.base[i]
	var top := hb + RAIL_H
	var ext := (b - a).normalized() * RAIL_T * 0.7
	var a2 := a - ext
	var b2 := b + ext
	var A := Vector3(a2.x, top, a2.y)
	var B := Vector3(b2.x, top, b2.y)
	var off := Vector3(into.x, 0, into.y) * RAIL_T
	var lo := hb - 0.03
	_quad(rails, A, B, B + off, A + off)
	var fa := Vector3(A.x, lo, A.z)
	var fb := Vector3(B.x, lo, B.z)
	# the face toward the open half: make sure it faces away from the solid corner
	if (fb - fa).cross(B - fa).dot(-off) >= 0.0:
		_quad(rails, fa, fb, B, A)
	else:
		_quad(rails, fb, fa, A, B)
	var bed := hb + BED
	var tri := [Vector3(a.x, bed, a.y), Vector3(b.x, bed, b.y), Vector3(solid_corner.x, bed, solid_corner.y)]
	var n: Vector3 = (tri[1] - tri[0]).cross(tri[2] - tri[0])
	if n.y < 0.0:
		tri = [tri[1], tri[0], tri[2]]
	for v in tri:
		beds.set_normal(Vector3.UP)
		beds.set_uv(Vector2(v.x, v.z))
		beds.add_vertex(v)


# --- steps between open cells, and the drops into water and the ravine ---

func _skirts() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var dirs := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
	for y in hole.h:
		for x in hole.w:
			var i := y * hole.w + x
			if not _open(hole.kind[i]):
				continue
			for d in dirs:
				var nk := _kind(x + d.x, y + d.y)
				if nk <= H.WALL:
					continue
				var j: int = (y + d.y) * hole.w + x + d.x
				var o := Vector2(x, y) * H.CELL
				var a: Vector2
				var b: Vector2
				match d:
					Vector2i(0, -1): a = o + Vector2(H.CELL, 0); b = o
					Vector2i(1, 0): a = o + Vector2(H.CELL, H.CELL); b = o + Vector2(H.CELL, 0)
					Vector2i(0, 1): a = o + Vector2(0, H.CELL); b = o + Vector2(H.CELL, H.CELL)
					_: a = o; b = o + Vector2(0, H.CELL)
				var n := 4
				for s in n:
					var p0 := a.lerp(b, float(s) / n)
					var p1 := a.lerp(b, float(s + 1) / n)
					var t0 := _top(i, p0)
					var t1 := _top(i, p1)
					var l0: float
					var l1: float
					if nk == H.CHASM:
						l0 = RAVINE
						l1 = RAVINE
					elif nk == H.WATER:
						l0 = hole.base[j] - POND
						l1 = l0
					else:
						l0 = _top(j, p0)
						l1 = _top(j, p1)
					if l0 < t0 - 0.004 or l1 < t1 - 0.004:
						_quad(st, Vector3(p0.x, minf(l0, t0), p0.y), Vector3(p1.x, minf(l1, t1), p1.y),
							Vector3(p1.x, t1, p1.y), Vector3(p0.x, t0, p0.y))
	_mesh(st, Pbr.material("stone_bricks", Color(0.8, 0.76, 0.72), 1.6)).name = "steps"


func _water_and_ravine() -> void:
	var water := SurfaceTool.new()
	var bed := SurfaceTool.new()
	var rocks := SurfaceTool.new()
	var stream := SurfaceTool.new()
	for st in [water, bed, rocks, stream]:
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var any_w := false
	var any_c := false
	for y in hole.h:
		for x in hole.w:
			var i := y * hole.w + x
			var o := Vector3(x * H.CELL, 0, y * H.CELL)
			var e := [o, o + Vector3(H.CELL, 0, 0), o + Vector3(H.CELL, 0, H.CELL), o + Vector3(0, 0, H.CELL)]
			var lift := func(v: Vector3, hh: float) -> Vector3: return v + Vector3(0, hh, 0)
			if hole.kind[i] == H.WATER:
				any_w = true
				var wl := hole.base[i] - WATER
				var bl := hole.base[i] - POND
				_quad(water, lift.call(e[0], wl), lift.call(e[1], wl), lift.call(e[2], wl), lift.call(e[3], wl))
				_quad(bed, lift.call(e[0], bl), lift.call(e[1], bl), lift.call(e[2], bl), lift.call(e[3], bl))
			elif hole.kind[i] == H.CHASM:
				any_c = true
				_quad(rocks, lift.call(e[0], RAVINE), lift.call(e[1], RAVINE), lift.call(e[2], RAVINE), lift.call(e[3], RAVINE))
				var sl := RAVINE + 0.12
				_quad(stream, lift.call(e[0], sl), lift.call(e[1], sl), lift.call(e[2], sl), lift.call(e[3], sl))
	if any_w:
		var wm := _mesh(water, water_mat, false)
		wm.name = "pond"
		_mesh(bed, Pbr.material("soil", Color(0.45, 0.4, 0.3), 1.0))
		# lily pads float on the ponds
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(hole.name)
		for y in hole.h:
			for x in hole.w:
				if hole.kind[y * hole.w + x] == H.WATER and rng.randf() < 0.3:
					var lp := _node("lily_pad")
					if lp:
						lp.position = Vector3((x + rng.randf_range(0.2, 0.8)) * H.CELL, hole.base[y * hole.w + x] - WATER + 0.005,
							(y + rng.randf_range(0.2, 0.8)) * H.CELL)
						lp.rotation.y = rng.randf() * TAU
						lp.scale = Vector3.ONE * rng.randf_range(0.7, 1.1)
						var lily := lp.find_child("lily", true, false) as Node3D
						if lily and rng.randf() < 0.5:
							lily.visible = false
						add_child(lp)
	if any_c:
		_mesh(rocks, Pbr.material("rock", Color(0.6, 0.58, 0.55), 1.0))
		_mesh(stream, water_mat, false).name = "stream"


# --- the cup, the tee, boosters ---

func _cup() -> void:
	var c := hole.cup
	var top := hole.cup_h
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 32
	var depth := 0.13
	for k in n:
		var a0 := TAU * k / n
		var a1 := TAU * (k + 1) / n
		var p0 := Vector3(c.x + cos(a0) * H.CUP_R, top, c.y + sin(a0) * H.CUP_R)
		var p1 := Vector3(c.x + cos(a1) * H.CUP_R, top, c.y + sin(a1) * H.CUP_R)
		# the liner, seen from inside
		var q0 := p0 - Vector3(0, depth, 0)
		var q1 := p1 - Vector3(0, depth, 0)
		for v in [[p0, Vector3(-cos(a0), 0, -sin(a0))], [p1, Vector3(-cos(a1), 0, -sin(a1))], [q1, Vector3(-cos(a1), 0, -sin(a1))],
				[p0, Vector3(-cos(a0), 0, -sin(a0))], [q1, Vector3(-cos(a1), 0, -sin(a1))], [q0, Vector3(-cos(a0), 0, -sin(a0))]]:
			st.set_normal(v[1])
			st.add_vertex(v[0])
		# the bottom
		for v2 in [Vector3(c.x, top - depth, c.y), q1, q0]:
			st.set_normal(Vector3.UP)
			st.add_vertex(v2)
	var liner := _mesh(st, _std(Color(0.92, 0.92, 0.9), 0.35), false)
	liner.name = "cup"
	# a bright rim ring just over the felt: it catches the light and, at night, glows
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = H.CUP_R
	tm.outer_radius = H.CUP_R + 0.012
	tm.rings = 32
	ring.mesh = tm
	var rm := _std(Color(1.0, 0.9, 0.6), 0.3, 0.6, 0.4)
	glow_mats.append(rm)
	ring.material_override = rm
	ring.position = Vector3(c.x, top + 0.002, c.y)
	ring.scale = Vector3(1, 0.3, 1)
	add_child(ring)
	flag = _node("flag")
	if flag == null:
		flag = Node3D.new()
		var pole := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.012
		cm.bottom_radius = 0.012
		cm.height = 1.0
		pole.mesh = cm
		pole.position.y = 0.5
		pole.material_override = _std(Color(0.95, 0.95, 0.95), 0.3)
		flag.add_child(pole)
		var cloth := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.3, 0.2, 0.005)
		cloth.mesh = bm
		cloth.position = Vector3(0.16, 0.84, 0)
		cloth.material_override = _std(Color(1.0, 0.8, 0.2), 0.8)
		cloth.name = "flag"
		flag.add_child(cloth)
	flag.position = Vector3(c.x, top - 0.1, c.y)
	add_child(flag)
	var cloth2 := flag.find_child("flag", true, false) as MeshInstance3D
	if cloth2:
		var fm := ShaderMaterial.new()
		fm.shader = load(SH + "links_flag.gdshader")
		cloth2.material_override = fm


func _tee() -> void:
	var t := hole.tee
	var hgt := hole.height(t)
	var mat := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.44, 0.012, 0.44)
	mat.mesh = bm
	mat.material_override = _std(Color(0.12, 0.3, 0.16), 0.9)
	mat.position = Vector3(t.x, hgt + 0.002, t.y)
	mat.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mat)
	for sx in [-0.18, 0.18]:
		var m := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.025
		sm.height = 0.05
		m.mesh = sm
		var gm := _std(Color(1.0, 0.85, 0.45), 0.3, 0.0, 0.6)
		glow_mats.append(gm)
		m.material_override = gm
		m.position = Vector3(t.x + sx, hgt + 0.03, t.y - 0.18)
		add_child(m)


func _boosts() -> void:
	if hole.boost.is_empty():
		return
	var sh: Shader = load(SH + "links_boost.gdshader")
	for i in hole.boost:
		var d: Vector2 = hole.boost[i]
		var c := hole.centre(i % hole.w, i / hole.w)
		var q := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(H.CELL, H.CELL) * 0.92
		q.mesh = pm
		var m := ShaderMaterial.new()
		m.shader = sh
		q.material_override = m
		q.position = Vector3(c.x, hole.height(c) + 0.004, c.y)
		q.rotation.y = -d.angle() - PI * 0.5
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(q)


# --- gadgets ---

func _gadget(g: Dictionary) -> Node3D:
	var n: Node3D
	match g["type"]:
		"windmill":
			n = _node("windmill")
			var c: Vector2i = g["cell"]
			var p := hole.centre(c.x, c.y)
			if n == null:
				n = Node3D.new()
				var body := MeshInstance3D.new()
				var bm := BoxMesh.new()
				bm.size = Vector3(1.5, 1.6, 0.5)
				body.mesh = bm
				body.position.y = 1.1
				body.material_override = _std(Color(0.95, 0.9, 0.8))
				n.add_child(body)
				var bl := Node3D.new()
				bl.name = "blades"
				bl.position = Vector3(0, 1.05, 0.33)
				for k in 4:
					var s := MeshInstance3D.new()
					var sb := BoxMesh.new()
					sb.size = Vector3(0.16, 0.98, 0.02)
					s.mesh = sb
					s.position = Vector3(0, 0.49, 0).rotated(Vector3.BACK, k * PI * 0.5)
					s.rotation.z = k * PI * 0.5
					s.material_override = _std(Color(0.9, 0.85, 0.75))
					bl.add_child(s)
				n.add_child(bl)
			var face: Vector2 = g["face"]
			n.position = Vector3(p.x, hole.base[c.y * hole.w + c.x], p.y)
			n.rotation.y = atan2(face.x, face.y)
			_collect_glow(n)
		"bumper":
			n = _node("bumper")
			if n == null:
				n = MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.18
				cm.bottom_radius = 0.18
				cm.height = 0.14
				(n as MeshInstance3D).mesh = cm
				(n as MeshInstance3D).material_override = _std(Color(0.9, 0.2, 0.2), 0.3)
			var pos: Vector2 = g["pos"]
			n.position = Vector3(pos.x, hole.height(pos), pos.y)
			var s2: float = g["r"] / 0.18
			n.scale = Vector3(s2, 1.0, s2)
			_collect_glow(n)
		"mover":
			n = Node3D.new()
			var half: Vector2 = g["half"]
			var block := MeshInstance3D.new()
			var bb := BoxMesh.new()
			bb.size = Vector3(half.x * 2.0, 0.22, half.y * 2.0)
			block.mesh = bb
			block.position.y = 0.11
			block.material_override = Pbr.local("planks", Color(0.55, 0.32, 0.22), 2.0)
			n.add_child(block)
			var cap := MeshInstance3D.new()
			var cb := BoxMesh.new()
			cb.size = Vector3(half.x * 2.0 + 0.02, 0.03, half.y * 2.0 + 0.02)
			cap.mesh = cb
			cap.position.y = 0.235
			var capm := _std(Color(0.85, 0.65, 0.3), 0.3, 0.8)
			cap.material_override = capm
			n.add_child(cap)
			# a lamp stripe round the block
			var strip := MeshInstance3D.new()
			var sbm := BoxMesh.new()
			sbm.size = Vector3(half.x * 2.0 + 0.006, 0.02, half.y * 2.0 + 0.006)
			strip.mesh = sbm
			strip.position.y = 0.16
			var gm := _std(Color(1.0, 0.6, 0.25), 0.4, 0.0, 1.2)
			glow_mats.append(gm)
			strip.material_override = gm
			n.add_child(strip)
		"spinner":
			n = _node("spinner")
			if n == null:
				n = MeshInstance3D.new()
				var sbm2 := BoxMesh.new()
				sbm2.size = Vector3(float(g["len"]) * 2.0, 0.07, 0.05)
				(n as MeshInstance3D).mesh = sbm2
				(n as MeshInstance3D).material_override = _std(Color(0.9, 0.4, 0.2), 0.4)
			var sp: Vector2 = g["pos"]
			n.position = Vector3(sp.x, hole.height(sp), sp.y)
			n.scale = Vector3(float(g["len"]) / 0.36, 1, 1)
			_collect_glow(n)
		"pipe":
			n = _pipe(g)
		"loop":
			n = _loop(g)
	if n:
		add_child(n)
	return n


func _collect_glow(n: Node) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for s in mesh.get_surface_count():
			var m := mesh.surface_get_material(s)
			if m is StandardMaterial3D and m.resource_name.contains("glow"):
				glow_mats.append(m)


## A glass pipe arcing from its mouth to its exit, with brass rings round both mouths.
func _pipe(g: Dictionary) -> Node3D:
	var n := Node3D.new()
	var pts := pipe_path(g)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rad := 0.075
	var sides := 12
	var prev: Array = []
	for k in pts.size():
		var p: Vector3 = pts[k]
		var t: Vector3 = (pts[mini(k + 1, pts.size() - 1)] - pts[maxi(k - 1, 0)]).normalized()
		var side := t.cross(Vector3.UP).normalized()
		if side.length_squared() < 0.5:
			side = Vector3.RIGHT
		var up := side.cross(t).normalized()
		var ring: Array = []
		for s in sides + 1:
			var a := TAU * s / sides
			ring.append([p + (side * cos(a) + up * sin(a)) * rad, (side * cos(a) + up * sin(a))])
		if not prev.is_empty():
			for s in sides:
				for v in [prev[s], ring[s], ring[s + 1], prev[s], ring[s + 1], prev[s + 1]]:
					st.set_normal(v[1])
					st.add_vertex(v[0])
		prev = ring
	var glass := StandardMaterial3D.new()
	glass.albedo_color = Color(0.75, 0.9, 1.0, 0.22)
	glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glass.roughness = 0.05
	glass.metallic_specular = 1.0
	glass.rim_enabled = true
	glass.rim = 0.6
	glass.cull_mode = BaseMaterial3D.CULL_DISABLED
	var tube := MeshInstance3D.new()
	tube.mesh = st.commit()
	tube.material_override = glass
	tube.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	n.add_child(tube)
	for end in [g["a"], g["b"]]:
		var e: Vector2 = end
		var ring2 := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = H.PIPE_R
		tm.outer_radius = H.PIPE_R + 0.03
		ring2.mesh = tm
		ring2.material_override = _std(Color(0.9, 0.7, 0.35), 0.25, 0.9)
		ring2.position = Vector3(e.x, hole.height(e) + 0.004, e.y)
		n.add_child(ring2)
		var hole_d := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = H.PIPE_R
		cm.bottom_radius = H.PIPE_R
		cm.height = 0.12
		hole_d.mesh = cm
		hole_d.material_override = _std(Color(0.05, 0.05, 0.06), 0.9)
		hole_d.position = Vector3(e.x, hole.height(e) - 0.065, e.y)
		n.add_child(hole_d)
		var lamp := _std(Color(0.4, 0.9, 1.0), 0.3, 0.0, 1.5)
		glow_mats.append(lamp)
		var glow_ring := MeshInstance3D.new()
		var tm2 := TorusMesh.new()
		tm2.inner_radius = H.PIPE_R + 0.03
		tm2.outer_radius = H.PIPE_R + 0.042
		glow_ring.mesh = tm2
		glow_ring.material_override = lamp
		glow_ring.position = ring2.position + Vector3(0, 0.002, 0)
		n.add_child(glow_ring)
	return n


## The ball's route through a pipe: down its mouth, up and over in a glass arc, down into the exit.
func pipe_path(g: Dictionary) -> PackedVector3Array:
	var a: Vector2 = g["a"]
	var b: Vector2 = g["b"]
	var ha := hole.height(a)
	var hb := hole.height(b)
	var out := PackedVector3Array()
	var n := 40
	for k in n + 1:
		var f := float(k) / n
		var p := a.lerp(b, f)
		var hgt := lerpf(ha, hb, f) + sin(f * PI) * (PIPE_PEAK + a.distance_to(b) * 0.08) - 0.1 * (1.0 - sin(f * PI))
		out.append(Vector3(p.x, hgt, p.y))
	return out


## The loop: two steel rails round the ball's circle (a little aside on the way out, as the track passes
## itself), a glowing strip between them, a lead in and out, and posts holding it up.
func _loop(g: Dictionary) -> Node3D:
	var n := Node3D.new()
	var base := hole.height(g["pos"])
	var rails := SurfaceTool.new()
	rails.begin(Mesh.PRIMITIVE_TRIANGLES)
	var strip := SurfaceTool.new()
	strip.begin(Mesh.PRIMITIVE_TRIANGLES)
	var dir: Vector2 = g["dir"]
	var side2 := Vector2(-dir.y, dir.x)
	var side := Vector3(side2.x, 0, side2.y)
	var steps := 96
	var pts: Array[Vector3] = []
	var norms: Array[Vector3] = []
	for k in steps + 1:
		var th := TAU * k / steps
		var p := loop_track(g, th, base)
		pts.append(p)
		# the track's inward normal (towards the circle's centre)
		norms.append(Vector3(-sin(th) * dir.x, cos(th), -sin(th) * dir.y))
	for off in [-0.045, 0.045]:
		_tube(rails, pts, norms, side * off, 0.012)
	for k in steps:
		var a := pts[k] - norms[k] * 0.004
		var b := pts[k + 1] - norms[k + 1] * 0.004
		_quad(strip, a - side * 0.02, b - side * 0.02, b + side * 0.02, a + side * 0.02)
	var steel := _std(Color(0.8, 0.82, 0.86), 0.2, 0.9)
	var rm := MeshInstance3D.new()
	rm.mesh = rails.commit()
	rm.material_override = steel
	n.add_child(rm)
	var lamp := _std(Color(0.4, 0.8, 1.0), 0.4, 0.0, 1.4)
	lamp.cull_mode = BaseMaterial3D.CULL_DISABLED
	glow_mats.append(lamp)
	var sm := MeshInstance3D.new()
	sm.mesh = strip.commit()
	sm.material_override = lamp
	sm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	n.add_child(sm)
	# posts from the lawn up to the loop's sides
	var centre := (g["pos"] as Vector2) + dir * (P.LOOP_SHIFT * 0.5)
	for s in [-1.0, 1.0]:
		var post := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.02
		cm.bottom_radius = 0.025
		var top := base + P.LOOP_R
		cm.height = top - GROUND + 0.05
		post.mesh = cm
		post.material_override = steel
		post.position = Vector3(centre.x, (top + GROUND) * 0.5, centre.y) + side * s * 0.2
		n.add_child(post)
		var arm := MeshInstance3D.new()
		var am := BoxMesh.new()
		am.size = Vector3(0.02, 0.02, 0.2)
		arm.mesh = am
		arm.material_override = steel
		arm.position = Vector3(centre.x, top, centre.y) + side * s * 0.12
		arm.look_at_from_position(arm.position, arm.position + side, Vector3.UP)
		n.add_child(arm)
	return n


func _tube(st: SurfaceTool, pts: Array[Vector3], norms: Array[Vector3], off: Vector3, r: float) -> void:
	var sides := 6
	var prev: Array = []
	for k in pts.size():
		var t := (pts[mini(k + 1, pts.size() - 1)] - pts[maxi(k - 1, 0)]).normalized()
		var u := norms[k]
		var v := t.cross(u).normalized()
		var ring: Array = []
		for s in sides + 1:
			var a := TAU * s / sides
			var nn := u * cos(a) + v * sin(a)
			ring.append([pts[k] + off - norms[k] * 0.01 + nn * r, nn])
		if not prev.is_empty():
			for s in sides:
				for q in [prev[s], ring[s], ring[s + 1], prev[s], ring[s + 1], prev[s + 1]]:
					st.set_normal(q[1])
					st.add_vertex(q[0])
		prev = ring


## The loop's running surface at angle `th` (the ball rides on it, inside the circle).
static func loop_track(g: Dictionary, th: float, base: float) -> Vector3:
	var p := P.loop_point(g, th)
	return Vector3(p.x, base + P.LOOP_R * (1.0 - cos(th)), p.y)


## The ball's centre on the loop (R in from the track).
static func loop_ball(g: Dictionary, th: float, base: float) -> Vector3:
	var dir: Vector2 = g["dir"]
	var t := loop_track(g, th, base)
	return t + Vector3(-sin(th) * dir.x, cos(th), -sin(th) * dir.y) * P.R


# --- per frame ---

func update(clock: float, delta: float, near_cup: bool) -> void:
	for k in hole.gadgets.size():
		var g: Dictionary = hole.gadgets[k]
		var n: Node3D = gadget_nodes[k]
		if n == null:
			continue
		match g["type"]:
			"windmill":
				var bl := n.find_child("blades", true, false) as Node3D
				if bl:
					bl.rotation.z = -P.windmill_angle(g, clock)
			"mover":
				var p := P.mover_pos(g, clock)
				n.position = Vector3(p.x, hole.height(p) - 0.0, p.y)
			"spinner":
				n.rotation.y = -P.spinner_angle(g, clock)
	# the flag lifts out of the cup as a ball comes close
	_flag_lift = move_toward(_flag_lift, 1.0 if near_cup else 0.0, delta * 2.0)
	if flag:
		flag.position.y = hole.cup_h - 0.1 + smoothstep(0.0, 1.0, _flag_lift) * 0.35
