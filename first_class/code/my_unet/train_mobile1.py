import datetime
import os
from tqdm import tqdm
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from model.mobilenet_unet import MobileNetUNet
from datasetconfig.datasetmulticlass import MyDataset
# from datasetconfig.dataset import MyDataset   # 如需数据增强，取消此行注释并注释上行
from utils import calculate_metrics_multiclass

"""
MobileNetUNet 训练脚本
"""
# ============================== 基础训练配置 ==============================
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ---------- 数据路径 ----------
train_data_path = r'D:\study\UNet\WHDLD-spilt\train'
val_data_path = r'D:\study\UNet\WHDLD-spilt\val'

# ---------- 保存与日志 ----------
time_str = str(datetime.datetime.now().strftime('%m%d%H%M'))
state_dict_path = os.path.join("save_pth_mobile", time_str)
os.makedirs(state_dict_path, exist_ok=True)
logs_path = r'logs_mobile1'
os.makedirs(logs_path, exist_ok=True)

# ============================== 数据集的加载 ==============================
# 无数据增强（适合数据充足）
train_dataloader = DataLoader(MyDataset(train_data_path), batch_size=16, shuffle=True)
val_dataloader = DataLoader(MyDataset(val_data_path), batch_size=16, shuffle=False)

# 带数据增强（适合数据较少，取消注释使用）
# train_dataloader = DataLoader(MyDataset(train_data_path, mode='train', img_size=(256, 256)),
#                               batch_size=8, shuffle=True, drop_last=True)
# val_dataloader = DataLoader(MyDataset(val_data_path, mode='val', img_size=(256, 256)),
#                             batch_size=8, shuffle=False, drop_last=True)

# ============================== 模型与工具 ==============================
num_classes = 7
lr = 0.001
# MobileNetUNet(in_channels, num_classes)，base_c 参数保留兼容但不使用
model = MobileNetUNet(3, num_classes).to(device)
optimizer = optim.Adam(model.parameters(), lr=lr)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', factor=0.1, patience=10)
writer = SummaryWriter(logs_path)

# ============================== 训练循环 ==============================
epoch = 100
best_miou = 0.0
best_f1 = 0.0
print(f"Training on {device}")
print(f"训练轮次：{epoch}")
print(f"当前学习率：{lr}")
print(f"当前类别数：{num_classes}")
print(f"模型保存位置：{state_dict_path}")
print("开始训练！")

for i in range(epoch):
    print(f'\n================== Epoch: {i+1} ==================')
    model.train()
    total_train_loss = 0
    train_step = 0
    for imgs, labels in tqdm(train_dataloader, desc=f"Epoch {i+1} - Training", ncols=100):
        imgs, labels = imgs.to(device), labels.to(device)
        outputs = model(imgs)
        criterion = nn.CrossEntropyLoss(ignore_index=255)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_train_loss += loss.item()
        train_step += 1

    mean_train_loss = total_train_loss / train_step
    print(f"\nTrain Loss: {mean_train_loss:.4f}")
    writer.add_scalar("train_loss", mean_train_loss, i + 1)

    # -------------------- 验证 --------------------
    model.eval()
    total_val_loss = 0
    val_step = 0
    all_miou, all_pre, all_rec, all_f1 = [], [], [], []
    with torch.no_grad():
        for imgs, labels in tqdm(val_dataloader, desc=f"Epoch {i+1} - Validation", ncols=100):
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            criterion = nn.CrossEntropyLoss(ignore_index=255)
            loss = criterion(outputs, labels)
            total_val_loss += loss.item()
            miou, pre, rec, f1 = calculate_metrics_multiclass(outputs, labels, num_classes)
            all_miou.append(miou)
            all_pre.append(pre)
            all_rec.append(rec)
            all_f1.append(f1)
            val_step += 1

    mean_val_loss = total_val_loss / val_step
    mean_miou = np.mean(all_miou)
    mean_precision = np.mean(all_pre)
    mean_recall = np.mean(all_rec)
    mean_f1 = np.mean(all_f1)

    print(f"Validation Loss: {mean_val_loss:.4f}")
    print(f"mIoU: {mean_miou:.4f} | Precision: {mean_precision:.4f} | Recall: {mean_recall:.4f} | F1: {mean_f1:.4f}")
    writer.add_scalar("val_loss", mean_val_loss, i + 1)
    writer.add_scalar("mIoU", mean_miou, i + 1)
    writer.add_scalar("Precision", mean_precision, i + 1)
    writer.add_scalar("Recall", mean_recall, i + 1)
    writer.add_scalar("F1", mean_f1, i + 1)
    scheduler.step(mean_val_loss)

    if mean_miou > best_miou:
        best_miou = mean_miou
        torch.save(model.state_dict(), os.path.join(state_dict_path, 'mobilenet_unet_best_miou.pth'))
        print(f"✅ Saved Best Model with mIoU: {best_miou:.4f}")
    if mean_f1 > best_f1:
        best_f1 = mean_f1
        torch.save(model.state_dict(), os.path.join(state_dict_path, 'mobilenet_unet_best_f1.pth'))
        print(f"✅ Saved Best Model with mF1: {best_f1:.4f}")

    torch.save(model.state_dict(), os.path.join(state_dict_path, f'mobilenet_unet_epoch_{i+1}.pth'))

writer.close()
