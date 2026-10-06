"""Marble race (vertical Short) in Blender.

Two passes so the race can be rendered in parallel chunks:
  RACE_VARIANT=n blender -b -P race.py -- --sim     run the rigid-body race -> sim_<TAG>_v<n>.npz
  (pick.py keeps the most exciting variant as sim_<TAG>.npz)
  blender -b -P race.py -- --out fr --start a --end b [--res 1080] [--samples 16] [--frames a,b,c]
                                                    replay the saved race and render frames
The course layout is seeded by RACE_CFG (one course per video), the variant only changes the start order."""
import bpy, math, os, sys, random
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import theme as T  # noqa: E402

FPS = 30
SIM_SECONDS = 75
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


SIM = "--sim" in argv
OUT = arg("--out", os.path.join(HERE, "frames_" + T.TAG))
RESX = int(arg("--res", "540"))
SAMPLES = int(arg("--samples", "12"))
SIMFILE = os.path.join(HERE, f"sim_{T.TAG}.npz")
if SIM:
    VARIANT = int(os.environ.get("RACE_VARIANT", "0"))
else:
    VARIANT = int(np.load(SIMFILE)["variant"])

R = 0.16          # marble radius
HALF_W = 2.0      # course half width
DEPTH = 0.17      # half depth of the channel (single file in depth)
N = T.N

rnd = random.Random(T.SEED)              # course
vrnd = random.Random(T.SEED * 101 + VARIANT)  # start order etc.

# ---------------------------------------------------------------- scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = SIM_SECONDS * FPS


def mat(name, col, rough=0.35, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.03
    return m


def box(name, loc, size, rot_y=0.0, m=None, phys="box", visible=True, bounce=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.rotation_euler = (0, rot_y, 0)
    if m:
        o.data.materials.append(m)
    o.hide_render = not visible
    o["phys"] = phys
    if bounce is not None:
        o["bounce"] = bounce
    return o


def cyl_y(name, x, z, r, m, bounce=None, length=2 * DEPTH + 0.1):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length, location=(x, 0, z), rotation=(math.pi / 2, 0, 0),
                                        vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    o["phys"] = "cyl"
    if bounce is not None:
        o["bounce"] = bounce
    return o


# palette varies per video
HUES = [((0.02, 0.06, 0.28), (0.32, 0.03, 0.3), (0.12, 0.03, 0.38)),
        ((0.01, 0.16, 0.2), (0.02, 0.05, 0.25), (0.0, 0.2, 0.15)),
        ((0.25, 0.04, 0.08), (0.08, 0.02, 0.22), (0.3, 0.1, 0.02)),
        ((0.03, 0.03, 0.06), (0.1, 0.02, 0.25), (0.02, 0.1, 0.3))]
PAL = HUES[T.SEED % len(HUES)]
track_m = mat("track", (0.92, 0.94, 1.0), 0.18, coat=0.6)
NEON = [(0.0, 0.8, 1.0), (1.0, 0.1, 0.7), (0.5, 1.0, 0.1), (1.0, 0.6, 0.0)]
rnd.shuffle(NEON)
edge_ms = [mat(f"edge{i}", c, 0.3, emit=6.0) for i, c in enumerate(NEON[:3])]
peg_m = mat("peg", (1.0, 0.75, 0.2), 0.2, emit=1.2, coat=0.8)
bumper_m = mat("bumper", NEON[3], 0.15, emit=2.5, coat=1.0)
wall_m = mat("wall", PAL[0], 0.6)
_nt = wall_m.node_tree
_tc = _nt.nodes.new("ShaderNodeTexCoord")
_sep = _nt.nodes.new("ShaderNodeSeparateXYZ")
_mth = _nt.nodes.new("ShaderNodeMath"); _mth.operation = "PINGPONG"; _mth.inputs[1].default_value = 6.0
_cr = _nt.nodes.new("ShaderNodeValToRGB")
_cr.color_ramp.elements[0].color = (*PAL[0], 1)
_cr.color_ramp.elements[1].color = (*PAL[1], 1)
_mid = _cr.color_ramp.elements.new(0.5); _mid.color = (*PAL[2], 1)
_mul = _nt.nodes.new("ShaderNodeMath"); _mul.operation = "DIVIDE"; _mul.inputs[1].default_value = 6.0
_nt.links.new(_tc.outputs["Object"], _sep.inputs[0])
_nt.links.new(_sep.outputs["Z"], _mth.inputs[0])
_nt.links.new(_mth.outputs[0], _mul.inputs[0])
_nt.links.new(_mul.outputs[0], _cr.inputs["Fac"])
_bsdf = _nt.nodes["Principled BSDF"]
_nt.links.new(_cr.outputs["Color"], _bsdf.inputs["Base Color"])
_nt.links.new(_cr.outputs["Color"], _bsdf.inputs["Emission Color"])
_bsdf.inputs["Emission Strength"].default_value = 0.35
spin_m = mat("spin", (1.0, 0.1, 0.55), 0.25, emit=0.8, coat=0.8)
gate_m = mat("gate", (1.0, 0.85, 0.1), 0.3, emit=1.5)

statics = []
ramps = []
spinners = []
k_edge = [0]


def ramp(xa, za, xb, zb):
    """Sloped plank from (xa,za) to (xb,zb) with a glowing front edge."""
    cx, cz = (xa + xb) / 2, (za + zb) / 2
    ln = math.hypot(xb - xa, zb - za)
    ang = -math.atan2(zb - za, xb - xa)
    statics.append(box(f"ramp{len(ramps)}", (cx, 0, cz - 0.05), (ln, 2 * DEPTH + 0.1, 0.1), ang, track_m))
    box(f"ramp{len(ramps)}_edge", (cx, -DEPTH - 0.06, cz - 0.02), (ln, 0.03, 0.05), ang, edge_ms[k_edge[0] % 3], phys="")
    k_edge[0] += 1
    ramps.append((xa, za, xb, zb))


# ---------------------------------------------------------------- course
GAP = 0.62
DROP = 0.42
z = 0.0

# start: marbles held in a grid above a V hopper; a trap door opens and they all pour through the neck
HOP_TOP = 0.0
NECK = 0.62
cols = 5
for sx in (-1, 1):
    xa, za = sx * HALF_W, HOP_TOP
    xb, zb = sx * NECK / 2, HOP_TOP - 1.3
    cx, cz = (xa + xb) / 2, (za + zb) / 2
    ln = math.hypot(xb - xa, zb - za)
    ang = -math.atan2(zb - za, xb - xa)
    statics.append(box(f"hop{sx}", (cx, 0, cz), (ln, 2 * DEPTH + 0.1, 0.08), ang, track_m))
    box(f"hop{sx}_e", (cx, -DEPTH - 0.06, cz), (ln, 0.03, 0.05), ang, edge_ms[0], phys="")
TRAP_Z = HOP_TOP + 0.12
start_xy = []
for i in range(N):
    r_, c_ = divmod(i, cols)
    start_xy.append(((c_ - (cols - 1) / 2) * 0.37 + (0.09 if r_ % 2 else 0), TRAP_Z + 0.06 + R + r_ * 0.36))
z = HOP_TOP - 1.3 - 0.55
d = 1 if rnd.random() < 0.5 else -1

features = ["plinko", "bumpers", "funnel", "spinner", "bumps"]
rnd.shuffle(features)
features = features[:5]
if "plinko" not in features and "bumpers" not in features:
    features[0] = "plinko"
seq = []
for f_ in features:
    seq += ["ramp", f_]
seq += ["ramp", "finish"]

for sec in seq:
    if sec in ("ramp", "finish", "bumps"):
        xa, xb = (-HALF_W, HALF_W - GAP) if d > 0 else (HALF_W, -HALF_W + GAP)
        drop = DROP * (0.3 if sec == "finish" else rnd.uniform(0.9, 1.15))
        za, zb = z, z - drop
        ramp(xa, za, xb, zb)
        if sec == "bumps":
            # low bumps, only after the marbles have picked up speed
            for j in range(3):
                u = 0.45 + 0.16 * j + rnd.uniform(-0.03, 0.03)
                bx, bz = xa + (xb - xa) * u, za + (zb - za) * u
                statics.append(cyl_y(f"bump{len(statics)}", bx, bz - 0.035, 0.065, peg_m))
        z = zb - 0.85
        last_d = d
        d = -d
        continue
    if sec == "plinko":
        top = z + 0.2
        rows = rnd.randint(5, 7)
        for r_ in range(rows):
            # every gap (peg-peg, peg-wall) is wider than a marble so nothing can wedge
            x = -HALF_W + (0.46 if r_ % 2 == 0 else 0.72)
            while x <= HALF_W - 0.46:
                statics.append(cyl_y(f"peg{len(statics)}", x + rnd.uniform(-0.03, 0.03), top - r_ * 0.46, 0.06, peg_m))
                x += 0.52
        z = top - rows * 0.46 - 0.3
        d = 1 if rnd.random() < 0.5 else -1
    elif sec == "bumpers":
        # pinball field: big springy round bumpers
        top = z + 0.1
        pts = []
        tries = 0
        while len(pts) < 6 and tries < 400:
            tries += 1
            x_, z_ = rnd.uniform(-HALF_W + 0.64, HALF_W - 0.64), rnd.uniform(top - 2.2, top - 0.3)
            if all(math.hypot(x_ - a, z_ - b) > 0.95 for a, b in pts):
                pts.append((x_, z_))
        for x_, z_ in pts:
            statics.append(cyl_y(f"bumper{len(statics)}", x_, z_, rnd.uniform(0.17, 0.24), bumper_m, bounce=1.0))
        z = top - 2.75
        d = 1 if rnd.random() < 0.5 else -1
    elif sec == "funnel":
        # V bottleneck: everyone jams into a narrow neck
        top = z + 0.15
        neck = rnd.uniform(0.42, 0.5)
        cx_n = rnd.uniform(-0.5, 0.5)
        for sx in (-1, 1):
            xa, za = sx * HALF_W, top
            xb, zb = cx_n + sx * neck / 2, top - 1.0
            cx, cz = (xa + xb) / 2, (za + zb) / 2
            ln = math.hypot(xb - xa, zb - za)
            ang = -math.atan2(zb - za, xb - xa)
            statics.append(box(f"fun{len(statics)}", (cx, 0, cz), (ln, 2 * DEPTH + 0.1, 0.08), ang, track_m))
            box(f"fun{len(statics)}_e", (cx, -DEPTH - 0.06, cz), (ln, 0.03, 0.05), ang, edge_ms[1], phys="")
        z = top - 1.0 - 0.6
        d = 1 if rnd.random() < 0.5 else -1
    elif sec == "spinner":
        # marbles fall off the previous ramp's low end onto the wheel
        sx = (HALF_W - 0.75) * last_d
        sz = z - 0.55
        spinners.append((sx, sz))
        z = sz - 1.3
        d = -last_d if rnd.random() < 0.5 else last_d

FIN = ramps[-1]
FIN_DIR = 1 if FIN[2] > FIN[0] else -1
FIN_X = FIN[2] - FIN_DIR * 0.35
FIN_Z = FIN[1]
TRAY_Z = FIN[3] - 1.15
BOTTOM = TRAY_Z - 0.5

H = -BOTTOM + 4
for sx in (-1, 1):
    statics.append(box(f"side{sx}", (sx * (HALF_W + 0.08), 0, -H / 2 + 2.5), (0.16, 2 * DEPTH + 0.1, H), 0, track_m))
statics.append(box("back", (0, DEPTH + 0.08, -H / 2 + 2.5), (2 * HALF_W + 0.4, 0.16, H), 0, wall_m))
statics.append(box("front", (0, -DEPTH - 0.08, -H / 2 + 2.5), (2 * HALF_W + 0.4, 0.16, H), 0, None, visible=False))
statics.append(box("tray", (0, 0, TRAY_Z - 0.05), (2 * HALF_W, 2 * DEPTH + 0.1, 0.1), 0, track_m))
gate = box("gate", (0, 0, TRAP_Z), (2 * HALF_W, 2 * DEPTH + 0.1, 0.08), 0, gate_m)
GATE_T = 4.6  # seconds (pick-your-entrant intro, then 3-2-1)

spin_objs = []
for si, (sx, sz) in enumerate(spinners):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.17, depth=2 * DEPTH + 0.06, location=(0, 0, 0),
                                        rotation=(math.pi / 2, 0, 0), vertices=32)
    hub = bpy.context.object
    parts = [hub]
    nb = 5
    for j in range(nb):
        a = j * 2 * math.pi / nb
        bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 0.42, 0, math.sin(a) * 0.42))
        p = bpy.context.object
        p.scale = (0.54, 2 * DEPTH + 0.06, 0.06)
        p.rotation_euler = (0, -a, 0)
        parts.append(p)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = hub
    bpy.ops.object.join()
    so = bpy.context.object
    so.name = f"spinner{si}"
    so.location = (sx, 0, sz)
    so.data.materials.append(spin_m)
    so["phys"] = "mesh"
    # turn so the side the marbles land on moves down (never scoops them back up)
    so["rate"] = (0.9 + rnd.uniform(-0.2, 0.3)) * (-1 if sx < 0 else 1)
    spin_objs.append(so)

# marbles
order = list(range(N))
vrnd.shuffle(order)
marbles = []
FLAG_DIR = os.path.join(HERE, "flags")
for slot, ei in enumerate(order):
    x, zz = start_xy[slot]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=48, ring_count=24,
                                         location=(x + vrnd.uniform(-0.02, 0.02), vrnd.uniform(-0.005, 0.005), zz))
    o = bpy.context.object
    o.name = f"m{ei}"
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new(f"mm{ei}")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    col = [c / 255 for c in T.RGB[ei]]
    if T.THEME == "countries":
        img = bpy.data.images.load(os.path.join(FLAG_DIR, T.ENTRANTS[ei] + ".png"))
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = img
        nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 0.25
    else:
        tex = nt.nodes.new("ShaderNodeTexWave")
        tex.inputs["Scale"].default_value = 2.2
        tex.inputs["Distortion"].default_value = 9.0
        ramp_ = nt.nodes.new("ShaderNodeValToRGB")
        ramp_.color_ramp.elements[0].color = (*[c * 0.85 for c in col], 1)
        ramp_.color_ramp.elements[1].color = (*[min(1, c * 0.7 + 0.35) for c in col], 1)
        nt.links.new(tex.outputs["Fac"], ramp_.inputs["Fac"])
        nt.links.new(ramp_.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = 0.6
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    o.data.materials.append(m)
    # flag faces the camera at the start
    o.rotation_euler = (0, 0, math.radians(90) + vrnd.uniform(-0.3, 0.3))
    marbles.append((ei, o))

NF = SIM_SECONDS * FPS

# ---------------------------------------------------------------- pass 1: physics
if SIM:
    bpy.ops.rigidbody.world_add()
    rw = scene.rigidbody_world
    rw.substeps_per_frame = 30
    rw.solver_iterations = 25
    rw.point_cache.frame_start = 1
    rw.point_cache.frame_end = NF
    # light, lively marbles: stronger gravity makes the big scene move like small glass marbles
    scene.use_gravity = True
    scene.gravity = (0, 0, -9.81 * 1.9)
    bpy.ops.object.select_all(action="DESELECT")
    for o in statics + [gate] + spin_objs:
        if not o.get("phys"):
            continue
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.rigidbody.object_add(type="PASSIVE")
        rb = o.rigid_body
        rb.collision_shape = {"cyl": "CYLINDER", "mesh": "MESH"}.get(o["phys"], "BOX")
        rb.friction = 0.3
        rb.restitution = o.get("bounce", 0.62)
        rb.collision_margin = 0.002
        o.select_set(False)
    for o in [gate] + spin_objs:
        o.rigid_body.kinematic = True
    gf = int(GATE_T * FPS)
    gate.keyframe_insert("location", frame=gf)
    gate.location.x += 2 * HALF_W + 0.3
    gate.keyframe_insert("location", frame=gf + 5)
    for so in spin_objs:
        so.rotation_mode = "XYZ"
        so.keyframe_insert("rotation_euler", frame=1)
        so.rotation_euler = (0, so["rate"] * NF / FPS * 2 * math.pi, 0)
        so.keyframe_insert("rotation_euler", frame=NF + 1)
        for fc in so.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    for ei, o in marbles:
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.rigidbody.object_add(type="ACTIVE")
        rb = o.rigid_body
        rb.collision_shape = "SPHERE"
        rb.mass = 0.08
        rb.friction = 0.3
        rb.restitution = 0.9
        rb.linear_damping = 0.01
        rb.angular_damping = 0.04
        rb.collision_margin = 0.002
        rb.use_deactivation = False
        rb.kinematic = True
        rb.keyframe_insert("kinematic", frame=gf + 1)
        rb.kinematic = False
        rb.keyframe_insert("kinematic", frame=gf + 2)
        o.select_set(False)
    pos = np.zeros((NF, N, 3), np.float32)
    rot = np.zeros((NF, N, 4), np.float32)
    for f in range(1, NF + 1):
        scene.frame_set(f)
        for ei, o in marbles:
            mw = o.matrix_world
            pos[f - 1, ei] = mw.translation
            rot[f - 1, ei] = mw.to_quaternion()
    out = os.path.join(HERE, f"sim_{T.TAG}_v{VARIANT}.npz")
    np.savez(out, pos=pos, rot=rot, fin=np.array([FIN_X, FIN_Z, FIN_DIR]), gate_t=GATE_T, variant=VARIANT,
             top_z=TRAP_Z, tray_z=TRAY_Z)
    print("saved", out)
    sys.exit(0)

# ---------------------------------------------------------------- pass 2: replay + render
S = np.load(SIMFILE)
POS, ROT = S["pos"], S["rot"]
from race_logic import race_info  # noqa: E402
INFO = race_info(POS, FIN_X, FIN_Z, FIN_DIR, TRAP_Z, TRAY_Z)
END_F = INFO["end_frame"]
scene.frame_end = END_F

# chequered finish post
fin_m = bpy.data.materials.new("fin")
fin_m.use_nodes = True
_ch = fin_m.node_tree.nodes.new("ShaderNodeTexChecker")
_ch.inputs["Scale"].default_value = 12
_ch.inputs["Color1"].default_value = (1, 1, 1, 1)
_ch.inputs["Color2"].default_value = (0.02, 0.02, 0.02, 1)
_fb = fin_m.node_tree.nodes["Principled BSDF"]
fin_m.node_tree.links.new(_ch.outputs["Color"], _fb.inputs["Base Color"])
fin_m.node_tree.links.new(_ch.outputs["Color"], _fb.inputs["Emission Color"])
_fb.inputs["Emission Strength"].default_value = 0.6
box("finish_line", (FIN_X, -DEPTH + 0.02, FIN_Z + 0.7), (0.09, 0.04, 1.3), 0, fin_m, phys="")

world = scene.world or bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.02, 0.015, 0.06, 1)
bg.inputs["Strength"].default_value = 1.0

bpy.ops.object.light_add(type="AREA", location=(0, -6, 3))
key = bpy.context.object
key.data.energy = 900
key.data.size = 8
key.rotation_euler = (math.radians(80), 0, 0)
bpy.ops.object.light_add(type="SUN", location=(0, -3, 5))
sun = bpy.context.object
sun.data.energy = 2.2
sun.data.angle = math.radians(25)
sun.rotation_euler = (math.radians(35), math.radians(-15), 0)
for sx_ in (-1, 1):
    box(f"rail{sx_}", (sx_ * (HALF_W + 0.08), -DEPTH - 0.07, -H / 2 + 2.5), (0.05, 0.04, H), 0,
        edge_ms[0 if sx_ < 0 else 1], phys="")

bpy.ops.object.camera_add()
cam = bpy.context.object
scene.camera = cam
cam.data.lens = 36
cam.rotation_euler = (math.radians(90), 0, 0)

for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.render.resolution_x = RESX
scene.render.resolution_y = RESX * 16 // 9
ee = scene.eevee
ee.taa_render_samples = SAMPLES
for k_, v in (("use_shadows", True), ("use_gtao", True), ("gtao_distance", 0.4), ("use_raytracing", False)):
    try:
        setattr(ee, k_, v)
    except Exception:
        pass
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.35
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 93
scene.render.use_overwrite = False
scene.use_nodes = True
ct = scene.node_tree
rl = ct.nodes.get("Render Layers") or ct.nodes.new("CompositorNodeRLayers")
comp = ct.nodes.get("Composite") or ct.nodes.new("CompositorNodeComposite")
gl = ct.nodes.new("CompositorNodeGlare")
gl.glare_type = "FOG_GLOW"
try:
    gl.threshold = 1.2
    gl.size = 7
    gl.mix = -0.5
except Exception:
    pass
ct.links.new(rl.outputs["Image"], gl.inputs["Image"])
ct.links.new(gl.outputs["Image"], comp.inputs["Image"])

CAMZ = INFO["cam_z"]


def interp(arr, t):
    i = max(0.0, min(len(arr) - 1.001, t))
    a = int(i)
    return arr[a] * (1 - (i - a)) + arr[a + 1] * (i - a)


def on_frame(sc, *a):
    fl = sc.frame_current + sc.frame_subframe - 1
    for ei, o in marbles:
        o.location = Vector(interp(POS[:, ei], fl))
        o.rotation_mode = "QUATERNION"
        q = ROT[min(len(ROT) - 1, int(round(fl))), ei]
        o.rotation_quaternion = tuple(q)
    t = (fl + 1) / FPS
    gate.location.x = (2 * HALF_W + 0.3) * max(0.0, min(1.0, (t - GATE_T) * 6))
    for so in spin_objs:
        so.rotation_euler = (0, so["rate"] * fl / FPS * 2 * math.pi, 0)
    cam.location = (0, -8.2, interp(CAMZ, fl))


bpy.app.handlers.frame_change_pre.append(on_frame)
os.makedirs(OUT, exist_ok=True)
frames = arg("--frames")
if frames:
    for f in [int(x) for x in frames.split(",")]:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(OUT, f"f{f:05d}.jpg")
        bpy.ops.render.render(write_still=True)
else:
    scene.frame_start = int(arg("--start", "1"))
    scene.frame_end = min(int(arg("--end", str(END_F))), END_F)
    scene.render.filepath = os.path.join(OUT, "f#####")
    bpy.ops.render.render(animation=True)
