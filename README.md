# VINGS-Mono SLAM 课程复现项目

本仓库是某高校 SLAM 课程期末小组项目（4 人小组），任务为复现论文 **VINGS-Mono: Visual-Inertial Gaussian Splatting Monocular SLAM in Large Scenes** (TRO 2025)。

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

## 仓库内容

- `VINGS.pdf` — 原始论文 PDF
- `SLAM复现论文作业要求.pdf` — 课程作业要求
- 后续将加入：环境配置脚本、复现代码、实验日志、报告等

## 复现计划

详见 [`docs/REPRODUCTION_PLAN.md`](docs/REPRODUCTION_PLAN.md)，里面包含：

- 课程目标对照（必做 / 可选）
- 论文核心方法 5 大模块速读
- 技术栈与依赖清单
- 硬件评估（显存需求 / 风险）
- 6 周阶段时间线（W1 环境 → W6 答辩）
- 4 人任务分工建议
- 复现成功的量化指标
- 已知坑与应急预案
- 最终交付清单

简要里程碑：

- [ ] **W1**：4 人环境搭好，跑通 Hotel demo
- [ ] **W2**：Hotel + SmallCity 两个官方 Demo 出结果 + 录屏
- [ ] **W3**：在 Waymo / KITTI 至少 1 个 scene 上复现 ATE 与 PSNR
- [ ] **W4**：完成 2 项消融实验（Score Manager + Pose Refinement）
- [ ] **W5**（冲分）：同济校园自采数据 / 手机端
- [ ] **W6**：报告 + PPT + 答辩 demo

## 小组分工

| 成员 | 分工 |
| ---- | ---- |
| TBD（组长 siri-iii） | 环境搭建 / 总协调 |
| TBD | 数据准备与预处理 |
| TBD | 论文方法解读与实验 |
| TBD | 报告撰写与可视化 |

## 致谢

本项目基于 [VINGS-Mono](https://github.com/Fudan-MAGIC-Lab/VINGS-Mono) 官方开源代码进行复现，所有原始代码与方法版权归原作者所有。
