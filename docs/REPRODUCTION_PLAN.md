# VINGS-Mono 复现计划

> 课程期末项目，4 人小组。本计划目标：**稳扎稳打把必做项做漂亮，再争取一项可选项加分**。
>
> 论文：Wu et al., *VINGS-Mono: Visual-Inertial Gaussian Splatting Monocular SLAM in Large Scenes*, TRO 2025 (arXiv:2501.08286)
> 官方仓库：<https://github.com/Fudan-MAGIC-Lab/VINGS-Mono>

---

## 0. 课程目标与本计划的对应

| 课程要求 | 优先级 | 我们的目标 |
| --- | --- | --- |
| 在自己电脑上复现 VINGS-Mono | **必做** | 在至少 1 个室内 + 1 个室外数据集上跑通，并复现论文里的关键指标（ATE / PSNR / Gaussian 数量） |
| 在手机上复现 | 可选 | 视时间和服务器情况争取做，主力在 PC 侧；做不了就不强求 |
| 用同济校园自采数据跑 | 可选鼓励 | 准备一段 5–10 分钟的校园骑行 / 步行数据，作为亮点放进报告与答辩 |

我们的策略：**必做保 95 分，争取至少做完一项可选，把整体目标推到 100 / 满分。**

---

## 1. 论文一句话总结（统一组员认知）

VINGS-Mono = **DROID-SLAM 风格的稠密 BA 前端 + GTSAM 视觉-惯性因子图** 提供位姿和稠密深度，作为 **2D Gaussian Splatting (2DGS) 地图** 的初始化与监督；同时引入 4 个核心模块解决"大场景 + 单目"的痛点：

1. **Score Manager** — 给每个 Gaussian 维护贡献分 \(S_C\) 和误差分 \(S_E\)，做稳定/不稳定状态切换、剪枝、以及 CPU↔GPU swap，把数千万 Gaussian 装进单卡。
2. **Sample Rasterizer** — 改造 2DGS 反向传播为 *Gaussian 维度并行 + 像素采样*，反传速度提升 273%。
3. **Single-to-Multi Pose Refinement** — 一次渲染回传梯度同时优化视锥内所有可见关键帧位姿，相比只优化当前帧的方法 ATE 更低。
4. **NVS Loop Closure** — 用 LightGlue 匹配特征点 + PnP 求相对位姿 + 渲染新视角与原图比对来判断回环；闭环后用每个 Gaussian 绑定的关键帧位姿一次性纠正所有 Gaussian 属性。
5. **Dynamic Eraser** — 用 FastSAM 出语义 mask + 重渲染损失（SSIM·L1·深度不确定度）筛选动态物体 mask。

记住这五个模块是答辩讲解和消融实验的主线。

---

## 2. 技术栈速查

| 模块 | 关键依赖 | 备注 |
| --- | --- | --- |
| VIO 前端 | DROID-SLAM (DBA + RAFT correlation) | 需要 `droid.pth` 权重 |
| 因子图 | GTSAM（vio 分支 fork：<https://github.com/Promethe-us/gtsam/tree/vio>） | **要从源码编 Python binding**，是最大的坑 |
| 地图 | 2DGS rasterizer + Sample Rasterizer (CUDA 扩展) | 编译需要 nvcc 11.8 |
| 回环检测 | SuperPoint + LightGlue (ONNX) | 权重已在 HuggingFace |
| 单目深度先验（可选） | Metric3D (`metric_depth_vit_small_800k.pth`) | 手机端 / 自采数据强烈建议开 |
| 动态分割 | FastSAM (`FastSAM-x.pt`) | 静态场景可以先不开 |
| 评测 | `evo` toolkit | ATE / RPE |

环境基线：**Python 3.9.19 + CUDA 11.8**（官方 README 明确给出），别用 12.x，不然 GTSAM/CUDA 扩展会编译失败。

---

## 3. 硬件 / 资源评估（**关键风险，请先确认**）

论文是在 **单卡 RTX 4090（24GB） + Xeon 6133** 上跑的。论文表 IX 的实测数据：

| 数据集 | 帧数 | 总运行时间 | 模型大小 |
| --- | --- | --- | --- |
| Waymo-Scene01 | 198 | 117 s | 386 MB |
| Hierarchical-SmallCity | 877 | 739 s | 1.8 GB |
| KITTI-Odom08 | 5177 | 4560 s（≈76 分钟） | 10.4 GB |
| KITTI360-drive_0006 | — | — | 51.7 M Gaussians（GPU+CPU） |

按这个推下我们小组的硬件需要：

| 任务 | 显存需求（建议） | 备注 |
| --- | --- | --- |
| Hotel / Hierarchical-SmallCity Demo | 8–12 GB | 1660 Ti / 3060 / 3070 即可 |
| Waymo / KITTI 单段 | 16 GB+ | 3080/3090/4070 Ti 比较稳；4090 最佳 |
| KITTI360 完整、千万级 Gaussian | 24 GB（4090 / A6000） | 没条件就**只跑短段** |

**小组动作项 P0**：4 个人各自报一下手头能用的 GPU（型号 + 显存），以及是否能用同济服务器 / 实验室卡。这个决定了我们能跑到什么规模。

---

## 4. 阶段时间线（**按"W = 第 N 周"标注，建议总时长 6 周；如截止日近可压到 4 周**）

> 每个阶段都给了：**目标 / 工作内容 / 交付物 / 验收标准 / 风险**。 

### Week 1 — 启动 & 环境（"能跑 import"是底线）

- **目标**：4 个人都 clone 仓库 + 至少 1 台机器能 `import` 通过、跑前 10 帧不报错。
- **工作内容**
  - [ ] 每人精读论文 1 遍 + 把官方仓库结构走一遍（`configs/`, `scripts/run.py`, `submodules/`）。
  - [ ] 把官方仓库以 submodule 形式加进来：
    ```bash
    git submodule add https://github.com/Fudan-MAGIC-Lab/VINGS-Mono third_party/VINGS-Mono
    git submodule update --init --recursive
    ```
  - [ ] 按 `set_env.sh` 建 conda 环境（Python 3.9.19 + CUDA 11.8 + PyTorch 2.0.x）。
  - [ ] 编译 GTSAM (vio 分支)、2DGS rasterizer、sample rasterizer 三个 CUDA 扩展。
  - [ ] 下载权重：`droid.pth`, `metric_depth_vit_small_800k.pth`, `superpoint.onnx`, `superpoint_lightglue.onnx`。
  - [ ] 写 `docs/SETUP.md` 把每一步踩过的坑记下来（包括报错截图 + 解决方案）。
- **交付物**：`docs/SETUP.md`、`environment.yml` 截图
- **验收标准**：在至少 1 台机器上，能跑：
  ```bash
  python scripts/run.py configs/rtg/hotel.yaml
  ```
  并看到 BEV / RGB 渲染窗口出现，前 30 帧无 crash。
- **风险**
  - **GTSAM 编译失败（最大坑）**：vio 分支需要从源码 build python wrapper，Boost、Eigen 版本要对得上；准备 1 天 buffer。
  - CUDA 版本不匹配：本机 CUDA driver 必须 ≥ 11.8。
  - 国内下载 HuggingFace 慢：用 hf-mirror 镜像或者 wget 直链。

### Week 2 — 跑通 2 个官方 Demo + 录像

- **目标**：把 *Hotel*（室内 RGBD）和 *Hierarchical-SmallCity*（室外骑行 RGB）两个 Demo 完整跑完。
- **工作内容**
  - [ ] 下载 HuggingFace 上官方处理好的两个 demo 数据。
  - [ ] 改 `configs/*.yaml` 的 `dataset.root` / `output.save_dir` / `frontend.weight` 三处。
  - [ ] 跑完整序列，保存：估计轨迹、最终 Gaussian ply、BEV 截图、渲染对比 RGB-GT 图。
  - [ ] 对照论文表 II / 表 V：
    - Hotel 我们能预期 PSNR ≈ 22–23 (论文 BundleFusion 各场景平均 20–22)；
    - SmallCity 我们能预期 ATE ≈ 2.8 m、PSNR ≈ 22；
  - [ ] **录屏**：起码 SmallCity 一次完整运行的 BEV+RGB 同步录屏，做成报告/答辩素材。
- **交付物**：两个 demo 的结果文件夹 + 录屏 + 一份简短 `results/demo_results.md`（含 PSNR/ATE 表格）。
- **验收标准**：两个 demo 的核心指标都落在论文报告值 ±20% 内。

### Week 3 — 在 1 个基准数据集上复现（**这是必做的核心**）

按硬件择优选一个：

| 候选 | 推荐场景 | 难度 | 显存要求 |
| --- | --- | --- | --- |
| **Waymo Scene01 / Scene03 / Scene14** | 200–500 帧短序列 | ★★☆ | 12 GB+ |
| **KITTI Odom 07 / 09** | 1000–1500 帧 | ★★★ | 16 GB+ |
| **KITTI Odom 08** | 5177 帧 | ★★★★ | 24 GB（论文规模） |

**默认推荐 = Waymo Scene01 + KITTI Odom 07**：能匹配论文表 II / 表 III / 表 VI 的具体数字，又不至于跑一晚上。

- **工作内容**
  - [ ] 数据预处理：参考官方 `configs/kitti/...` 和 `docs/`，把 KITTI 的 IMU 时间戳对齐（论文有提到 KITTI unsync 数据要修）。
  - [ ] 跑两次：**(a) Mono-only**、**(b) Mono + IMU**（VIO 模式）。
  - [ ] 用 `evo` 算 ATE/RPE，与论文表 I/II/III 比对；用 `lpips/ssim/psnr` 算渲染质量，与表 V/VI 比对。
  - [ ] 把 Gaussian ply 导出，用 SuperSplat / nerfstudio viewer 出 1–2 张漂亮的展示图。
- **交付物**：`results/<dataset>_<scene>/` 下保存配置、轨迹 TUM/KITTI 格式、PSNR/SSIM/LPIPS 报告、可视化图。
- **验收标准**：至少在 1 个 outdoor scene 上 ATE ≤ 论文报告值的 1.5 倍，PSNR ≥ 论文报告值 − 1.5 dB。

### Week 4 — 消融实验 & 模块分析（**答辩高分项**）

不需要全做，挑 2 个能讲清楚的就够拿差异化分。建议优先级：

| 优先级 | 消融 | 论文位置 | 工作量 |
| --- | --- | --- | --- |
| ★★★ | **Score Manager**（开 / 关 / 不同阈值） | 表 VII | 改 1 个配置开关，跑 3 次 |
| ★★★ | **Pose Refinement**（无 / 只优化当前帧 / 优化可见关键帧） | 表 VIII | 改前端调用，跑 2 次 |
| ★★ | **Sample Rasterizer**（原版 2DGS vs. 我们的） | 图 11 | 切换 rasterizer，profile 反传时间 |
| ★ | Dynamic Eraser 在 BONN 上的开/关 | 表 IV | 需要额外数据集 |

- **工作内容**
  - [ ] 复现论文表 VII（Score Manager）—— 在 1 个 indoor + 1 个 outdoor 场景上跑不同 `Sstorage_C` 阈值，记录 GS 数量和 PSNR。
  - [ ] 复现论文表 VIII（Pose Refinement）—— 在 ScanNet-0106、Copyroom、Campus 中选 1 个。
  - [ ] 给每个消融出一张定量表 + 1 张定性图，写进 `docs/ABLATION.md`。
- **交付物**：`docs/ABLATION.md`（含图表）+ 原始日志。
- **验收标准**：至少 2 个消融的趋势方向与论文一致（即使绝对数值有差异）。

### Week 5 — 可选项（**冲分**，按时间决定做哪个）

#### 选项 A：手机端复现

- 用作者提供的 [3DGS_SLAM_mobile_app](https://github.com/victkk/3DGS_SLAM_mobile_app) 编一个 APK（需要 Android Studio 或者 Flutter）。
- 服务器（带 GPU 的 PC）上跑 VINGS-Mono 服务端；手机推 RGB + IMU 流到服务器。
- 录一段室内手持视频，回传重建结果。
- **工作量**：1 人 × 3–4 天。需要稳定 WiFi、Android 手机、GPU 服务器。

#### 选项 B：同济校园自采数据

- 工具：iPhone（30Hz 1080p + 50Hz IMU + 1Hz GPS）或者 GoPro。
- 路线建议：图书馆 → 大礼堂 → 三好坞，骑行约 8–10 km/h，10 分钟左右。
- 同步采集 GPS 作为 ground-truth 参考（不是绝对真值，但可对比 trajectory）。
- 处理：用作者在论文里描述的方法，按 [IMU 标定 + 时间同步 + Demo1 格式打包] 三步走。
- **工作量**：1–2 人 × 3–5 天。需要先验证 iPhone IMU 频率与质量是否够。

**推荐**：**优先做 B**（校园数据），因为它直接对应作业里"鼓励项"，并且对答辩观感极强（一段同济校园的高质量 Gaussian map 演示，远比手机 APK 更"硬"）。手机端如果时间富余再做。

### Week 6 — 报告 & PPT & 答辩准备

- [ ] **报告**（建议 15–20 页 PDF / LaTeX）
  - 论文背景 + 我们要解决的问题
  - 方法原理：5 大模块 + 每个模块的关键公式（用论文式 (4)、(7)、(11)、(13)、(14)、(16)）
  - 实验复现表格 + 与原论文对比
  - 消融实验
  - 自采数据 / 手机端结果（如果做了）
  - 失败案例 & 分析（哪些场景 ATE 比论文差？为什么？）
  - 复现过程总结 + 课程感悟
- [ ] **PPT**（建议 15–20 页）
  - 1 页 motivation
  - 2 页 method overview（用论文 Fig.2 pipeline 图）
  - 5 页核心模块（每模块 1 页）
  - 5 页实验结果（含定量表 + 定性图 + 视频 demo 嵌入）
  - 2 页消融
  - 1 页校园 / 手机端 demo
  - 1 页 conclusion + future work
- [ ] **答辩视频素材**：把所有跑出来的录屏剪成一段 2–3 分钟的 highlight reel。
- **交付物**：`docs/REPORT.pdf`、`docs/SLIDES.pdf`、`docs/demo_video.mp4`

---

## 5. 任务分工（4 人，按个人意愿微调）

| 角色 | 主要职责 | 配对的阶段 |
| --- | --- | --- |
| **A. 环境 & 基础设施**（建议组长 / 强工程能力者） | 搭 conda 环境、解决 GTSAM 编译、维护 Docker（可选）、CUDA 扩展 build、写 `SETUP.md` | W1 主，W2-3 持续支持 |
| **B. 数据 & 实验**（重 Linux / 数据处理） | 下载并预处理 Demo / KITTI / Waymo，跑实验，整理结果 | W2-4 主 |
| **C. 算法 & 消融**（重论文阅读 / 写代码） | 读懂 score manager / pose refinement / sample rasterizer，做消融实验和定量分析 | W3-4 主 |
| **D. 演示 & 文档**（重表达 / 美工） | 校园自采数据、录屏、可视化（CloudCompare / SuperSplat）、写报告、做 PPT | W2 起持续，W5-6 主 |

每周一次例会（线上 30 分钟），更新各自进度 + 同步阻塞问题 + 调整下周分工。

---

## 6. 复现成功的量化指标（**用来自检和写报告**）

直接对照论文的关键表格：

| 数据集 | 指标 | 论文值 | 我们的目标值 |
| --- | --- | --- | --- |
| BundleFusion-apt0 | ATE (cm) | 44.22 | ≤ 70 |
| BundleFusion-apt0 | PSNR | 20.45 | ≥ 18.5 |
| Hierarchical-SmallCity | ATE (m) | 2.82 | ≤ 4.0 |
| Hierarchical-SmallCity | PSNR | 22.07 | ≥ 20.5 |
| KITTI-Odom07 | trel (%) | 1.01 | ≤ 1.5 |
| KITTI-Odom07 | rrel (°/100m) | 0.80 | ≤ 1.2 |
| Waymo-Scene01 | ATE (m) | 0.91 | ≤ 1.5 |
| Waymo-Scene01 | PSNR | 23.48 | ≥ 22 |

只要至少 4 个指标达标，就足以在报告里写"复现成功"。

---

## 7. 已知坑 & 应急预案

| 坑 | 表现 | 预案 |
| --- | --- | --- |
| GTSAM vio 分支编译失败 | `pip install` 时报 Boost / Eigen 找不到 | 用 Promethe-us fork 而不是 mainline；Ubuntu 22.04 用 apt 装 `libboost-all-dev libeigen3-dev`；准备一台备用机；实在不行先跑 **不带 IMU** 的纯 Mono 模式（论文里 Hierarchical 就是 mono-only） |
| CUDA 11.8 与 RTX 40 系不兼容 | `RuntimeError: CUDA error: no kernel image is available` | 用 PyTorch 2.0.1+cu118；CUDA architecture 设 `8.9`；确认 `nvcc --version` 与 `torch.version.cuda` 一致 |
| Sample Rasterizer build 失败 | `setup.py` 编译时报错 | 看 `submodules/diff-surfel-rasterization` 的 `CMakeLists`，确认 `TORCH_CUDA_ARCH_LIST` 包含本机算力 |
| 显存爆 OOM | 跑到中段 CUDA OOM | 减小 `keyframe_window` / `n_iter_per_kf`；提前触发 `score_manager` 的 storage prune；跑短序列 |
| 数据集下载慢 | HF / Waymo / KITTI 拉不下来 | 提前一周开始挂；用同济校园网；用 hf-mirror.com |
| KITTI IMU 时间戳乱序 | 跑到一半 IMU 因子图发散 | 用论文提到的 fix 脚本（issue 里有），手动排序 |
| 手机 APK 跑不起来 | 服务器连不上 / 协议不通 | 直接放弃手机端，把精力转到校园自采数据 |
| 渲染指标比论文差很多 | PSNR 低 3 dB 以上 | 检查是否跑足训练迭代（每帧 80–100 iters）；检查是否打开 `use_vis=False` 但忘了关其他可视化导致掉帧；检查 metric_depth 权重是否加载 |

---

## 8. 最终交付清单（截止日前）

仓库根目录应该长这样：

```
SLAM期末项目/
├── README.md              # 项目入口
├── VINGS.pdf              # 原论文
├── SLAM复现论文作业要求.pdf
├── third_party/VINGS-Mono/   # 官方代码（submodule）
├── docs/
│   ├── REPRODUCTION_PLAN.md  # 本文件
│   ├── SETUP.md              # 环境搭建踩坑记
│   ├── ABLATION.md           # 消融实验
│   ├── REPORT.pdf            # 最终报告
│   └── SLIDES.pdf            # 答辩 PPT
├── configs/                  # 我们改过的 yaml 副本
├── scripts/                  # 自己写的辅助脚本（数据预处理、评测、可视化）
├── results/
│   ├── hotel/
│   ├── smallcity/
│   ├── kitti_07/
│   ├── waymo_01/
│   └── tongji_campus/        # 自采（如果做了）
└── media/
    ├── demo_smallcity.mp4
    └── demo_video.mp4        # 答辩用 highlight reel
```

---

## 9. 下一步立即行动项（本周内）

1. **组长（A）**：在群里收集 4 个人的硬件信息（GPU 型号、显存、CUDA 版本、操作系统），填到本文件第 3 节下方的"小组实际硬件清单"里。
2. **每个人**：先把论文通读 1 遍，重点看 Sec. IV–VII（方法）和 Sec. VIII（实验）。
3. **A & B**：本周内出 1 台能跑通 Hotel demo 的机器，写 `docs/SETUP.md` 第一版。
4. **D**：去 HuggingFace 把 Hotel + SmallCity 数据下载到一台带大硬盘的机器上（demo 数据 ≈ 几十 GB，KITTI/Waymo 后面再下）。
5. **C**：把论文 Sec. V (2D Gaussian Map) 和 Sec. VI (NVS Loop Closure) 各做一份 1 页中文笔记，下次例会讲给大家听。

---

*本计划是 v1，跑通环境后会根据实际硬件 / 进度修订。* 
