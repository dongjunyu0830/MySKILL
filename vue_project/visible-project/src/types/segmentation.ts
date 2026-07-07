// 遥感语义分割可视化系统 - 数据类型定义
// 这些类型同时作为"未来真实后端"的数据契约，前端只依赖这些类型，
// 数据来源（mock / 后端 API / ONNX / 预计算结果）都返回同样的结构。

/** 类别与其可视化颜色 */
export interface ClassColor {
  /** 类别 id（与标签图中的整数值对应） */
  id: number
  /** 类别名称 */
  name: string
  /** 十六进制颜色，如 #db5f57 */
  color: string
}

/** 数据集信息 */
export interface DatasetInfo {
  /** 唯一标识，如 "BDCI2017" */
  id: string
  /** 展示名称 */
  name: string
  /** 类别数 */
  numClasses: number
  /** 简介 */
  description: string
  /** 类别调色板 */
  classes: ClassColor[]
}

/** 模型信息 */
export interface ModelInfo {
  /** 唯一标识，如 "unet" */
  id: string
  /** 展示名称 */
  name: string
  /** 简介 */
  description: string
}

/** 单个类别在预测结果中的占比 */
export interface ClassDistribution {
  classId: number
  className: string
  color: string
  /** 像素占比，0~1 */
  ratio: number
}

/** 单张图片的预测结果 */
export interface PredictionResult {
  /** 原图 URL */
  originalUrl: string
  /** 预测彩色分割图 URL */
  predictionUrl: string
  /** 预测与原图叠加后的图 URL */
  overlayUrl: string
  /** 各类别像素占比 */
  distribution: ClassDistribution[]
  /** 推理耗时（毫秒） */
  inferenceMs: number
}

/** 单个类别的评估指标 */
export interface ClassMetric {
  classId: number
  className: string
  color: string
  iou: number
  precision: number
  recall: number
  f1: number
}

/** 测试集整体评估结果 */
export interface EvaluationResult {
  datasetId: string
  modelId: string
  /** 参与评估的样本数 */
  numSamples: number
  /** 整体（平均）指标 */
  mIoU: number
  precision: number
  recall: number
  f1: number
  /** 逐类指标 */
  perClass: ClassMetric[]
}

/** 数据集里可供选择的一张示例图片 */
export interface SampleImage {
  id: string
  name: string
  thumbnailUrl: string
}
