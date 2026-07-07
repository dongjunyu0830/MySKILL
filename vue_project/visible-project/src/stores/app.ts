import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  DatasetInfo,
  ModelInfo,
  PredictionResult,
  EvaluationResult,
} from '@/types/segmentation'
import * as api from '@/services/segmentationApi'
import type { PredictOptions } from '@/services/segmentationApi'

export const useAppStore = defineStore('app', () => {
  const datasets = ref<DatasetInfo[]>([])
  const models = ref<ModelInfo[]>([])

  const currentDatasetId = ref<string>('')
  const currentModelId = ref<string>('unet')

  const currentDataset = computed(() =>
    datasets.value.find((d) => d.id === currentDatasetId.value),
  )
  const currentModel = computed(() =>
    models.value.find((m) => m.id === currentModelId.value),
  )

  const prediction = ref<PredictionResult | null>(null)
  const evaluation = ref<EvaluationResult | null>(null)
  const predicting = ref(false)
  const evaluating = ref(false)

  async function refreshModels() {
    if (!currentDatasetId.value) {
      models.value = await api.listModels()
    } else {
      models.value = await api.listModels(currentDatasetId.value)
    }
    if (models.value.length && !models.value.some((m) => m.id === currentModelId.value)) {
      currentModelId.value = models.value[0]!.id
    }
  }

  async function loadMeta() {
    datasets.value = await api.listDatasets()
    if (datasets.value.length === 0) return
    if (!datasets.value.some((d) => d.id === currentDatasetId.value)) {
      currentDatasetId.value = datasets.value[0]!.id
    }
    await refreshModels()
  }

  function setDataset(id: string) {
    currentDatasetId.value = id
    prediction.value = null
    evaluation.value = null
    refreshModels()
  }

  function setModel(id: string) {
    currentModelId.value = id
    prediction.value = null
    evaluation.value = null
  }

  async function runPredict(opts: PredictOptions) {
    if (!currentDatasetId.value) return
    predicting.value = true
    try {
      prediction.value = await api.predict(
        currentDatasetId.value,
        currentModelId.value,
        opts,
      )
    } finally {
      predicting.value = false
    }
  }

  async function runEvaluate(limit = 60) {
    if (!currentDatasetId.value) return
    evaluating.value = true
    try {
      evaluation.value = await api.evaluate(
        currentDatasetId.value,
        currentModelId.value,
        limit,
      )
    } finally {
      evaluating.value = false
    }
  }

  return {
    datasets,
    models,
    currentDatasetId,
    currentModelId,
    currentDataset,
    currentModel,
    prediction,
    evaluation,
    predicting,
    evaluating,
    loadMeta,
    refreshModels,
    setDataset,
    setModel,
    runPredict,
    runEvaluate,
  }
})
