"""
后端核心：加载已训练的 UNet 权重，提供预测与评估能力。

复用 first_class/code/my_unet 下的模型与数据加载代码，不改动原文件。
"""
import os
import sys
import glob
import time
import base64
from io import BytesIO
from functools import lru_cache

import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from torchvision.transforms import functional as TF
from torch.utils.data import DataLoader

# ------------------------------------------------------------------
# 路径与模块接入
# ------------------------------------------------------------------
# 本文件位于 vue_project/backend/，向上两级到项目根目录 home_work
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, "..", ".."))
MYUNET_DIR = os.path.join(PROJECT_ROOT, "first_class", "code", "my_unet")
RESULT_DIR = os.path.join(PROJECT_ROOT, "first_class", "result")

# 接入 first_class 的代码，以便 import model.unet 等
if MYUNET_DIR not in sys.path:
    sys.path.insert(0, MYUNET_DIR)

from model.unet import unet  # noqa: E402
from datasetconfig.datasetmulticlass import MyDataset  # noqa: E402


# ------------------------------------------------------------------
# 设备
# ------------------------------------------------------------------
def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


DEVICE = select_device()


# ------------------------------------------------------------------
# 数据集注册表（id / 名称 / 目录 / 类别与调色板）
# 调色板与 first_class 的 prediction_mac.py 对齐。
# ------------------------------------------------------------------
def _rgb(hex_list):
    return hex_list


DATASET_REGISTRY = {
    "BDCI2017": {
        "name": "BDCI2017",
        "dir": "BDCI2017-spilt",
        "description": "CCF 大数据比赛遥感数据，256×256，5 类地物。",
        "eval_batch": 8,
        "classes": [
            {"id": 0, "name": "其他 other", "color": "#ffffff"},
            {"id": 1, "name": "植被 vegetation", "color": "#008000"},
            {"id": 2, "name": "建筑 building", "color": "#800000"},
            {"id": 3, "name": "水体 water", "color": "#000080"},
            {"id": 4, "name": "道路 road", "color": "#808000"},
        ],
    },
    "DFC22": {
        "name": "DFC22",
        "dir": "DFC22-split",
        "description": "MiniFrance-DFC22 航空影像，512×512，12 类土地覆盖。",
        "eval_batch": 4,
        "classes": [
            {"id": 0, "name": "无数据", "color": "#231f20"},
            {"id": 1, "name": "城市", "color": "#db5f57"},
            {"id": 2, "name": "工业", "color": "#db9757"},
            {"id": 3, "name": "矿山", "color": "#dbd057"},
            {"id": 4, "name": "人造", "color": "#addb57"},
            {"id": 5, "name": "耕地", "color": "#75db57"},
            {"id": 6, "name": "永久作物", "color": "#7bc47b"},
            {"id": 7, "name": "牧场", "color": "#58b158"},
            {"id": 8, "name": "森林", "color": "#d4f6d4"},
            {"id": 9, "name": "草本", "color": "#b0e2b0"},
            {"id": 10, "name": "裸地", "color": "#008000"},
            {"id": 11, "name": "水域", "color": "#58b0a7"},
        ],
    },
    "WHDLD": {
        "name": "WHDLD",
        "dir": "WHDLD-spilt",
        "description": "武汉大学 WHDLD 数据集，256×256，6 类土地覆盖（含背景共 7 通道）。",
        "eval_batch": 8,
        "classes": [
            {"id": 0, "name": "背景 background", "color": "#000000"},
            {"id": 1, "name": "裸土 bare soil", "color": "#ff0000"},
            {"id": 2, "name": "建筑 building", "color": "#ffff00"},
            {"id": 3, "name": "人行道 pavement", "color": "#00ff00"},
            {"id": 4, "name": "道路 road", "color": "#00ffff"},
            {"id": 5, "name": "植被 vegetation", "color": "#0000ff"},
            {"id": 6, "name": "水体 water", "color": "#ff00ff"},
        ],
    },
}


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def num_classes_of(dataset_id: str) -> int:
    return len(DATASET_REGISTRY[dataset_id]["classes"])


def color_map_of(dataset_id: str):
    return [_hex_to_rgb(c["color"]) for c in DATASET_REGISTRY[dataset_id]["classes"]]


# ------------------------------------------------------------------
# 权重发现与模型缓存
# ------------------------------------------------------------------
def find_latest_checkpoint(dataset_id: str):
    """定位 result/<dataset>_*/checkpoints/unet_best_f1.pth 中最新的一个。"""
    pattern = os.path.join(RESULT_DIR, f"{dataset_id}_*", "checkpoints", "unet_best_f1.pth")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def available_datasets():
    """返回有权重、可用于推理的数据集 id 列表。"""
    return [d for d in DATASET_REGISTRY if find_latest_checkpoint(d) is not None]


@lru_cache(maxsize=8)
def load_model(dataset_id: str):
    """按数据集加载并缓存模型。"""
    ckpt = find_latest_checkpoint(dataset_id)
    if ckpt is None:
        raise FileNotFoundError(f"数据集 {dataset_id} 未找到已训练权重")
    n = num_classes_of(dataset_id)
    model = unet(3, n, 64).to(DEVICE)
    model.load_state_dict(torch.load(ckpt, map_location=DEVICE))
    model.eval()
    return model


# ------------------------------------------------------------------
# 图片工具
# ------------------------------------------------------------------
def _pil_to_data_uri(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def decode_segmap(pred_mask: np.ndarray, color_map) -> Image.Image:
    h, w = pred_mask.shape
    color = np.zeros((h, w, 3), dtype=np.uint8)
    for cls_id, c in enumerate(color_map):
        color[pred_mask == cls_id] = c
    return Image.fromarray(color)


# ------------------------------------------------------------------
# 测试集目录 / 示例图
# ------------------------------------------------------------------
def test_image_dir(dataset_id: str) -> str:
    return os.path.join(PROJECT_ROOT, "first_class", DATASET_REGISTRY[dataset_id]["dir"], "test", "image")


def list_samples(dataset_id: str, limit: int = 12):
    d = test_image_dir(dataset_id)
    if not os.path.isdir(d):
        return []
    names = sorted(
        f for f in os.listdir(d)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
    )
    return names[:limit]


def original_image_path(dataset_id: str, name: str):
    """安全地返回测试集原图路径（防目录穿越）。"""
    base = test_image_dir(dataset_id)
    safe = os.path.basename(name)
    path = os.path.join(base, safe)
    if not os.path.isfile(path):
        return None
    return path


# ------------------------------------------------------------------
# 预测
# ------------------------------------------------------------------
_to_tensor = transforms.ToTensor()


def predict(dataset_id: str, pil_image: Image.Image) -> dict:
    model = load_model(dataset_id)
    color_map = color_map_of(dataset_id)
    classes = DATASET_REGISTRY[dataset_id]["classes"]

    image = pil_image.convert("RGB")
    tensor = _to_tensor(image).unsqueeze(0).to(DEVICE)

    t0 = time.time()
    with torch.no_grad():
        output = model(tensor)
        pred = torch.argmax(output, dim=1)[0].cpu().numpy().astype(np.uint8)
    if DEVICE.type == "mps":
        torch.mps.synchronize()
    infer_ms = int((time.time() - t0) * 1000)

    # 彩色分割图
    pred_color = decode_segmap(pred, color_map)
    # 叠加图（原图与分割图各半透明混合）
    overlay = Image.blend(image, pred_color.resize(image.size), alpha=0.5)

    # 各类别占比
    total = pred.size
    distribution = []
    for c in classes:
        ratio = float((pred == c["id"]).sum()) / total if total else 0.0
        if ratio > 0:
            distribution.append(
                {
                    "classId": c["id"],
                    "className": c["name"],
                    "color": c["color"],
                    "ratio": ratio,
                }
            )
    distribution.sort(key=lambda x: x["ratio"], reverse=True)

    return {
        "originalUrl": _pil_to_data_uri(image),
        "predictionUrl": _pil_to_data_uri(pred_color),
        "overlayUrl": _pil_to_data_uri(overlay),
        "distribution": distribution,
        "inferenceMs": infer_ms,
    }


# ------------------------------------------------------------------
# 评估
# ------------------------------------------------------------------
def evaluate(dataset_id: str, limit: int = 60, ignore_index: int = 255) -> dict:
    model = load_model(dataset_id)
    n = num_classes_of(dataset_id)
    classes = DATASET_REGISTRY[dataset_id]["classes"]
    test_path = os.path.join(PROJECT_ROOT, "first_class", DATASET_REGISTRY[dataset_id]["dir"], "test")

    batch = DATASET_REGISTRY[dataset_id]["eval_batch"]
    loader = DataLoader(MyDataset(test_path), batch_size=batch, shuffle=False, num_workers=0)

    tp = np.zeros(n, dtype=np.float64)
    fp = np.zeros(n, dtype=np.float64)
    fn = np.zeros(n, dtype=np.float64)
    seen = 0

    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(DEVICE)
            outputs = model(imgs)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            labs = labels.numpy()
            mask = labs != ignore_index
            for c in range(n):
                pred_c = (preds == c) & mask
                targ_c = (labs == c) & mask
                tp[c] += np.logical_and(pred_c, targ_c).sum()
                fp[c] += np.logical_and(pred_c, ~targ_c).sum()
                fn[c] += np.logical_and(~pred_c, targ_c).sum()
            seen += imgs.shape[0]
            if seen >= limit:
                break
    if DEVICE.type == "mps":
        torch.mps.synchronize()

    eps = 1e-8
    per_class = []
    for i, c in enumerate(classes):
        iou = tp[i] / (tp[i] + fp[i] + fn[i] + eps)
        precision = tp[i] / (tp[i] + fp[i] + eps)
        recall = tp[i] / (tp[i] + fn[i] + eps)
        f1 = 2 * precision * recall / (precision + recall + eps)
        per_class.append(
            {
                "classId": c["id"],
                "className": c["name"],
                "color": c["color"],
                "iou": float(iou),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            }
        )

    def mean(key):
        return float(np.mean([p[key] for p in per_class])) if per_class else 0.0

    return {
        "datasetId": dataset_id,
        "modelId": "unet",
        "numSamples": seen,
        "mIoU": mean("iou"),
        "precision": mean("precision"),
        "recall": mean("recall"),
        "f1": mean("f1"),
        "perClass": per_class,
    }
