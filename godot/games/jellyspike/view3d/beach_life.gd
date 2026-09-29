class_name BeachLife
extends Node3D
## The Jelly Spike beach's background life: now and then something happens away from the court, small and behind
## it, so the blobs and the ball stay the focus. A crab or two scuttle across the wet sand, dolphins leap far out,
## a gull glides in to land on a mooring post and looks about, kites climb over the far dunes, a coconut drops from a
## palm and rolls, a turtle waddles down to the sea, a line of pelicans glides over the water, a ferry or a sailboat
## crosses the horizon. Models: art/beach/critters.glb (tools/blender/jellyspike_beach.py); perch_<i> and coco_<i>
## empties in the diorama say where gulls land and coconuts fall. SpikeBeach.build() makes one and calls setup().
## Everything is random but seeded by the variant and driven by the node's own clock, so fixed-fps captures and the
## demo repeat exactly.

const GLB := "res://games/jellyspike/art/beach/critters.glb"
const SEA := -0.55
## kind: [weight, allowed at night]
const KINDS := {
	"crabs": [3.0, true], "dolphins": [2.2, true], "gull": [2.5, false], "kites": [1.4, false],
	"coconut": [1.2, true], "turtle": [1.6, true], "pelicans": [1.6, false], "ferry": [0.9, true], "sail": [1.0, true],
}
const MAX_ACTIVE := 2  ## events at once (the slow ones, boats on the horizon and the turtle, do not count)
const SLOW := ["ferry", "sail", "turtle"]
const BOATS := ["ferry", "sail"]

var _beach: SpikeBeach
var _t := 0.0
var _rng := RandomNumberGenerator.new()
var _next := 1.2
var _recent: Array = []  ## the last few kinds, not picked again straight away
var _night := false
var _active := {}      ## kind -> Dictionary of the event's state (t0, dur, ...)
var _n := {}           ## node lists per role
var _perches: Array = []
var _cocos: Array = []
var _coco_next := 0
var _splashes: Array = []
var _splash_i := 0


## Loads the critter models, dresses them with the beach's materials and hides them until their turn.
func setup(beach: SpikeBeach, diorama: Node3D, d: Dictionary, seed_: int) -> void:
	_beach = beach
	_night = d["night"]
	_rng.seed = seed_
	for n in diorama.find_children("*", "Node3D", true, false):
		var nm := String(n.name)
		if nm.begins_with("perch_"):
			_perches.append(beach._local_xform(n).origin)
		elif nm.begins_with("coco_"):
			_cocos.append(beach._local_xform(n).origin)
	var packed := load(GLB) as PackedScene
	if packed == null:
		push_error("BeachLife: missing %s" % GLB)
		return
	var root := packed.instantiate() as Node3D
	beach._dress(root, d)
	var tmpl := {}
	for c in root.get_children():
		if c is MeshInstance3D:
			tmpl[String(c.name)] = c
	_n["crab"] = _clones(tmpl, "ev_crab", 2, true)
	_n["gull"] = _clones(tmpl, "ev_gull", 1, true)
	_n["dolphin"] = _clones(tmpl, "ev_dolphin", 2, false)
	_n["turtle"] = _clones(tmpl, "ev_turtle", 1, true)
	_n["kite"] = [_one(tmpl, "ev_kite_0", false), _one(tmpl, "ev_kite_1", false)]
	_n["coconut"] = _clones(tmpl, "ev_coconut", maxi(1, _cocos.size()), true)
	_n["ferry"] = _clones(tmpl, "ev_ferry", 1, false)
	_n["sail"] = _clones(tmpl, "ev_sail", 1, false)
	root.free()
	# fliers: the beach's gull mesh, a gull that lands and five pelicans
	var mesh := beach._bird_mesh()
	var gm := beach._shader("beach_bird")
	gm.set_shader_parameter("color", Color("#f4f4f2"))
	gm.set_shader_parameter("tip", Color("#3a3e46"))
	gm.set_shader_parameter("rate", 8.0)
	_n["flyer"] = [_bird(mesh, gm, 0.42)]
	var pm := beach._shader("beach_bird")
	pm.set_shader_parameter("color", Color("#b0a498"))
	pm.set_shader_parameter("tip", Color("#2e2a26"))
	pm.set_shader_parameter("rate", 4.0)
	var pel: Array = []
	for i in 5:
		pel.append(_bird(mesh, pm, 0.75))
	_n["pelican"] = pel
	for i in 2:
		_splashes.append(_make_splash(i))
	# a boat already on its way when the match starts, so the horizon is never empty for long
	_start("sail" if _rng.randf() < 0.5 else "ferry", _rng.randf_range(0.15, 0.45))


func _clones(tmpl: Dictionary, nm: String, count: int, shadow: bool) -> Array:
	var out: Array = []
	for i in count:
		out.append(_one(tmpl, nm, shadow))
	return out


func _one(tmpl: Dictionary, nm: String, shadow: bool) -> Node3D:
	var src: MeshInstance3D = tmpl.get(nm)
	if src == null:
		push_error("BeachLife: %s has no %s" % [GLB, nm])
		var empty := Node3D.new()
		add_child(empty)
		return empty
	var m := MeshInstance3D.new()
	m.name = nm
	m.mesh = src.mesh
	for i in src.mesh.get_surface_count():
		m.set_surface_override_material(i, src.get_surface_override_material(i))
	m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	m.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	m.visible = false
	add_child(m)
	return m


func _bird(mesh: Mesh, mat: Material, size: float) -> MeshInstance3D:
	var b := MeshInstance3D.new()
	b.mesh = mesh
	b.material_override = mat
	b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	b.scale = Vector3.ONE * size
	b.visible = false
	b.set_instance_shader_parameter("glide", 0.7)
	add_child(b)
	return b


func _make_splash(i: int) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "splash_%d" % i
	p.amount = 22
	p.lifetime = 1.1
	p.one_shot = true
	p.explosiveness = 0.85
	p.emitting = false
	p.fixed_fps = 30
	p.use_fixed_seed = true
	p.seed = 240 + i
	p.visibility_aabb = AABB(Vector3(-4, -2, -4), Vector3(8, 8, 8))
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 0.35
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 28
	pm.initial_velocity_min = 2.0
	pm.initial_velocity_max = 4.2
	pm.gravity = Vector3(0, -9.8, 0)
	pm.scale_min = 0.6
	pm.scale_max = 1.4
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0.95))
	ramp.set_color(ramp.get_point_count() - 1, Color(1, 1, 1, 0))
	var gt := GradientTexture1D.new()
	gt.gradient = ramp
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.28, 0.28)
	var m := _beach._shader("beach_particle")
	m.set_shader_parameter("shape", 3)
	m.set_shader_parameter("emit", 0.35 if _night else 1.1)
	q.material = m
	p.draw_pass_1 = q
	add_child(p)
	return p


func _splash(at: Vector3) -> void:
	var p: GPUParticles3D = _splashes[_splash_i % _splashes.size()]
	_splash_i += 1
	p.position = at
	p.restart()


## The sand's height near the court (the Blender script's h_land without its small noise; valid where there are no
## dunes, |x - 8| < 13).
static func sand_y(x: float, z: float) -> float:
	var shore := -18.5 + 1.1 * sin(x * 0.06 + 1.0)
	var d := shore - z
	var beach := SEA - 0.045 * d - 0.12 * maxf(0.0, d - 3.0) - 0.02 * pow(maxf(0.0, d - 20.0), 1.3)
	var h := maxf(0.5 - absf(beach), 0.0) / 0.5
	return minf(0.0, beach) - h * h * 0.5 * 0.25


# ------------------------------------------------------------------ the scheduler

func _process(delta: float) -> void:
	_t += delta
	if _t >= _next:
		_pick()
		_next = _t + _rng.randf_range(5.0, 11.0)
	for kind in _active.keys():
		var e: Dictionary = _active[kind]
		var k := (_t - float(e["t0"])) / float(e["dur"])
		if k >= 1.0:
			call("_end_" + kind, e)
			_active.erase(kind)
		else:
			call("_run_" + kind, e, k, delta)


func _pick() -> void:
	var busy := 0
	for kind in _active:
		if not kind in SLOW:
			busy += 1
	var boat := _active.has("ferry") or _active.has("sail")
	if busy >= MAX_ACTIVE and boat:
		return
	var total := 0.0
	var pool: Array = []
	for kind in KINDS:
		var w: float = KINDS[kind][0]
		if _active.has(kind) or kind in _recent or (_night and not KINDS[kind][1]):
			continue
		if busy >= MAX_ACTIVE and not kind in SLOW:
			continue
		if kind == "coconut" and _coco_next >= _cocos.size():
			continue
		if kind == "gull" and _perches.is_empty():
			continue
		if kind in BOATS and boat:
			continue
		pool.append([kind, w])
		total += w
	if pool.is_empty():
		return
	var r := _rng.randf() * total
	for p in pool:
		r -= p[1]
		if r <= 0.0:
			_start(p[0])
			return
	_start(pool[-1][0])


func _start(kind: String, progress := 0.0) -> void:
	var e := {"t0": _t}
	call("_begin_" + kind, e)
	e["t0"] = _t - progress * float(e["dur"])
	_active[kind] = e
	_recent.append(kind)
	if _recent.size() > 3:
		_recent.pop_front()


# ------------------------------------------------------------------ crabs: across the wet sand behind the court

func _begin_crabs(e: Dictionary) -> void:
	var dir := 1.0 if _rng.randf() < 0.5 else -1.0
	var count := 1 if _rng.randf() < 0.55 else 2
	var crabs: Array = []
	for i in count:
		var z := _rng.randf_range(-15.8, -13.6) - 1.2 * i
		crabs.append({"z": z, "s": -1.6 * i, "ph": _rng.randf() * TAU, "v": _rng.randf_range(1.2, 1.7)})
	e["crabs"] = crabs
	e["dir"] = dir
	e["x0"] = -7.0 if dir > 0.0 else 25.0
	e["span"] = 32.0
	e["dur"] = 60.0  # ends early when they are across


func _run_crabs(e: Dictionary, _k: float, delta: float) -> void:
	var dir: float = e["dir"]
	var done := true
	for i in (e["crabs"] as Array).size():
		var c: Dictionary = e["crabs"][i]
		var node: Node3D = _n["crab"][i]
		# stop and go: bursts of scuttling, short pauses
		var go := clampf(sin(_t * 1.3 + c["ph"]) * 1.6 + 0.7, 0.0, 1.0)
		c["s"] = float(c["s"]) + float(c["v"]) * go * delta
		var s: float = c["s"]
		if s < 0.0 or s > float(e["span"]):
			node.visible = false
			if s < 0.0:
				done = false
			continue
		done = false
		node.visible = true
		var x: float = float(e["x0"]) + dir * s
		var z: float = c["z"]
		var bob := absf(sin(_t * 24.0 + c["ph"])) * 0.02 * go
		var b := Basis(Vector3.UP, dir * PI * 0.5 + sin(_t * 3.0 + c["ph"]) * 0.08 * go)
		node.transform = Transform3D(b, Vector3(x, sand_y(x, z) + bob, z))
	if done:
		e["t0"] = _t - float(e["dur"])  # everyone is across: finish


func _end_crabs(_e: Dictionary) -> void:
	for n in _n["crab"]:
		n.visible = false


# ------------------------------------------------------------------ dolphins: two or three leaps far out

func _begin_dolphins(e: Dictionary) -> void:
	e["dir"] = 1.0 if _rng.randf() < 0.5 else -1.0
	e["x"] = _rng.randf_range(-20.0, 20.0) + 8.0
	e["z"] = _rng.randf_range(-105.0, -70.0)
	e["jumps"] = _rng.randi_range(2, 3)
	e["two"] = _rng.randf() < 0.6
	e["period"] = 2.5
	e["dur"] = float(e["jumps"]) * 2.5 + 0.8
	e["air"] = [false, false]


func _run_dolphins(e: Dictionary, _k: float, _delta: float) -> void:
	var el := _t - float(e["t0"])
	var dir: float = e["dir"]
	for i in 2:
		var node: Node3D = _n["dolphin"][i]
		if i == 1 and not e["two"]:
			continue
		var tt := el - 0.45 * i
		var p: float = e["period"]
		var cyc := floorf(tt / p)
		var ph := fmod(tt, p) / 1.15  # 1.15 s in the air, the rest under water
		var in_air := tt >= 0.0 and cyc < float(e["jumps"]) and ph < 1.0
		var x: float = float(e["x"]) + dir * (tt * 6.5) - dir * 1.2 * i
		var z: float = float(e["z"]) + 1.5 * i
		var y := SEA
		if in_air:
			var hgt := 1.5 - 0.3 * i
			y = SEA - 0.9 + (hgt + 0.9) * 4.0 * ph * (1.0 - ph)
			# the body follows its arc: nose up leaving the water, down going in
			var slope := (hgt + 0.9) * 4.0 * (1.0 - 2.0 * ph) / (6.5 * 1.15)
			var b := Basis(Vector3.UP, 0.0 if dir > 0.0 else PI) * Basis(Vector3.BACK, atan(slope) * 1.3)
			node.transform = Transform3D(b, Vector3(x, y, z))
		node.visible = in_air
		var was: bool = e["air"][i]
		if in_air != was and tt >= 0.0:
			_splash(Vector3(x, SEA, z))
		e["air"][i] = in_air


func _end_dolphins(_e: Dictionary) -> void:
	for n in _n["dolphin"]:
		n.visible = false


# ------------------------------------------------------------------ a gull glides in, lands on a post, flies off

func _begin_gull(e: Dictionary) -> void:
	var perch: Vector3 = _perches[_rng.randi_range(0, _perches.size() - 1)]
	var side := -1.0 if _rng.randf() < 0.5 else 1.0
	e["perch"] = perch
	e["from"] = perch + Vector3(side * 26.0, 10.0, -8.0)
	e["to"] = perch + Vector3(-side * 24.0, 12.0, -14.0)
	e["look"] = _rng.randf() * TAU
	e["dur"] = 5.0 + 9.0 + 4.0


func _run_gull(e: Dictionary, _k: float, _delta: float) -> void:
	var el := _t - float(e["t0"])
	var fly: MeshInstance3D = _n["flyer"][0]
	var stand: Node3D = _n["gull"][0]
	var perch: Vector3 = e["perch"]
	if el < 5.0:
		# glide in on a curve, flare and flap the last second
		var k := el / 5.0
		var a: Vector3 = e["from"]
		var mid := a.lerp(perch, 0.6) + Vector3(0, 3.0, 4.0)
		var p := a.lerp(mid, k).lerp(mid.lerp(perch + Vector3(0, 0.35, 0), k), k)
		var ahead := a.lerp(mid, k + 0.02).lerp(mid.lerp(perch + Vector3(0, 0.35, 0), k + 0.02), k + 0.02)
		_fly_to(fly, p, ahead, 0.6 if k < 0.75 else 0.0, 0.42)
		fly.visible = true
		stand.visible = false
	elif el < 14.0:
		fly.visible = false
		stand.visible = true
		# standing: every couple of seconds a quick look about, a little hop on landing
		var s := el - 5.0
		var slot := floorf(s / 2.2)
		var look := float(e["look"]) + (fmod(slot * 0.618, 1.0) - 0.5) * 2.2
		var prev := float(e["look"]) + (fmod((slot - 1.0) * 0.618, 1.0) - 0.5) * 2.2 if slot > 0.0 else look
		var yaw := lerpf(prev, look, smoothstep(0.0, 0.2, fmod(s, 2.2)))
		var hop := maxf(0.0, sin(minf(s, 0.4) / 0.4 * PI)) * 0.08
		stand.transform = Transform3D(Basis(Vector3.UP, yaw) * Basis.from_scale(Vector3.ONE * 0.85), perch + Vector3(0, hop, 0))
	else:
		# take off: flap hard, climb away
		stand.visible = false
		var k := (el - 14.0) / 4.0
		var to: Vector3 = e["to"]
		var p := perch.lerp(to, k * k * 0.6 + k * 0.4) + Vector3(0, sin(k * PI) * 1.5, 0)
		var ahead := perch.lerp(to, minf(1.0, k + 0.03) * minf(1.0, k + 0.03) * 0.6 + (k + 0.03) * 0.4)
		_fly_to(fly, p, ahead + Vector3(0, 0.3, 0), 0.0, 0.42)
		fly.visible = true


func _fly_to(b: MeshInstance3D, p: Vector3, ahead: Vector3, glide: float, size: float) -> void:
	var dirv := ahead - p
	var basis := Basis.looking_at(dirv, Vector3.UP) if dirv.length() > 0.001 and absf(dirv.normalized().y) < 0.98 else Basis()
	b.transform = Transform3D(basis.scaled_local(Vector3.ONE * size), p)
	b.set_instance_shader_parameter("glide", glide)


func _end_gull(_e: Dictionary) -> void:
	_n["flyer"][0].visible = false
	_n["gull"][0].visible = false


# ------------------------------------------------------------------ kites over the far dunes

func _begin_kites(e: Dictionary) -> void:
	var side := -1.0 if _rng.randf() < 0.5 else 1.0
	e["c"] = Vector3(8.0 + side * 17.0, 8.5, -42.0)
	e["two"] = _rng.randf() < 0.5
	e["ph"] = _rng.randf() * TAU
	e["dur"] = _rng.randf_range(16.0, 22.0)


func _run_kites(e: Dictionary, k: float, _delta: float) -> void:
	var el := _t - float(e["t0"])
	var dur: float = e["dur"]
	var rise := smoothstep(0.0, 6.0, el) * smoothstep(dur, dur - 5.0, el)
	for i in 2:
		var node: Node3D = _n["kite"][i]
		if i == 1 and not e["two"]:
			node.visible = false
			continue
		var ph: float = float(e["ph"]) + i * 2.1
		var c: Vector3 = e["c"] + Vector3(-3.5 * i, -1.5 * i, 3.0 * i)
		# swoops: a slow figure of eight, the climb from behind the dunes and the descent at the end
		var p := c + Vector3(sin(el * 0.45 + ph) * 2.6, sin(el * 0.9 + ph) * 0.9 - (1.0 - rise) * 16.0, 0)
		var roll := sin(el * 0.45 + ph + 0.8) * 0.4
		var b := Basis(Vector3.UP, 0.15 * sin(el * 0.3 + ph)) * Basis(Vector3.BACK, roll) * Basis(Vector3.RIGHT, -0.35)
		node.transform = Transform3D(b.scaled(Vector3.ONE * 1.3), p)
		node.visible = p.y > 3.0
	if k < 0.0:
		pass


func _end_kites(_e: Dictionary) -> void:
	for n in _n["kite"]:
		n.visible = false


# ------------------------------------------------------------------ a coconut drops from a palm and rolls

func _begin_coconut(e: Dictionary) -> void:
	var i := _coco_next
	_coco_next += 1
	var top: Vector3 = _cocos[i]
	e["i"] = i
	e["p"] = top
	e["v"] = Vector3(0, 0, 0)
	e["out"] = signf(top.x - 8.0)  # it rolls away from the court
	e["spin"] = 0.0
	e["dur"] = 7.0


func _run_coconut(e: Dictionary, _k: float, delta: float) -> void:
	var node: Node3D = _n["coconut"][e["i"]]
	node.visible = true
	var p: Vector3 = e["p"]
	var v: Vector3 = e["v"]
	var r := 0.16
	v.y -= 9.8 * delta
	p += v * delta
	var ground := sand_y(p.x, p.z) + r
	if p.y < ground:
		p.y = ground
		if v.y < -1.2:
			# a bounce: it loses most of its speed and kicks sideways, away from the court
			v.y = -v.y * 0.32
			v.x = float(e["out"]) * 0.9 + v.x * 0.5
			v.z = 0.25
		else:
			v.y = 0.0
			v.x *= maxf(0.0, 1.0 - 1.6 * delta)  # rolling to a stop in the sand
			v.z *= maxf(0.0, 1.0 - 1.6 * delta)
	e["spin"] = float(e["spin"]) - v.x / r * delta
	e["p"] = p
	e["v"] = v
	node.transform = Transform3D(Basis(Vector3.BACK, e["spin"]) * Basis(Vector3.RIGHT, 0.4), p)


func _end_coconut(_e: Dictionary) -> void:
	pass  # it stays where it rolled


# ------------------------------------------------------------------ a turtle heads down to the sea

func _begin_turtle(e: Dictionary) -> void:
	var left := _rng.randf() < 0.5
	e["a"] = Vector3(-4.3, 0, -12.6) if left else Vector3(19.2, 0, -13.4)
	e["b"] = e["a"] + Vector3(-0.6 if left else 0.9, 0, -8.5)
	e["s"] = 0.0
	e["dur"] = 60.0


func _run_turtle(e: Dictionary, _k: float, delta: float) -> void:
	var node: Node3D = _n["turtle"][0]
	# flipper strokes: a surge, a pause
	var stroke := maxf(0.0, sin(_t * 2.6))
	e["s"] = float(e["s"]) + (0.1 + 0.5 * stroke) * delta
	var a: Vector3 = e["a"]
	var b: Vector3 = e["b"]
	var k: float = float(e["s"]) / a.distance_to(b)
	if k >= 1.0:
		e["t0"] = _t - float(e["dur"])
		node.visible = false
		return
	var p := a.lerp(b, k)
	var y := sand_y(p.x, p.z)
	var dirv := (b - a).normalized()
	var yaw := atan2(-dirv.z, dirv.x) + sin(_t * 2.6) * 0.06
	var bs := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, sin(_t * 2.6 + 0.5) * 0.06) * Basis(Vector3.BACK, 0.05)
	# into the water: it slips under the surface
	node.transform = Transform3D(bs, Vector3(p.x, y + 0.02 * stroke, p.z))
	node.visible = y > SEA - 0.35


func _end_turtle(_e: Dictionary) -> void:
	_n["turtle"][0].visible = false


# ------------------------------------------------------------------ pelicans in a line, low over the water

func _begin_pelicans(e: Dictionary) -> void:
	e["dir"] = 1.0 if _rng.randf() < 0.5 else -1.0
	e["z"] = _rng.randf_range(-70.0, -45.0)
	e["y"] = _rng.randf_range(5.0, 8.0)
	e["n"] = _rng.randi_range(3, 5)
	e["dur"] = 20.0


func _run_pelicans(e: Dictionary, k: float, _delta: float) -> void:
	var dir: float = e["dir"]
	for i in 5:
		var b: MeshInstance3D = _n["pelican"][i]
		if i >= int(e["n"]):
			b.visible = false
			continue
		var x := 8.0 - dir * 70.0 + dir * 140.0 * k - dir * 3.2 * i
		var p := Vector3(x, float(e["y"]) + 0.5 * i + sin(_t * 0.8 + i) * 0.25, float(e["z"]) + 1.8 * i)
		# they flap a few beats in turn, then glide
		var flap := 0.0 if fmod(_t * 0.35 + i * 0.12, 1.0) < 0.3 else 0.85
		_fly_to(b, p, p + Vector3(dir, 0, 0), flap, 0.75)
		b.visible = true


func _end_pelicans(_e: Dictionary) -> void:
	for b in _n["pelican"]:
		b.visible = false


# ------------------------------------------------------------------ boats across the horizon

func _begin_ferry(e: Dictionary) -> void:
	e["dir"] = 1.0 if _rng.randf() < 0.5 else -1.0
	e["z"] = _rng.randf_range(-420.0, -360.0)
	e["dur"] = 100.0


func _run_ferry(e: Dictionary, k: float, _delta: float) -> void:
	_boat(_n["ferry"][0], e, k, 330.0, 0.05, 0.015)


func _end_ferry(_e: Dictionary) -> void:
	_n["ferry"][0].visible = false


func _begin_sail(e: Dictionary) -> void:
	e["dir"] = 1.0 if _rng.randf() < 0.5 else -1.0
	e["z"] = _rng.randf_range(-210.0, -150.0)
	e["dur"] = 110.0


func _run_sail(e: Dictionary, k: float, _delta: float) -> void:
	_boat(_n["sail"][0], e, k, 150.0, 0.14, 0.06)


func _end_sail(_e: Dictionary) -> void:
	_n["sail"][0].visible = false


func _boat(node: Node3D, e: Dictionary, k: float, half: float, bob: float, heel: float) -> void:
	var dir: float = e["dir"]
	var x := 8.0 - dir * half + dir * 2.0 * half * k
	var b := Basis(Vector3.UP, 0.0 if dir > 0.0 else PI) * Basis(Vector3.RIGHT, 0.12 * heel / 0.06 + sin(_t * 0.9) * heel)
	node.transform = Transform3D(b, Vector3(x, SEA + sin(_t * 1.1) * bob, e["z"]))
	node.visible = true
