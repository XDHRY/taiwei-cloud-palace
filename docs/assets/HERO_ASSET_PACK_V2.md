# 太微云宫 Hero Asset Pack V2

本资产包是 PR #3 的第二阶段程序化构件库，目标是在不触碰受保护主场景的前提下，提供可重复生成、可独立复用、可被 Blender 主场景生成器直接实例化的 Hero/Midpoly 构件。

## 资产规模

- 24 个独立资产根
- 9 个统一材质族
- Blender 4.2.23 LTS
- deterministic geometry，无 LLM 运行依赖
- 每个资产带 `asset_id`、`category`、`quality_tier`、`reusable`、`protected_scene_safe`
- Git LFS 保存最终 `.blend`
- GitHub Actions 真机生成、重新打开校验并输出 4 张视觉审查图

## 资产目录

### 屋脊与屋面
1. TW_HERO_CHIWEN_01 — 鸱吻·英雄级轮廓
2. TW_HERO_BEAST_DRAGON_01 — 屋脊走兽·龙
3. TW_HERO_BEAST_PHOENIX_01 — 屋脊走兽·凤
4. TW_HERO_BEAST_LION_01 — 屋脊走兽·狮
5. TW_HERO_BEAST_QILIN_01 — 屋脊走兽·麒麟
6. TW_HERO_BEAST_TIANMA_01 — 屋脊走兽·天马
7. TW_HERO_BEAST_HAIMA_01 — 屋脊走兽·海马
8. TW_HERO_EAVES_TILE_01 — 兽面瓦当与滴水
9. TW_HERO_WIND_BELL_01 — 檐角风铎

### 木构与门窗
10. TW_HERO_DOUGONG_01 — 单翘斗拱·英雄级
11. TW_HERO_CORNER_DOUGONG_01 — 转角铺作·英雄级
12. TW_HERO_GESHAN_DOOR_01 — 格扇门·如意云纹
13. TW_HERO_LATTICE_WINDOW_01 — 槛窗·冰裂纹
14. TW_HERO_CAISSON_01 — 八角藻井·莲心

### 石作
15. TW_HERO_COLUMN_BASE_01 — 覆莲柱础
16. TW_HERO_HUABIAO_01 — 盘龙华表
17. TW_HERO_SUTRA_PILLAR_01 — 八面经幢
18. TW_HERO_BALUSTRADE_01 — 白石栏杆·云龙栏板

### 宫廷陈设
19. TW_HERO_LANTERN_01 — 六角宫灯·描金
20. TW_HERO_CENSER_01 — 兽耳青铜香炉
21. TW_HERO_PLAQUE_01 — 宫殿匾额·云龙边
22. TW_HERO_SCREEN_01 — 山水座屏
23. TW_HERO_BRONZE_CRANE_01 — 青铜仙鹤
24. TW_HERO_LOTUS_PEDESTAL_01 — 重瓣莲花座

## 质量分层

本轮标记为 `hero_midpoly_reusable`，含义是：

- 可以作为主场景中近/中景构件继续使用；
- 结构、轮廓和材质分区不再只是纯占位；
- 仍允许后续增加高频雕刻、UV/PBR 贴图、历史形制校正和 LOD；
- 不把当前程序化几何冒充为最终雕塑级高模。

## 验证门槛

构建必须同时满足：

1. 24 个资产根全部存在；
2. 每项至少 5 个 Mesh/Curve 几何子对象；
3. 每个根均为 `reusable=true`；
4. 每个根均为 `protected_scene_safe=true`；
5. 9 个声明材质必须全部被实际使用；
6. 生成的 blend 必须能由 Blender 4.2.23 再次打开；
7. `scenes/**` 在构建前后逐文件 SHA256 完全一致；
8. `scenes` 与 `blender/src` 不允许出现工作树差异；
9. 自动生成 4 张 1600×900 视觉审查图；
10. 最终 blend 通过 Git LFS 入库。

## 下一轮精细化重点

优先级仍以画面识别度为准：

- 屋脊走兽与鸱吻：提升头部、鳞甲、鬃毛、角、爪和剪影差异；
- 斗拱：继续校正斗、栱、昂、翘的真实承托关系；
- 格扇/槛窗：把规则格网推进到更复杂的传统棂花纹样；
- 匾额：由占位字形替换为真正书法/浮雕字接口；
- 石作：补石材微破损、雨蚀、积灰与边缘磨损；
- 金属陈设：补铜锈、金属划痕、铸造纹理和更精细的兽面纹。
