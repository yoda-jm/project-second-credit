"""Shared kit for the skinned creatures (Whisker Alley's animals, the Fruitburrow gardener): organic bodies grown from
metaballs and tubes into one watertight mesh (voxel-fused, relaxed), coloured with vertex or face-corner colours
(soft fur patterns, sharp clothing seams), an armature with IK legs, heat weights blended across neighbouring bones,
rigid accessories, and keyed animations (Bezier key poses or per-frame procedural cycles) exported as one glTF
animation per action. Deterministic; output CC BY-SA 4.0; provenance: this script.

Conventions: the creature faces -Y, +Z is up, its left side is +X ("L" bones). Pose rotations are Euler XYZ degrees
about the ARMATURE axes, applied at the bone's head and carried along by its parents: +X pitches a forward bone's tip
down (and swings a hanging limb backwards), +Z turns a forward bone to the creature's left, +Y rolls. Locations are
offsets in armature axes from the rest position.
"""
import bpy, bmesh, math, os, time
from mathutils import Vector, Matrix, Euler

FPS = 30
MB_K = 1.0 / 0.5707  # metaball element radius per unit of surface radius (threshold 0.6, stiffness 2)
MATS = {}
_T0 = time.time()


def log(*a):
    print("[kit %6.1fs]" % (time.time() - _T0), *a, flush=True)


# ------------------------------------------------------------------ scene and materials
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.actions, bpy.data.meshes, bpy.data.armatures, bpy.data.metaballs):
        for x in list(coll):
            coll.remove(x)
    bpy.context.scene.render.fps = FPS


def mat(name, color, rough=0.6, coat=0.0, emit=0.0, sheen=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    MATS[name] = m
    return m


def vc_mat(name, rough=0.8, sheen=0.4, coat=0.0):
    """A material whose base colour comes from the mesh's vertex colours ("Col"). Its name ends in "_vc": the game
    views switch on vertex_color_use_as_albedo for such materials (Godot's glTF import leaves it off)."""
    name = name if name.endswith("_vc") else name + "_vc"
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
    MATS[name] = m
    return m


def ss(x, a, b):
    """Smooth step of x from a (0) to b (1); a > b flips it."""
    return smooth01((x - a) / (b - a)) if b != a else float(x >= a)


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def paint_vc(o, fn, material):
    """Vertex colours from fn(position, normal) -> linear (r, g, b), shown through a vc_mat material."""
    o.data.materials.clear()
    o.data.materials.append(material)
    ca = o.data.color_attributes.get("Col") or o.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    mw, m3 = o.matrix_world, o.matrix_world.to_3x3()
    flat = []
    for v in o.data.vertices:
        flat += (*fn(mw @ v.co, (m3 @ v.normal).normalized()), 1.0)
    ca.data.foreach_set("color", flat)  # one bulk write: element-wise writes are very slow
    return o


def cut(o, planes):
    """Cuts the mesh along planes [(point, normal, region(centre) or None)], so colour seams can follow straight
    edges (a waistband, a cuff) instead of the triangles' zigzag."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for co, no, region in planes:
        faces = [f for f in bm.faces if region is None or region(f.calc_center_median())]
        edges = {e for f in faces for e in f.edges}
        verts = {v for f in faces for v in f.verts}
        bmesh.ops.bisect_plane(bm, geom=list(verts) + list(edges) + faces, dist=0.0004, plane_co=Vector(co),
                               plane_no=Vector(no).normalized())
    bm.to_mesh(o.data)
    bm.free()
    return o


def paint_faces(o, fn, material, smooth=None):
    """Face-corner colours: each face takes fn(face centre, normal), so seams are sharp; where smooth(centre) is
    true, corners take fn at their own vertex instead (soft blends: blush, hair)."""
    o.data.materials.clear()
    o.data.materials.append(material)
    me = o.data
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    flat = [0.0] * (len(me.loops) * 4)
    for p in me.polygons:
        c = p.center
        soft = smooth is not None and smooth(c)
        col = None if soft else fn(c, p.normal)
        for li in p.loop_indices:
            if soft:
                v = me.vertices[me.loops[li].vertex_index]
                col = fn(v.co, v.normal)
            flat[li * 4:li * 4 + 4] = (*col, 1.0)
    ca.data.foreach_set("color", flat)
    return o


def active():
    return bpy.context.active_object


def select_only(objs, act=None):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for x in objs:
        x.select_set(True)
    bpy.context.view_layer.objects.active = act or objs[0]


# ------------------------------------------------------------------ organic bodies
def _quat_x_to(d):
    return Vector((1, 0, 0)).rotation_difference(Vector(d).normalized())


class Blob:
    """A metaball body. Radii are the wanted SURFACE radii of each element alone; overlapping elements blend and
    swell a little, which gives soft fillets at the joints."""

    count = 0

    def __init__(self, name, res=0.006):
        Blob.count += 1
        name = "%s%d" % (name.replace(".", "_"), Blob.count)  # unique base names: no metaball families
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = self.mb.render_resolution = res
        self.mb.threshold = 0.6
        self.obj = bpy.data.objects.new(name, self.mb)
        bpy.context.scene.collection.objects.link(self.obj)

    def _el(self, kind, co, neg, stiff):
        e = self.mb.elements.new(type=kind)
        e.co = co
        e.use_negative = neg
        e.stiffness = stiff
        return e

    def ball(self, c, r, neg=False, stiff=2.0):
        self._el("BALL", c, neg, stiff).radius = r * MB_K
        return self

    def ell(self, c, rx, ry, rz, rot=(0, 0, 0), neg=False, stiff=2.0):
        """An ellipsoid with semi-axes rx, ry, rz, turned by rot (Euler degrees)."""
        e = self._el("ELLIPSOID", c, neg, stiff)
        s = min(rx, ry, rz)
        e.radius = s * MB_K * 0.99
        e.size_x, e.size_y, e.size_z = rx / s, ry / s, rz / s
        e.rotation = Euler([math.radians(a) for a in rot]).to_quaternion()
        return self

    def cap(self, a, b, r, neg=False, stiff=2.0):
        a, b = Vector(a), Vector(b)
        e = self._el("CAPSULE", (a + b) / 2, neg, stiff)
        e.radius = r * MB_K
        e.size_x = max(0.0005, (b - a).length / 2)
        e.rotation = _quat_x_to(b - a)
        return self

    def mesh(self, name, faces=None, smooth=2):
        """Converts to a mesh, merges, optionally decimates to about `faces` faces and relaxes the surface."""
        select_only([self.obj])
        bpy.ops.object.convert(target="MESH")
        o = active()
        o.name = name
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
        bm.to_mesh(o.data)
        bm.free()
        if faces and len(o.data.polygons) > faces:
            d = o.modifiers.new("dec", "DECIMATE")
            d.ratio = faces / len(o.data.polygons)
            d.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=d.name)
        if smooth:
            s = o.modifiers.new("relax", "SMOOTH")
            s.factor = 0.5
            s.iterations = smooth
            bpy.ops.object.modifier_apply(modifier=s.name)
        bpy.ops.object.shade_smooth()
        return o


def tube(points, radii, name="tube", res=6, bevel_res=6, smooth=True):
    """A smooth tapered tube through the points (a tail, a limb), with a radius per point and rounded ends."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = True
    cu.resolution_u = res
    sp = cu.splines.new("BEZIER" if smooth else "POLY")
    pts = [Vector(p) for p in points]
    if smooth:
        sp.bezier_points.add(len(pts) - 1)
        for bp, p, r in zip(sp.bezier_points, pts, radii):
            bp.co = p
            bp.radius = r
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    else:
        sp.points.add(len(pts) - 1)
        for bp, p, r in zip(sp.points, pts, radii):
            bp.co = (*p, 1)
            bp.radius = r
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    select_only([o])
    bpy.ops.object.convert(target="MESH")
    o = active()
    # round ends: a ball at each end
    for p, r in ((pts[0], radii[0]), (pts[-1], radii[-1])):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=p)
        e = active()
        select_only([o, e], o)
        bpy.ops.object.join()
        o = active()
    return o


def fuse(objs, name, voxel=0.005, smooth=6, faces=None):
    """Unites meshes (and metaball blobs) into one watertight skin: voxel remesh, relaxed for soft fillets, then
    decimated to about `faces` quads' worth of triangles."""
    ms = []
    for x in objs:
        if isinstance(x, Blob):
            select_only([x.obj])
            bpy.ops.object.convert(target="MESH")
            ms.append(active())
        else:
            ms.append(x)
    select_only(ms)
    bpy.ops.object.join()
    o = active()
    o.name = name
    r = o.modifiers.new("vox", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = voxel
    r.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier=r.name)
    if smooth:
        s = o.modifiers.new("relax", "LAPLACIANSMOOTH")
        s.iterations = smooth
        s.lambda_factor = 1.0
        s.use_volume_preserve = True
        s.use_normalized = True
        bpy.ops.object.modifier_apply(modifier=s.name)
    if faces and len(o.data.polygons) > faces:
        d = o.modifiers.new("dec", "DECIMATE")
        d.ratio = faces / len(o.data.polygons)
        bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_smooth()
    log("fused", name, len(o.data.vertices), "verts")
    return o


_BVH = {}


def surface(o, origin, direction):
    """Where a ray from `origin` first meets the mesh: (point, normal), or (None, None). One BVH per mesh."""
    from mathutils.bvhtree import BVHTree
    key = (o.name, len(o.data.vertices))
    if key not in _BVH:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        _BVH[key] = BVHTree.FromBMesh(bm)
        bm.free()
    loc, nor, _, _ = _BVH[key].ray_cast(Vector(origin), Vector(direction).normalized())
    return (loc, nor) if loc is not None else (None, None)


def collar(skin, centre, tilt, minor, bone, material, snug=0.35, segs=48):
    """A torus fitted round a neck: the ring's radius is the neck's mean radius (rays in the ring's plane).
    tilt: degrees about X; the ring's axis is (0, -sin tilt, cos tilt), so a neck leaning forward-up wants tilt > 0.
    Returns (torus, ring radius, rotation)."""
    R = Euler((math.radians(tilt), 0, 0)).to_matrix()
    c = Vector(centre)
    ds = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        d = R @ Vector((math.cos(a), math.sin(a), 0))
        hit, _ = surface(skin, c, d)
        if hit is not None:
            ds.append((hit - c).length)
    ds.sort()
    med = ds[len(ds) // 2]
    ds = [d for d in ds if d < med * 1.5]
    rad = sum(ds) / len(ds) + minor * snug
    bpy.ops.mesh.primitive_torus_add(major_radius=rad, minor_radius=minor, location=c, rotation=(math.radians(tilt), 0, 0),
                                     major_segments=segs, minor_segments=12)
    return _tag(active(), bone, material), rad, R


def paint(o, rules):
    """rules: [(material, predicate(centre, normal) -> bool)], first match wins; rules[0] is the default."""
    o.data.materials.clear()
    for m, _ in rules:
        o.data.materials.append(m)
    mw = o.matrix_world
    for p in o.data.polygons:
        c, n = mw @ p.center, (mw.to_3x3() @ p.normal).normalized()
        p.material_index = 0
        for i, (_, pred) in enumerate(rules):
            if i and pred(c, n):
                p.material_index = i
                break
    return o


# ------------------------------------------------------------------ rigid accessories (tagged with their bone)
def _tag(o, bone, material, smooth=True):
    o.data.materials.clear()
    o.data.materials.append(material)
    o["bone"] = bone
    if smooth:
        select_only([o])
        bpy.ops.object.shade_smooth()
    return o


def sphere(r, loc, bone, material, scale=(1, 1, 1), segs=None, rings=None, rot=(0, 0, 0)):
    if segs is None:  # small parts need few facets
        segs = 12 if r < 0.012 else (16 if r < 0.03 else 20)
        rings = segs * 2 // 3
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc,
                                         rotation=[math.radians(a) for a in rot])
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return _tag(o, bone, material)


def cone(r1, r2, depth, loc, bone, material, rot=(0, 0, 0), verts=12, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc,
                                    rotation=[math.radians(a) for a in rot])
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return _tag(o, bone, material)


def cyl(r, depth, loc, bone, material, rot=(0, 0, 0), r2=None, verts=20, bevel=0.25, scale=(1, 1, 1)):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc,
                                            rotation=[math.radians(a) for a in rot])
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc,
                                        rotation=[math.radians(a) for a in rot])
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = min(r, depth) * bevel
        b.segments = 3
        bpy.ops.object.modifier_apply(modifier=b.name)
    return _tag(o, bone, material)


def rod(r, a, b, bone, material, r2=None, verts=10, caps=True):
    """A rounded rod from a to b (whiskers, handles, straps)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    r2 = r if r2 is None else r2
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = active()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    parts = [o]
    if caps:
        for p, rr in ((a, r), (b, r2)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=verts, ring_count=6, radius=rr, location=p)
            parts.append(active())
        select_only(parts)
        bpy.ops.object.join()
    return _tag(active(), bone, material)


# ------------------------------------------------------------------ armature
class Rig:
    def __init__(self, name, bones):
        """bones: {name: (head, tail, parent, flags)}; flags is a set of "nodeform", "connect"."""
        bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
        self.obj = active()
        self.obj.name = name + "_rig"
        self.obj.data.name = name + "_armature"
        eb = self.obj.data.edit_bones
        eb.remove(eb[0])
        self.nodeform = set()
        for bname, spec in bones.items():
            h, t, p = spec[:3]
            flags = spec[3] if len(spec) > 3 else set()
            b = eb.new(bname)
            b.head, b.tail = h, t
            d = (Vector(t) - Vector(h)).normalized()
            z = Vector((1, 0, 0)).cross(d) if abs(d.x) < 0.8 else Vector((0, 0, 1))
            b.align_roll(z)
            if p:
                b.parent = eb[p]
                b.use_connect = "connect" in flags
            if "nodeform" in flags:
                self.nodeform.add(bname)
        bpy.ops.object.mode_set(mode="OBJECT")
        self.pb = self.obj.pose.bones
        for b in self.pb:
            b.rotation_mode = "QUATERNION"
            b.bone.use_deform = b.name not in self.nodeform
        self._rest3 = {b.name: b.bone.matrix_local.to_3x3() for b in self.pb}
        self._prevq = {}
        self.ik_bones = []  # (bone, constraint name, tag)

    def ik(self, bone, target, chain, hinge=(), copy_rot=None, stiff=None, tag=None):
        """An IK chain ending at `bone`, reaching for `target`'s head. hinge: bones limited to their local X
        (the sagittal plane). copy_rot: a bone that copies the target's orientation (a paw kept flat)."""
        c = self.pb[bone].constraints.new("IK")
        c.name = "IK"
        c.target = self.obj
        c.subtarget = target
        c.chain_count = chain
        self.ik_bones.append((bone, "IK", tag))
        for h in hinge:
            self.pb[h].lock_ik_y = self.pb[h].lock_ik_z = True
        for b, s in (stiff or {}).items():
            self.pb[b].ik_stiffness_x = s
        if copy_rot:
            cr = self.pb[copy_rot].constraints.new("COPY_ROTATION")
            cr.name = "IKROT"
            cr.target = self.obj
            cr.subtarget = target
            self.ik_bones.append((copy_rot, "IKROT", tag))

    def rest_head(self, b):
        return self.pb[b].bone.head_local.copy()

    def rest_tail(self, b):
        return self.pb[b].bone.tail_local.copy()

    # ---------------------------------------------------------------- posing and keying
    def set_pose(self, pose):
        """pose: {bone: (rx, ry, rz)}, {"@bone": (dx, dy, dz)} location, {"%bone": (sx, sy, sz)} scale,
        {"ik": 0..1 or {tag: 0..1}} IK weight (default 1)."""
        for b in self.pb:
            b.rotation_quaternion = (1, 0, 0, 0)
            b.location = (0, 0, 0)
            b.scale = (1, 1, 1)
        for k, v in pose.items():
            if k == "ik":
                continue
            if k[0] == "@":
                self.pb[k[1:]].location = self._rest3[k[1:]].inverted() @ Vector(v)
            elif k[0] == "%":
                self.pb[k[1:]].scale = v
            else:
                B = self._rest3[k]
                R = Euler([math.radians(a) for a in v], "XYZ").to_matrix()
                self.pb[k].rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()
        w = pose.get("ik", 1.0)
        for bone, cname, tag in self.ik_bones:
            self.pb[bone].constraints[cname].influence = w.get(tag, 1.0) if isinstance(w, dict) else w

    def head_of(self, pose, bone):
        """Where `bone`'s head sits (armature space) in the given pose, before IK: to plant feet under joints."""
        pose = dict(pose)
        pose["ik"] = 0.0
        self.set_pose(pose)
        bpy.context.view_layer.update()
        return self.pb[bone].head.copy()

    def key(self, frame):
        for b in self.pb:
            q = b.rotation_quaternion.copy()
            p = self._prevq.get(b.name)
            if p is not None and p.dot(q) < 0:
                q.negate()
                b.rotation_quaternion = q
            self._prevq[b.name] = q
            b.keyframe_insert("rotation_quaternion", frame=frame)
            b.keyframe_insert("location", frame=frame)
            b.keyframe_insert("scale", frame=frame)
        for bone, cname, _ in self.ik_bones:
            self.pb[bone].constraints[cname].keyframe_insert("influence", frame=frame)

    def _begin(self, name):
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        self.obj.animation_data_create()
        self.obj.animation_data.action = act
        self._prevq = {}
        return act

    def _end(self, act, loop):
        ad = self.obj.animation_data
        curves = []
        try:
            for layer in act.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        curves += list(bag.fcurves)
        except AttributeError:
            curves = list(act.fcurves)
        for fc in curves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            if loop:
                fc.modifiers.new("CYCLES")
            fc.update()
        log("action", act.name)
        tr = ad.nla_tracks.new()
        tr.name = act.name
        tr.strips.new(act.name, int(act.frame_range[0]), act)
        ad.action = None

    def poses(self, name, frames, loop=False):
        """Key poses at the given frames with smooth Bezier curves. For a loop, the last frame repeats the first."""
        act = self._begin(name)
        fs = sorted(frames)
        if loop:
            frames = dict(frames)
            frames[fs[-1]] = frames[fs[0]]
        for f in fs:
            self.set_pose(frames[f])
            self.key(f)
        self._end(act, loop)

    def cycle(self, name, n, fn, loop=True, step=1):
        """A procedural action: fn(t) -> pose for t in [0, 1] over n frames (frames 1 .. n + 1)."""
        act = self._begin(name)
        f = 0
        while f <= n:
            self.set_pose(fn(f / n))
            self.key(1 + f)
            f += step
        if (f - step) != n:
            self.set_pose(fn(1.0))
            self.key(1 + n)
        self._end(act, loop)


# ------------------------------------------------------------------ skinning
def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
    return (p - (a + ab * t)).length


def skin(body, rig, smooth_iter=3, smooth_fac=0.5, limit=4, exclude=None):
    """Heat weights from the deforming bones, relaxed across neighbouring vertices, at most `limit` per vertex.
    exclude: {bone: predicate(co)} vertices where a bone must not pull (e.g. a leg on the belly)."""
    arm = rig.obj
    select_only([body, arm], arm)
    log("heat weights...")
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    log("heat weights done")
    me = body.data
    groups = {g.index: g.name for g in body.vertex_groups}
    W = [dict() for _ in me.vertices]
    for v in me.vertices:
        for g in v.groups:
            if g.weight > 1e-4:
                W[v.index][groups[g.group]] = g.weight
    deform = [b for b in rig.pb if b.bone.use_deform]
    segs = {b.name: (b.bone.head_local, b.bone.tail_local) for b in deform}
    # holes in the heat solution: nearest bones by distance
    for v in me.vertices:
        if not W[v.index]:
            ds = sorted((_seg_dist(v.co, *segs[n]), n) for n in segs)
            d0 = ds[0][0] + 1e-4
            W[v.index] = {n: (d0 / (d + 1e-4)) ** 4 for d, n in ds[:3]}
    if exclude:
        for v in me.vertices:
            for bn, pred in exclude.items():
                if bn in W[v.index] and pred(v.co):
                    del W[v.index][bn]
            if not W[v.index]:
                ds = sorted((_seg_dist(v.co, *segs[n]), n) for n in segs if not (n in exclude and exclude[n](v.co)))
                W[v.index] = {ds[0][1]: 1.0}
    # relax: average with the neighbours
    nbr = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nbr[a].append(b)
        nbr[b].append(a)
    for _ in range(smooth_iter):
        new = []
        for i, w in enumerate(W):
            acc = dict()
            for n, x in w.items():
                acc[n] = acc.get(n, 0.0) + x * (1 - smooth_fac)
            if nbr[i]:
                k = smooth_fac / len(nbr[i])
                for j in nbr[i]:
                    for n, x in W[j].items():
                        acc[n] = acc.get(n, 0.0) + x * k
            new.append(acc)
        W = new
    for g in list(body.vertex_groups):
        body.vertex_groups.remove(g)
    vg = {b.name: body.vertex_groups.new(name=b.name) for b in rig.pb}
    log("weights relaxed")
    for i, w in enumerate(W):
        top = sorted(w.items(), key=lambda kv: -kv[1])[:limit]
        tot = sum(x for _, x in top) or 1.0
        for n, x in top:
            if x / tot > 0.01:
                vg[n].add([i], x / tot, "REPLACE")
    return body


def assemble(name, body, rig, parts):
    """Joins the rigid accessories (fully weighted to their bone) into the skinned body: one mesh per character."""
    for o in parts:
        vg = o.vertex_groups.new(name=o["bone"])
        vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    select_only([body] + parts, body)
    bpy.ops.object.join()
    body = active()
    body.name = name
    body.data.name = name
    for m in list(body.modifiers):
        body.modifiers.remove(m)
    mod = body.modifiers.new("rig", "ARMATURE")
    mod.object = rig.obj
    body.parent = rig.obj
    body.matrix_parent_inverse = Matrix.Identity(4)
    for b in rig.pb:  # the rigid bones deform their parts
        b.bone.use_deform = True
    for uv in list(body.data.uv_layers):  # untextured: no UVs to carry
        body.data.uv_layers.remove(uv)
    return body


def export(name, rig, body, out_dir):
    log("export...")
    select_only([rig.obj, body], rig.obj)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_optimize_animation_size=True)
    print("exported", name, len(body.data.vertices), "verts", len(body.data.polygons), "faces", len(rig.pb), "bones")


# ------------------------------------------------------------------ helpers
def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)
