"""
Mac 专用训练脚本（不改动原有 train.py / train2.py / train_mobile1.py）

特点：
1. 自动选择设备：优先 Apple Silicon 的 MPS，其次 CUDA，最后 CPU。
2. 使用项目内相对路径，无需手动改 Windows 绝对路径。
3. 通过顶部 DATASET 一个变量即可切换 BDCI2017 / DFC22 / WHDLD 三个数据集。
4. 所有过程与结果数据统一保存在 first_class/result/<数据集>_<时间戳>/ 下：
   - logs/         过程数据：TensorBoard 日志
   - metrics.csv   过程数据：逐轮次的 loss 与各项指标
   - checkpoints/  结果数据：最佳模型权重（best_miou / best_f1）

用法：
    cd code/my_unet
    python train_mac.py
"""
import os
import sys
import csv
import datetime

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import transforms
from torchvision.transforms import functional as TF
from tqdm import tqdm

from model.unet import unet
from datasetconfig.datasetmulticlass import MyDataset
from utils import calculate_metrics_multiclass


# 标签变换：与原 datasetmulticlass 的默认行为一致，但用模块级函数而非 lambda，
# 以便在 num_workers>0（macOS spawn 多进程）时可被 pickle，从而启用并行数据加载。
def label_to_tensor(pil_img):
    return TF.pil_to_tensor(pil_img).long().squeeze(0)


# 图像变换同样显式指定为可 pickle 的对象
image_to_tensor = transforms.ToTensor()

# ============================== 用户配置 ==============================
# 可选："BDCI2017" | "DFC22" | "WHDLD"
DATASET = "WHDLD"

# 训练超参数
EPOCHS = 10
# 默认 batch_size（适用于 256×256 的数据集）。
# 加大可提升 MPS(GPU) 利用率、减少 Python 循环开销，从而加快训练。
BATCH_SIZE = 16
# 按数据集设置 batch_size：DFC22 是 512×512 大图，显存占用约为 256×256 的 4 倍，
# 用 16 会导致 MPS 内存溢出(OOM)，因此单独调小；其余 256×256 数据集用默认 16。
# 未在此列出的数据集会回退到 BATCH_SIZE。若仍 OOM 可继续下调。
BATCH_SIZE_MAP = {
    "BDCI2017": 16,  # 256×256
    "DFC22": 4,      # 512×512，大图
    "WHDLD": 16,     # 256×256
}
LEARNING_RATE = 1e-3
# 多进程并行加载数据，避免 GPU 等待数据。0 表示不并行；建议设为 CPU 核心数的一半左右。
NUM_WORKERS = min(4, (os.cpu_count() or 2))

# 各数据集的类别数（与原始脚本保持一致）
NUM_CLASSES_MAP = {
    "BDCI2017": 5,
    "DFC22": 12,
    "WHDLD": 7,
}

# 数据集目录名（相对项目根目录）
DATASET_DIR_MAP = {
    "BDCI2017": "BDCI2017-spilt",
    "DFC22": "DFC22-split",
    "WHDLD": "WHDLD-spilt",
}
# ====================================================================


def select_device():
    """自动选择可用的计算设备：MPS > CUDA > CPU。"""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_project_root():
    """返回项目根目录（当前脚本位于 code/my_unet/ 下，向上两级即根目录）。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def main():
    device = select_device()

    project_root = get_project_root()
    dataset_root = os.path.join(project_root, DATASET_DIR_MAP[DATASET])
    train_data_path = os.path.join(dataset_root, "train")
    val_data_path = os.path.join(dataset_root, "val")
    num_classes = NUM_CLASSES_MAP[DATASET]
    # 按数据集选择 batch_size（大图数据集用更小值以避免显存溢出）
    batch_size = BATCH_SIZE_MAP.get(DATASET, BATCH_SIZE)

    if not os.path.isdir(train_data_path):
        raise FileNotFoundError(f"找不到训练数据目录：{train_data_path}")
    if not os.path.isdir(val_data_path):
        raise FileNotFoundError(f"找不到验证数据目录：{val_data_path}")

    # 输出目录：first_class/result/<数据集>_<时间戳>/
    # 过程数据（TensorBoard 日志）与结果数据（模型权重、指标）统一存放于 result 下
    time_str = datetime.datetime.now().strftime("%m%d%H%M")
    result_root = os.path.join(project_root, "result")
    run_dir = os.path.join(result_root, f"{DATASET}_{time_str}")
    ckpt_dir = os.path.join(run_dir, "checkpoints")   # 结果数据：模型权重
    logs_dir = os.path.join(run_dir, "logs")          # 过程数据：训练日志
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # 数据加载（datasetmulticlass 兼容三个数据集的图/标签扩展名差异）
    # persistent_workers：跨轮次复用子进程，省去每轮重新启动的开销（需 num_workers>0）
    # pin_memory：CUDA 下加速 host->device 拷贝（MPS/CPU 无效，故按设备开启）
    loader_kwargs = dict(
        batch_size=batch_size,
        num_workers=NUM_WORKERS,
        drop_last=True,
        pin_memory=(device.type == "cuda"),
        persistent_workers=(NUM_WORKERS > 0),
    )
    train_dataloader = DataLoader(
        MyDataset(
            train_data_path,
            image_transform=image_to_tensor,
            label_transform=label_to_tensor,
        ),
        shuffle=True,
        **loader_kwargs,
    )
    val_dataloader = DataLoader(
        MyDataset(
            val_data_path,
            image_transform=image_to_tensor,
            label_transform=label_to_tensor,
        ),
        shuffle=False,
        **loader_kwargs,
    )

    # 模型与优化器
    model = unet(3, num_classes, 64).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, "min", factor=0.1, patience=10
    )
    criterion = nn.CrossEntropyLoss(ignore_index=255)
    writer = SummaryWriter(logs_dir)

    print("=" * 60)
    print(f"数据集：{DATASET}（类别数 {num_classes}）")
    print(f"计算设备：{device}")
    print(
        f"训练轮次：{EPOCHS} | batch_size：{batch_size} | "
        f"lr：{LEARNING_RATE} | 数据加载线程：{NUM_WORKERS}"
    )
    print(f"训练数据：{train_data_path}")
    print(f"输出目录：{run_dir}")
    print("=" * 60)
    print("开始训练！")

    # 过程数据：逐轮次指标写入 metrics.csv
    metrics_csv = os.path.join(run_dir, "metrics.csv")
    with open(metrics_csv, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(
            ["epoch", "train_loss", "val_loss", "mIoU", "precision", "recall", "f1"]
        )

    best_miou = 0.0
    best_f1 = 0.0

    for epoch in range(EPOCHS):
        print(f"\n================== Epoch: {epoch + 1}/{EPOCHS} ==================")
        # -------------------- 训练 --------------------
        model.train()
        total_train_loss = 0.0
        train_step = 0
        for imgs, labels in tqdm(
            train_dataloader,
            desc=f"Epoch {epoch + 1} - Training",
            ncols=100,
            file=sys.stdout,
            leave=True,
            dynamic_ncols=False,
            mininterval=0.5,
            ascii=True,
            disable=not sys.stdout.isatty(),
        ):
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_train_loss += loss.item()
            train_step += 1
        mean_train_loss = total_train_loss / max(train_step, 1)
        print(f"\nTrain Loss: {mean_train_loss:.4f}")
        writer.add_scalar("train_loss", mean_train_loss, epoch + 1)

        # -------------------- 验证 --------------------
        model.eval()
        total_val_loss = 0.0
        val_step = 0
        all_miou, all_pre, all_rec, all_f1 = [], [], [], []
        with torch.no_grad():
            for imgs, labels in tqdm(
                val_dataloader,
                desc=f"Epoch {epoch + 1} - Validation",
                ncols=100,
                file=sys.stdout,
                leave=True,
                dynamic_ncols=False,
                mininterval=0.5,
                ascii=True,
                disable=not sys.stdout.isatty(),
            ):
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                total_val_loss += loss.item()
                miou, pre, rec, f1 = calculate_metrics_multiclass(
                    outputs, labels, num_classes
                )
                all_miou.append(miou)
                all_pre.append(pre)
                all_rec.append(rec)
                all_f1.append(f1)
                val_step += 1

        mean_val_loss = total_val_loss / max(val_step, 1)
        mean_miou = float(np.mean(all_miou)) if all_miou else 0.0
        mean_precision = float(np.mean(all_pre)) if all_pre else 0.0
        mean_recall = float(np.mean(all_rec)) if all_rec else 0.0
        mean_f1 = float(np.mean(all_f1)) if all_f1 else 0.0

        print(f"\nValidation Loss: {mean_val_loss:.4f}")
        print(
            f"mIoU: {mean_miou:.4f} | Precision: {mean_precision:.4f} | "
            f"Recall: {mean_recall:.4f} | F1: {mean_f1:.4f}"
        )
        writer.add_scalar("val_loss", mean_val_loss, epoch + 1)
        writer.add_scalar("mIoU", mean_miou, epoch + 1)
        writer.add_scalar("Precision", mean_precision, epoch + 1)
        writer.add_scalar("Recall", mean_recall, epoch + 1)
        writer.add_scalar("F1", mean_f1, epoch + 1)
        scheduler.step(mean_val_loss)

        # 追加当前轮次指标到 metrics.csv
        with open(metrics_csv, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                epoch + 1,
                f"{mean_train_loss:.6f}",
                f"{mean_val_loss:.6f}",
                f"{mean_miou:.6f}",
                f"{mean_precision:.6f}",
                f"{mean_recall:.6f}",
                f"{mean_f1:.6f}",
            ])

        # -------------------- 保存模型 --------------------
        if mean_miou > best_miou:
            best_miou = mean_miou
            torch.save(model.state_dict(), os.path.join(ckpt_dir, "unet_best_miou.pth"))
            print(f"\n[已保存] 最佳 mIoU 模型：{best_miou:.4f}")
        if mean_f1 > best_f1:
            best_f1 = mean_f1
            torch.save(model.state_dict(), os.path.join(ckpt_dir, "unet_best_f1.pth"))
            print(f"[已保存] 最佳 F1 模型：{best_f1:.4f}")

    writer.close()

    # 结果数据：写入训练总结
    with open(os.path.join(run_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"数据集：{DATASET}（类别数 {num_classes}）\n")
        f.write(f"计算设备：{device}\n")
        f.write(f"训练轮次：{EPOCHS} | batch_size：{batch_size} | lr：{LEARNING_RATE}\n")
        f.write(f"最佳 mIoU：{best_miou:.4f}\n")
        f.write(f"最佳 F1：{best_f1:.4f}\n")

    print("\n训练完成！")
    print(f"最佳 mIoU：{best_miou:.4f} | 最佳 F1：{best_f1:.4f}")
    print(f"过程与结果数据保存在：{run_dir}")


if __name__ == "__main__":
    main()
