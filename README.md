# VINGS-Mono SLAM 课程复现项目

本仓库是同济大学 SE SLAM 课程期末小组项目（4 人小组），任务为复现论文 **VINGS-Mono: Visual-Inertial Gaussian Splatting Monocular SLAM in Large Scenes** (TRO 2025)。

## 论文信息

- **标题**: VINGS-Mono: Visual-Inertial Gaussian Splatting Monocular SLAM in Large Scenes
- **作者**: Ke Wu, Zicheng Zhang, Muer Tie, Ziqing Ai, Zhongxue Gan, Wenchao Ding
- **发表**: TRO 2025 / arXiv:2501.08286
- **官方仓库**: https://github.com/Fudan-MAGIC-Lab/VINGS-Mono

```bibtex
@article{wu2025vings,
  title={Vings-mono: Visual-inertial gaussian splatting monocular slam in large scenes},
  author={Wu, Ke and Zhang, Zicheng and Tie, Muer and Ai, Ziqing and Gan, Zhongxue and Ding, Wenchao},
  journal={arXiv preprint arXiv:2501.08286},
  year={2025}
}
```

## 复现计划

完整计划见 [`docs/REPRODUCTION_PLAN.md`](docs/REPRODUCTION_PLAN.md)。

**总盘子**：15 天 · AutoDL RTX 4090 · 4 人均衡分工 · 答辩 15–18 分钟。

**阶段摘要**：

| 阶段 | 内容 |
| --- | --- |
| **D1–D3** | A 搭环境 + 制作 AutoDL 镜像；B/C/D 论文精读 + 数据准备 |
| **D4–D6** | 4 人并行实验（前端 / 建图 / 回环 / 校园采集） |
| **D7–D9** | 消融实验 + 手机端联调 + 校园数据建图收尾 |
| **D10** | **写作 Freeze**（禁开新实验） |
| **D10–D13** | 报告 + PPT |
| **D14–D15** | 彩排 + buffer |

## 小组分工

每人 1 个独立任务包 + 1 个 PPT 章节（约 3 分 30 秒，4 页 PPT）。

| 成员 | 角色 | 负责模块 | 主要实验 | PPT 主题 |
| --- | --- | --- | --- | --- |
| **A**（组长 siri-iii） | 前端 & 系统部署 | DROID-SLAM DBA + IMU 因子图 + AutoDL 镜像 | KITTI/Waymo 前端 ATE/RPE 对比（论文表 II / III） | "视觉惯性前端：DBA + 因子图融合" |
| **B** | 2D 高斯建图核心 | Score Manager + Sample Rasterizer + Pose Refinement | Hotel/SmallCity demo + 3 项消融（论文表 VII / VIII + 图 11） | "2D 高斯建图：分数管理 + 采样光栅化 + 多帧位姿优化" |
| **C** | 回环 + 动态 + 长序列 | NVS Loop Closure + Dynamic Eraser | KITTI-08 长序列 + 回环对比 + BONN 动态实验（论文图 10 + 表 IV）+ Mesh 导出 | "大场景一致性：NVS 回环 + 动态物体擦除" |
| **D** | 实地应用 + 报告主笔 | 同济校园数据全流程 + 手机端联调 + 报告整体排版 | iPhone 采集 → VINGS-Mono 建图 + 官方 APK 推流到 AutoDL 服务端 | "实地落地：同济校园建图 + 手机端实时 SLAM" |

> **跨人协作点**：A 在 D6–D8 完成自己实验后，协助 D 配通手机端的 AutoDL 服务端。
>
> **关键节点**：A 必须在 D3 晚交付 AutoDL 镜像快照（阻塞 B/C/D 的所有实验）；D 必须在 D4 完成校园数据采集（受天气影响）；D10 写作 Freeze 是硬截止。

## 复现成功量化指标

对照论文表格设定 11 项硬指标（ATE / PSNR / 回环触发 / 手机端演示 / 校园数据等），**达标 ≥ 9/11** 即认定"复现成功"。完整指标见复现计划第 4 节。

## 克隆方式

> ⚠️ 官方仓库会以 git submodule 形式加在 `third_party/VINGS-Mono`（含嵌套子模块：GTSAM / 2DGS rasterizer 等）。clone 时**必须**带 `--recursive`：

```bash
git clone --recursive git@github.com:siri-iii/VINGS-Mono-SLAM-Course.git
# 如果已经 clone 但忘了 --recursive：
cd VINGS-Mono-SLAM-Course
git submodule update --init --recursive
```

## 目录结构

```
.
├── README.md
├── docs/
│   ├── VINGS.pdf                     # 原论文
│   ├── SLAM复现论文作业要求.pdf       # 课程作业要求
│   ├── REPRODUCTION_PLAN.md          # 复现计划
│   ├── SETUP.md                      # 环境搭建（A 维护）
│   ├── ABLATION.md                   # 消融结果（B 维护）
│   ├── REPORT.pdf                    # 最终报告（D 主笔）
│   └── SLIDES.pdf                    # 答辩 PPT
├── third_party/VINGS-Mono/           # 官方代码 submodule（D1 由 A 添加）
├── configs/                          # 我们改过的 yaml
├── scripts/                          # 辅助脚本（预处理 / 评测 / 可视化）
├── results/
│   ├── frontend/                     # A
│   ├── mapping/ + ablation/          # B
│   ├── loop/ + dynamic/              # C
│   ├── tongji_campus/ + mobile/      # D
└── media/                            # 录屏 + highlight reel
```

## 致谢

本项目基于 [VINGS-Mono](https://github.com/Fudan-MAGIC-Lab/VINGS-Mono) 官方开源代码进行复现，所有原始代码与方法版权归原作者所有。
