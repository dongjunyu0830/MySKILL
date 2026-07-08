#!/usr/bin/env python3
"""
生成课堂最终汇报 PPTX（基础文字排版版）。

用法:
    source venv/bin/activate
    pip install python-pptx
    python second_class/generate_pptx.py

输出: second_class/课堂最终汇报PPT.pptx
"""

from pathlib import Path

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

OUTPUT_PATH = Path(__file__).parent / "课堂最终汇报PPT.pptx"

FONT_NAME = "PingFang SC"
FONT_FALLBACK = "Microsoft YaHei"

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

FONT_COVER_TITLE = Pt(32)
FONT_COVER_SUB = Pt(20)
FONT_PAGE_TITLE = Pt(28)
FONT_BODY = Pt(18)
FONT_TABLE = Pt(16)
FONT_SECTION = Pt(20)

MARGIN_LEFT = Inches(0.8)
MARGIN_TOP = Inches(0.5)
CONTENT_WIDTH = Inches(11.7)


def _set_font(run, size, bold=False):
    run.font.name = FONT_NAME
    run.font.size = size
    run.font.bold = bold


def _add_centered_slide(prs, lines, title_size=FONT_COVER_TITLE, body_size=FONT_COVER_SUB):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    total_lines = len(lines)
    box_height = Inches(0.5) * total_lines + Inches(0.3)
    top = (SLIDE_HEIGHT - box_height) / 2
    textbox = slide.shapes.add_textbox(MARGIN_LEFT, top, CONTENT_WIDTH, box_height)
    tf = textbox.text_frame
    tf.word_wrap = True

    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = PP_ALIGN.CENTER
        size = title_size if i == 0 else body_size
        bold = i == 0 or (i == len(lines) - 1 and line == "Q&A")
        _set_font(p.runs[0], size, bold=bold)

    return slide


def _add_bullet_slide(prs, title, bullets, sections=None):
    """sections: optional list of (section_title, [bullets]) for grouped content."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(MARGIN_LEFT, MARGIN_TOP, CONTENT_WIDTH, Inches(0.8))
    tp = title_box.text_frame.paragraphs[0]
    tp.text = title
    _set_font(tp.runs[0], FONT_PAGE_TITLE, bold=True)

    body_top = Inches(1.3)
    body_box = slide.shapes.add_textbox(MARGIN_LEFT, body_top, CONTENT_WIDTH, Inches(5.8))
    tf = body_box.text_frame
    tf.word_wrap = True

    if sections:
        first = True
        for sec_title, sec_bullets in sections:
            if not first:
                tf.add_paragraph()
            sp = tf.paragraphs[-1] if first else tf.add_paragraph()
            sp.text = sec_title
            sp.level = 0
            _set_font(sp.runs[0], FONT_SECTION, bold=True)
            first = False
            for item in sec_bullets:
                bp = tf.add_paragraph()
                bp.text = item
                bp.level = 0
                _set_font(bp.runs[0], FONT_BODY)
    else:
        for i, item in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item
            p.level = 0
            _set_font(p.runs[0], FONT_BODY)

    return slide


def _add_table_slide(prs, title, headers, rows, bullets_before=None, bullets_after=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(MARGIN_LEFT, MARGIN_TOP, CONTENT_WIDTH, Inches(0.8))
    tp = title_box.text_frame.paragraphs[0]
    tp.text = title
    _set_font(tp.runs[0], FONT_PAGE_TITLE, bold=True)

    y = Inches(1.2)

    if bullets_before:
        bullet_box = slide.shapes.add_textbox(MARGIN_LEFT, y, CONTENT_WIDTH, Inches(1.8))
        tf = bullet_box.text_frame
        tf.word_wrap = True
        for i, item in enumerate(bullets_before):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item
            _set_font(p.runs[0], FONT_BODY)
        y += Inches(0.35 * len(bullets_before) + 0.3)

    n_rows = len(rows) + 1
    n_cols = len(headers)
    table_height = Inches(0.35 * n_rows)
    table = slide.shapes.add_table(n_rows, n_cols, MARGIN_LEFT, y, CONTENT_WIDTH, table_height).table

    for ci, header in enumerate(headers):
        cell = table.cell(0, ci)
        cell.text = header
        _set_font(cell.text_frame.paragraphs[0].runs[0], FONT_TABLE, bold=True)

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.cell(ri + 1, ci)
            cell.text = val
            _set_font(cell.text_frame.paragraphs[0].runs[0], FONT_TABLE)

    if bullets_after:
        y_after = y + table_height + Inches(0.2)
        bullet_box = slide.shapes.add_textbox(MARGIN_LEFT, y_after, CONTENT_WIDTH, Inches(2.5))
        tf = bullet_box.text_frame
        tf.word_wrap = True
        for i, item in enumerate(bullets_after):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item
            _set_font(p.runs[0], FONT_BODY)

    return slide


def _add_dual_table_slide(prs, title, table1_title, headers1, rows1, table2_title, headers2, rows2):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_box = slide.shapes.add_textbox(MARGIN_LEFT, MARGIN_TOP, CONTENT_WIDTH, Inches(0.6))
    tp = title_box.text_frame.paragraphs[0]
    tp.text = title
    _set_font(tp.runs[0], FONT_PAGE_TITLE, bold=True)

    y = Inches(1.0)

    sec1 = slide.shapes.add_textbox(MARGIN_LEFT, y, CONTENT_WIDTH, Inches(0.4))
    sp = sec1.text_frame.paragraphs[0]
    sp.text = table1_title
    _set_font(sp.runs[0], FONT_SECTION, bold=True)
    y += Inches(0.35)

    n_rows1 = len(rows1) + 1
    h1 = Inches(0.32 * n_rows1)
    t1 = slide.shapes.add_table(n_rows1, len(headers1), MARGIN_LEFT, y, CONTENT_WIDTH, h1).table
    for ci, h in enumerate(headers1):
        c = t1.cell(0, ci)
        c.text = h
        _set_font(c.text_frame.paragraphs[0].runs[0], FONT_TABLE, bold=True)
    for ri, row in enumerate(rows1):
        for ci, val in enumerate(row):
            c = t1.cell(ri + 1, ci)
            c.text = val
            _set_font(c.text_frame.paragraphs[0].runs[0], FONT_TABLE)

    y += h1 + Inches(0.25)

    sec2 = slide.shapes.add_textbox(MARGIN_LEFT, y, CONTENT_WIDTH, Inches(0.4))
    sp2 = sec2.text_frame.paragraphs[0]
    sp2.text = table2_title
    _set_font(sp2.runs[0], FONT_SECTION, bold=True)
    y += Inches(0.35)

    n_rows2 = len(rows2) + 1
    h2 = Inches(0.32 * n_rows2)
    t2 = slide.shapes.add_table(n_rows2, len(headers2), MARGIN_LEFT, y, CONTENT_WIDTH, h2).table
    for ci, h in enumerate(headers2):
        c = t2.cell(0, ci)
        c.text = h
        _set_font(c.text_frame.paragraphs[0].runs[0], FONT_TABLE, bold=True)
    for ri, row in enumerate(rows2):
        for ci, val in enumerate(row):
            c = t2.cell(ri + 1, ci)
            c.text = val
            _set_font(c.text_frame.paragraphs[0].runs[0], FONT_TABLE)

    return slide


def build_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # 1 封面
    _add_centered_slide(
        prs,
        [
            "基于 U-Net 的遥感影像语义分割系统",
            "课程设计（数字工程）课堂汇报",
            "汇报人：陈诗雅 | 学号：2023211857",
            "人工智能学院 | 空间信息与数字技术 | 04072301",
            "指导教师：朱盼盼",
            "2026 年 7 月",
        ],
    )

    # 2 目录
    _add_bullet_slide(
        prs,
        "目录",
        [
            "1. 研究背景与任务定义",
            "2. 技术方案与系统架构",
            "3. 数据预处理与模型设计",
            "4. 训练实验与超参数设置",
            "5. 评估结果与 TensorBoard 分析",
            "6. 可视化系统演示",
            "7. 总结、不足与展望",
            "8. Q&A",
        ],
    )

    # 3 研究背景与意义
    _add_bullet_slide(
        prs,
        "研究背景与意义",
        [
            "土地利用与遥感解译在城市规划、环境监测、农业监测等领域具有重要应用价值",
            "语义分割任务：对图像每个像素进行分类，输入 RGB 遥感图，输出类别掩码",
            "课程目标：掌握从数据预处理、模型构建、训练评估到可视化展示的完整深度学习工程链路",
        ],
    )

    # 4 任务与数据集
    _add_table_slide(
        prs,
        "任务与数据集",
        ["数据集", "类别数", "分辨率", "本项目用途"],
        [
            ["BDCI2017", "5", "256×256", "主要训练与评估"],
            ["DFC22", "12", "512×512", "可拓展"],
            ["WHDLD", "6-7", "256×256", "可拓展"],
        ],
        bullets_before=[
            "主要数据集：BDCI2017（CCF 大数据竞赛遥感数据）",
            "图像规格：256×256 RGB",
            "5 类地物：其他(0)、植被(1)、建筑(2)、水体(3)、道路(4)",
            "数据划分：train / val / test（训练约 85 batch，验证 37 batch，测试 74 张）",
        ],
    )

    # 5 系统总体架构
    _add_bullet_slide(
        prs,
        "系统总体架构",
        [
            "遥感影像数据 → 数据加载与增强 → U-Net 模型 → 训练（CrossEntropy + Adam）"
            " → 验证（mIoU/F1）→ 保存最优权重 → 测试集评估 → Gradio Web 单图预测与可视化",
            "数据层：datasetconfig/",
            "模型层：model/unet.py",
            "训练层：train.py",
            "评估层：evaluate.py",
            "展示层：Gradio 界面",
        ],
    )

    # 6 UNet 模型原理
    _add_bullet_slide(
        prs,
        "UNet 模型原理",
        [
            "编码器（下采样）：逐层提取多尺度特征",
            "解码器（上采样）：恢复空间分辨率",
            "跳跃连接（Skip Connection）：融合浅层细节与深层语义",
            "本实验配置：5 类输出、3 通道 RGB 输入、GroupNorm",
            "输入 256×256 → 输出 256×256 类别图",
        ],
    )

    # 7 实验环境与依赖
    _add_table_slide(
        prs,
        "实验环境与依赖",
        ["组件", "版本/配置"],
        [
            ["Python", "3.10"],
            ["虚拟环境", "conda unet"],
            ["PyTorch", "2.5.1+cu121"],
            ["torchvision", "0.20.1+cu121"],
            ["CUDA", "12.1"],
            ["其他", "numpy, pillow, tqdm, tensorboard 2.21.0, gradio 6.20.0"],
            ["硬件", "NVIDIA GPU（CUDA 训练）"],
        ],
        bullets_after=["单 epoch 训练约 4-5 分钟，GPU 加速对实验效率至关重要。"],
    )

    # 8 数据预处理与训练配置
    _add_table_slide(
        prs,
        "数据预处理与训练配置",
        ["超参数", "取值"],
        [
            ["batch size", "16"],
            ["learning rate", "0.001"],
            ["epochs", "100"],
            ["num_classes", "5"],
            ["保存路径", "save_pth/07070905"],
        ],
        bullets_before=[
            "数据加载：DataLoader，train/val 划分",
            "损失函数：CrossEntropyLoss（ignore_index=255）",
            "优化器：Adam，初始学习率 0.001",
            "训练轮次：100 epochs",
            "学习率调度：ReduceLROnPlateau",
            "模型保存：按 best_mIoU / best_F1 分别保存",
        ],
    )

    # 9 训练过程与收敛分析
    _add_bullet_slide(
        prs,
        "训练过程与收敛分析",
        [],
        sections=[
            (
                "初期（Epoch 1-2）",
                [
                    "Epoch 1：train_loss=1.3024，val_loss=1.3020，mIoU=0.1110，F1=0.1656",
                    "Epoch 2：train_loss=1.2424，val_loss=1.2253，mIoU=0.1318，F1=0.1923",
                ],
            ),
            (
                "末期（Epoch 98-100）",
                [
                    "Epoch 100：train_loss≈0.5500，val_loss≈0.9040，mIoU≈0.3784，F1≈0.5052",
                ],
            ),
            (
                "观察",
                [
                    "train_loss 持续下降，模型在学习",
                    "val_loss 高于 train_loss，存在一定过拟合",
                    "指标后期趋于平稳，训练充分",
                ],
            ),
        ],
    )

    # 10 TensorBoard 可视化分析
    _add_bullet_slide(
        prs,
        "TensorBoard 可视化分析",
        [
            "启动命令：tensorboard --logdir=logs",
            "访问地址：http://localhost:6006/",
            "train_loss 曲线：Step 0-100，从约 1.2 降至约 0.85，收敛良好",
            "F1 曲线：Step 0-100，从约 0.27 升至 0.5052",
            "同时监控：Precision、Recall、mIoU",
            "训练前 20 step 损失下降最快；F1 在 60 step 后进入平台期；"
            "与终端 Epoch 100 的 F1=0.5052 一致。",
        ],
    )

    # 11 测试集评估结果
    _add_table_slide(
        prs,
        "测试集评估结果",
        ["指标", "验证集（Epoch 100）", "测试集（evaluate.py）"],
        [
            ["mIoU", "0.3784", "0.3196"],
            ["Precision", "0.5500", "0.4499"],
            ["Recall", "0.4971", "0.4242"],
            ["F1", "0.5052", "0.4163"],
        ],
        bullets_after=[
            "测试集指标低于验证集，存在一定泛化差距",
            "mIoU 约 32%，多类遥感分割中属于可接受基线，仍有提升空间",
            "可能原因：类别不平衡、边界模糊、数据增强不足",
        ],
    )

    # 12 分割效果定性展示
    _add_bullet_slide(
        prs,
        "分割效果定性展示",
        [
            "展示内容：原始遥感图、模型预测分割图、预测与原图叠加图",
            "Gradio 输出各类别像素占比，例如：",
            "  类别 0：15.6% | 类别 1：57.5% | 类别 2：5.8%",
            "  类别 3：0.4% | 类别 4：20.7%",
            "定性观察与定量指标结合，验证模型对建筑、植被、道路等类别的分割效果",
        ],
    )

    # 13 可视化系统设计（Gradio）
    _add_bullet_slide(
        prs,
        "可视化系统设计（Gradio）",
        [],
        sections=[
            (
                "界面功能",
                [
                    "上传单张图片",
                    "选择模型权重路径、架构、类别数、颜色表",
                    "一键预测，输出分割彩图",
                    "显示各类别像素占比与推理设备信息",
                ],
            ),
            (
                "设计思路",
                [
                    "降低使用门槛，非技术人员也可操作",
                    "参数可调，便于切换不同 checkpoint",
                    "支持 CUDA 加速推理",
                    "课件原版为 Tkinter 桌面端，本项目采用 Gradio Web 端，更易演示与分享",
                ],
            ),
        ],
    )

    # 14 源码理解要点
    _add_bullet_slide(
        prs,
        "源码理解要点",
        [
            "train.py：训练循环、前向传播、损失计算、反向传播、验证与模型保存",
            "evaluate.py：加载 best 权重、测试集推理、聚合 mIoU/Precision/Recall/F1",
            "model/unet.py：DoubleConv、下采样、上采样、skip connection 拼接",
            "datasetconfig/：图像-标签配对加载、train/val 模式",
        ],
    )

    # 15 课程要求完成情况
    _add_dual_table_slide(
        prs,
        "课程要求完成情况",
        "基本要求",
        ["要求", "完成情况", "证据"],
        [
            ["源码理解", "部分", "已运行全流程"],
            ["UNet 结构", "部分", "原理说明"],
            ["完整流程", "完成", "训练+评估+可视化"],
            ["超参数调整", "部分", "lr=0.001"],
            ["TensorBoard", "完成", "损失/F1 曲线"],
            ["可视化功能", "完成", "Gradio 单图预测+指标"],
        ],
        "拓展要求",
        ["要求", "完成情况"],
        [
            ["数据增强", "未做"],
            ["注意力机制", "未做"],
            ["多模型对比", "未做"],
            ["自采数据集", "未做"],
        ],
    )

    # 16 不足与改进方向
    _add_bullet_slide(
        prs,
        "不足与改进方向",
        [],
        sections=[
            (
                "不足",
                [
                    "指标层面：测试 mIoU 32% 偏低，边界类（道路、水体）可能较差",
                    "实验层面：未系统对比 lr/batch size，未做数据增强消融",
                    "工程层面：数据路径硬编码，未实现多模型切换界面",
                    "文档层面：报告文字分析、团队分工尚未完成",
                ],
            ),
            (
                "改进方向",
                [
                    "引入 Dice Loss / Focal Loss",
                    "增加旋转、翻转、色彩扰动",
                    "尝试 MobileNet-UNet 轻量化对比",
                    "完善叠加可视化与批量评估入口",
                ],
            ),
        ],
    )

    # 17 总结与收获
    _add_bullet_slide(
        prs,
        "总结与收获",
        [
            "掌握了遥感语义分割从数据到部署的完整流程",
            "理解了 U-Net 结构与训练评估指标（mIoU、F1）",
            "学会使用 TensorBoard 监控训练、Gradio 搭建演示界面",
            "体会到深度学习工程中数据质量、超参数、泛化能力的重要性",
        ],
    )

    # 18 致谢 & Q&A
    _add_centered_slide(
        prs,
        [
            "致谢 & Q&A",
            "感谢朱盼盼老师指导",
            "感谢课程提供的 UNet 框架与 BDCI2017 数据集",
            "Q&A",
        ],
    )

    return prs


def main():
    prs = build_presentation()
    prs.save(OUTPUT_PATH)
    print(f"已生成: {OUTPUT_PATH}")
    print(f"幻灯片页数: {len(prs.slides)}")


if __name__ == "__main__":
    main()
