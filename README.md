# home_work

遥感语义分割课程作业仓库：基于 U-Net 在多个遥感数据集上完成训练与评估，并提供 Vue + FastAPI 可视化系统，支持单图预测、结果叠加与测试集指标展示。

## 项目概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 模型训练与评估 | `first_class/code/my_unet/` | U-Net 训练、预测、评估脚本及数据加载 |
| 训练产物 | `first_class/result/` | 权重（`.pth`）、指标、TensorBoard 日志、示例预测图 |
| 可视化前端 | `vue_project/visible-project/` | Vue 3 + Vite，单图预测 / 测试集评估页面 |
| 可视化后端 | `vue_project/backend/` | FastAPI，加载 `first_class/result` 权重并提供 REST API |
| 课程文档 | `second_class/` | 作业要求、实践报告模板等 |
| 额外数据（可选） | `extra_data/` | 自行下载的大体积数据集存放处（未入库） |

作业基本要求（节选）：理解 U-Net 全流程；使用 TensorBoard 观察训练曲线；在可视化界面中实现单图预测、预测叠加与测试集评估。详见 `second_class/作业要求.txt`。

---

## 目录结构

```
home_work/
├── README.md
├── requirements.txt          # Python 依赖（训练 + 推理）
├── .gitignore
├── first_class/
│   ├── 环境配置.md           # Conda / PyTorch 安装参考
│   ├── code/my_unet/         # 训练代码（已提交）
│   │   ├── train_mac.py      # 推荐：Mac/通用训练入口
│   │   ├── prediction_mac.py # 命令行单图预测
│   │   ├── evaluate_mac.py   # 命令行测试集评估
│   │   ├── model/            # U-Net 等模型定义
│   │   └── datasetconfig/    # 数据集读取
│   ├── result/               # 训练权重与指标（已提交）
│   ├── BDCI2017-spilt/       # 数据集（未提交，需自行准备）
│   ├── DFC22-split/          # 数据集（未提交，需自行准备）
│   └── WHDLD-spilt/          # 数据集（未提交，需自行准备）
├── vue_project/
│   ├── visible-project/      # 前端
│   └── backend/                # 后端 API
├── second_class/               # 课程材料
├── extra_data/                 # 额外数据集目录（未提交）
└── venv/                       # Python 虚拟环境（未提交）
```

---

## 可视化系统

### 项目位置

- **前端**：`vue_project/visible-project/`
  - `/predict`：选择数据集与模型，上传或选用示例图，查看原图 / 分割图 / 叠加图及类别占比
  - `/evaluate`：在测试集上计算 mIoU、Precision、Recall、F1
- **后端**：`vue_project/backend/`
  - 自动扫描 `first_class/result/<数据集>_*/checkpoints/unet_best_f1.pth` 加载最新权重
  - 数据集元信息（类别、颜色）定义在 `seg_core.py` 的 `DATASET_REGISTRY`

### 环境要求

- **Python** 3.9+（训练与后端）
- **Node.js** `^22.18.0` 或 `>=24.12.0`（见 `vue_project/visible-project/package.json`；仓库内 `.nvmrc` 为 `24`）

### 启动步骤

需要**两个终端**，均从仓库根目录开始。

**终端 1 — Python 后端（端口 8000）**

```bash
# 1. 创建并激活虚拟环境（首次）
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
pip install -r vue_project/backend/requirements.txt

# 3. 启动 API
cd vue_project/backend
uvicorn main:app --reload --port 8000
```

验证：浏览器打开 http://localhost:8000/api/health ，应返回 `{"status":"ok",...}`。

**终端 2 — Vue 前端（端口 5173）**

```bash
cd vue_project/visible-project
npm install
npm run dev
```

验证：浏览器打开 http://localhost:5173 。

前端默认请求 `http://localhost:8000`（可在 `vue_project/visible-project/.env` 中设置 `VITE_API_BASE` 覆盖）。

### 仅体验预测（无完整数据集）

仓库已提交三个数据集的**预训练权重**（`first_class/result/` 下各数据集的 `unet_best_f1.pth`）。因此：

- **上传自定义图片预测**：无需本地数据集，启动前后端后即可在「预测」页上传任意遥感图进行推理。
- **示例图列表 / 测试集评估**：依赖本地 `first_class/<数据集>/test/` 目录（见下文「未提交内容」），缺少时示例图为空、评估接口无法运行。

---

## 拉取仓库后：哪些内容未提交？

以下内容在 `.gitignore` 中排除，**不会随 `git clone` 下发**，需要自行准备：

| 路径 | 原因 | 影响 |
|------|------|------|
| `venv/`、`.venv/` | 虚拟环境 | 需本地 `python -m venv venv` 后安装依赖 |
| `node_modules/` | Node 依赖 | 前端目录执行 `npm install` |
| `first_class/BDCI2017-spilt/` | 原始数据集体积大 | 训练、示例图、测试集评估 |
| `first_class/DFC22-split/` | 同上 | 同上 |
| `first_class/WHDLD-spilt/` | 同上 | 同上 |
| `extra_data/` | 额外下载数据 | 自定义 / 第三方数据集 |
| `.env` | 本地环境变量 | 按需创建（如修改 API 地址） |

**已提交、拉取即可用：**

- 全部训练与推理代码（`first_class/code/my_unet/`）
- 预训练权重与训练记录（`first_class/result/` 下的 `.pth`、`metrics.csv`、`summary.txt` 等）
- 三张示例预测效果图（`first_class/result/predictions/`）
- 完整可视化前后端源码（`vue_project/`）

---

## `first_class` 目录是否需要完整？

**视使用场景而定：**

| 场景 | 是否需要完整 `first_class` 数据集目录 |
|------|--------------------------------------|
| 启动可视化 + 上传图片预测 | **否**。仅需 `first_class/result/` 中的权重（已提交） |
| 可视化「示例图」下拉 | **部分**。需要对应数据集的 `test/image/` |
| 可视化「测试集评估」 | **是**。需要 `test/image/` 与 `test/label/` 成对存在 |
| 重新训练 / 调参 | **是**。至少需要 `train/` 与 `val/`（含 `image/`、`label/` 子目录） |
| 命令行 `prediction_mac.py` / `evaluate_mac.py` | 预测单张图可指定任意路径；评估需要完整 `test/` |

### 数据集目录规范

将数据解压或放置到 `first_class/` 下，目录名须与代码一致：

```
first_class/
├── BDCI2017-spilt/     # 注意拼写为 spilt
│   ├── train/  {image/, label/}
│   ├── val/    {image/, label/}
│   └── test/   {image/, label/}
├── DFC22-split/
│   ├── train/  {image/, label/}
│   ├── val/    {image/, label/}
│   └── test/   {image/, label/}
└── WHDLD-spilt/
    ├── train/  {image/, label/}
    ├── val/    {image/, label/}
    └── test/   {image/, label/}   # 图像多为 .jpg，标签多为 .png
```

- 图像与标签**文件名一一对应**（WHDLD 的标签扩展名由 `datasetmulticlass.py` 自动处理）。
- BDCI2017：256×256，5 类；DFC22：512×512，12 类；WHDLD：256×256，7 类（含背景）。

数据集来源请按课程要求或官方渠道获取。若使用 LoveDA 等其他大体积数据，可在仓库根目录自行创建 `extra_data/` 存放，并裁剪为 256×256、整理为上述 `image/label` 结构后再用于训练。

---

## 自定义数据与训练模型

### 1. 使用现有三个数据集重新训练

```bash
source venv/bin/activate
cd first_class/code/my_unet
```

编辑 `train_mac.py` 顶部配置：

```python
DATASET = "WHDLD"          # "BDCI2017" | "DFC22" | "WHDLD"
EPOCHS = 10
LEARNING_RATE = 1e-3
# BATCH_SIZE_MAP 已按分辨率预设；DFC22 为 512×512，默认 batch 较小
```

执行训练：

```bash
python train_mac.py
```

输出目录：`first_class/result/<数据集>_<时间戳>/`

- `checkpoints/unet_best_f1.pth`、`unet_best_miou.pth` — 模型权重
- `metrics.csv` — 逐轮指标
- `logs/` — TensorBoard 日志

查看训练曲线：

```bash
tensorboard --logdir first_class/result
```

训练完成后**重启后端**，可视化系统会自动选用各数据集下**最新的** `unet_best_f1.pth`。

### 2. 命令行预测与评估

```bash
cd first_class/code/my_unet
python prediction_mac.py   # 修改顶部 DATASET、IMG_PATH、MODEL_PATH
python evaluate_mac.py     # 修改顶部 DATASET、MODEL_PATH
```

### 3. 接入全新自定义数据集

1. **准备数据**：在 `first_class/` 或 `extra_data/` 下按 `train/val/test` + `image/label` 结构存放。
2. **修改数据加载**（若扩展名或尺寸特殊）：参考 `datasetconfig/datasetmulticlass.py`、`dataset.py`。
3. **注册数据集**：
   - `train_mac.py`：在 `NUM_CLASSES_MAP`、`DATASET_DIR_MAP`、`BATCH_SIZE_MAP` 中增加条目；
   - `vue_project/backend/seg_core.py`：在 `DATASET_REGISTRY` 中增加 `id`、目录名、类别与颜色（供前端图例与叠加着色）。
4. **训练** → 权重写入 `first_class/result/<新数据集名>_*/checkpoints/`。
5. **重启后端**，前端即可在下拉框中看到新数据集（需存在对应权重文件）。

### 4. 超参数与模型结构实验

- 学习率、batch size、epoch：直接改 `train_mac.py` 顶部常量；历史实验日志见 `first_class/code/my_unet/train_logs/`。
- 数据增强：见 `datasetconfig/dataset.py`（翻转、旋转、裁剪、色彩扰动等）。
- 更换骨干或加注意力：在 `model/` 下扩展，并在训练脚本中替换 `unet(...)` 实例化；若要在可视化中支持多模型，需同步扩展 `seg_core.py` 与前端 `ModelSelector`。

更详细的 PyTorch / Conda 环境说明见 `first_class/环境配置.md`。

---

## Python 环境（训练与后端共用）

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

主要依赖：`torch`、`torchvision`、`numpy`、`pillow`、`tqdm`、`tensorboard`；后端另需 `fastapi`、`uvicorn`（见 `vue_project/backend/requirements.txt`）。

Apple Silicon 会自动使用 MPS；NVIDIA GPU 使用 CUDA；否则回退 CPU。

受限网络下可指定镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 开发与质量工具

```bash
source venv/bin/activate
pytest          # 测试
black .         # 格式化
flake8 .        # 静态检查
```

---

## 远程仓库

| 远程名 | 地址 |
|--------|------|
| `origin` | GitHub：`git@github.com:dongjunyu0830/MySKILL.git` |
| `gitee` | Gitee：`git@gitee.com:dongjunyu1231/MySKILL.git` |

可视化相关作业分支：`homeworkVisible`。

---

## 常见问题

**Q：克隆后前端能打开，但数据集下拉为空？**  
A：检查 `first_class/result/` 下是否存在对应数据集的 `checkpoints/unet_best_f1.pth`；并确认后端已启动且 `http://localhost:8000/api/health` 正常。

**Q：能预测上传的图片，但示例图和评估不可用？**  
A：需要自行补充 `first_class/<数据集>/test/` 下的 `image` 与 `label`，该部分未纳入 Git。

**Q：训练报错「找不到训练数据目录」？**  
A：确认数据集已解压到 `first_class/` 且目录名与 `DATASET_DIR_MAP` 一致（注意 `BDCI2017-spilt` 的拼写）。

**Q：修改后端 API 地址？**  
A：在前端目录创建 `.env`：`VITE_API_BASE=http://<host>:<port>`，然后重新 `npm run dev`。
