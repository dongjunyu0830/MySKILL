import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class MobileNetUNet(nn.Module):
    """
    使用 MobileNetV2 作为编码器的 U-Net 风格语义分割模型。
    接口兼容现有的 unet(in_channels, num_classes, base_c)。
    base_c 参数在此模型中不使用（保留以兼容接口）。
    """

    def __init__(self, in_channels=3, num_classes=5, base_c=64):
        super().__init__()
        self.num_classes = num_classes

        # ---------- MobileNetV2 编码器 (ImageNet 预训练) ----------
        mobilenet = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

        # 当 in_channels != 3 时，替换第一层卷积
        # 处理非 RGB 输入
        if in_channels != 3:
            old_conv = mobilenet.features[0][0]
            mobilenet.features[0][0] = nn.Conv2d(
                in_channels, old_conv.out_channels,
                kernel_size=3, stride=2, padding=1, bias=False
            )

        # 切分 MobileNetV2 的 features 为 5 个编码阶段
        # 通道数来自 MobileNetV2 实际结构：
        # features[0]: 3→32(stride2) | features[1]: 32→16(stride1)
        self.enc0 = mobilenet.features[0:2]     # → 1/2 尺度, 16ch
        # features[2]: 16→24(stride2) | features[3]: 24→24(stride1)
        self.enc1 = mobilenet.features[2:4]     # → 1/4 尺度, 24ch
        # features[4]: 24→32(stride2) | features[5-6]: 32→32(stride1)
        self.enc2 = mobilenet.features[4:7]     # → 1/8 尺度, 32ch
        # features[7]: 32→64(stride2) | features[8-13]: 64→96(stride1)
        self.enc3 = mobilenet.features[7:14]    # → 1/16 尺度, 96ch
        # features[14]: 96→160(stride2) | features[15-17]: 160→320(stride1)
        self.enc4 = mobilenet.features[14:18]   # → 1/32 尺度, 320ch

        # ---------- 解码器 ----------
        self.dec4 = DecoderBlock(320, 96)          # 320→96
        self.dec3 = DecoderBlock(96 + 96, 64)      # d4(96) + skip enc3(96) = 192
        self.dec2 = DecoderBlock(64 + 32, 32)      # d3(64) + skip enc2(32) = 96
        self.dec1 = DecoderBlock(32 + 24, 16)      # d2(32) + skip enc1(24) = 56

        self.final_conv = nn.Sequential(
            nn.Conv2d(16 + 16, 16, kernel_size=3, padding=1),   # d1(16) + skip enc0(16) = 32
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, num_classes, kernel_size=1)
        )

    def forward(self, x):
        input_size = x.shape[2:]

        # Encoder
        e0 = self.enc0(x)      # 128×128, 24ch
        e1 = self.enc1(e0)     #  64×64, 32ch
        e2 = self.enc2(e1)     #  32×32, 64ch
        e3 = self.enc3(e2)     #  16×16, 96ch
        e4 = self.enc4(e3)     #   8×8, 320ch

        # Decoder (上采样 + skip connection)
        d4 = self.dec4(e4)                                      # 8×8
        d4 = F.interpolate(d4, e3.shape[2:], mode='bilinear', align_corners=True)
        d3 = self.dec3(torch.cat([d4, e3], dim=1))              # 16×16
        d3 = F.interpolate(d3, e2.shape[2:], mode='bilinear', align_corners=True)
        d2 = self.dec2(torch.cat([d3, e2], dim=1))              # 32×32
        d2 = F.interpolate(d2, e1.shape[2:], mode='bilinear', align_corners=True)
        d1 = self.dec1(torch.cat([d2, e1], dim=1))              # 64×64
        d1 = F.interpolate(d1, e0.shape[2:], mode='bilinear', align_corners=True)
        out = self.final_conv(torch.cat([d1, e0], dim=1))      # 128×128
        out = F.interpolate(out, input_size, mode='bilinear', align_corners=True)

        return out


class DecoderBlock(nn.Module):
    """解码器基本块：卷积 + BN + ReLU"""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


# 测试网络结构
if __name__ == '__main__':
    model = MobileNetUNet(3, 5)
    x = torch.randn(2, 3, 256, 256)
    y = model(x)
    print(f"输入: {x.shape} → 输出: {y.shape}")
    params = sum(p.numel() for p in model.parameters())
    print(f"参数量: {params / 1e6:.2f}M")
