import os
import random
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms
from torchvision.transforms import functional as TF

class MyDataset(Dataset):
    def __init__(self, path, image_transform=None, label_transform=None, img_size=(512, 512), mode='train'):
        self.path = path
        self.name = os.listdir(os.path.join(path, 'image'))
        self.img_size = img_size
        self.mode = mode  # 'train' or 'val/test'

        self.image_transform = image_transform or transforms.Compose([
            transforms.ToTensor()
        ])
        self.label_transform = label_transform or (lambda x: TF.pil_to_tensor(x).long().squeeze(0))

    def __getitem__(self, idx):
        name = self.name[idx]
        image_path = os.path.join(self.path, 'image', name)
        label_path = os.path.join(self.path, 'label', name)

        image = Image.open(image_path).convert('RGB')
        label = Image.open(label_path)

        # ---------- 训练模式下进行数据增强 ----------
        if self.mode == 'train':
            # 随机水平翻转
            if random.random() > 0.5:
                image = TF.hflip(image)
                label = TF.hflip(label)
            # 随机垂直翻转
            if random.random() > 0.5:
                image = TF.vflip(image)
                label = TF.vflip(label)
            # 随机90度旋转
            if random.random() > 0.5:
                angle = random.choice([90, 180, 270])
                image = TF.rotate(image, angle)
                label = TF.rotate(label, angle, interpolation=TF.InterpolationMode.NEAREST)
            # 随机裁剪或缩放
            i, j, h, w = transforms.RandomCrop.get_params(image, output_size=self.img_size)
            image = TF.crop(image, i, j, h, w)
            label = TF.crop(label, i, j, h, w)
            # 颜色增强（光照变化）
            color_jitter = transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2)
            image = color_jitter(image)
        else:
            # 验证或测试阶段统一缩放中心裁剪
            image = TF.resize(image, self.img_size, interpolation=Image.BILINEAR)
            label = TF.resize(label, self.img_size, interpolation=Image.NEAREST)

        image = self.image_transform(image)
        label = self.label_transform(label)

        return image, label

    def __len__(self):
        return len(self.name)

if __name__ == '__main__':
    dataset = MyDataset(r'E:\zj-dataset\dataset\DFC22', img_size=(512, 512), mode='train')
    img, lbl = dataset[0]
    print(img.shape)   # torch.Size([3, 512, 512])
    print(lbl.shape)   # torch.Size([512, 512])
