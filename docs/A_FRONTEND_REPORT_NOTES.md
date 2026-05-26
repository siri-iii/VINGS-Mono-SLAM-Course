# A 组员前端与系统部署工作记录

日期：2026-05-26

本文用于小组汇报准备，记录 A 负责的前端与系统部署部分实际完成了哪些工作、遇到了哪些问题、如何处理，以及最终可以在汇报中呈现的结果。PPT 中不需要全部展开，可以从本文挑选重点。

## 1. A 的任务定位

A 的主题是“视觉惯性前端：稠密 BA + 因子图融合”，对应论文 Sec. IV 的 VIO Front End。A 的工作主要承担基础设施和前端复现实验两部分：

- 搭建 AutoDL RTX 4090 服务器环境，保证后续 B/C/D 能复用同一套依赖。
- 跑通 VINGS-Mono 前端，重点验证 KITTI 07 上 mono-only 和 mono+IMU 两种模式。
- 尝试 Waymo Scene01 纯 mono 实验，并准备对应评估脚本。
- 生成前端相关指标表、轨迹图、对比图和演示视频，供汇报使用。
- 排查 VIO 运行中的 GTSAM 私有接口兼容问题。

## 2. 已完成的主要工作

### 2.1 环境与仓库部署

A 完成了远程服务器上的基本环境搭建和仓库准备：

- 服务器环境：AutoDL / SeetaCloud 远程服务器，GPU 为 RTX 4090。
- Python/Conda 环境：使用 `vings_vio` 环境运行 VINGS-Mono 前端。
- CUDA/PyTorch 相关依赖已满足前端运行需求。
- 准备了项目仓库和 VINGS-Mono 子模块。
- 编译并安装了 GTSAM，后续进一步切换和测试了 VINGS-Mono 需要的 vio 分支 GTSAM。
- 保留了 `docs/SETUP.md` 作为环境和踩坑记录。

相关交付物：

- `docs/SETUP.md`
- `third_party/VINGS-Mono/`
- `configs/kitti/`
- `/root/run_kitti_exp.sh`

说明：原计划里提到“AutoDL 镜像 ID”，目前仓库内没有记录明确镜像 ID。因此汇报时可以说“环境已在服务器搭好并可复用”，不要强调已经提交镜像 ID。

### 2.2 KITTI07 前端实验

A 针对 KITTI Odometry 07 做了多组前端实验：

1. KITTI07 mono-only 原始配置。
2. KITTI07 mono-only dense keyframe 配置。
3. KITTI07 mono+IMU 原始配置。
4. KITTI07 mono+IMU dense keyframe 配置。
5. KITTI07 mono+IMU guarded GTSAM 配置，即修复 native GTSAM `marginalizeOut` 崩溃后的可完成运行版本。

结果文件集中保存在：

- `results/frontend/kitti07_vo/`
- `results/frontend/kitti07_vo_dense/`
- `results/frontend/kitti07_vio/`
- `results/frontend/kitti07_vio_dense/`
- `results/frontend/a_frontend_summary.csv`

### 2.3 前端评估脚本

A 增加和修正了前端评估工具：

- `scripts/eval_kitti.py`：用于 KITTI 轨迹评估，输出 ATE、t_rel、r_rel。
- `scripts/plot_traj.py`：用于绘制轨迹对比图。
- `scripts/make_tracking_video.py`：用于从保存轨迹生成 replay 视频。
- `scripts/check_frontend_data.py`：用于检查 KITTI / Waymo 数据是否存在。
- `scripts/eval_waymo.py`：为 Waymo Scene01 数据到位后的评估预留。
- `scripts/run_waymo_exp.sh`：为 Waymo 实验预留运行脚本。

一个关键修正是：前端输出的位姿文件名是 camera timestamp，不能简单按第 N 行和 GT 第 N 行配对。因此 `eval_kitti.py` 改成按 KITTI camera timestamp 匹配预测轨迹和 GT。这一点很适合汇报中作为“评估修正”的技术细节。

### 2.4 可视化材料

A 已生成前端汇报可以使用的图和视频：

- `media/figures/traj_kitti07_compare.png`：KITTI07 轨迹对比图。
- `media/figures/vio_vs_vo_bar.png`：VO / VIO 指标对比柱状图。
- `media/videos/tracking_kitti07.mp4`：基于保存位姿生成的轨迹 replay 视频。

注意：`tracking_kitti07.mp4` 是轨迹 replay，不是原始 tracker GUI 录屏。汇报时可以说“轨迹回放视频”，避免说成实时前端界面录屏。

## 3. 最终指标记录

截至 2026-05-26，A 的前端结果汇总如下：

| 实验 | 匹配帧数 | ATE RMSE (m) | t_rel (%) | r_rel (deg/100m) | 结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| KITTI07 VO original | 233 | 19.485853 | 14.171275 | 3.201596 | 可运行，但未达论文目标 |
| KITTI07 VO dense | 727 | 13.043128 | 9.759937 | 3.002223 | VO 中最好，但仍未达标 |
| KITTI07 VIO original | 736 | 72.524843 | 63.152289 | 65.343844 | 可运行，但精度失败 |
| KITTI07 VIO dense | 737 | 72.210345 | 68.725937 | 65.566344 | 可运行，但精度失败 |
| KITTI07 VIO guarded GTSAM | 346 | 64.620664 | 61.143212 | 24.544240 | 崩溃问题解决，但精度仍未达标 |

论文目标中，KITTI07 VIO 的 t_rel 目标约为小于等于 1.5%。当前结果距离论文指标仍有较大差距。因此 A 的结论应该表述为：

> 前端工程链路和评估链路已经基本跑通，能生成轨迹、指标和可视化材料；但科学指标没有复现到论文水平，主要瓶颈集中在 VIO 初始化、IMU/GTSAM 因子图和边缘化质量上。

## 4. 遇到的问题与解决过程

### 4.1 KITTI 评估最初存在时间匹配问题

问题：

VINGS-Mono 前端输出的 `droid_c2w/*.txt` 不是按连续帧编号保存，而是按 camera timestamp 命名。如果直接按输出顺序和 KITTI GT 行号配对，会造成评估错位，得到不可信指标。

解决：

- 修改 `scripts/eval_kitti.py`。
- 读取 KITTI raw 数据中的 `camstamp.txt`。
- 将预测文件名中的 timestamp 四舍五入后映射到 GT frame index。
- 再计算 ATE、t_rel、r_rel。

结果：

- 评估流程更可信。
- 所有 A 的 KITTI 指标都重新按 timestamp 匹配生成。

汇报可讲：

> 我们发现前端保存轨迹使用的是相机时间戳，而不是帧序号，所以修正了评估脚本，按 timestamp 对齐预测和 GT，避免轨迹错配。

### 4.2 VO 能跑，但精度不达标

问题：

KITTI07 mono-only 能完成运行，但原始配置只匹配到 233 帧，ATE 和 t_rel 都明显高于论文目标。

尝试：

- 增加 dense keyframe 配置，降低 `keyframe_thresh` 到 1.0。
- 重新运行 KITTI07 VO dense。

结果：

- 匹配帧数从 233 提高到 727。
- ATE 从 19.49 m 改善到 13.04 m。
- t_rel 从 14.17% 改善到 9.76%。
- 仍未达到论文目标，但 dense 配置确实改善了 VO 轨迹覆盖和精度。

汇报可讲：

> 对 VO 部分，我们通过更密集的关键帧策略提升了轨迹覆盖和指标，但仍无法完全达到论文表格水平。

### 4.3 VIO 依赖 GTSAM 私有扩展接口

问题：

VINGS-Mono 的 VIO 前端依赖若干 GTSAM 私有扩展接口，例如：

- `marginalizeOut`
- `GTSAM2BA`
- `BA2GTSAM`
- `CustomHessianFactor`
- `CombinedImuFactor.evaluateErrorCustom`

普通 GTSAM 安装不一定包含这些接口，导致 VIO 路径无法稳定运行。

解决过程：

1. 检查当前环境中 GTSAM 是否存在上述接口。
2. 发现普通安装缺少部分 VINGS-Mono 需要的接口。
3. 切换并编译 GTSAM 子模块的 `origin/vio` 分支。
4. 确认 vio 分支 GTSAM 提供 `marginalizeOut`、`GTSAM2BA`、`BA2GTSAM`、`CustomHessianFactor` 等接口。
5. 修改 `scripts/frontend/gtsam_compat.py`，避免兼容层无条件覆盖 native GTSAM 函数。

相关提交：

- VINGS-Mono 子模块：`4d710b2 Guard VIO GTSAM marginalization`
- 主仓库：`9bc8384 Record member A guarded VIO run`

汇报可讲：

> VIO 不是简单配置问题，它依赖作者改过的 GTSAM 分支。我们切换到 vio 分支后补齐了私有接口，并修改兼容层，保证原生接口不会被旧 fallback 覆盖。

### 4.4 原生 `marginalizeOut` 出现段错误

问题：

切换到 vio 分支 GTSAM 后，KITTI07 VIO 在约 80 帧左右崩溃。最初日志没有 Python traceback，只看到进程提前结束。后来用 `PYTHONFAULTHANDLER=1` 复现，定位到：

- 崩溃位置：`third_party/VINGS-Mono/scripts/frontend/depth_video.py:1792`
- 崩溃调用：`gtsam.marginalizeOut(graph, marg_values, marg_paras)`
- 现象：C++ 层 segmentation fault，Python 无法捕获异常。

原因分析：

- vio 分支原生 `marginalizeOut` 的 C++ 实现对 marginalize keys / connected keys 的一致性检查不足。
- 当边缘化图中的 key 与线性化后的 key/dim map 不完全一致时，可能在 C++ 层越界或构造非法 Hessian，直接段错误。

解决：

- 保留 native `GTSAM2BA`，因为它是 VIO 坐标增量转换需要的原生实现。
- 对 `gtsam.marginalizeOut` 使用 Python fallback，绕过 C++ 段错误。
- 在 fallback 中对 keep keys 去重，并使用 public `GaussianFactorGraph` API 近似实现边缘化。
- 重新运行 KITTI07 VIO，成功越过 80 帧并完整跑到 1106/1106。

结果：

- 崩溃问题解决。
- 最新 guarded VIO 运行成功生成 346 个 timestamp-matched 位姿。
- 但精度仍未达标，ATE 64.62 m，t_rel 61.14%。

汇报可讲：

> VIO 的最大工程问题是 GTSAM 边缘化在 C++ 层段错误。我们通过 faulthandler 定位到 `depth_video.py:1792`，再将 `marginalizeOut` 切回 Python fallback，保留其他 native VIO 接口，最终让 KITTI07 VIO 能完整跑完。

### 4.5 Waymo Scene01 数据缺失

问题：

A 的任务里包含 Waymo Scene01 mono 实验，但服务器上没有 Waymo Scene01 数据。检查脚本显示缺少：

```text
/root/autodl-tmp/data/waymo/Scene01/color
/root/autodl-tmp/data/waymo/Scene01/pose
```

处理：

- 增加 `scripts/check_frontend_data.py` 显式检查数据是否存在。
- 增加 `scripts/eval_waymo.py` 和 `scripts/run_waymo_exp.sh`，数据补齐后可以直接运行。
- 在 `docs/A_FRONTEND_AUDIT.md` 中明确标记 Waymo 为 blocked，不再把它误报为完成。

汇报可讲：

> Waymo 部分不是代码没有准备，而是服务器缺少 Scene01 数据。我们已经把数据检查、运行脚本和评估脚本准备好，后续只要补齐数据即可跑。

## 5. 可以在 PPT 中重点展示的内容

建议 A 的 4-5 分钟汇报按以下结构组织：

### 第 1 页：A 的模块职责

可以讲：

- A 负责 VINGS-Mono 前端和系统部署。
- 论文前端由 DROID-SLAM 风格 Dense BA 和 IMU 因子图组成。
- 实验目标是 KITTI07 mono-only / mono+IMU，以及 Waymo Scene01 mono。

推荐图：

- 论文 VIO front end 结构图，或自己画一个“图像/IMU -> Dense BA -> GTSAM 因子图 -> 位姿”的流程图。

### 第 2 页：工程部署和评估链路

可以讲：

- 在 RTX 4090 服务器上完成环境部署。
- 修正 KITTI 评估方式：按 camera timestamp 对齐预测和 GT。
- 生成轨迹文件、指标表、轨迹图和 replay 视频。

可展示文件：

- `results/frontend/a_frontend_summary.csv`
- `media/figures/traj_kitti07_compare.png`
- `media/videos/tracking_kitti07.mp4`

### 第 3 页：实验结果

建议展示表格：

| 方法 | ATE RMSE | t_rel | r_rel | 结论 |
| --- | ---: | ---: | ---: | --- |
| VO original | 19.49 m | 14.17% | 3.20 | 可跑，未达标 |
| VO dense | 13.04 m | 9.76% | 3.00 | 最好 VO |
| VIO guarded | 64.62 m | 61.14% | 24.54 | 可跑，精度失败 |

讲法建议：

> dense keyframe 对 VO 有明显改善，但 VIO 指标仍然失败，说明问题不只是关键帧密度，而在 IMU 初始化、标定和边缘化链路。

### 第 4 页：问题排查和结论

重点讲两个技术问题：

1. KITTI 评估需要 timestamp 对齐。
2. VIO 的 GTSAM 私有接口和 `marginalizeOut` 段错误。

结论建议：

> A 的工程链路基本完成，能复现实验流程并输出可汇报材料；但指标没有达到论文水平。主要原因是 VIO 前端对作者定制 GTSAM 和数据标定非常敏感，当前服务器环境下只能保证跑通和定位问题，尚未复现论文精度。

## 6. A 任务当前完成度判断

可以判断为：

- 工程部署：基本完成。
- KITTI VO：完成运行与评估，但指标未达标。
- KITTI VIO：完成运行、修复崩溃、完成评估，但指标未达标。
- Waymo Scene01：脚本准备完成，但数据缺失，状态为 blocked。
- 图表和视频：完成。
- 汇报素材：基本齐全。

因此，A 的任务不是“论文指标完全复现成功”，而是“前端复现实验链路、排查过程、可视化和失败原因记录基本完成”。小组汇报时应采用诚实表述：

> 我们完成了 VINGS-Mono 前端的部署、运行、评估和关键问题排查；KITTI VO/VIO 均可输出结果，但没有达到论文指标。我们定位了主要工程瓶颈，包括 timestamp 评估对齐、GTSAM 私有接口缺失和 native marginalization 段错误，并给出了可运行的 guarded 版本。

## 7. 后续如果还要继续优化，优先方向

如果还有时间继续提升 A 的指标，优先级建议如下：

1. 检查 KITTI07 IMU 与相机外参、时间同步、重力方向初始化是否和论文/作者配置一致。
2. 对比作者官方 demo 数据的 VIO 初始化日志，重点看 `V-I successfully initialized` 前后的 scale、gravity、bias 数值是否异常。
3. 进一步排查 Python fallback `marginalizeOut` 与 native DM-VIO 风格边缘化的数值差异。
4. 使用更完整的 KITTI raw / odom 标定文件重新构造输入。
5. 如果 Waymo Scene01 数据补齐，优先跑 Waymo mono，作为 A 的另一条可展示结果线。

## 8. 相关文件索引

- A 审计总结：`docs/A_FRONTEND_AUDIT.md`
- 本汇报记录：`docs/A_FRONTEND_REPORT_NOTES.md`
- 环境记录：`docs/SETUP.md`
- KITTI 评估：`scripts/eval_kitti.py`
- Waymo 评估：`scripts/eval_waymo.py`
- 数据检查：`scripts/check_frontend_data.py`
- 汇总指标：`results/frontend/a_frontend_summary.csv`
- 轨迹图：`media/figures/traj_kitti07_compare.png`
- 指标图：`media/figures/vio_vs_vo_bar.png`
- replay 视频：`media/videos/tracking_kitti07.mp4`
- GTSAM 兼容层：`third_party/VINGS-Mono/scripts/frontend/gtsam_compat.py`

## 9. 可直接放进汇报的精简版发言稿

我负责的是 VINGS-Mono 的视觉惯性前端和系统部署部分。前端主要包括 DROID-SLAM 风格的稠密 BA，以及融合 IMU 预积分的 GTSAM 因子图优化。工程上，我在 RTX 4090 服务器上搭好了运行环境，并跑通了 KITTI07 的 mono-only 和 mono+IMU 前端实验，生成了轨迹、指标表、轨迹图和 replay 视频。

实验过程中我们遇到两个比较关键的问题。第一个是评估对齐问题：VINGS-Mono 保存的轨迹文件以相机时间戳命名，不能直接按行号和 KITTI GT 对齐，所以我修改了评估脚本，按 camera timestamp 匹配预测轨迹和 GT 后再计算 ATE、t_rel 和 r_rel。第二个是 VIO 的 GTSAM 兼容问题：普通 GTSAM 缺少作者使用的私有接口，切换到 vio 分支后，原生 `marginalizeOut` 又会在约 80 帧处发生 C++ 段错误。最后我用 `PYTHONFAULTHANDLER` 定位到 `depth_video.py:1792`，保留 native `GTSAM2BA`，但将 `marginalizeOut` 改为 Python fallback，使 KITTI07 VIO 能完整跑完。

最终结果是，前端链路已经基本跑通。VO dense 的 KITTI07 ATE 为 13.04 m，t_rel 为 9.76%；修复崩溃后的 VIO guarded run ATE 为 64.62 m，t_rel 为 61.14%。这些结果没有达到论文指标，说明当前 VIO 的初始化、标定或边缘化质量仍有较大差距。Waymo Scene01 部分因为服务器缺少数据，暂时标记为 blocked，但运行和评估脚本已经准备好。
