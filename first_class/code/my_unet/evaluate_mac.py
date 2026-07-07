"""
Mac 专用测试集评估脚本（不改动原有 evaluate.py）

特点：
1. 自动选择设备：MPS > CUDA > CPU。
2. 使用项目内相对路径，通过 DATASET 一个变量切换数据集。
3. 默认自动定位 result/ 下最新一次训练的 unet_best_f1.pth；也可手动指定权重。
4. 在测试集上计算 mIoU / Precision / Recall / F1，并把结果写入该权重所在运行目录的
   eval_result.txt。

用法：
    cd first_class/code/my_unet
    python evaluate_mac.py
"""
import os
import sys
import glob
import datetime

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from model.unet import unet
from datasetconfig.datasetmulticlass import MyDataset
from utils import calculate_metrics_multiclass

# 复用 train_mac 的设备选择、路径与可 pickle 变换，保持行为一致
from train_mac import (
    select_device,
    get_project_root,
    label_to_tensor,
    image_to_tensor,
    NUM_CLASSES_MAP,
    DATASET_DIR_MAP,
)

# ============================== 用户配置 ==============================
# 可选："BDCI2017" | "DFC22" | "WHDLD"
DATASET = "WHDLD"

BATCH_SIZE = 8
NUM_WORKERS = min(4, (os.cpu_count() or 2))

# 权重路径：留空则自动查找 result/ 下最新一次训练的 unet_best_f1.pth
MODEL_PATH = ""
# ====================================================================


def find_latest_checkpoint(result_root, dataset):
    """在 result/<dataset>_*/checkpoints/ 中查找最新的 unet_best_f1.pth。"""
    pattern = os.path.join(result_root, f"{dataset}_*", "checkpoints", "unet_best_f1.pth")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    # 按修改时间取最新
    return max(candidates, key=os.path.getmtime)


def main():
    device = select_device()
    project_root = get_project_root()
    num_classes = NUM_CLASSES_MAP[DATASET]

    test_data_path = os.path.join(project_root, DATASET_DIR_MAP[DATASET], "test")
    if not os.path.isdir(test_data_path):
        raise FileNotFoundError(f"找不到测试数据目录：{test_data_path}")

    # 解析权重路径
    model_path = MODEL_PATH.strip()
    if not model_path:
        model_path = find_latest_checkpoint(
            os.path.join(project_root, "result"), DATASET
        )
        if model_path is None:
            raise FileNotFoundError(
                "未找到已训练的权重（result/<数据集>_*/checkpoints/unet_best_f1.pth）。"
                "请先训练，或在 MODEL_PATH 中手动指定权重路径。"
            )
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"权重文件不存在：{model_path}")

    test_dataloader = DataLoader(
        MyDataset(
            test_data_path,
            image_transform=image_to_tensor,
            label_transform=label_to_tensor,
        ),
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        drop_last=True,
        persistent_workers=(NUM_WORKERS > 0),
    )

    model = unet(3, num_classes, 64).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    print("=" * 60)
    print(f"数据集：{DATASET}（类别数 {num_classes}）")
    print(f"计算设备：{device}")
    print(f"测试数据：{test_data_path}")
    print(f"使用权重：{model_path}")
    print("=" * 60)
    print("开始评估！")

    ious, precisions, recalls, f1_scores = [], [], [], []
    with torch.no_grad():
        for imgs, labels in tqdm(
            test_dataloader,
            desc="Test",
            ncols=100,
            ascii=True,
            disable=not sys.stdout.isatty(),
        ):
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            miou, pre, rec, f1 = calculate_metrics_multiclass(
                outputs, labels, num_classes
            )
            ious.append(miou)
            precisions.append(pre)
            recalls.append(rec)
            f1_scores.append(f1)

    mean_iou = float(np.mean(ious)) if ious else 0.0
    mean_precision = float(np.mean(precisions)) if precisions else 0.0
    mean_recall = float(np.mean(recalls)) if recalls else 0.0
    mean_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0

    print("\n============== 测试集评估结果 ==============")
    print(f"平均交并比 (mIoU)     : {mean_iou:.4f}")
    print(f"平均精确率 (Precision): {mean_precision:.4f}")
    print(f"平均召回率 (Recall)   : {mean_recall:.4f}")
    print(f"平均 F1 分数 (F1)     : {mean_f1:.4f}")

    # 将评估结果写入权重所在的运行目录
    run_dir = os.path.dirname(os.path.dirname(model_path))
    out_file = os.path.join(run_dir, "eval_result.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"评估时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据集：{DATASET}（类别数 {num_classes}）\n")
        f.write(f"使用权重：{model_path}\n")
        f.write(f"mIoU：{mean_iou:.4f}\n")
        f.write(f"Precision：{mean_precision:.4f}\n")
        f.write(f"Recall：{mean_recall:.4f}\n")
        f.write(f"F1：{mean_f1:.4f}\n")
    print(f"\n结果已保存到：{out_file}")


if __name__ == "__main__":
    main()
