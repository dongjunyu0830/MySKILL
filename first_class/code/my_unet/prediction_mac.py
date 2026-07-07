"""
Mac 专用单图预测可视化脚本（不改动原有 prediction.py）

特点：
1. 自动选择设备：MPS > CUDA > CPU。
2. 使用项目内相对路径，通过 DATASET 一个变量切换数据集。
3. 默认自动定位 result/ 下最新一次训练的 unet_best_f1.pth；也可手动指定权重。
4. 默认对该数据集测试集中的第一张图预测；也可在 IMG_PATH 手动指定。
5. 预测的彩色分割图保存到 first_class/result/predictions/ 下。

用法：
    cd first_class/code/my_unet
    python prediction_mac.py
"""
import os

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from model.unet import unet
from train_mac import (
    select_device,
    get_project_root,
    NUM_CLASSES_MAP,
    DATASET_DIR_MAP,
)
from evaluate_mac import find_latest_checkpoint

# ============================== 用户配置 ==============================
# 可选："BDCI2017" | "DFC22" | "WHDLD"
DATASET = "WHDLD"

# 待预测图片路径：留空则自动取该数据集 test/image 下的第一张
IMG_PATH = ""

# 权重路径：留空则自动查找 result/ 下最新一次训练的 unet_best_f1.pth
MODEL_PATH = ""
# ====================================================================

# 各数据集的类别调色板（RGB）
COLOR_MAPS = {
    # BDCI2017：5 类
    "BDCI2017": [
        (255, 255, 255),   # 0 背景/其他 - 白
        (128, 0, 0),       # 1 - 暗红
        (0, 128, 0),       # 2 - 暗绿
        (128, 128, 0),     # 3 - 橄榄
        (0, 0, 128),       # 4 - 深蓝
    ],
    # WHDLD：7 类
    "WHDLD": [
        (0, 0, 0),         # 0
        (255, 0, 0),       # 1
        (255, 255, 0),     # 2
        (0, 255, 0),       # 3
        (0, 255, 255),     # 4
        (0, 0, 255),       # 5
        (255, 0, 255),     # 6
    ],
    # DFC22：12 类
    "DFC22": [
        (35, 31, 32),
        (219, 95, 87),
        (219, 151, 87),
        (219, 208, 87),
        (173, 219, 87),
        (117, 219, 87),
        (123, 196, 123),
        (88, 177, 88),
        (212, 246, 212),
        (176, 226, 176),
        (0, 128, 0),
        (88, 176, 167),
    ],
}


def decode_segmap(pred_mask, color_map):
    """将预测的类别图(H,W)转换为 RGB 彩色图。"""
    pred_mask = pred_mask.squeeze().cpu().numpy().astype(np.uint8)
    h, w = pred_mask.shape
    color_mask = np.zeros((h, w, 3), dtype=np.uint8)
    for cls_id, color in enumerate(color_map):
        color_mask[pred_mask == cls_id] = color
    return Image.fromarray(color_mask)


def main():
    device = select_device()
    project_root = get_project_root()
    num_classes = NUM_CLASSES_MAP[DATASET]
    color_map = COLOR_MAPS[DATASET]

    # 解析待预测图片
    img_path = IMG_PATH.strip()
    if not img_path:
        test_image_dir = os.path.join(
            project_root, DATASET_DIR_MAP[DATASET], "test", "image"
        )
        names = sorted(os.listdir(test_image_dir))
        if not names:
            raise FileNotFoundError(f"测试图像目录为空：{test_image_dir}")
        img_path = os.path.join(test_image_dir, names[0])
    if not os.path.isfile(img_path):
        raise FileNotFoundError(f"待预测图片不存在：{img_path}")

    # 解析权重
    model_path = MODEL_PATH.strip()
    if not model_path:
        model_path = find_latest_checkpoint(
            os.path.join(project_root, "result"), DATASET
        )
        if model_path is None:
            raise FileNotFoundError(
                "未找到已训练的权重，请先训练或在 MODEL_PATH 中指定。"
            )
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"权重文件不存在：{model_path}")

    save_dir = os.path.join(project_root, "result", "predictions")
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 60)
    print(f"数据集：{DATASET}（类别数 {num_classes}）")
    print(f"计算设备：{device}")
    print(f"输入图片：{img_path}")
    print(f"使用权重：{model_path}")
    print("=" * 60)

    # 预处理
    img = Image.open(img_path).convert("RGB")
    img_tensor = transforms.ToTensor()(img).unsqueeze(0).to(device)

    # 加载模型并预测
    model = unet(3, num_classes, 64).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    with torch.no_grad():
        output = model(img_tensor)
        pred = torch.argmax(output, dim=1)

    # 可视化保存
    pred_color = decode_segmap(pred, color_map)
    filename = os.path.basename(img_path)
    save_path = os.path.join(save_dir, f"{DATASET}_pred_{filename}")
    # 统一存为 png，避免 tif 等格式的兼容问题
    save_path = os.path.splitext(save_path)[0] + ".png"
    pred_color.save(save_path)
    print(f"预测完成，彩色分割图已保存到：{save_path}")


if __name__ == "__main__":
    main()
