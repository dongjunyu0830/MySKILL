import numpy as np
import torch
import torch.nn.functional as F
# 适用于二分类
def SoftIoULoss(pred, target):
    pred = torch.sigmoid(pred)
    smooth = 1
    intersection = pred * target
    loss = (intersection.sum() + smooth) / (pred.sum() + target.sum() - intersection.sum() + smooth)
    loss = 1 - loss.mean()
    return loss

# 多类计算损失
def SoftIoULoss_multiclass(pred, target, num_classes, ignore_index=255, smooth=1.0):
    """
    多类别 soft IoU 损失，支持 ignore_index。
    pred: [B, C, H, W]，softmax前 logits
    target: [B, H, W]，整数标签
    """
    pred = F.softmax(pred, dim=1)  # -> [B, C, H, W]

    # 创建有效掩码（非 ignore 像素）
    valid_mask = (target != ignore_index)

    # 为了 one-hot 不报错，先拷贝 target，将 ignore 处设为0（临时）
    target = target.clone()
    target[~valid_mask] = 0

    # One-hot 编码，并转换为 float 类型
    target_onehot = F.one_hot(target, num_classes=num_classes)  # -> [B, H, W, C]
    target_onehot = target_onehot.permute(0, 3, 1, 2).float()  # -> [B, C, H, W]

    # 加入 valid_mask 使得 ignore 的像素不参与计算
    valid_mask = valid_mask.unsqueeze(1).float()  # -> [B, 1, H, W]
    pred = pred * valid_mask
    target_onehot = target_onehot * valid_mask

    intersection = (pred * target_onehot).sum(dim=(2, 3))
    union = pred.sum(dim=(2, 3)) + target_onehot.sum(dim=(2, 3)) - intersection

    iou = (intersection + smooth) / (union + smooth)
    return 1 - iou.mean()

"""
评估指标的计算
名称	含义	举个例子（检测“变化”）
TP（True Positive）真正例	预测是 1，真实是 1	模型说有变化，实际确实有
FP（False Positive）假正例	预测是 1，真实是 0	模型说有变化，实际上没有（误报）
TN（True Negative）真负例	预测是 0，真实是 0	模型说没变化，确实没有
FN（False Negative）假负例	预测是 0，真实是 1	模型说没变化，实际上有（漏检）
====================
-Dice 系数（Dice coefficient）：
表示 预测区域和真实区域的重合程度，范围：0 到 1，越接近 1 越好
-精确率（Precision）：
模型说“有变化”的像素中，多少是真的有变化，高精确率意味着 误报少
-召回率（Recall）：
表示所有真实为 1 的像素中，模型找对了多少，高召回率意味着 漏检少
-特异度（Specificity）：
表示所有真实为 0 的像素中，模型准确识别为 0 的比例
"""
# 适用于二分类
def calculate_metrics(pred, target, threshold):
    pred = (pred > threshold).float()
    target = (target > threshold).float()

    # 将预测和标签二值化
    pred_flat = pred.view(-1)
    target_flat = target.view(-1)

    # 计算真正例、假正例、真负例、假负例
    tp = (pred_flat * target_flat).sum().item()
    fp = (pred_flat * (1 - target_flat)).sum().item()
    tn = ((1 - pred_flat) * (1 - target_flat)).sum().item()
    fn = ((1 - pred_flat) * target_flat).sum().item()

    # 计算评价指标
    dice = (2 * tp) / (2 * tp + fp + fn + 1e-8)
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    specificity = tn / (tn + fp + 1e-8)

    return dice, precision, recall, specificity

# 多类计算
def calculate_metrics_multiclass(pred, target, num_classes, ignore_index=255):
    """
    多类别评估指标：mIoU, Precision, Recall, F1，支持 ignore_index。
    pred: [B, C, H, W]，softmax前 logits
    target: [B, H, W]，整数标签
    """
    pred = torch.argmax(pred, dim=1)  # -> [B, H, W]
    target = target.long()

    # 忽略 ignore_index 像素
    mask = (target != ignore_index)
    pred = pred[mask]
    target = target[mask]

    ious, precisions, recalls, f1s = [], [], [], []

    for cls in range(num_classes):
        pred_cls = (pred == cls).float()
        target_cls = (target == cls).float()

        tp = (pred_cls * target_cls).sum()
        fp = (pred_cls * (1 - target_cls)).sum()
        fn = ((1 - pred_cls) * target_cls).sum()

        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)

        # intersection = (pred_cls * target_cls).sum()
        # union = pred_cls.sum() + target_cls.sum() - intersection
        # iou = (intersection + 1e-8) / (union + 1e-8)
        iou = tp / (tp + fp + fn + 1e-8)
        precisions.append(precision.item())
        recalls.append(recall.item())
        f1s.append(f1.item())
        ious.append(iou.item())

    mean_iou = np.mean(ious)
    mean_precision = np.mean(precisions)
    mean_recall = np.mean(recalls)
    mean_f1 = np.mean(f1s)

    return mean_iou, mean_precision, mean_recall, mean_f1