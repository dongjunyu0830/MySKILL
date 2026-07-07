// 分割服务（数据访问层）— 调用 FastAPI 后端真实接口

import type {
  DatasetInfo,
  ModelInfo,
  PredictionResult,
  EvaluationResult,
  SampleImage,
} from '@/types/segmentation'
import { API_BASE } from './config'

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `请求失败: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function listDatasets(): Promise<DatasetInfo[]> {
  return apiGet('/api/datasets')
}

export function listModels(dataset?: string): Promise<ModelInfo[]> {
  const q = dataset ? `?dataset=${encodeURIComponent(dataset)}` : ''
  return apiGet(`/api/models${q}`)
}

export function listSampleImages(datasetId: string, limit = 12): Promise<SampleImage[]> {
  return apiGet(
    `/api/samples?dataset=${encodeURIComponent(datasetId)}&limit=${limit}`,
  )
}

export interface PredictOptions {
  /** 测试集图片文件名，如 0_0_0.png */
  sample?: string
  /** 本地上传的图片文件 */
  file?: File
}

export async function predict(
  datasetId: string,
  modelId: string,
  opts: PredictOptions,
): Promise<PredictionResult> {
  const form = new FormData()
  form.append('dataset', datasetId)
  form.append('model', modelId)
  if (opts.sample) form.append('sample', opts.sample)
  if (opts.file) form.append('file', opts.file)

  const res = await fetch(`${API_BASE}/api/predict`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `预测失败: ${res.status}`)
  }
  return res.json() as Promise<PredictionResult>
}

export function evaluate(
  datasetId: string,
  modelId: string,
  limit = 60,
): Promise<EvaluationResult> {
  return apiGet(
    `/api/evaluate?dataset=${encodeURIComponent(datasetId)}&model=${encodeURIComponent(modelId)}&limit=${limit}`,
  )
}
