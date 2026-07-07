"""
遥感语义分割可视化系统 - 后端服务

提供数据集/模型/示例图/单图预测/测试集评估接口，供 Vue 前端调用。
模型与权重复用 first_class 下已训练的 UNet（见 seg_core.py）。

启动：
    uvicorn main:app --reload --port 8000
"""
from typing import Optional
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image

import seg_core

app = FastAPI(title="遥感语义分割后端", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "遥感语义分割后端已启动", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok", "device": str(seg_core.DEVICE)}


@app.get("/api/datasets")
def get_datasets():
    """返回有权重、可用于推理的数据集（含类别与颜色）。"""
    result = []
    for ds_id in seg_core.available_datasets():
        meta = seg_core.DATASET_REGISTRY[ds_id]
        result.append(
            {
                "id": ds_id,
                "name": meta["name"],
                "numClasses": len(meta["classes"]),
                "description": meta["description"],
                "classes": meta["classes"],
            }
        )
    return result


@app.get("/api/models")
def get_models(dataset: Optional[str] = None):
    """返回可用模型。当前仅训练了 U-Net。"""
    if dataset is not None and seg_core.find_latest_checkpoint(dataset) is None:
        return []
    return [{"id": "unet", "name": "U-Net", "description": "编码器-解码器 + 跳跃连接。"}]


@app.get("/api/samples")
def get_samples(request: Request, dataset: str, limit: int = 12):
    """返回某数据集测试集的示例图（name + 原图 URL）。"""
    if dataset not in seg_core.DATASET_REGISTRY:
        raise HTTPException(status_code=404, detail="未知数据集")
    base = str(request.base_url).rstrip("/")
    names = seg_core.list_samples(dataset, limit)
    return [
        {
            "id": f"{dataset}/{name}",
            "name": name,
            "thumbnailUrl": f"{base}/api/image?dataset={dataset}&name={name}",
        }
        for name in names
    ]


@app.get("/api/image")
def get_image(dataset: str, name: str):
    """返回测试集原图字节。"""
    path = seg_core.original_image_path(dataset, name)
    if path is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(path)


@app.post("/api/predict")
async def post_predict(
    dataset: str = Form(...),
    model: str = Form("unet"),
    sample: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """单图预测：sample=测试集图片名，或上传 file。返回预测/叠加图与类别占比。"""
    if dataset not in seg_core.DATASET_REGISTRY:
        raise HTTPException(status_code=404, detail="未知数据集")
    if seg_core.find_latest_checkpoint(dataset) is None:
        raise HTTPException(status_code=400, detail="该数据集暂无已训练模型")

    # 载入待预测图片
    if file is not None:
        content = await file.read()
        try:
            image = Image.open(BytesIO(content))
        except Exception:
            raise HTTPException(status_code=400, detail="无法解析上传的图片")
    elif sample is not None:
        path = seg_core.original_image_path(dataset, sample)
        if path is None:
            raise HTTPException(status_code=404, detail="示例图片不存在")
        image = Image.open(path)
    else:
        raise HTTPException(status_code=400, detail="需要提供 sample 或上传 file")

    return seg_core.predict(dataset, image)


@app.get("/api/evaluate")
def get_evaluate(dataset: str, model: str = "unet", limit: int = 60):
    """在测试集（子集）上评估，返回 mIoU/Precision/Recall/F1 与逐类指标。"""
    if dataset not in seg_core.DATASET_REGISTRY:
        raise HTTPException(status_code=404, detail="未知数据集")
    if seg_core.find_latest_checkpoint(dataset) is None:
        raise HTTPException(status_code=400, detail="该数据集暂无已训练模型")
    return seg_core.evaluate(dataset, limit=limit)
