# -*- coding: utf-8 -*-
"""Convert CTRL/SCENE diag EXRs to PNG with per-channel stats (RGB vs alpha split)."""
import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2
import numpy as np

SRC = r"D:\UnrealProjects\TaiWei_Cinema\Saved\DiagShots"
OUT = r"E:\UserData\xdrhh\.openclaw\workspace\ue_pipeline\research\ctrl_views"
os.makedirs(OUT, exist_ok=True)

files = ["CTRL_UnlitLit_ldr", "CTRL_UnlitLit_basecolor", "CTRL_UnlitLit_hdr",
         "SCENE_Main_ldr", "SCENE_Main_basecolor"]
for f in files:
    p = os.path.join(SRC, f)
    if not os.path.exists(p):
        print(f"{f}: MISSING")
        continue
    img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"{f}: cv2 read FAILED")
        continue
    if img.ndim == 3 and img.shape[2] >= 3:
        b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        a = img[:, :, 3] if img.shape[2] == 4 else None
        rgb_max = max(float(b.max()), float(g.max()), float(r.max()))
        rgb_mean = float((b.mean() + g.mean() + r.mean()) / 3.0)
        line = f"{f}: shape={img.shape} RGB[max={rgb_max:.4f} mean={rgb_mean:.4f}]"
        if a is not None:
            line += f" A[min={float(a.min()):.3f} max={float(a.max()):.3f} mean={float(a.mean()):.3f}]"
        line += f" B(mean={float(b.mean()):.4f}) G(mean={float(g.mean()):.4f}) R(mean={float(r.mean()):.4f})"
        print(line)
        rgb = img[:, :, :3]
    else:
        print(f"{f}: shape={img.shape} gray min={img.min()} max={img.max()} mean={img.mean()}")
        rgb = img
    out = np.clip(rgb, 0.0, 1.0)
    out = np.power(out, 1.0 / 2.2)
    out8 = (out * 255.0).astype(np.uint8)
    dst = os.path.join(OUT, f + "_view.png")
    cv2.imwrite(dst, out8)
    print(f"  -> {dst}")
