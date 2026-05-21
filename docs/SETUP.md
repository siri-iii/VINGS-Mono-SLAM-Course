# VINGS-Mono 环境搭建（SETUP）

> 维护：**成员 A**。其他人遇到问题先看这份文档，再问。
>
> 时间预算：**D1–D3 共 3 天**。D3 晚 22:00 前必须制作出 AutoDL 镜像快照（关键里程碑）。

---

## 0. 速查：成员 B/C/D 怎么用 A 的镜像

> 这一节给 B/C/D 看的。等 A 做完 D3 任务后，按下面 3 步就能开始干活。

1. 在 AutoDL → "我的镜像" 里找到 A 分享的镜像（A 会在群里发镜像 ID）
2. 用这个镜像新开一台 4090 实例（按量付费）
3. SSH 上去后：
   ```bash
   cd /root/autodl-tmp/VINGS-Mono-SLAM-Course
   conda activate vings_vio
   git pull
   ```
4. 跑你自己的实验（B：`configs/hierarchical/smallcity.yaml`；C：`configs/kitti/...`；D：先用 demo 验证环境，自采数据另说）

---

## 1. AutoDL 选机指引（**A 第 1 步**）

### 1.1 注册 + 充值

- 网址：<https://www.autodl.com>
- 充值 ¥500（够 D1–D5 单卡用，后续 4 人并行再加）
- **学生认证**可以拿优惠券，记得申请

### 1.2 选实例

| 参数 | 推荐值 | 理由 |
| --- | --- | --- |
| GPU | **RTX 4090 (24GB)** 单卡 | 论文同款，能跑 KITTI 千万级 Gaussian |
| 计费 | **按量付费** | 灵活，环境装好就关机省钱 |
| 系统盘 | **30 GB**（免费） | 装 conda + 代码 |
| 数据盘 | **100 GB**（每月 ¥7） | 存 demo 数据 + checkpoints + 实验输出，**重要：**不随实例释放 |
| 区域 | 任选有 4090 的区 | 北京/上海/西北都行，看价格 |

### 1.3 选镜像（**最关键**）

> 镜像选错了，后面所有事都白干。

**推荐镜像**：

- **基础镜像 → PyTorch 2.0.1 → Python 3.9（cu118）**
- 或者 **Miniconda + Python 3.9 + cuda 11.8**

如果 AutoDL 没有完全匹配的，**就选 CUDA 11.8 + 任意 PyTorch**，我们自己装 PyTorch 2.0.1。**绝对不要选 CUDA 12.x** —— GTSAM vio 分支 + dbaf 在 12.x 上编不过。

---

## 2. 拉代码（**A 第 2 步**）

SSH 上 AutoDL 后：

```bash
# 切到数据盘（系统盘空间不够）
cd /root/autodl-tmp

# clone 我们的仓库（带 --recursive 拉嵌套 submodule）
git clone --recursive https://github.com/siri-iii/VINGS-Mono-SLAM-Course.git
cd VINGS-Mono-SLAM-Course

# 验证 submodule 是否拉全
git submodule status --recursive
# 应该看到 6 个嵌套模块（gtsam / dbaf / diff-surfel-rasterization / metric_modules / lietorch / eigen）
```

如果 GitHub 拉得慢，AutoDL 一般支持学术加速：

```bash
source /etc/network_turbo   # AutoDL 自带的学术加速
```

---

## 3. Conda 环境（**A 第 3 步**）

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono

# 按官方 set_env.sh 但分步跑，便于排错
conda create --name vings_vio python=3.9.19 -y
conda activate vings_vio

# PyTorch 2.0.1 + CUDA 11.8
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

# torch-scatter（必须匹配 PyTorch 2.0 + CUDA 11.8）
pip install torch-scatter==2.0.2 \
    -f https://data.pyg.org/whl/torch-2.0.2+cu118.html

# 其他依赖
pip install -r requirements.txt
```

### 3.1 验证 PyTorch + CUDA

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"
# 应该输出：2.0.1+cu118 True 11.8
```

---

## 4. 编译 dbaf（**A 第 4 步**）

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/submodules/dbaf
python setup.py install
# 注意：官方 set_env.sh 用了 sudo，AutoDL 的 conda 环境里直接 root，不要 sudo
```

如果报错找不到 `nvcc`：

```bash
which nvcc                                    # 看 nvcc 在哪
export CUDA_HOME=/usr/local/cuda-11.8         # 改成你 AutoDL 上的路径
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
# 然后重试 python setup.py install
```

如果报错 `RuntimeError: CUDA error: no kernel image is available`，是 CUDA arch 没设对：

```bash
# 4090 是 Ada Lovelace 架构，算力 8.9
export TORCH_CUDA_ARCH_LIST="8.9"
python setup.py install
```

---

## 5. 编译 GTSAM vio 分支（**最大的坑，留 1 天 buffer**）

> 这一步是整个项目最容易卡死人的。建议 A 单开一个终端 tab 编 GTSAM，主 tab 继续装其他东西，并行进行。

```bash
# 1) 装系统依赖（AutoDL Ubuntu 22.04）
apt update && apt install -y libboost-all-dev libeigen3-dev libtbb-dev cmake

# 2) clone vio 分支
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/submodules
rm -rf gtsam
git clone -b vio --recursive https://github.com/Promethe-us/gtsam.git
cd gtsam

# 3) 配置 + 编译
mkdir build && cd build
cmake .. -DGTSAM_BUILD_PYTHON=ON \
         -DGTSAM_PYTHON_VERSION=3.9 \
         -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF \
         -DGTSAM_BUILD_TESTS=OFF
make -j$(nproc)            # AutoDL 通常 8-16 核，这一步 30-60 分钟
make python-install        # 装到当前 conda 环境
```

验证：

```bash
python -c "import gtsam; print(gtsam.__version__)"
```

### 常见坑

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `Could NOT find Boost` | 系统少装 boost | `apt install libboost-all-dev` |
| `Eigen3 not found` | 系统少装 eigen | `apt install libeigen3-dev` |
| `Python.h: No such file` | 缺 Python 开发头 | `apt install python3.9-dev` |
| `make python-install` 装错了 Python 版本 | conda 环境没 activate | `conda activate vings_vio` 再跑 |
| 编译卡在某个 .cpp 几分钟 | 这是正常的（GTSAM 编译很慢） | 等着，**别 Ctrl+C** |

### 实在编不过的降级方案

如果 D2 晚还在卡，**先跳过 GTSAM**，按官方说法用纯 mono 模式跑（论文 SmallCity 就是 mono-only，不需要 IMU 因子图）。所有 yaml 里改 `mode: 'vo'` 就行。等 D3-D4 再回来补 GTSAM，**不阻塞 B/C/D**。

---

## 6. 下载预训练权重（**A 第 5 步**）

```bash
mkdir -p /root/autodl-tmp/VINGS-Mono-SLAM-Course/ckpts/lightglue
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/ckpts

# 国内访问 HuggingFace 慢，先设镜像
export HF_ENDPOINT=https://hf-mirror.com

# DROID-SLAM 前端权重
wget https://hf-mirror.com/Promethe-us/VINGS-Mono-Checkpoints/resolve/main/droid.pth

# Metric3D 单目深度先验（手机端 / 自采数据要用）
wget https://hf-mirror.com/Promethe-us/VINGS-Mono-Checkpoints/resolve/main/metric_depth_vit_small_800k.pth

# LightGlue（NVS Loop Closure 用）
cd lightglue
wget https://hf-mirror.com/Promethe-us/VINGS-Mono-Checkpoints/resolve/main/superpoint.onnx
wget https://hf-mirror.com/Promethe-us/VINGS-Mono-Checkpoints/resolve/main/superpoint_lightglue.onnx

# FastSAM（动态物体擦除用，可选）
cd ..
wget https://hf-mirror.com/Promethe-us/VINGS-Mono-Checkpoints/resolve/main/FastSAM-x.pt
```

验证：

```bash
ls -lh /root/autodl-tmp/VINGS-Mono-SLAM-Course/ckpts/
# droid.pth ~ 256 MB
# metric_depth_vit_small_800k.pth ~ 100 MB
# lightglue/superpoint.onnx ~ 5 MB
# lightglue/superpoint_lightglue.onnx ~ 50 MB
```

---

## 7. 下载 Hotel demo 数据（**A 第 6 步**）

```bash
mkdir -p /root/autodl-tmp/data/hotel
cd /root/autodl-tmp/data/hotel

# Hotel 数据集（RTG-SLAM 收集，作者上传到 HuggingFace）
# 在 https://huggingface.co/datasets/Promethe-us/VINGS-Mono-Dataset 找具体链接
# 需要先 agree license
```

> **TODO（A 填）**：实际下载命令在跑通后补到这里。

---

## 8. 改配置（**A 第 7 步**）

把 `third_party/VINGS-Mono/configs/rtg/hotel.yaml` **复制到我们仓库的 `configs/` 目录下再改**，不要直接改 submodule 内的文件（会污染 submodule 状态）。

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course
mkdir -p configs/rtg
cp third_party/VINGS-Mono/configs/rtg/hotel.yaml configs/rtg/hotel.yaml
```

要改的字段（4 处）：

```yaml
dataset:
  root: /root/autodl-tmp/data/hotel/                                    # ← 改

output:
  save_dir: /root/autodl-tmp/VINGS-Mono-SLAM-Course/results/hotel/      # ← 改

frontend:
  weight: /root/autodl-tmp/VINGS-Mono-SLAM-Course/ckpts/droid.pth       # ← 改

looper:
  lightglue_weight_dir: /root/autodl-tmp/VINGS-Mono-SLAM-Course/ckpts/lightglue/  # ← 改
```

---

## 9. 跑通 Hotel demo（**A 第 8 步，D3 关键里程碑**）

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono
conda activate vings_vio

python scripts/run.py /root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/rtg/hotel.yaml
```

成功标志：

- 终端打印进度（"keyframe XX", "rendering...", "score manager pruned XX gaussians" 之类）
- 30 帧之后不 crash
- `results/hotel/` 下出现 `trajectory.txt` 和 `gaussians.ply`

跑完后**截图终端 + ply 大小**，发到群里报喜。

---

## 10. 制作镜像快照（**A 第 9 步，D3 晚 22:00 前必须完成**）

```bash
# 1) 关闭所有跑着的进程
# 2) 清理临时文件
conda clean -a -y
pip cache purge
rm -rf /tmp/*

# 3) 在 AutoDL 控制台 → "我的镜像" → 保存为镜像
#    镜像名建议：vings-mono-d3-env-by-A
```

保存好后把镜像 ID 发到群里，B/C/D 各自开实例时选这个镜像即可。

---

## 11. 已知坑总表（持续更新）

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `nvcc not found` | CUDA 路径没设 | `export CUDA_HOME=/usr/local/cuda-11.8` |
| `torch-scatter` 装不上 | 版本号要严格匹配 | 用上面的具体命令，别 `pip install torch-scatter` 自动找最新 |
| GTSAM `Boost not found` | 系统少 boost | `apt install libboost-all-dev` |
| dbaf 编译 `no kernel image` | TORCH_CUDA_ARCH_LIST 没设 | `export TORCH_CUDA_ARCH_LIST="8.9"` |
| 跑 demo 时 `CUDA out of memory` | 帧太大或 keyframe 太多 | yaml 里 `frontend.buffer` 调小、`active_window` 调小 |
| HuggingFace 下载慢 | 国内访问慢 | `export HF_ENDPOINT=https://hf-mirror.com` |
| AutoDL 实例 SSH 断开 | 长跑任务被前台终止 | 用 `tmux` 或 `nohup ... &`，**绝对不要在裸 SSH 里跑长实验** |

> **A 跑通后补充**：在这一节加上实际遇到的坑 + 解决方法，注明日期。

---

## 12. A 的 D1–D3 自检 checklist

- [ ] AutoDL 账号注册 + 充值 + 学生认证（D1 上午）
- [ ] 开 4090 实例 + 选对镜像 + 挂数据盘（D1 上午）
- [ ] 拉代码 + 拉 submodule（D1 下午）
- [ ] Conda 环境 + PyTorch + 依赖（D1 下午）
- [ ] dbaf 编译通过（D1 晚 / D2 上午）
- [ ] GTSAM vio 分支编译通过（D2 全天，buffer 到 D3 上午）
- [ ] 权重 + Hotel 数据下载完（D2 晚）
- [ ] 改 yaml 路径（D3 上午）
- [ ] Hotel demo 跑通 30 帧不 crash（D3 下午）
- [ ] 制作镜像快照 + 群里发 ID（D3 晚 22:00 前）
- [ ] 更新本文档"已知坑总表"（D3 晚 / D4 早）

---

*最后更新：2026-05-19，by A。在 AutoDL 跑通后逐项更新。*

---

## 12.1 A 在 D3 实际踩坑补充（2026-05-21）

### 环境修复清单

以下为跑通 Hotel demo 实际遇到的坑，均已修复：

| 坑 | 现象 | 修复方式 |
| --- | --- | --- |
| `droid_backends` ImportError | `libc10.so: cannot open shared object file` | 运行前 `export LD_LIBRARY_PATH=<vings_vio>/torch/lib:$LD_LIBRARY_PATH` |
| `metric_modules` 找不到 | `ModuleNotFoundError: No module named metric_modules` | `metric_model.py` 硬编码了作者机器路径，已改为动态推算 submodules 目录 |
| `mmengine` / `mmcv` 缺失 | 导入 metric_modules 时报错 | `pip install mmengine==0.10.5 mmcv-full==1.7.2` |
| `setuptools` 太新导致 `pkg_resources` 问题 | `ImportError: cannot import name packaging from pkg_resources` | `pip install setuptools==59.5.0` |
| `html4vision` 缺失 | metric3d/mono/utils/visualization.py import 失败 | `pip install HTML4Vision` |
| `gtsam_compat` 找不到 | `depth_video.py` 直接 `import gtsam_compat` | 运行前 `export PYTHONPATH=$SCRIPTS:$SCRIPTS/frontend` |
| metric3d `mono_utils` 找不到 | `No module named metric_modules.metric3d.mono.mono_utils` | `ln -s mono/utils mono/mono_utils`（软链接） |
| metric 权重路径错误 | `RuntimeError: No weight found at scripts/ckpts/...` | `metric_model.py` 改为从 `cfg[frontend][weight]` 推算 ckpts 目录 |

### 最终运行命令

```bash
# 用提供的脚本（已包含所有环境变量设置）
/root/run_hotel_demo.sh

# 或手动：
TORCH_LIB=/root/miniconda3/envs/vings_vio/lib/python3.9/site-packages/torch/lib
SCRIPTS=/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts
export LD_LIBRARY_PATH=$TORCH_LIB:$LD_LIBRARY_PATH
export PYTHONPATH=$SCRIPTS:$SCRIPTS/frontend:$PYTHONPATH
cd $SCRIPTS
conda activate vings_vio
python run.py /root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/rtg/hotel.yaml
```

### ONNX Runtime 警告（非致命）

`libcufft.so.10: cannot open shared object file` — 这是 onnxruntime 的 CUDA provider 加载失败，LightGlue 会自动降级到 CPU 推理，**不影响建图结果**。

