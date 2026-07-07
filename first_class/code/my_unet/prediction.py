import os
import torch
from PIL import Image
from torchvision import transforms
import numpy as np
from PIL import Image as PILImage
from model.unet import unet

# img_path = r'E:\zj-dataset\dataset\BDCI2017-spilt\test\image\0_0_0.png'
img_path = r'E:\zj-dataset\dataset\BDCI2017-spilt\test\image\0_0_0.png'
save_path = 'vis'
saved_model_path = 'train_logs/pth/BDCI2017/BDCI2017_5_unet_best_f1.pth'
# 没有文件夹就创建
if not os.path.exists(save_path):
    os.mkdir(save_path)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 颜色表：你可以自定义颜色，下面是一个示例
color_map_BDCI = [
    (255, 255, 255),   # 类别 0：白色
    (128, 0, 0),       # 类别 1：暗红色
    (0, 128, 0),       # 类别 2：暗绿色
    (128, 128, 0),     # 类别 3：橄榄色
    (0, 0, 128)        # 类别 4：深蓝色
]

color_list_DFC22 = [
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
    (88, 176, 167)
]
# 设置类别数
num_classes=5
if num_classes==5:
    color_map=color_map_BDCI
else:
    color_map=color_list_DFC22

# 将预测类别图变为RGB彩图
def decode_segmap(pred_mask, color_map):
    pred_mask = pred_mask.squeeze().cpu().numpy().astype(np.uint8)  # (H, W)
    h, w = pred_mask.shape
    color_mask = np.zeros((h, w, 3), dtype=np.uint8)
    for cls_id, color in enumerate(color_map):
        color_mask[pred_mask == cls_id] = color
    return PILImage.fromarray(color_mask)
# ================数据预处理====================
img = Image.open(img_path)
transform = transforms.Compose([
    transforms.ToTensor()
])
img_tensor = transform(img).to(device)
# 将图像扩展为4维张量 [batch_size, channels, height, width]
img_tensor = img_tensor.unsqueeze(0)
# =================模型定义==================

model = unet(3,num_classes,64).to(device)
# 加载模型参数
model.load_state_dict(torch.load(saved_model_path, map_location=device))
# ==============模型预测以及图片可视化===========
with torch.no_grad():
    output = model(img_tensor)
    pred = torch.argmax(output, dim=1)  # 预测类别图

# 可视化和保存
pred_color = decode_segmap(pred, color_map)
# 只取文件名部分，不含路径
filename = os.path.basename(img_path)
pred_color.save(os.path.join(save_path, f'1_{filename}'))
print("Model prediction completed.")