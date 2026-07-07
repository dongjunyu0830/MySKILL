# 后端服务（遥感语义分割）

最简 FastAPI 基础框架，用于给 Vue 前端提供接口。当前仅有健康检查，后续逐步接入模型推理。

## 环境

复用项目根目录的 Python 虚拟环境（已装 torch/pillow/numpy），再补装 fastapi、uvicorn。

```bash
# 在项目根目录激活 venv
source /Users/dongjunyu/project/home_work/venv/bin/activate

# 安装后端依赖
pip install -r vue_project/backend/requirements.txt
```

## 启动

```bash
cd vue_project/backend
uvicorn main:app --reload --port 8000
```

启动后：

- 根路径：http://localhost:8000/
- 健康检查：http://localhost:8000/api/health
- 交互式 API 文档（Swagger）：http://localhost:8000/docs

## 目录结构

```
backend/
├── main.py            # FastAPI 入口（当前含 / 与 /api/health）
├── requirements.txt   # 后端依赖
└── README.md
```

## 后续规划

- 加载 first_class/result 下各数据集的 UNet 权重（.pth）
- `POST /api/predict`：单图预测，返回预测图/叠加图/类别占比
- `GET /api/evaluate`：测试集评估，返回 mIoU/F1/Precision/Recall
- `GET /api/datasets`、`GET /api/models`：供前端下拉选择
