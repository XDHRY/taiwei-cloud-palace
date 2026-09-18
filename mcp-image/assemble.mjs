// Path B 组装：12 镜 Ken Burns → xfade 链式溶解 → 竖屏成片
// 用法: node assemble.mjs seg <start> <end>   （生成段，1-based 闭区间）
//       node assemble.mjs film                 （拼片）
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const FF = "D:/ffmpeg/bin/ffmpeg.exe";
const KF = "E:/UserData/xdrhh/.openclaw/workspace/image-runs/v4-keyframes";
const OUT = "E:/UserData/xdrhh/.openclaw/workspace/media-forge/film";
fs.mkdirSync(OUT, { recursive: true });

// 每镜运镜（单轴、慢；R1 安全运镜纪律）: zin | zout | panLR | panRL | tiltUp | tiltDn
const SHOTS = [
  { id: "S01", dir: "S01-yunjing", motion: "zin" },
  { id: "S02", dir: "../s02-attack/v2-paifang-frontal", motion: "zout" },
  { id: "S03", dir: "../../image-runs/s02-attack/v1-P1-verbatim", motion: "tiltUp" }, // S03=P1 玉阶
  { id: "S04", dir: "S04-hongqiao", motion: "panLR" },
  { id: "S05", dir: "S05-tianjie", motion: "zin" },
  { id: "S06", dir: "S06-yaochi", motion: "zout" },
  { id: "S07", dir: "S07-jinque", motion: "tiltUp" },
  { id: "S08", dir: "S08-shenguang", motion: "zin" },
  { id: "S09", dir: "S09-xingcha", motion: "panLR" },
  { id: "S10", dir: "S10-qiongtai", motion: "zin" },
  { id: "S11", dir: "S11-jinding", motion: "panLR" },
  { id: "S12", dir: "S12-yuedong", motion: "zin" },
];
const SRC = (s) => path.resolve(KF, s.dir, "img-01.png");
const DUR = 6, FPS = 30, W = 1080, H = 1920, FADE = 1.2;

function motionExpr(m) {
  const zIn = "min(zoom+0.0012,1.25)";
  const zOut = "max(1.25-0.0012*on,1.0)";
  const zHold = "1.18";
  const cx = "iw/2-(iw/zoom/2)", cy = "ih/2-(ih/zoom/2)";
  switch (m) {
    case "zin": return { z: zIn, x: cx, y: cy };
    case "zout": return { z: zOut, x: cx, y: cy };
    case "panLR": return { z: zHold, x: `(iw-iw/zoom)*on/${DUR * FPS - 1}`, y: cy };
    case "panRL": return { z: zHold, x: `(iw-iw/zoom)*(1-on/${DUR * FPS - 1})`, y: cy };
    case "tiltUp": return { z: zHold, x: cx, y: `(ih-ih/zoom)*(1-on/${DUR * FPS - 1})` };
    case "tiltDn": return { z: zHold, x: cx, y: `(ih-ih/zoom)*on/${DUR * FPS - 1}` };
  }
}

function makeSegment(i) {
  const s = SHOTS[i];
  const src = SRC(s);
  if (!fs.existsSync(src)) { console.error("MISSING:", src); process.exit(1); }
  const m = motionExpr(s.motion);
  const out = path.join(OUT, `seg${String(i + 1).padStart(2, "0")}.mp4`);
  const vf = `scale=2160:3840,zoompan=z='${m.z}':x='${m.x}':y='${m.y}':d=${DUR * FPS}:s=${W}x${H}:fps=${FPS},format=yuv420p`;
  console.log("seg", s.id, s.motion);
  execFileSync(FF, ["-y", "-v", "error", "-loop", "1", "-i", src, "-vf", vf, "-t", String(DUR), "-r", String(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-movflags", "+faststart", out], { stdio: "inherit" });
  return out;
}

function makeFilm() {
  const segs = SHOTS.map((_, i) => path.join(OUT, `seg${String(i + 1).padStart(2, "0")}.mp4`));
  for (const s of segs) if (!fs.existsSync(s)) { console.error("MISSING SEG:", s); process.exit(1); }
  const inputs = segs.flatMap((s) => ["-i", s]);
  let fc = "", prev = "[0:v]", offset = 0;
  for (let k = 1; k < segs.length; k++) {
    offset += DUR - FADE;
    const outL = k === segs.length - 1 ? "[vout]" : `[v${k}]`;
    fc += `${prev}[${k}:v]xfade=transition=fade:duration=${FADE}:offset=${offset.toFixed(2)}${outL};`;
    prev = outL;
  }
  fc = fc.slice(0, -1);
  const out = path.join(OUT, "tiangong-tour-v1.mp4");
  console.log("xfade chain, total ≈", (DUR + (segs.length - 1) * (DUR - FADE)).toFixed(1), "s");
  execFileSync(FF, ["-y", "-v", "error", ...inputs, "-filter_complex", fc, "-map", "[vout]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], { stdio: "inherit" });
  console.log("FILM:", out);
}

const mode = process.argv[2];
if (mode === "seg") {
  const a = Number(process.argv[3]) - 1, b = Number(process.argv[4]);
  for (let i = a; i < b && i < SHOTS.length; i++) makeSegment(i);
} else if (mode === "film") {
  makeFilm();
} else {
  console.log("usage: node assemble.mjs seg <start> <end> | film");
}
