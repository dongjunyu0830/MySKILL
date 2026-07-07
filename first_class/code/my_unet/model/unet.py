import torch
from torch import nn
import torch.nn.functional as F

# 构建一个双层卷积
# U-Net 的基本构建块：两个卷积层 + 归一化 + 激活函数
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels, mid_channels=None):
        super(DoubleConv, self).__init__()
        if mid_channels is None:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            # 第1个卷积层：3×3 卷积核
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False),
            # 分组归一化  稳定训练，加速收敛
            nn.GroupNorm(mid_channels // 32, num_channels=mid_channels),
            # 激活函数 ReLU
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(out_channels // 32, num_channels=out_channels),
            nn.ReLU(inplace=True),
        )

    # 前向传播函数，定义了数据如何通过网络流动
    def forward(self, x):
        return self.double_conv(x)

# 下采样+双层卷积
class Down(nn.Sequential):
    def __init__(self, in_channels, out_channels):
        super(Down, self).__init__(
            # 2×2 最大池化：空间尺寸减半 
            nn.MaxPool2d(2, stride=2),
            DoubleConv(in_channels, out_channels)
        )

# 上采样+双层卷积
class Up(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Up, self).__init__()
        # 双线性插值上采样：将特征图尺寸放大2倍
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.conv = DoubleConv(in_channels, out_channels, (in_channels // 2))

    def forward(self, x1, x2):
        """
        x1 是来自上一个 decoder 层的输出,x1 = self.up(x1)：对 x1 做上采样，使它的空间尺寸变为原来的两倍，以便与 x2 拼接
        由于上采样后的 x1 与 x2（encoder 对应层的输出）尺寸可能有细微误差
        这里用 F.pad 让 x1 尺寸与 x2 对齐,保证上下左右等量补齐，使 x1 精确匹配 x2 的尺寸
        """
        x1 = self.up(x1)
        # [N, C, H, W]
        diff_y = x2.size()[2] - x1.size()[2]
        diff_x = x2.size()[3] - x1.size()[3]
        # padding_left, padding_right, padding_top, padding_bottom
        x1 = F.pad(x1, [diff_x // 2, diff_x - diff_x // 2,
                        diff_y // 2, diff_y - diff_y // 2])
        # 将上采样后的特征图 x1 与跳跃连接的 x2 进行通道维度上的拼接（dim=1），得到融合后的特征
        x = torch.cat([x2, x1], dim=1)
        x = self.conv(x)
        return x

# 最后的输出层卷积
class OutConv(nn.Sequential):
    def __init__(self, in_channels, num_classes):
        super(OutConv, self).__init__(
            # 1×1 卷积：将通道数从 in_channels 映射到 num_classes  每个像素位置输出一个长度为 num_classes 的向量
            nn.Conv2d(in_channels, num_classes, kernel_size=1)
        )

# 整个模型结构的搭建
class unet(nn.Module):
    def __init__(self, in_channels, num_classes, base_c):
        super(unet, self).__init__()
        # 输入图像的通道数,普通的RGB图像：in_channels=3
        self.in_channels = in_channels
        # 多分类：num_classes=类别数（例如遥感中：耕地、水体、建筑、林地、背景，共5类，则 num_classes=5）
        # 二分类：num_classes=1 或 2（通常设为1并用 sigmoid 输出）
        # 决定最后一个输出卷积层（out_conv）的输出通道数
        self.num_classes = num_classes
        # 基础通道数，是网络中第一个 DoubleConv 模块输出通道数，也作为通道扩张的基础倍数。
        # base_c=64 是标准 U-Net 设置
        self.base_c = base_c
        self.in_conv = DoubleConv(in_channels, base_c)
        self.down1 = Down(base_c, base_c * 2)
        self.down2 = Down(base_c * 2, base_c * 4)
        self.down3 = Down(base_c * 4, base_c * 8)
        self.down4 = Down(base_c * 8, base_c * 8)
        self.up1 = Up(base_c * 16, base_c * 4)
        self.up2 = Up(base_c * 8, base_c * 2)
        self.up3 = Up(base_c * 4, base_c)
        self.up4 = Up(base_c * 2, base_c)
        self.out_conv = OutConv(base_c, num_classes)

    def forward(self, x):
        e1 = self.in_conv(x)
        e2 = self.down1(e1)
        e3 = self.down2(e2)
        e4 = self.down3(e3)
        e5 = self.down4(e4)


        d5 = self.up1(e5, e4)
        d4 = self.up2(d5, e3)
        d3 = self.up3(d4, e2)
        d2 = self.up4(d3, e1)
        d1 = self.out_conv(d2)
        return d1

# 如下部分是测试网络结构的搭建是否有问题
if __name__ == '__main__':
    input = torch.randn(2, 3, 256, 256)
    model = unet(3, 1, 64)
    print(model(input).shape)
    # writer = SummaryWriter("logs")
    # writer.add_graph(model, input)
    # writer.close()

