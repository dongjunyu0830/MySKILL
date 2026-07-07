import os
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms
from torchvision.transforms import functional as TF
"""
多类别分类
"""

def default_image_transform():
    return transforms.Compose([
        # 修改大小为256*256
        # transforms.Resize((256, 256)),
        transforms.ToTensor(),  # 图像归一化（适用于 RGB 图像）
    ])


def default_label_transform():
    return transforms.Compose([
        # transforms.Resize((256, 256), interpolation=Image.NEAREST),  # 缩放标签图，保持标签整数
        transforms.Lambda(lambda x: TF.pil_to_tensor(x).long().squeeze(0))  # 转为整数 tensor，shape [H, W]
    ])



class MyDataset(Dataset):
    def __init__(self, path, image_transform=None, label_transform=None):
        self.path = path
        self.name = os.listdir(os.path.join(path, 'image'))
        if image_transform is not None:
            self.image_transform = image_transform
        else:
            self.image_transform = default_image_transform()
        if label_transform is not None:
            self.label_transform = label_transform
        else:
            self.label_transform = default_label_transform()

    def __getitem__(self, idx):
        name = self.name[idx]
        image_path = os.path.join(self.path, 'image', name)
        #label_path = os.path.join(self.path, 'label', name)
        # WHDLD 数据集的标签是 .png 格式，而图像是 .jpg 格式，所以这里需要替换后缀名
        label_path = os.path.join(self.path, 'label', name.replace('.jpg', '.png')) 

        image = Image.open(image_path).convert('RGB')  # 彩色图
        label = Image.open(label_path)                 # 不转换模式，保留原值

        image = self.image_transform(image)
        label = self.label_transform(label)

        return image, label

    def __len__(self):
        return len(self.name)

if __name__ == '__main__':
    data = MyDataset(r'E:\zj-dataset\dataset\CCF-training')
    image, label = data[0]
    print(image.shape)
    print(label.shape)
    print(len(data))
