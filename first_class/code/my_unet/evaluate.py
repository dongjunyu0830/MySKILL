import numpy as np
from tqdm import tqdm
from torch.utils.data import DataLoader
from model.unet import *
from datasetconfig.datasetmulticlass import MyDataset
from utils import calculate_metrics_multiclass


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
test_data_path = r'E:\zj-dataset\dataset\BDCI2017-spilt\test'
model_path = r'train_logs/pth/BDCI2017/BDCI2017_5_unet_best_f1.pth'
test_dataloader = DataLoader(MyDataset(test_data_path), batch_size=4, shuffle=True,drop_last=True)
num_classes = 5
model = unet(3, num_classes, 64).to(device)
model.load_state_dict(torch.load(model_path, map_location=device))
with torch.no_grad():
    ious = []
    recalls = []
    precisions = []
    f1_scores = []
    for imgs, labels in tqdm(test_dataloader, desc=f"Test", ncols=100):
        imgs, labels = imgs.to(device), labels.to(device)
        outputs = model(imgs)
        miou, pre, rec, f1 = calculate_metrics_multiclass(outputs, labels, num_classes)
        ious.append(miou)
        recalls.append(rec)
        precisions.append(pre)
        f1_scores.append(f1)

    mean_iou = np.mean(ious)
    mean_recall = np.mean(recalls)
    mean_precision = np.mean(precisions)
    mean_f1_score = np.mean(f1_scores)

print(f'平均交并比 (IoU): {mean_iou:.4f}')
print(f'平均召回率 (Recall): {mean_recall:.4f}')
print(f'平均准确率 (Precision): {mean_precision:.4f}')
print(f'平均F1分数 (F1 Score): {mean_f1_score:.4f}')