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

## 计划（占位，后续小组共同维护）

- [ ] 阅读并整理论文核心方法
- [ ] 按官方仓库（[Fudan-MAGIC-Lab/VINGS-Mono](https://github.com/Fudan-MAGIC-Lab/VINGS-Mono)）搭建 Python 3.9 + CUDA 11.8 环境
- [ ] 下载预训练权重（droid.pth、metric depth、SuperPoint+LightGlue）
- [ ] 跑通官方 Demo（SmallCity / Hotel）
- [ ] 在 KITTI / KITTI360 上复现指标
- [ ] 撰写实验报告 & 制作答辩 PPT

## 小组分工

| 成员 | 分工 |
| ---- | ---- |
| TBD（组长 siri-iii） | 环境搭建 / 总协调 |
| TBD | 数据准备与预处理 |
| TBD | 论文方法解读与实验 |
| TBD | 报告撰写与可视化 |

## 致谢

本项目基于 [VINGS-Mono](https://github.com/Fudan-MAGIC-Lab/VINGS-Mono) 官方开源代码进行复现，所有原始代码与方法版权归原作者所有。
