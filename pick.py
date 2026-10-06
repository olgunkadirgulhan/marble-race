"""Keep the most exciting simulated variant: sim_<TAG>_v*.npz -> sim_<TAG>.npz"""
import glob, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import theme as T  # noqa: E402
from race_logic import load, FPS  # noqa: E402

best = None
for p in sorted(glob.glob(os.path.join(HERE, f"sim_{T.TAG}_v*.npz"))):
    S, I = load(p)
    race_s = (I["winner_f"] - float(S["gate_t"]) * FPS) / FPS
    ok = I["all_done"] and 9 <= race_s <= 40
    score = I["lead_changes"] * 2.0 + max(0.0, 2.0 - I["margin"]) * 3 - abs(race_s - 18) * 0.15
    print(os.path.basename(p), "ok" if ok else "REJECT", f"race {race_s:.1f}s changes {I['lead_changes']} "
          f"margin {I['margin']:.2f}s score {score:.2f}")
    if ok and (best is None or score > best[0]):
        best = (score, p)
if best is None:
    sys.exit("no usable variant")
shutil.copy(best[1], os.path.join(HERE, f"sim_{T.TAG}.npz"))
print("picked", os.path.basename(best[1]))
