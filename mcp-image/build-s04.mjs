// S04 v1 生成脚本：从 DNA-v4.md 提取负向块，拼装虹桥提示词并写 jobs
import fs from "node:fs";
const dna = fs.readFileSync("E:/UserData/xdrhh/.openclaw/workspace/media-forge/DNA-v4.md", "utf8");
const start = dna.indexOf("`do not use");
const end = dna.indexOf("watermarks.", start);
if (start < 0 || end < 0) { console.error("NEG block not found"); process.exit(1); }
const NEG = dna.slice(start + 1, end + "watermarks.".length);
const p =
  "9:16 immersive vertical frame, ultra-monumental scale, low side view at human height. " +
  "A slender vermilion-and-gilt bridge extends beyond both frame edges across a boundless sea of luminous clouds, " +
  "spanning between two floating mountain islands crowned with jade pines, waterfalls pouring from the island cliffs into the void; " +
  "the small moon-white robed traveler walks at its center, under five percent frame height, full back, one leftward wind on robe and sash — scale anchor only, never portrait. " +
  "Fixed five layers: near bridge rail cropped at the frame edge, bridge span with the traveler, the two islands, smaller distant pavilions, terminal cloud sea and high sky. " +
  "Cloud voids beneath the bridge and sky keep about forty-five percent content-bearing air, all edges railing-free. " +
  "Single warm antique-gold key light from upper right rakes the bridge deck, misty blue-gray shadow in the cloud depth, one restrained star-flare at the backlit edge only. " +
  "Restrained palette of ivory, vermilion, antique gold and mineral teal; weathered lacquer and aged timber materials; " +
  "distant islands dissolving into cloud haze while keeping color. " +
  "cinematic fantasy film still, monumental scale, refined Eastern production design, physically plausible light, intricate material detail. " + NEG;
const jobs = [{ id: "S04-v1", prompt: p, size: "1024x1824", quality: "high", output_dir: "v4-keyframes/S04-hongqiao" }];
fs.writeFileSync("C:/Users/xdrhh/.zcode/mcp-image/jobs-s04v1.json", JSON.stringify(jobs, null, 1));
console.log("S04 v1 prompt len:", p.length);
