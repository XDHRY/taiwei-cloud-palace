# -*- coding: utf-8 -*-
"""太微云宫 billboard 白底抠图管线。

把 textures_wukong/ 下白底 isolated 贴图转成 RGBA：
- alpha = (255 - 亮度) * gain，低噪阈值截断
- 白底去混（un-premultiply against white），防白边
产物写入 textures_wukong/billboards/，供 generator billboard_material 直读。
"""
import os
import numpy as np
from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "taiwei_video", "textures_wukong")
DST = os.path.join(SRC, "billboards")
os.makedirs(DST, exist_ok=True)

JOBS = {
    "tex-lotus-leaf-pad.png": 1.00,
    "tex-peach-petal-cluster.png": 1.00,
    "tex-reed-tassel.png": 1.00,
    "tex-bamboo-leaf-cluster.png": 1.00,
    "tex-pine-needle-cluster.png": 1.00,
    "tex-distant-mountain-mist.png": 1.00,
    "tex-wispy-mist-sheet.png": 2.60,
    "tex-volume-cumulus-cloud.png": 2.20,
    "tex-night-milkyway-nebula.png": 1.20,
}

for name, gain in JOBS.items():
    src = os.path.join(SRC, name)
    if not os.path.isfile(src):
        print("MISS", name)
        continue
    im = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32)
    lum = im.max(axis=2)  # 白底≈255；彩色主体 max 通道低于 255
    a = np.clip((255.0 - lum) * gain, 0, 255)
    a[a < 14] = 0
    # 白底去混：c' = (c - (255 - a)) * 255 / a
    af = a / 255.0
    safe = np.maximum(af, 1e-3)[..., None]
    unmix = np.clip((im - (255.0 - a)[..., None]) / safe, 0, 255)
    out = np.dstack([np.where(a[..., None] > 0, unmix, im), a]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(os.path.join(DST, name))
    cov = float((a > 0).mean())
    print("OK", name, "coverage=%.3f" % cov)
