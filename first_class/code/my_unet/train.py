import datetime
import os
from tqdm import tqdm
import numpy as np
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from model.unet import *
from datasetconfig.datasetmulticlass import MyDataset
#from datasetconfig.dataset import MyDataset
from utils import SoftIoULoss_multiclass,calculate_metrics_multiclass
"""
多分类的训练脚本
"""
# ==============================基础训练配置=============================
# 设备的选择
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# 数据路径的指定【加r的原因：在win中\的出现，会有字符转移的可能（如\t就会被理解为制表符），不做处理就会导致路径加载错误，加r就可以解决】
#train_data_path = r'/mnt/data/hyl_backup/code/mycodes/unet-new/DFC22-split/train'
#val_data_path = r'/mnt/data/hyl_backup/code/mycodes/unet-new/DFC22-split/val'

train_data_path = r'C:\Users\abc\Downloads\课程设计（数字工程）\自处理后的数据集和代码\BDCI2017-spilt\train'
val_data_path = r'C:\Users\abc\Downloads\课程设计（数字工程）\自处理后的数据集和代码\BDCI2017-spilt\val'
# 参数的保存位置
time = str(datetime.datetime.now().strftime('%m%d%H%M')) #获取当前月日时分
state_dict_path =os.path.join("save_pth", time)
# 创建这个文件夹，如果不存在就创建，存在就不创建
os.makedirs(state_dict_path, exist_ok=True)
# 日志的保存位置
logs_path = r'logs'
os.makedirs(logs_path, exist_ok=True)
# ===============================数据集的加载=============================
#train_dataloader = DataLoader(MyDataset(train_data_path,mode='train', img_size=(256, 256)), batch_size=16, shuffle=True)
#val_dataloader = DataLoader(MyDataset(val_data_path,mode='val', img_size=(256, 256)), batch_size=16, shuffle=False)
train_dataloader = DataLoader(MyDataset(train_data_path), batch_size=16, shuffle=True)
val_dataloader = DataLoader(MyDataset(val_data_path), batch_size=16, shuffle=False)
# ==============================模型及其相关工具的实例化=============================
# DFCC-12类（512,512），BDCI2017-5类（256，256）
num_classes = 5
lr=0.001
model = unet(3, num_classes, 64).to(device)
optimizer = optim.Adam(model.parameters(), lr=lr) #1e-6
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', factor=0.1, patience=10)
writer = SummaryWriter(logs_path)

# ===================== Training Loop =====================
epoch = 100
best_miou = 0.0
best_f1 = 0.0
print(f"Training on {device}")
print(f"训练轮次：{epoch}")
print(f"当前学习率：{lr}")
print(f"当前类别数：{num_classes }")
print(f"模型保存位置：{state_dict_path}")
print("开始训练！")
for i in range(epoch):
    print(f'\n================== Epoch: {i+1} ==================')
    model.train()
    total_train_loss = 0
    train_step=0
    for imgs, labels in tqdm(train_dataloader, desc=f"Epoch {i + 1} - Training", ncols=100):
        imgs, labels = imgs.to(device), labels.to(device)
        outputs = model(imgs)
        # loss = SoftIoULoss_multiclass(outputs, labels, num_classes)
        criterion = nn.CrossEntropyLoss(ignore_index=255)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_train_loss += loss.item()
        train_step += 1
    mean_train_loss = total_train_loss / train_step
    print(f"\nTrain Loss: {mean_train_loss:.4f}")
    writer.add_scalar("\ntrain_loss", mean_train_loss, i+1)

    # -------------------- Validation --------------------
    model.eval()
    total_val_loss = 0
    val_step=0
    all_miou, all_pre, all_rec, all_f1 = [], [], [], []
    with torch.no_grad():
        for imgs, labels in tqdm(val_dataloader, desc=f"Epoch {i + 1} - Validation", ncols=100):
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            # loss = SoftIoULoss_multiclass(outputs, labels, num_classes)
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

    print(f"\nValidation Loss: {mean_val_loss:.4f}")
    print(f"mIoU: {mean_miou:.4f} | Precision: {mean_precision:.4f} | Recall: {mean_recall:.4f} | F1: {mean_f1:.4f}")
    writer.add_scalar("val_loss", mean_val_loss, i+1)
    writer.add_scalar("mIoU", mean_miou, i+1)
    writer.add_scalar("Precision", mean_precision, i+1)
    writer.add_scalar("Recall", mean_recall, i+1)
    writer.add_scalar("F1", mean_f1, i+1)
    scheduler.step(mean_val_loss)

    if mean_miou > best_miou:
        best_miou = mean_miou
        torch.save(model.state_dict(), os.path.join(state_dict_path, 'unet_best_miou.pth'))
        print(f"\n✅ Saved Best Model with mIoU: {best_miou:.4f}")
    if mean_f1 > best_f1:
        best_f1 = mean_f1
        torch.save(model.state_dict(), os.path.join(state_dict_path, 'unet_best_f1.pth'))
        print(f"\n✅ Saved Best Model with mF1: {best_f1:.4f}")

    torch.save(model.state_dict(), os.path.join(state_dict_path, f'unet_epoch_{i+1}.pth'))

writer.close()