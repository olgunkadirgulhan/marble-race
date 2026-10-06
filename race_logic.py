"""Race bookkeeping shared by the renderer, the variant picker and the HUD pass (numpy only)."""
import numpy as np

FPS = 30
VIEW_H = 8.2  # visible height of the camera at its distance (metres)


def race_info(pos, fin_x, fin_z, fin_dir, top_z, tray_z):
    nf, n, _ = pos.shape
    x, z = pos[:, :, 0], pos[:, :, 2]
    crossed = ((x - fin_x) * fin_dir > 0) & (z < fin_z + 0.6) & (z > fin_z - 1.0)
    fin = np.full(n, 10 ** 9)
    for j in range(n):
        idx = np.nonzero(crossed[:, j])[0]
        if len(idx):
            fin[j] = idx[0]
    order_final = [int(j) for j in np.argsort(fin, kind="stable")]
    winner_f = int(fin[order_final[0]])
    if winner_f >= 10 ** 9:
        winner_f = nf - 1
    done = [f for f in fin if f < 10 ** 9]
    all_f = max(done) if len(done) == n else nf - 1
    end = int(min(nf, min(all_f + 1.0 * FPS, winner_f + 6 * FPS) + 1.5 * FPS))

    # live ranking: finished marbles by finish time, others by how far down they are
    prog = np.maximum.accumulate(-z, axis=0)
    rank = np.zeros((nf, n), int)
    for f in range(nf):
        key = [(0, fin[j]) if fin[j] <= f else (1, -prog[f, j]) for j in range(n)]
        rank[f] = sorted(range(n), key=lambda j: key[j])

    # camera: follow the leader (lowest unfinished marble), critically damped
    top_cam, bot_cam = top_z - 1.4, tray_z + 3.6
    cam = np.zeros(nf)
    c, v = top_cam, 0.0
    w = 3.2
    for f in range(nf):
        alive = [j for j in range(n) if fin[j] > f]
        lead = min(z[f, j] for j in alive) if alive else fin_z
        tgt = min(top_cam, max(bot_cam, lead + 1.6))
        a = w * w * (tgt - c) - 2 * w * v
        v += a / FPS
        c += v / FPS
        cam[f] = c

    # excitement: how often the leader changes (held >= 0.5 s), how close the finish is
    leaders = rank[:winner_f, 0]
    changes, cur, held = 0, leaders[0] if len(leaders) else -1, 0
    for f in range(len(leaders)):
        if leaders[f] != cur:
            held += 1
            if held >= FPS:
                changes += 1
                cur = leaders[f]
                held = 0
        else:
            held = 0
    margin = (sorted(done)[1] - sorted(done)[0]) / FPS if len(done) > 1 else 99
    return dict(finish=fin, order=order_final, winner_f=winner_f, end_frame=end, rank=rank, cam_z=cam,
                all_done=len(done) == n, lead_changes=changes, margin=margin)


def load(path):
    S = np.load(path)
    fx, fz, fd = S["fin"]
    return S, race_info(S["pos"], fx, fz, fd, float(S["top_z"]), float(S["tray_z"]))
