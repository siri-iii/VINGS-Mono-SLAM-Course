# VINGS-Mono 复现计划 v2

> **v2 改动要点**：
> - 时间盘子压到 **15 天**
> - 硬件 = AutoDL **RTX 4090**（去掉硬件焦虑）
> - 两个可选项（手机端 + 同济校园自采）**都必须高质量完成**
> - 任务按 **4 个独立子领域** 切，每人一块，PPT 各自讲各自的
> - 不复用去年 CV 课的 3DGS app

论文：Wu et al., *VINGS-Mono: Visual-Inertial Gaussian Splatting Monocular SLAM in Large Scenes*, TRO 2025
官方仓库：<https://github.com/Fudan-MAGIC-Lab/VINGS-Mono>

---

## 0. 任务目标

| 课程要求 | 状态 |
| --- | --- |
| 在自己电脑/服务器上复现 VINGS-Mono | **必做 — 力求精彩** |
| 在手机上复现 | **必做 — 优质完成** |
| 用同济校园自采数据跑 | **必做 — 优质完成** |

---

## 1. 论文 5 大模块（PPT 主线）

每位组员主讲其中 1–2 个模块，配合自己的实验：

1. **VIO Front End**（Sec. IV）— DROID-SLAM DBA + IMU 因子图 → **Person A**
2. **2D Gaussian Map**（Sec. V）— Score Manager / Sample Rasterizer / Pose Refinement → **Person B**
3. **NVS Loop Closure**（Sec. VI）— LightGlue 匹配 + 渲染验证 + Gaussian-Pose 配对 → **Person C**
4. **Dynamic Eraser**（Sec. VII）— FastSAM mask × 重渲染损失 → **Person C**
5. **System & Application**（Sec. VIII + Mobile App）— 实地部署 + 校园数据 → **Person D**

---

## 2. 4 人任务包（**均衡分工 + 各自可独立答辩**）

> 每人分到的总工作量约 **15 人天**，对应 PPT 4–5 分钟讲解。

### Person A — 前端 & 系统部署（"基础设施"）

**PPT 主题**："**视觉惯性前端：稠密 BA + 因子图融合**"

| 责任 | 具体内容 |
| --- | --- |
| 部署 | AutoDL 4090 环境搭建（Python 3.9.19 + CUDA 11.8 + PyTorch 2.0），编译 GTSAM (vio 分支)、2DGS rasterizer、Sample Rasterizer 三个 CUDA 扩展，**做成镜像快照供 B/C/D 复用** |
| 模块讲解 | DROID-SLAM 的 RAFT 相关性 + Dense BA（论文式 1-5）；IMU 预积分因子（论文式 6-8）；深度协方差（论文式 9） |
| 实验 1 | **VO 对比**（论文表 II）：在 Waymo Scene01 跑纯 mono；与 DROID-SLAM、ORB-SLAM3 对比 ATE |
| 实验 2 | **VIO 对比**（论文表 III）：在 KITTI Odom 07 同时跑 mono-only 和 mono+IMU；记录 trel / rrel |
| 交付物 | `docs/SETUP.md`（环境踩坑记）+ `results/frontend/`（轨迹文件 + 指标表）+ AutoDL 镜像 ID |

### Person B — 2D 高斯建图（"核心方法"，工作量最重 → 拿主创署名）

**PPT 主题**："**2D Gaussian 高效建图：分数管理 + 采样光栅化 + 多帧位姿优化**"

| 责任 | 具体内容 |
| --- | --- |
| 模块讲解 | 在线建图流程（Sec. V-A，论文式 10-12）+ Score Manager（Sec. V-B，Algo. 1）+ Sample Rasterizer（Sec. V-C，图 3）+ Single-to-Multi Pose Refinement（Sec. V-D，式 14） |
| 实验 1 | **Hotel demo + Hierarchical-SmallCity demo 完整跑通**（论文表 II / V 的对应行） |
| 实验 2 | **Score Manager 消融**（论文表 VII）：在 ScanNet-0106 + Waymo-Scene13 上跑 5 组阈值（0 / 0.8 / 12.8 / 25.6 / 102.4），记录 Gaussian 数量 + PSNR |
| 实验 3 | **Sample Rasterizer profiling**（论文图 11）：对比原版 2DGS / Taming3DGS / 我们的 Sample Rasterizer 三种反传策略的时间和 PSNR |
| 实验 4 | **Pose Refinement 消融**（论文表 VIII）：3 种策略 × 3 个场景 = 9 组实验 |
| 交付物 | `docs/ABLATION.md` + `results/mapping/` + 1 段 2 分钟的 SmallCity BEV 建图过程录屏 |

### Person C — 回环 + 动态 + 长序列（"鲁棒性"）

**PPT 主题**："**大场景一致性：NVS 回环检测 + 动态物体擦除**"

| 责任 | 具体内容 |
| --- | --- |
| 模块讲解 | NVS Loop Closure 三步走（特征匹配 + PnP + 渲染验证，论文图 4） + Loop Correction（Gaussian-Pose 配对 + 一次性更新，论文式 15） + Dynamic Eraser（FastSAM + 重渲染损失，论文式 16） |
| 实验 1 | **KITTI Odom 08（5177 帧，3.2 km）完整跑完**：长序列稳定性验证 + 触发并展示回环效果（论文图 10 复现） |
| 实验 2 | **回环开/关对比**：在同一序列上分别跑开闭环 / 不开闭环，对比 ATE 漂移 |
| 实验 3 | **Dynamic Eraser 消融**（论文表 IV）：在 BONN dynamic 数据集 4 个序列上跑"开/关"，记录 ATE |
| 实验 4 | **TSDF mesh 导出**：在 Waymo Scene01 上跑 + 导出 mesh + 用 CloudCompare / Meshlab 出渲染图（论文图 9 复现） |
| 交付物 | `results/loop/`（轨迹 + BEV 截图）+ `results/dynamic/`（BONN 结果表）+ 1 段 1 分钟回环纠正前后对比的录屏 |

### Person D — 实地应用（"两个可选项 + 报告"）

**PPT 主题**："**实地落地：同济校园建图 + 手机端实时 SLAM**"

| 责任 | 具体内容 |
| --- | --- |
| **可选 1：同济校园自采** | (a) 路线规划（图书馆 → 大礼堂 → 三好坞，~1.5 km × 0.5 km，10 km/h 骑行）<br>(b) iPhone 30Hz 视频 + 50Hz IMU + 1Hz GPS 采集<br>(c) 数据预处理（IMU 标定 / 时间同步 / 转 Demo1 格式）<br>(d) 跑 VINGS-Mono 完整建图<br>(e) BEV 地图 + GPS 轨迹叠图（论文图 12 同款） |
| **可选 2：手机端复现** | (a) AutoDL 开 4090 服务端，跑作者的 server-side VINGS-Mono<br>(b) 在 Android 手机上装作者提供的 [官方 APK](https://github.com/victkk/3DGS_SLAM_mobile_app)<br>(c) 配通手机 → 服务器的 RGB+IMU 推流（WiFi / 4G）<br>(d) 手机屏幕实时显示 BEV 地图 + 渲染图（论文图 13 同款）<br>(e) 录制室内 + 室外 2 段实机演示 |
| 横向对比 | 校园数据 vs Hierarchical-SmallCity：定性比较两者的 Gaussian map 质量；定量比较 trajectory length / Gaussian 数量 / GPU 占用 |
| 交付物 | `results/tongji_campus/`（完整建图结果） + `results/mobile/`（手机端联调录屏 ≥ 2 段）+ 1 段 3 分钟"同济校园 SLAM"答辩视频 + 报告主笔（章节后面会说） |

> **D 同学比较辛苦**：要兼顾两个 optional，但**采集只占 1 天，剩下的预处理与跑实验时间是可控的**。手机端的真正瓶颈是"服务器配通 + 网络打通"，不在 D 一个人 — 让 A 在 D5 之后协助打通服务端联调（A 是熟环境的人）。

---

## 3. 15 天日程表（每日每人）

> 时间标记：**D1 = 项目启动当天**。所有人**白天 4–6 小时**专注本项目 = 每人 ~75 小时 ≈ 15 人天。

### D1 — 启动

| 全员 | 论文精读（每人精读 1 个章节并准备晚上 10 分钟讲解：A→Sec.IV，B→Sec.V，C→Sec.VI+VII，D→Sec.VIII） |
| --- | --- |
| A | 开 AutoDL 4090 × 1 台，开始装环境 |
| B | 把官方仓库 clone + 看 `configs/` 和 `scripts/run.py` 入口 |
| C | 看 Loop Closure 和 Dynamic Eraser 的源码位置 |
| D | 列校园采集路线 + 借手机三脚架 / 自行车架；研究官方 APK 仓库 |

晚上：**第 1 次例会**（论文互讲 + 同步明天分工）。

### D2 — 环境 + 论文

| A | 环境继续，重点解决 GTSAM 编译；准备**镜像快照** |
| --- | --- |
| B | 论文 Sec. V 二刷 + 看 2DGS rasterizer 源码；列消融实验配置 |
| C | 看 LightGlue + FastSAM 集成代码；申请 BONN 数据集 |
| D | 校园路线试走（不采，先确认信号和路况） |

### D3 — 跑通 Demo

| A | **A 必须完成环境** + 跑通 Hotel demo + 把镜像快照分享给 B/C/D；写 `docs/SETUP.md` v1 |
| --- | --- |
| B | 拿到镜像，自己开 1 台 AutoDL，跑 Hotel demo + SmallCity demo |
| C | 拿到镜像，自己开 1 台 AutoDL，下载 KITTI 数据 |
| D | 申请并下载 BONN dataset；准备 iPhone + 三脚架 |

晚上：**第 2 次例会**（环境 OK 否 → 决定 D4 的实验排程）。

### D4 — 实验开跑

| A | KITTI 07 mono-only 跑通；同时尝试 mono+IMU |
| --- | --- |
| B | 跑 SmallCity 完整序列；记录 baseline 数据（不消融） |
| C | 跑 KITTI 08 起步（不求完跑，先看几百帧能否稳定） |
| D | **校园数据采集**（白天进行，~半天）；同步研究官方 APK 怎么编译 |

### D5 — 实验深入

| A | 整理 KITTI 07 结果；开始 Waymo Scene01；写前端章节 PPT 大纲 |
| --- | --- |
| B | Score Manager 消融第 1 组 + 第 2 组（不同阈值） |
| C | KITTI 08 完整跑完；触发回环并截图 |
| D | 校园数据预处理（视频抽帧 + IMU 时间戳对齐 + 转 Demo 格式）；A 协助开服务端 |

### D6 — 实验深入 II

| A | Waymo 跑完；KITTI 07 mono+IMU 跑完 → 完成"前端表 II + 表 III" |
| --- | --- |
| B | Score Manager 消融第 3-5 组 |
| C | 开闭环对比实验（同一 KITTI 08 / KITTI360 序列） |
| D | 校园数据跑 VINGS-Mono 第一遍；A 帮 D 把官方 APK 部署到 D 的安卓手机上 |

晚上：**第 3 次例会**（中期检查）。

### D7 — 推进

| A | 写前端章节 PPT 与报告草稿（4–5 页）；开始 profiling 时间分析 |
| --- | --- |
| B | Sample Rasterizer profiling（原版 vs Ours）；Pose Refinement 消融跑 3 组 |
| C | BONN dynamic eraser 实验 4 个序列 + 表格整理 |
| D | 校园数据跑通 + 出 BEV 图；联调手机端推流（先把"手机能连上服务器"打通） |

### D8 — 推进

| A | 帮 B/C/D 调他们卡住的实验环境问题；前端 PPT 80% 完成 |
| --- | --- |
| B | Pose Refinement 消融剩余 6 组跑完；开始整理 `docs/ABLATION.md` |
| C | TSDF mesh 导出 + CloudCompare 出图；开始整理回环章节 PPT |
| D | 手机端推流跑通；录制第 1 段"手机端建图"演示视频（室内） |

### D9 — 收口实验

| A | 所有前端实验复跑 1 次验证可重复性；导出最终 trajectory 文件 |
| --- | --- |
| B | 消融完成 → `docs/ABLATION.md` 第一版；选出 SmallCity 最漂亮的一段做 BEV 录屏 |
| C | KITTI 长序列录屏（回环纠正前后对比 2 段）；dynamic eraser 演示录屏 |
| D | 校园数据建图最终结果 + 与 SmallCity 横向对比表；录第 2 段"手机端建图"演示（室外） |

### D10 — 开始写

| 全员 | 实验全部完成 → **进入写作阶段**，禁止再开新实验（重要！避免拖时间） |
| --- | --- |
| A | 报告 Sec. 1（引言）+ Sec. 4（前端） |
| B | 报告 Sec. 5（2D Gaussian Map）+ Sec. 6（消融） |
| C | 报告 Sec. 7（回环 + 动态） |
| D | 报告 Sec. 8（实地应用 + 手机端）+ 整体格式协调（建议 D 主笔，因为最熟全局） |

### D11 — 报告 v1 完成

| 全员 | 各自章节写完 → 合并到主分支，互审 |
| --- | --- |
| 晚上 | **第 4 次例会**：互审报告，列出修改清单 |

### D12 — 报告 v2 + PPT 开工（**每人 4 页，对应 3.5 分钟讲解**）

| A | 修改报告 + 完成 PPT（**4 页**：定位/方法/实验/总结） |
| --- | --- |
| B | 修改报告 + 完成 PPT（**4 页**：消融做一页"3 项消融对比表"压缩呈现） |
| C | 修改报告 + 完成 PPT（**4 页**：回环 1 页 + 动态 1 页 + 实验 1 页 + 总结 1 页） |
| D | 修改报告 + 完成 PPT（**4 页**含手机/校园视频嵌入）+ **出 PPT 统一模板**（封面 + 过渡页） + 报告整体排版 |

### D13 — 答辩素材 + 视频整合

| 全员 | 各自 PPT 终稿；D 把所有录屏剪成 **1 段 3 分钟 highlight reel**（含 SmallCity / 校园 / 手机端 / 回环 4 段） |
| --- | --- |

### D14 — 彩排

| 全员 | 第 1 次完整彩排（每人 5 分钟 + 全员 Q&A 5 分钟） → 收反馈 → 修订 PPT |
| --- | --- |

### D15 — Buffer + 终彩排

| 全员 | 最后一次彩排 + buffer 应对任何意外（提交格式、视频压缩、ppt 字体丢失等） |
| --- | --- |

---

## 4. 复现成功的量化指标（**用于自检 & 答辩**）

直接对照论文表格。每人对自己的实验负责：

| 实验 | 负责人 | 论文值 | 我们目标值 |
| --- | --- | --- | --- |
| BundleFusion-apt0 ATE (cm) | B | 44.22 | ≤ 70 |
| Hierarchical-SmallCity ATE (m) | B | 2.82 | ≤ 4.0 |
| Hierarchical-SmallCity PSNR | B | 22.07 | ≥ 20.5 |
| KITTI-07 trel (%) | A | 1.01 | ≤ 1.5 |
| KITTI-08 ATE drift | C | — | 完整跑完且触发至少 1 次回环 |
| BONN ball ATE (cm) | C | 4.08 | ≤ 8 |
| Waymo-01 ATE (m) | A | 0.91 | ≤ 1.5 |
| 校园数据 trajectory 长度 | D | — | ≥ 1 km |
| 手机端实机演示 | D | — | 室内 + 室外各 1 段 ≥ 30 秒 |
| Score Manager 表 VII | B | Gaussian 数量减半 PSNR 几乎不降 | 在 1 个 indoor + 1 个 outdoor 上复现趋势 |
| Pose Refinement 表 VIII | B | 我们 > current-only > 不做 | 趋势一致 |

只要 **≥ 9/11 项** 达标，就足以写"复现成功且充分超越基线"。

---

## 5. AutoDL 4090 使用规划

| 阶段 | 实例数 | 用途 |
| --- | --- | --- |
| D1-D3 环境期 | 1 台 | A 装环境 + 做镜像 |
| D4-D9 实验期 | **2–4 台并行** | A / B / C / D 各 1 台（D 在 D6-D9 才需要）|
| D10-D15 写作期 | 0–1 台 | 保留 1 台用于紧急复跑 |

**成本估算**（4090 单卡约 1.7–2.5 元/小时）：
- 单台 24 小时 × 15 天 = 360 小时 ≈ 700 元
- 4 台并行 6 天 × 8 小时/天 = 192 小时 ≈ 400 元
- **保守预算 ~ ¥1500–2000，4 人分摊每人 500 块以内**

省钱策略：
1. 镜像做好后，不用的实例**立即关机**（按量付费，不收磁盘费）
2. 数据集预先下到 AutoDL 公共数据集或自己的数据盘（不随实例释放）
3. 写作期完全关机，只在需要复跑时再开

---

## 6. 风险与应急（v1 基础上更新）

| 坑 | 表现 | 预案 |
| --- | --- | --- |
| GTSAM vio 分支编译失败 | D1-D2 卡 A | A 多预留 1 天；先用纯 Mono 跑（论文 SmallCity 就是 mono-only），不阻塞 B/C |
| 手机端 APK 与服务器连不通 | D8 D 卡住 | A 提前在 D6-D7 协助 D 打通；最坏情况 D 手机端只做"服务器侧建图 + 手机查看 BEV"，不强求完整推流 |
| 校园数据采集天气不好 / 数据废 | D4 重采 | D5 必须重采，D4 数据当晚检查质量 |
| Sample Rasterizer 在 4090 上编不过 | B 的实验 3 受阻 | 跳过该消融，仅对比原版 2DGS（仍能讲清楚问题）；不影响 main result |
| KITTI 08 跑到 50% 卡死 | C 的实验 1 | 切到 KITTI 07（更短）；或者用前 2500 帧也行 |
| BONN 数据集下载受限 | C 的实验 3 | 用 BONN 子集 / 用 TUM dynamic objects 替代 |
| 报告写不完 | D14 紧张 | D10 是强制 freeze 日，已留 5 天写作 buffer |

---

## 7. 最终交付清单

```
SLAM期末项目/
├── README.md
├── VINGS.pdf
├── SLAM复现论文作业要求.pdf
├── third_party/VINGS-Mono/         # 官方代码 submodule
├── docs/
│   ├── REPRODUCTION_PLAN.md        # 本计划
│   ├── SETUP.md                    # A 负责，环境记录
│   ├── ABLATION.md                 # B 负责，消融结果
│   ├── REPORT.pdf                  # 最终报告（4 人协作，D 主笔排版）
│   └── SLIDES.pdf                  # 答辩 PPT（合并版 / 也可以 4 个分册）
├── configs/                        # 我们改过的 yaml（每个数据集 1 份）
├── scripts/                        # 数据预处理、评测、可视化辅助脚本
├── results/
│   ├── frontend/                   # A
│   ├── mapping/                    # B
│   ├── ablation/                   # B
│   ├── loop/                       # C
│   ├── dynamic/                    # C
│   ├── tongji_campus/              # D
│   └── mobile/                     # D
└── media/
    ├── figures/                    # 静态图（详见 §7.5）
    └── videos/                     # 录屏（详见 §7.5）
```

---

## 7.5 可视化产出清单（**by Person，D9 自检用**）

> 每件可视化都明确 owner + 输出路径 + 用途，D9 之前每人对照打勾。

### A — 视觉惯性前端（3 件）

| # | 类型 | 文件 | 内容 | 用途 |
| --- | --- | --- | --- | --- |
| A1 | 录屏 | `media/videos/tracking_kitti07.mp4` | KITTI 07 DROID-SLAM DBA 收敛过程，30–60 秒 | PPT 方法页 |
| A2 | 静态图 | `media/figures/traj_kitti07_compare.png` | 我们 / VINS-Mono / ORB-SLAM3 / DROID-SLAM / GT 五条轨迹叠加 | PPT 实验页 |
| A3 | 静态图 | `media/figures/vio_vs_vo_bar.png` | mono-only vs mono+IMU 的 ATE/RPE 柱状图（KITTI 07 + Waymo Scene01） | PPT 实验页 |

### B — 2D 高斯建图核心（5 件）

| # | 类型 | 文件 | 内容 | 用途 |
| --- | --- | --- | --- | --- |
| B1 | 录屏 | `media/videos/demo_smallcity.mp4` | SmallCity 完整建图 BEV + RGB 并排，2 分钟 | PPT 实验页 + highlight reel |
| B2 | 静态图 | `media/figures/render_compare.png` | GT vs Ours vs MonoGS vs PhotoSLAM 渲染对比拼图，论文图 7 同款 | PPT 实验页 |
| B3 | 静态图 | `media/figures/score_manager_curve.png` | Score Manager 阈值 vs PSNR/GS 数量趋势曲线，论文表 VII 转图 | PPT 消融页 |
| B4 | 静态图 | `media/figures/sample_rasterizer_bar.png` | 反传时间对比柱状图（原版 2DGS / Taming3DGS / Ours），论文图 11 同款 | PPT 消融页 |
| B5 | 静态图 | `media/figures/pose_refine_traj.png` | Pose Refinement 3 策略轨迹差异叠加图，论文表 VIII 转图 | PPT 消融页 |

### C — 回环 + 动态 + 长序列（5 件）

| # | 类型 | 文件 | 内容 | 用途 |
| --- | --- | --- | --- | --- |
| C1 | 录屏 | `media/videos/demo_kitti08_loop.mp4` | KITTI 08 回环前/后对比，1 分钟 | PPT 实验页 + highlight reel |
| C2 | 录屏 | `media/videos/demo_dynamic_eraser.mp4` | BONN 动态物体擦除前后渲染对比，30 秒 | PPT 动态页 |
| C3 | 静态图 | `media/figures/kitti08_bev.png` | KITTI 08 完整 3.2 km BEV 大图，论文图 8 同款 | PPT 长序列页 |
| C4 | 静态图 | `media/figures/loop_correction_compare.png` | 闭环 on/off 轨迹叠加 + 局部 Gaussian map 放大，论文图 10 同款 | PPT 回环页 |
| C5 | 静态图 | `media/figures/waymo_mesh.png` | Waymo Scene01 TSDF mesh 在 CloudCompare 的渲染图，论文图 9 同款 | PPT 长序列页 |

### D — 实地应用（7 件，含 highlight reel 主剪）

| # | 类型 | 文件 | 内容 | 用途 |
| --- | --- | --- | --- | --- |
| D1 | 录屏 | `media/videos/demo_tongji_campus.mp4` | 同济校园 BEV 旋转 + Gaussian map 漫游，3 分钟 | PPT 校园页 + highlight reel |
| D2 | 录屏 | `media/videos/demo_mobile_indoor.mp4` | 手机端室内演示，≥ 30 秒 | PPT 手机页 + highlight reel |
| D3 | 录屏 | `media/videos/demo_mobile_outdoor.mp4` | 手机端室外演示，≥ 30 秒 | PPT 手机页 + highlight reel |
| D4 | 静态图 | `media/figures/campus_gps_overlay.png` | 校园 Gaussian 轨迹与 Google Map 叠图，论文图 12 同款 | PPT 校园页 |
| D5 | 静态图 | `media/figures/mobile_4panel.png` | 手机屏 RGB + BEV + 渲染深度 + 渲染法向 4 联屏截图，论文图 13 同款 | PPT 手机页 |
| D6 | 静态图 | `media/figures/campus_vs_smallcity.png` | 校园数据 vs Hierarchical-SmallCity 横向对比 | PPT 校园页 |
| D7 | **综合** | `media/videos/highlight_reel_3min.mp4` | 把全员录屏剪成 3 分钟答辩高光（A1 / B1 / C1 / D1-D3） | 答辩收尾 |

### 总量

| 人 | 录屏 | 静态图 | 综合 | 合计 |
| --- | --- | --- | --- | --- |
| A | 1 | 2 | 0 | 3 |
| B | 1 | 4 | 0 | 5 |
| C | 2 | 3 | 0 | 5 |
| D | 3 | 3 | 1 | 7 |
| **总计** | **7** | **12** | **1** | **20** |

D 看上去最多，但 3 段录屏是采集时同步出片（不额外加工），主要工作量在 D7 highlight reel 剪辑 + 报告排版。

---

## 8. 答辩讲述结构（**总时长 15-18 分钟**，统一模板，避免互相重复）

**总盘子 16 分钟**：开场 30 秒 + 4 人 × 3 分 30 秒 + 收尾/highlight reel 1 分 30 秒 ≈ 16 分钟（可弹性 ±2 分钟覆盖 15-18 范围）。

**全员开场 30 秒**（建议组长讲）：项目概览 + 一张 Fig. 2 pipeline 图标出 4 人负责的方框颜色。

**每人 3 分 30 秒**：

| 时间 | 内容 | 页数 |
| --- | --- | --- |
| 20 秒 | "我负责的是 XX 模块"（用 pipeline 图高亮自己的部分） | 0.5 页 |
| 1 分 20 秒 | 方法关键点：1 个核心公式 / 1 张原理图，**只讲一个 take-home message** | 1-2 页 |
| 1 分 30 秒 | 我的实验 + 结果：1 张定量表 + 1 张定性图/视频 | 1-2 页 |
| 20 秒 | 一句话总结 + 局限 | 0.5 页 |

合计每人 **4 页左右 PPT**（含标题、过渡），4 人总共 16 页正文 + 开场 1 页 + 收尾 1 页 ≈ **18 页 PPT**。

**收尾 1 分 30 秒**（建议 D 讲）：播放 highlight reel（剪到 1 分钟内）+ 一句"future work"。

### 时间控制硬规则

1. **每人 PPT 不超过 5 页**（含标题页）。每页讲话 40-50 秒，超过就是"信息密度太低"。
2. **方法部分只能贴 1 个公式**。所有人都遵守，避免连讲 4 段满屏公式让评委疲劳。
3. **每人必须有 1 段视频 / 1 张定性图**，不能全是数字表格。
4. 4 人 PPT 文件**用统一模板**（D 同学在 D11 出模板，其他 3 人套用）。
5. **D14 彩排时严格掐表**，每人超过 4 分钟就砍内容，不要超过 4 分钟去解释。

---

## 9. 立即行动项（**今天 / D1**）

1. **组长**：把这份计划在群里发给另外 3 个人，每人选自己愿意当 A / B / C / D（同等权重，按各人兴趣或专长分）。
2. **A**：今晚或明天上午开 AutoDL 账号 + 充值 ~500 元，跑通"4090 实例 + 挂载 80GB 数据盘"。
3. **D**：开始联系一台可用的 Android 手机（IMU 频率 ≥ 50 Hz，建议小米 / 一加 / 华为，**iOS 跑不动 Android APK，但 iOS 可以采集校园数据**）。
4. **全员**：把论文 PDF 通读 1 遍，重点 Sec. IV-VII。

---

*v2 / 2026-05-19。计划在 D3、D6、D10 三个节点根据实际进度可修订。*
