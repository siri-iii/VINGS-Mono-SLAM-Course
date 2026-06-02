# 成员 A 最终工作汇总与 PPT 备注

日期：2026-06-01

用途：本文是成员 A 部分的最终汇报依据。历史排查过程见 `docs/A_PROGRESS_HANDOFF.md`，原始实验数据见 `results/frontend/a_frontend_summary.csv`。PPT 应优先使用本文结论，避免引用早期已被推翻的判断。

## 1. 最终状态

成员 A 的任务已完成。

- 已完成 VINGS-Mono 前端部署、KITTI07 VO/VIO 运行、评测、可视化和问题排查。
- 已修复 VIO 崩溃，并将公开代码条件下的 KITTI07 VIO `t_rel` 从 `61.14%` 改善到 `20.84%`。
- 未复现论文 Table III 的 `1.01%` 指标。
- 剩余差距无法由公开材料继续闭环：官方未公开 Table III 使用的 KITTI 评测脚本、精确轨迹导出流程、实验 commit 和完整命令。
- Waymo Scene01 未运行，原因是服务器缺少对应数据；运行和评测脚本已准备。

汇报时应诚实表述为：

> 我们完成了视觉惯性前端的工程复现、评测链路修正和关键故障定位。在公开代码和公开数据条件下，KITTI07 VIO 可以稳定完整运行，最佳 `t_rel` 为 `20.84%`。该结果仍未达到论文报告的 `1.01%`，且公开仓库没有提供 Table III 的完整复现流程。

## 2. A 的职责

成员 A 负责论文 VIO Front End 和复现基础设施：

- 在 RTX 4090 远程服务器部署 VINGS-Mono 运行环境。
- 跑通 KITTI07 mono-only VO 和 mono+IMU VIO。
- 验证 Dense BA、IMU 预积分和 GTSAM 因子图链路。
- 修正 KITTI 轨迹评测方式。
- 排查作者定制 GTSAM 私有接口和边缘化崩溃。
- 生成指标表、轨迹图和轨迹回放视频。
- 为 Waymo Scene01 预留运行和评测入口。

## 3. 系统链路

前端可概括为：

```text
RGB 图像 ──> DROID 风格稠密光流与 Dense BA ──┐
                                             ├──> GTSAM 因子图优化 ──> 相机位姿
IMU 数据 ──> 预积分与 bias / gravity 初始化 ──┘
```

关键实现位置：

- 前端入口：`third_party/VINGS-Mono/scripts/frontend/dbaf.py`
- VIO 前端：`third_party/VINGS-Mono/scripts/frontend/dbaf_frontend.py`
- Dense BA 与边缘化：`third_party/VINGS-Mono/scripts/frontend/depth_video.py`
- GTSAM 兼容层：`third_party/VINGS-Mono/scripts/frontend/gtsam_compat.py`
- KITTI 评测：`scripts/eval_kitti.py`

## 4. 最终指标

论文 Table III 中 KITTI Sync 序列 `07` 的 VIO 目标：

| 来源 | `t_rel` | `r_rel` |
| --- | ---: | ---: |
| VINGS-Mono 论文 Table III | `1.01%` | `0.80 deg/100m` |

本次复现实验：

| 实验 | 匹配帧数 | ATE RMSE | `t_rel` | `r_rel` | 结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| KITTI07 VO original | 233 | 19.49 m | 14.17% | 3.20 | 可运行 |
| KITTI07 VO dense | 727 | 13.04 m | 9.76% | 3.00 | 最佳 VO |
| KITTI07 VIO original | 736 | 72.52 m | 63.15% | 65.34 | 精度失败 |
| KITTI07 VIO guarded early | 346 | 64.62 m | 61.14% | 24.54 | 已避免崩溃 |
| KITTI07 VIO native private APIs | 359 | 39.71 m | 23.19% | 5.95 | 明显改善 |
| KITTI07 VIO official `run_tracking.py` + guarded native | 360 | 36.02 m | **20.84%** | 9.47 | 当前最佳公开路径 |

注意：

- 当前最佳 VIO 结果仍不能宣称复现论文指标。
- VO 和 VIO 的评测轨迹覆盖不同，不能只凭单一数字宣称某个模式整体更优。
- `ATE` 使用 Sim(3) 对齐，`t_rel` 和 `r_rel` 用于 KITTI 相对误差分析。

## 5. 关键工程工作

### 5.1 修正 KITTI 评测对齐

问题：

- 前端输出的 `droid_c2w/*.txt` 使用 camera timestamp 命名，不是连续帧编号。
- 直接按输出顺序与 KITTI GT 行号配对会造成错误评估。

处理：

- 在 `scripts/eval_kitti.py` 中读取 `metadata/camstamp.txt`。
- 将预测轨迹文件名映射回 GT frame index。
- 重新计算 ATE、`t_rel`、`r_rel`。
- 额外执行逐帧插值评测和 `-8..+8` 帧偏移扫描。

结论：

- 插值复评 `t_rel=24.24%`，与稀疏关键帧评测接近。
- 帧偏移扫描最佳仍约 `20.82%`。
- 剩余差距不是 timestamp 对齐或简单 GT 索引偏移问题。

### 5.2 补齐并验证作者定制 GTSAM

VIO 依赖普通 GTSAM 不一定提供的私有接口：

- `marginalizeOut`
- `BA2GTSAM`
- `GTSAM2BA`
- `CustomHessianFactor`
- `CombinedImuFactor.evaluateErrorCustom`

服务器已验证：

- GTSAM 来源：`Promethe-us/gtsam`
- 分支：`origin/vio`
- commit：`c572c6f32`
- 上述私有接口均存在。

### 5.3 修复兼容层覆盖原生接口

问题：

- 课程分支加入了 Python compatibility shim。
- 服务器已经安装作者原生私有接口，但部分路径仍被 Python fallback 覆盖，降低数值质量。

处理：

- 保留原生 `BA2GTSAM`、`GTSAM2BA`、`CustomHessianFactor`。
- 适配原生 `BA2GTSAM` 返回的增广矩阵 `[H | v]`。
- 将视觉 Hessian factor 路由到原生 `CustomHessianFactor`。
- 增加回归测试，确保重复安装 patch 不会递归覆盖原生函数。

结果：

- VIO `t_rel` 从 `61.14%` 改善到 `23.19%`。
- 使用作者 `run_tracking.py` 后进一步得到当前最佳 `20.84%`。

### 5.4 保留 `marginalizeOut` 最小防崩保护

问题：

- 作者 GTSAM `marginalizeOut` 的 C++ 实现假定边缘化 key 同时存在于 `Values` 和 graph。
- 边缘化参数中出现无效 key 时，原生代码可能访问非法维度并触发段错误。

处理：

- 调用原生 C++ 前，只过滤不在 `Values` 或 graph 中的 key。
- 有效 key 仍走作者原生边缘化。
- 原生调用抛出可捕获异常时才进入 Python fallback。

消融：

| 路径 | `t_rel` |
| --- | ---: |
| 作者公开原始路径 | 72.73% |
| 直接调用原生 `marginalizeOut` | 46.67% |
| guarded native 路径 | **20.84%** |

结论：

- 不应移除 key 过滤。
- 不应恢复全面 Python fallback。
- 当前 guarded native 路径是已测试方案中最合理的实现。

## 6. 已排除原因

以下方向已经验证，不应继续重复排查：

| 假设 | 验证方式 | 结论 |
| --- | --- | --- |
| KITTI Sync 只有 10 Hz IMU，无法达到论文指标 | 核对论文正文和 Table III | 错误。论文明确使用 `10 Hz KITTI sync data` |
| 需要额外 100 Hz unsync OXTS 才能复现 | 核对论文数据说明 | 不成立。论文 KITTI 指标使用 Sync 数据 |
| 服务器 metadata 与作者数据不一致 | 下载官方 `KITTI_Sync.zip`，逐文件 SHA256 比对 | 四个 metadata 文件逐字节一致 |
| DROID 权重不一致 | 比对 `ckpts/droid.pth` SHA256 | 与作者发布权重一致 |
| GTSAM 分支错误 | 检查子模块 remote、branch 和 commit | 已使用 README 指定 `Promethe-us/gtsam@c572c6f32` |
| 时间戳匹配错误 | timestamp 映射、逐帧插值复评 | 不是剩余根因 |
| raw-to-odometry GT 存在固定帧偏移 | 扫描 `-8..+8` 帧 | 不是剩余根因 |
| 只需恢复作者原始路径 | 隔离 worktree 运行公开原始版本 | 原始路径更差，`t_rel=72.73%` |

官方 metadata SHA256：

| 文件 | SHA256 |
| --- | --- |
| `c2i.txt` | `2dbd8219bd02d0deb4c86e551ed73ba6b6fc1e4103de5628006faa66144aed2c` |
| `calib.txt` | `6a0797d9b695a0786fc983a9a0c94f58b0d9c2135ff5f2f95ab5f6a8f94e1bbd` |
| `camstamp.txt` | `309c0ae3a6362c7bb2cab0078240af689655493cd916898b813e6c2fa0146d70` |
| `imu.txt` | `cb74836938da99cfaa3121f1fe8d8ca9beae7149b029793c1b932d85dcd66ab0` |

权重 SHA256：

```text
46476ef64cde45a97504910d6f3de2eef7b398ec1c6e4e668815c29076024526  ckpts/droid.pth
```

## 7. 公开复现缺口

已检查作者官方 GitHub、项目页、Hugging Face 数据集、权重仓库、GTSAM vio 分支和公开 Issue。公开材料中没有找到：

1. Table III 使用的 KITTI 官方评测脚本；
2. Table III 使用的精确轨迹导出方式；
3. Table III 对应的实验 commit；
4. 可直接达到论文指标的 KITTI07 完整运行命令。

需要准确表述：

> 公开仓库存在轨迹导出代码，但没有说明论文 Table III 实际使用哪条导出路径和评测流程。因此当前无法严格复现论文口径。

不建议继续做大规模参数扫描。只有作者补充复现流程后，进一步优化才有明确依据。

## 8. Waymo 状态

Waymo Scene01 状态为 blocked：

```text
/root/autodl-tmp/data/waymo/Scene01/color
/root/autodl-tmp/data/waymo/Scene01/pose
```

服务器缺少上述数据。已准备：

- `scripts/check_frontend_data.py`
- `scripts/eval_waymo.py`
- `scripts/run_waymo_exp.sh`

汇报时可说：

> Waymo Scene01 的运行入口和评测脚本已经准备，但服务器没有对应数据，因此本次未生成 Waymo 指标。

## 9. PPT 建议结构

### 第 1 页：任务与前端结构

- A 负责系统部署和 VIO Front End。
- 展示“RGB -> Dense BA”和“IMU -> 预积分 -> GTSAM 因子图”的流程图。
- 强调该模块为后续建图提供相机位姿。

### 第 2 页：工程部署与评测修正

- RTX 4090 服务器环境已搭建。
- 作者 VIO 依赖定制 GTSAM vio 分支。
- KITTI 评测必须按 camera timestamp 匹配 GT。

推荐展示：

- `scripts/eval_kitti.py` 的 timestamp 映射示意。
- `media/figures/traj_kitti07_compare.png`。

### 第 3 页：指标演进

推荐表格：

| 版本 | `t_rel` | 说明 |
| --- | ---: | --- |
| VIO early guarded | 61.14% | 已能完整运行 |
| native private APIs | 23.19% | 避免 Python 覆盖原生接口 |
| official tracking + guarded native | **20.84%** | 当前最佳公开路径 |
| 论文 Table III | 1.01% | 未严格复现 |

讲解重点：

- 工程修复带来显著改善。
- 公开路径仍无法达到论文表格指标。

### 第 4 页：关键故障与修复

- 普通 GTSAM 缺少作者私有扩展。
- 原生 `marginalizeOut` 对无效 key 缺少防御。
- 使用“原生私有 API + 最小 key 过滤”后稳定跑完 `1106/1106`。

### 第 5 页：结论与边界

- 前端工程链路、评测链路和可视化已完成。
- 排除了数据频率、metadata、权重、GTSAM 分支和 timestamp 偏移问题。
- 论文 Table III 的精确复现流程未公开。
- 成员 A 的任务到此完成。

## 10. 可直接使用的发言稿

我负责 VINGS-Mono 的视觉惯性前端和系统部署。前端由两部分组成：图像侧使用 DROID 风格的稠密光流和 Dense BA，IMU 侧使用预积分以及 GTSAM 因子图优化，最终为后续建图提供相机位姿。

工程上，我在 RTX 4090 服务器完成了环境部署，并跑通了 KITTI07 的 VO 和 VIO。评测过程中首先修正了轨迹对齐问题：前端输出使用相机时间戳命名，不能直接按行号匹配 KITTI GT。因此我们新增了 timestamp 映射评测，并补充了逐帧插值和帧偏移扫描。

VIO 的主要难点是作者依赖定制 GTSAM 分支，其中包含 `BA2GTSAM`、`GTSAM2BA`、`CustomHessianFactor` 和 `marginalizeOut` 等私有接口。服务器安装这些原生接口后，我们发现课程兼容层仍会覆盖部分原生实现，于是改为优先使用作者原生 API。同时，为避免 C++ 边缘化在无效 key 上崩溃，只保留了一层最小 key 过滤。修改后，KITTI07 VIO 可以稳定跑完全部 1106 帧，`t_rel` 从 61.14% 改善到 20.84%。

论文 Table III 在 KITTI Sync 07 上报告的 `t_rel` 是 1.01%。我们进一步核对了论文、官方 metadata、DROID 权重、GTSAM vio 分支、时间戳和 GT 帧偏移，均没有发现差异。论文也明确使用 10 Hz KITTI Sync IMU，因此不能把剩余差距归因于 IMU 频率不足。

最终结论是：公开代码条件下的前端工程复现、故障修复和评测链路已经完成，但公开仓库没有提供 Table III 的完整评测脚本、轨迹导出流程、实验 commit 和复现命令，因此无法严格对齐论文指标。

## 11. 素材与文件索引

### PPT 优先使用

- 最终汇报备注：`docs/PERSON_A_PPT_NOTES.md`
- 轨迹图：`media/figures/traj_kitti07_compare.png`
- 指标图：`media/figures/vio_vs_vo_bar.png`
- 轨迹回放：`media/videos/tracking_kitti07.mp4`
- 指标汇总：`results/frontend/a_frontend_summary.csv`

### 工程记录

- 详细 handoff：`docs/A_PROGRESS_HANDOFF.md`
- 早期审计：`docs/A_FRONTEND_AUDIT.md`
- 历史报告备注：`docs/A_FRONTEND_REPORT_NOTES.md`
- 环境记录：`docs/SETUP.md`
- KITTI 评测：`scripts/eval_kitti.py`
- GTSAM 兼容层：`third_party/VINGS-Mono/scripts/frontend/gtsam_compat.py`
- Dense BA 与边缘化：`third_party/VINGS-Mono/scripts/frontend/depth_video.py`

### 当前最佳结果目录

```text
results/frontend/kitti07_vio/06-01-10-50-kitti_sync-kitti07_vio-_official_tracking
```

## 12. 官方来源

- 论文：`https://arxiv.org/abs/2501.08286`
- 项目页：`https://vings-mono.github.io/`
- 作者仓库：`https://github.com/Fudan-MAGIC-Lab/VINGS-Mono`
- 数据准备说明：`https://github.com/Fudan-MAGIC-Lab/VINGS-Mono/blob/main/docs/PREPARE_DATA.md`
- 官方数据集：`https://huggingface.co/datasets/Promethe-us/VINGS-Mono-Dataset`
- 官方权重：`https://huggingface.co/Promethe-us/VINGS-Mono-Checkpoints/tree/main`
- 作者指定 GTSAM vio 分支：`https://github.com/Promethe-us/gtsam/tree/vio`
- KITTI VIO 公开 Issue：`https://github.com/Fudan-MAGIC-Lab/VINGS-Mono/issues/18`

